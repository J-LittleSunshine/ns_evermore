# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import dataclasses
import logging
import unittest
from datetime import datetime, timezone

from ns_common.async_runtime import TaskSupervisor
from ns_common.config import NsConfig
from ns_common.exceptions import (
    NsRuntimeStateStoreIndeterminateWriteError,
    NsRuntimeStateStoreNotReadyError,
    NsRuntimeStateStoreUnavailableError,
    NsValidationError,
)
from ns_common.observability import InMemoryMetricsSink, InMemoryTraceSink
from ns_common.state_store import StateNamespace, StateStoreLifecycleState
from ns_common.time import ControlledClock
from ns_runtime.context import RuntimeContext, RuntimeDependencySlots
from ns_runtime.processor import (
    AuditAction,
    AuditConsistency,
    DeterministicTestAuditSink,
    LoggingAuditSink,
    ProcessorAuditBoundary,
    ProcessorAuditRecord,
    ProcessorSafeSummary,
    ProcessorTraceReference,
)
from ns_runtime.service import RuntimeService, RuntimeServiceState
from ns_runtime.shutdown import (
    RuntimeShutdownCoordinator,
    RuntimeShutdownPhase,
)
from ns_runtime.state_authority import (
    AuthorityRoutingAuditSink,
    StateStoreStrongAuditAuthorityService,
    StrongAuditAuthorityService,
)

from tests._state_store_contract_model import DeterministicStateStoreContractModel


NOW = datetime(2026, 7, 22, tzinfo=timezone.utc)


class _RecordingMetricsSink(InMemoryMetricsSink):
    def __init__(self, events: list[str]) -> None:
        super().__init__()
        self._events = events

    async def flush(self) -> None:
        self._events.append("metrics:flush")
        await super().flush()


def _context(
    *,
    clock: ControlledClock,
    supervisor: TaskSupervisor,
    state_store: DeterministicStateStoreContractModel | None = None,
    metrics: object | None = None,
) -> RuntimeContext:
    return RuntimeContext(
        config=NsConfig(),
        clock=clock,
        logger=logging.Logger("runtime-state-store-test"),
        metrics=metrics or InMemoryMetricsSink(),  # type: ignore[arg-type]
        traces=InMemoryTraceSink(),
        task_supervisor=supervisor,
        dependencies=RuntimeDependencySlots(state_store=state_store),
    )


def _audit_record(
    consistency: AuditConsistency = AuditConsistency.STRONG_REQUIRED,
) -> ProcessorAuditRecord:
    return ProcessorAuditRecord(
        safe_summary=ProcessorSafeSummary(
            message_type="management.test",
            category="management",
            object_reference="sha256:0123456789abcdef",
        ),
        processor="test.processor",
        action=AuditAction.SUCCEEDED,
        error=None,
        trace=ProcessorTraceReference(
            value="op_0123456789abcdef0123456789abcdef",
        ),
        config_version="config-v1",
        policy_version="policy-v1",
        required_consistency=consistency,
        occurred_at=NOW,
    )


class RuntimeStateStoreCompositionTestCase(unittest.IsolatedAsyncioTestCase):

    async def test_context_slot_is_typed_isolated_and_not_a_locator(self) -> None:
        first_clock = ControlledClock(utc_start=NOW)
        second_clock = ControlledClock(utc_start=NOW)
        first = DeterministicStateStoreContractModel(clock=first_clock)
        second = DeterministicStateStoreContractModel(clock=second_clock)
        first_context = _context(
            clock=first_clock,
            supervisor=TaskSupervisor(),
            state_store=first,
        )
        second_context = _context(
            clock=second_clock,
            supervisor=TaskSupervisor(),
            state_store=second,
        )
        self.addAsyncCleanup(first_context.task_supervisor.shutdown)
        self.addAsyncCleanup(second_context.task_supervisor.shutdown)
        self.addAsyncCleanup(first.close)
        self.addAsyncCleanup(second.close)

        self.assertIs(first, first_context.state_store)
        self.assertIs(second, second_context.state_store)
        self.assertIsNot(first_context.state_store, second_context.state_store)
        self.assertFalse(hasattr(first_context.dependencies, "get"))
        self.assertFalse(hasattr(first_context.dependencies, "resolve"))
        with self.assertRaises(NsValidationError):
            RuntimeDependencySlots(state_store=object())  # type: ignore[arg-type]

    async def test_runtime_service_requires_injected_store_ready_before_start(self) -> None:
        clock = ControlledClock(utc_start=NOW)
        store = DeterministicStateStoreContractModel(clock=clock)
        context = _context(
            clock=clock,
            supervisor=TaskSupervisor(),
            state_store=store,
        )
        service = RuntimeService(context=context)
        with self.assertRaises(NsRuntimeStateStoreNotReadyError):
            await service.start()
        self.assertIs(RuntimeServiceState.FAILED, service.state)
        await service.stop()
        self.assertIs(StateStoreLifecycleState.CLOSED, store.state)

        ready_store = DeterministicStateStoreContractModel(clock=clock)
        await ready_store.open()
        ready_context = _context(
            clock=clock,
            supervisor=TaskSupervisor(),
            state_store=ready_store,
        )
        ready_service = RuntimeService(context=ready_context)
        await ready_service.start()
        self.assertIs(RuntimeServiceState.RUNNING, ready_service.state)
        await ready_service.stop()
        self.assertIs(StateStoreLifecycleState.CLOSED, ready_store.state)

    async def test_runtime_service_rejects_unhealthy_store(self) -> None:
        clock = ControlledClock(utc_start=NOW)
        store = DeterministicStateStoreContractModel(clock=clock)
        store.health_status = store.health_status.UNAVAILABLE
        await store.open()
        context = _context(
            clock=clock,
            supervisor=TaskSupervisor(),
            state_store=store,
        )
        service = RuntimeService(context=context)
        with self.assertRaises(NsRuntimeStateStoreUnavailableError):
            await service.start()
        await service.stop()

    async def test_shutdown_reuses_single_owner_and_closes_store_before_sinks(self) -> None:
        events: list[str] = []
        clock = ControlledClock(utc_start=NOW)
        supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        store = DeterministicStateStoreContractModel(clock=clock, events=events)
        await store.open()
        context = _context(
            clock=clock,
            supervisor=supervisor,
            state_store=store,
            metrics=_RecordingMetricsSink(events),
        )
        started = asyncio.Event()

        async def worker() -> None:
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                events.append("task:cancelled")

        supervisor.create_task(worker(), name="state-store-test-worker")
        await started.wait()
        coordinator = RuntimeShutdownCoordinator(context=context)
        report = await coordinator.shutdown()

        self.assertTrue(report.clean)
        self.assertLess(events.index("task:cancelled"), events.index("state_store:close"))
        self.assertLess(events.index("state_store:close"), events.index("metrics:flush"))
        self.assertEqual(1, store.close_count)
        self.assertEqual(1, report.phases.count(RuntimeShutdownPhase.CLOSE_STATE_STORE))
        self.assertIs(report, await coordinator.shutdown())
        self.assertEqual(1, store.close_count)


