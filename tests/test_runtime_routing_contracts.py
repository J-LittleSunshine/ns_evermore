# -*- coding: utf-8 -*-
from __future__ import annotations

import dataclasses
import unittest
from pathlib import Path

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import (
    NsRuntimeEnvelopeSchemaError,
    NsRuntimeRouteRejectedError,
    NsValidationError,
)
from ns_common.iam import IamPrincipalType, PermissionInvalidation
from ns_common.time import ControlledClock
from ns_runtime.processor import (
    DefaultProcessorErrorMapper,
    DeterministicTestAuditSink,
    EventBus,
    InterfaceOnlyIdempotencyPrecheck,
    InterfaceOnlyRateLimitEntry,
    PassthroughResponseFinalizer,
    ProcessorContext,
    ProcessorDependencies,
    ProcessorTraceReference,
    RoutingPreparationOutcome,
    AuthorizationDecisionEvidence,
)
from ns_runtime.processor.testing import (
    issue_contract_test_authorization_evidence,
)
from ns_runtime.processor.integration import (
    DeterministicTestProcessorAuthorization,
    IamProcessorAuthorization,
)
from ns_runtime.iam import AuthorizationMode, MessageAuthorizationService
from ns_runtime.protocol import (
    BUILTIN_MESSAGE_REGISTRY,
    MessageAuditLevel,
    MessageCategory,
    MessageGroup,
    MessageTypeRegistry,
    RoutingRequirement,
    TargetGroup,
)
from ns_runtime.routing import (
    DefaultLocalRoutingPolicy,
    LocalRoutingPreparation,
    RequestedRoutingIntent,
    ResolvedRoutingPlan,
    RoutingFailureReason,
    RoutingPolicyInvocation,
    RoutingStrategy,
)

from tests.test_runtime_processor_pipeline import NOW, _envelope, _session
from tests.test_runtime_routing import RUNTIME_ID, _router, _snapshot, _SnapshotIndex, _routing_context
from tests.test_runtime_iam_authorization import _Iam


class _CountingPolicy(DefaultLocalRoutingPolicy):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def decide(self, *args, **kwargs):
        self.calls += 1
        return super().decide(*args, **kwargs)


class _MismatchedInvocationPolicy(DefaultLocalRoutingPolicy):
    def __init__(self, replacement: RoutingPolicyInvocation) -> None:
        super().__init__()
        self.replacement = replacement
        self.calls = 0

    def decide(self, invocation):
        self.calls += 1
        return super().decide(self.replacement)


