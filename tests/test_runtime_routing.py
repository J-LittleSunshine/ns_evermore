# -*- coding: utf-8 -*-
from __future__ import annotations

import dataclasses
import unittest
from types import MappingProxyType
from uuid import UUID

from ns_common.config.groups.runtime import NsRuntimeRoutingConfig
from ns_common.exceptions import (
    NsRuntimeRouteRejectedError,
    NsRuntimeRouteUnavailableError,
    NsValidationError,
)
from ns_common.identifiers import IdentifierFactory
from ns_common.time import ControlledClock
from ns_runtime.connection import (
    ConnectionIndexEntrySnapshot,
    ConnectionRoutingEligibility,
    LocalConnectionIndex,
    LocalConnectionIndexSnapshot,
    LogicalConnectionState,
)
from ns_runtime.processor import AuthorizationDecisionEvidence
from ns_runtime.protocol import MessageAuditLevel, MessageCategory, TargetGroup
from ns_runtime.routing import (
    DefaultLocalRoutingPolicy,
    LocalRouter,
    LocalRoutingConsistencyPolicy,
    RebindPolicy,
    RequestedRoutingIntent,
    ResolvedRoutingPlan,
    RoutingFailureReason,
    RoutingFailureReport,
    RoutingFailureOutcome,
    RoutingRequest,
    RoutingRiskMetadata,
    RoutingStrategy,
    StrategyParameters,
)

from tests.test_runtime_connection_binding import UTC_START, _context, _transport


RUNTIME_ID = "runtime_123e4567e89b42d3a456426614174900"
MESSAGE_REF = "sha256:0123456789abcdef"


class _SnapshotIndex(LocalConnectionIndex):
    def __init__(self, snapshot: LocalConnectionIndexSnapshot) -> None:
        super().__init__()
        self._provided_snapshot = snapshot
        self.snapshot_calls = 0

    async def snapshot(self) -> LocalConnectionIndexSnapshot:
        self.snapshot_calls += 1
        return self._provided_snapshot


class LocalRouterTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.clock = ControlledClock(utc_start=UTC_START)
        self.contexts = tuple(_routing_context(index) for index in range(3))
        self.snapshot = _snapshot(self.contexts)
        self.index = _SnapshotIndex(self.snapshot)
        self.router = _router(self.index, self.clock)

    async def test_all_target_kinds_use_one_snapshot(self) -> None:
        targets = (
            TargetGroup(
                kind="connection",
                connection_id=self.contexts[0].connection_id,
                connection_epoch=0,
            ),
            TargetGroup(kind="identity", identity="identity-shared"),
            TargetGroup(kind="tenant", tenant_id="tenant-a"),
            TargetGroup(kind="capability", capabilities=("cap.shared",)),
            TargetGroup(kind="component_type", component_type="worker"),
            TargetGroup(kind="runtime", runtime_id=RUNTIME_ID),
            TargetGroup(
                kind="broadcast",
                scope="tenant",
                tenant_id="tenant-a",
                multi_connection_policy="broadcast",
            ),
        )
        for target in targets:
            with self.subTest(kind=target.kind):
                before = self.index.snapshot_calls
                decision = await self.router.route(_request(target))
                self.assertIsInstance(decision, ResolvedRoutingPlan)
                self.assertEqual(before + 1, self.index.snapshot_calls)

    async def test_strategy_matrix_is_selection_only(self) -> None:
        cases = (
            ("single", {}, 1),
            ("all", {}, 3),
            ("quorum", {"fanout_count": 2, "required_count": 1}, 2),
            ("all_required", {}, 3),
            ("weighted_subset", {"subset_size": 2}, 2),
        )
        for strategy, options, expected in cases:
            with self.subTest(strategy=strategy):
                target = TargetGroup(
                    kind="tenant",
                    tenant_id="tenant-a",
                    multi_connection_policy=strategy,
                    **options,
                )
                decision = await self.router.route(_request(target))
                self.assertIsInstance(decision, ResolvedRoutingPlan)
                self.assertEqual(expected, len(decision.selected_bindings))
                self.assertTrue(
                    all(
                        candidate.score is not None
                        for candidate in decision.candidates
                    ),
                )
                if strategy == "quorum":
                    self.assertEqual(1, decision.strategy_parameters.required_count)
                self.assertFalse(hasattr(decision, "ack_count"))

    async def test_deterministic_fingerprint_and_tie_break_ignore_plan_id(self) -> None:
        target = TargetGroup(kind="tenant", tenant_id="tenant-a")
        first = await self.router.route(_request(target))
        second = await self.router.route(_request(target))
        assert isinstance(first, ResolvedRoutingPlan)
        assert isinstance(second, ResolvedRoutingPlan)
        self.assertNotEqual(first.plan_id, second.plan_id)
        self.assertEqual(first.decision_fingerprint, second.decision_fingerprint)
        self.assertEqual(first.selected_bindings, second.selected_bindings)
        self.assertEqual("runtime_fallback", first.scorer_source)
        self.assertEqual("fallback.v1", first.scorer_version)

    def test_sender_intent_cannot_bypass_policy_decision(self) -> None:
        target = TargetGroup(
            kind="tenant",
            tenant_id="tenant-a",
            multi_connection_policy="all",
        )
        policy = DefaultLocalRoutingPolicy(
            allowed_strategies=frozenset({RoutingStrategy.SINGLE}),
        )
        intent = RequestedRoutingIntent.from_target(target)
        rejected = policy.decide(
            intent,
            risk=_risk(MessageCategory.TASK),
            config_version="config-v1",
            policy_version="policy-v1",
        )
        self.assertFalse(rejected.accepted)
        self.assertIs(
            RoutingFailureReason.STRATEGY_NOT_PERMITTED,
            rejected.rejection_reason,
        )
        with self.assertRaises(NsValidationError):
            dataclasses.replace(
                _request(TargetGroup(kind="tenant", tenant_id="tenant-a")),
                target=target,
                requested_intent=intent,
                policy_decision=rejected,
            )

    def test_policy_accept_reject_and_security_tighten(self) -> None:
        for policy_name in ("same_identity", "same_capability", "same_tenant"):
            with self.subTest(accepted=policy_name):
                target = TargetGroup(
                    kind="tenant",
                    tenant_id="tenant-a",
                    rebind_policy=policy_name,
                )
                request = _request(target)
                self.assertTrue(request.policy_decision.accepted)
                self.assertIs(
                    RebindPolicy(policy_name),
                    request.effective_rebind_policy,
                )
        denied = DefaultLocalRoutingPolicy(
            allowed_rebind_policies=frozenset({RebindPolicy.FIXED_CONNECTION}),
        ).decide(
            RequestedRoutingIntent.from_target(TargetGroup(
                kind="tenant",
                tenant_id="tenant-a",
                rebind_policy="same_tenant",
            )),
            risk=_risk(MessageCategory.TASK),
            config_version="config-v1",
            policy_version="policy-v1",
        )
        self.assertFalse(denied.accepted)
        self.assertIs(RoutingFailureReason.REBIND_NOT_PERMITTED, denied.rejection_reason)

        for category in (
            MessageCategory.CONTROL,
            MessageCategory.MANAGEMENT,
            MessageCategory.CONFIG,
            MessageCategory.CLUSTER,
        ):
            with self.subTest(security_category=category.value):
                decision = DefaultLocalRoutingPolicy().decide(
                    RequestedRoutingIntent.from_target(TargetGroup(
                        kind="tenant",
                        tenant_id="tenant-a",
                        rebind_policy="same_tenant",
                    )),
                    risk=_risk(category),
                    config_version="config-v1",
                    policy_version="policy-v1",
                )
                self.assertTrue(decision.accepted)
                self.assertIs(
                    RebindPolicy.NO_REBIND_FOR_CONTROL,
                    decision.effective_rebind_policy,
                )
                self.assertIn("trusted_contract", decision.security_override_evidence)

        security_audit = DefaultLocalRoutingPolicy().decide(
            RequestedRoutingIntent.from_target(TargetGroup(
                kind="tenant", tenant_id="tenant-a", rebind_policy="same_identity",
            )),
            risk=RoutingRiskMetadata(
                message_type="task.dispatch",
                category=MessageCategory.TASK,
                audit_level=MessageAuditLevel.SECURITY,
                security_sensitive=True,
            ),
            config_version="config-v1",
            policy_version="policy-v1",
        )
        self.assertIs(
            RebindPolicy.NO_REBIND_FOR_CONTROL,
            security_audit.effective_rebind_policy,
        )

    async def test_broadcast_is_fixed_and_rebroadcast_uses_new_full_snapshot(self) -> None:
        target = TargetGroup(
            kind="broadcast",
            scope="tenant",
            tenant_id="tenant-a",
            multi_connection_policy="broadcast",
        )
        first_contexts = self.contexts[:2]
        rebroadcast_index = _SnapshotIndex(_snapshot(first_contexts))
        rebroadcast_router = _router(rebroadcast_index, self.clock)
        first = await rebroadcast_router.route(_request(target))
        assert isinstance(first, ResolvedRoutingPlan)
        self.assertIs(RebindPolicy.FIXED_CONNECTION, first.effective_rebind_policy)
        self.assertIsNone(first.requested_rebind_policy)

        replacement = _routing_context(9)
        second_contexts = (first_contexts[1], replacement)
        rebroadcast_index._provided_snapshot = _snapshot(second_contexts)
        before = rebroadcast_index.snapshot_calls
        second = await rebroadcast_router.route(
            _request(target),
            previous=first.previous_context(),
        )
        assert isinstance(second, ResolvedRoutingPlan)
        self.assertEqual(before + 1, rebroadcast_index.snapshot_calls)
        self.assertEqual(2, second.plan_version)
        self.assertNotEqual(first.plan_id, second.plan_id)
        self.assertIs(RebindPolicy.FIXED_CONNECTION, second.effective_rebind_policy)
        self.assertTrue(all(
            binding.binding_rebind_policy is RebindPolicy.FIXED_CONNECTION
            for binding in second.selected_bindings
        ))
        selected = {item.connection_id for item in second.selected_bindings}
        self.assertIn(replacement.connection_id, selected)
        self.assertNotIn(first_contexts[0].connection_id, selected)

    async def test_previous_context_rejects_cross_message_and_invalid_evidence(self) -> None:
        target = TargetGroup(kind="tenant", tenant_id="tenant-a")
        first = await self.router.route(_request(target))
        assert isinstance(first, ResolvedRoutingPlan)
        before = self.index.snapshot_calls
        unrelated = await self.router.route(
            _request(target, message_reference="sha256:1111111111111111"),
            previous=first.previous_context(),
        )
        assert isinstance(unrelated, RoutingFailureReport)
        self.assertIs(RoutingFailureReason.PREVIOUS_MESSAGE_MISMATCH, unrelated.reason)
        self.assertIsInstance(unrelated.public_error(), NsRuntimeRouteRejectedError)
        self.assertEqual(before, self.index.snapshot_calls)

        malformed = first.previous_context()
        object.__setattr__(malformed, "decision_fingerprint", "missing")
        invalid = await self.router.route(_request(target), previous=malformed)
        assert isinstance(invalid, RoutingFailureReport)
        self.assertIs(RoutingFailureReason.PREVIOUS_FINGERPRINT_INVALID, invalid.reason)
        self.assertEqual(before, self.index.snapshot_calls)

        mismatched = first.previous_context()
        object.__setattr__(
            mismatched,
            "decision_fingerprint",
            "sha256:" + "b" * 64,
        )
        mismatch = await self.router.route(_request(target), previous=mismatched)
        assert isinstance(mismatch, RoutingFailureReport)
        self.assertIs(RoutingFailureReason.PREVIOUS_FINGERPRINT_MISMATCH, mismatch.reason)
        self.assertEqual(before, self.index.snapshot_calls)

        malformed_id = first.previous_context()
        object.__setattr__(malformed_id, "plan_id", "plan-invalid")
        invalid_id = await self.router.route(_request(target), previous=malformed_id)
        assert isinstance(invalid_id, RoutingFailureReport)
        self.assertIs(RoutingFailureReason.PREVIOUS_PLAN_ID_INVALID, invalid_id.reason)
        self.assertEqual(before, self.index.snapshot_calls)

        malformed_version = first.previous_context()
        object.__setattr__(malformed_version, "plan_version", 0)
        invalid_version = await self.router.route(
            _request(target),
            previous=malformed_version,
        )
        assert isinstance(invalid_version, RoutingFailureReport)
        self.assertIs(
            RoutingFailureReason.PREVIOUS_PLAN_VERSION_INVALID,
            invalid_version.reason,
        )
        self.assertEqual(before, self.index.snapshot_calls)

    async def test_previous_fingerprint_is_plan_id_independent(self) -> None:
        target = TargetGroup(kind="identity", identity="identity-shared", rebind_policy="same_identity")
        request = _request(target)
        first = await self.router.route(request)
        alternate = await self.router.route(request)
        assert isinstance(first, ResolvedRoutingPlan)
        assert isinstance(alternate, ResolvedRoutingPlan)
        self.assertNotEqual(first.plan_id, alternate.plan_id)
        next_first = await self.router.route(request, previous=first.previous_context())
        next_alternate = await self.router.route(request, previous=alternate.previous_context())
        assert isinstance(next_first, ResolvedRoutingPlan)
        assert isinstance(next_alternate, ResolvedRoutingPlan)
        self.assertEqual(
            next_first.decision_fingerprint,
            next_alternate.decision_fingerprint,
        )

    async def test_direct_invalid_contract_construction_fails_closed(self) -> None:
        invalid_parameters = (
            {"strategy": RoutingStrategy.QUORUM, "fanout_count": True, "required_count": 1},
            {"strategy": RoutingStrategy.QUORUM, "fanout_count": 1, "required_count": 2},
            {"strategy": RoutingStrategy.WEIGHTED_SUBSET, "subset_size": 1, "fanout_count": 1},
            {"strategy": RoutingStrategy.SINGLE, "fanout_count": 1},
        )
        for values in invalid_parameters:
            with self.subTest(values=values), self.assertRaises(NsValidationError):
                StrategyParameters(**values)

        first = await self.router.route(_request(TargetGroup(kind="tenant", tenant_id="tenant-a")))
        assert isinstance(first, ResolvedRoutingPlan)
        second = await self.router.route(
            _request(TargetGroup(kind="tenant", tenant_id="tenant-a")),
            previous=first.previous_context(),
        )
        assert isinstance(second, ResolvedRoutingPlan)
        with self.assertRaises(NsValidationError):
            dataclasses.replace(second, plan_version=1)
        with self.assertRaises(NsValidationError):
            dataclasses.replace(
                first,
                selected_bindings=(first.selected_bindings[0], first.selected_bindings[0]),
            )
        with self.assertRaises(NsValidationError):
            dataclasses.replace(
                first,
                effective_strategy_parameters=StrategyParameters(
                    strategy=RoutingStrategy.ALL,
                ),
            )

        missing = await self.router.route(_request(TargetGroup(
            kind="connection", connection_id="connection_123e4567e89b42d3a456000000009999",
        )))
        assert isinstance(missing, RoutingFailureReport)
        self.assertIs(RoutingFailureOutcome.REJECTED, missing.outcome)
        self.assertEqual("config-v1", missing.config_version)
        self.assertEqual("policy-v1", missing.policy_version)
        self.assertRegex(missing.original_target_safe_reference, r"sha256:[0-9a-f]{16}")
        with self.assertRaises(NsValidationError):
            dataclasses.replace(missing, outcome="rejected")
        with self.assertRaises(NsValidationError):
            dataclasses.replace(missing, config_version="")

    async def test_plan_is_deeply_immutable_versioned_and_safe(self) -> None:
        target = TargetGroup(
            kind="identity",
            identity="identity-shared",
            rebind_policy="same_identity",
        )
        first = await self.router.route(_request(target))
        assert isinstance(first, ResolvedRoutingPlan)
        second = await self.router.route(
            _request(target),
            previous=first.previous_context(),
        )
        assert isinstance(second, ResolvedRoutingPlan)
        self.assertEqual(2, second.plan_version)
        self.assertEqual(first.plan_id, second.previous_plan_id)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            second.plan_version = 3  # type: ignore[misc]
        rendered = repr(second.safe_projection())
        self.assertNotIn("connection_", rendered)
        self.assertNotIn("identity-shared", rendered)
        self.assertNotIn("tenant-a", rendered)

    async def test_rebind_policy_matrix(self) -> None:
        first = await self.router.route(
            _request(TargetGroup(
                kind="connection",
                connection_id=self.contexts[0].connection_id,
                connection_epoch=0,
            )),
        )
        assert isinstance(first, ResolvedRoutingPlan)
        for policy in (
            "same_identity", "same_capability", "same_tenant",
        ):
            with self.subTest(policy=policy):
                target = TargetGroup(
                    kind="tenant",
                    tenant_id="tenant-a",
                    rebind_policy=policy,
                )
                decision = await self.router.route(
                    _request(target),
                    previous=first.previous_context(),
                )
                self.assertIsInstance(decision, ResolvedRoutingPlan)
        for policy in ("fixed_connection", "no_rebind_for_control"):
            with self.subTest(policy=policy):
                category = "control" if policy == "no_rebind_for_control" else "task"
                target = TargetGroup(
                    kind="tenant",
                    tenant_id="tenant-a",
                    rebind_policy=policy,
                )
                decision = await self.router.route(
                    _request(target, category=category),
                    previous=first.previous_context(),
                )
                self.assertIsInstance(decision, ResolvedRoutingPlan)
                assert isinstance(decision, ResolvedRoutingPlan)
                self.assertEqual(
                    first.selected_bindings[0].connection_id,
                    decision.selected_bindings[0].connection_id,
                )

    async def test_dynamic_eligibility_and_all_required_fail_closed(self) -> None:
        entries = dict(self.snapshot.by_connection_id)
        first_id = self.contexts[0].connection_id
        entries[first_id] = dataclasses.replace(
            entries[first_id],
            active_target_eligible=False,
            routing_eligibility=ConnectionRoutingEligibility.RECONNECT_GRACE,
        )
        index = _SnapshotIndex(_snapshot_from_entries(entries, sequence=7))
        router = _router(index, self.clock)
        decision = await router.route(_request(TargetGroup(
            kind="tenant",
            tenant_id="tenant-a",
            multi_connection_policy="all_required",
        )))
        self.assertIsInstance(decision, RoutingFailureReport)
        assert isinstance(decision, RoutingFailureReport)
        self.assertIs(RoutingFailureReason.RECONNECT_GRACE_TARGET, decision.reason)

    async def test_remote_and_strong_required_are_unavailable(self) -> None:
        remote = await self.router.route(_request(TargetGroup(
            kind="runtime",
            runtime_id="runtime_123e4567e89b42d3a456426614174999",
        )))
        self.assertIsInstance(remote, RoutingFailureReport)
        assert isinstance(remote, RoutingFailureReport)
        self.assertIs(RoutingFailureReason.REMOTE_RUNTIME_REQUIRED, remote.reason)

        strong_router = LocalRouter(
            connection_index=self.index,
            clock=self.clock,
            identifier_factory=_identifier_factory(),
            runtime_id=RUNTIME_ID,
            config=NsRuntimeRoutingConfig(),
            consistency_policy=LocalRoutingConsistencyPolicy(
                strong_message_types=frozenset({"task.dispatch"}),
            ),
        )
        strong = await strong_router.route(_request(TargetGroup(
            kind="tenant",
            tenant_id="tenant-a",
        )))
        self.assertIsInstance(strong, RoutingFailureReport)
        assert isinstance(strong, RoutingFailureReport)
        self.assertIs(RoutingFailureReason.STRONG_PLAN_AUTHORITY_UNAVAILABLE, strong.reason)
        self.assertIsInstance(strong.public_error(), NsRuntimeRouteUnavailableError)

    async def test_limits_and_5001_selected_bindings_without_truncation(self) -> None:
        contexts = tuple(_routing_context(index) for index in range(5001))
        index = _SnapshotIndex(_snapshot(contexts))
        router = LocalRouter(
            connection_index=index,
            clock=self.clock,
            identifier_factory=_identifier_factory(),
            runtime_id=RUNTIME_ID,
            config=NsRuntimeRoutingConfig(
                max_candidate_count=10_000,
                max_selected_target_count=10_000,
                max_plan_evidence_count=20_000,
            ),
        )
        decision = await router.route(_request(TargetGroup(
            kind="tenant",
            tenant_id="tenant-a",
            multi_connection_policy="all",
        )))
        self.assertIsInstance(decision, ResolvedRoutingPlan)
        assert isinstance(decision, ResolvedRoutingPlan)
        self.assertEqual(5001, len(decision.selected_bindings))

        limited = LocalRouter(
            connection_index=index,
            clock=self.clock,
            identifier_factory=_identifier_factory(),
            runtime_id=RUNTIME_ID,
            config=NsRuntimeRoutingConfig(max_candidate_count=5000),
        )
        failure = await limited.route(_request(TargetGroup(
            kind="tenant",
            tenant_id="tenant-a",
            multi_connection_policy="all",
        )))
        self.assertIsInstance(failure, RoutingFailureReport)
        assert isinstance(failure, RoutingFailureReport)
        self.assertIs(RoutingFailureReason.CANDIDATE_LIMIT_EXCEEDED, failure.reason)


