# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import unittest

from ns_common.async_runtime import TaskSupervisor
from ns_common.identifiers import IdentifierFactory
from ns_common.time import ControlledClock
from ns_runtime.connection import (
    ConnectionHandshakeRejector,
    ConnectionRejectedEnvelopeBuilder,
    ConnectionRejectionReason,
    ConnectionRejectionSendPolicy,
    REJECTED_PAYLOAD_FIELDS,
)
from ns_runtime.protocol import ProtocolGroup
from ns_runtime.transport import WEBSOCKET_TCP_CAPABILITIES

from tests.test_runtime_connection_binding import UTC_START
from tests.test_runtime_connection_handshake import _FakeTransportSession


class _RejectTransport(_FakeTransportSession):
    def __init__(self) -> None:
        super().__init__(capabilities=WEBSOCKET_TCP_CAPABILITIES)
        self.sent: list[str] = []
        self.send_failure: Exception | None = None
        self.block_send = False

    async def send(self, text: str) -> None:
        if self.block_send:
            await asyncio.Event().wait()
        if self.send_failure is not None:
            raise self.send_failure
        self.sent.append(text)


class ConnectionRejectedEnvelopeTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.clock = ControlledClock(utc_start=UTC_START)
        self.supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        self.transport = _RejectTransport()
        self.builder = ConnectionRejectedEnvelopeBuilder(
            clock=self.clock,
            identifier_factory=IdentifierFactory(),
        )

    async def asyncTearDown(self) -> None:
        await self.supervisor.shutdown(timeout_seconds=1)

    def _rejector(self, *, timeout_seconds: float = 5) -> ConnectionHandshakeRejector:
        return ConnectionHandshakeRejector(
            transport_session=self.transport,
            builder=self.builder,
            clock=self.clock,
            task_supervisor=self.supervisor,
            task_sequence=501,
            policy=ConnectionRejectionSendPolicy(
                timeout_seconds=timeout_seconds,
            ),
        )

    async def test_builder_uses_exact_canonical_low_cardinality_payload(self) -> None:
        text = self.builder.serialize(
            protocol=ProtocolGroup(major=2, minor=0, patch=0),
            reason=ConnectionRejectionReason.PROTOCOL_INCOMPATIBLE,
        )
        value = json.loads(text)
        self.assertEqual("connection.rejected", value["message"]["type"])
        self.assertEqual(REJECTED_PAYLOAD_FIELDS, set(value["payload"]["inline"]))
        self.assertEqual(
            {
                "reason": "protocol_incompatible",
                "server_time": "2026-07-21T00:00:00.000000Z",
                "retryable": False,
            },
            value["payload"]["inline"],
        )
        encoded = json.dumps(value)
        for forbidden in (
            "token", "identity", "tenant", "capabilities", "permission",
            "peer", "transport", "exception",
        ):
            self.assertNotIn(forbidden, encoded)

    async def test_send_failure_is_best_effort_and_does_not_raise(self) -> None:
        self.transport.send_failure = RuntimeError("token=must-not-escape")
        sent = await self._rejector().send(
            protocol=ProtocolGroup(major=1, minor=0, patch=0),
            reason=ConnectionRejectionReason.IAM_DENIED,
        )
        self.assertFalse(sent)
        self.assertEqual([], self.transport.sent)
        self.assertEqual((), self.supervisor.pending_task_names)

    async def test_send_timeout_is_bounded_by_clock_and_supervisor(self) -> None:
        self.transport.block_send = True
        task = asyncio.create_task(self._rejector().send(
            protocol=ProtocolGroup(major=1, minor=0, patch=0),
            reason=ConnectionRejectionReason.IAM_UNAVAILABLE,
        ))
        await _wait_until(lambda: self.clock.pending_sleep_count == 1)
        self.clock.advance(5)
        self.assertFalse(await task)
        self.assertEqual((), self.supervisor.pending_task_names)
        self.assertEqual(0, self.clock.pending_sleep_count)


async def _wait_until(predicate) -> None:
    for _ in range(100):
        if predicate():
            return
        await asyncio.sleep(0)
    raise AssertionError("condition did not become true")


if __name__ == "__main__":
    unittest.main()
