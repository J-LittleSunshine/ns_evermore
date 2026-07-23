# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import importlib.util
import unittest
from typing import Any

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import (
    NsRuntimeTransportFlowControlBlockedError,
    NsRuntimeTransportReceiveFailedError,
    NsRuntimeTransportStreamResetError,
    NsStateError,
)
from ns_common.time import SystemClock
from ns_common.observability import InMemoryMetricsSink
from ns_runtime.transport import (
    TransportCloseReason,
    TransportIdentityFactory,
    TransportMetricsRecorder,
    TransportWriteState,
    WebSocketTcpAdapterOptions,
    WebSocketTcpSession,
)


class _ControlledConnection:
    def __init__(
        self,
        *,
        slow_send: bool = False,
        slow_close: bool = False,
        receive_failure: Exception | None = None,
        ping_failure: Exception | None = None,
        pending_pong: bool = False,
    ) -> None:
        self.inbound: asyncio.Queue[Any] = asyncio.Queue()
        self.slow_send = slow_send
        self.slow_close = slow_close
        self.receive_failure = receive_failure
        self.ping_failure = ping_failure
        self.pending_pong = pending_pong
        self.send_started = asyncio.Event()
        self.release_send = asyncio.Event()
        self.close_started = asyncio.Event()
        self.release_close = asyncio.Event()
        self.sent: list[str] = []
        self.close_code: int | None = None
        self.close_calls = 0

    async def recv(self) -> Any:
        if self.receive_failure is not None:
            raise self.receive_failure
        return await self.inbound.get()

    async def send(self, text: str) -> None:
        self.send_started.set()
        if self.slow_send:
            await self.release_send.wait()
        self.sent.append(text)

    async def ping(self) -> asyncio.Future[float]:
        if self.ping_failure is not None:
            raise self.ping_failure
        future: asyncio.Future[float] = asyncio.get_running_loop().create_future()
        if not self.pending_pong:
            future.set_result(0.0)
        return future

    async def close(self, *, code: int, reason: str) -> None:
        self.close_calls += 1
        self.close_started.set()
        if self.slow_close:
            await self.release_close.wait()
        self.close_code = code