class StrongAuditAuthorityTestCase(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self) -> None:
        self.clock = ControlledClock(utc_start=NOW)
        self.store = DeterministicStateStoreContractModel(clock=self.clock)
        await self.store.open()
        self.authority = StateStoreStrongAuditAuthorityService(
            state_store=self.store,
            namespace=StateNamespace.audit(domain="processor"),
        )
        self.ordinary = DeterministicTestAuditSink()
        self.sink = AuthorityRoutingAuditSink(
            strong_authority=self.authority,
            ordinary_sink=self.ordinary,
        )

    async def asyncTearDown(self) -> None:
        await self.store.close()

    async def test_strong_audit_chain_commits_without_exposing_store_to_processor(self) -> None:
        outcome = await ProcessorAuditBoundary(sink=self.sink).write_final(
            _audit_record(),
        )
        self.assertTrue(outcome.succeeded)
        self.assertEqual(1, sum(len(entries) for entries in self.store.logs.values()))
        self.assertEqual(0, self.ordinary.attempted_count)

        from ns_runtime.processor import ProcessorDependencies, ProcessorContext

        self.assertNotIn(
            "state_store",
            {field.name for field in dataclasses.fields(ProcessorContext)},
        )
        self.assertNotIn(
            "state_store",
            {field.name for field in dataclasses.fields(ProcessorDependencies)},
        )

    async def test_strong_audit_failure_blocks_success_without_retry(self) -> None:
        self.store.write_error = asyncio.TimeoutError()
        outcome = await ProcessorAuditBoundary(sink=self.sink).write_final(
            _audit_record(),
        )
        self.assertFalse(outcome.succeeded)
        self.assertIs(AuditConsistency.STRONG_REQUIRED, outcome.required_consistency)
        self.assertEqual(1, self.store.write_count)
        self.assertEqual({}, self.store.logs)

        with self.assertRaises(NsRuntimeStateStoreIndeterminateWriteError):
            await self.authority.append(_audit_record())
        self.assertEqual(2, self.store.write_count)

    async def test_ordinary_audit_does_not_touch_state_store(self) -> None:
        await self.sink.emit(_audit_record(AuditConsistency.ORDINARY))
        self.assertEqual(0, self.store.write_count)
        self.assertEqual(1, self.ordinary.attempted_count)

    async def test_logging_sink_cannot_claim_strong_audit_success(self) -> None:
        outcome = await ProcessorAuditBoundary(
            sink=LoggingAuditSink(logger=logging.Logger("ordinary-audit")),
        ).write_final(_audit_record())
        self.assertFalse(outcome.succeeded)
        self.assertIs(AuditConsistency.STRONG_REQUIRED, outcome.required_consistency)

    def test_service_contract_is_explicit_and_has_no_lifecycle_owner(self) -> None:
        self.assertTrue(
            issubclass(
                StateStoreStrongAuditAuthorityService,
                StrongAuditAuthorityService,
            ),
        )
        fields = vars(self.authority)
        self.assertNotIn("task_supervisor", fields)
        self.assertNotIn("event_loop", fields)
        self.assertNotIn("shutdown_coordinator", fields)


if __name__ == "__main__":
    unittest.main()
