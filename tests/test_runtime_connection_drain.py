# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import dataclasses
import json
import unittest

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import NsRuntimeProtocolViolationError, NsStateError
from ns_common.time import ControlledClock
from ns_runtime.connection import (
    DRAIN_ALLOWED_MESSAGE_TYPES,
    ConnectionDrainService,
    ConnectionDrainEnvelopeHandler,
    DrainPolicy,
    DrainingMessageDisposition,
    DrainingMessageGate,
    LocalConnectionIndex,
    LogicalConnectionCloseReason,
    LogicalConnectionState,
)
from ns_runtime.transport import WEBSOCKET_TCP_CAPABILITIES
from ns_runtime.protocol import JsonV1Codec

from tests.test_runtime_connection_binding import CONNECTION_ID, UTC_START, _context
from tests.test_runtime_connection_handshake import _FakeTransportSession
from tests.test_runtime_connection_index import _authenticated_machine


class _BlockingCloseTransport(_FakeTransportSession):
    def __init__(self) -> None:
        super().__init__(capabilities=WEBSOCKET_TCP_CAPABILITIES)
        self.close_started = asyncio.Event()
        self.close_release = asyncio.Event()

    async def close(self):
        self.close_started.set()
        await self.close_release.wait()
        return await super().close()


class ConnectionDrainTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.clock = ControlledClock(utc_start=UTC_START)
        self.supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        self.transport = _FakeTransportSession(
            capabilities=WEBSOCKET_TCP_CAPABILITIES,
        )
        self.context = _context(self.transport, clock=self.clock)
        self.machine = await _authenticated_machine()
        self.index = LocalConnectionIndex()
        await self.index.add_authenticated(
            session_context=self.context,
            state_machine=self.machine,
        )
        await self.index.transition(CONNECTION_ID, LogicalConnectionState.ACTIVE)
        self.service = _service(
            index=self.index,
            transport=self.transport,
            clock=self.clock,
            supervisor=self.supervisor,
        )

    async def asyncTearDown(self) -> None:
        await self.supervisor.shutdown(timeout_seconds=1)

    async def test_begin_is_one_way_and_immediately_removes_target(self) -> None:
        snapshot = await self.service.begin()

        self.assertIs(LogicalConnectionState.DRAINING, snapshot.state)
        self.assertEqual(0.0, snapshot.started_monotonic)
        self.assertEqual(10.0, snapshot.deadline_monotonic)
        self.assertTrue(snapshot.timeout_pending)
        self.assertEqual((), await self.index.active_targets())
        self.assertEqual(0, self.transport.close_calls)
        with self.assertRaises(NsStateError):
            await self.index.transition(CONNECTION_ID, LogicalConnectionState.ACTIVE)

    async def test_repeated_begin_is_idempotent_and_cannot_cancel_drain(self) -> None:
        first = await self.service.begin()
        second = await self.service.begin()

        self.assertEqual(first.started_monotonic, second.started_monotonic)
        self.assertEqual(first.deadline_monotonic, second.deadline_monotonic)
        self.assertEqual(
            ("logical-drain-91-deadline",),
            self.supervisor.pending_task_names,
        )
        self.assertIs(LogicalConnectionState.DRAINING, self.machine.state)

    async def test_gate_preserves_only_control_health_and_existing_delivery_responses(self) -> None:
        gate = DrainingMessageGate()
        for message_type in DRAIN_ALLOWED_MESSAGE_TYPES:
            with self.subTest(message_type=message_type):
                self.assertIs(
                    DrainingMessageDisposition.ALLOWED_LIFECYCLE_OR_EXISTING_DELIVERY,
                    gate.classify(message_type),
                )
        for message_type in (
            "task.dispatch",
            "task.result",
            "delivery.accepted",
            "stream.start",
            "config.update",
        ):
            with self.subTest(message_type=message_type):
                self.assertIs(
                    DrainingMessageDisposition.REJECT_NEW_WORK,
                    gate.classify(message_type),
                )

    async def test_explicit_complete_closes_after_drain_not_at_begin(self) -> None:
        await self.service.begin()

        self.assertTrue(await self.service.complete())

        self.assertIs(LogicalConnectionState.CLOSED, self.machine.state)
        self.assertIs(LogicalConnectionCloseReason.NORMAL, self.machine.close_reason)
        self.assertIsNone(await self.index.lookup_connection(CONNECTION_ID))
        self.assertEqual(1, self.transport.close_calls)
        await _wait_until(lambda: not self.supervisor.pending_task_names)
        self.assertEqual(0, self.clock.pending_sleep_count)

    async def test_drain_timeout_uses_clock_and_supervised_task(self) -> None:
        await self.service.begin()
        await _wait_until(lambda: self.clock.pending_sleep_count == 1)

        self.clock.advance(10)
        await _wait_until(lambda: self.machine.state is LogicalConnectionState.CLOSED)

        snapshot = await self.service.snapshot()
        self.assertIs(LogicalConnectionCloseReason.DRAIN_TIMEOUT, snapshot.terminal_reason)
        self.assertIs(LogicalConnectionCloseReason.DRAIN_TIMEOUT, self.machine.close_reason)
        self.assertIsNone(await self.index.lookup_connection(CONNECTION_ID))
        await _wait_until(lambda: not self.supervisor.pending_task_names)
        self.assertEqual(0, self.clock.pending_sleep_count)

    async def test_close_failure_keeps_closing_and_retry_owner(self) -> None:
        await self.service.begin()
        self.transport.close_failures_remaining = 1

        self.assertFalse(await self.service.complete())

        entry = await self.index.lookup_connection(CONNECTION_ID)
        assert entry is not None
        self.assertIs(LogicalConnectionState.CLOSING, entry.state)
        self.assertFalse(entry.active_target_eligible)
        self.assertTrue(await self.service.retry_cleanup())
        self.assertIsNone(await self.index.lookup_connection(CONNECTION_ID))

    async def test_cancelled_close_never_restores_active_and_can_retry(self) -> None:
        blocking = _BlockingCloseTransport()
        context = _context(blocking, clock=self.clock)
        machine = await _authenticated_machine()
        index = LocalConnectionIndex()
        await index.add_authenticated(session_context=context, state_machine=machine)
        await index.transition(CONNECTION_ID, LogicalConnectionState.ACTIVE)
        service = _service(
            index=index,
            transport=blocking,
            clock=self.clock,
            supervisor=self.supervisor,
        )
        await service.begin()
        task = asyncio.create_task(service.complete())
        await blocking.close_started.wait()

        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task

        entry = await index.lookup_connection(CONNECTION_ID)
        assert entry is not None
        self.assertIs(LogicalConnectionState.CLOSING, entry.state)
        self.assertFalse(entry.active_target_eligible)
        blocking.close_release.set()
        self.assertTrue(await service.retry_cleanup())
        self.assertIsNone(await index.lookup_connection(CONNECTION_ID))

    async def test_concurrent_terminal_requests_publish_one_reason(self) -> None:
        await self.service.begin()

        outcomes = await asyncio.gather(
            self.service.terminate(LogicalConnectionCloseReason.KICKED),
            self.service.terminate(LogicalConnectionCloseReason.SHUTDOWN),
        )

        self.assertEqual([True, True], outcomes)
        snapshot = await self.service.snapshot()
        self.assertIsNotNone(snapshot.terminal_reason)
        self.assertIs(snapshot.terminal_reason, self.machine.close_reason)
        self.assertIs(LogicalConnectionState.CLOSED, snapshot.state)
        self.assertEqual(1, self.transport.close_calls)

    async def test_begin_from_non_active_state_is_rejected_without_task(self) -> None:
        index = LocalConnectionIndex()
        machine = await _authenticated_machine()
        await index.add_authenticated(
            session_context=self.context,
            state_machine=machine,
        )
        service = _service(
            index=index,
            transport=self.transport,
            clock=self.clock,
            supervisor=self.supervisor,
        )
        with self.assertRaises(NsStateError) as context:
            await service.begin()
        self.assertEqual("active_state_required", context.exception.details["reason"])
        self.assertEqual((), self.supervisor.pending_task_names)

    async def test_drain_snapshot_is_frozen_and_contains_no_work_records(self) -> None:
        snapshot = await self.service.begin()
        with self.assertRaises((dataclasses.FrozenInstanceError, TypeError)):
            snapshot.timeout_pending = False  # type: ignore[misc]
        self.assertFalse(hasattr(snapshot, "deliveries"))
        self.assertFalse(hasattr(snapshot, "transfer"))

    async def test_connection_drain_envelope_is_p03_validated_and_self_scoped(self) -> None:
        handler = ConnectionDrainEnvelopeHandler(
            drain_service=self.service,
            codec=JsonV1Codec(),
            schema_key=self.context.protocol_schema_key,
        )

        snapshot = await handler.handle_text(_drain_envelope())

        self.assertIs(LogicalConnectionState.DRAINING, snapshot.state)
        self.assertEqual((), await self.index.active_targets())

    async def test_connection_drain_rejects_target_payload_and_other_types(self) -> None:
        handler = ConnectionDrainEnvelopeHandler(
            drain_service=self.service,
            codec=JsonV1Codec(),
            schema_key=self.context.protocol_schema_key,
        )
        for mutation in ("target", "payload", "type"):
            value = json.loads(_drain_envelope())
            if mutation == "target":
                value["target"] = {"kind": "connection", "connection_id": CONNECTION_ID}
            elif mutation == "payload":
                value["payload"] = {"mode": "inline", "inline": {"connection_id": CONNECTION_ID}}
            else:
                value["message"]["type"] = "connection.heartbeat"
            with self.subTest(mutation=mutation):
                with self.assertRaises(NsRuntimeProtocolViolationError):
                    await handler.handle_text(json.dumps(value))
        self.assertIs(LogicalConnectionState.ACTIVE, self.machine.state)


def _service(
    *,
    index,
    transport,
    clock,
    supervisor,
) -> ConnectionDrainService:
    return ConnectionDrainService(
        connection_id=CONNECTION_ID,
        connection_index=index,
        transport_session=transport,
        clock=clock,
        task_supervisor=supervisor,
        task_sequence=91,
        policy=DrainPolicy(timeout_seconds=10),
    )


def _drain_envelope() -> str:
    return json.dumps({
        "protocol": {"major": 1, "minor": 0, "patch": 0},
        "message": {
            "message_id": "message_00000000000000000000000000000091",
            "type": "connection.drain",
            "category": "connection",
            "priority": 0,
            "created_at": "2026-07-21T00:00:00Z",
            "reliability": "reliable",
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