@unittest.skipUnless(
    importlib.util.find_spec("websockets") is not None,
    "runtime transport dependency isn't installed",
)
class TransportBackpressureTestCase(unittest.IsolatedAsyncioTestCase):
    def _session(
        self,
        connection: _ControlledConnection,
        *,
        read_capacity: int = 1,
        write_capacity: int = 1,
        send_timeout: float = 1,
        ping_timeout: float = 1,
        sink: InMemoryMetricsSink | None = None,
        record_connection_opened: bool = False,
    ) -> WebSocketTcpSession:
        supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        self.addAsyncCleanup(supervisor.shutdown)
        clock = SystemClock()
        metrics = TransportMetricsRecorder(
            clock=clock,
            sink=(InMemoryMetricsSink() if sink is None else sink),
        )
        if record_connection_opened:
            metrics.connection_opened()
        session = WebSocketTcpSession(
            connection=connection,
            options=WebSocketTcpAdapterOptions(
                host="127.0.0.1",
                port=0,
                clock=clock,
                environment="test",
                allow_plaintext_non_prod=True,
                read_queue_capacity=read_capacity,
                write_queue_capacity=write_capacity,
                send_timeout_seconds=send_timeout,
                ping_timeout_seconds=ping_timeout,
                close_timeout_seconds=1,
            ),
            task_supervisor=supervisor,
            task_suffix=1,
            identity=TransportIdentityFactory().create(
                local_address=("127.0.0.1", 8765),
                peer_address=("127.0.0.1", 54321),
                validated_at=clock.utc_now(),
            ),
            metrics=metrics,
        )
        self.addAsyncCleanup(session.close)
        return session

    async def test_read_queue_full_closes_without_unbounded_growth(self) -> None:
        connection = _ControlledConnection()
        session = self._session(connection, read_capacity=1)
        await connection.inbound.put("first")
        await connection.inbound.put("second")
        await asyncio.wait_for(session.wait_closed(), timeout=1)

        self.assertEqual(1, session.read_queue_depth)
        self.assertEqual("first", (await session.receive()).text)
        with self.assertRaises(NsRuntimeTransportReceiveFailedError) as raised:
            await session.receive()
        self.assertEqual("read_queue_full", raised.exception.details["reason"])
        self.assertEqual(TransportCloseReason.READ_QUEUE_FULL, session.close_info.reason)
        self.assertEqual(1013, connection.close_code)

    async def test_slow_write_fills_bounded_queue_and_preserves_send_order(self) -> None:
        connection = _ControlledConnection(slow_send=True)
        session = self._session(connection, write_capacity=1)
        first = asyncio.create_task(session.send("first"))
        await connection.send_started.wait()
        second = asyncio.create_task(session.send("second"))
        await asyncio.sleep(0)
        self.assertEqual(1, session.write_queue_depth)

        with self.assertRaises(NsRuntimeTransportFlowControlBlockedError) as raised:
            await session.send("third")
        self.assertEqual("write_queue_full", raised.exception.details["reason"])
        connection.release_send.set()
        results = await asyncio.gather(first, second)
        self.assertEqual(
            [TransportWriteState.SUCCEEDED, TransportWriteState.SUCCEEDED],
            [item.state for item in results],
        )
        self.assertEqual(["first", "second"], connection.sent)

    async def test_cancelled_queued_send_is_not_written(self) -> None:
        connection = _ControlledConnection(slow_send=True)
        session = self._session(connection, write_capacity=1)
        first = asyncio.create_task(session.send("first"))
        await connection.send_started.wait()
        cancelled = asyncio.create_task(session.send("cancelled"))
        await asyncio.sleep(0)
        cancelled.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await cancelled
        connection.release_send.set()
        await first
        await asyncio.sleep(0)
        self.assertEqual(["first"], connection.sent)

    async def test_queued_send_timeout_never_reaches_underlying_connection(
        self,
    ) -> None:
        connection = _ControlledConnection(slow_send=True)
        session = self._session(connection, write_capacity=1, send_timeout=0.01)
        abandoned = asyncio.create_task(session.send("active"))
        await connection.send_started.wait()
        abandoned.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await abandoned

        result = await session.send("queued-timeout")
        self.assertIs(TransportWriteState.NOT_STARTED, result.state)
        self.assertEqual("send_timeout", result.failure_reason)
        self.assertEqual("handshaking", session.state.value)
        connection.release_send.set()
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        self.assertEqual(["active"], connection.sent)

    async def test_send_timeout_is_bounded_and_closes_session(self) -> None:
        connection = _ControlledConnection(slow_send=True)
        session = self._session(connection, send_timeout=0.01)
        result = await session.send("slow")
        self.assertIs(TransportWriteState.UNCERTAIN, result.state)
        self.assertEqual("send_timeout", result.failure_reason)
        await asyncio.wait_for(session.wait_closed(), timeout=1)
        self.assertEqual(TransportCloseReason.SEND_TIMEOUT, session.close_info.reason)
        self.assertEqual([], connection.sent)
        connection.release_send.set()
        await asyncio.sleep(0)
        self.assertEqual([], connection.sent)
        with self.assertRaises(NsStateError):
            await session.send("after-timeout")

    async def test_active_send_timeout_returns_only_after_terminal_close(
        self,
    ) -> None:
        connection = _ControlledConnection(slow_send=True, slow_close=True)
        session = self._session(connection, send_timeout=0.01)
        send_task = asyncio.create_task(session.send("racing-send"))
        await connection.send_started.wait()
        await asyncio.wait_for(connection.close_started.wait(), timeout=1)

        self.assertFalse(send_task.done())
        self.assertEqual("closing", session.state.value)
        connection.release_send.set()
        await asyncio.sleep(0)
        self.assertEqual([], connection.sent)
        self.assertFalse(send_task.done())
        connection.release_close.set()

        result = await send_task
        self.assertIs(TransportWriteState.UNCERTAIN, result.state)
        self.assertEqual("send_timeout", result.failure_reason)
        self.assertEqual("closed", session.state.value)
        self.assertEqual(TransportCloseReason.SEND_TIMEOUT, session.close_info.reason)
        self.assertEqual([], connection.sent)

    async def test_concurrent_close_is_idempotent_and_new_writes_are_rejected(self) -> None:
        connection = _ControlledConnection()
        session = self._session(connection)
        closes = await asyncio.gather(*(session.close() for _ in range(10)))
        self.assertTrue(all(item is closes[0] for item in closes))
        with self.assertRaises(NsStateError):
            await session.send("after-close")

    async def test_generic_receive_failure_uses_exact_terminal_outcome(self) -> None:
        sink = InMemoryMetricsSink()
        connection = _ControlledConnection(
            receive_failure=RuntimeError("credential=must-not-leak"),
        )
        session = self._session(connection, sink=sink)

        with self.assertRaises(NsRuntimeTransportReceiveFailedError) as raised:
            await session.receive()
        await session.wait_closed()

        self.assertEqual("read_failed", raised.exception.details["reason"])
        self.assertEqual(TransportCloseReason.RECEIVE_FAILED, session.close_info.reason)
        self.assertFalse(session.close_info.clean)
        self.assertNotIn("must-not-leak", repr(raised.exception))
        close_metric = next(
            record for record in sink.records
            if record.name == "runtime_transport_close_total"
        )
        self.assertEqual("receive_failed", close_metric.attributes["close_reason"])

    async def test_keepalive_timeout_is_terminal_and_not_reusable(self) -> None:
        sink = InMemoryMetricsSink()
        connection = _ControlledConnection(pending_pong=True)
        session = self._session(connection, ping_timeout=0.01, sink=sink)

        with self.assertRaises(NsRuntimeTransportStreamResetError) as raised:
            await session.ping()
        self.assertEqual("keepalive_timeout", raised.exception.details["reason"])
        self.assertEqual(TransportCloseReason.KEEPALIVE_FAILED, session.close_info.reason)
        self.assertFalse(session.close_info.clean)
        self.assertEqual("closed", session.state.value)
        with self.assertRaises(NsStateError):
            await session.send("after-keepalive-failure")
        with self.assertRaises(NsRuntimeTransportReceiveFailedError):
            await session.receive()
        self.assertIs(session.close_info, await session.close())
        close_metrics = [
            record for record in sink.records
            if record.name == "runtime_transport_close_total"
        ]
        self.assertEqual(1, len(close_metrics))
        self.assertEqual(
            "keepalive_failed",
            close_metrics[0].attributes["close_reason"],
        )
        error_metric = next(
            record for record in sink.records
            if record.name == "runtime_transport_receive_errors_total"
        )
        self.assertEqual(
            "RUNTIME_TRANSPORT_STREAM_RESET",
            error_metric.attributes["error_code"],
        )

    async def test_keepalive_ordinary_failure_is_safe_and_terminal(self) -> None:
        connection = _ControlledConnection(
            ping_failure=RuntimeError("credential=must-not-leak"),
        )
        session = self._session(connection)

        with self.assertRaises(NsRuntimeTransportStreamResetError) as raised:
            await session.ping()
        self.assertEqual("keepalive_failed", raised.exception.details["reason"])
        self.assertNotIn("must-not-leak", repr(raised.exception))
        self.assertEqual(TransportCloseReason.KEEPALIVE_FAILED, session.close_info.reason)

    async def test_cancelled_ping_does_not_publish_keepalive_failure(self) -> None:
        sink = InMemoryMetricsSink()
        connection = _ControlledConnection(pending_pong=True)
        session = self._session(connection, sink=sink)
        ping_task = asyncio.create_task(session.ping())
        await asyncio.sleep(0)
        ping_task.cancel()

        with self.assertRaises(asyncio.CancelledError):
            await ping_task
        self.assertIsNone(session.close_info)
        self.assertEqual("handshaking", session.state.value)
        self.assertFalse(any(
            record.name in {
                "runtime_transport_close_total",
                "runtime_transport_receive_errors_total",
            }
            for record in sink.records
        ))

    async def test_cancelled_close_retains_ownership_and_retry_finalizes_once(
        self,
    ) -> None:
        sink = InMemoryMetricsSink()
        connection = _ControlledConnection(slow_close=True)
        session = self._session(
            connection,
            sink=sink,
            record_connection_opened=True,
        )
        first = asyncio.create_task(session.close())
        await connection.close_started.wait()
        waiter = asyncio.create_task(session.close())
        await asyncio.sleep(0)
        first.cancel()

        with self.assertRaises(asyncio.CancelledError):
            await first
        self.assertEqual("closing", session.state.value)
        self.assertIsNone(session.close_info)
        self.assertFalse(session._closed.is_set())
        self.assertFalse(any(
            record.name == "runtime_transport_close_total"
            for record in sink.records
        ))

        second = asyncio.create_task(session.close())
        await asyncio.sleep(0)
        connection.release_close.set()
        second_result, waiter_result = await asyncio.gather(second, waiter)

        self.assertIs(second_result, waiter_result)
        self.assertIs(second_result, session.close_info)
        self.assertEqual("closed", session.state.value)
        self.assertEqual(2, connection.close_calls)
        close_metrics = [
            record for record in sink.records
            if record.name == "runtime_transport_close_total"
        ]
        self.assertEqual(1, len(close_metrics))
        connection_metrics = [
            record for record in sink.records
            if record.name == "runtime_transport_connections"
        ]
        self.assertEqual(2, len(connection_metrics))
        self.assertEqual(0.0, connection_metrics[-1].value)