class TargetGroupContractTestCase(unittest.TestCase):
    def test_registry_freezes_explicit_routing_requirement(self) -> None:
        required = {
            contract.message_type
            for contract in BUILTIN_MESSAGE_REGISTRY.contracts
            if contract.routing_requirement is RoutingRequirement.TARGET_REQUIRED
        }
        self.assertEqual(
            {"task.dispatch", "task.result", "task.callback", "stream.start"},
            required,
        )
        self.assertTrue(all(
            isinstance(contract.routing_requirement, RoutingRequirement)
            for contract in BUILTIN_MESSAGE_REGISTRY.contracts
        ))

    def test_valid_strategy_and_rebind_matrix(self) -> None:
        cases = (
            TargetGroup(kind="connection", connection_id="connection-a"),
            TargetGroup(kind="identity", identity="identity-a", rebind_policy="same_identity"),
            TargetGroup(kind="capability", capabilities=("cap.a",), rebind_policy="same_capability"),
            TargetGroup(kind="tenant", tenant_id="tenant-a", rebind_policy="same_tenant"),
            TargetGroup(kind="tenant", tenant_id="tenant-a", multi_connection_policy="all"),
            TargetGroup(
                kind="tenant", tenant_id="tenant-a", multi_connection_policy="quorum",
                fanout_count=3, required_count=2,
            ),
            TargetGroup(
                kind="tenant", tenant_id="tenant-a",
                multi_connection_policy="all_required",
            ),
            TargetGroup(
                kind="tenant", tenant_id="tenant-a",
                multi_connection_policy="weighted_subset", subset_size=2,
            ),
            TargetGroup(
                kind="broadcast", scope="tenant", tenant_id="tenant-a",
                multi_connection_policy="broadcast",
            ),
        )
        self.assertEqual(9, len(cases))

    def test_full_negative_combination_matrix(self) -> None:
        cases = (
            ({"kind": "unknown", "identity": "i"}, "unsupported_target_kind"),
            ({"kind": "connection"}, "required_for_target_kind"),
            ({"kind": "identity", "identity": "i", "connection_id": "c"}, "field_not_allowed_for_kind"),
            ({"kind": "connection", "connection_id": "c", "multi_connection_policy": "all"}, "connection_requires_single"),
            ({"kind": "broadcast", "scope": "runtime", "tenant_id": "t", "multi_connection_policy": "broadcast"}, "tenant_broadcast_required"),
            ({"kind": "broadcast", "scope": "tenant", "tenant_id": "t"}, "broadcast_strategy_required"),
            ({"kind": "broadcast", "scope": "tenant", "tenant_id": "t", "multi_connection_policy": "broadcast", "rebind_policy": "same_tenant"}, "field_not_allowed_for_kind"),
            ({"kind": "tenant", "tenant_id": "t", "multi_connection_policy": "quorum", "fanout_count": 1}, "quorum_counts_required"),
            ({"kind": "tenant", "tenant_id": "t", "multi_connection_policy": "quorum", "fanout_count": 1, "required_count": 2}, "quorum_count_order"),
            ({"kind": "tenant", "tenant_id": "t", "multi_connection_policy": "weighted_subset"}, "subset_size_required"),
            ({"kind": "tenant", "tenant_id": "t", "fanout_count": 1}, "field_not_allowed_for_strategy"),
            ({"kind": "capability", "capabilities": []}, "non_empty_array_required"),
            ({"kind": "capability", "capabilities": ["a", "a"]}, "duplicate_capability"),
            ({"kind": "tenant", "tenant_id": "t", "rebind_policy": "same_component"}, "unsupported_rebind_policy"),
        )
        for values, reason in cases:
            with self.subTest(values=values):
                with self.assertRaises(NsRuntimeEnvelopeSchemaError) as caught:
                    TargetGroup(**values)
                self.assertEqual(reason, caught.exception.details["reason"])

    def test_unknown_field_is_rejected_by_strict_group(self) -> None:
        with self.assertRaises(NsRuntimeEnvelopeSchemaError) as caught:
            TargetGroup.from_mapping({
                "kind": "tenant",
                "tenant_id": "tenant-a",
                "sender_weight": 10,
            })
        self.assertEqual("unknown_field", caught.exception.details["reason"])

    def test_capabilities_are_and_set_and_canonicalized(self) -> None:
        target = TargetGroup(
            kind="capability",
            capabilities=["cap.z", "cap.a"],
        )
        self.assertEqual(("cap.a", "cap.z"), target.capabilities)

    def test_router_has_no_transport_delivery_or_state_store_dependency(self) -> None:
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "ns_runtime" / "routing" / "router.py").read_text(
            encoding="utf-8",
        )
        for forbidden in (
            "ns_runtime.transport",
            "TransportSession",
            "DeliveryRecord",
            "DeliveryAttempt",
            "ns_common.state_store",
            "StateStore(",
            ".send(",
            "TaskSupervisor",
            "EventBus",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


class RoutingPreparationIsolationTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        self.clock = ControlledClock(utc_start=NOW)

    async def asyncTearDown(self) -> None:
        await self.supervisor.shutdown(timeout_seconds=1)

    async def test_feature_disabled_target_message_never_calls_router(self) -> None:
        index = _SnapshotIndex(_snapshot((_routing_context(0),)))
        preparation = LocalRoutingPreparation(router=_router(index, self.clock))
        session = dataclasses.replace(
            _session(),
            tenant_id="tenant-a",
            permission_snapshot_ref="permission-ref",
            permission_version="permission-v1",
        )
        envelope = dataclasses.replace(
            _envelope(),
            message=MessageGroup(
                message_id="message-test",
                type="task.dispatch",
                category="task",
                priority=0,
                created_at="2026-07-22T00:00:00Z",
            ),
            target=TargetGroup(kind="tenant", tenant_id="tenant-a"),
        )
        envelope = dataclasses.replace(
            envelope,
            source=dataclasses.replace(
                envelope.source,
                connection_id=session.connection_id,
                tenant_id=session.tenant_id,
            ),
            auth_context=dataclasses.replace(
                envelope.auth_context,
                permission_snapshot_ref=session.permission_snapshot_ref,
            ),
        )
        dependencies = ProcessorDependencies(
            authorization=DeterministicTestProcessorAuthorization(),
            rate_limit=InterfaceOnlyRateLimitEntry(),
            idempotency=InterfaceOnlyIdempotencyPrecheck(),
            routing=preparation,
            response_finalizer=PassthroughResponseFinalizer(),
            error_mapper=DefaultProcessorErrorMapper(),
            principal_type=IamPrincipalType.CLIENT,
            audit_sink=DeterministicTestAuditSink(),
            event_bus=EventBus(
                task_supervisor=self.supervisor,
                default_timeout_seconds=1,
            ),
            task_supervisor=self.supervisor,
        )
        context = ProcessorContext(
            normalized_envelope=envelope,
            session=session,
            trace=ProcessorTraceReference(value="trace:test"),
            config_version="config-v1",
            policy_version="policy-v1",
            clock=self.clock,
            dependencies=dependencies,
        )
        result = await preparation.prepare(context, None)
        self.assertIs(RoutingPreparationOutcome.NO_ROUTING_REQUIRED, result.outcome)
        self.assertEqual(0, index.snapshot_calls)

    async def test_explicit_cross_tenant_authorization_evidence_is_required(self) -> None:
        target_context = dataclasses.replace(_routing_context(0), tenant_id="tenant-b")
        index = _SnapshotIndex(_snapshot((target_context,)))
        contract = dataclasses.replace(
            BUILTIN_MESSAGE_REGISTRY.require("task.dispatch"),
            feature_enabled=True,
        )
        registry = MessageTypeRegistry((contract,))
        preparation = LocalRoutingPreparation(
            router=_router(index, self.clock),
            protocol_registry=registry,
        )
        session = dataclasses.replace(
            _session(),
            tenant_id="tenant-a",
            permission_snapshot_ref="permission-ref",
            permission_version="permission-v1",
        )
        target = TargetGroup(kind="tenant", tenant_id="tenant-b")
        envelope = dataclasses.replace(
            _envelope(),
            message=MessageGroup(
                message_id="message-test",
                type="task.dispatch",
                category="task",
                priority=0,
                created_at="2026-07-22T00:00:00Z",
            ),
            target=target,
        )
        envelope = dataclasses.replace(
            envelope,
            source=dataclasses.replace(
                envelope.source,
                connection_id=session.connection_id,
                tenant_id=session.tenant_id,
            ),
            auth_context=dataclasses.replace(
                envelope.auth_context,
                permission_snapshot_ref=session.permission_snapshot_ref,
            ),
        )
        authorization = DeterministicTestProcessorAuthorization(
            authorize_cross_tenant=True,
        )
        dependencies = ProcessorDependencies(
            authorization=authorization,
            rate_limit=InterfaceOnlyRateLimitEntry(),
            idempotency=InterfaceOnlyIdempotencyPrecheck(),
            routing=preparation,
            response_finalizer=PassthroughResponseFinalizer(),
            error_mapper=DefaultProcessorErrorMapper(),
            principal_type=IamPrincipalType.CLIENT,
            audit_sink=DeterministicTestAuditSink(),
            event_bus=EventBus(task_supervisor=self.supervisor, default_timeout_seconds=1),
            task_supervisor=self.supervisor,
        )
        context = ProcessorContext(
            normalized_envelope=envelope,
            session=session,
            trace=ProcessorTraceReference(value="trace:test"),
            config_version="config-v1",
            policy_version="policy-v1",
            clock=self.clock,
            dependencies=dependencies,
        )
        evidence = await authorization.authorize(context)
        self.assertIsInstance(evidence, AuthorizationDecisionEvidence)
        self.assertTrue(evidence.cross_tenant_authorized)
        resolved = await preparation.prepare(context, evidence)
        self.assertIs(RoutingPreparationOutcome.RESOLVED, resolved.outcome)
        self.assertIsInstance(resolved.plan, ResolvedRoutingPlan)
        assert isinstance(resolved.plan, ResolvedRoutingPlan)
        self.assertEqual(
            evidence.semantic_decision_reference,
            resolved.plan.iam_decision_reference,
        )
        self.assertEqual(evidence.decision_version, resolved.plan.iam_decision_version)
        self.assertNotEqual(session.permission_snapshot_ref, resolved.plan.iam_decision_reference)

        other_envelope = dataclasses.replace(
            envelope,
            message=dataclasses.replace(
                envelope.message,
                message_id="message-other",
            ),
        )
        other_context = dataclasses.replace(
            context,
            normalized_envelope=other_envelope,
        )
        other_evidence = await authorization.authorize(other_context)
        other_resolved = await preparation.prepare(other_context, other_evidence)
        self.assertIs(RoutingPreparationOutcome.RESOLVED, other_resolved.outcome)
        assert isinstance(other_resolved.plan, ResolvedRoutingPlan)
        self.assertNotEqual(
            evidence.message_binding_reference,
            other_evidence.message_binding_reference,
        )
        self.assertEqual(
            evidence.semantic_decision_reference,
            other_evidence.semantic_decision_reference,
        )
        self.assertEqual(
            resolved.plan.decision_fingerprint,
            other_resolved.plan.decision_fingerprint,
        )

        intent = resolved.plan.policy_decision.invocation.requested_intent
        mismatched_invocations = (
            RoutingPolicyInvocation.from_contract(
                contract=contract,
                requested_intent=RequestedRoutingIntent.from_target(
                    TargetGroup(kind="tenant", tenant_id="tenant-other"),
                ),
                config_version=context.config_version,
                policy_version=context.policy_version,
            ),
            RoutingPolicyInvocation.from_contract(
                contract=BUILTIN_MESSAGE_REGISTRY.require("stream.start"),
                requested_intent=intent,
                config_version=context.config_version,
                policy_version=context.policy_version,
            ),
            RoutingPolicyInvocation.from_contract(
                contract=dataclasses.replace(
                    contract,
                    category=MessageCategory.CONTROL,
                    audit_level=MessageAuditLevel.SECURITY,
                ),
                requested_intent=intent,
                config_version=context.config_version,
                policy_version=context.policy_version,
            ),
            RoutingPolicyInvocation.from_contract(
                contract=contract,
                requested_intent=intent,
                config_version="config-v9",
                policy_version=context.policy_version,
            ),
            RoutingPolicyInvocation.from_contract(
                contract=contract,
                requested_intent=intent,
                config_version=context.config_version,
                policy_version="policy-v9",
            ),
        )
        for replacement in mismatched_invocations:
            with self.subTest(invocation_mismatch=replacement):
                mismatch_index = _SnapshotIndex(_snapshot((target_context,)))
                mismatch_policy = _MismatchedInvocationPolicy(replacement)
                mismatch_preparation = LocalRoutingPreparation(
                    router=_router(mismatch_index, self.clock),
                    protocol_registry=registry,
                    policy=mismatch_policy,
                )
                mismatch_result = await mismatch_preparation.prepare(
                    context,
                    evidence,
                )
                self.assertIs(
                    RoutingPreparationOutcome.REJECTED,
                    mismatch_result.outcome,
                )
                self.assertIs(
                    RoutingFailureReason.POLICY_DECISION_MISMATCH,
                    mismatch_result.failure.reason,
                )
                self.assertEqual(1, mismatch_policy.calls)
                self.assertEqual(0, mismatch_index.snapshot_calls)

        security_contract = dataclasses.replace(
            contract,
            required_capabilities=("runtime.management",),
        )
        security_registry = MessageTypeRegistry((security_contract,))
        malicious_index = _SnapshotIndex(_snapshot((target_context,)))
        malicious_policy = _MismatchedInvocationPolicy(
            resolved.plan.policy_decision.invocation,
        )
        malicious_result = await LocalRoutingPreparation(
            router=_router(malicious_index, self.clock),
            protocol_registry=security_registry,
            policy=malicious_policy,
        ).prepare(context, evidence)
        self.assertIs(RoutingPreparationOutcome.REJECTED, malicious_result.outcome)
        self.assertIs(
            RoutingFailureReason.POLICY_DECISION_MISMATCH,
            malicious_result.failure.reason,
        )
        self.assertFalse(malicious_policy.replacement.security_sensitive)
        self.assertEqual(0, malicious_index.snapshot_calls)

        before = index.snapshot_calls
        mismatch_cases = (
            _bound_replace(
                evidence,
                session_permission_snapshot_ref="permission-other",
                effective_permission_snapshot_ref="permission-other",
            ),
            _bound_replace(
                evidence,
                session_permission_snapshot_version="permission-v9",
            ),
        )
        for mismatch in mismatch_cases:
            with self.subTest(permission_evidence=mismatch):
                counting_policy = _CountingPolicy()
                isolated = LocalRoutingPreparation(
                    router=_router(index, self.clock),
                    protocol_registry=registry,
                    policy=counting_policy,
                )
                mismatch_result = await isolated.prepare(context, mismatch)
                self.assertIs(
                    RoutingPreparationOutcome.REJECTED,
                    mismatch_result.outcome,
                )
                self.assertIs(
                    RoutingFailureReason.AUTHORIZATION_EVIDENCE_MISMATCH,
                    mismatch_result.failure.reason,
                )
                self.assertEqual(0, counting_policy.calls)
                self.assertEqual(before, index.snapshot_calls)

        for invalid_change in (
            {"effective_permission_snapshot_ref": "permission-other"},
            {"effective_permission_snapshot_version": "permission-v9"},
            {"session_permission_snapshot_ref": ""},
            {"session_permission_snapshot_version": ""},
            {"message_binding_reference": "sha256:" + "0" * 64},
            {"decision_reason": "different_allow_reason"},
        ):
            with self.subTest(invalid_evidence=invalid_change), self.assertRaises(
                NsValidationError,
            ):
                dataclasses.replace(evidence, **invalid_change)

        policy_rejected = await LocalRoutingPreparation(
            router=_router(index, self.clock),
            protocol_registry=registry,
            policy=DefaultLocalRoutingPolicy(
                allowed_strategies=frozenset({RoutingStrategy.ALL}),
            ),
        ).prepare(context, evidence)
        self.assertIs(RoutingPreparationOutcome.REJECTED, policy_rejected.outcome)
        self.assertIs(
            RoutingFailureReason.STRATEGY_NOT_PERMITTED,
            policy_rejected.failure.reason,
        )
        self.assertIsInstance(
            policy_rejected.failure.public_error(),
            NsRuntimeRouteRejectedError,
        )
        self.assertEqual(before, index.snapshot_calls)

        unauthorized = _bound_replace(
            evidence,
            cross_tenant_authorized=False,
            effective_tenant_id=session.tenant_id,
        )
        rejected = await preparation.prepare(context, unauthorized)
        self.assertIs(RoutingPreparationOutcome.REJECTED, rejected.outcome)
        self.assertIs(
            RoutingFailureReason.AUTHORIZATION_EVIDENCE_MISMATCH,
            rejected.failure.reason,
        )
        self.assertEqual(before, index.snapshot_calls)

        unrelated = _bound_replace(
            evidence,
            message_reference="sha256:1111111111111111",
        )
        self.assertEqual(
            evidence.semantic_decision_reference,
            unrelated.semantic_decision_reference,
        )
        self.assertNotEqual(
            evidence.message_binding_reference,
            unrelated.message_binding_reference,
        )
        cross_message_index = _SnapshotIndex(_snapshot((target_context,)))
        cross_message_policy = _CountingPolicy()
        rejected_message = await LocalRoutingPreparation(
            router=_router(cross_message_index, self.clock),
            protocol_registry=registry,
            policy=cross_message_policy,
        ).prepare(context, unrelated)
        self.assertIs(RoutingPreparationOutcome.REJECTED, rejected_message.outcome)
        self.assertIs(
            RoutingFailureReason.AUTHORIZATION_EVIDENCE_MISMATCH,
            rejected_message.failure.reason,
        )
        self.assertEqual(0, cross_message_policy.calls)
        self.assertEqual(0, cross_message_index.snapshot_calls)

    async def test_iam_refresh_binds_session_and_effective_snapshots(self) -> None:
        contract = dataclasses.replace(
            BUILTIN_MESSAGE_REGISTRY.require("task.dispatch"),
            feature_enabled=True,
        )
        registry = MessageTypeRegistry((contract,))
        session = _session()
        target = TargetGroup(kind="tenant", tenant_id=session.tenant_id)
        envelope = dataclasses.replace(
            _envelope(),
            message=MessageGroup(
                message_id="message-refresh",
                type="task.dispatch",
                category="task",
                priority=0,
                created_at="2026-07-22T00:00:00Z",
            ),
            target=target,
        )
        envelope = dataclasses.replace(
            envelope,
            source=dataclasses.replace(
                envelope.source,
                connection_id=session.connection_id,
                tenant_id=session.tenant_id,
            ),
            auth_context=dataclasses.replace(
                envelope.auth_context,
                permission_snapshot_ref=session.permission_snapshot_ref,
            ),
        )
        refresh_calls = 0

        async def refresh(snapshot):
            nonlocal refresh_calls
            refresh_calls += 1
            return dataclasses.replace(
                snapshot,
                permission_digest="sha256:refreshed",
                permission_version="version:refreshed",
            )

        iam = _Iam([True], self.clock)
        service = MessageAuthorizationService.for_contract_tests(
            iam_client=iam,
            clock=self.clock,
            mode=AuthorizationMode.CACHE,
            cache_ttl_seconds=60,
            snapshot_refresher=refresh,
        )
        service.invalidate(PermissionInvalidation(
            permission_snapshot_ref=session.permission_snapshot_ref,
            previous_version=session.permission_version,
            current_version="version:refreshed",
            invalidated_at=NOW,
            reason="role_changed",
        ))
        target_context = dataclasses.replace(
            _routing_context(0),
            tenant_id=session.tenant_id,
        )
        index = _SnapshotIndex(_snapshot((target_context,)))
        preparation = LocalRoutingPreparation(
            router=_router(index, self.clock),
            protocol_registry=registry,
        )
        authorization = IamProcessorAuthorization.for_contract_tests(
            service=service,
            protocol_registry=registry,
        )
        dependencies = ProcessorDependencies(
            authorization=authorization,
            rate_limit=InterfaceOnlyRateLimitEntry(),
            idempotency=InterfaceOnlyIdempotencyPrecheck(),
            routing=preparation,
            response_finalizer=PassthroughResponseFinalizer(),
            error_mapper=DefaultProcessorErrorMapper(),
            principal_type=IamPrincipalType.CLIENT,
            audit_sink=DeterministicTestAuditSink(),
            event_bus=EventBus(
                task_supervisor=self.supervisor,
                default_timeout_seconds=1,
            ),
            task_supervisor=self.supervisor,
        )
        context = ProcessorContext(
            normalized_envelope=envelope,
            session=session,
            trace=ProcessorTraceReference(value="trace:refresh"),
            config_version="config-v1",
            policy_version="policy-v1",
            clock=self.clock,
            dependencies=dependencies,
        )

        evidence = await authorization.authorize(context)
        self.assertEqual(
            session.permission_version,
            evidence.session_permission_snapshot_version,
        )
        self.assertEqual(
            "version:refreshed",
            evidence.effective_permission_snapshot_version,
        )
        self.assertTrue(evidence.has_valid_binding())
        self.assertEqual(1, refresh_calls)
        resolved = await preparation.prepare(context, evidence)
        self.assertIs(RoutingPreparationOutcome.RESOLVED, resolved.outcome)
        self.assertEqual(1, index.snapshot_calls)
        assert isinstance(resolved.plan, ResolvedRoutingPlan)
        self.assertEqual(
            "version:refreshed",
            resolved.plan.effective_permission_snapshot_version,
        )


def _bound_replace(
    evidence: AuthorizationDecisionEvidence,
    **changes: object,
) -> AuthorizationDecisionEvidence:
    values = {
        item.name: getattr(evidence, item.name)
        for item in dataclasses.fields(AuthorizationDecisionEvidence)
        if not item.name.startswith("_") and item.name not in {
            "message_binding_reference",
            "semantic_decision_reference",
        }
    }
    values.update(changes)
    return issue_contract_test_authorization_evidence(**values)


if __name__ == "__main__":
    unittest.main()
