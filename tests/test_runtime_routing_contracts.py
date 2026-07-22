# -*- coding: utf-8 -*-
from __future__ import annotations

import dataclasses
import unittest
from pathlib import Path

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import NsRuntimeEnvelopeSchemaError
from ns_common.iam import IamPrincipalType
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
)
from ns_runtime.processor.integration import DeterministicTestProcessorAuthorization
from ns_runtime.protocol import (
    BUILTIN_MESSAGE_REGISTRY,
    MessageGroup,
    RoutingRequirement,
    TargetGroup,
)
from ns_runtime.routing import LocalRoutingPreparation

from tests.test_runtime_processor_pipeline import NOW, _envelope, _session
from tests.test_runtime_routing import RUNTIME_ID, _router, _snapshot, _SnapshotIndex, _routing_context


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


if __name__ == "__main__":
    unittest.main()
