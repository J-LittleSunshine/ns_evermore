# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import dataclasses
import json
import unittest
from datetime import datetime, timedelta, timezone

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import (
    NsRuntimeEnvelopeSchemaError,
    NsRuntimeIamDeniedError,
    NsRuntimeIamTimeoutError,
    NsRuntimeIamUnavailableError,
)
from ns_common.time import ControlledClock
from ns_runtime.connection import (
    ConnectionHandshakeAuthenticator,
    ConnectionHelloReceiver,
    DeterministicTestIamAdapter,
    FailClosedHandshakeIamAdapter,
    HandshakeIamAdapter,
    HandshakeIamAuthority,
    HandshakeIamRequest,
    HelloClaimParser,
    LogicalConnectionCloseReason,
    LogicalConnectionState,
    LogicalConnectionStateMachine,
    TestIamAction,
    TestIamOutcome,
)
from ns_runtime.protocol import JsonV1Codec

from tests.test_runtime_connection_handshake import _FakeTransportSession


UTC_START = datetime(2026, 7, 21, tzinfo=timezone.utc)
CONNECTION_ID = "connection_123e4567e89b42d3a456426614174000"
SESSION_ID = "session_123e4567e89b42d3a456426614174001"


class ConnectionHandshakeAuthenticationTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.clock = ControlledClock(utc_start=UTC_START)
        self.supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        self.transport = _FakeTransportSession()
        self.machine = LogicalConnectionStateMachine()

    async def asyncTearDown(self) -> None:
        await self.supervisor.shutdown(timeout_seconds=1)

    async def test_explicit_test_adapter_authenticates_and_copies_authority(self) -> None:
        configured = _authority()
        adapter = DeterministicTestIamAdapter(
            (TestIamOutcome(action=TestIamAction.ALLOW, authority=configured),),
            clock=self.clock,
        )
        authenticator = self._authenticator(adapter)
        await self.transport.messages.put(_hello())
        result = await authenticator.authenticate()
        self.assertIs(LogicalConnectionState.AUTHENTICATED, self.machine.state)
        self.assertEqual("client", result.claims.component_type)
        self.assertEqual(
            frozenset({"runtime.connection", "runtime.management"}),
            result.claims.requested_capabilities,
        )
        self.assertEqual(frozenset({"runtime.connection"}), result.authority.capabilities)
        self.assertIsNot(configured, result.authority)
        self.assertEqual(1, adapter.call_count)
        self.assertEqual(1, adapter.consumed_credential_count)
        self.assertEqual((), self.supervisor.pending_task_names)
        self.assertEqual(0, self.clock.pending_sleep_count)
        combined_repr = repr(result) + repr(adapter) + repr(configured)
        self.assertNotIn("top-secret-token", combined_repr)
        with self.assertRaises(TypeError):
            result.authority.permissions["runtime.connection"] = False  # type: ignore[index]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.authority.component_type = "node"  # type: ignore[misc]

    async def test_production_adapter_is_explicit_and_fails_closed(self) -> None:
        authenticator = self._authenticator(FailClosedHandshakeIamAdapter())
        await self.transport.messages.put(_hello())
        with self.assertRaises(NsRuntimeIamDeniedError) as context:
            await authenticator.authenticate()
        self.assertEqual(
            "production_iam_unavailable",
            context.exception.details["reason"],
        )
        self.assertIs(LogicalConnectionState.CLOSED, self.machine.state)
        self.assertIs(LogicalConnectionCloseReason.AUTH_FAILED, self.machine.close_reason)

    async def test_configured_denial_is_terminal_without_token_retention(self) -> None:
        adapter = DeterministicTestIamAdapter(
            (TestIamOutcome(action=TestIamAction.DENY),),
            clock=self.clock,
        )
        authenticator = self._authenticator(adapter)
        await self.transport.messages.put(_hello())
        with self.assertRaises(NsRuntimeIamDeniedError):
            await authenticator.authenticate()
        self.assertEqual(1, adapter.consumed_credential_count)
        self.assertNotIn("top-secret-token", repr(authenticator))
        self.assertIs(LogicalConnectionCloseReason.AUTH_FAILED, self.machine.close_reason)

    async def test_total_deadline_cancels_test_adapter_timeout_without_real_sleep(self) -> None:
        adapter = DeterministicTestIamAdapter(
            (TestIamOutcome(action=TestIamAction.TIMEOUT),),
            clock=self.clock,
        )
        authenticator = self._authenticator(adapter)
        await self.transport.messages.put(_hello())
        task = asyncio.create_task(authenticator.authenticate())
        await _wait_until(
            lambda: adapter.call_count == 1 and self.clock.pending_sleep_count >= 2,
        )
        self.clock.advance(10)
        with self.assertRaises(NsRuntimeIamTimeoutError) as context:
            await task
        self.assertEqual(
            "total_handshake_deadline",
            context.exception.details["reason"],
        )
        self.assertEqual((), self.supervisor.pending_task_names)
        self.assertEqual(0, self.clock.pending_sleep_count)
        self.assertIs(LogicalConnectionCloseReason.TIMEOUT_CLOSED, self.machine.close_reason)

    async def test_configured_cancellation_preserves_cancelled_error(self) -> None:
        adapter = DeterministicTestIamAdapter(
            (TestIamOutcome(action=TestIamAction.CANCEL),),
            clock=self.clock,
        )
        authenticator = self._authenticator(adapter)
        await self.transport.messages.put(_hello())
        with self.assertRaises(asyncio.CancelledError):
            await authenticator.authenticate()
        self.assertEqual((), self.supervisor.pending_task_names)
        self.assertIs(LogicalConnectionCloseReason.SHUTDOWN, self.machine.close_reason)

    async def test_expired_authority_is_rejected(self) -> None:
        expired = _authority(
            issued_at=UTC_START - timedelta(minutes=2),
            expires_at=UTC_START - timedelta(minutes=1),
        )
        adapter = DeterministicTestIamAdapter(
            (TestIamOutcome(action=TestIamAction.EXPIRED, authority=expired),),
            clock=self.clock,
        )
        authenticator = self._authenticator(adapter)
        await self.transport.messages.put(_hello())
        with self.assertRaises(NsRuntimeIamDeniedError) as context:
            await authenticator.authenticate()
        self.assertEqual("authority_expired", context.exception.details["reason"])
        self.assertIs(LogicalConnectionCloseReason.AUTH_FAILED, self.machine.close_reason)

    async def test_inconsistent_component_identity_is_rejected(self) -> None:
        inconsistent = _authority(component_type="node")
        adapter = DeterministicTestIamAdapter(
            (
                TestIamOutcome(
                    action=TestIamAction.INCONSISTENT,
                    authority=inconsistent,
                ),
            ),
            clock=self.clock,
        )
        authenticator = self._authenticator(adapter)
        await self.transport.messages.put(_hello(component_type="client"))
        with self.assertRaises(NsRuntimeIamDeniedError) as context:
            await authenticator.authenticate()
        self.assertEqual(
            "authority_identity_inconsistent",
            context.exception.details["reason"],
        )
        self.assertIs(LogicalConnectionCloseReason.AUTH_FAILED, self.machine.close_reason)

    async def test_resume_claim_uses_registered_extension_and_typed_ids(self) -> None:
        adapter = DeterministicTestIamAdapter(
            (TestIamOutcome(action=TestIamAction.ALLOW, authority=_authority()),),
            clock=self.clock,
        )
        authenticator = self._authenticator(adapter)
        await self.transport.messages.put(_hello(resume=True))
        result = await authenticator.authenticate()
        self.assertIsNotNone(result.claims.resume)
        assert result.claims.resume is not None
        self.assertEqual(CONNECTION_ID, result.claims.resume.connection_id)
        self.assertEqual(3, result.claims.resume.connection_epoch)
        self.assertEqual(SESSION_ID, result.claims.resume.session_id)
        self.assertNotIn(CONNECTION_ID, repr(result))
        self.assertNotIn(SESSION_ID, repr(result))

    async def test_protocol_mismatch_fails_before_iam_and_releases_token(self) -> None:
        adapter = DeterministicTestIamAdapter(
            (TestIamOutcome(action=TestIamAction.ALLOW, authority=_authority()),),
            clock=self.clock,
        )
        authenticator = self._authenticator(adapter)
        await self.transport.messages.put(_hello(requested_version="1.0.1"))
        with self.assertRaises(NsRuntimeEnvelopeSchemaError) as context:
            await authenticator.authenticate()
        self.assertEqual("protocol_group_mismatch", context.exception.details["reason"])
        self.assertEqual(0, adapter.call_count)
        self.assertIs(LogicalConnectionCloseReason.PROTOCOL_FAILED, self.machine.close_reason)
        self.assertNotIn("top-secret-token", repr(context.exception.details))
        self.assertEqual((), self.supervisor.failures)

    async def test_unknown_resume_extension_fails_closed_before_iam(self) -> None:
        adapter = DeterministicTestIamAdapter(
            (TestIamOutcome(action=TestIamAction.ALLOW, authority=_authority()),),
            clock=self.clock,
        )
        authenticator = self._authenticator(adapter)
        await self.transport.messages.put(_hello(unknown_extension=True))
        with self.assertRaises(NsRuntimeEnvelopeSchemaError):
            await authenticator.authenticate()
        self.assertEqual(0, adapter.call_count)
        self.assertIs(LogicalConnectionCloseReason.PROTOCOL_FAILED, self.machine.close_reason)

    async def test_hostile_adapter_failure_is_normalized_and_credential_cleared(self) -> None:
        adapter = _CapturingFailureAdapter()
        authenticator = self._authenticator(adapter)
        await self.transport.messages.put(_hello())
        with self.assertRaises(NsRuntimeIamUnavailableError) as context:
            await authenticator.authenticate()
        self.assertIsNone(context.exception.__cause__)
        self.assertEqual("adapter_failure", context.exception.details["reason"])
        self.assertIsNotNone(adapter.request)
        assert adapter.request is not None
        self.assertFalse(adapter.request.credential.available)
        self.assertNotIn("top-secret-token", repr(adapter.request))
        self.assertIs(LogicalConnectionCloseReason.AUTH_FAILED, self.machine.close_reason)

    async def test_authenticator_is_one_shot_and_does_not_read_second_hello(self) -> None:
        adapter = DeterministicTestIamAdapter(
            (TestIamOutcome(action=TestIamAction.ALLOW, authority=_authority()),),
            clock=self.clock,
        )
        authenticator = self._authenticator(adapter)
        await self.transport.messages.put(_hello())
        await authenticator.authenticate()
        await self.transport.messages.put(_hello())
        with self.assertRaises(NsRuntimeIamDeniedError):
            await authenticator.authenticate()
        self.assertEqual(1, self.transport.receive_calls)

    def test_test_adapter_outcome_matrix_is_explicit_and_offline(self) -> None:
        self.assertEqual(
            {"allow", "deny", "timeout", "cancel", "expired", "inconsistent"},
            {item.value for item in TestIamAction},
        )
        self.assertNotIn("http", DeterministicTestIamAdapter.__module__)
        self.assertNotIn("token", repr(TestIamOutcome(
            action=TestIamAction.ALLOW,
            authority=_authority(),
        )))

    def _authenticator(
        self,
        adapter: HandshakeIamAdapter,
    ) -> ConnectionHandshakeAuthenticator:
        receiver = ConnectionHelloReceiver(
            transport_session=self.transport,
            state_machine=self.machine,
            clock=self.clock,
            task_supervisor=self.supervisor,
            task_sequence=31,
            timeout_seconds=10,
            codec=JsonV1Codec(),
        )
        return ConnectionHandshakeAuthenticator(
            hello_receiver=receiver,
            claim_parser=HelloClaimParser(),
            iam_adapter=adapter,
            clock=self.clock,
            task_supervisor=self.supervisor,
            task_sequence=31,
            timeout_seconds=10,
        )


