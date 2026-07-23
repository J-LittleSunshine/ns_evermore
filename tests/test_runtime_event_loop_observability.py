# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
from io import StringIO
import logging
import unittest
from datetime import datetime

from ns_common.async_runtime import (
    NsEventLoopImplementation,
    TaskSupervisor,
)
from ns_common.config import NsConfig
from ns_common.exceptions import NsValidationError
from ns_common.observability import (
    InMemoryMetricsSink,
    InMemoryTraceSink,
    NsMetricKind,
    RUNTIME_EVENT_LOOP_METRIC_NAMES,
)
from ns_common.time import SystemClock
from ns_runtime.context import RuntimeContext
from ns_runtime.event_loop_observability import (
    EVENT_LOOP_MONITOR_TASK_NAME,
    RuntimeEventLoopMonitor,
)
from ns_runtime.service import RuntimeService, RuntimeServiceState
from ns_runtime.shutdown import (
    RuntimeShutdownCoordinator,
    RuntimeShutdownReason,
    RuntimeShutdownReport,
)


def _context(
    *,
    config: NsConfig | None = None,
    metrics: object | None = None,
    clock: object | None = None,
) -> RuntimeContext:
    return RuntimeContext(
        config=config or NsConfig(),
        clock=clock or SystemClock(),  # type: ignore[arg-type]
        logger=logging.Logger("runtime-event-loop-observability"),
        metrics=metrics or InMemoryMetricsSink(),  # type: ignore[arg-type]
        traces=InMemoryTraceSink(),
        task_supervisor=TaskSupervisor(shutdown_timeout_seconds=1),
    )


class _RejectingMetricsSink:
    def record(self, _record: object) -> bool:
        return False

    async def flush(self) -> None:
        return None

    async def aclose(self) -> None:
        return None


class _FailingClock(SystemClock):
    def utc_now(self) -> datetime:
        raise RuntimeError("clock-secret")


class _FailingMonitor(RuntimeEventLoopMonitor):
    async def _run(self, _loop: asyncio.AbstractEventLoop) -> None:
        await asyncio.sleep(0)
        raise RuntimeError("critical-monitor-secret")


class _CountingShutdownCoordinator(RuntimeShutdownCoordinator):
    def __init__(self, *, context: RuntimeContext) -> None:
        super().__init__(context=context)
        self.shutdown_count = 0

    async def shutdown(self) -> RuntimeShutdownReport:
        self.shutdown_count += 1
        return await super().shutdown()


class _CountingStopService(RuntimeService):
    def __init__(
        self,
        *,
        context: RuntimeContext,
        shutdown_coordinator: RuntimeShutdownCoordinator,
        event_loop_monitor: RuntimeEventLoopMonitor,
    ) -> None:
        super().__init__(
            context=context,
            shutdown_coordinator=shutdown_coordinator,
            event_loop_monitor=event_loop_monitor,
        )
        self.stop_hook_count = 0

    async def _on_stop(self) -> None:
        self.stop_hook_count += 1


