# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import importlib.util
import logging
import unittest
from unittest import mock

from ns_common.async_runtime import NsEventLoopImplementation, TaskSupervisor
from ns_common.config import NsConfig
from ns_common.observability import InMemoryMetricsSink, InMemoryTraceSink
from ns_common.time import SystemClock
from ns_runtime.context import RuntimeContext
from ns_runtime.event_loop_observability import RuntimeEventLoopMonitor
from ns_runtime.main import _run_service_once
from ns_runtime.service import RuntimeServiceState
from ns_runtime.shutdown import RuntimeShutdownPhase, RuntimeShutdownReason
from ns_runtime.transport import (
    TransportAdapter,
    TransportCapabilities,
    TransportManager,
    TransportManagerState,
    TransportIdentityFactory,
    TransportMetricsRecorder,
    TransportRuntimeService,
    WebSocketTcpAdapter,
    WebSocketTcpAdapterOptions,
)


class _RecordingAdapter(TransportAdapter):
    def __init__(
        self,
        name: str,
        events: list[str],
        *,
        failures: dict[str, BaseException] | None = None,
    ) -> None:
        self.name = name
        self.events = events
        self.failures = failures or {}
        self._accepting = False

    @property
    def transport_type(self) -> str:
        return self.name

    @property
    def capabilities(self) -> TransportCapabilities:
        return TransportCapabilities()

    @property
    def accepting(self) -> bool:
        return self._accepting

    def _record(self, operation: str) -> None:
        self.events.append(f"{operation}:{self.name}")
        failure = self.failures.get(operation)
        if failure is not None:
            raise failure

    async def start(self) -> None:
        self._record("start")
        self._accepting = True

    async def accept(self) -> object:  # type: ignore[override]
        raise NotImplementedError

    def stop_admission_now(self) -> None:
        self._accepting = False
        self._record("stop_now")

    async def stop_admission(self) -> None:
        self._accepting = False
        self._record("stop_admission")

    async def drain(self) -> None:
        self._record("drain")

    async def close(self) -> None:
        self._accepting = False
        self._record("close")


class _OwnedResourceAdapter(_RecordingAdapter):
    def __init__(
        self,
        name: str,
        events: list[str],
        *,
        supervisor: TaskSupervisor,
    ) -> None:
        super().__init__(name, events)
        self._supervisor = supervisor
        self.listener_open = False
        self.session_open = False
        self.resource_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        await super().start()
        self.listener_open = True
        self.session_open = True

        async def resource_task() -> None:
            try:
                await asyncio.Event().wait()
            finally:
                self.session_open = False

        self.resource_task = self._supervisor.create_task(
            resource_task(),
            name="owned-transport-resource",
            cancel_order=20,
        )

    async def close(self) -> None:
        self.listener_open = False
        self.session_open = False
        await super().close()


def _context(supervisor: TaskSupervisor) -> RuntimeContext:
    return RuntimeContext(
        config=NsConfig(),
        clock=SystemClock(),
        logger=logging.Logger("transport-lifecycle-test"),
        metrics=InMemoryMetricsSink(),
        traces=InMemoryTraceSink(),
        task_supervisor=supervisor,
    )


