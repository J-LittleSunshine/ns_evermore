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
    NsRuntimeDeliveryStateError,
    NsRuntimeOwnerMismatchError,
    NsValidationError,
)
from ns_common.state_store import (
    StateAccessScope, StateAtomicScope, StateAuthorityKind,
    StateCallerCapability, StateOrderedIndexKey, StateOrderedIndexMutation,
    StateOrderedIndexMutationKind, StateStoreCapabilities, StateTransaction,
)
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
    OutboundDeliveryMaterial,
    OwnerRiskGuard,
    PayloadValidationResult,
    PayloadReference,
    PreparedActivationWorker,
    LocalDeliveryDispatchCoordinator,
    SendOutcome,
    SendWorker,
    StageSixAdmissionInput,
    StateStoreDeliveryAdmissionStore,
    StateStoreDeliveryPayloadAuthority,
    StateStoreDeliveryScheduler,
)
from ns_runtime.processor import RoutingPreparationResult
from ns_runtime.protocol import PayloadGroup, ProtocolGroup

from tests._state_store_contract_model import DeterministicStateStoreContractModel
from tests.test_runtime_connection_binding import UTC_START
from tests.test_runtime_delivery_admission import (
    MESSAGE_ID, _PayloadClient, _envelope_authority, _ids, _plan,
)


class _Validator(DeliveryPayloadValidator):
    def __init__(self, *, valid: bool = True, illegal: bool = False) -> None:
        self.valid = valid
        self.illegal = illegal
        self.calls = 0

    async def validate(self, delivery, *, target):
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
            request_binding_fingerprint=delivery.policy_decision.request_fingerprint,
            target_binding_fingerprint=delivery.target_fingerprint,
            target_access_decision_reference=target.access_decision_reference,
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
        if evidence.kind.value == "inline":
            payload = PayloadGroup(
                mode="inline", inline={"safe": [1, 2]},
                content_type=evidence.media_type,
                size_bytes=evidence.size_bytes, checksum=evidence.checksum,
            )
        else:
            payload = PayloadGroup(
                mode="reference", payload_ref={
                    "object_id": evidence.object_id,
                    "version": evidence.object_version,
                    "checksum": evidence.checksum,
                }, content_type=evidence.media_type,
                size_bytes=evidence.size_bytes, checksum=evidence.checksum,
                version=evidence.object_version,
            )
        return OutboundDeliveryMaterial(
            payload=payload,
            evidence_fingerprint=evidence.evidence_fingerprint,
        )


class _Targets(DeliveryTargetResolver):
    def __init__(
        self, *, active: bool = True, mismatch: bool = False,
        illegal: bool = False, protocol=None, access_decision_reference=None,
    ) -> None:
        self.active = active
        self.mismatch = mismatch
        self.illegal = illegal
        self.protocol = protocol
        self.access_decision_reference = access_decision_reference
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
            protocol=self.protocol or delivery.envelope_authority.protocol,
            protocol_schema_key="envelope-v1",
            access_decision_reference=(
                self.access_decision_reference
                or delivery.target_access_decision_reference
            ),
        )


