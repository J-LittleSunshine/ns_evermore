# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import unittest
from datetime import datetime, timezone

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import (
    NsRuntimeEnvelopeSchemaError,
    NsRuntimeProtocolViolationError,
    NsStateError,
)
from ns_common.time import ControlledClock
from ns_runtime.connection import (
    ConnectionHelloReceiver,
    LogicalConnectionCloseReason,
    LogicalConnectionState,
    LogicalConnectionStateMachine,
)
from ns_runtime.protocol import JsonV1Codec
from ns_runtime.transport import (
    TransportCapabilities,
    TransportClose,
    TransportCloseInitiator,
    TransportCloseReason,
    TransportDiagnosticSummary,
    TransportIdentity,
    TransportPathSnapshot,
    TransportSession,
    TransportSessionState,
)


class _FakeTransportSession(TransportSession):
    def __init__(
        self,
        *,
        capabilities: TransportCapabilities = TransportCapabilities(),
    ) -> None:
        self.messages: asyncio.Queue[object] = asyncio.Queue()
        self.receive_calls = 0
        self.close_calls = 0
        self.ping_calls = 0
        self._receive_waiting = False
        self.close_failures_remaining = 0
        self.close_failure = RuntimeError("credential=close-secret")
        self._state = TransportSessionState.HANDSHAKING
        self._close_info: TransportClose | None = None
        self._capabilities = capabilities
        self._identity = TransportIdentity(
            transport_connection_id="transport_connection_00000000000000000000000000000001",
            transport_session_id="transport_session_00000000000000000000000000000002",
            transport_stream_id="transport_stream_00000000000000000000000000000003",
            path=TransportPathSnapshot(
                path_id="transport_path_00000000000000000000000000000004",
                path_epoch=0,
                local_summary="sha256:0000000000000000",
                peer_summary="sha256:0000000000000000",
                validated_at=datetime(2026, 7, 21, tzinfo=timezone.utc),
            ),
        )

    @property
    def transport_type(self) -> str:
        return "websocket_tcp"

    @property
    def capabilities(self) -> TransportCapabilities:
        return self._capabilities

    @property
    def state(self) -> TransportSessionState:
        return self._state

    @property
    def close_info(self) -> TransportClose | None:
        return self._close_info

    @property
    def identity(self) -> TransportIdentity:
        return self._identity

    @property
    def diagnostic_summary(self) -> TransportDiagnosticSummary:
        return self._identity.diagnostic_summary(
            transport_type="websocket_tcp",
            tls=False,
        )

    async def receive(self):
        from ns_runtime.transport import TransportMessage

        self.receive_calls += 1
        self._receive_waiting = True
        try:
            value = await self.messages.get()
        finally:
            self._receive_waiting = False
        if isinstance(value, BaseException):
            raise value
        return TransportMessage(
            text=value,
            byte_size=len(value.encode("utf-8")),
            received_at=datetime(2026, 7, 21, tzinfo=timezone.utc),
        )

    async def send(self, text: str) -> None:
        raise AssertionError("handshake W02 must not send")

    async def ping(self) -> None:
        self.ping_calls += 1

    async def close(self) -> TransportClose:
        self.close_calls += 1
        if self.close_failures_remaining > 0:
            self.close_failures_remaining -= 1
            raise self.close_failure
        if self._close_info is None:
            self._state = TransportSessionState.CLOSED
            self._close_info = TransportClose(
                reason=TransportCloseReason.NORMAL,
                initiator=TransportCloseInitiator.LOCAL,
                clean=True,
                protocol_code=1000,
            )
            if self._receive_waiting and self.messages.empty():
                self.messages.put_nowait(RuntimeError("transport_closed"))
        return self._close_info


class ConnectionHelloReceiverTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.clock = ControlledClock()
        self.supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        self.transport = _FakeTransportSession()
        self.machine = LogicalConnectionStateMachine()
        self.receiver = ConnectionHelloReceiver(
            transport_session=self.transport,
            state_machine=self.machine,
            clock=self.clock,
            task_supervisor=self.supervisor,
            task_sequence=1,
            timeout_seconds=10,
            codec=JsonV1Codec(),
        )

    async def asyncTearDown(self) -> None:
        await self.supervisor.shutdown(timeout_seconds=1)

    async def test_first_valid_message_is_one_registry_validated_hello(self) -> None:
        await self.transport.messages.put(_hello())
        inbound = await self.receiver.receive()
        self.assertEqual("connection.hello", inbound.message.type)
        self.assertEqual(1, self.transport.receive_calls)
        self.assertEqual(0, self.transport.close_calls)
        self.assertEqual(0, self.transport.ping_calls)
        self.assertIs(LogicalConnectionState.HANDSHAKING, self.machine.state)
        self.assertEqual((), self.supervisor.pending_task_names)
        self.assertEqual(0, self.clock.pending_sleep_count)

    async def test_non_hello_first_message_is_terminal_and_not_dispatched(self) -> None:
        await self.transport.messages.put(_heartbeat())
        with self.assertRaises(NsRuntimeProtocolViolationError) as context:
            await self.receiver.receive()
        self.assertEqual("hello_required_first", context.exception.details["reason"])
        self.assertEqual(1, self.transport.receive_calls)
        self.assertEqual(1, self.transport.close_calls)
        self.assertIs(LogicalConnectionState.CLOSED, self.machine.state)
        self.assertIs(
            LogicalConnectionCloseReason.PROTOCOL_FAILED,
            self.machine.close_reason,
        )

    async def test_malformed_hello_closes_without_reading_a_second_message(self) -> None:
        await self.transport.messages.put(_hello(include_token=False))
        await self.transport.messages.put(_hello())
        with self.assertRaises(NsRuntimeEnvelopeSchemaError):
            await self.receiver.receive()
        self.assertEqual(1, self.transport.receive_calls)
        self.assertEqual(1, self.transport.messages.qsize())
        self.assertIs(LogicalConnectionState.CLOSED, self.machine.state)

    async def test_close_failure_does_not_replace_protocol_failure(self) -> None:
        self.transport.close_failures_remaining = 1
        await self.transport.messages.put(_heartbeat())
        with self.assertRaises(NsRuntimeProtocolViolationError) as context:
            await self.receiver.receive()
        self.assertEqual("hello_required_first", context.exception.details["reason"])
        self.assertEqual(1, self.transport.close_calls)
        self.assertIs(LogicalConnectionState.CLOSING, self.machine.state)
        self.assertNotIn("close-secret", repr(await self.machine.snapshot()))
        await self.receiver.terminate(LogicalConnectionCloseReason.PROTOCOL_FAILED)
        self.assertEqual(2, self.transport.close_calls)
        self.assertIs(LogicalConnectionState.CLOSED, self.machine.state)

    async def test_deadline_uses_controlled_clock_and_leaves_no_task(self) -> None:
        task = asyncio.create_task(self.receiver.receive())
        await _wait_until(lambda: self.clock.pending_sleep_count == 1)
        self.clock.advance(10)
        with self.assertRaises(NsRuntimeProtocolViolationError) as context:
            await task
        self.assertEqual("hello_timeout", context.exception.details["reason"])
        self.assertEqual(1, self.transport.close_calls)
        self.assertEqual((), self.supervisor.pending_task_names)
        self.assertEqual(0, self.clock.pending_sleep_count)
        self.assertIs(LogicalConnectionState.CLOSED, self.machine.state)
        self.assertIs(
            LogicalConnectionCloseReason.TIMEOUT_CLOSED,
            self.machine.close_reason,
        )

    async def test_message_completed_before_deadline_wins(self) -> None:
        task = asyncio.create_task(self.receiver.receive())
        await _wait_until(lambda: self.clock.pending_sleep_count == 1)
        await self.transport.messages.put(_hello())
        inbound = await task
        self.assertEqual("connection.hello", inbound.message.type)
        self.assertIs(LogicalConnectionState.HANDSHAKING, self.machine.state)

    async def test_arrival_at_expired_deadline_is_rejected_deterministically(self) -> None:
        task = asyncio.create_task(self.receiver.receive())
        await _wait_until(lambda: self.clock.pending_sleep_count == 1)
        await self.transport.messages.put(_hello())
        self.clock.advance(10)
        with self.assertRaises(NsRuntimeProtocolViolationError) as context:
            await task
        self.assertEqual("hello_timeout", context.exception.details["reason"])
        self.assertIs(LogicalConnectionState.CLOSED, self.machine.state)

    async def test_cancellation_closes_and_cleans_receive_and_deadline_tasks(self) -> None:
        task = asyncio.create_task(self.receiver.receive())
        await _wait_until(lambda: self.clock.pending_sleep_count == 1)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual((), self.supervisor.pending_task_names)
        self.assertEqual(0, self.clock.pending_sleep_count)
        self.assertIs(LogicalConnectionState.CLOSED, self.machine.state)
        self.assertIs(LogicalConnectionCloseReason.SHUTDOWN, self.machine.close_reason)

    async def test_hello_racing_external_close_never_advances_past_handshake(self) -> None:
        task = asyncio.create_task(self.receiver.receive())
        await _wait_until(lambda: self.clock.pending_sleep_count == 1)
        await self.transport.messages.put(_hello())
        await self.machine.transition(
            LogicalConnectionState.CLOSING,
            close_reason=LogicalConnectionCloseReason.SHUTDOWN,
        )
        await self.transport.close()
        await self.machine.transition(LogicalConnectionState.CLOSED)
        result = await asyncio.gather(task, return_exceptions=True)
        self.assertEqual(1, len(result))
        self.assertIs(LogicalConnectionState.CLOSED, self.machine.state)
        self.assertNotIn(
            LogicalConnectionState.ACTIVE,
            {self.machine.state},
        )
        self.assertEqual((), self.supervisor.pending_task_names)

    async def test_duplicate_receive_is_rejected_and_cannot_read_again(self) -> None:
        await self.transport.messages.put(_hello())
        await self.receiver.receive()
        with self.assertRaises(NsRuntimeProtocolViolationError) as context:
            await self.receiver.receive()
        self.assertEqual("duplicate_hello", context.exception.details["reason"])
        self.assertEqual(1, self.transport.receive_calls)
        self.assertIs(LogicalConnectionState.CLOSED, self.machine.state)

    async def test_concurrent_duplicate_receive_has_one_reader_and_one_terminal(self) -> None:
        first = asyncio.create_task(self.receiver.receive())
        await _wait_until(lambda: self.clock.pending_sleep_count == 1)
        second = asyncio.create_task(self.receiver.receive())
        with self.assertRaises(NsRuntimeProtocolViolationError):
            await second
        with self.assertRaises(Exception):
            await first
        self.assertEqual(1, self.transport.receive_calls)
        self.assertIs(LogicalConnectionState.CLOSED, self.machine.state)

    async def test_transport_failure_is_terminal_and_preserves_exception(self) -> None:
        failure = RuntimeError("credential=secret")
        await self.transport.messages.put(failure)
        with self.assertRaises(RuntimeError) as context:
            await self.receiver.receive()
        self.assertIs(failure, context.exception)
        self.assertNotIn("secret", repr(await self.machine.snapshot()))
        self.assertIs(
            LogicalConnectionCloseReason.TRANSPORT_DISCONNECTED,
            self.machine.close_reason,
        )

    async def test_reuse_after_external_close_is_stably_rejected(self) -> None:
        await self.machine.transition(
            LogicalConnectionState.CLOSING,
            close_reason=LogicalConnectionCloseReason.SHUTDOWN,
        )
        await self.machine.transition(LogicalConnectionState.CLOSED)
        with self.assertRaises(NsStateError):
            await self.receiver.receive()
        self.assertEqual(0, self.transport.receive_calls)


async def _wait_until(predicate) -> None:
    for _ in range(20):
        if predicate():
            return
        await asyncio.sleep(0)
    raise AssertionError("condition was not reached")


def _hello(*, include_token: bool = True) -> str:
    payload = {
        "component_type": "client",
        "requested_version": "1.0.0",
        "requested_capabilities": ["runtime.connection"],
    }
    if include_token:
        payload["token"] = "top-secret-token"
    return _wire("connection.hello", payload=payload)


def _heartbeat() -> str:
    return _wire("connection.heartbeat")


def _wire(message_type: str, *, payload: dict[str, object] | None = None) -> str:
    value: dict[str, object] = {
        "protocol": {"major": 1, "minor": 0, "patch": 0},
        "message": {
            "message_id": "message_00000000000000000000000000000001",
            "type": message_type,
            "category": "connection",
            "priority": 0,
            "created_at": "2026-07-21T00:00:00Z",
            "reliability": "best_effort",
        },
    }
    if payload is not None:
        value["payload"] = {"mode": "inline", "inline": payload}
    return json.dumps(value, separators=(",", ":"))


if __name__ == "__main__":
    unittest.main()