def _request(
    target: TargetGroup,
    *,
    category: str = "task",
    message_reference: str = MESSAGE_REF,
    principal_tenant_id: str = "tenant-a",
    policy: DefaultLocalRoutingPolicy | None = None,
) -> RoutingRequest:
    intent = RequestedRoutingIntent.from_target(target)
    risk_category = MessageCategory(category)
    decision = (policy or DefaultLocalRoutingPolicy()).decide(
        intent,
        risk=RoutingRiskMetadata(
            message_type="task.dispatch",
            category=risk_category,
            audit_level=(
                MessageAuditLevel.SECURITY
                if risk_category in {
                    MessageCategory.CONTROL,
                    MessageCategory.MANAGEMENT,
                    MessageCategory.CONFIG,
                    MessageCategory.CLUSTER,
                }
                else MessageAuditLevel.STANDARD
            ),
            security_sensitive=risk_category in {
                MessageCategory.CONTROL,
                MessageCategory.MANAGEMENT,
                MessageCategory.CONFIG,
                MessageCategory.CLUSTER,
            },
        ),
        config_version="config-v1",
        policy_version="policy-v1",
    )
    target_tenant = target.tenant_id
    crosses = target_tenant is not None and target_tenant != principal_tenant_id
    evidence = AuthorizationDecisionEvidence(
        decision_reference="sha256:" + "a" * 64,
        decision_version="authorization-decision.v1",
        message_reference=message_reference,
        message_type="task.dispatch",
        principal_tenant_id=principal_tenant_id,
        effective_tenant_id=target_tenant if crosses else principal_tenant_id,
        cross_tenant_authorized=crosses,
        authorized_target_reference=AuthorizationDecisionEvidence.target_reference(
            target,
            session_tenant_id=principal_tenant_id,
        ),
        permission_snapshot_ref="permission-ref",
        permission_snapshot_version="permission-v1",
    )
    return RoutingRequest(
        message_reference=message_reference,
        message_type="task.dispatch",
        target=target,
        requested_intent=intent,
        policy_decision=decision,
        authorization_evidence=evidence,
    )


