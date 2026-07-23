# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import copy
import dataclasses
from datetime import timedelta
import hashlib
import json
import itertools
import unittest

from ns_common.async_runtime import TaskSupervisor
from ns_common.config import NsRuntimeDeliveryConfig
from ns_common.exceptions import (
    NsRuntimeDeliveryLeaseExpiredError,
    NsRuntimeDeliveryStateError,
    NsRuntimeOwnerMismatchError,
    NsRuntimeIamUnavailableError,
    NsRuntimeStateStoreUnavailableError,
    NsRuntimeStateStoreVersionMismatchError,
    NsValidationError,
)
from ns_common.iam import (
    PayloadRefRevalidationDecision,
    PayloadRefRevalidationRequest,
)
from ns_common.state_store import (
    StateAccessScope, StateAssertion, StateAtomicScope, StateAuthorityKind,
    StateCallerCapability, StateOrderedIndexKey, StateOrderedIndexMutation,
    StateOrderedIndexEntry, StateOrderedIndexMutationKind,
    StateStoreCapabilities, StateTransaction,
    StateDocument, StateKey, StateMutation, StateMutationKind,
)
from ns_common.time import ControlledClock
from ns_runtime.delivery import (
    AdmissionOutcome,
    AdmissionPolicyConfig,
    AdmissionRequest,
    AdmissionTrace,
    ActivationSkipReason,
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
    DeliveryTransportWriteResult,
    DeliveryTransportWriteState,
    DeliveryWriteFailure,
    DeliveryAuthorityLayout,
    InlinePayload,
    IamDeliveryPayloadReferenceValidator,
    LeaseRenewOutcome,
    LeaseRenewWorker,
    LocalDeliveryTarget,
    OutboundDeliveryMaterial,
    OwnerRiskGuard,
    PayloadAccessDecisionEvidence,
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
    StateStoreDeliveryAuthorityRegistry,
    delivery_from_dict,
    delivery_to_dict,
    validate_payload_authority,
)
from ns_runtime.iam.client import IamClient, IamClientFactory
from ns_common.http_client import NsHttpClientOwner
import ns_runtime.delivery.scheduling as scheduling_module
from ns_runtime.processor import RoutingPreparationResult
from ns_runtime.protocol import PayloadGroup, ProtocolGroup

from tests._state_store_contract_model import DeterministicStateStoreContractModel
from tests.test_runtime_connection_binding import UTC_START
from tests.test_runtime_delivery_admission import (
    MESSAGE_ID, _PayloadClient, _envelope_authority, _ids, _plan,
)


def _repositories(model, *, runtime_id: str = "runtime-local"):
    return model.repository_composition().delivery_repositories(
        runtime_id=runtime_id,
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
            valid=(
                self.valid
                and evidence.kind.value != "payload_ref"
            ),
            evidence_fingerprint=evidence.evidence_fingerprint,
            object_id=evidence.object_id,
            object_version=evidence.object_version,
            checksum=evidence.checksum,
            tenant_id=delivery.tenant_id,
            request_binding_fingerprint=delivery.policy_decision.request_fingerprint,
            target_binding_fingerprint=delivery.target_fingerprint,
            access_decision_evidence=None,
        )


class _PayloadIamServer:
    def __init__(
        self,
        clock: ControlledClock,
        *,
        allowed: bool = True,
        permission_version: str = "permission-version:current",
        expires_in_seconds: int = 120,
        illegal_decision: bool = False,
        object_id: str | None = None,
        target_principal: str | None = None,
        unavailable: bool = False,
    ) -> None:
        self.clock = clock
        self.allowed = allowed
        self.permission_version = permission_version
        self.expires_in_seconds = expires_in_seconds
        self.illegal_decision = illegal_decision
        self.object_id = object_id
        self.target_principal = target_principal
        self.unavailable = unavailable
        self.requests: list[PayloadRefRevalidationRequest] = []
        self.server: asyncio.AbstractServer | None = None

    async def start(self) -> str:
        self.server = await asyncio.start_server(
            self._handle,
            "127.0.0.1",
            0,
        )
        port = self.server.sockets[0].getsockname()[1]
        return f"http://127.0.0.1:{port}/"

    async def close(self) -> None:
        if self.server is not None:
            self.server.close()
            await self.server.wait_closed()

    async def _handle(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        headers_raw = await reader.readuntil(b"\r\n\r\n")
        headers = {
            name.strip().casefold(): value.strip()
            for line in headers_raw.decode("iso-8859-1").split("\r\n")[1:]
            if ":" in line
            for name, value in (line.split(":", 1),)
        }
        body = await reader.readexactly(
            int(headers.get("content-length", "0")),
        )
        request = PayloadRefRevalidationRequest.from_wire(json.loads(body))
        self.requests.append(request)
        if self.unavailable:
            writer.write(
                b"HTTP/1.1 503 Service Unavailable\r\n"
                b"Content-Length: 0\r\nConnection: close\r\n\r\n"
            )
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return
        if self.illegal_decision:
            data: object = {"allowed": True}
        else:
            current = self.clock.utc_now()
            live = self.expires_in_seconds > 0
            data = PayloadRefRevalidationDecision(
                valid=live,
                allowed=self.allowed and live,
                reason="acl_allow" if self.allowed and live else "denied",
                object_id=self.object_id or request.object_id,
                version=request.version,
                checksum=request.checksum,
                size_bytes=request.size_bytes,
                tenant_id=request.tenant_id,
                target_principal=(
                    self.target_principal or request.target_principal
                ),
                target_fingerprint=request.target_fingerprint,
                permission_snapshot_ref=request.permission_snapshot_ref,
                permission_version=self.permission_version,
                decision_reference="iam-payload:test-decision",
                decided_at=current,
                expires_at=(
                    current + timedelta(seconds=self.expires_in_seconds)
                    if live else current
                ),
                refresh_required=(
                    self.permission_version != request.permission_version
                ),
            ).to_wire()
        response_body = json.dumps({
            "success": True,
            "code": "OK",
            "error": None,
            "message": "ok",
            "data": data,
            "request_id": "payload-test",
        }).encode()
        writer.write(
            b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
            + f"Content-Length: {len(response_body)}\r\n".encode()
            + b"Connection: close\r\n\r\n"
            + response_body
        )
        await writer.drain()
        writer.close()
        await writer.wait_closed()


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
                or "session-permission-snapshot:current"
            ),
            permission_snapshot_reference="permission:snapshot:current",
            permission_version="permission-version:current",
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
        after_write=None,
        result_state: DeliveryTransportWriteState = (
            DeliveryTransportWriteState.SUCCEEDED
        ),
    ) -> None:
        self.error = error
        self.block = block
        self.authority_model = authority_model
        self.delivery_id = delivery_id
        self.indeterminate = indeterminate
        self.after_write = after_write
        self.result_state = result_state
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
        if self.after_write is not None:
            await self.after_write()
        return DeliveryTransportWriteResult(
            state=self.result_state,
            failure=(
                None
                if self.result_state is DeliveryTransportWriteState.SUCCEEDED
                else DeliveryWriteFailure.TRANSPORT_WRITE_FAILED
            ),
        )


class DeliverySchedulingTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.clock = ControlledClock(utc_start=UTC_START)
        self.plan = await _plan()
        self.tenant_id = self.plan.authorization_evidence.effective_tenant_id
        self.model = DeterministicStateStoreContractModel(
            clock=self.clock,
            capabilities=StateStoreCapabilities.p10_contract(),
        )
        self.repositories = _repositories(self.model)
        await self.model.open()
        self.admission_config = AdmissionPolicyConfig(
            config_version="c1",
            policy_version="p1",
            max_ack_timeout_seconds=60,
        )
        self.admission = DeliveryAdmissionService.for_contract_tests(
            policy=DefaultAdmissionPolicy(),
            policy_config=self.admission_config,
            store=StateStoreDeliveryAdmissionStore(
                repository=self.repositories.admission,
                registry_repository=self.repositories.registry,
            ),
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
            repository=self.repositories.scheduler,
            registry_repository=self.repositories.registry,
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

    async def _payload_iam(self, **options: object) -> IamClient:
        server = _PayloadIamServer(self.clock, **options)
        base_url = await server.start()
        owner = NsHttpClientOwner()
        http = owner.create(
            name="payload-iam-composition-test",
            base_url=base_url,
            timeout_seconds=0.2,
        )
        client = IamClientFactory(
            http_owner=owner,
            http_client=http,
            runtime_composition=self,
        ).create(
            internal_service_credential="p" * 32,
            trace_id_factory=lambda: "operation:payload-test",
            clock=self.clock,
        )
        client.revalidation_requests = server.requests  # type: ignore[attr-defined]
        self.addAsyncCleanup(owner.aclose)
        self.addAsyncCleanup(server.close)
        return client

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

    async def _create_projection_clones(
        self,
        *,
        source,
        scope,
        index,
        prefix: str,
        count: int,
        first_score: float,
        status: DeliveryRecordStatus,
        owner=None,
    ) -> tuple[str, ...]:
        members = tuple(f"{prefix}-{position:03d}" for position in range(count))
        mutations = []
        index_mutations = []
        for position, member in enumerate(members):
            clone = dataclasses.replace(
                source,
                delivery_id=member,
                status=status,
                activation=(
                    None
                    if status is DeliveryRecordStatus.PREPARED
                    else source.activation
                ),
                owner=owner,
                last_fencing=(0 if owner is None else owner.fencing),
                owner_epoch=(0 if owner is None else owner.owner_epoch),
                state_version=1,
            )
            mutations.append(StateMutation(
                key=StateKey(
                    namespace=scope.namespace,
                    object_type="delivery",
                    object_id="sha256:" + hashlib.sha256(
                        member.encode()
                    ).hexdigest(),
                ),
                assertion=StateAssertion.absent(),
                kind=StateMutationKind.CREATE,
                document=StateDocument(
                    schema_name="delivery_delivery",
                    schema_version=1,
                    state_version=clone.state_version,
                    payload=json.dumps(
                        delivery_to_dict(clone),
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode(),
                ),
            ))
            index_mutations.append(StateOrderedIndexMutation(
                index=index,
                kind=StateOrderedIndexMutationKind.ADD,
                member=member,
                score=first_score + position,
            ))
        await self.model.transact(StateTransaction(
            scope=scope,
            mutations=tuple(mutations),
            ordered_index_mutations=tuple(index_mutations),
        ))
        return members

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

    async def test_fix03_runtime_global_watermark_recovers_all_registered_tenants(self) -> None:
        layout = DeliveryAuthorityLayout(bucket_count=8)
        registry = StateStoreDeliveryAuthorityRegistry(
            repository=self.repositories.registry,
        )
        await registry.ensure_registered(tenant_id="tenant-b", layout=layout)
        tenant_b_scope = self.repositories.scheduler.delivery_scope(
            tenant_id="tenant-b", bucket_id=7, layout_generation=2,
        )
        tenant_b_index = StateOrderedIndexKey(
            namespace=tenant_b_scope.namespace,
            name="delivery.ready",
            bucket="delivery",
        )
        await self.model.transact(StateTransaction(
            scope=tenant_b_scope,
            mutations=(),
            ordered_index_mutations=(StateOrderedIndexMutation(
                index=tenant_b_index,
                kind=StateOrderedIndexMutationKind.ADD,
                member="tenant-b-ready-1",
                score=1.0,
            ),),
        ))
        restarted = StateStoreDeliveryScheduler(
            repository=self.repositories.scheduler,
            registry_repository=self.repositories.registry,
            clock=self.clock,
        )
        policy = dataclasses.replace(
            self.policy,
            global_queued_high_watermark=1,
            tenant_queued_high_watermark=10,
        )
        self.assertEqual(1, await restarted.runtime_queued_count(policy=policy))
        blocked = await restarted.activate_prepared(
            tenant_id=self.tenant_id,
            policy=policy,
        )
        self.assertEqual(0, len(blocked.activated))
        self.assertIn(ActivationSkipReason.GLOBAL_WATERMARK, blocked.skip_reasons)
        tenant_a = await restarted.resource_counts(tenant_id=self.tenant_id)
        tenant_b = await restarted.resource_counts(tenant_id="tenant-b")
        self.assertEqual((0, 1), (tenant_a.queued, tenant_b.queued))

    async def test_fix03_authority_layout_change_is_restart_fail_closed(self) -> None:
        registry = StateStoreDeliveryAuthorityRegistry(
            repository=self.repositories.registry,
        )
        with self.assertRaises(NsRuntimeStateStoreVersionMismatchError) as caught:
            await registry.ensure_registered(
                tenant_id=self.tenant_id,
                layout=DeliveryAuthorityLayout(bucket_count=16),
            )
        self.assertEqual(
            "authority_layout_migration_required",
            caught.exception.details["reason"],
        )

    def test_fix03_runtime_config_snapshot_carries_layout_and_scan_budget(self) -> None:
        runtime = NsRuntimeDeliveryConfig(
            authority_bucket_count=16,
            activation_scan_budget=321,
        )
        scheduling = DeliverySchedulingPolicy.from_runtime_config(
            runtime, config_version="c-layout", policy_version="p-layout",
        )
        admission = AdmissionPolicyConfig.from_runtime_config(
            runtime, config_version="c-layout", policy_version="p-layout",
        )
        self.assertEqual((16, 321, 2), (
            scheduling.authority_bucket_count,
            scheduling.activation_scan_budget,
            scheduling.authority_layout_generation,
        ))
        self.assertEqual((16, 2), (
            admission.authority_bucket_count,
            admission.authority_layout_generation,
        ))
        self.assertEqual("restart_required", runtime.authority_layout_apply_mode)

    async def test_fix03_blocked_bucket_does_not_starve_later_bucket(self) -> None:
        source_record = next(
            record for record in self.model.records.values()
            if record.key.object_type == "delivery"
        )
        source = delivery_from_dict(json.loads(source_record.document.payload))
        blocked = dataclasses.replace(
            source,
            delivery_id="delivery-blocked-bucket-0",
            authority_bucket_id=0,
        )
        scope = self.repositories.scheduler.delivery_scope(
            tenant_id=self.tenant_id, bucket_id=0, layout_generation=2,
        )
        delivery_key = StateKey(
            namespace=scope.namespace,
            object_type="delivery",
            object_id="sha256:" + __import__("hashlib").sha256(
                blocked.delivery_id.encode()
            ).hexdigest(),
        )
        prepared = StateOrderedIndexKey(
            namespace=scope.namespace, name="delivery.prepared", bucket="delivery",
        )
        target = StateOrderedIndexKey(
            namespace=scope.namespace,
            name="delivery.target." + blocked.target_fingerprint.split(":", 1)[1],
            bucket="delivery",
        )
        await self.model.transact(StateTransaction(
            scope=scope,
            mutations=(StateMutation(
                key=delivery_key,
                assertion=StateAssertion.absent(),
                kind=StateMutationKind.CREATE,
                document=StateDocument(
                    schema_name="delivery_delivery",
                    schema_version=1,
                    state_version=blocked.state_version,
                    payload=json.dumps(
                        delivery_to_dict(blocked),
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode(),
                ),
            ),),
            ordered_index_mutations=(
                StateOrderedIndexMutation(
                    index=prepared,
                    kind=StateOrderedIndexMutationKind.ADD,
                    member=blocked.delivery_id,
                    score=0.0,
                ),
                StateOrderedIndexMutation(
                    index=target,
                    kind=StateOrderedIndexMutationKind.ADD,
                    member="blocked-target-1",
                    score=0.0,
                ),
                StateOrderedIndexMutation(
                    index=target,
                    kind=StateOrderedIndexMutationKind.ADD,
                    member="blocked-target-2",
                    score=1.0,
                ),
            ),
        ))
        result = await self._activate(
            policy=dataclasses.replace(self.policy, activation_batch_size=1),
        )
        self.assertEqual(1, len(result.activated))
        self.assertNotEqual(blocked.delivery_id, result.activated[0].delivery_id)

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

    async def test_fix04_ready_cursor_repairs_sixteen_wrong_status_records_across_providers(
        self,
    ) -> None:
        one = dataclasses.replace(
            self.policy,
            activation_batch_size=1,
            activation_scan_budget=16,
        )
        activated = await self._activate(policy=one)
        real = activated.activated[0]
        scope = self.repositories.scheduler.delivery_scope(
            tenant_id=self.tenant_id,
            bucket_id=real.authority_bucket_id,
            layout_generation=2,
        )
        ready = StateOrderedIndexKey(
            namespace=scope.namespace,
            name="delivery.ready",
            bucket="delivery",
        )
        ready_values = self.model.ordered_indexes[ready]
        real_score = ready_values[real.delivery_id]
        stale_members = await self._create_projection_clones(
            source=real,
            scope=scope,
            index=ready,
            prefix="stale-ready-prepared",
            count=16,
            first_score=real_score - 1000,
            status=DeliveryRecordStatus.PREPARED,
        )

        provider_a = StateStoreDeliveryScheduler(
            repository=self.repositories.scheduler,
            registry_repository=self.repositories.registry,
            clock=self.clock,
        )
        first = await ClaimWorker(
            scheduler=provider_a,
            policy=one,
            runtime_id=self.plan.selected_bindings[0].runtime_id,
            worker_id="provider-a",
            token_factory=lambda: "provider-a-claim",
        ).run_once(tenant_id=self.tenant_id)
        self.assertIs(ClaimOutcome.EMPTY, first.outcome)

        provider_b = StateStoreDeliveryScheduler(
            repository=self.repositories.scheduler,
            registry_repository=self.repositories.registry,
            clock=self.clock,
        )
        second = await ClaimWorker(
            scheduler=provider_b,
            policy=one,
            runtime_id=self.plan.selected_bindings[0].runtime_id,
            worker_id="provider-b",
            token_factory=lambda: "provider-b-claim",
        ).run_once(tenant_id=self.tenant_id)
        self.assertIs(ClaimOutcome.CLAIMED, second.outcome)
        self.assertEqual(real.delivery_id, second.claim.delivery_id)
        self.assertTrue(set(stale_members).isdisjoint(
            self.model.ordered_indexes[ready],
        ))
        repair_events = [
            json.loads(document.payload)
            for key, documents in self.model.logs.items()
            if key.object_type == "delivery_scheduler_repair_log"
            for document in documents
        ]
        self.assertEqual(
            16,
            sum(
                event["reason"] == "status_not_queued"
                for event in repair_events
            ),
        )
        serialized_events = json.dumps(repair_events)
        self.assertNotIn("stale-ready-prepared", serialized_events)

    async def test_fix04_lease_cursor_repairs_sixteen_unrecoverable_before_owner(
        self,
    ) -> None:
        one = dataclasses.replace(
            self.policy,
            activation_batch_size=1,
            activation_scan_budget=16,
        )
        await self._activate(policy=one)
        original = await self._claim(
            worker_id="original-worker",
            token="original-claim",
            policy=one,
        )
        scope = self.repositories.scheduler.delivery_scope(
            tenant_id=self.tenant_id,
            bucket_id=original.delivery.authority_bucket_id,
            layout_generation=2,
        )
        lease = StateOrderedIndexKey(
            namespace=scope.namespace,
            name="delivery.lease",
            bucket="delivery",
        )
        real_score = self.model.ordered_indexes[lease][
            original.delivery.delivery_id
        ]
        foreign_owner = dataclasses.replace(
            original.delivery.owner,
            runtime_id="runtime-foreign",
        )
        stale_members = await self._create_projection_clones(
            source=original.delivery,
            scope=scope,
            index=lease,
            prefix="stale-foreign-lease",
            count=16,
            first_score=real_score - 1000,
            status=DeliveryRecordStatus.QUEUED,
            owner=foreign_owner,
        )
        self.clock.advance(61)

        provider_a = StateStoreDeliveryScheduler(
            repository=self.repositories.scheduler,
            registry_repository=self.repositories.registry,
            clock=self.clock,
        )
        first = await ClaimWorker(
            scheduler=provider_a,
            policy=one,
            runtime_id=original.claim.runtime_id,
            worker_id="recovery-a",
            token_factory=lambda: "recovery-a-claim",
        ).run_once(tenant_id=self.tenant_id)
        self.assertIs(ClaimOutcome.EMPTY, first.outcome)

        provider_b = StateStoreDeliveryScheduler(
            repository=self.repositories.scheduler,
            registry_repository=self.repositories.registry,
            clock=self.clock,
        )
        recovered = await ClaimWorker(
            scheduler=provider_b,
            policy=one,
            runtime_id=original.claim.runtime_id,
            worker_id="recovery-b",
            token_factory=lambda: "recovery-b-claim",
        ).run_once(tenant_id=self.tenant_id)
        self.assertIs(ClaimOutcome.CLAIMED, recovered.outcome)
        self.assertEqual(original.claim.delivery_id, recovered.claim.delivery_id)
        self.assertEqual(original.claim.fencing + 1, recovered.claim.fencing)
        self.assertTrue(set(stale_members).isdisjoint(
            self.model.ordered_indexes[lease],
        ))

    async def test_fix05_repairs_bind_release_renew_and_missing_create_observations(
        self,
    ) -> None:
        one = dataclasses.replace(self.policy, activation_batch_size=1)
        activated = await self._activate(policy=one)
        claimed = await self._claim(policy=one, token="repair-race-claim")
        scope = self.repositories.scheduler.delivery_scope(
            tenant_id=self.tenant_id,
            bucket_id=claimed.delivery.authority_bucket_id,
            layout_generation=2,
        )
        ready = StateOrderedIndexKey(
            namespace=scope.namespace,
            name="delivery.ready",
            bucket="delivery",
        )
        lease = StateOrderedIndexKey(
            namespace=scope.namespace,
            name="delivery.lease",
            bucket="delivery",
        )
        stale_ready_score = self.clock.utc_now().timestamp() - 10
        await self.model.transact(StateTransaction(
            scope=scope,
            mutations=(),
            ordered_index_mutations=(StateOrderedIndexMutation(
                index=ready,
                kind=StateOrderedIndexMutationKind.ADD,
                member=claimed.claim.delivery_id,
                score=stale_ready_score,
            ),),
        ))
        observed_claimed = await self.scheduler._read_delivery(
            scope,
            claimed.claim.delivery_id,
        )
        before_logs = sum(len(items) for items in self.model.logs.values())

        async def release_during_repair(_transaction):
            await self.scheduler.fail_precheck(
                claim=claimed.claim,
                failure=DeliveryWriteFailure.TARGET_DISCONNECTED,
            )

        self.model.before_transaction = release_during_repair
        repaired = await self.scheduler._repair_ordered_projection(
            scope=scope,
            index=ready,
            entry=StateOrderedIndexEntry(
                member=claimed.claim.delivery_id,
                score=stale_ready_score,
            ),
            reason="queued_owner_present",
            observed_record=observed_claimed.record,
        )
        self.assertFalse(repaired)
        self.assertIn(claimed.claim.delivery_id, self.model.ordered_indexes[ready])
        released = await self.scheduler._read_delivery(
            scope,
            claimed.claim.delivery_id,
        )
        self.assertIsNone(released.value.owner)
        self.assertEqual(
            before_logs + 1,
            sum(len(items) for items in self.model.logs.values()),
        )

        await self._activate(policy=one)
        reclaimed = None
        for attempt in range(3):
            candidate = await self._claim(
                policy=one,
                worker_id="renew-race-worker",
                token=f"renew-race-claim-{attempt}",
            )
            if candidate.outcome is ClaimOutcome.CLAIMED:
                reclaimed = candidate
                break
        self.assertIsNotNone(reclaimed)
        assert reclaimed is not None and reclaimed.claim is not None
        lease_score = self.model.ordered_indexes[lease][
            reclaimed.claim.delivery_id
        ]
        observed_owner = await self.scheduler._read_delivery(
            scope,
            reclaimed.claim.delivery_id,
        )
        self.clock.advance(one.renew_interval_seconds)

        async def renew_during_repair(_transaction):
            await self.scheduler.renew_owner(
                claim=reclaimed.claim,
                policy=one,
            )

        self.model.before_transaction = renew_during_repair
        repaired = await self.scheduler._repair_ordered_projection(
            scope=scope,
            index=lease,
            entry=StateOrderedIndexEntry(
                member=reclaimed.claim.delivery_id,
                score=lease_score,
            ),
            reason="lease_score_stale",
            observed_record=observed_owner.record,
            replacement_score=lease_score - 1,
        )
        self.assertFalse(repaired)
        self.assertGreater(
            self.model.ordered_indexes[lease][reclaimed.claim.delivery_id],
            lease_score,
        )

        missing_member = "missing-create-race"
        missing_score = self.clock.utc_now().timestamp()
        await self.model.transact(StateTransaction(
            scope=scope,
            mutations=(),
            ordered_index_mutations=(StateOrderedIndexMutation(
                index=ready,
                kind=StateOrderedIndexMutationKind.ADD,
                member=missing_member,
                score=missing_score,
            ),),
        ))
        clone = dataclasses.replace(
            activated.activated[0],
            delivery_id=missing_member,
            state_version=1,
        )

        async def create_during_repair(_transaction):
            await self.model.transact(StateTransaction(
                scope=scope,
                mutations=(StateMutation(
                    key=StateKey(
                        namespace=scope.namespace,
                        object_type="delivery",
                        object_id="sha256:" + hashlib.sha256(
                            missing_member.encode(),
                        ).hexdigest(),
                    ),
                    assertion=StateAssertion.absent(),
                    kind=StateMutationKind.CREATE,
                    document=StateDocument(
                        schema_name="delivery_delivery",
                        schema_version=1,
                        state_version=1,
                        payload=json.dumps(
                            delivery_to_dict(clone),
                            sort_keys=True,
                            separators=(",", ":"),
                        ).encode(),
                    ),
                ),),
            ))

        self.model.before_transaction = create_during_repair
        repaired = await self.scheduler._repair_ordered_projection(
            scope=scope,
            index=ready,
            entry=StateOrderedIndexEntry(
                member=missing_member,
                score=missing_score,
            ),
            reason="record_missing_or_malformed",
            observe_missing_or_malformed=True,
            quarantine=True,
        )
        self.assertFalse(repaired)
        self.assertIn(missing_member, self.model.ordered_indexes[ready])

    async def test_fix05_cursor_identity_and_legacy_reset_gate(self) -> None:
        from ns_runtime.delivery.scheduling_store import (
            _legacy_scheduler_cursor_key,
            _scheduler_cursor_key,
        )

        scope_2_0 = self.repositories.scheduler.delivery_scope(
            tenant_id=self.tenant_id, bucket_id=0, layout_generation=2,
        )
        scope_2_1 = self.repositories.scheduler.delivery_scope(
            tenant_id=self.tenant_id, bucket_id=1, layout_generation=2,
        )
        scope_3_0 = self.repositories.scheduler.delivery_scope(
            tenant_id=self.tenant_id, bucket_id=0, layout_generation=3,
        )
        keys = {
            _scheduler_cursor_key(scope_2_0, "activation.prepared").object_id,
            _scheduler_cursor_key(scope_2_1, "activation.prepared").object_id,
            _scheduler_cursor_key(scope_3_0, "activation.prepared").object_id,
            _scheduler_cursor_key(scope_2_0, "claim.ready").object_id,
        }
        self.assertEqual(4, len(keys))
        legacy = _legacy_scheduler_cursor_key(
            scope_2_0,
            "activation.prepared",
        )
        await self.model.transact(StateTransaction(
            scope=scope_2_0,
            mutations=(StateMutation(
                key=legacy,
                assertion=StateAssertion.absent(),
                kind=StateMutationKind.CREATE,
                document=StateDocument(
                    schema_name="delivery_scheduler_cursor",
                    schema_version=1,
                    state_version=1,
                    payload=b"legacy",
                ),
            ),),
        ))
        with self.assertRaises(NsRuntimeStateStoreVersionMismatchError):
            await self.scheduler._read_scheduler_cursor(
                scope_2_0,
                "activation.prepared",
            )

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
        self.assertEqual(authority.message.message_id, outbound.message.message_id)
        self.assertEqual(authority.message.type, outbound.message.type)
        self.assertEqual(authority.message.category, outbound.message.category)
        self.assertEqual(authority.message.created_at, outbound.message.created_at)
        self.assertEqual(0, outbound.message.priority)
        self.assertEqual("at_least_once", outbound.message.reliability)
        self.assertEqual(
            result.delivery.policy_decision.expires_at.isoformat(),
            outbound.message.expires_at,
        )
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
                valid = await super().validate(delivery, target=target)
                return dataclasses.replace(
                    valid,
                    request_binding_fingerprint="sha256:" + ("0" * 64),
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
        self.assertIs(SendOutcome.WRITE_UNCERTAIN, absent.outcome)
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

    async def test_fix03_lease_renew_after_transport_write_reconciles_uncertain(self) -> None:
        one = dataclasses.replace(self.policy, activation_batch_size=1)
        await self._activate(policy=one)
        claimed = await self._claim(token="claim-renew-race", policy=one)

        async def renew_after_write():
            await self.scheduler.renew_owner(claim=claimed.claim, policy=one)

        result = await self._send_worker(
            policy=one,
            writer=_Writer(after_write=renew_after_write),
            attempt_id_factory=lambda: "attempt-renew-race",
        ).run_once(claim=claimed.claim)
        self.assertIs(SendOutcome.WRITE_UNCERTAIN, result.outcome)
        self.assertIs(DeliveryRecordStatus.WRITE_UNCERTAIN, result.delivery.status)
        self.assertIs(
            DeliveryWriteFailure.AUTHORITY_CONFLICT_AFTER_WRITE,
            result.failure,
        )

    async def test_fix04_expired_lease_after_transport_write_reconciles_uncertain(
        self,
    ) -> None:
        one = dataclasses.replace(self.policy, activation_batch_size=1)
        await self._activate(policy=one)
        claimed = await self._claim(token="claim-expired-after-write", policy=one)

        async def expire_after_write():
            self.clock.advance(one.lease_ttl_seconds + 1)

        result = await self._send_worker(
            policy=one,
            writer=_Writer(after_write=expire_after_write),
            attempt_id_factory=lambda: "attempt-expired-after-write",
        ).run_once(claim=claimed.claim)
        self.assertIs(SendOutcome.WRITE_UNCERTAIN, result.outcome)
        self.assertIs(DeliveryRecordStatus.WRITE_UNCERTAIN, result.delivery.status)
        self.assertIsNone(result.delivery.owner)
        self.assertIs(
            DeliveryWriteFailure.AUTHORITY_CONFLICT_AFTER_WRITE,
            result.failure,
        )

    async def test_fix04_committed_ack_reconciles_after_lease_expiry(self) -> None:
        one = dataclasses.replace(self.policy, activation_batch_size=1)
        await self._activate(policy=one)
        claimed = await self._claim(token="claim-committed-expired", policy=one)
        transition = await self.scheduler.start_sending(
            claim=claimed.claim,
            attempt_id="attempt-committed-expired",
            policy=one,
        )
        committed = await self.scheduler.complete_write_success(
            claim=claimed.claim,
            expected_state_version=transition.delivery.state_version,
        )
        self.assertIs(DeliveryRecordStatus.ACK_WAITING, committed.status)
        self.clock.advance(one.lease_ttl_seconds + 1)
        reconciled = await self.scheduler.reconcile_write_completion(
            claim=claimed.claim,
        )
        self.assertIs(DeliveryRecordStatus.ACK_WAITING, reconciled.status)
        self.assertEqual(committed.state_version, reconciled.state_version)

    async def test_fix04_higher_fencing_replacement_reconciles_attempt_uncertain(
        self,
    ) -> None:
        one = dataclasses.replace(self.policy, activation_batch_size=1)
        await self._activate(policy=one)
        claimed = await self._claim(token="claim-before-fencing", policy=one)
        sending = await self.scheduler.start_sending(
            claim=claimed.claim,
            attempt_id="attempt-before-fencing",
            policy=one,
        )
        authority_record = next(
            record
            for record in self.model.records.values()
            if record.key.object_type == "delivery"
            and json.loads(record.document.payload).get("delivery_id")
            == claimed.claim.delivery_id
        )
        replacement_owner = dataclasses.replace(
            sending.delivery.owner,
            worker_id="replacement-worker",
            claim_token="replacement-claim",
            fencing=sending.delivery.owner.fencing + 1,
            owner_epoch=sending.delivery.owner.owner_epoch + 1,
        )
        replaced = dataclasses.replace(
            sending.delivery,
            owner=replacement_owner,
            last_fencing=replacement_owner.fencing,
            owner_epoch=replacement_owner.owner_epoch,
            state_version=sending.delivery.state_version + 1,
        )
        await self.model.transact(StateTransaction(
            scope=self.repositories.scheduler.delivery_scope(
                tenant_id=self.tenant_id,
                bucket_id=sending.delivery.authority_bucket_id,
                layout_generation=2,
            ),
            mutations=(StateMutation(
                key=authority_record.key,
                assertion=StateAssertion.matches(
                    authority_record.revision,
                    state_version=authority_record.document.state_version,
                ),
                kind=StateMutationKind.REPLACE,
                document=StateDocument(
                    schema_name=authority_record.document.schema_name,
                    schema_version=authority_record.document.schema_version,
                    state_version=replaced.state_version,
                    payload=json.dumps(
                        delivery_to_dict(replaced),
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode(),
                ),
            ),),
        ))
        reconciled = await self.scheduler.reconcile_write_completion(
            claim=claimed.claim,
        )
        self.assertIs(DeliveryRecordStatus.WRITE_UNCERTAIN, reconciled.status)
        self.assertIsNone(reconciled.owner)
        self.assertEqual(replacement_owner.fencing, reconciled.last_fencing)

    async def test_fix04_activation_cursor_persists_across_provider_restarts(self) -> None:
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
        namespace = next(
            key.namespace for key in self.model.records
            if key.object_type == "delivery"
        )
        scope = self.model.issue_contract_test_scope(
            atomic_scope=StateAtomicScope(
                namespace=namespace, partition=f"layout-2-bucket-{bucket_id}",
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
        policy = dataclasses.replace(
            self.policy,
            activation_batch_size=1,
            activation_scan_budget=16,
        )
        results = []
        for _ in range(6):
            provider = StateStoreDeliveryScheduler(
                repository=self.repositories.scheduler,
                registry_repository=self.repositories.registry,
                clock=self.clock,
            )
            result = await PreparedActivationWorker(
                scheduler=provider,
                policy=policy,
            ).run_once(tenant_id=self.tenant_id)
            results.append(result)
            if result.activated:
                break
        self.assertEqual(0, len(results[0].activated))
        self.assertEqual(1, len(results[-1].activated))
        self.assertLessEqual(len(results), 6)
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
        authority = StateStoreDeliveryPayloadAuthority(
            repository=self.repositories.payload,
        )
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

    async def test_payload_iam_validator_rejects_fakes_uninitialized_and_override(
        self,
    ) -> None:
        with self.assertRaises(ImportError):
            from ns_runtime.delivery.scheduling import (  # type: ignore[attr-defined]  # noqa: F401
                _issue_payload_access_decision_evidence,
            )
        self.assertFalse(hasattr(
            scheduling_module,
            "_issue_payload_access_decision_evidence",
        ))
        class TextSubclass(str):
            pass

        class ForgedIamClient(IamClient):
            async def revalidate_payload_ref(self, request):
                return object()

        invalid_clients = (
            object(),
            {},
            TextSubclass("iam-client"),
            object.__new__(IamClient),
            object.__new__(ForgedIamClient),
        )
        for value in invalid_clients:
            with self.subTest(client_type=type(value).__name__):
                with self.assertRaises(NsValidationError):
                    IamDeliveryPayloadReferenceValidator(
                        iam_client=value,  # type: ignore[arg-type]
                        clock=self.clock,
                    )

        real_client = await self._payload_iam()
        validator = IamDeliveryPayloadReferenceValidator(
            iam_client=real_client,
            clock=self.clock,
        )
        with self.assertRaises(NsValidationError):
            copy.copy(validator._evidence_issuer)

        async def forged_revalidation(_request):
            return object()

        real_client.revalidate_payload_ref = forged_revalidation  # type: ignore[method-assign]
        delivery = next(
            delivery_from_dict(json.loads(record.document.payload))
            for record in self.model.records.values()
            if record.key.object_type == "delivery"
        )
        with self.assertRaises(NsValidationError):
            await validator.validate(
                delivery,
                target=await _Targets().resolve(delivery),
            )

    async def test_w04_invalid_payload_reference_is_revalidated_before_write(self) -> None:
        model = DeterministicStateStoreContractModel(
            clock=self.clock,
            capabilities=StateStoreCapabilities.p10_contract(),
        )
        await model.open()
        try:
            repositories = _repositories(model)
            plan = await _plan(count=1)
            tenant_id = plan.authorization_evidence.effective_tenant_id
            service = DeliveryAdmissionService.for_contract_tests(
                policy=DefaultAdmissionPolicy(),
                policy_config=self.admission_config,
                store=StateStoreDeliveryAdmissionStore(
                    repository=repositories.admission,
                    registry_repository=repositories.registry,
                ),
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
            reference_delivery = next(
                delivery_from_dict(json.loads(record.document.payload))
                for record in model.records.values()
                if record.key.object_type == "delivery"
            )
            target = await _Targets().resolve(reference_delivery)
            iam = await self._payload_iam()
            production_validator = IamDeliveryPayloadReferenceValidator(
                iam_client=iam,
                clock=self.clock,
            )
            valid = await production_validator.validate(
                reference_delivery,
                target=target,
            )
            self.assertTrue(validate_payload_authority(
                reference_delivery,
                valid,
                target=target,
                now=self.clock.utc_now(),
            ))
            self.assertEqual(
                target.permission_snapshot_reference,
                iam.revalidation_requests[0].permission_snapshot_ref,
            )
            self.assertEqual(
                target.identity,
                iam.revalidation_requests[0].target_principal,
            )
            self.assertEqual(
                reference_delivery.policy_decision.request_fingerprint,
                iam.revalidation_requests[0].admission_authority_reference,
            )
            stale = await IamDeliveryPayloadReferenceValidator(
                iam_client=await self._payload_iam(
                    permission_version="permission-version:stale",
                ),
                clock=self.clock,
            ).validate(reference_delivery, target=target)
            self.assertFalse(stale.valid)
            denied = await IamDeliveryPayloadReferenceValidator(
                iam_client=await self._payload_iam(allowed=False),
                clock=self.clock,
            ).validate(reference_delivery, target=target)
            self.assertFalse(denied.valid)
            expired = await IamDeliveryPayloadReferenceValidator(
                iam_client=await self._payload_iam(expires_in_seconds=-1),
                clock=self.clock,
            ).validate(reference_delivery, target=target)
            self.assertFalse(expired.valid)
            self.assertIsNone(expired.access_decision_evidence)
            with self.assertRaises(NsRuntimeIamUnavailableError):
                await IamDeliveryPayloadReferenceValidator(
                    iam_client=await self._payload_iam(
                        illegal_decision=True,
                    ),
                    clock=self.clock,
                ).validate(reference_delivery, target=target)
            with self.assertRaises(NsValidationError):
                dataclasses.replace(
                    valid.access_decision_evidence,
                    iam_decision_version="permission-version:forged",
                )
            with self.assertRaises(NsValidationError):
                copy.copy(valid.access_decision_evidence)
            copied_access = object.__new__(PayloadAccessDecisionEvidence)
            for field in dataclasses.fields(PayloadAccessDecisionEvidence):
                object.__setattr__(
                    copied_access,
                    field.name,
                    getattr(valid.access_decision_evidence, field.name),
                )
            object.__setattr__(
                copied_access,
                "iam_decision_version",
                "permission-version:forged",
            )
            self.assertFalse(validate_payload_authority(
                reference_delivery,
                dataclasses.replace(
                    valid,
                    access_decision_evidence=copied_access,
                ),
                target=target,
                now=self.clock.utc_now(),
            ))
            with self.assertRaises(NsValidationError):
                PayloadAccessDecisionEvidence(**{
                    field.name: getattr(valid.access_decision_evidence, field.name)
                    for field in dataclasses.fields(PayloadAccessDecisionEvidence)
                    if not field.name.startswith("_")
                })
            cross_object = await production_validator.__class__(
                iam_client=await self._payload_iam(
                    object_id="object-other",
                ),
                clock=self.clock,
            ).validate(reference_delivery, target=target)
            self.assertFalse(cross_object.valid)
            cross_target = await production_validator.__class__(
                iam_client=await self._payload_iam(
                    target_principal="identity-other",
                ),
                clock=self.clock,
            ).validate(reference_delivery, target=target)
            self.assertFalse(cross_target.valid)
            with self.assertRaises(NsRuntimeIamUnavailableError):
                await production_validator.__class__(
                    iam_client=await self._payload_iam(unavailable=True),
                    clock=self.clock,
                ).validate(reference_delivery, target=target)
            scheduler = StateStoreDeliveryScheduler(
                repository=repositories.scheduler,
                registry_repository=repositories.registry,
                clock=self.clock,
            )
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
        handle = renew.schedule(claim=claimed.claim, supervisor=supervisor)
        self.assertEqual(claimed.claim.delivery_id, handle.delivery_id)
        await asyncio.sleep(0)
        original_expiry = claimed.delivery.owner.lease_expires_at
        self.clock.advance(self.policy.renew_interval_seconds)
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        renewed = await self.scheduler.load_claimed(claim=claimed.claim)
        self.assertGreater(renewed.owner.lease_expires_at, original_expiry)
        await handle.stop()
        self.assertTrue(handle.done)
        report = await supervisor.shutdown()
        self.assertTrue(report.clean)
        self.assertEqual((), supervisor.failures)

    async def test_fix05_unknown_write_stops_renewal_and_expires_to_recovery(
        self,
    ) -> None:
        supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        sequence = itertools.count()

        class UnknownWriter(DeliveryTransportWriter):
            async def write(inner_self, *, target, payload):
                self.model.indeterminate_before_transaction = True
                self.model.read_error = NsRuntimeStateStoreUnavailableError()

        writer = UnknownWriter()
        coordinator = LocalDeliveryDispatchCoordinator(
            task_supervisor=supervisor,
            scheduler=self.scheduler,
            policy=dataclasses.replace(
                self.policy,
                activation_batch_size=1,
            ),
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
        dispatch_name = next(
            name for name in supervisor.task_names
            if name.startswith("p11-local-dispatch:")
        )
        await supervisor.get_task(dispatch_name)
        self.assertFalse(any(
            name.startswith("p11-lease-renew:")
            for name in supervisor.pending_task_names
        ))
        self.assertEqual((), supervisor.failures)

        self.model.read_error = None
        self.model.indeterminate_before_transaction = False
        self.clock.advance(self.policy.lease_ttl_seconds + 1)
        await self._claim(
            policy=dataclasses.replace(self.policy, activation_batch_size=1),
            worker_id="unknown-recovery",
            token="unknown-recovery-token",
        )
        delivery_values = [
            delivery_from_dict(json.loads(record.document.payload))
            for record in self.model.records.values()
            if record.key.object_type == "delivery"
        ]
        self.assertIn(
            DeliveryRecordStatus.WRITE_UNCERTAIN,
            {value.status for value in delivery_values},
        )
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
        delivery_namespace = next(
            key.namespace for key in self.model.records
            if key.object_type == "delivery"
        )
        names = {
            key.name: values for key, values in self.model.ordered_indexes.items()
            if key.namespace == delivery_namespace
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

    async def test_w08_started_write_exception_is_uncertain_and_never_retried(self) -> None:
        await self._activate(policy=dataclasses.replace(self.policy, activation_batch_size=1))
        claimed = await self._claim(token="claim-failure")
        failed = await self._send_worker(
            writer=_Writer(error=ConnectionError("peer detail must not persist")),
        ).run_once(claim=claimed.claim)
        self.assertIs(SendOutcome.WRITE_UNCERTAIN, failed.outcome)
        self.assertIs(DeliveryRecordStatus.WRITE_UNCERTAIN, failed.delivery.status)
        self.assertIs(DeliveryWriteFailure.TRANSPORT_WRITE_FAILED, failed.failure)
        persisted = b" ".join(record.document.payload for record in self.model.records.values())
        self.assertNotIn(b"peer detail", persisted)
        self.assertNotIn(b"retry_scheduled", persisted)
        self.assertNotIn(b"dead_letter", persisted)

    async def test_before_start_failure_is_the_only_transport_write_failed_path(
        self,
    ) -> None:
        await self._activate(policy=dataclasses.replace(
            self.policy,
            activation_batch_size=1,
        ))
        claimed = await self._claim(token="claim-before-start")
        failed = await self._send_worker(writer=_Writer(
            result_state=DeliveryTransportWriteState.NOT_STARTED,
        )).run_once(claim=claimed.claim)
        self.assertIs(SendOutcome.WRITE_FAILED, failed.outcome)
        self.assertIs(DeliveryRecordStatus.WRITE_FAILED, failed.delivery.status)

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
        self.assertEqual("write_uncertain", delivery["status"])
        self.assertEqual("shutdown_interrupted", delivery["last_failure"])
        self.assertEqual("write_uncertain", attempt["status"])

    async def test_public_replace_and_illegal_dependencies_fail_closed(self) -> None:
        with self.assertRaises(NsValidationError):
            StateStoreDeliveryScheduler(
                repository=self.repositories.admission,
                registry_repository=self.repositories.registry,
                clock=self.clock,
            )
        with self.assertRaises(NsValidationError):
            StateStoreDeliveryPayloadAuthority(
                repository=self.repositories.scheduler,
            )
        with self.assertRaises(NsValidationError):
            StateStoreDeliveryAdmissionStore(
                repository=self.repositories.payload,
                registry_repository=self.repositories.registry,
            )
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

    async def test_fix05_coordinator_precheck_and_write_failure_leave_no_renew_task(
        self,
    ) -> None:
        sequence = itertools.count()

        async def run(*, targets, writer):
            supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
            coordinator = LocalDeliveryDispatchCoordinator(
                task_supervisor=supervisor,
                scheduler=self.scheduler,
                policy=dataclasses.replace(
                    self.policy,
                    activation_batch_size=1,
                ),
                runtime_id=self.plan.selected_bindings[0].runtime_id,
                target_resolver=targets,
                payload_validator=_Validator(),
                payload_resolver=_Payloads(),
                transport_writer=writer,
                risk_guard=self.risk_guard,
                identifier_factory=lambda kind: (
                    f"{kind}-failure-{next(sequence)}"
                ),
                clock=self.clock,
            )
            self.assertTrue(coordinator.schedule(tenant_id=self.tenant_id))
            dispatch_name = next(
                name for name in supervisor.task_names
                if name.startswith("p11-local-dispatch:")
            )
            await supervisor.get_task(dispatch_name)
            self.assertFalse(any(
                name.startswith("p11-lease-renew:")
                for name in supervisor.pending_task_names
            ))
            self.assertEqual((), supervisor.failures)
            report = await supervisor.shutdown()
            self.assertTrue(report.clean)

        await run(targets=_Targets(active=False), writer=_Writer())
        await run(
            targets=_Targets(),
            writer=_Writer(error=ConnectionError("write failed")),
        )


if __name__ == "__main__":
    unittest.main()