class TransportLifecycleTestCase(unittest.IsolatedAsyncioTestCase):
    @unittest.skipUnless(
        importlib.util.find_spec("websockets") is not None,
        "runtime transport dependency isn't installed",
    )
    async def test_real_adapter_service_lifecycle_delivers_then_drains(self) -> None:
        from websockets.asyncio.client import connect

        supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        context = _context(supervisor)
        adapter = WebSocketTcpAdapter(
            options=WebSocketTcpAdapterOptions(
                host="127.0.0.1",
                port=0,
                clock=context.clock,
                environment="test",
                allow_plaintext_non_prod=True,
                close_timeout_seconds=1,
                adapter_shutdown_timeout_seconds=1,
            ),
            task_supervisor=supervisor,
            identity_factory=TransportIdentityFactory(),
            metrics=TransportMetricsRecorder(
                clock=context.clock,
                sink=context.metrics,
            ),
        )
        service = TransportRuntimeService(
            context=context,
            transport_manager=TransportManager((adapter,)),
        )
        await service.start()
        client = await connect(
            f"ws://127.0.0.1:{adapter.bound_port}",
            proxy=None,
        )
        session = await adapter.accept()
        await client.send("before-shutdown")
        self.assertEqual("before-shutdown", (await session.receive()).text)

        service.shutdown_coordinator.request_shutdown(
            RuntimeShutdownReason.EXTERNAL,
        )
        self.assertFalse(adapter.accepting)
        await service.stop()
        await asyncio.wait_for(client.wait_closed(), timeout=1)
        self.assertEqual(RuntimeServiceState.STOPPED, service.state)
        self.assertEqual(TransportManagerState.CLOSED, service.transport_manager.state)
        names = {record.name for record in context.metrics.records}  # type: ignore[attr-defined]
        self.assertIn("runtime_transport_connections", names)
        self.assertIn("runtime_transport_bytes_received_total", names)
        self.assertIn("runtime_transport_close_total", names)

    async def test_service_uses_existing_coordinator_and_exact_transport_shutdown_order(
        self,
    ) -> None:
        events: list[str] = []
        supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        started = asyncio.Event()

        async def background() -> None:
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                events.append("task_cancelled")

        supervisor.create_task(background(), name="lifecycle-background")
        await started.wait()
        adapter = _RecordingAdapter("websocket_tcp", events)
        manager = TransportManager((adapter,))
        context = _context(supervisor)
        service = TransportRuntimeService(
            context=context,
            transport_manager=manager,
        )

        await service.start()
        self.assertEqual(TransportManagerState.RUNNING, manager.state)
        self.assertIs(context, service.shutdown_coordinator.context)
        self.assertTrue(service.shutdown_coordinator.request_shutdown(
            RuntimeShutdownReason.SIGTERM,
        ))
        self.assertFalse(adapter.accepting)
        self.assertEqual(["start:websocket_tcp", "stop_now:websocket_tcp"], events)

        await service.stop()
        self.assertEqual(RuntimeServiceState.STOPPED, service.state)
        self.assertEqual(TransportManagerState.CLOSED, manager.state)
        self.assertEqual(
            [
                "start:websocket_tcp",
                "stop_now:websocket_tcp",
                "stop_admission:websocket_tcp",
                "drain:websocket_tcp",
                "close:websocket_tcp",
                "task_cancelled",
            ],
            events,
        )
        self.assertEqual(tuple(RuntimeShutdownPhase), service.shutdown_report.phases)

    async def test_ordinary_adapter_failure_isolated_and_safe(self) -> None:
        events: list[str] = []
        supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        manager = TransportManager((
            _RecordingAdapter(
                "websocket_tcp",
                events,
                failures={"drain": RuntimeError("peer secret")},
            ),
            _RecordingAdapter("websocket_http3", events),
        ))
        service = TransportRuntimeService(
            context=_context(supervisor),
            transport_manager=manager,
        )
        await service.start()
        await service.stop()

        self.assertIn("drain:websocket_http3", events)
        self.assertIn("close:websocket_tcp", events)
        failures = service.shutdown_report.failures
        self.assertEqual(1, len(failures))
        self.assertEqual(RuntimeShutdownPhase.DRAIN_TRANSPORT, failures[0].phase)
        self.assertNotIn("peer secret", repr(service.shutdown_report))

    async def test_base_exception_from_transport_drain_preserves_identity(self) -> None:
        events: list[str] = []
        fatal = KeyboardInterrupt()
        manager = TransportManager((
            _RecordingAdapter(
                "websocket_tcp",
                events,
                failures={"drain": fatal},
            ),
        ))
        service = TransportRuntimeService(
            context=_context(TaskSupervisor()),
            transport_manager=manager,
        )
        await service.start()
        with self.assertRaises(KeyboardInterrupt) as raised:
            await service.stop()
        self.assertIs(fatal, raised.exception)
        self.assertEqual(RuntimeServiceState.FAILED, service.state)

    async def test_start_failure_closes_already_started_adapter(self) -> None:
        events: list[str] = []
        failure = RuntimeError("listener secret")
        manager = TransportManager((
            _RecordingAdapter("websocket_tcp", events),
            _RecordingAdapter(
                "websocket_http3",
                events,
                failures={"start": failure},
            ),
        ))
        with self.assertRaises(RuntimeError) as raised:
            await manager.start()
        self.assertIs(failure, raised.exception)
        self.assertEqual(TransportManagerState.FAILED, manager.state)
        self.assertEqual(
            [
                "start:websocket_tcp",
                "start:websocket_http3",
                "close:websocket_tcp",
            ],
            events,
        )

    async def test_composition_root_cleans_transport_after_monitor_start_failure(
        self,
    ) -> None:
        events: list[str] = []
        supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        context = _context(supervisor)
        adapter = _OwnedResourceAdapter(
            "websocket_tcp",
            events,
            supervisor=supervisor,
        )
        manager = TransportManager((adapter,))
        monitor = RuntimeEventLoopMonitor(
            context=context,
            implementation=NsEventLoopImplementation.ASYNCIO,
        )
        service = TransportRuntimeService(
            context=context,
            transport_manager=manager,
            event_loop_monitor=monitor,
        )
        failure = RuntimeError("monitor credential must not escape")

        with mock.patch.object(
            RuntimeEventLoopMonitor,
            "start",
            side_effect=failure,
        ):
            with self.assertRaises(RuntimeError) as raised:
                await _run_service_once(service)

        self.assertIs(failure, raised.exception)
        self.assertEqual(RuntimeServiceState.STOPPED, service.state)
        self.assertEqual(TransportManagerState.CLOSED, manager.state)
        self.assertFalse(adapter.accepting)
        self.assertFalse(adapter.listener_open)
        self.assertFalse(adapter.session_open)
        self.assertTrue(adapter.resource_task.done())
        self.assertEqual(
            [
                "start:websocket_tcp",
                "stop_now:websocket_tcp",
                "stop_admission:websocket_tcp",
                "drain:websocket_tcp",
                "close:websocket_tcp",
            ],
            events,
        )
        self.assertEqual((), service.shutdown_report.unfinished_tasks)

    async def test_composition_root_cleans_transport_after_start_cancellation(
        self,
    ) -> None:
        events: list[str] = []
        context = _context(TaskSupervisor(shutdown_timeout_seconds=1))
        adapter = _RecordingAdapter("websocket_tcp", events)
        manager = TransportManager((adapter,))
        monitor = RuntimeEventLoopMonitor(
            context=context,
            implementation=NsEventLoopImplementation.ASYNCIO,
        )
        service = TransportRuntimeService(
            context=context,
            transport_manager=manager,
            event_loop_monitor=monitor,
        )
        cancellation = asyncio.CancelledError()

        with mock.patch.object(
            RuntimeEventLoopMonitor,
            "start",
            side_effect=cancellation,
        ):
            with self.assertRaises(asyncio.CancelledError) as raised:
                await _run_service_once(service)

        self.assertIs(cancellation, raised.exception)
        self.assertEqual(RuntimeServiceState.STOPPED, service.state)
        self.assertEqual(TransportManagerState.CLOSED, manager.state)
        self.assertFalse(adapter.accepting)

    async def test_process_level_cleanup_failure_precedes_ordinary_start_failure(
        self,
    ) -> None:
        events: list[str] = []
        fatal = KeyboardInterrupt()
        context = _context(TaskSupervisor(shutdown_timeout_seconds=1))
        adapter = _RecordingAdapter(
            "websocket_tcp",
            events,
            failures={"close": fatal},
        )
        manager = TransportManager((adapter,))
        monitor = RuntimeEventLoopMonitor(
            context=context,
            implementation=NsEventLoopImplementation.ASYNCIO,
        )
        service = TransportRuntimeService(
            context=context,
            transport_manager=manager,
            event_loop_monitor=monitor,
        )

        with mock.patch.object(
            RuntimeEventLoopMonitor,
            "start",
            side_effect=RuntimeError("ordinary start failure"),
        ):
            with self.assertRaises(KeyboardInterrupt) as raised:
                await _run_service_once(service)

        self.assertIs(fatal, raised.exception)
        self.assertEqual(RuntimeServiceState.FAILED, service.state)

    async def test_ordinary_cleanup_failure_does_not_replace_start_failure(
        self,
    ) -> None:
        events: list[str] = []
        start_failure = RuntimeError("monitor start secret")
        context = _context(TaskSupervisor(shutdown_timeout_seconds=1))
        adapter = _RecordingAdapter(
            "websocket_tcp",
            events,
            failures={"close": RuntimeError("transport cleanup secret")},
        )
        service = TransportRuntimeService(
            context=context,
            transport_manager=TransportManager((adapter,)),
            event_loop_monitor=RuntimeEventLoopMonitor(
                context=context,
                implementation=NsEventLoopImplementation.ASYNCIO,
            ),
        )

        with mock.patch.object(
            RuntimeEventLoopMonitor,
            "start",
            side_effect=start_failure,
        ):
            with self.assertRaises(RuntimeError) as raised:
                await _run_service_once(service)

        self.assertIs(start_failure, raised.exception)
        self.assertEqual(RuntimeServiceState.STOPPED, service.state)
        self.assertEqual(1, len(service.shutdown_report.failures))
        self.assertNotIn("transport cleanup secret", repr(service.shutdown_report))

    async def test_direct_ordinary_stop_error_preserves_start_error_identity(
        self,
    ) -> None:
        start_failure = RuntimeError("start secret")
        cleanup_failure = RuntimeError("cleanup secret")
        context = _context(TaskSupervisor(shutdown_timeout_seconds=1))

        class FailingService:
            def __init__(self) -> None:
                from ns_runtime.shutdown import RuntimeShutdownCoordinator

                self.shutdown_coordinator = RuntimeShutdownCoordinator(
                    context=context,
                )

            async def start(self) -> None:
                raise start_failure

            async def stop(self) -> None:
                raise cleanup_failure

        with self.assertRaises(RuntimeError) as raised:
            await _run_service_once(FailingService())  # type: ignore[arg-type]

        self.assertIs(start_failure, raised.exception)
