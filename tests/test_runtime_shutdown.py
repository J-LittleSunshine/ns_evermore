# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import logging
import signal
import unittest
from unittest import mock

from ns_common.async_runtime import TaskSupervisor
from ns_common.config import NsConfig
from ns_common.exceptions import NsValidationError
from ns_common.http_client import NsHttpClientOwner
from ns_common.observability import (
    InMemoryMetricsSink,
    InMemoryTraceSink,
)
from ns_common.time import SystemClock
from ns_runtime.context import RuntimeContext, RuntimeDependencySlots
from ns_runtime.service import RuntimeService, RuntimeServiceState
from ns_runtime.shutdown import (
    RuntimeShutdownCoordinator,
    RuntimeShutdownPhase,
    RuntimeShutdownReason,
)


class _RecordingSink:
    def __init__(
        self,
        name: str,
        events: list[str],
        *,
        flush_error: Exception | None = None,
        close_error: Exception | None = None,
    ) -> None:
        self.name = name
        self.events = events
        self.flush_error = flush_error
        self.close_error = close_error

    def record(self, _record: object) -> bool:
        return True

    async def flush(self) -> None:
        self.events.append(f"flush:{self.name}")
        if self.flush_error is not None:
            raise self.flush_error

    async def aclose(self) -> None:
        self.events.append(f"close:{self.name}")
        if self.close_error is not None:
            raise self.close_error


class _RecordingHttpOwner(NsHttpClientOwner):
    def __init__(
        self,
        events: list[str],
        *,
        close_error: Exception | None = None,
    ) -> None:
        super().__init__()
        self._events = events
        self._close_error = close_error

    async def aclose(self) -> None:
        self._events.append("close:http")
        if self._close_error is not None:
            raise self._close_error
        await super().aclose()


class _ListHandler(logging.Handler):
    def __init__(self, events: list[str]) -> None:
        super().__init__()
        self.events = events
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.events.append("summary")
        self.records.append(record)


class _RecordingTransportLifecycleOwner:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def stop_admission_now(self) -> None:
        self.events.append("transport:stop-now")

    async def stop_admission(self) -> None:
        self.events.append("transport:stop")

    async def drain(self) -> None:
        self.events.append("transport:drain")

    async def close(self) -> None:
        self.events.append("transport:close")


class _RecordingLogicalLifecycleOwner:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def stop_admission_now(self) -> None:
        self.events.append("logical:stop-now")

    async def stop_admission(self) -> None:
        self.events.append("logical:stop")

    async def drain(self) -> None:
        self.events.append("logical:drain")


def _context(
    *,
    logger: logging.Logger,
    supervisor: TaskSupervisor,
    metrics: object,
    traces: object,
    diagnostic: object | None = None,
    http_owner: NsHttpClientOwner | None = None,
) -> RuntimeContext:
    return RuntimeContext(
        config=NsConfig(),
        clock=SystemClock(),
        logger=logger,
        metrics=metrics,  # type: ignore[arg-type]
        traces=traces,  # type: ignore[arg-type]
        task_supervisor=supervisor,
        dependencies=RuntimeDependencySlots(
            diagnostic_snapshot_sink=diagnostic,  # type: ignore[arg-type]
            http_client_owner=http_owner,
        ),
    )