def _risk(category: MessageCategory) -> RoutingRiskMetadata:
    sensitive = category in {
        MessageCategory.CONTROL,
        MessageCategory.MANAGEMENT,
        MessageCategory.CONFIG,
        MessageCategory.CLUSTER,
    }
    return RoutingRiskMetadata(
        message_type="task.dispatch",
        category=category,
        audit_level=(
            MessageAuditLevel.SECURITY if sensitive else MessageAuditLevel.STANDARD
        ),
        security_sensitive=sensitive,
    )


def _router(index: LocalConnectionIndex, clock: ControlledClock) -> LocalRouter:
    return LocalRouter(
        connection_index=index,
        clock=clock,
        identifier_factory=_identifier_factory(),
        runtime_id=RUNTIME_ID,
        config=NsRuntimeRoutingConfig(),
    )


def _identifier_factory() -> IdentifierFactory:
    counter = iter(range(1, 100_000))
    return IdentifierFactory(
        uuid_factory=lambda: UUID(f"123e4567-e89b-42d3-a456-{next(counter):012x}"),
    )


def _routing_context(index: int):
    base = _context(_transport(suffix="110"), clock=ControlledClock(utc_start=UTC_START))
    return dataclasses.replace(
        base,
        connection_id=f"connection_123e4567e89b42d3a456{index:012x}",
        session_id=f"session_123e4567e89b42d3b456{index:012x}",
        identity="identity-shared",
        tenant_id="tenant-a",
        component_type="worker",
        capabilities=frozenset({"cap.shared", f"cap.{index % 2}"}),
    )


