# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import unittest
from uuid import UUID

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import (
    NsRuntimeEnvelopeSchemaError,
    NsRuntimeProtocolViolationError,
    NsStateError,
)
from ns_common.identifiers import IdentifierFactory
from ns_common.time import ControlledClock
from ns_runtime.connection import (
    HEARTBEAT_ACK_PAYLOAD_FIELDS,
    ConnectionDrainService,
    ConnectionHeartbeatService,
    DrainPolicy,
    EnvelopeHeartbeatOutcome,
    HeartbeatPolicy,
    LocalConnectionIndex,
    LogicalConnectionCloseReason,
    LogicalConnectionState,
)
from ns_runtime.protocol import JsonV1Codec
from ns_runtime.transport import WEBSOCKET_TCP_CAPABILITIES

from tests.test_runtime_connection_binding import (
    CONNECTION_ID,
    SESSION_ID,
    UTC_START,
    _context,
)
from tests.test_runtime_connection_handshake import _FakeTransportSession
from tests.test_runtime_connection_index import _authenticated_machine


class _HeartbeatTransport(_FakeTransportSession):
    def __init__(self) -> None:
        super().__init__(capabilities=WEBSOCKET_TCP_CAPABILITIES)
        self.sent: list[str] = []
        self.ping_failure: BaseException | None = None

    async def send(self, text: str) -> None:
        self.sent.append(text)

    async def ping(self) -> None:
        self.ping_calls += 1
        if self.ping_failure is not None:
            raise self.ping_failure


class ConnectionHeartbeatTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.clock = ControlledClock(utc_start=UTC_START)
        self.supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        self.transport = _HeartbeatTransport()
        self.context = _context(self.transport, clock=self.clock)
        self.machine = await _authenticated_machine()
        self.index = LocalConnectionIndex()
        await self.index.add_authenticated(
            session_context=self.context,
            state_machine=self.machine,
        )
        await self.index.transition(CONNECTION_ID, LogicalConnectionState.ACTIVE)
        self.service = _service(
            context=self.context,
            index=self.index,
            transport=self.transport,
            clock=self.clock,
            supervisor=self.supervisor,
        )

    async def asyncTearDown(self) -> None:
        await self.supervisor.shutdown(timeout_seconds=1)

    async def test_envelope_heartbeat_uses_p03_and_sends_exact_lightweight_ack(self) -> None:
        outcome = await self.service.handle_text(_heartbeat(sequence=0))

        self.assertIs(EnvelopeHeartbeatOutcome.ACCEPTED, outcome)
        self.assertEqual(1, len(self.transport.sent))
        ack = JsonV1Codec().decode_document(self.transport.sent[0])
        self.assertEqual("connection.heartbeat_ack", ack["message"]["type"])
        self.assertEqual(
            HEARTBEAT_ACK_PAYLOAD_FIELDS,
            frozenset(ack["payload"]["inline"]),
        )
        self.assertNotIn("delivery", ack)
        self.assertNotIn("auth_context", ack)
        snapshot = await self.service.snapshot()
        self.assertEqual(0, snapshot.last_envelope_sequence)
        self.assertEqual(1, snapshot.envelope_accepted_count)
        self.assertEqual(0, snapshot.native_ping_count)

    async def test_duplicate_is_idempotent_without_ack_or_liveness_refresh(self) -> None:
        await self.service.handle_text(_heartbeat(sequence=7))
        before = await self.service.snapshot()
        self.clock.advance(1)

        outcome = await self.service.handle_text(_heartbeat(sequence=7))

        after = await self.service.snapshot()
        self.assertIs(EnvelopeHeartbeatOutcome.DUPLICATE, outcome)
        self.assertEqual(1, len(self.transport.sent))
        self.assertEqual(before.last_envelope_monotonic, after.last_envelope_monotonic)
        self.assertEqual(1, after.envelope_duplicate_count)

    async def test_out_of_order_is_rejected_without_closing_or_ack(self) -> None:
        await self.service.handle_text(_heartbeat(sequence=4))
        with self.assertRaises(NsRuntimeProtocolViolationError) as context:
            await self.service.handle_text(_heartbeat(sequence=3))
        self.assertEqual(
            "heartbeat_sequence_out_of_order",
            context.exception.details["reason"],
        )
        self.assertEqual(1, len(self.transport.sent))
        self.assertIs(LogicalConnectionState.ACTIVE, self.machine.state)

    async def test_session_and_epoch_are_fenced_before_ack(self) -> None:
        for kwargs, reason in (
            ({"session_id": "session_123e4567e89b42d3a456426614174099"}, "session_id_mismatch"),
            ({"connection_epoch": 99}, "connection_epoch_mismatch"),
            ({"connection_id": "connection_123e4567e89b42d3a456426614174098"}, "connection_id_mismatch"),
        ):
            with self.subTest(reason=reason):
                with self.assertRaises(NsRuntimeProtocolViolationError) as context:
                    await self.service.handle_text(_heartbeat(sequence=1, **kwargs))
                self.assertEqual(reason, context.exception.details["reason"])
        self.assertEqual([], self.transport.sent)

    async def test_drain_keeps_health_heartbeat_but_not_target_eligibility(self) -> None:
        await self.index.transition(CONNECTION_ID, LogicalConnectionState.DRAINING)

        outcome = await self.service.handle_text(_heartbeat(sequence=1))

        self.assertIs(EnvelopeHeartbeatOutcome.ACCEPTED, outcome)
        self.assertEqual((), await self.index.active_targets())
        self.assertEqual(1, len(self.transport.sent))

    async def test_native_ping_and_envelope_heartbeat_are_distinct(self) -> None:
        await self.service.start()
        await _wait_until(lambda: self.clock.pending_sleep_count == 2)
        self.clock.advance(2)
        await _wait_until(lambda: self.transport.ping_calls == 1)

        snapshot = await self.service.snapshot()
        self.assertEqual(1, snapshot.native_ping_count)
        self.assertEqual(0, snapshot.envelope_accepted_count)
        self.assertEqual([], self.transport.sent)

    async def test_envelope_timeout_is_terminal_and_cleans_both_tasks(self) -> None:
        await self.service.start()
        await _wait_until(lambda: self.clock.pending_sleep_count == 2)
        self.clock.advance(5)
        await _wait_until(lambda: self.machine.state is LogicalConnectionState.CLOSED)

        snapshot = await self.service.snapshot()
        self.assertIs(LogicalConnectionCloseReason.TIMEOUT_CLOSED, snapshot.terminal_reason)
        self.assertFalse(snapshot.running)
        self.assertIsNone(await self.index.lookup_connection(CONNECTION_ID))
        await _wait_until(lambda: not self.supervisor.pending_task_names)
        self.assertEqual(0, self.clock.pending_sleep_count)

    async def test_draining_heartbeat_timeout_cancels_drain_terminal(self) -> None:
        drain = ConnectionDrainService(
            connection_id=CONNECTION_ID,
            connection_index=self.index,
            transport_session=self.transport,
            clock=self.clock,
            task_supervisor=self.supervisor,
            task_sequence=82,
            policy=DrainPolicy(timeout_seconds=30),
        )
        service = _service(
            context=self.context,
            index=self.index,
            transport=self.transport,
            clock=self.clock,
            supervisor=self.supervisor,
            drain_service=drain,
        )
        await service.start()
        await drain.begin()
        await _wait_until(lambda: self.clock.pending_sleep_count == 3)

        self.clock.advance(5)
        await _wait_until(lambda: self.machine.state is LogicalConnectionState.CLOSED)
        await drain.wait_closed()

        snapshot = await drain.snapshot()
        self.assertIs(LogicalConnectionCloseReason.TIMEOUT_CLOSED, snapshot.terminal_reason)
        self.assertFalse(snapshot.timeout_pending)
        self.clock.advance(30)
        await asyncio.sleep(0)
        self.assertIs(
            LogicalConnectionCloseReason.TIMEOUT_CLOSED,
            (await drain.snapshot()).terminal_reason,
        )
        self.assertIs(
            LogicalConnectionCloseReason.TIMEOUT_CLOSED,
            self.machine.close_reason,
        )
        self.assertFalse(any(
            name.startswith("logical-drain-")
            for name in self.supervisor.pending_task_names
        ))

    async def test_native_ping_failure_uses_transport_close_classification(self) -> None:
        self.transport.ping_failure = RuntimeError("native-ping-secret")
        await self.service.start()
        await _wait_until(lambda: self.clock.pending_sleep_count == 2)
        self.clock.advance(2)
        await _wait_until(lambda: self.machine.state is LogicalConnectionState.CLOSED)

        snapshot = await self.service.snapshot()
        self.assertIs(
            LogicalConnectionCloseReason.TRANSPORT_DISCONNECTED,
            snapshot.terminal_reason,
        )
        self.assertEqual(0, snapshot.native_ping_count)
        self.assertEqual(1, self.transport.ping_calls)

    async def test_timeout_wins_when_heartbeat_arrives_at_deadline(self) -> None:
        self.clock.advance(5)

        with self.assertRaises(NsRuntimeProtocolViolationError) as context:
            await self.service.handle_text(_heartbeat(sequence=1))

        self.assertEqual("envelope_heartbeat_timeout", context.exception.details["reason"])
        self.assertIs(LogicalConnectionCloseReason.TIMEOUT_CLOSED, self.machine.close_reason)
        self.assertEqual([], self.transport.sent)

    async def test_shutdown_cancels_supervised_waiters_and_is_idempotent(self) -> None:
        await self.service.start()
        await _wait_until(lambda: self.clock.pending_sleep_count == 2)

        await self.service.shutdown()
        await self.service.shutdown()

        self.assertIs(LogicalConnectionCloseReason.SHUTDOWN, self.machine.close_reason)
        self.assertIsNone(await self.index.lookup_connection(CONNECTION_ID))
        self.assertEqual((), self.supervisor.pending_task_names)
        self.assertEqual(0, self.clock.pending_sleep_count)

    async def test_malformed_or_non_heartbeat_never_reaches_lifecycle_handler(self) -> None:
        with self.assertRaises(NsRuntimeEnvelopeSchemaError) as wrong_type:
            await self.service.handle_text(_heartbeat(sequence=1, message_type="connection.drain"))
        self.assertEqual("group_not_allowed", wrong_type.exception.details["reason"])
        malformed = json.loads(_heartbeat(sequence=1))
        malformed["payload"]["inline"]["unexpected"] = "attacker"
        with self.assertRaises(NsRuntimeEnvelopeSchemaError) as malformed_error:
            await self.service.handle_text(json.dumps(malformed))
        self.assertEqual(
            "message_field_not_allowed",
            malformed_error.exception.details["reason"],
        )
        self.assertEqual([], self.transport.sent)


