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
from ns_runtime.protocol import (
    BUILTIN_MESSAGE_REGISTRY,
    MessageAuditLevel,
    MessageCategory,
    TargetGroup,
)
from ns_runtime.routing import (
    DefaultLocalRoutingPolicy,
    CandidateFilterReason,
    LocalRouter,
    LocalRoutingConsistencyPolicy,
    RebindPolicy,
    RequestedRoutingIntent,
    ResolvedRoutingPlan,
    RoutingFailureReason,
    RoutingFailureReport,
    RoutingFailureOutcome,
    RoutingPolicyInvocation,
    RoutingRequest,
    RoutingScorerIdentity,
    RoutingScoringDecision,
    RoutingSecurityOverride,
    RoutingStrategy,
    ResolutionHint,
    StrategyParameters,
    SelectedRoutingBinding,
    compute_routing_decision_fingerprint,
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


class _ScoringPolicy(DefaultLocalRoutingPolicy):
    def __init__(self, scoring_decision: RoutingScoringDecision) -> None:
        super().__init__()
        self._scoring_decision = scoring_decision

    def decide(self, *args, **kwargs):
        return dataclasses.replace(
            super().decide(*args, **kwargs),
            scoring_decision=self._scoring_decision,
        )


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

        other_message = await self.router.route(_request(
            target,
            message_reference="sha256:1111111111111111",
        ))
        assert isinstance(other_message, ResolvedRoutingPlan)
        self.assertNotEqual(
            first.authorization_evidence.message_binding_reference,
            other_message.authorization_evidence.message_binding_reference,
        )
        self.assertEqual(
            first.authorization_evidence.semantic_decision_reference,
            other_message.authorization_evidence.semantic_decision_reference,
        )
        self.assertEqual(
            first.decision_fingerprint,
            other_message.decision_fingerprint,
        )

        changed_iam = await self.router.route(_request(
            target,
            iam_decision_result_reference="sha256:" + "b" * 64,
        ))
        changed_permission = await self.router.route(_request(
            target,
            session_permission_snapshot_version="permission-v2",
            effective_permission_snapshot_version="permission-v2",
        ))
        changed_permission_ref = await self.router.route(_request(
            target,
            session_permission_snapshot_ref="permission-other",
            effective_permission_snapshot_ref="permission-other",
        ))
        changed_iam_result = await self.router.route(_request(
            target,
            iam_decision_reason="allowed_by_role",
        ))
        changed_target = await self.router.route(_request(TargetGroup(
            kind="identity",
            identity="identity-shared",
        )))
        changed_tenant_decision = await self.router.route(_request(
            target,
            principal_tenant_id="tenant-b",
        ))
        assert isinstance(changed_iam, ResolvedRoutingPlan)
        assert isinstance(changed_permission, ResolvedRoutingPlan)
        assert isinstance(changed_permission_ref, ResolvedRoutingPlan)
        assert isinstance(changed_iam_result, ResolvedRoutingPlan)
        assert isinstance(changed_target, ResolvedRoutingPlan)
        assert isinstance(changed_tenant_decision, ResolvedRoutingPlan)
        self.assertNotEqual(first.decision_fingerprint, changed_iam.decision_fingerprint)
        self.assertNotEqual(
            first.decision_fingerprint,
            changed_permission.decision_fingerprint,
        )
        for changed in (
            changed_permission_ref,
            changed_iam_result,
            changed_target,
            changed_tenant_decision,
        ):
            self.assertNotEqual(
                first.decision_fingerprint,
                changed.decision_fingerprint,
            )

    async def test_scoring_inputs_are_policy_owned_and_fingerprinted(self) -> None:
        target = TargetGroup(kind="tenant", tenant_id="tenant-a")
        default = _request(target)
        request_fields = {item.name for item in dataclasses.fields(RoutingRequest)}
        self.assertNotIn("trusted_affinity_connection_ids", request_fields)
        self.assertNotIn("runtime_policy_static_weights", request_fields)
        self.assertEqual((), default.scoring_decision.trusted_affinity_connection_ids)
        self.assertEqual((), default.scoring_decision.runtime_policy_static_weights)
        request_values = {
            item.name: getattr(default, item.name)
            for item in dataclasses.fields(RoutingRequest)
        }
        with self.assertRaises(TypeError):
            RoutingRequest(
                **request_values,
                trusted_affinity_connection_ids=(self.contexts[0].connection_id,),
            )

        preferred = self.contexts[2].connection_id
        scoring = RoutingScoringDecision.from_inputs(
            scorer_input_version="routing-scoring.policy-v7",
            trusted_affinity_connection_ids=(preferred,),
            runtime_policy_static_weights=((preferred, 25),),
        )
        scored = await self.router.route(_request(
            target,
            policy=_ScoringPolicy(scoring),
        ))
        baseline = await self.router.route(default)
        assert isinstance(scored, ResolvedRoutingPlan)
        assert isinstance(baseline, ResolvedRoutingPlan)
        self.assertEqual(preferred, scored.selected_bindings[0].connection_id)
        self.assertEqual(scoring.scorer_input_reference, scored.scorer_input_reference)
        self.assertEqual(scoring.scorer_input_version, scored.scorer_input_version)
        self.assertNotEqual(baseline.decision_fingerprint, scored.decision_fingerprint)
        with self.assertRaises(NsValidationError):
            dataclasses.replace(
                scoring,
                scorer_input_reference="sha256:" + "0" * 64,
            )
        with self.assertRaises(NsValidationError):
            RoutingScorerIdentity(source="sender", version="fallback.v1")
        with self.assertRaises(NsValidationError):
            dataclasses.replace(scored, scorer_identity="runtime_fallback/fake")

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
        rejected = policy.decide(_policy_invocation(target))
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
        ).decide(_policy_invocation(TargetGroup(
                kind="tenant",
                tenant_id="tenant-a",
                rebind_policy="same_tenant",
        )))
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
                    _policy_invocation(TargetGroup(
                        kind="tenant",
                        tenant_id="tenant-a",
                        rebind_policy="same_tenant",
                    ), category=category),
                )
                self.assertTrue(decision.accepted)
                self.assertIs(
                    RebindPolicy.NO_REBIND_FOR_CONTROL,
                    decision.effective_rebind_policy,
                )
                self.assertIs(
                    RoutingSecurityOverride.NO_REBIND_FOR_SECURITY,
                    decision.security_override_evidence,
                )

        security_audit = DefaultLocalRoutingPolicy().decide(
            _policy_invocation(TargetGroup(
                kind="tenant", tenant_id="tenant-a", rebind_policy="same_identity",
            ), audit_level=MessageAuditLevel.SECURITY),
        )
        self.assertIs(
            RebindPolicy.NO_REBIND_FOR_CONTROL,
            security_audit.effective_rebind_policy,
        )

    def test_rebind_policy_decision_direct_construction_closes_expansion(self) -> None:
        no_request = _request(
            TargetGroup(kind="tenant", tenant_id="tenant-a"),
        ).policy_decision
        for expanded in (
            RebindPolicy.SAME_IDENTITY,
            RebindPolicy.SAME_CAPABILITY,
            RebindPolicy.SAME_TENANT,
        ):
            with self.subTest(no_request_expanded=expanded), self.assertRaises(
                NsValidationError,
            ):
                dataclasses.replace(no_request, effective_rebind_policy=expanded)

        same_policies = (
            RebindPolicy.SAME_IDENTITY,
            RebindPolicy.SAME_CAPABILITY,
            RebindPolicy.SAME_TENANT,
        )
        for requested in same_policies:
            decision = _request(TargetGroup(
                kind="tenant",
                tenant_id="tenant-a",
                rebind_policy=requested.value,
            )).policy_decision
            for expanded in same_policies:
                if expanded is requested:
                    continue
                with self.subTest(
                    requested=requested,
                    expanded=expanded,
                ), self.assertRaises(NsValidationError):
                    dataclasses.replace(
                        decision,
                        effective_rebind_policy=expanded,
                    )
            for tightened in (
                requested,
                RebindPolicy.FIXED_CONNECTION,
                RebindPolicy.NO_REBIND_FOR_CONTROL,
            ):
                with self.subTest(requested=requested, valid=tightened):
                    dataclasses.replace(
                        decision,
                        effective_rebind_policy=tightened,
                    )

        broadcast = _request(TargetGroup(
            kind="broadcast",
            scope="tenant",
            tenant_id="tenant-a",
            multi_connection_policy="broadcast",
        )).policy_decision
        with self.assertRaises(NsValidationError):
            dataclasses.replace(
                broadcast,
                effective_rebind_policy=RebindPolicy.NO_REBIND_FOR_CONTROL,
            )

        security = _request(
            TargetGroup(kind="tenant", tenant_id="tenant-a"),
            category="control",
        ).policy_decision
        with self.assertRaises(NsValidationError):
            dataclasses.replace(
                security,
                effective_rebind_policy=RebindPolicy.FIXED_CONNECTION,
            )
        with self.assertRaises(NsValidationError):
            dataclasses.replace(
                security,
                security_override_evidence=RoutingSecurityOverride.NONE,
            )
        sensitive_broadcast = DefaultLocalRoutingPolicy().decide(
            _policy_invocation(TargetGroup(
                kind="broadcast",
                scope="tenant",
                tenant_id="tenant-a",
                multi_connection_policy="broadcast",
            ), category=MessageCategory.CONTROL),
        )
        self.assertFalse(sensitive_broadcast.accepted)
        self.assertIs(
            RoutingFailureReason.REBIND_NOT_PERMITTED,
            sensitive_broadcast.rejection_reason,
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
        strategy_expansions = (
            StrategyParameters(strategy=RoutingStrategy.ALL),
            StrategyParameters(strategy=RoutingStrategy.BROADCAST),
            StrategyParameters(
                strategy=RoutingStrategy.QUORUM,
                fanout_count=2,
                required_count=1,
            ),
            StrategyParameters(strategy=RoutingStrategy.ALL_REQUIRED),
            StrategyParameters(
                strategy=RoutingStrategy.WEIGHTED_SUBSET,
                subset_size=2,
            ),
        )
        for expanded_parameters in strategy_expansions:
            with self.subTest(
                strategy_expansion=expanded_parameters.strategy,
            ), self.assertRaises(NsValidationError):
                dataclasses.replace(
                    first,
                    effective_strategy=expanded_parameters.strategy,
                    effective_strategy_parameters=expanded_parameters,
                )
        with self.assertRaises(NsValidationError):
            dataclasses.replace(
                first,
                effective_rebind_policy=RebindPolicy.SAME_TENANT,
            )
        with self.assertRaises(NsValidationError):
            dataclasses.replace(first, effective_policy_evidence="policy:forged")
        with self.assertRaises(NsValidationError):
            dataclasses.replace(
                first,
                authorization_evidence=dataclasses.replace(
                    first.authorization_evidence,
                    effective_permission_snapshot_version="permission-v9",
                ),
            )
        with self.assertRaises(NsValidationError):
            dataclasses.replace(
                first,
                selected_bindings=(dataclasses.replace(
                    first.selected_bindings[0],
                    binding_rebind_policy=RebindPolicy.SAME_TENANT,
                ),),
            )

        broadcast = await self.router.route(_request(TargetGroup(
            kind="broadcast",
            scope="tenant",
            tenant_id="tenant-a",
            multi_connection_policy="broadcast",
        )))
        assert isinstance(broadcast, ResolvedRoutingPlan)
        with self.assertRaises(NsValidationError):
            dataclasses.replace(
                broadcast,
                effective_rebind_policy=RebindPolicy.NO_REBIND_FOR_CONTROL,
            )

        security = await self.router.route(_request(
            TargetGroup(kind="tenant", tenant_id="tenant-a"),
            category="control",
        ))
        assert isinstance(security, ResolvedRoutingPlan)
        with self.assertRaises(NsValidationError):
            dataclasses.replace(
                security,
                security_override_evidence=RoutingSecurityOverride.NONE,
            )

        same_identity_plan = await self.router.route(_request(TargetGroup(
            kind="tenant",
            tenant_id="tenant-a",
            rebind_policy="same_identity",
        )))
        assert isinstance(same_identity_plan, ResolvedRoutingPlan)
        for expanded in (RebindPolicy.SAME_CAPABILITY, RebindPolicy.SAME_TENANT):
            with self.subTest(plan_rebind_expansion=expanded), self.assertRaises(
                NsValidationError,
            ):
                dataclasses.replace(
                    same_identity_plan,
                    effective_rebind_policy=expanded,
                )

        quorum_plan = await self.router.route(_request(TargetGroup(
            kind="tenant",
            tenant_id="tenant-a",
            multi_connection_policy="quorum",
            fanout_count=2,
            required_count=1,
        )))
        assert isinstance(quorum_plan, ResolvedRoutingPlan)
        with self.assertRaises(NsValidationError):
            dataclasses.replace(
                quorum_plan,
                effective_strategy_parameters=StrategyParameters(
                    strategy=RoutingStrategy.QUORUM,
                    fanout_count=3,
                    required_count=1,
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
        self.assertIs(ResolutionHint.LOCAL, missing.resolution_hint)
        with self.assertRaises(NsValidationError):
            dataclasses.replace(missing, outcome="rejected")
        with self.assertRaises(NsValidationError):
            dataclasses.replace(missing, config_version="")

    async def test_plan_candidate_sets_and_strategy_cardinality_are_independent(self) -> None:
        single = await self.router.route(_request(TargetGroup(
            kind="tenant",
            tenant_id="tenant-a",
        )))
        assert isinstance(single, ResolvedRoutingPlan)
        selected_key = _candidate_key(single.candidates[0])
        with self.assertRaises(NsValidationError):
            _replace_plan_semantics(
                single,
                candidates=tuple(
                    value
                    for value in single.candidates
                    if _candidate_key(value) != selected_key
                ),
            )
        mismatched_binding = dataclasses.replace(
            single.selected_bindings[0],
            tenant_id="tenant-forged",
        )
        with self.assertRaises(NsValidationError):
            _replace_plan_semantics(
                single,
                selected_bindings=(mismatched_binding,),
            )

        second_candidate = next(
            value
            for value in single.candidates
            if value.filter_reason is CandidateFilterReason.ELIGIBLE
        )
        expanded_candidates = tuple(
            dataclasses.replace(
                value,
                filter_reason=CandidateFilterReason.SELECTED,
            )
            if value == second_candidate
            else value
            for value in single.candidates
        )
        with self.assertRaises(NsValidationError):
            _replace_plan_semantics(
                single,
                candidates=expanded_candidates,
                selected_bindings=(
                    *single.selected_bindings,
                    _binding_from_candidate(single, second_candidate),
                ),
            )

        cardinality_targets = (
            TargetGroup(
                kind="tenant",
                tenant_id="tenant-a",
                multi_connection_policy="quorum",
                fanout_count=2,
                required_count=1,
            ),
            TargetGroup(
                kind="tenant",
                tenant_id="tenant-a",
                multi_connection_policy="weighted_subset",
                subset_size=2,
            ),
            TargetGroup(
                kind="tenant",
                tenant_id="tenant-a",
                multi_connection_policy="all",
            ),
        )
        for target in cardinality_targets:
            plan = await self.router.route(_request(target))
            assert isinstance(plan, ResolvedRoutingPlan)
            removed = plan.selected_bindings[-1]
            reduced_candidates = tuple(
                dataclasses.replace(
                    value,
                    filter_reason=CandidateFilterReason.ELIGIBLE,
                )
                if _candidate_key(value) == _binding_key(removed)
                else value
                for value in plan.candidates
            )
            with self.subTest(strategy=plan.effective_strategy), self.assertRaises(
                NsValidationError,
            ):
                _replace_plan_semantics(
                    plan,
                    candidates=reduced_candidates,
                    selected_bindings=plan.selected_bindings[:-1],
                )

        entries = dict(self.snapshot.by_connection_id)
        first_id = self.contexts[0].connection_id
        entries[first_id] = dataclasses.replace(
            entries[first_id],
            state=LogicalConnectionState.DRAINING,
            active_target_eligible=False,
            routing_eligibility=ConnectionRoutingEligibility.DRAINING,
        )
        filtered_router = _router(
            _SnapshotIndex(_snapshot_from_entries(entries, sequence=8)),
            self.clock,
        )
        filtered_plan = await filtered_router.route(_request(TargetGroup(
            kind="tenant",
            tenant_id="tenant-a",
            multi_connection_policy="all",
        )))
        assert isinstance(filtered_plan, ResolvedRoutingPlan)
        self.assertEqual(1, len(filtered_plan.filtered_evidence))
        with self.assertRaises(NsValidationError):
            _replace_plan_semantics(filtered_plan, filtered_evidence=())
        eligible = next(
            value
            for value in filtered_plan.candidates
            if value.filter_reason is CandidateFilterReason.SELECTED
        )
        with self.assertRaises(NsValidationError):
            _replace_plan_semantics(
                filtered_plan,
                filtered_evidence=(*filtered_plan.filtered_evidence, eligible),
            )

    async def test_plan_recomputes_candidate_policy_iam_and_scoring_fingerprint(self) -> None:
        target = TargetGroup(
            kind="tenant",
            tenant_id="tenant-a",
            multi_connection_policy="all",
        )
        plan = await self.router.route(_request(target))
        assert isinstance(plan, ResolvedRoutingPlan)
        assert plan.candidates[0].score is not None
        changed_candidate = dataclasses.replace(
            plan.candidates[0],
            score=(*plan.candidates[0].score, "changed"),
        )
        with self.assertRaises(NsValidationError):
            dataclasses.replace(
                plan,
                candidates=(changed_candidate, *plan.candidates[1:]),
            )
        with self.assertRaises(NsValidationError):
            dataclasses.replace(
                plan,
                selected_bindings=tuple(reversed(plan.selected_bindings)),
            )
        with self.assertRaises(NsValidationError):
            dataclasses.replace(
                plan,
                index_mutation_sequence=plan.index_mutation_sequence + 1,
            )

        next_plan = await self.router.route(
            _request(target),
            previous=plan.previous_context(),
        )
        assert isinstance(next_plan, ResolvedRoutingPlan)
        with self.assertRaises(NsValidationError):
            dataclasses.replace(
                next_plan,
                previous_decision_fingerprint="sha256:" + "b" * 64,
            )

        changed_authorization = _request(
            target,
            iam_decision_reason="allowed_by_role",
        ).authorization_evidence
        with self.assertRaises(NsValidationError):
            dataclasses.replace(
                plan,
                authorization_evidence=changed_authorization,
                iam_decision_reference=(
                    changed_authorization.semantic_decision_reference
                ),
                iam_decision_version=changed_authorization.decision_version,
                authorized_target_reference=(
                    changed_authorization.authorized_target_reference
                ),
                effective_permission_snapshot_ref=(
                    changed_authorization.effective_permission_snapshot_ref
                ),
                effective_permission_snapshot_version=(
                    changed_authorization.effective_permission_snapshot_version
                ),
            )

        changed_scoring = RoutingScoringDecision.from_inputs(
            scorer_input_version="routing-scoring.policy-v2",
            trusted_affinity_connection_ids=(self.contexts[1].connection_id,),
        )
        changed_policy = dataclasses.replace(
            plan.policy_decision,
            scoring_decision=changed_scoring,
        )
        with self.assertRaises(NsValidationError):
            dataclasses.replace(
                plan,
                policy_decision=changed_policy,
                scorer_input_reference=changed_scoring.scorer_input_reference,
                scorer_input_version=changed_scoring.scorer_input_version,
            )

        changed_invocation = _policy_invocation(
            target,
            policy_version="policy-v2",
        )
        changed_policy_version = DefaultLocalRoutingPolicy().decide(
            changed_invocation,
        )
        with self.assertRaises(NsValidationError):
            dataclasses.replace(
                plan,
                policy_decision=changed_policy_version,
                policy_version="policy-v2",
            )

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
        self.assertIs(ResolutionHint.REMOTE_RUNTIME_REQUIRED, remote.resolution_hint)

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
        self.assertIs(
            ResolutionHint.AUTHORITY_RECOVERY_REQUIRED,
            strong.resolution_hint,
        )
        self.assertIsInstance(strong.public_error(), NsRuntimeRouteUnavailableError)

        self.assertEqual(
            {
                "local",
                "master_query_required",
                "remote_runtime_required",
                "authority_recovery_required",
            },
            {value.value for value in ResolutionHint},
        )

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
    iam_decision_result_reference: str = "sha256:" + "a" * 64,
    iam_decision_reason: str = "allowed",
    session_permission_snapshot_ref: str = "permission-ref",
    session_permission_snapshot_version: str = "permission-v1",
    effective_permission_snapshot_ref: str | None = None,
    effective_permission_snapshot_version: str | None = None,
) -> RoutingRequest:
    intent = RequestedRoutingIntent.from_target(target)
    risk_category = MessageCategory(category)
    decision = (policy or DefaultLocalRoutingPolicy()).decide(
        _policy_invocation(target, category=risk_category),
    )
    target_tenant = target.tenant_id
    crosses = target_tenant is not None and target_tenant != principal_tenant_id
    evidence = AuthorizationDecisionEvidence.bound(
        decision_version="authorization-decision.v1",
        decision_classification="allow",
        decision_reason=iam_decision_reason,
        semantic_access_check_reference=iam_decision_result_reference,
        message_reference=message_reference,
        message_type="task.dispatch",
        principal_tenant_id=principal_tenant_id,
        effective_tenant_id=target_tenant if crosses else principal_tenant_id,
        cross_tenant_authorized=crosses,
        authorized_target_reference=AuthorizationDecisionEvidence.target_reference(
            target,
            session_tenant_id=principal_tenant_id,
        ),
        session_permission_snapshot_ref=session_permission_snapshot_ref,
        session_permission_snapshot_version=session_permission_snapshot_version,
        effective_permission_snapshot_ref=(
            effective_permission_snapshot_ref or session_permission_snapshot_ref
        ),
        effective_permission_snapshot_version=(
            effective_permission_snapshot_version
            or session_permission_snapshot_version
        ),
    )
    return RoutingRequest(
        message_reference=message_reference,
        message_type="task.dispatch",
        target=target,
        requested_intent=intent,
        policy_decision=decision,
        authorization_evidence=evidence,
    )


def _policy_invocation(
    target: TargetGroup,
    *,
    category: MessageCategory = MessageCategory.TASK,
    audit_level: MessageAuditLevel | None = None,
    config_version: str = "config-v1",
    policy_version: str = "policy-v1",
) -> RoutingPolicyInvocation:
    sensitive_category = category in {
        MessageCategory.CONTROL,
        MessageCategory.MANAGEMENT,
        MessageCategory.CONFIG,
        MessageCategory.CLUSTER,
    }
    contract = dataclasses.replace(
        BUILTIN_MESSAGE_REGISTRY.require("task.dispatch"),
        category=category,
        audit_level=(
            MessageAuditLevel.SECURITY
            if sensitive_category and audit_level is None
            else audit_level or MessageAuditLevel.STANDARD
        ),
    )
    return RoutingPolicyInvocation.from_contract(
        contract=contract,
        requested_intent=RequestedRoutingIntent.from_target(target),
        config_version=config_version,
        policy_version=policy_version,
    )


def _candidate_key(value) -> tuple[str, str, str, int]:
    return (
        value.runtime_id,
        value.connection_id,
        value.session_id,
        value.connection_epoch,
    )


def _binding_key(value: SelectedRoutingBinding) -> tuple[str, str, str, int]:
    return (
        value.runtime_id,
        value.connection_id,
        value.session_id,
        value.connection_epoch,
    )


def _binding_from_candidate(
    plan: ResolvedRoutingPlan,
    candidate,
) -> SelectedRoutingBinding:
    return SelectedRoutingBinding(
        runtime_id=candidate.runtime_id,
        connection_id=candidate.connection_id,
        session_id=candidate.session_id,
        connection_epoch=candidate.connection_epoch,
        tenant_id=candidate.tenant_id,
        identity_reference=candidate.identity_reference,
        required_capabilities=candidate.required_capabilities,
        component_type=candidate.component_type,
        binding_rebind_policy=plan.effective_rebind_policy,
    )


def _replace_plan_semantics(
    plan: ResolvedRoutingPlan,
    **changes: object,
) -> ResolvedRoutingPlan:
    target = changes.get("original_target", plan.original_target)
    policy_decision = changes.get("policy_decision", plan.policy_decision)
    authorization_evidence = changes.get(
        "authorization_evidence",
        plan.authorization_evidence,
    )
    scorer_identity = changes.get("scorer_identity", plan.scorer_identity)
    candidates = changes.get("candidates", plan.candidates)
    selected_bindings = changes.get(
        "selected_bindings",
        plan.selected_bindings,
    )
    index_mutation_sequence = changes.get(
        "index_mutation_sequence",
        plan.index_mutation_sequence,
    )
    previous_decision_fingerprint = changes.get(
        "previous_decision_fingerprint",
        plan.previous_decision_fingerprint,
    )
    used_stale_route = changes.get("used_stale_route", plan.used_stale_route)
    fingerprint = compute_routing_decision_fingerprint(
        target=target,  # type: ignore[arg-type]
        policy_decision=policy_decision,  # type: ignore[arg-type]
        authorization_evidence=authorization_evidence,  # type: ignore[arg-type]
        scorer_identity=scorer_identity,  # type: ignore[arg-type]
        candidates=candidates,  # type: ignore[arg-type]
        selected_bindings=selected_bindings,  # type: ignore[arg-type]
        index_mutation_sequence=index_mutation_sequence,  # type: ignore[arg-type]
        previous_decision_fingerprint=previous_decision_fingerprint,  # type: ignore[arg-type]
        used_stale_route=used_stale_route,  # type: ignore[arg-type]
    )
    return dataclasses.replace(
        plan,
        decision_fingerprint=fingerprint,
        **changes,
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