class _Writer(DeliveryTransportWriter):
    def __init__(
        self,
        *,
        error: Exception | None = None,
        block: bool = False,
        authority_model=None,
        delivery_id: str | None = None,
        indeterminate: str | None = None,
    ) -> None:
        self.error = error
        self.block = block
        self.authority_model = authority_model
        self.delivery_id = delivery_id
        self.indeterminate = indeterminate
        self.calls = 0
        self.saw_authoritative_sending = False
        self.payloads = []
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def write(self, *, target, payload):
        self.calls += 1
        self.payloads.append(payload)
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
        if self.indeterminate == "before":
            self.authority_model.indeterminate_before_transaction = True
        elif self.indeterminate == "after":
            self.authority_model.indeterminate_after_transaction = True


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
            envelope_authority=_envelope_authority(self.plan),
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

    def _send_worker(self, *, targets=None, validator=None, payloads=None, writer=None,
                     policy=None, attempt_id_factory=None):
        return SendWorker(
            scheduler=self.scheduler,
            policy=policy or self.policy,
            target_resolver=targets or _Targets(),
            payload_validator=validator or _Validator(),
            payload_resolver=payloads or _Payloads(),
            transport_writer=writer or _Writer(),
            risk_guard=self.risk_guard,
            attempt_id_factory=attempt_id_factory or (lambda: "attempt-1"),
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

    async def test_fix01_expired_prepared_is_terminalized_and_not_revisited(self) -> None:
        self.clock.advance(31)
        result = await self._activate()
        self.assertEqual(0, len(result.activated))
        counts = await self.scheduler.resource_counts(tenant_id=self.tenant_id)
        self.assertEqual(0, counts.prepared)
        self.assertEqual(0, counts.queued)
        self.assertEqual(0, counts.write_failed)
        self.assertEqual(3, counts.expired)
        second = await self._activate()
        self.assertEqual(0, second.candidate_count)
        deliveries = [
            json.loads(record.document.payload)
            for record in self.model.records.values()
            if record.key.object_type == "delivery"
        ]
        self.assertEqual(
            {DeliveryRecordStatus.EXPIRED.value},
            {value["status"] for value in deliveries},
        )

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
        outbound = writer.payloads[0].envelope
        authority = result.delivery.envelope_authority
        self.assertEqual(authority.source, outbound.source)
        self.assertEqual(authority.auth_context, outbound.auth_context)
        self.assertEqual(authority.message, outbound.message)
        self.assertEqual(authority.trace, outbound.trace)
        self.assertEqual(authority.protocol, outbound.protocol)
        self.assertNotEqual(result.delivery.binding.runtime_id, outbound.source.runtime_id)
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

    async def test_fix02_protocol_and_payload_validation_replay_fail_closed(self) -> None:
        one = dataclasses.replace(self.policy, activation_batch_size=1)
        await self._activate(policy=one)
        mismatch_claim = await self._claim(token="claim-protocol", policy=one)
        writer = _Writer()
        protocol_result = await self._send_worker(
            policy=one,
            targets=_Targets(protocol=ProtocolGroup(major=1, minor=1, patch=0)),
            writer=writer,
        ).run_once(claim=mismatch_claim.claim)
        self.assertIs(DeliveryWriteFailure.POLICY_VERSION_MISMATCH, protocol_result.failure)
        self.assertEqual(0, writer.calls)

        await self._activate(policy=one)
        replay_claim = await self._claim(token="claim-replay", policy=one)

        class ReplayValidator(_Validator):
            async def validate(self, delivery, *, target):
                result = await super().validate(delivery, target=target)
                return dataclasses.replace(
                    result,
                    target_access_decision_reference="sha256:" + "9" * 64,
                )

        replay_writer = _Writer()
        replay = await self._send_worker(
            policy=one, validator=ReplayValidator(), writer=replay_writer,
        ).run_once(claim=replay_claim.claim)
        self.assertIs(DeliveryWriteFailure.PAYLOAD_INVALID, replay.failure)
        self.assertEqual(0, replay_writer.calls)

    async def test_fix02_release_reclaim_monotonic_and_old_claim_never_revives(self) -> None:
        one = dataclasses.replace(self.policy, activation_batch_size=1)
        await self._activate(policy=one)
        first = await self._claim(token="same-token", policy=one)
        released = await self.scheduler.release_claim(claim=first.claim)
        self.assertEqual(first.claim.fencing, released.last_fencing)
        second = await self._claim(token="same-token", policy=one)
        self.assertEqual(first.claim.fencing + 1, second.claim.fencing)
        self.assertEqual(first.claim.owner_epoch + 1, second.claim.owner_epoch)
        with self.assertRaises(NsRuntimeOwnerMismatchError):
            await self.scheduler.load_claimed(claim=first.claim)

    async def test_fix02_waiting_is_nonterminal_and_not_write_failed(self) -> None:
        one = dataclasses.replace(self.policy, activation_batch_size=1)
        await self._activate(policy=one)
        claim = await self._claim(token="claim-waiting", policy=one)
        result = await self._send_worker(
            policy=one, targets=_Targets(active=False), writer=_Writer(),
        ).run_once(claim=claim.claim)
        self.assertIs(DeliveryRecordStatus.TARGET_WAITING, result.delivery.status)
        counts = await self.scheduler.resource_counts(
            tenant_id=self.tenant_id,
            authority_bucket_count=one.authority_bucket_count,
        )
        self.assertEqual(1, counts.waiting)
        self.assertEqual(0, counts.write_failed)

    async def test_fix02_ack_deadline_does_not_extend_owner_lease(self) -> None:
        short = dataclasses.replace(
            self.policy, activation_batch_size=1, lease_ttl_seconds=5,
            renew_interval_seconds=1, write_timeout_seconds=1,
        )
        await self._activate(policy=short)
        claim = await self._claim(token="claim-short-lease", policy=short)
        result = await self._send_worker(policy=short).run_once(claim=claim.claim)
        owner = result.delivery.owner
        self.assertLess(owner.lease_expires_at, result.delivery.ack_deadline)
        lease_values = next(
            values for key, values in self.model.ordered_indexes.items()
            if key.name == "delivery.lease"
        )
        self.assertEqual(
            owner.lease_expires_at.timestamp(),
            lease_values[result.delivery.delivery_id],
        )
        self.clock.advance(6)
        recovered = await self._claim(
            worker_id="worker-recovered", token="claim-recovered", policy=short,
        )
        self.assertIs(ClaimOutcome.EMPTY, recovered.outcome)
        current = next(
            json.loads(record.document.payload)
            for record in self.model.records.values()
            if record.key.object_type == "delivery"
            and json.loads(record.document.payload)["delivery_id"]
            == result.delivery.delivery_id
        )
        from datetime import datetime
        self.assertLess(
            datetime.fromisoformat(current["owner"]["lease_expires_at"]),
            datetime.fromisoformat(current["ack_deadline"]),
        )

    async def test_fix02_envelope_authority_replace_cannot_impersonate_target(self) -> None:
        first = await self._activate()
        delivery = first.activated[0]
        hostile = dataclasses.replace(
            delivery.envelope_authority.source,
            runtime_id=delivery.binding.runtime_id,
            connection_id=delivery.binding.connection_id,
        )
        with self.assertRaises(NsValidationError):
            dataclasses.replace(
                delivery,
                envelope_authority=dataclasses.replace(
                    delivery.envelope_authority, source=hostile,
                ),
            )
        hostile_auth = dataclasses.replace(
            delivery.envelope_authority.auth_context,
            permission_digest="sha256:" + "f" * 64,
        )
        with self.assertRaises(NsValidationError):
            dataclasses.replace(
                delivery,
                envelope_authority=dataclasses.replace(
                    delivery.envelope_authority, auth_context=hostile_auth,
                ),
            )

    async def test_fix02_indeterminate_write_completion_reconciles_three_branches(self) -> None:
        one = dataclasses.replace(self.policy, activation_batch_size=1)

        await self._activate(policy=one)
        committed_claim = await self._claim(token="claim-committed", policy=one)
        committed = await self._send_worker(
            policy=one,
            writer=_Writer(
                authority_model=self.model,
                delivery_id=committed_claim.claim.delivery_id,
                indeterminate="after",
            ),
            attempt_id_factory=lambda: "attempt-indeterminate-after",
        ).run_once(claim=committed_claim.claim)
        self.assertIs(SendOutcome.ACK_WAITING, committed.outcome)
        self.assertIs(DeliveryRecordStatus.ACK_WAITING, committed.delivery.status)

        await self._activate(policy=one)
        absent_claim = await self._claim(token="claim-absent", policy=one)
        absent = await self._send_worker(
            policy=one,
            writer=_Writer(
                authority_model=self.model,
                delivery_id=absent_claim.claim.delivery_id,
                indeterminate="before",
            ),
            attempt_id_factory=lambda: "attempt-indeterminate-before",
        ).run_once(claim=absent_claim.claim)
        self.assertIs(SendOutcome.WRITE_FAILED, absent.outcome)
        self.assertIs(DeliveryRecordStatus.WRITE_UNCERTAIN, absent.delivery.status)
        self.assertIs(
            DeliveryWriteFailure.AUTHORITY_CONFLICT_AFTER_WRITE, absent.failure,
        )

        await self._activate(policy=one)
        conflict_claim = await self._claim(token="claim-conflict", policy=one)
        await self.scheduler.start_sending(
            claim=conflict_claim.claim,
            attempt_id="attempt-concurrent-state",
            policy=one,
        )
        await self.scheduler.complete_write_failure(
            claim=conflict_claim.claim,
            failure=DeliveryWriteFailure.TRANSPORT_WRITE_FAILED,
        )
        with self.assertRaises(NsRuntimeDeliveryStateError) as caught:
            await self.scheduler.reconcile_write_completion(claim=conflict_claim.claim)
        self.assertEqual(
            "completion_reconcile_conflict", caught.exception.details["reason"],
        )

    async def test_fix02_activation_cursor_skips_invalid_first_page(self) -> None:
        prepared = next(
            value for key, value in self.model.ordered_indexes.items()
            if key.name == "delivery.prepared"
        )
        first_delivery = next(
            json.loads(record.document.payload)
            for record in self.model.records.values()
            if record.key.object_type == "delivery"
        )
        bucket_id = first_delivery["authority_bucket_id"]
        namespace = next(iter(self.model.records)).namespace
        scope = StateAccessScope(
            atomic_scope=StateAtomicScope(
                namespace=namespace, partition=f"bucket-{bucket_id}",
            ),
            authority=StateAuthorityKind.DELIVERY_ADMISSION,
            caller="delivery.scheduling",
            capabilities=frozenset({
                StateCallerCapability.READ, StateCallerCapability.SCAN,
                StateCallerCapability.COMPARE_AND_SET,
                StateCallerCapability.TRANSACT,
                StateCallerCapability.ORDERED_INDEX,
                StateCallerCapability.APPEND,
            }),
        )
        index = StateOrderedIndexKey(
            namespace=namespace, name="delivery.prepared", bucket="delivery",
        )
        base_score = min(prepared.values()) - 1000
        await self.model.transact(StateTransaction(
            scope=scope,
            mutations=(),
            ordered_index_mutations=tuple(
                StateOrderedIndexMutation(
                    index=index,
                    kind=StateOrderedIndexMutationKind.ADD,
                    member=f"missing-delivery-{position:03d}",
                    score=base_score + position,
                )
                for position in range(65)
            ),
        ))
        result = await self._activate(policy=dataclasses.replace(
            self.policy, activation_batch_size=1, activation_scan_budget=80,
        ))
        self.assertEqual(1, len(result.activated))
        remaining = next(
            values for key, values in self.model.ordered_indexes.items()
            if key.name == "delivery.prepared"
        )
        self.assertFalse(any(member.startswith("missing-") for member in remaining))

    async def test_fix01_durable_inline_body_rebuilds_typed_envelope(self) -> None:
        await self._activate(policy=dataclasses.replace(
            self.policy, activation_batch_size=1,
        ))
        claimed = await self._claim(token="claim-durable-body")
        authority = StateStoreDeliveryPayloadAuthority(store=self.model)
        writer = _Writer(
            authority_model=self.model,
            delivery_id=claimed.claim.delivery_id,
        )
        result = await self._send_worker(
            validator=authority,
            payloads=authority,
            writer=writer,
            attempt_id_factory=lambda: "attempt-durable-body",
        ).run_once(claim=claimed.claim)
        self.assertIs(SendOutcome.ACK_WAITING, result.outcome)
        self.assertTrue(writer.saw_authoritative_sending)

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

        await self._activate(policy=dataclasses.replace(self.policy, activation_batch_size=1))
        mismatch_claim = await self._claim(token="claim-mismatch")
        mismatch = await self._send_worker(
            targets=_Targets(mismatch=True), writer=writer,
        ).run_once(claim=mismatch_claim.claim)
        self.assertIs(DeliveryWriteFailure.TARGET_IDENTITY_MISMATCH, mismatch.failure)
        self.assertEqual(0, writer.calls)

        await self._activate(policy=dataclasses.replace(self.policy, activation_batch_size=1))
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
                envelope_authority=_envelope_authority(plan),
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
        risky = await self.scheduler.mark_owner_at_risk(
            claim=claimed.claim,
            policy=self.policy,
        )
        self.assertIs(DeliveryOwnerRisk.AT_RISK, risky.owner.risk)
        self.assertEqual(1, risky.owner.renew_failures)
        self.risk_guard.mark_at_risk(claimed.claim)
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

    async def test_fix01_expired_owner_recovers_with_higher_fencing(self) -> None:
        await self._activate(policy=dataclasses.replace(self.policy, activation_batch_size=1))
        first = await self._claim(worker_id="worker-old", token="claim-old")
        self.assertEqual(1, first.claim.fencing)
        self.clock.advance(61)
        recovered = await self._claim(worker_id="worker-new", token="claim-new")
        self.assertIs(ClaimOutcome.CLAIMED, recovered.outcome)
        self.assertEqual(2, recovered.claim.fencing)
        with self.assertRaises(NsRuntimeOwnerMismatchError):
            await self.scheduler.load_claimed(claim=first.claim)
        current = await self.scheduler.load_claimed(claim=recovered.claim)
        self.assertEqual(2, current.owner.fencing)

    async def test_fix01_supervised_real_renew_loop(self) -> None:
        await self._activate(policy=dataclasses.replace(self.policy, activation_batch_size=1))
        claimed = await self._claim(token="claim-renew-loop")
        supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        renew = LeaseRenewWorker(
            scheduler=self.scheduler, policy=self.policy,
            risk_guard=self.risk_guard,
        )
        renew.schedule(claim=claimed.claim, supervisor=supervisor)
        await asyncio.sleep(0)
        original_expiry = claimed.delivery.owner.lease_expires_at
        self.clock.advance(self.policy.renew_interval_seconds)
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        renewed = await self.scheduler.load_claimed(claim=claimed.claim)
        self.assertGreater(renewed.owner.lease_expires_at, original_expiry)
        report = await supervisor.shutdown()
        self.assertTrue(report.clean)

    async def test_fix01_raw_material_wrong_digest_and_config_update_fail_closed(self) -> None:
        attempt_ids = (f"attempt-fix01-{value}" for value in itertools.count(1))
        next_attempt_id = lambda: next(attempt_ids)

        class RawResolver(DeliveryPayloadResolver):
            async def resolve(self, delivery):
                return '{"type":"task.dispatch"}'

        await self._activate(policy=dataclasses.replace(self.policy, activation_batch_size=1))
        raw_claim = await self._claim(token="claim-raw")
        writer = _Writer()
        raw = await self._send_worker(
            payloads=RawResolver(), writer=writer,
            attempt_id_factory=next_attempt_id,
        ).run_once(claim=raw_claim.claim)
        self.assertIs(SendOutcome.PRECHECK_FAILED, raw.outcome)
        self.assertEqual(0, writer.calls)

        await self._activate(policy=dataclasses.replace(self.policy, activation_batch_size=1))
        digest_claim = await self._claim(token="claim-digest")

        class WrongDigestResolver(DeliveryPayloadResolver):
            async def resolve(self, delivery):
                return OutboundDeliveryMaterial(
                    payload=PayloadGroup(mode="inline", inline={"safe": [9]}),
                    evidence_fingerprint=delivery.payload_evidence.evidence_fingerprint,
                )

        wrong = await self._send_worker(
            payloads=WrongDigestResolver(), writer=writer,
            attempt_id_factory=next_attempt_id,
        ).run_once(claim=digest_claim.claim)
        self.assertIs(SendOutcome.WRITE_FAILED, wrong.outcome)
        self.assertIs(DeliveryWriteFailure.PAYLOAD_INVALID, wrong.failure)
        self.assertEqual(0, writer.calls)

        await self._activate(policy=dataclasses.replace(self.policy, activation_batch_size=1))
        updated_claim = await self._claim(token="claim-config-update")
        updated_policy = dataclasses.replace(
            self.policy, config_version="c2", policy_version="p2",
        )
        updated = await self._send_worker(
            policy=updated_policy, writer=writer,
            attempt_id_factory=next_attempt_id,
        ).run_once(claim=updated_claim.claim)
        self.assertIs(SendOutcome.ACK_WAITING, updated.outcome)
        self.assertEqual(1, writer.calls)

    async def test_fix01_projection_indexes_and_transition_log_are_authoritative(self) -> None:
        await self._activate(policy=dataclasses.replace(self.policy, activation_batch_size=1))
        claimed = await self._claim(token="claim-projection")
        names = {
            key.name: values for key, values in self.model.ordered_indexes.items()
            if key.namespace == next(iter(self.model.records)).namespace
        }
        self.assertEqual(0, len(names["delivery.ready"]))
        self.assertEqual(1, len(names["delivery.claimed"]))
        self.assertEqual(1, len(names["delivery.lease"]))
        duplicate = await self._claim(worker_id="duplicate", token="duplicate")
        self.assertIs(ClaimOutcome.EMPTY, duplicate.outcome)
        events = [
            json.loads(document.payload)
            for documents in self.model.logs.values()
            for document in documents
        ]
        self.assertIn("delivery_claimed", {item["operation"] for item in events})
        self.assertEqual(
            1, sum(item["operation"] == "delivery_claimed" for item in events),
        )

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
        self.assertGreaterEqual(len(supervisor.task_names), 1)
        dispatch_name = next(name for name in supervisor.task_names
                             if name.startswith("p11-local-dispatch:"))
        await supervisor.get_task(dispatch_name)
        report = await supervisor.shutdown()
        self.assertTrue(report.clean)
        self.assertEqual(2, writer.calls)
        counts = await self.scheduler.resource_counts(tenant_id=self.tenant_id)
        self.assertEqual((1, 0, 0, 2), (
            counts.prepared, counts.queued, counts.active, counts.inflight,
        ))


if __name__ == "__main__":
    unittest.main()