def _snapshot(contexts) -> LocalConnectionIndexSnapshot:
    entries = {
        context.connection_id: ConnectionIndexEntrySnapshot(
            session_context=context,
            state=LogicalConnectionState.ACTIVE,
            active_target_eligible=True,
            routing_eligibility=ConnectionRoutingEligibility.ELIGIBLE,
        )
        for context in contexts
    }
    return _snapshot_from_entries(entries, sequence=1)


def _snapshot_from_entries(entries, *, sequence: int) -> LocalConnectionIndexSnapshot:
    def secondary(attribute):
        built = {}
        for connection_id, entry in entries.items():
            value = getattr(entry.session_context, attribute)
            built.setdefault(value, set()).add(connection_id)
        return MappingProxyType({key: frozenset(value) for key, value in built.items()})

    capabilities = {}
    for connection_id, entry in entries.items():
        for capability in entry.session_context.capabilities:
            capabilities.setdefault(capability, set()).add(connection_id)
    return LocalConnectionIndexSnapshot(
        by_connection_id=MappingProxyType(dict(entries)),
        by_session_id=MappingProxyType({
            entry.session_context.session_id: connection_id
            for connection_id, entry in entries.items()
        }),
        by_identity=secondary("identity"),
        by_tenant=secondary("tenant_id"),
        by_component_type=secondary("component_type"),
        by_capability=MappingProxyType({
            key: frozenset(value) for key, value in capabilities.items()
        }),
        active_target_connection_ids=frozenset(
            connection_id
            for connection_id, entry in entries.items()
            if entry.active_target_eligible
        ),
        mutation_sequence=sequence,
    )


if __name__ == "__main__":
    unittest.main()
