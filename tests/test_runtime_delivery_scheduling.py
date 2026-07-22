# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import dataclasses
from datetime import timedelta
import json
import itertools
import unittest

from ns_common.async_runtime import TaskSupervisor
from ns_common.config import NsRuntimeDeliveryConfig
from ns_common.exceptions import (
    NsRuntimeDeliveryLeaseExpiredError,
    NsRuntimeOwnerMismatchError,
    NsValidationError,
)
from ns_common.state_store import StateStoreCapabilities
from ns_common.time import ControlledClock
from ns_runtime.delivery import (
    AdmissionOutcome,
    AdmissionPolicyConfig,
    AdmissionRequest,
    AdmissionTrace,
    ClaimOutcome,
    ClaimWorker,
    DefaultAdmissionPolicy,
    DeliveryAdmissionService,
    DeliveryOwnerRisk,
    DeliveryPayloadResolver,
    DeliveryPayloadValidator,
    DeliveryRecordStatus,
    DeliverySchedulingPolicy,
    DeliveryTargetResolver,
    DeliveryTransportWriter,
    DeliveryWriteFailure,
    InlinePayload,
    LeaseRenewOutcome,
    LeaseRenewWorker,
    LocalDeliveryTarget,
    OutboundDeliveryPayload,
    OwnerRiskGuard,
    PayloadValidationResult,
    PayloadReference,
    PreparedActivationWorker,
    LocalDeliveryDispatchCoordinator,
    SendOutcome,
    SendWorker,
    StageSixAdmissionInput,
    StateStoreDeliveryAdmissionStore,
    StateStoreDeliveryScheduler,
)
from ns_runtime.processor import RoutingPreparationResult

from tests._state_store_contract_model import DeterministicStateStoreContractModel
from tests.test_runtime_connection_binding import UTC_START
from tests.test_runtime_delivery_admission import MESSAGE_ID, _PayloadClient, _ids, _plan


class _Validator(DeliveryPayloadValidator):
    def __init__(self, *, valid: bool = True, illegal: bool = False) -> None:
        self.valid = valid
        self.illegal = illegal
        self.calls = 0

    async def validate(self, delivery):
        self.calls += 1
        if self.illegal:
            return {"valid": True}
        evidence = delivery.payload_evidence
        return PayloadValidationResult(
            valid=self.valid,
            evidence_fingerprint=evidence.evidence_fingerprint,
            object_id=evidence.object_id,
            object_version=evidence.object_version,
            checksum=evidence.checksum,
            tenant_id=delivery.tenant_id,
        )


class _Payloads(DeliveryPayloadResolver):
    def __init__(self, *, illegal: bool = False) -> None:
        self.illegal = illegal
        self.calls = 0

    async def resolve(self, delivery):
        self.calls += 1
        if self.illegal:
            return object()
        evidence = delivery.payload_evidence
        return OutboundDeliveryPayload(
            wire_text='{"type":"task.dispatch"}',
            message_id=delivery.message_id,
            target_fingerprint=delivery.target_fingerprint,
            evidence_fingerprint=evidence.evidence_fingerprint,
            content_digest=evidence.digest,
        )


class _Targets(DeliveryTargetResolver):
    def __init__(self, *, active: bool = True, mismatch: bool = False, illegal: bool = False) -> None:
        self.active = active
        self.mismatch = mismatch
        self.illegal = illegal
        self.calls = 0

    async def resolve(self, delivery):
        self.calls += 1
        if self.illegal:
            return object()
        binding = delivery.binding
        return LocalDeliveryTarget(
            runtime_id=binding.runtime_id,
            connection_id=binding.connection_id,
            session_id=binding.session_id,
            connection_epoch=binding.connection_epoch,
            tenant_id=binding.tenant_id,
            identity=("wrong-identity" if self.mismatch else binding.identity_reference.value),
            active=self.active,
        )


