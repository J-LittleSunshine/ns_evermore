# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import unittest
from collections.abc import Mapping
from uuid import UUID

from ns_common.exceptions import NsStateError, NsValidationError
from ns_common.identifiers import IdentifierFactory
from ns_common.time import ControlledClock
from ns_runtime.connection import (
    ACCEPTED_HEARTBEAT_FIELDS,
    ACCEPTED_PAYLOAD_FIELDS,
    AcceptedHeartbeatPolicy,
    ConnectionAcceptedEnvelopeBuilder,
    ConnectionAdmissionActivator,
    LocalConnectionIndex,
    LogicalConnectionCloseReason,
    LogicalConnectionState,
)
from ns_runtime.protocol import (
    BUILTIN_MESSAGE_REGISTRY,
    JsonV1Codec,
    canonical_serialize,
)
from ns_runtime.roles import RuntimeRole
from ns_runtime.transport import WEBSOCKET_TCP_CAPABILITIES

from tests.test_runtime_connection_binding import CONNECTION_ID, UTC_START, _context
from tests.test_runtime_connection_handshake import _FakeTransportSession
from tests.test_runtime_connection_index import _authenticated_machine


RUNTIME_ID = "runtime_123e4567e89b42d3a456426614174020"


class _CaptureTransport(_FakeTransportSession):
    def __init__(self) -> None:
        super().__init__(capabilities=WEBSOCKET_TCP_CAPABILITIES)
        self.sent: list[str] = []
        self.send_failure: BaseException | None = None
        self.send_started = asyncio.Event()
        self.send_release: asyncio.Event | None = None

    async def send(self, text: str) -> None:
        self.send_started.set()
        if self.send_release is not None:
            await self.send_release.wait()
        if self.send_failure is not None:
            raise self.send_failure
        self.sent.append(text)


class _HostileSendError(RuntimeError):
    def __str__(self) -> str:
        raise AssertionError("send error must not be stringified")

    def __repr__(self) -> str:
        raise AssertionError("send error must not be represented")


class ConnectionAcceptedTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.clock = ControlledClock(utc_start=UTC_START)
        self.transport = _CaptureTransport()
        self.context = _context(self.transport, clock=self.clock)
        self.machine = await _authenticated_machine()
        self.index = LocalConnectionIndex()
        await self.index.add_authenticated(
            session_context=self.context,
            state_machine=self.machine,
        )
        self.builder = _builder(self.clock)

    async def test_exact_minimum_payload_and_p03_registry(self) -> None:
        envelope = self.builder.build(self.context)
        validated = BUILTIN_MESSAGE_REGISTRY.validate_envelope(
            envelope,
            self.context.protocol_schema_key,
        )
        self.assertIs(envelope, validated)
        self.assertEqual("connection.accepted", envelope.message.type)
        self.assertEqual("best_effort", envelope.message.reliability)
        self.assertIsNone(envelope.source)
        self.assertIsNone(envelope.target)
        self.assertIsNone(envelope.delivery)
        self.assertIsNone(envelope.auth_context)
        payload = envelope.payload.inline
        assert isinstance(payload, Mapping)
        self.assertEqual(ACCEPTED_PAYLOAD_FIELDS, frozenset(payload))
        heartbeat = payload["heartbeat"]
        self.assertEqual(ACCEPTED_HEARTBEAT_FIELDS, frozenset(heartbeat))
        self.assertEqual("1.0.0", payload["protocol_version"])
        self.assertEqual(RUNTIME_ID, payload["runtime_id"])
        self.assertEqual("singleton", payload["role"])

    async def test_serialization_is_canonical_and_uses_negotiated_codec(self) -> None:
        envelope = self.builder.build(self.context)
        text = self.builder.serialize(self.context)
        decoded = JsonV1Codec().decode_document(text)

        self.assertEqual(canonical_serialize(envelope), text.encode("utf-8"))
        self.assertEqual("1.0.0", decoded["payload"]["inline"]["protocol_version"])
        self.assertEqual(1, decoded["protocol"]["major"])

    async def test_successful_send_is_the_only_activation_gate(self) -> None:
        activator = self._activator()

        await activator.activate(self.context)

        self.assertEqual(1, len(self.transport.sent))
        entry = await self.index.lookup_connection(CONNECTION_ID)
        assert entry is not None
        self.assertIs(LogicalConnectionState.ACTIVE, entry.state)
        self.assertTrue(entry.active_target_eligible)
        self.assertEqual(1, len(await self.index.active_targets()))

    async def test_payload_never_exposes_authority_or_transport_details(self) -> None:
        serialized = self.builder.serialize(self.context)
        value = json.loads(serialized)
        payload = value["payload"]["inline"]
        forbidden = {
            "token", "tenant_id", "identity", "capabilities", "permissions",
            "permission_snapshot_ref", "permission_digest", "transport_id",
            "transport_session_id", "peer", "config", "iam_response",
        }
        self.assertTrue(forbidden.isdisjoint(payload))
        for secret in (
            "identity:test-user",
            "tenant:test",
            "permission:snapshot-test",
            "sha256:permission-test",
            self.transport.identity.transport_session_id,
            self.transport.identity.path.peer_summary,
        ):
            self.assertNotIn(secret, serialized)

    async def test_send_failure_closes_and_removes_indexes_without_active(self) -> None:
        failure = _HostileSendError()
        self.transport.send_failure = failure
        activator = self._activator()

        with self.assertRaises(_HostileSendError) as context:
            await activator.activate(self.context)

        self.assertIs(failure, context.exception)
        self.assertEqual((), await self.index.active_targets())
        self.assertIsNone(await self.index.lookup_connection(CONNECTION_ID))
        self.assertIs(LogicalConnectionState.CLOSED, self.machine.state)
        self.assertIs(LogicalConnectionCloseReason.SEND_FAILED, self.machine.close_reason)
        self.assertEqual(1, self.transport.close_calls)

    async def test_close_failure_leaves_closing_non_target_and_is_retryable(self) -> None:
        self.transport.send_failure = RuntimeError("send-failed")
        self.transport.close_failures_remaining = 1
        activator = self._activator()

        with self.assertRaises(RuntimeError):
            await activator.activate(self.context)

        entry = await self.index.lookup_connection(CONNECTION_ID)
        assert entry is not None
        self.assertIs(LogicalConnectionState.CLOSING, entry.state)
        self.assertFalse(entry.active_target_eligible)
        self.assertTrue(await activator.retry_cleanup(CONNECTION_ID))
        self.assertIsNone(await self.index.lookup_connection(CONNECTION_ID))
        self.assertEqual(2, self.transport.close_calls)

    async def test_cancelled_send_rolls_back_without_publishing_active(self) -> None:
        self.transport.send_release = asyncio.Event()
        activator = self._activator()
        task = asyncio.create_task(activator.activate(self.context))
        await self.transport.send_started.wait()

        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task

        self.assertIsNone(await self.index.lookup_connection(CONNECTION_ID))
        self.assertEqual((), await self.index.active_targets())
        self.assertIs(LogicalConnectionCloseReason.SHUTDOWN, self.machine.close_reason)

    async def test_activation_is_one_shot_and_requires_indexed_exact_context(self) -> None:
        activator = self._activator()
        await activator.activate(self.context)
        with self.assertRaises(NsStateError) as duplicate:
            await activator.activate(self.context)
        self.assertEqual("activation_already_attempted", duplicate.exception.details["reason"])
        self.assertEqual(1, len(self.transport.sent))

        missing_index = LocalConnectionIndex()
        other = ConnectionAdmissionActivator(
            connection_index=missing_index,
            transport_session=_CaptureTransport(),
            envelope_builder=self.builder,
        )
        with self.assertRaises(NsStateError) as missing:
            await other.activate(self.context)
        self.assertEqual("authenticated_session_not_indexed", missing.exception.details["reason"])

    def test_heartbeat_policy_is_frozen_and_bounded(self) -> None:
        with self.assertRaises(NsValidationError):
            AcceptedHeartbeatPolicy(interval_seconds=10, timeout_seconds=10)
        policy = AcceptedHeartbeatPolicy(interval_seconds=10, timeout_seconds=30)
        with self.assertRaises((AttributeError, TypeError)):
            policy.interval_seconds = 20  # type: ignore[misc]

    def _activator(self) -> ConnectionAdmissionActivator:
        return ConnectionAdmissionActivator(
            connection_index=self.index,
            transport_session=self.transport,
            envelope_builder=self.builder,
        )


def _builder(clock: ControlledClock) -> ConnectionAcceptedEnvelopeBuilder:
    return ConnectionAcceptedEnvelopeBuilder(
        clock=clock,
        identifier_factory=IdentifierFactory(
            uuid_factory=lambda: UUID("123e4567-e89b-42d3-a456-426614174021"),
        ),
        runtime_id=RUNTIME_ID,
        role=RuntimeRole.SINGLETON,
        heartbeat_policy=AcceptedHeartbeatPolicy(
            interval_seconds=10,
            timeout_seconds=30,
        ),
    )


if __name__ == "__main__":
    unittest.main()