class _HostileIamError(RuntimeError):
    def __str__(self) -> str:
        raise AssertionError("hostile IAM error must not be stringified")

    def __repr__(self) -> str:
        raise AssertionError("hostile IAM error must not be represented")


class _CapturingFailureAdapter(HandshakeIamAdapter):
    def __init__(self) -> None:
        self.request: HandshakeIamRequest | None = None

    async def authenticate(
        self,
        request: HandshakeIamRequest,
    ) -> HandshakeIamAuthority:
        self.request = request
        credential = request.credential.take()
        del credential
        raise _HostileIamError


async def _wait_until(predicate) -> None:
    for _ in range(40):
        if predicate():
            return
        await asyncio.sleep(0)
    raise AssertionError("condition was not reached")


def _authority(
    *,
    component_type: str = "client",
    issued_at: datetime = UTC_START,
    expires_at: datetime = UTC_START + timedelta(minutes=5),
) -> HandshakeIamAuthority:
    return HandshakeIamAuthority(
        identity="identity:test-user",
        tenant_id="tenant:test",
        component_type=component_type,
        capabilities=frozenset({"runtime.connection"}),
        permissions={"runtime.connection": True},
        permission_snapshot_ref="permission:snapshot-test",
        permission_digest="sha256:permission-test",
        permission_version="version:1",
        issued_at=issued_at,
        expires_at=expires_at,
        resume_eligible=True,
        iam_mode="test",
    )


def _hello(
    *,
    component_type: str = "client",
    requested_version: str = "1.0.0",
    resume: bool = False,
    unknown_extension: bool = False,
) -> str:
    value: dict[str, object] = {
        "protocol": {"major": 1, "minor": 0, "patch": 0},
        "message": {
            "message_id": "message_00000000000000000000000000000001",
            "type": "connection.hello",
            "category": "connection",
            "priority": 0,
            "created_at": "2026-07-21T00:00:00Z",
            "reliability": "best_effort",
        },
        "payload": {
            "mode": "inline",
            "inline": {
                "token": "top-secret-token",
                "component_type": component_type,
                "requested_version": requested_version,
                "min_version": "1.0.0",
                "requested_capabilities": [
                    "runtime.connection",
                    "runtime.management",
                ],
            },
        },
    }
    if resume:
        value["extensions"] = {
            "ns.connection_resume": {
                "connection_id": CONNECTION_ID,
                "connection_epoch": 3,
                "session_id": SESSION_ID,
            },
        }
    elif unknown_extension:
        value["extensions"] = {"attacker.resume": {"credential": "secret"}}
    return json.dumps(value, separators=(",", ":"))


if __name__ == "__main__":
    unittest.main()