class _Writer(DeliveryTransportWriter):
    def __init__(
        self,
        *,
        error: Exception | None = None,
        block: bool = False,
        authority_model=None,
        delivery_id: str | None = None,
    ) -> None:
        self.error = error
        self.block = block
        self.authority_model = authority_model
        self.delivery_id = delivery_id
        self.calls = 0
        self.saw_authoritative_sending = False
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def write(self, *, target, payload):
        self.calls += 1
        if self.authority_model is not None:
            values = [
                json.loads(record.document.payload)
                for record in self.authority_model.records.values()
            ]
            delivery = next(
                value for value in values
                if value.get("delivery_id") == self.delivery_id
            )
            attempt = next(
                value for value in values
                if value.get("attempt_id") == delivery.get("current_attempt_id")
            )
            if delivery["status"] != "sending" or attempt["status"] != "writing":
                raise AssertionError("transport invoked before atomic sending transition")
            self.saw_authoritative_sending = True
        self.started.set()
        if self.block:
            await self.release.wait()
        if self.error is not None:
            raise self.error


class DeliverySchedulingTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.clock = ControlledClock(utc_start=UTC_START)
        self.plan = await _plan()
        self.tenant_id = self.plan.authorization_evidence.effective_tenant_id
        self.model = DeterministicStateStoreContractModel(
            clock=self.clock,
            capabilities=StateStoreCapabilities.p10_contract(),
        )
        await self.model.open()
        self.admission_config = AdmissionPolicyConfig(
            config_version="c1",
            policy_version="p1",
            max_ack_timeout_seconds=60,
        )
        self.admission = DeliveryAdmissionService(
            policy=DefaultAdmissionPolicy(),
            policy_config=self.admission_config,
            store=StateStoreDeliveryAdmissionStore(self.model),
            payload_ref_client=_PayloadClient(self.clock),
            clock=self.clock,
            identifier_factory=_ids,
        )
        stage_six = StageSixAdmissionInput.from_result(
            RoutingPreparationResult.resolved(self.plan)
        )
        request = AdmissionRequest.from_stage_six(
            stage_six=stage_six,
            message_id=MESSAGE_ID,
            tenant_id=self.tenant_id,
            source_identity="identity-source",
            authorization_binding_reference=(
                self.plan.authorization_evidence.message_binding_reference
            ),
            payload=InlinePayload(
                value={"safe": [1, 2]},
                media_type="application/json",
                application_limit_bytes=4096,
                transport_limit_bytes=4096,
            ),
            requested_priority=None,
            requested_reliability=None,
            requested_expires_at=self.clock.utc_now() + timedelta(seconds=30),
            requested_ack_timeout_seconds=30,
            requested_target_strategy=self.plan.requested_strategy,
        )
        admitted = await self.admission.admit(
            request,
            trace=AdmissionTrace(trace_id="trace-p11"),
        )
        self.assertIs(AdmissionOutcome.ACCEPTED, admitted.outcome)
        self.scheduler = StateStoreDeliveryScheduler(
            store=self.model,
            clock=self.clock,
        )
        self.policy = DeliverySchedulingPolicy(
            config_version="c1",
            policy_version="p1",
            activation_batch_size=2,
            tenant_queued_high_watermark=10,
            target_queued_high_watermark=2,
            lease_ttl_seconds=60,
            renew_interval_seconds=5,
            max_renew_failures=2,
            owner_risk_window_seconds=4,
            write_timeout_seconds=1,
        )
        self.risk_guard = OwnerRiskGuard()

    async def asyncTearDown(self) -> None:
        await self.model.close()

    async def _activate(self, *, policy=None):
        return await PreparedActivationWorker(
            scheduler=self.scheduler,
            policy=policy or self.policy,
        ).run_once(tenant_id=self.tenant_id)

    async def _claim(self, *, worker_id="worker-1", token="claim-1", policy=None):
        return await ClaimWorker(
            scheduler=self.scheduler,
            policy=policy or self.policy,
            runtime_id=self.plan.selected_bindings[0].runtime_id,
            worker_id=worker_id,
            token_factory=lambda: token,
        ).run_once(tenant_id=self.tenant_id)

    def _send_worker(self, *, targets=None, validator=None, payloads=None, writer=None):
        return SendWorker(
            scheduler=self.scheduler,
            policy=self.policy,
            target_resolver=targets or _Targets(),
            payload_validator=validator or _Validator(),
            payload_resolver=payloads or _Payloads(),
            transport_writer=writer or _Writer(),
            risk_guard=self.risk_guard,
            attempt_id_factory=lambda: "attempt-1",
            clock=self.clock,
        )

    async def test_w01_activation_batches_watermarks_and_counts(self) -> None:
        first = await self._activate()
        self.assertEqual(3, first.candidate_count)
        self.assertEqual(2, len(first.activated))
        self.assertTrue(all(
            item.status is DeliveryRecordStatus.QUEUED
            and item.activation.policy_version == "p1"
            and item.owner is None
            for item in first.activated
        ))
        self.assertEqual((0, 2), (first.queued_before, first.queued_after))
        second = await self._activate()
        self.assertEqual(1, len(second.activated))
        documents = [json.loads(record.document.payload) for record in self.model.records.values()]
        root = next(
            value for value in documents
            if value.get("summary_id") == "summary:0" and "shard_count" in value
        )
        self.assertEqual((0, 3, 0, 0), (
            root["prepared_count"], root["queued_count"],
            root["active_count"], root["inflight_count"],
        ))

        limited_model = self.model
        self.assertIs(limited_model, self.model)

    async def test_w01_tenant_watermark_limits_activation(self) -> None:
        limited = dataclasses.replace(
            self.policy,
            activation_batch_size=3,
            tenant_queued_high_watermark=1,
        )
        result = await self._activate(policy=limited)
        self.assertEqual(1, len(result.activated))
        self.assertIn("tenant_watermark", {value.value for value in result.skip_reasons})
        global_limited = dataclasses.replace(
            self.policy,
            activation_batch_size=3,
            global_queued_high_watermark=1,
        )
        global_result = await self._activate(policy=global_limited)
        self.assertEqual(0, len(global_result.activated))
        self.assertIn(
            "global_watermark",
            {value.value for value in global_result.skip_reasons},
        )

    async def test_w02_multi_worker_claim_is_atomic_and_queued_is_not_transport_queue(self) -> None:
        one = dataclasses.replace(self.policy, activation_batch_size=1)
        await self._activate(policy=one)
        workers = tuple(
            ClaimWorker(
                scheduler=self.scheduler,
                policy=one,
                runtime_id=self.plan.selected_bindings[0].runtime_id,
                worker_id=f"worker-{index}",
                token_factory=lambda index=index: f"claim-{index}",
            )
            for index in range(8)
        )
        results = await asyncio.gather(*(
            worker.run_once(tenant_id=self.tenant_id) for worker in workers
        ))
        self.assertEqual(1, sum(
            result.outcome is ClaimOutcome.CLAIMED for result in results
        ))
        self.assertEqual(7, sum(
            result.outcome in {ClaimOutcome.CONTENDED, ClaimOutcome.EMPTY}
            for result in results
        ))
        duplicate = await self._claim(worker_id="duplicate", token="duplicate", policy=one)
        self.assertIs(ClaimOutcome.EMPTY, duplicate.outcome)
        self.assertEqual(0, _Writer().calls)

    async def test_w04_to_w07_success_creates_attempt_and_only_ack_waiting(self) -> None:
        await self._activate(policy=dataclasses.replace(self.policy, activation_batch_size=1))
        claimed = await self._claim()
        writer = _Writer(
            authority_model=self.model,
            delivery_id=claimed.claim.delivery_id,
        )
        result = await self._send_worker(writer=writer).run_once(claim=claimed.claim)
        self.assertIs(SendOutcome.ACK_WAITING, result.outcome)
        self.assertIs(DeliveryRecordStatus.ACK_WAITING, result.delivery.status)
        self.assertIsNotNone(result.delivery.ack_deadline)
        self.assertEqual(1, writer.calls)
        self.assertTrue(writer.saw_authoritative_sending)
        documents = [json.loads(record.document.payload) for record in self.model.records.values()]
        attempts = [value for value in documents if value.get("attempt_id") == "attempt-1"]
        self.assertEqual(1, len(attempts))
        self.assertEqual("write_succeeded", attempts[0]["status"])
        self.assertNotIn("sent_success", json.dumps(documents))
        root = next(
            value for value in documents
            if value.get("summary_id") == "summary:0" and "shard_count" in value
        )
        self.assertEqual((0, 0, 1), (
            root["active_count"], root["sending_count"], root["inflight_count"],
        ))
        counts = await self.scheduler.resource_counts(tenant_id=self.tenant_id)
        self.assertEqual((2, 0, 0, 1, 0), (
            counts.prepared, counts.queued, counts.active,
            counts.inflight, counts.write_failed,
        ))

    async def test_w04_prechecks_disconnect_payload_and_expiry_without_transport_write(self) -> None:
        await self._activate(policy=dataclasses.replace(self.policy, activation_batch_size=1))
        disconnected_claim = await self._claim(token="claim-disconnected")
        writer = _Writer()
        disconnected = await self._send_worker(
            targets=_Targets(active=False), writer=writer,
        ).run_once(claim=disconnected_claim.claim)
        self.assertIs(SendOutcome.PRECHECK_FAILED, disconnected.outcome)
        self.assertIs(DeliveryWriteFailure.TARGET_DISCONNECTED, disconnected.failure)
        self.assertEqual(0, writer.calls)
        self.assertIsNone(disconnected.delivery.owner)

        invalid_claim = await self._claim(token="claim-invalid")
        invalid = await self._send_worker(
            validator=_Validator(illegal=True), writer=writer,
        ).run_once(claim=invalid_claim.claim)
        self.assertIs(DeliveryWriteFailure.PAYLOAD_INVALID, invalid.failure)
        self.assertEqual(0, writer.calls)

        mismatch_claim = await self._claim(token="claim-mismatch")
        mismatch = await self._send_worker(
            targets=_Targets(mismatch=True), writer=writer,
        ).run_once(claim=mismatch_claim.claim)
        self.assertIs(DeliveryWriteFailure.TARGET_IDENTITY_MISMATCH, mismatch.failure)
        self.assertEqual(0, writer.calls)

        expired_claim = await self._claim(token="claim-expired")
        self.clock.advance(31)
        expired = await self._send_worker(writer=writer).run_once(
            claim=expired_claim.claim,
        )
        self.assertIs(DeliveryWriteFailure.DELIVERY_EXPIRED, expired.failure)
        self.assertEqual(0, writer.calls)

    async def test_w04_invalid_payload_reference_is_revalidated_before_write(self) -> None:
        model = DeterministicStateStoreContractModel(
            clock=self.clock,
            capabilities=StateStoreCapabilities.p10_contract(),
        )
        await model.open()
        try:
            plan = await _plan(count=1)
            tenant_id = plan.authorization_evidence.effective_tenant_id
            service = DeliveryAdmissionService(
                policy=DefaultAdmissionPolicy(),
                policy_config=self.admission_config,
                store=StateStoreDeliveryAdmissionStore(model),
                payload_ref_client=_PayloadClient(self.clock),
                clock=self.clock,
                identifier_factory=lambda kind, index: f"ref-{kind}:{index}",
            )
            request = AdmissionRequest.from_stage_six(
                stage_six=StageSixAdmissionInput.from_result(
                    RoutingPreparationResult.resolved(plan)
                ),
                message_id=MESSAGE_ID,
                tenant_id=tenant_id,
                source_identity="identity-source",
                authorization_binding_reference=(
                    plan.authorization_evidence.message_binding_reference
                ),
                payload=PayloadReference(
                    object_id="object-p11",
                    version="v1",
                    checksum="sha256:" + "1" * 64,
                    owner_identity="identity-source",
                ),
                requested_priority=None,
                requested_reliability=None,
                requested_expires_at=self.clock.utc_now() + timedelta(seconds=30),
                requested_ack_timeout_seconds=30,
                requested_target_strategy=plan.requested_strategy,
            )
            admitted = await service.admit(
                request,
                trace=AdmissionTrace(trace_id="trace-ref-p11"),
            )
            self.assertIs(AdmissionOutcome.ACCEPTED, admitted.outcome)
            scheduler = StateStoreDeliveryScheduler(store=model, clock=self.clock)
            policy = dataclasses.replace(self.policy, activation_batch_size=1)
            await PreparedActivationWorker(
                scheduler=scheduler, policy=policy,
            ).run_once(tenant_id=tenant_id)
            claim = await ClaimWorker(
                scheduler=scheduler,
                policy=policy,
                runtime_id=plan.selected_bindings[0].runtime_id,
                worker_id="ref-worker",
                token_factory=lambda: "ref-claim",
            ).run_once(tenant_id=tenant_id)
            writer = _Writer()
            result = await SendWorker(
                scheduler=scheduler,
                policy=policy,
                target_resolver=_Targets(),
                payload_validator=_Validator(valid=False),
                payload_resolver=_Payloads(),
                transport_writer=writer,
                risk_guard=OwnerRiskGuard(),
                attempt_id_factory=lambda: "ref-attempt",
                clock=self.clock,
            ).run_once(claim=claim.claim)
            self.assertIs(DeliveryWriteFailure.PAYLOAD_INVALID, result.failure)
            self.assertEqual(0, writer.calls)
        finally:
            await model.close()

    async def test_w03_w09_owner_risk_stops_new_write(self) -> None:
        await self._activate(policy=dataclasses.replace(self.policy, activation_batch_size=1))
        claimed = await self._claim(token="claim-risk")
        renew = LeaseRenewWorker(
            scheduler=self.scheduler,
            policy=self.policy,
            risk_guard=self.risk_guard,
        )
        self.assertIs(LeaseRenewOutcome.FAILURE_RECORDED, (
            await renew.run_once(claim=claimed.claim, renewal_succeeded=False)
        ).outcome)
        self.assertIs(LeaseRenewOutcome.FAILURE_RECORDED, (
            await renew.run_once(claim=claimed.claim, renewal_succeeded=False)
        ).outcome)
        risk = await renew.run_once(claim=claimed.claim, renewal_succeeded=False)
        self.assertIs(LeaseRenewOutcome.AT_RISK, risk.outcome)
        writer = _Writer()
        stopped = await self._send_worker(writer=writer).run_once(claim=claimed.claim)
        self.assertIs(SendOutcome.OWNER_RISK, stopped.outcome)
        self.assertEqual(0, writer.calls)
        self.assertIsNone(stopped.delivery.owner)

    async def test_w03_expired_or_old_owner_cannot_write(self) -> None:
        await self._activate(policy=dataclasses.replace(self.policy, activation_batch_size=1))
        claimed = await self._claim(token="claim-current")
        stale = dataclasses.replace(claimed.claim, claim_token="claim-stale")
        writer = _Writer()
        with self.assertRaises(NsRuntimeOwnerMismatchError):
            await self._send_worker(writer=writer).run_once(claim=stale)
        self.assertEqual(0, writer.calls)
        self.clock.advance(61)
        with self.assertRaises(NsRuntimeDeliveryLeaseExpiredError):
            await self._send_worker(writer=writer).run_once(claim=claimed.claim)
        self.assertEqual(0, writer.calls)

    async def test_w08_write_failure_is_typed_and_never_enters_retry_or_dead_letter(self) -> None:
        await self._activate(policy=dataclasses.replace(self.policy, activation_batch_size=1))
        claimed = await self._claim(token="claim-failure")
        failed = await self._send_worker(
            writer=_Writer(error=ConnectionError("peer detail must not persist")),
        ).run_once(claim=claimed.claim)
        self.assertIs(SendOutcome.WRITE_FAILED, failed.outcome)
        self.assertIs(DeliveryRecordStatus.WRITE_FAILED, failed.delivery.status)
        self.assertIs(DeliveryWriteFailure.TRANSPORT_WRITE_FAILED, failed.failure)
        persisted = b" ".join(record.document.payload for record in self.model.records.values())
        self.assertNotIn(b"peer detail", persisted)
        self.assertNotIn(b"retry_scheduled", persisted)
        self.assertNotIn(b"dead_letter", persisted)

    async def test_shutdown_cancellation_records_interrupted_attempt_for_recovery(self) -> None:
        await self._activate(policy=dataclasses.replace(self.policy, activation_batch_size=1))
        claimed = await self._claim(token="claim-shutdown")
        writer = _Writer(block=True)
        task = asyncio.create_task(
            self._send_worker(writer=writer).run_once(claim=claimed.claim)
        )
        await writer.started.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        documents = [json.loads(record.document.payload) for record in self.model.records.values()]
        delivery = next(
            value for value in documents
            if value.get("delivery_id") == claimed.claim.delivery_id
        )
        attempt = next(value for value in documents if value.get("attempt_id") == "attempt-1")
        self.assertEqual("write_failed", delivery["status"])
        self.assertEqual("shutdown_interrupted", delivery["last_failure"])
        self.assertEqual("write_failed", attempt["status"])

    async def test_public_replace_and_illegal_dependencies_fail_closed(self) -> None:
        activation = await self._activate(policy=dataclasses.replace(self.policy, activation_batch_size=1))
        queued = activation.activated[0]
        with self.assertRaises(NsValidationError):
            dataclasses.replace(queued, status="sending")
        with self.assertRaises(NsValidationError):
            dataclasses.replace(queued, status=DeliveryRecordStatus.SENDING)
        with self.assertRaises(NsValidationError):
            dataclasses.replace(queued, status=DeliveryRecordStatus.RETRY_SCHEDULED)
        claimed = await self._claim(token="claim-illegal")
        writer = _Writer()
        result = await self._send_worker(
            targets=_Targets(illegal=True), writer=writer,
        ).run_once(claim=claimed.claim)
        self.assertIs(DeliveryWriteFailure.TARGET_DISCONNECTED, result.failure)
        self.assertEqual(0, writer.calls)
        self.assertIs(DeliveryOwnerRisk.HEALTHY, queued.owner.risk if queued.owner else DeliveryOwnerRisk.HEALTHY)

    async def test_w11_local_experiment_uses_existing_supervisor_and_stays_bounded(self) -> None:
        self.assertFalse(NsRuntimeDeliveryConfig().local_task_dispatch_experimental_enabled)
        supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        sequence = itertools.count()
        writer = _Writer()
        coordinator = LocalDeliveryDispatchCoordinator(
            task_supervisor=supervisor,
            scheduler=self.scheduler,
            policy=self.policy,
            runtime_id=self.plan.selected_bindings[0].runtime_id,
            target_resolver=_Targets(),
            payload_validator=_Validator(),
            payload_resolver=_Payloads(),
            transport_writer=writer,
            risk_guard=self.risk_guard,
            identifier_factory=lambda kind: f"{kind}-{next(sequence)}",
            clock=self.clock,
        )
        self.assertTrue(coordinator.schedule(tenant_id=self.tenant_id))
        self.assertEqual(1, len(supervisor.task_names))
        await supervisor.get_task(supervisor.task_names[0])
        report = await supervisor.shutdown()
        self.assertTrue(report.clean)
        self.assertEqual(2, writer.calls)
        counts = await self.scheduler.resource_counts(tenant_id=self.tenant_id)
        self.assertEqual((1, 0, 0, 2), (
            counts.prepared, counts.queued, counts.active, counts.inflight,
        ))


if __name__ == "__main__":
    unittest.main()