def _service(
    *,
    context,
    index,
    transport,
    clock,
    supervisor,
    drain_service=None,
) -> ConnectionHeartbeatService:
    return ConnectionHeartbeatService(
        session_context=context,
        connection_index=index,
        transport_session=transport,
        clock=clock,
        task_supervisor=supervisor,
        task_sequence=81,
        identifier_factory=IdentifierFactory(
            uuid_factory=lambda: UUID("123e4567-e89b-42d3-a456-426614174081"),
        ),
        policy=HeartbeatPolicy(
            native_interval_seconds=2,
            envelope_timeout_seconds=5,
        ),
        codec=JsonV1Codec(),
        drain_service=drain_service,
    )


def _heartbeat(
    *,
    sequence: int,
    connection_id: str = CONNECTION_ID,
    session_id: str = SESSION_ID,
    connection_epoch: int = 0,
    message_type: str = "connection.heartbeat",
) -> str:
    return json.dumps({
        "protocol": {"major": 1, "minor": 0, "patch": 0},
        "message": {
            "message_id": "message_00000000000000000000000000000081",
            "type": message_type,
            "category": "connection",
            "priority": 0,
            "created_at": "2026-07-21T00:00:00Z",
            "reliability": "best_effort",
        },
        "payload": {
            "mode": "inline",
            "inline": {
                "connection_id": connection_id,
                "session_id": session_id,
                "connection_epoch": connection_epoch,
                "sequence": sequence,
                "sent_at": "2026-07-21T00:00:00Z",
            },
        },
    }, separators=(",", ":"))


async def _wait_until(predicate) -> None:
    for _ in range(100):
        if predicate():
            return
        await asyncio.sleep(0)
    raise AssertionError("condition was not reached")


if __name__ == "__main__":
    unittest.main()