class RuntimeEventLoopMonitorTestCase(unittest.IsolatedAsyncioTestCase):

    async def test_snapshot_and_all_standard_metrics_are_bounded_and_readable(
        self,
    ) -> None:
        loop = asyncio.get_running_loop()
        metrics = InMemoryMetricsSink(capacity=64)
        context = _context(metrics=metrics)
        monitor = RuntimeEventLoopMonitor(
            context=context,
            implementation=NsEventLoopImplementation.ASYNCIO,
            history_size=3,
            pending_task_probe=lambda _loop: 4,
            executor_queue_depth_probe=lambda _loop: 7,
        )

        for lag_ms in (10.0, 20.0, 200.0, 5.0):
            snapshot = monitor._capture_sample(loop, lag_ms=lag_ms)

        self.assertEqual(
            NsEventLoopImplementation.ASYNCIO,
            snapshot.implementation,
        )
        self.assertEqual(5.0, snapshot.latest_lag_ms)
        self.assertEqual(200.0, snapshot.lag_p95_ms)
        self.assertEqual(200.0, snapshot.lag_p99_ms)
        self.assertEqual(4, snapshot.sample_count)
        self.assertEqual(1, snapshot.slow_callback_count)
        self.assertEqual(4, snapshot.pending_task_count)
        self.assertEqual(7, snapshot.executor_queue_depth)
        self.assertEqual(0, snapshot.probe_failure_count)
        self.assertEqual(0, snapshot.metric_rejection_count)

        latest_records = metrics.records[-len(RUNTIME_EVENT_LOOP_METRIC_NAMES):]
        self.assertEqual(
            set(RUNTIME_EVENT_LOOP_METRIC_NAMES),
            {record.name for record in latest_records},
        )
        by_name = {record.name: record for record in latest_records}
        self.assertEqual(
            {"implementation": "asyncio"},
            dict(by_name["runtime_event_loop_implementation"].attributes),
        )
        self.assertEqual(
            {"component_type": "runtime"},
            dict(by_name["runtime_pending_task_count"].attributes),
        )
        self.assertIs(
            NsMetricKind.HISTOGRAM,
            by_name["runtime_event_loop_lag_ms"].kind,
        )
        self.assertIs(
            NsMetricKind.COUNTER,
            by_name["runtime_slow_callback_total"].kind,
        )

    async def test_asyncio_and_uvloop_implementation_values_are_explicit(
        self,
    ) -> None:
        loop = asyncio.get_running_loop()
        for implementation in NsEventLoopImplementation:
            with self.subTest(implementation=implementation):
                metrics = InMemoryMetricsSink()
                monitor = RuntimeEventLoopMonitor(
                    context=_context(metrics=metrics),
                    implementation=implementation,
                )
                monitor._capture_sample(loop, lag_ms=0.0)
                record = next(
                    item
                    for item in metrics.records
                    if item.name == "runtime_event_loop_implementation"
                )
                self.assertEqual(
                    implementation.value,
                    record.attributes["implementation"],
                )

    async def test_metrics_disabled_and_sink_rejection_do_not_break_snapshot(
        self,
    ) -> None:
        loop = asyncio.get_running_loop()
        disabled_config = NsConfig.from_dict({
            "runtime": {
                "observability": {
                    "metrics_enabled": False,
                },
            },
        })
        disabled_metrics = InMemoryMetricsSink()
        disabled_monitor = RuntimeEventLoopMonitor(
            context=_context(
                config=disabled_config,
                metrics=disabled_metrics,
            ),
            implementation=NsEventLoopImplementation.ASYNCIO,
        )
        snapshot = disabled_monitor._capture_sample(loop, lag_ms=1.0)
        self.assertEqual(1, snapshot.sample_count)
        self.assertEqual((), disabled_metrics.records)

        rejecting_monitor = RuntimeEventLoopMonitor(
            context=_context(metrics=_RejectingMetricsSink()),
            implementation=NsEventLoopImplementation.ASYNCIO,
        )
        snapshot = rejecting_monitor._capture_sample(loop, lag_ms=1.0)
        self.assertEqual(
            len(RUNTIME_EVENT_LOOP_METRIC_NAMES),
            snapshot.metric_rejection_count,
        )

        clock_failure_monitor = RuntimeEventLoopMonitor(
            context=_context(clock=_FailingClock()),
            implementation=NsEventLoopImplementation.ASYNCIO,
        )
        snapshot = clock_failure_monitor._capture_sample(loop, lag_ms=1.0)
        self.assertEqual(
            len(RUNTIME_EVENT_LOOP_METRIC_NAMES),
            snapshot.metric_rejection_count,
        )
        self.assertNotIn("clock-secret", repr(snapshot))

        failing_probe_metrics = InMemoryMetricsSink()
        failing_probe_monitor = RuntimeEventLoopMonitor(
            context=_context(metrics=failing_probe_metrics),
            implementation=NsEventLoopImplementation.ASYNCIO,
            pending_task_probe=lambda _loop: (_ for _ in ()).throw(
                RuntimeError("pending-secret"),
            ),
            executor_queue_depth_probe=lambda _loop: -1,
        )
        snapshot = failing_probe_monitor._capture_sample(loop, lag_ms=1.0)
        self.assertIsNone(snapshot.pending_task_count)
        self.assertIsNone(snapshot.executor_queue_depth)
        self.assertEqual(2, snapshot.probe_failure_count)
        self.assertNotIn("pending-secret", repr(snapshot))
        self.assertNotIn(
            "runtime_pending_task_count",
            {record.name for record in failing_probe_metrics.records},
        )
        self.assertNotIn(
            "runtime_executor_queue_depth",
            {record.name for record in failing_probe_metrics.records},
        )

    async def test_constructor_rejects_invalid_inputs_without_object_repr(
        self,
    ) -> None:
        context = _context()
        invalid_cases = (
            {"context": object()},
            {"implementation": "asyncio"},
            {"sample_interval_seconds": 0},
            {"sample_interval_seconds": float("nan")},
            {"history_size": 0},
            {"pending_task_probe": None},
            {"executor_queue_depth_probe": None},
        )
        defaults: dict[str, object] = {
            "context": context,
            "implementation": NsEventLoopImplementation.ASYNCIO,
        }
        for overrides in invalid_cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises(NsValidationError) as captured:
                    RuntimeEventLoopMonitor(  # type: ignore[arg-type]
                        **(defaults | overrides),
                    )
                self.assertNotIn("object at", str(captured.exception.details))

    async def test_service_starts_monitor_and_shutdown_cancels_it_before_sinks(
        self,
    ) -> None:
        metrics = InMemoryMetricsSink()
        context = _context(metrics=metrics)
        monitor = RuntimeEventLoopMonitor(
            context=context,
            implementation=NsEventLoopImplementation.ASYNCIO,
            sample_interval_seconds=60,
        )
        coordinator = RuntimeShutdownCoordinator(context=context)
        service = RuntimeService(
            context=context,
            shutdown_coordinator=coordinator,
            event_loop_monitor=monitor,
        )

        await service.start()
        self.assertIs(RuntimeServiceState.RUNNING, service.state)
        self.assertIs(monitor.snapshot, service.event_loop_snapshot)
        self.assertIn(
            EVENT_LOOP_MONITOR_TASK_NAME,
            context.task_supervisor.pending_task_names,
        )
        self.assertEqual(len(RUNTIME_EVENT_LOOP_METRIC_NAMES), len(metrics.records))

        await service.stop()

        self.assertIs(RuntimeServiceState.STOPPED, service.state)
        self.assertEqual(
            (EVENT_LOOP_MONITOR_TASK_NAME,),
            service.shutdown_report.cancelled_tasks,  # type: ignore[union-attr]
        )
        self.assertEqual(1, context.task_supervisor.cancelled_task_count)
        self.assertTrue(metrics.is_closed)

    async def test_critical_monitor_failure_requests_shutdown_and_fails_service(
        self,
    ) -> None:
        context = _context()
        log_output = StringIO()
        context.logger.addHandler(logging.StreamHandler(log_output))
        monitor = _FailingMonitor(
            context=context,
            implementation=NsEventLoopImplementation.ASYNCIO,
        )
        coordinator = _CountingShutdownCoordinator(context=context)
        service = _CountingStopService(
            context=context,
            shutdown_coordinator=coordinator,
            event_loop_monitor=monitor,
        )

        await service.start()
        reason = await asyncio.wait_for(coordinator.wait_requested(), timeout=1)

        self.assertIs(RuntimeShutdownReason.CRITICAL_TASK_FAILURE, reason)
        self.assertIs(RuntimeServiceState.FAILED, service.state)
        await service.stop()
        self.assertIs(RuntimeServiceState.STOPPED, service.state)
        report = service.shutdown_report
        self.assertIsNotNone(report)
        self.assertIs(RuntimeShutdownReason.CRITICAL_TASK_FAILURE, report.reason)
        self.assertEqual(
            (EVENT_LOOP_MONITOR_TASK_NAME,),
            report.failed_tasks,  # type: ignore[union-attr]
        )
        self.assertEqual(1, service.stop_hook_count)
        self.assertEqual(1, coordinator.shutdown_count)

        await service.stop()
        self.assertIs(RuntimeServiceState.STOPPED, service.state)
        self.assertIs(report, service.shutdown_report)
        self.assertEqual(1, service.stop_hook_count)
        self.assertEqual(1, coordinator.shutdown_count)
        self.assertNotIn("critical-monitor-secret", repr(report))
        self.assertNotIn("critical-monitor-secret", log_output.getvalue())

    async def test_probe_failure_remains_fail_soft_for_running_service(self) -> None:
        context = _context()
        monitor = RuntimeEventLoopMonitor(
            context=context,
            implementation=NsEventLoopImplementation.ASYNCIO,
            sample_interval_seconds=60,
            pending_task_probe=lambda _loop: (_ for _ in ()).throw(
                RuntimeError("ordinary-probe-secret"),
            ),
            executor_queue_depth_probe=lambda _loop: 0,
        )
        service = RuntimeService(
            context=context,
            event_loop_monitor=monitor,
        )

        await service.start()
        self.assertIs(RuntimeServiceState.RUNNING, service.state)
        self.assertEqual(1, monitor.snapshot.probe_failure_count)
        self.assertIsNone(monitor.snapshot.pending_task_count)
        self.assertIsNone(service.shutdown_coordinator.reason)
        self.assertNotIn("ordinary-probe-secret", repr(monitor.snapshot))

        await service.stop()
        self.assertIs(RuntimeServiceState.STOPPED, service.state)

    async def test_service_rejects_monitor_for_another_context(self) -> None:
        first_context = _context()
        second_context = _context()
        monitor = RuntimeEventLoopMonitor(
            context=first_context,
            implementation=NsEventLoopImplementation.ASYNCIO,
        )

        with self.assertRaisesRegex(
            NsValidationError,
            "event-loop monitor context is invalid",
        ) as captured:
            RuntimeService(
                context=second_context,
                event_loop_monitor=monitor,
            )

        self.assertEqual(
            {
                "component": "runtime_service",
                "dependency": "event_loop_monitor.context",
                "reason": "context_identity_mismatch",
            },
            captured.exception.details,
        )


if __name__ == "__main__":
    unittest.main()
