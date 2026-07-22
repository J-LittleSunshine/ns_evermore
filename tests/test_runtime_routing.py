# -*- coding: utf-8 -*-
from __future__ import annotations

import dataclasses
import unittest
from types import MappingProxyType
from uuid import UUID

from ns_common.config.groups.runtime import NsRuntimeRoutingConfig
from ns_common.exceptions import NsRuntimeRouteUnavailableError
from ns_common.identifiers import IdentifierFactory
from ns_common.time import ControlledClock
from ns_runtime.connection import (
    ConnectionIndexEntrySnapshot,
    ConnectionRoutingEligibility,
    LocalConnectionIndex,
    LocalConnectionIndexSnapshot,
    LogicalConnectionState,
)
from ns_runtime.protocol import TargetGroup
from ns_runtime.routing import (
    LocalRouter,
    LocalRoutingConsistencyPolicy,
    RebindPolicy,
    ResolvedRoutingPlan,
    RoutingFailureReason,
    RoutingFailureReport,
    RoutingRequest,
    RoutingStrategy,
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
        self.assertIs(RoutingFailureReason.RECONNECT_GRACE, decision.reason)

    async def test_remote_and_strong_required_are_unavailable(self) -> None:
        remote = await self.router.route(_request(TargetGroup(
            kind="runtime",
            runtime_id="runtime_123e4567e89b42d3a456426614174999",
        )))
        self.assertIsInstance(remote, RoutingFailureReport)
        assert isinstance(remote, RoutingFailureReport)
        self.assertIs(RoutingFailureReason.REMOTE_RUNTIME, remote.reason)

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
        self.assertIs(RoutingFailureReason.AUTHORITY_UNAVAILABLE, strong.reason)
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
        self.assertIs(RoutingFailureReason.LIMIT_EXCEEDED, failure.reason)


def _request(target: TargetGroup, *, category: str = "task") -> RoutingRequest:
    return RoutingRequest.from_target(
        message_reference=MESSAGE_REF,
        message_type="task.dispatch",
        message_category=category,
        target=target,
        effective_tenant_id="tenant-a",
        config_version="config-v1",
        policy_version="policy-v1",
        iam_decision_reference="permission-ref",
        iam_decision_version="permission-v1",
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
