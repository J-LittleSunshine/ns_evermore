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
    NsRuntimeTransportSendFailedError,
    NsStateError,
)
from ns_common.time import SystemClock
from ns_common.observability import InMemoryMetricsSink
from ns_runtime.transport import (
    TransportCloseReason,
    TransportIdentityFactory,
    TransportMetricsRecorder,
    WebSocketTcpAdapterOptions,
    WebSocketTcpSession,
)


class _ControlledConnection:
    def __init__(self, *, slow_send: bool = False) -> None:
        self.inbound: asyncio.Queue[Any] = asyncio.Queue()
        self.slow_send = slow_send
        self.send_started = asyncio.Event()
        self.release_send = asyncio.Event()
        self.sent: list[str] = []
        self.close_code: int | None = None

    async def recv(self) -> Any:
        return await self.inbound.get()

    async def send(self, text: str) -> None:
        self.send_started.set()
        if self.slow_send:
            await self.release_send.wait()
        self.sent.append(text)

    async def ping(self) -> asyncio.Future[float]:
        future: asyncio.Future[float] = asyncio.get_running_loop().create_future()
        future.set_result(0.0)
        return future

    async def close(self, *, code: int, reason: str) -> None:
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
    ) -> WebSocketTcpSession:
        supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        self.addAsyncCleanup(supervisor.shutdown)
        clock = SystemClock()
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
                close_timeout_seconds=1,
            ),
            task_supervisor=supervisor,
            task_suffix=1,
            identity=TransportIdentityFactory().create(
                local_address=("127.0.0.1", 8765),
                peer_address=("127.0.0.1", 54321),
                validated_at=clock.utc_now(),
            ),
            metrics=TransportMetricsRecorder(
                clock=clock,
                sink=InMemoryMetricsSink(),
            ),
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
        await asyncio.gather(first, second)
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

    async def test_send_timeout_is_bounded_and_closes_session(self) -> None:
        connection = _ControlledConnection(slow_send=True)
        session = self._session(connection, send_timeout=0.01)
        with self.assertRaises(NsRuntimeTransportSendFailedError) as raised:
            await session.send("slow")
        self.assertEqual("send_timeout", raised.exception.details["reason"])
        await asyncio.wait_for(session.wait_closed(), timeout=1)
        self.assertEqual(TransportCloseReason.SEND_TIMEOUT, session.close_info.reason)

    async def test_concurrent_close_is_idempotent_and_new_writes_are_rejected(self) -> None:
        connection = _ControlledConnection()
        session = self._session(connection)
        closes = await asyncio.gather(*(session.close() for _ in range(10)))
        self.assertTrue(all(item is closes[0] for item in closes))
        with self.assertRaises(NsStateError):
            await session.send("after-close")
