# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import dataclasses
from datetime import timedelta
import json
import math
import unittest

from ns_common.exceptions import (
    NsRuntimeStateStoreConflictError, NsRuntimeStateStoreUnavailableError,
    NsValidationError,
)
from ns_common.iam import PayloadRefValidationResult
from ns_common.state_store import StateStoreCapabilities
from ns_common.time import ControlledClock
from ns_runtime.delivery import (
    ADMISSION_RESPONSE_VERSION, AdmissionCommitState, AdmissionEmissionObserver, AdmissionOutcome,
    AdmissionPolicy, AdmissionPolicyConfig, AdmissionPriority,
    AdmissionReliability, AdmissionRequest, AdmissionResponseSender,
    AdmissionResult, AdmissionTrace, AtomicAdmissionOutcome,
    AtomicAdmissionResult, DefaultAdmissionPolicy, DeliveryAcceptedResponse,
    DeliveryAdmissionService, DeliveryAdmissionStore, DeliveryEnvelopeAuthority,
    DeliveryRecordStatus,
    DeliverySummaryStatus, DuplicateLifecycle, InlinePayload,
    PayloadDependencyDisposition, PayloadRefClient, PayloadReference,
    RejectionReason, StageSixAdmissionInput, StateStoreDeliveryAdmissionStore,
    cancel_initializing_graph, compute_dedup_evidence_fingerprint,
    emit_admission_result,
    BoundPayloadRefValidationResult,
    delivery_from_dict, delivery_to_dict,
)
from ns_runtime.protocol import (
    AuthContextGroup, MessageGroup, ProtocolGroup, SourceGroup, TargetGroup,
    TraceGroup,
)
from ns_runtime.routing import ResolvedRoutingPlan
from ns_runtime.processor import RoutingPreparationResult

from tests._state_store_contract_model import DeterministicStateStoreContractModel
from tests.test_runtime_connection_binding import UTC_START
from tests.test_runtime_routing import (
    _SnapshotIndex, _request, _router, _routing_context, _snapshot,
)


MESSAGE_ID = "message-delivery-1"
MESSAGE_REFERENCE = "sha256:" + __import__("hashlib").sha256(
    MESSAGE_ID.encode()
).hexdigest()[:16]


def _ids(kind: str, index: int) -> str:
    return f"{kind}:{index}"


def _envelope_authority(plan: ResolvedRoutingPlan) -> DeliveryEnvelopeAuthority:
    return DeliveryEnvelopeAuthority(
        protocol=ProtocolGroup(major=1, minor=0, patch=0),
        message=MessageGroup(
            message_id=MESSAGE_ID,
            type=plan.authorization_evidence.message_type,
            category="task",
            priority=20,
            created_at=UTC_START.isoformat(),
            expires_at=(UTC_START + timedelta(minutes=5)).isoformat(),
            reliability="at_least_once",
        ),
        source=SourceGroup(
            runtime_id="runtime-source", connection_id="connection-source",
            identity_digest="sha256:" + "1" * 64, tenant_id="tenant-a",
            component_type="client", capabilities_digest="sha256:" + "2" * 64,
        ),
        auth_context=AuthContextGroup(
            permission_snapshot_ref=plan.effective_permission_snapshot_ref,
            permission_digest="sha256:" + "3" * 64,
            iam_mode="strict", issued_at=UTC_START.isoformat(),
            expires_at=(UTC_START + timedelta(minutes=5)).isoformat(),
        ),
        trace=TraceGroup(trace_id="trace-original", request_id="request-original"),
    )


async def _plan(count: int = 3) -> ResolvedRoutingPlan:
    contexts = tuple(_routing_context(index) for index in range(count))
    clock = ControlledClock(utc_start=UTC_START)
    target = TargetGroup(
        kind="tenant", tenant_id="tenant-a", multi_connection_policy="all",
    )
    value = await _router(_SnapshotIndex(_snapshot(contexts)), clock).route(
        _request(target, message_reference=MESSAGE_REFERENCE)
    )
    assert isinstance(value, ResolvedRoutingPlan)
    return value