class RuntimeShutdownCoordinatorTestCase(unittest.IsolatedAsyncioTestCase):

    async def test_p05_logical_owner_precedes_transport_drain_and_supervisor(self) -> None:
        events: list[str] = []
        supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        context = _context(
            logger=logging.Logger("runtime-p05-shutdown-order"),
            supervisor=supervisor,
            metrics=InMemoryMetricsSink(),
            traces=InMemoryTraceSink(),
        )
        coordinator = RuntimeShutdownCoordinator(
            context=context,
            transport_owner=_RecordingTransportLifecycleOwner(events),
            logical_connection_owner=_RecordingLogicalLifecycleOwner(events),
        )

        coordinator.request_shutdown(RuntimeShutdownReason.SERVICE_STOP)
        report = await coordinator.shutdown()

        self.assertTrue(report.clean)
        self.assertEqual(
            [
                "transport:stop-now",
                "logical:stop-now",
                "transport:stop",
                "logical:stop",
                "logical:drain",
                "transport:drain",
                "transport:close",
            ],
            events,
        )
        self.assertLess(
            report.phases.index(RuntimeShutdownPhase.DRAIN_LOGICAL_CONNECTIONS),
            report.phases.index(RuntimeShutdownPhase.DRAIN_TRANSPORT),
        )

    async def test_shutdown_order_summary_and_repetition_are_deterministic(
        self,
    ) -> None:
        events: list[str] = []
        logger = logging.Logger("runtime-shutdown-order")
        handler = _ListHandler(events)
        logger.addHandler(handler)
        supervisor = TaskSupervisor(shutdown_timeout_seconds=1)

        task_started = asyncio.Event()

        async def background_task() -> None:
            task_started.set()
            try:
                await asyncio.Event().wait()
            finally:
                events.append("task:cancelled")

        supervisor.create_task(background_task(), name="background", cancel_order=10)
        await task_started.wait()

        metrics = _RecordingSink("metrics", events)
        traces = _RecordingSink("traces", events)
        diagnostic = _RecordingSink("diagnostic", events)
        http_owner = _RecordingHttpOwner(events)
        context = _context(
            logger=logger,
            supervisor=supervisor,
            metrics=metrics,
            traces=traces,
            diagnostic=diagnostic,
            http_owner=http_owner,
        )
        coordinator = RuntimeShutdownCoordinator(
            context=context,
            logger_close=lambda: events.append("close:logger"),
        )

        self.assertTrue(
            coordinator.request_shutdown(RuntimeShutdownReason.SIGTERM),
        )
        self.assertFalse(
            coordinator.request_shutdown(RuntimeShutdownReason.SIGINT),
        )
        self.assertFalse(coordinator.admission_open)
        report = await coordinator.shutdown()

        self.assertEqual(RuntimeShutdownReason.SIGTERM, report.reason)
        self.assertEqual(("background",), report.cancelled_tasks)
        self.assertTrue(report.clean)
        self.assertEqual(
            tuple(RuntimeShutdownPhase),
            report.phases,
        )
        self.assertLess(events.index("task:cancelled"), events.index("flush:metrics"))
        self.assertLess(events.index("flush:diagnostic"), events.index("close:metrics"))
        self.assertLess(events.index("close:diagnostic"), events.index("close:http"))
        self.assertLess(events.index("close:http"), events.index("summary"))
        self.assertLess(events.index("summary"), events.index("close:logger"))
        self.assertEqual("runtime_shutdown_summary", handler.records[0].event)
        self.assertEqual(0, handler.records[0].task_unfinished_count)

        events_before_repeat = list(events)
        self.assertIs(report, await coordinator.shutdown())
        self.assertEqual(events_before_repeat, events)

    async def test_cleanup_failures_are_safe_and_do_not_skip_later_resources(
        self,
    ) -> None:
        events: list[str] = []
        logger = logging.Logger("runtime-shutdown-failures")
        handler = _ListHandler(events)
        logger.addHandler(handler)
        context = _context(
            logger=logger,
            supervisor=TaskSupervisor(),
            metrics=_RecordingSink(
                "metrics",
                events,
                flush_error=RuntimeError("metrics-secret"),
            ),
            traces=_RecordingSink(
                "traces",
                events,
                close_error=ValueError("trace-secret"),
            ),
            http_owner=_RecordingHttpOwner(
                events,
                close_error=OSError("http-secret"),
            ),
        )

        def failing_logger_close() -> None:
            events.append("close:logger")
            raise LookupError("logger-secret")

        coordinator = RuntimeShutdownCoordinator(
            context=context,
            logger_close=failing_logger_close,
        )
        report = await coordinator.shutdown()

        self.assertFalse(report.clean)
        self.assertEqual(
            (
                ("flush_sinks", "metrics", "RuntimeError"),
                ("close_sinks", "traces", "ValueError"),
                ("close_clients", "http_client_owner", "OSError"),
                ("close_logger", "runtime_logger", "LookupError"),
            ),
            tuple(
                (failure.phase.value, failure.resource, failure.error_type)
                for failure in report.failures
            ),
        )
        self.assertIn("close:metrics", events)
        self.assertIn("close:traces", events)
        self.assertIn("close:http", events)
        self.assertIn("summary", events)
        self.assertIn("close:logger", events)
        self.assertNotIn("metrics-secret", repr(report))
        self.assertNotIn("trace-secret", repr(report))
        self.assertNotIn("http-secret", repr(report))
        self.assertNotIn("logger-secret", repr(report))

    async def test_task_timeout_is_observable_without_logging_task_errors(self) -> None:
        events: list[str] = []
        logger = logging.Logger("runtime-shutdown-timeout")
        handler = _ListHandler(events)
        logger.addHandler(handler)
        supervisor = TaskSupervisor(shutdown_timeout_seconds=0.001)
        release = asyncio.Event()
        started = asyncio.Event()

        async def cancellation_resistant_task() -> None:
            started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                await release.wait()

        task = supervisor.create_task(
            cancellation_resistant_task(),
            name="unfinished-worker",
        )
        await started.wait()
        context = _context(
            logger=logger,
            supervisor=supervisor,
            metrics=InMemoryMetricsSink(),
            traces=InMemoryTraceSink(),
        )
        coordinator = RuntimeShutdownCoordinator(context=context)

        report = await coordinator.shutdown()
        self.assertTrue(report.timed_out)
        self.assertEqual(("unfinished-worker",), report.unfinished_tasks)
        self.assertEqual(1, handler.records[0].task_unfinished_count)
        self.assertEqual(1, len(handler.records[0].task_unfinished_digests))
        self.assertNotIn("unfinished-worker", repr(vars(handler.records[0])))

        release.set()
        await asyncio.wait_for(task, timeout=1)

    async def test_real_signal_registration_uses_first_signal_and_restores(self) -> None:
        logger = logging.Logger("runtime-shutdown-signal")
        context = _context(
            logger=logger,
            supervisor=TaskSupervisor(),
            metrics=InMemoryMetricsSink(),
            traces=InMemoryTraceSink(),
        )
        coordinator = RuntimeShutdownCoordinator(context=context)

        previous = signal.getsignal(signal.SIGTERM)
        with coordinator.install_signal_handlers():
            signal.raise_signal(signal.SIGTERM)
            reason = await asyncio.wait_for(
                coordinator.wait_requested(),
                timeout=1,
            )
            self.assertEqual(RuntimeShutdownReason.SIGTERM, reason)
        self.assertEqual(previous, signal.getsignal(signal.SIGTERM))

    async def test_loop_signal_registration_restores_exact_custom_handlers(
        self,
    ) -> None:
        context = _context(
            logger=logging.Logger("runtime-signal-loop-restore"),
            supervisor=TaskSupervisor(),
            metrics=InMemoryMetricsSink(),
            traces=InMemoryTraceSink(),
        )
        coordinator = RuntimeShutdownCoordinator(context=context)

        def original_sigint(_signum: int, _frame: object) -> None:
            return None

        def original_sigterm(_signum: int, _frame: object) -> None:
            return None

        previous = {
            signal.SIGINT: signal.getsignal(signal.SIGINT),
            signal.SIGTERM: signal.getsignal(signal.SIGTERM),
        }
        try:
            signal.signal(signal.SIGINT, original_sigint)
            signal.signal(signal.SIGTERM, original_sigterm)
            with coordinator.install_signal_handlers() as registration:
                pass
            registration.close()

            self.assertIs(original_sigint, signal.getsignal(signal.SIGINT))
            self.assertIs(original_sigterm, signal.getsignal(signal.SIGTERM))
        finally:
            signal.signal(signal.SIGINT, previous[signal.SIGINT])
            signal.signal(signal.SIGTERM, previous[signal.SIGTERM])

    async def test_fallback_signal_registration_restores_exact_custom_handlers(
        self,
    ) -> None:
        context = _context(
            logger=logging.Logger("runtime-signal-fallback-restore"),
            supervisor=TaskSupervisor(),
            metrics=InMemoryMetricsSink(),
            traces=InMemoryTraceSink(),
        )
        coordinator = RuntimeShutdownCoordinator(context=context)
        loop = asyncio.get_running_loop()

        def original_sigint(_signum: int, _frame: object) -> None:
            return None

        def original_sigterm(_signum: int, _frame: object) -> None:
            return None

        previous = {
            signal.SIGINT: signal.getsignal(signal.SIGINT),
            signal.SIGTERM: signal.getsignal(signal.SIGTERM),
        }
        try:
            signal.signal(signal.SIGINT, original_sigint)
            signal.signal(signal.SIGTERM, original_sigterm)
            with mock.patch.object(
                loop,
                "add_signal_handler",
                side_effect=NotImplementedError,
            ):
                with coordinator.install_signal_handlers() as registration:
                    pass
                registration.close()

            self.assertIs(original_sigint, signal.getsignal(signal.SIGINT))
            self.assertIs(original_sigterm, signal.getsignal(signal.SIGTERM))
        finally:
            signal.signal(signal.SIGINT, previous[signal.SIGINT])
            signal.signal(signal.SIGTERM, previous[signal.SIGTERM])

    async def test_runtime_service_exposes_shutdown_report_and_stops_cleanly(
        self,
    ) -> None:
        context = _context(
            logger=logging.Logger("runtime-service-shutdown"),
            supervisor=TaskSupervisor(),
            metrics=InMemoryMetricsSink(),
            traces=InMemoryTraceSink(),
        )
        coordinator = RuntimeShutdownCoordinator(context=context)
        service = RuntimeService(
            context=context,
            shutdown_coordinator=coordinator,
        )

        await service.start()
        await service.stop()

        self.assertIs(RuntimeServiceState.STOPPED, service.state)
        self.assertIs(coordinator.report, service.shutdown_report)
        self.assertEqual(
            RuntimeShutdownReason.SERVICE_STOP,
            service.shutdown_report.reason,  # type: ignore[union-attr]
        )

    async def test_runtime_service_rejects_coordinator_for_another_context(
        self,
    ) -> None:
        first_context = _context(
            logger=logging.Logger("runtime-shutdown-first-context"),
            supervisor=TaskSupervisor(),
            metrics=InMemoryMetricsSink(),
            traces=InMemoryTraceSink(),
        )
        second_context = _context(
            logger=logging.Logger("runtime-shutdown-second-context"),
            supervisor=TaskSupervisor(),
            metrics=InMemoryMetricsSink(),
            traces=InMemoryTraceSink(),
        )
        coordinator = RuntimeShutdownCoordinator(context=first_context)

        with self.assertRaisesRegex(
            NsValidationError,
            "shutdown coordinator context is invalid",
        ) as captured:
            RuntimeService(
                context=second_context,
                shutdown_coordinator=coordinator,
            )

        self.assertEqual(
            {
                "component": "runtime_service",
                "dependency": "shutdown_coordinator.context",
                "reason": "context_identity_mismatch",
            },
            captured.exception.details,
        )


if __name__ == "__main__":
    unittest.main()