class _PayloadClient(PayloadRefClient):
    def __init__(self, clock, *, invalid_indexes=(), error=None, malicious=False):
        self.clock = clock
        self.invalid_indexes = set(invalid_indexes)
        self.error = error
        self.malicious = malicious
        self.calls = []

    async def validate_payload_ref(self, request):
        self.calls.append(request)
        if self.error:
            raise self.error
        index = len(self.calls) - 1
        if index in self.invalid_indexes:
            value = PayloadRefValidationResult(
                valid=False, reason="unauthorized", revoked=False,
                expires_at=self.clock.utc_now() + timedelta(seconds=30),
            )
        else:
            value = PayloadRefValidationResult(
                valid=True, reason="valid", revoked=False,
                expires_at=self.clock.utc_now() + timedelta(minutes=10),
                object_id=("wrong" if self.malicious else request.object_id),
                version=request.version, checksum=request.checksum,
                tenant_id=request.tenant_id, size_bytes=128,
            )
        return BoundPayloadRefValidationResult(
            result=value,
            request_binding_fingerprint=request.request_binding_fingerprint,
            target_binding_fingerprint=request.target_binding_fingerprint,
        )


class _Store(DeliveryAdmissionStore):
    def __init__(self):
        self.values = []
        self.result_override = None
        self.error = None
        self._winner = None
        self._lock = asyncio.Lock()

    async def initialize(self, value):
        self.values.append(value)
        if self.error:
            raise self.error
        if self.result_override is not None:
            return self.result_override
        async with self._lock:
            if self._winner is None:
                self._winner = value
                return AtomicAdmissionResult(
                    outcome=AtomicAdmissionOutcome.CREATED,
                    root_summary=value.root_summary, dedup=value.dedup,
                )
            return AtomicAdmissionResult(
                outcome=AtomicAdmissionOutcome.DUPLICATE,
                root_summary=None, dedup=self._winner.dedup,
            )


class _FailSecondTransactionStore(DeterministicStateStoreContractModel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transaction_calls = 0

    async def _transact(self, transaction):
        self.transaction_calls += 1
        if self.transaction_calls == 2:
            raise NsRuntimeStateStoreConflictError(details={
                "component": "p10_test", "reason": "second_batch_failure",
            })
        return await super()._transact(transaction)


class _Policy(AdmissionPolicy):
    def __init__(self, replacement=None):
        self.base = DefaultAdmissionPolicy()
        self.replacement = replacement

    def decide(self, request, *, now, config):
        result = self.base.decide(request, now=now, config=config)
        return self.replacement(result) if self.replacement else result


class DeliveryAdmissionTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.clock = ControlledClock(utc_start=UTC_START)
        self.plan = await _plan()
        self.store = _Store()
        self.payload_client = _PayloadClient(self.clock)
        self.config = AdmissionPolicyConfig(
            config_version="config-v1", policy_version="admission-v1",
            max_inline_bytes=128, max_json_depth=4,
            min_delivery_window_seconds=5, max_ack_timeout_seconds=60,
            dedup_ttl_seconds=120,
        )
        self.service = self._service()

    def _service(self, *, policy=None, store=None, payload_client=None):
        return DeliveryAdmissionService(
            policy=policy or DefaultAdmissionPolicy(),
            policy_config=self.config, store=store or self.store,
            payload_ref_client=payload_client or self.payload_client,
            clock=self.clock, identifier_factory=_ids,
        )

    def _request(self, *, payload=None, expires_delta=30,
                 reliability=AdmissionReliability.AT_LEAST_ONCE):
        stage_six = StageSixAdmissionInput.from_result(
            RoutingPreparationResult.resolved(self.plan)
        )
        return AdmissionRequest.from_stage_six(
            stage_six=stage_six, message_id=MESSAGE_ID,
            tenant_id=self.plan.authorization_evidence.effective_tenant_id,
            source_identity="identity-source",
            authorization_binding_reference=(
                self.plan.authorization_evidence.message_binding_reference
            ),
            envelope_authority=_envelope_authority(self.plan),
            payload=payload or InlinePayload(
                value={"safe": [1, 2]}, media_type="application/json",
                application_limit_bytes=128, transport_limit_bytes=128,
            ),
            requested_priority=AdmissionPriority.CRITICAL,
            requested_reliability=reliability,
            requested_expires_at=self.clock.utc_now() + timedelta(seconds=expires_delta),
            requested_ack_timeout_seconds=90,
            requested_target_strategy=self.plan.requested_strategy,
        )

    async def test_w01_w02_all_accepted_dr1_graph_and_sender_is_only_request(self):
        result = await self.service.admit(
            self._request(), trace=AdmissionTrace(trace_id="trace-1")
        )
        self.assertEqual(AdmissionOutcome.ACCEPTED, result.outcome)
        initialization = self.store.values[0]
        root = initialization.root_summary
        self.assertEqual(DeliverySummaryStatus.PENDING, root.status)
        self.assertEqual(0, root.shard_count)
        self.assertFalse(initialization.shard_summaries)
        self.assertTrue(all(item.summary_id == root.summary_id
                            and item.shard_index is None
                            for item in initialization.deliveries))
        self.assertEqual((3, 3, 0, 3, 0, 0), (
            root.total_count, root.accepted_count, root.rejected_count,
            root.prepared_count, root.active_count, root.inflight_count,
        ))
        self.assertTrue(all(
            item.status is DeliveryRecordStatus.PREPARED
            for item in initialization.deliveries
        ))
        self.assertEqual(60, root.policy_decision.ack_timeout_seconds)
        self.assertIs(root.policy_decision.target_strategy, self.plan.effective_strategy)

    def test_pc1_stage_six_accepts_only_typed_resolved_result(self):
        handoff = StageSixAdmissionInput.from_result(
            RoutingPreparationResult.resolved(self.plan)
        )
        self.assertIs(self.plan, handoff.plan)
        for hostile in (self.plan, {"plan": self.plan}, {"plan_id": self.plan.plan_id}):
            with self.subTest(hostile=type(hostile).__name__):
                with self.assertRaises(NsValidationError):
                    StageSixAdmissionInput.from_result(hostile)
        with self.assertRaises(NsValidationError):
            StageSixAdmissionInput(plan=self.plan)
        with self.assertRaises(NsValidationError):
            dataclasses.replace(handoff, plan=self.plan)
        with self.assertRaises(NsValidationError):
            AdmissionRequest(
                plan=self.plan, message_id=MESSAGE_ID,
                tenant_id="tenant-a", source_identity="identity-source",
                authorization_binding_reference=(
                    self.plan.authorization_evidence.message_binding_reference
                ),
                envelope_authority=_envelope_authority(self.plan),
                payload=InlinePayload(
                    value={}, media_type="application/json",
                    application_limit_bytes=128, transport_limit_bytes=128,
                ),
                requested_priority=None, requested_reliability=None,
                requested_expires_at=self.clock.utc_now() + timedelta(seconds=30),
                requested_ack_timeout_seconds=30,
                requested_target_strategy=self.plan.requested_strategy,
            )

    async def test_w02_expired_and_short_windows_create_failed_summary(self):
        for delta, reason in ((0, RejectionReason.EXPIRED),
                              (2, RejectionReason.WINDOW_TOO_SHORT)):
            store = _Store()
            result = await self._service(store=store).admit(
                self._request(expires_delta=delta),
                trace=AdmissionTrace(trace_id=f"trace-{delta}"),
            )
            self.assertEqual(AdmissionOutcome.REJECTED, result.outcome)
            self.assertEqual(reason, result.response.reason)
            self.assertEqual(DeliverySummaryStatus.FAILED,
                             store.values[0].root_summary.status)
            self.assertFalse(store.values[0].deliveries)

    async def test_w03_inline_size_depth_digest_and_no_plaintext_in_state(self):
        oversized = InlinePayload(
            value="secret-business-plaintext" * 20,
            media_type="application/json", application_limit_bytes=1000,
            transport_limit_bytes=1000,
        )
        rejected = await self.service.admit(
            self._request(payload=oversized), trace=AdmissionTrace(trace_id="trace-size")
        )
        self.assertEqual(RejectionReason.INLINE_TOO_LARGE, rejected.response.reason)
        deep = InlinePayload(
            value={"a": {"b": {"c": {"d": 1}}}},
            media_type="application/json", application_limit_bytes=128,
            transport_limit_bytes=128,
        )
        store = _Store()
        depth = await self._service(store=store).admit(
            self._request(payload=deep), trace=AdmissionTrace(trace_id="trace-depth")
        )
        self.assertEqual(RejectionReason.INLINE_TOO_DEEP, depth.response.reason)
        accepted_store = _Store()
        await self._service(store=accepted_store).admit(
            self._request(), trace=AdmissionTrace(trace_id="trace-digest")
        )
        evidence = accepted_store.values[0].root_summary.payload_evidence
        self.assertRegex(evidence.digest, r"^sha256:[0-9a-f]{64}$")
        with self.assertRaises(NsValidationError):
            dataclasses.replace(evidence, size_bytes=evidence.size_bytes + 1)
        self.assertNotIn("safe", repr(accepted_store.values[0]))

    async def test_fix04_inline_descriptor_rejects_cycle_and_nonfinite_once(self):
        cyclic: list[object] = []
        cyclic.append(cyclic)
        cases = (
            (cyclic, RejectionReason.INLINE_TYPE_INVALID),
            ({"value": math.nan}, RejectionReason.INLINE_TYPE_INVALID),
            ({"a": {"b": {"c": {"d": {"e": 1}}}}},
             RejectionReason.INLINE_TOO_DEEP),
        )
        for position, (value, reason) in enumerate(cases):
            store = _Store()
            result = await self._service(store=store).admit(
                self._request(payload=InlinePayload(
                    value=value,
                    media_type="application/json",
                    application_limit_bytes=128,
                    transport_limit_bytes=128,
                )),
                trace=AdmissionTrace(trace_id=f"trace-invalid-inline-{position}"),
            )
            self.assertIs(AdmissionOutcome.REJECTED, result.outcome)
            self.assertIs(reason, result.response.reason)
            self.assertIs(
                DeliverySummaryStatus.FAILED,
                store.values[0].root_summary.status,
            )
            self.assertFalse(store.values[0].deliveries)
        shared = {"safe": [1, 2]}
        shared_store = _Store()
        shared_result = await self._service(store=shared_store).admit(
            self._request(payload=InlinePayload(
                value=[shared, shared],
                media_type="application/json",
                application_limit_bytes=128,
                transport_limit_bytes=128,
            )),
            trace=AdmissionTrace(trace_id="trace-shared-inline"),
        )
        self.assertIs(AdmissionOutcome.ACCEPTED, shared_result.outcome)

    async def test_w04_w05_payload_ref_partial_invalid_and_dependency_dispositions(self):
        ref = PayloadReference(
            object_id="object:1", version="version:1", checksum="sha256:abcd",
            owner_identity="identity-source",
        )
        client = _PayloadClient(self.clock, invalid_indexes={1})
        store = _Store()
        partial = await self._service(store=store, payload_client=client).admit(
            self._request(payload=ref), trace=AdmissionTrace(trace_id="trace-ref")
        )
        self.assertEqual(AdmissionOutcome.ACCEPTED, partial.outcome)
        self.assertEqual(DeliverySummaryStatus.PENDING,
                         store.values[0].root_summary.status)
        self.assertEqual(2, len(store.values[0].deliveries))
        self.assertEqual(3, len(client.calls))
        for reliability, outcome in (
            (AdmissionReliability.BEST_EFFORT, AdmissionOutcome.REJECTED),
            (AdmissionReliability.AT_LEAST_ONCE, AdmissionOutcome.WAIT_REQUIRED),
            (AdmissionReliability.CRITICAL, AdmissionOutcome.DEAD_LETTER_REQUIRED),
        ):
            failed = await self._service(
                store=_Store(), payload_client=_PayloadClient(
                    self.clock, error=TimeoutError()
                )
            ).admit(
                self._request(payload=ref, reliability=reliability),
                trace=AdmissionTrace(trace_id=f"trace-{reliability.value}"),
            )
            self.assertEqual(outcome, failed.outcome)

    async def test_w06_w07_concurrent_dedup_has_one_created_and_stable_duplicate(self):
        request = self._request()
        results = await asyncio.gather(*(
            self.service.admit(request, trace=AdmissionTrace(trace_id=f"trace-{i}"))
            for i in range(16)
        ))
        self.assertEqual(1, sum(item.outcome is AdmissionOutcome.ACCEPTED for item in results))
        duplicates = [item for item in results if item.outcome is AdmissionOutcome.DUPLICATE]
        self.assertEqual(15, len(duplicates))
        self.assertTrue(all(item.response.lifecycle is DuplicateLifecycle.IN_PROGRESS
                            for item in duplicates))
        self.assertEqual(1, len({item.response.summary_id for item in results}))

    async def test_w07_terminal_duplicates_never_republish(self):
        await self.service.admit(
            self._request(), trace=AdmissionTrace(trace_id="trace-seed")
        )
        seed = self.store.values[0]
        for lifecycle in DuplicateLifecycle:
            values = dict(
                tenant_id=seed.dedup.tenant_id,
                message_id=seed.dedup.message_id,
                target_fingerprint=seed.dedup.target_fingerprint,
                summary_id=seed.dedup.summary_id, lifecycle=lifecycle,
                registered_at=seed.dedup.registered_at,
                expires_at=seed.dedup.expires_at,
            )
            duplicate = dataclasses.replace(
                seed.dedup, lifecycle=lifecycle,
                evidence_fingerprint=compute_dedup_evidence_fingerprint(**values),
            )
            store = _Store()
            store._winner = dataclasses.replace(seed, dedup=duplicate)
            result = await self._service(store=store).admit(
                self._request(), trace=AdmissionTrace(trace_id=f"trace-{lifecycle.value}")
            )
            self.assertEqual(AdmissionOutcome.DUPLICATE, result.outcome)
            self.assertIs(lifecycle, result.response.lifecycle)
            self.assertFalse(any(
                item.outcome is AtomicAdmissionOutcome.CREATED
                for item in (store.result_override,) if item is not None
            ))

    async def test_w08_all_rejected_has_summary_and_zero_delivery(self):
        ref = PayloadReference(
            object_id="object:1", version="version:1", checksum="sha256:abcd",
            owner_identity="identity-source",
        )
        store = _Store()
        result = await self._service(
            store=store, payload_client=_PayloadClient(self.clock,
                                                       invalid_indexes={0, 1, 2})
        ).admit(self._request(payload=ref), trace=AdmissionTrace(trace_id="trace-all-reject"))
        self.assertEqual(AdmissionOutcome.REJECTED, result.outcome)
        self.assertEqual(3, store.values[0].root_summary.rejected_count)
        self.assertFalse(store.values[0].deliveries)

    async def test_w09_store_failure_returns_unavailable_without_false_success(self):
        store = _Store()
        store.error = NsRuntimeStateStoreUnavailableError()
        result = await self._service(store=store).admit(
            self._request(), trace=AdmissionTrace(trace_id="trace-store")
        )
        self.assertEqual(AdmissionOutcome.UNAVAILABLE, result.outcome)
        self.assertFalse(result.committed)

    async def test_w10_fanout_boundaries_4999_5000_5001(self):
        for count, expected_shards in ((4999, 0), (5000, 0), (5001, 6)):
            plan = await _plan(count)
            self.plan = plan
            store = _Store()
            result = await self._service(store=store).admit(
                self._request(), trace=AdmissionTrace(trace_id=f"trace-{count}")
            )
            self.assertEqual(AdmissionOutcome.ACCEPTED, result.outcome)
            initialization = store.values[0]
            self.assertEqual(expected_shards, len(initialization.shard_summaries))
            self.assertEqual(500, initialization.initialization_batch_size)
            self.assertEqual(count, len(initialization.deliveries))

    async def test_fix03_custom_fanout_policy_and_inline_fingerprint(self):
        plan = await _plan(3)
        self.plan = plan
        config = dataclasses.replace(
            self.config, fanout_shard_threshold=2, shard_bucket_size=2,
            initialization_batch_size=2, activation_batch_size=1,
        )
        first_store = _Store()
        first = DeliveryAdmissionService(
            policy=DefaultAdmissionPolicy(), policy_config=config,
            store=first_store, payload_ref_client=self.payload_client,
            clock=self.clock, identifier_factory=_ids,
        )
        await first.admit(
            self._request(payload=InlinePayload(
                value={"content": "one"}, media_type="application/json",
                application_limit_bytes=128, transport_limit_bytes=128,
            )), trace=AdmissionTrace(trace_id="trace-custom-one"),
        )
        graph = first_store.values[0]
        self.assertEqual(2, len(graph.shard_summaries))
        self.assertEqual(2, graph.initialization_batch_size)
        self.assertEqual((2, 2, 2, 1), (
            graph.root_summary.policy_decision.fanout_shard_threshold,
            graph.root_summary.policy_decision.shard_bucket_size,
            graph.root_summary.policy_decision.initialization_batch_size,
            graph.root_summary.policy_decision.activation_batch_size,
        ))
        second_store = _Store()
        second = DeliveryAdmissionService(
            policy=DefaultAdmissionPolicy(), policy_config=config,
            store=second_store, payload_ref_client=self.payload_client,
            clock=self.clock, identifier_factory=_ids,
        )
        await second.admit(
            self._request(payload=InlinePayload(
                value={"content": "two"}, media_type="application/json",
                application_limit_bytes=128, transport_limit_bytes=128,
            )), trace=AdmissionTrace(trace_id="trace-custom-two"),
        )
        self.assertNotEqual(
            graph.root_summary.policy_decision.request_fingerprint,
            second_store.values[0].root_summary.policy_decision.request_fingerprint,
        )

    async def test_fix03_target_replay_and_legacy_schema_fail_closed(self):
        class ReplayClient(_PayloadClient):
            async def validate_payload_ref(self, request):
                result = await super().validate_payload_ref(request)
                return dataclasses.replace(
                    result, target_binding_fingerprint="sha256:" + "0" * 64,
                )

        ref = PayloadReference(
            object_id="object:1", version="version:1", checksum="sha256:abcd",
            owner_identity="identity-source",
        )
        with self.assertRaises(NsValidationError):
            await self._service(
                store=_Store(), payload_client=ReplayClient(self.clock),
            ).admit(
                self._request(payload=ref),
                trace=AdmissionTrace(trace_id="trace-replay"),
            )
        await self.service.admit(
            self._request(), trace=AdmissionTrace(trace_id="trace-schema"),
        )
        legacy = delivery_to_dict(self.store.values[0].deliveries[0])
        legacy["schema_version"] = "dr-1"
        with self.assertRaises(NsValidationError) as context:
            delivery_from_dict(legacy)
        self.assertEqual(
            "delivery.schema_migration_required",
            context.exception.details["field"],
        )

    async def test_w11_w12_prepared_never_active_and_cancel_scope_is_closed_enum(self):
        await self.service.admit(
            self._request(), trace=AdmissionTrace(trace_id="trace-prepared")
        )
        root = self.store.values[0].root_summary
        self.assertEqual(0, root.active_count)
        self.assertEqual(0, root.inflight_count)
        with self.assertRaises(NsValidationError):
            dataclasses.replace(root, status="queued")
        for reserved in (
            DeliverySummaryStatus.PARTIAL_ACKED,
            DeliverySummaryStatus.ALL_ACKED,
            DeliverySummaryStatus.PARTIAL_FAILED,
        ):
            with self.subTest(reserved=reserved.value):
                with self.assertRaises(NsValidationError):
                    dataclasses.replace(root, status=reserved)
        with self.assertRaises(NsValidationError):
            dataclasses.replace(self.store.values[0].deliveries[0], status="queued")
        initialization = self.store.values[0]
        initializing_root = dataclasses.replace(
            root, status=DeliverySummaryStatus.INITIALIZING,
            accepted_count=2, prepared_count=2, not_initialized_count=1,
        )
        cancelled_root, cancelled_shards, cancelled_deliveries = (
            cancel_initializing_graph(
                root=initializing_root, shards=(),
                created_deliveries=initialization.deliveries[:2],
                cancelled_at=self.clock.utc_now(),
            )
        )
        self.assertEqual(DeliverySummaryStatus.CANCELLED,
                         cancelled_root.status)
        self.assertEqual((2, 1, 0), (
            cancelled_root.cancelled_count,
            cancelled_root.not_initialized_count,
            cancelled_root.prepared_count,
        ))
        self.assertTrue(all(item.status is DeliveryRecordStatus.CANCELLED
                            for item in cancelled_deliveries))
        self.assertFalse(cancelled_shards)
        with self.assertRaises(NsValidationError):
            cancel_initializing_graph(
                root=cancelled_root, shards=cancelled_shards,
                created_deliveries=cancelled_deliveries,
                cancelled_at=self.clock.utc_now(),
            )

    async def test_w13_response_is_lightweight_and_exact(self):
        result = await self.service.admit(
            self._request(), trace=AdmissionTrace(trace_id="trace-response")
        )
        self.assertEqual({"message_id", "summary_id", "accepted_at",
                          "status_query_hint", "trace"},
                         set(result.response.to_wire()))
        self.assertNotIn("delivery_id", repr(result.response.to_wire()))

    async def test_public_replace_and_malicious_dependencies_fail_closed(self):
        accepted_result = await self.service.admit(
            self._request(), trace=AdmissionTrace(trace_id="trace-base")
        )
        root = self.store.values[0].root_summary
        with self.assertRaises(NsValidationError):
            dataclasses.replace(root, accepted_count=2)
        with self.assertRaises(NsValidationError):
            dataclasses.replace(accepted_result, schema_version="forged")
        with self.assertRaises(NsValidationError):
            dataclasses.replace(self.store.values[0], schema_version="forged")
        initialization = self.store.values[0]
        duplicate_target = dataclasses.replace(
            initialization.deliveries[1],
            target_index=initialization.deliveries[0].target_index,
        )
        with self.assertRaises(NsValidationError):
            dataclasses.replace(
                initialization,
                deliveries=(initialization.deliveries[0], duplicate_target)
                + initialization.deliveries[2:],
            )
        with self.assertRaises(NsValidationError):
            dataclasses.replace(initialization, payload_body=b'{}')
        with self.assertRaises(NsValidationError):
            dataclasses.replace(self.config, activation_batch_size=1001)
        bad_policy = _Policy(lambda value: dataclasses.replace(
            value, target_strategy=self.plan.requested_strategy
            if self.plan.requested_strategy is not self.plan.effective_strategy
            else "all",
        ))
        with self.assertRaises(NsValidationError):
            await self._service(policy=bad_policy, store=_Store()).admit(
                self._request(), trace=AdmissionTrace(trace_id="trace-policy")
            )
        ref = PayloadReference(
            object_id="object:1", version="version:1", checksum="sha256:abcd",
            owner_identity="identity-source",
        )
        with self.assertRaises(NsValidationError):
            await self._service(
                store=_Store(), payload_client=_PayloadClient(self.clock, malicious=True)
            ).admit(self._request(payload=ref), trace=AdmissionTrace(trace_id="trace-payload"))
        malicious_store = _Store()
        malicious_store.result_override = object()
        with self.assertRaises(NsValidationError):
            await self._service(store=malicious_store).admit(
                self._request(), trace=AdmissionTrace(trace_id="trace-store-malicious")
            )


class _Sender(AdmissionResponseSender):
    async def send(self, response):
        raise ConnectionError("contains-sensitive-peer-and-payload")


class _Observer(AdmissionEmissionObserver):
    def __init__(self):
        self.outcomes = []

    def response_emission_failed(self, *, outcome):
        self.outcomes.append(outcome)


class DeliveryAdmissionInfrastructureTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_w09_state_store_atomic_documents_are_evidence_only(self):
        clock = ControlledClock(utc_start=UTC_START)
        plan = await _plan()
        model = DeterministicStateStoreContractModel(
            clock=clock, capabilities=StateStoreCapabilities.p10_contract(),
        )
        await model.open()
        store = StateStoreDeliveryAdmissionStore(model)
        service = DeliveryAdmissionService(
            policy=DefaultAdmissionPolicy(),
            policy_config=AdmissionPolicyConfig(
                config_version="c1", policy_version="p1",
            ),
            store=store, payload_ref_client=_PayloadClient(clock),
            clock=clock, identifier_factory=_ids,
        )
        stage_six = StageSixAdmissionInput.from_result(
            RoutingPreparationResult.resolved(plan)
        )
        request = AdmissionRequest.from_stage_six(
            stage_six=stage_six, message_id=MESSAGE_ID,
            tenant_id=plan.authorization_evidence.effective_tenant_id,
            source_identity="identity-source",
            authorization_binding_reference=plan.authorization_evidence.message_binding_reference,
            envelope_authority=_envelope_authority(plan),
            payload=InlinePayload(
                value={"business_secret": "never-store-me"},
                media_type="application/json", application_limit_bytes=4096,
                transport_limit_bytes=4096,
            ),
            requested_priority=None, requested_reliability=None,
            requested_expires_at=clock.utc_now() + timedelta(seconds=30),
            requested_ack_timeout_seconds=30,
            requested_target_strategy=plan.requested_strategy,
        )
        result = await service.admit(request, trace=AdmissionTrace(trace_id="trace-state"))
        self.assertEqual(AdmissionOutcome.ACCEPTED, result.outcome)
        persisted = b" ".join(record.document.payload for record in model.records.values())
        self.assertNotIn(b"never-store-me", persisted)
        self.assertNotIn(b"business_secret", persisted)
        self.assertEqual(2, model.write_count)
        await model.close()

    async def test_w10_w12_real_second_batch_failure_cancels_prepared(self):
        clock = ControlledClock(utc_start=UTC_START)
        plan = await _plan(501)
        model = _FailSecondTransactionStore(
            clock=clock, capabilities=StateStoreCapabilities.p10_contract(),
        )
        await model.open()
        service = DeliveryAdmissionService(
            policy=DefaultAdmissionPolicy(),
            policy_config=AdmissionPolicyConfig(
                config_version="c1", policy_version="p1",
            ),
            store=StateStoreDeliveryAdmissionStore(model),
            payload_ref_client=_PayloadClient(clock), clock=clock,
            identifier_factory=_ids,
        )
        stage_six = StageSixAdmissionInput.from_result(
            RoutingPreparationResult.resolved(plan)
        )
        request = AdmissionRequest.from_stage_six(
            stage_six=stage_six, message_id=MESSAGE_ID,
            tenant_id=plan.authorization_evidence.effective_tenant_id,
            source_identity="identity-source",
            authorization_binding_reference=plan.authorization_evidence.message_binding_reference,
            envelope_authority=_envelope_authority(plan),
            payload=InlinePayload(
                value={"v": 1}, media_type="application/json",
                application_limit_bytes=4096, transport_limit_bytes=4096,
            ),
            requested_priority=None, requested_reliability=None,
            requested_expires_at=clock.utc_now() + timedelta(seconds=30),
            requested_ack_timeout_seconds=30,
            requested_target_strategy=plan.requested_strategy,
        )
        result = await service.admit(
            request, trace=AdmissionTrace(trace_id="trace-batch-failure")
        )
        self.assertEqual(AdmissionOutcome.REJECTED, result.outcome)
        self.assertTrue(result.committed)
        self.assertEqual(3, model.transaction_calls)
        documents = [json.loads(record.document.payload)
                     for record in model.records.values()]
        root = next(item for item in documents
                    if item.get("summary_id") == "summary:0"
                    and "status" in item)
        self.assertEqual("cancelled", root["status"])
        self.assertEqual(500, root["cancelled_count"])
        self.assertEqual(1, root["not_initialized_count"])
        self.assertEqual(500, sum(
            item.get("status") == "cancelled"
            and "delivery_id" in item for item in documents
        ))
        dedup = next(item for item in documents if "lifecycle" in item)
        self.assertEqual("cancelled", dedup["lifecycle"])
        await model.close()

    async def test_w06_w09_real_state_store_concurrency_and_atomic_failure(self):
        clock = ControlledClock(utc_start=UTC_START)
        plan = await _plan()
        model = DeterministicStateStoreContractModel(
            clock=clock, capabilities=StateStoreCapabilities.p10_contract(),
        )
        await model.open()
        service = DeliveryAdmissionService(
            policy=DefaultAdmissionPolicy(),
            policy_config=AdmissionPolicyConfig(
                config_version="c1", policy_version="p1",
            ),
            store=StateStoreDeliveryAdmissionStore(model),
            payload_ref_client=_PayloadClient(clock), clock=clock,
            identifier_factory=_ids,
        )
        stage_six = StageSixAdmissionInput.from_result(
            RoutingPreparationResult.resolved(plan)
        )
        request = AdmissionRequest.from_stage_six(
            stage_six=stage_six, message_id=MESSAGE_ID,
            tenant_id=plan.authorization_evidence.effective_tenant_id,
            source_identity="identity-source",
            authorization_binding_reference=plan.authorization_evidence.message_binding_reference,
            envelope_authority=_envelope_authority(plan),
            payload=InlinePayload(
                value={"v": 1}, media_type="application/json",
                application_limit_bytes=4096, transport_limit_bytes=4096,
            ),
            requested_priority=None, requested_reliability=None,
            requested_expires_at=clock.utc_now() + timedelta(seconds=30),
            requested_ack_timeout_seconds=30,
            requested_target_strategy=plan.requested_strategy,
        )
        results = await asyncio.gather(*(
            service.admit(request, trace=AdmissionTrace(trace_id=f"trace-real-{i}"))
            for i in range(8)
        ))
        self.assertEqual(1, sum(item.outcome is AdmissionOutcome.ACCEPTED
                                for item in results))
        self.assertEqual(7, sum(item.outcome is AdmissionOutcome.DUPLICATE
                                for item in results))
        await model.close()

        failing = DeterministicStateStoreContractModel(
            clock=clock, capabilities=StateStoreCapabilities.p10_contract(),
        )
        await failing.open()
        failing.write_error = RuntimeError("atomic-failure")
        failed_service = DeliveryAdmissionService(
            policy=DefaultAdmissionPolicy(),
            policy_config=AdmissionPolicyConfig(
                config_version="c1", policy_version="p1",
            ),
            store=StateStoreDeliveryAdmissionStore(failing),
            payload_ref_client=_PayloadClient(clock), clock=clock,
            identifier_factory=_ids,
        )
        failed = await failed_service.admit(
            request, trace=AdmissionTrace(trace_id="trace-atomic-failure")
        )
        self.assertEqual(AdmissionOutcome.UNAVAILABLE, failed.outcome)
        self.assertIs(AdmissionCommitState.INDETERMINATE, failed.commit_state)
        self.assertFalse(failing.records)
        await failing.close()

    async def test_w14_response_failure_does_not_rollback_committed_result(self):
        response = DeliveryAcceptedResponse(
            schema_version=ADMISSION_RESPONSE_VERSION,
            message_id="message:1", summary_id="summary:1",
            accepted_at=UTC_START,
            status_query_hint="delivery.summary:summary:1",
            trace=AdmissionTrace(trace_id="trace-emit"),
        )
        result = AdmissionResult(
            outcome=AdmissionOutcome.ACCEPTED, response=response,
            commit_state=AdmissionCommitState.COMMITTED,
        )
        observer = _Observer()
        self.assertFalse(await emit_admission_result(
            result, sender=_Sender(), observer=observer,
        ))
        self.assertEqual([AdmissionOutcome.ACCEPTED], observer.outcomes)
        self.assertTrue(result.committed)


if __name__ == "__main__":
    unittest.main()
