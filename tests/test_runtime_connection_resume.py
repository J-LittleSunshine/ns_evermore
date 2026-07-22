# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import dataclasses
import json
import unittest
from uuid import UUID

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import (
    NsRuntimeIamDeniedError,
    NsRuntimeIamTimeoutError,
    NsRuntimeProtocolViolationError,
    NsStateError,
)
from ns_common.identifiers import IdentifierFactory
from ns_common.iam import IamPrincipalType
from ns_common.time import ControlledClock
from ns_runtime.connection import (
    ConnectionEpochGate,
    ConnectionLifecycleAuditBoundary,
    ConnectionResumeCoordinator,
    DeterministicTestConnectionAuditSink,
    DeterministicTestIamAdapter,
    HandshakeCredential,
    HelloResumeRequest,
    LocalConnectionIndex,
    LogicalConnectionCloseReason,
    LogicalConnectionState,
    LogicalConnectionTransportMap,
    LogicalSessionIdentityFactory,
    ParsedHello,
    PendingHelloClaims,
    ReconnectGracePolicy,
    ReconnectGraceService,
    TestIamAction,
    TestIamOutcome,
)
from ns_runtime.protocol import ProtocolVersion
from ns_runtime.transport import WEBSOCKET_TCP_CAPABILITIES

from tests.test_runtime_connection_accepted import _builder
from tests.test_runtime_connection_binding import (
    CONNECTION_ID,
    SESSION_ID,
    UTC_START,
    _context,
    _transport,
)
from tests.test_runtime_connection_handshake import _FakeTransportSession
from tests.test_runtime_connection_index import _authenticated_machine
from tests.test_runtime_connection_session import _authority


NEW_SESSION_ID = "session_123e4567e89b42d3a456426614174111"


class _ResumeTransport(_FakeTransportSession):
    def __init__(self, *, suffix: str = "110") -> None:
        replacement = _transport(suffix=suffix)
        super().__init__(capabilities=WEBSOCKET_TCP_CAPABILITIES)
        self._identity = replacement.identity
        self.sent: list[str] = []
        self.send_failure: BaseException | None = None

    async def send(self, text: str) -> None:
        if self.send_failure is not None:
            raise self.send_failure
        self.sent.append(text)


class ConnectionResumeTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.clock = ControlledClock(utc_start=UTC_START)
        self.supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        self.old_transport = _FakeTransportSession(
            capabilities=WEBSOCKET_TCP_CAPABILITIES,
        )
        self.current = _context(self.old_transport, clock=self.clock)
        self.machine = await _authenticated_machine()
        self.index = LocalConnectionIndex()
        await self.index.add_authenticated(
            session_context=self.current,
            state_machine=self.machine,
        )
        await self.index.transition(CONNECTION_ID, LogicalConnectionState.ACTIVE)
        self.mapping = LogicalConnectionTransportMap(
            session_context=self.current,
            transport_session=self.old_transport,
        )
        self.grace = ReconnectGraceService(
            session_context=self.current,
            connection_index=self.index,
            transport_mapping=self.mapping,
            clock=self.clock,
            task_supervisor=self.supervisor,
            task_sequence=110,
            policy=ReconnectGracePolicy(),
        )
        await self.grace.enter(
            transport_session_id=self.old_transport.identity.transport_session_id,
        )
        self.new_transport = _ResumeTransport()

    async def asyncTearDown(self) -> None:
        await self.supervisor.shutdown(timeout_seconds=1)

    async def test_resume_reauthenticates_negotiates_sends_accepted_and_increments_epoch(self) -> None:
        adapter = _adapter(self.clock)
        coordinator = self._coordinator(adapter)

        result = await coordinator.resume(_parsed())

        context = result.session.context
        self.assertEqual(CONNECTION_ID, context.connection_id)
        self.assertEqual(NEW_SESSION_ID, context.session_id)
        self.assertEqual(1, context.connection_epoch)
        self.assertEqual(0, result.previous_connection_epoch)
        self.assertEqual(frozenset({"runtime.connection"}), context.capabilities)
        self.assertEqual(1, adapter.call_count)
        self.assertEqual(1, adapter.consumed_credential_count)
        self.assertEqual(1, len(self.new_transport.sent))
        accepted = json.loads(self.new_transport.sent[0])
        self.assertEqual("connection.accepted", accepted["message"]["type"])
        self.assertEqual(NEW_SESSION_ID, accepted["payload"]["inline"]["session_id"])
        entry = await self.index.lookup_connection(CONNECTION_ID)
        assert entry is not None
        self.assertEqual(context, entry.session_context)
        self.assertTrue(entry.active_target_eligible)
        mapping = await self.mapping.snapshot()
        assert mapping.transport is not None
        self.assertEqual(context, mapping.session_context)
        self.assertEqual(
            self.new_transport.identity.transport_session_id,
            mapping.transport.transport_session_id,
        )
        self.assertEqual((), self.supervisor.pending_task_names)

    async def test_identity_tenant_and_component_mismatch_fail_closed(self) -> None:
        cases = (
            ({"identity": "identity:attacker"}, "resume_identity_mismatch"),
            ({"tenant_id": "tenant:other"}, "resume_tenant_mismatch"),
            ({"component_type": "node"}, "resume_component_type_mismatch"),
            (
                {"principal_type": IamPrincipalType.BACKEND_SERVICE},
                "resume_principal_type_mismatch",
            ),
        )
        for changes, reason in cases:
            with self.subTest(reason=reason):
                await self._reset_after_terminal_if_needed()
                authority = dataclasses.replace(_resume_authority(), **changes)
                coordinator = self._coordinator(_adapter(self.clock, authority=authority))
                with self.assertRaises(NsRuntimeIamDeniedError) as context:
                    await coordinator.resume(_parsed())
                self.assertEqual(reason, context.exception.details["reason"])
                self.assertIs(LogicalConnectionState.CLOSED, self.machine.state)
                self.assertIsNone(await self.index.lookup_connection(CONNECTION_ID))

    async def test_resume_eligibility_is_required_from_old_and_new_authority(self) -> None:
        self.current = dataclasses.replace(self.current, resume_eligible=False)
        await self._rebuild_active_grace()
        coordinator = self._coordinator(_adapter(self.clock))
        with self.assertRaises(NsRuntimeIamDeniedError) as old:
            await coordinator.resume(_parsed())
        self.assertEqual("current_session_not_resume_eligible", old.exception.details["reason"])

        await self._reset_after_terminal_if_needed()
        authority = dataclasses.replace(_resume_authority(), resume_eligible=False)
        coordinator = self._coordinator(_adapter(self.clock, authority=authority))
        with self.assertRaises(NsRuntimeIamDeniedError) as new:
            await coordinator.resume(_parsed())
        self.assertEqual("authority_not_resume_eligible", new.exception.details["reason"])

    async def test_capability_is_renegotiated_and_cannot_expand_from_client(self) -> None:
        authority = _resume_authority(capabilities=frozenset({"runtime.connection"}))
        coordinator = self._coordinator(_adapter(self.clock, authority=authority))
        parsed = _parsed(capabilities=frozenset({
            "runtime.connection",
            "runtime.management",
        }))

        with self.assertRaises(NsRuntimeIamDeniedError):
            await coordinator.resume(parsed)

        self.assertIs(LogicalConnectionState.CLOSED, self.machine.state)
        self.assertEqual([], self.new_transport.sent)

    async def test_total_deadline_cancels_iam_and_closes_claimed_grace(self) -> None:
        adapter = DeterministicTestIamAdapter(
            (TestIamOutcome(action=TestIamAction.TIMEOUT),),
            clock=self.clock,
        )
        coordinator = self._coordinator(adapter, timeout_seconds=10)
        task = asyncio.create_task(coordinator.resume(_parsed()))
        await _wait_until(lambda: adapter.call_count == 1 and self.clock.pending_sleep_count >= 2)

        self.clock.advance(10)
        with self.assertRaises(NsRuntimeIamTimeoutError) as context:
            await task

        self.assertEqual("resume_total_deadline", context.exception.details["reason"])
        self.assertIs(LogicalConnectionCloseReason.TIMEOUT_CLOSED, self.machine.close_reason)
        self.assertIsNone(await self.index.lookup_connection(CONNECTION_ID))
        self.assertEqual((), self.supervisor.pending_task_names)
        self.assertEqual(0, self.clock.pending_sleep_count)

    async def test_configured_cancellation_closes_claimed_grace(self) -> None:
        adapter = DeterministicTestIamAdapter(
            (TestIamOutcome(action=TestIamAction.CANCEL),),
            clock=self.clock,
        )
        coordinator = self._coordinator(adapter)

        with self.assertRaises(asyncio.CancelledError):
            await coordinator.resume(_parsed())

        self.assertIs(LogicalConnectionCloseReason.SHUTDOWN, self.machine.close_reason)
        self.assertIsNone(await self.index.lookup_connection(CONNECTION_ID))
        self.assertEqual(1, self.new_transport.close_calls)

    async def test_accepted_send_failure_never_restores_active(self) -> None:
        failure = RuntimeError("resume-send-secret")
        self.new_transport.send_failure = failure
        coordinator = self._coordinator(_adapter(self.clock))

        with self.assertRaises(RuntimeError) as context:
            await coordinator.resume(_parsed())

        self.assertIs(failure, context.exception)
        self.assertEqual((), await self.index.active_targets())
        self.assertIsNone(await self.index.lookup_connection(CONNECTION_ID))
        self.assertIs(LogicalConnectionCloseReason.SEND_FAILED, self.machine.close_reason)
        self.assertIsNone((await self.mapping.snapshot()).transport)

    async def test_concurrent_resume_attempts_allow_one_and_close_loser_transport(self) -> None:
        loser_transport = _ResumeTransport(suffix="120")
        first = self._coordinator(_adapter(self.clock))
        second = self._coordinator(
            _adapter(self.clock),
            transport=loser_transport,
            session_uuid=UUID("123e4567-e89b-42d3-a456-426614174112"),
            task_sequence=112,
        )

        outcomes = await asyncio.gather(
            first.resume(_parsed(token="resume-token-one")),
            second.resume(_parsed(token="resume-token-two")),
            return_exceptions=True,
        )

        self.assertEqual(1, sum(not isinstance(item, BaseException) for item in outcomes))
        self.assertEqual(1, sum(isinstance(item, NsStateError) for item in outcomes))
        self.assertIs(LogicalConnectionState.ACTIVE, self.machine.state)
        self.assertEqual(1, len(await self.index.active_targets()))
        self.assertEqual(1, loser_transport.close_calls)

    async def test_epoch_gate_rejects_old_epoch_for_normal_ack_nack_and_defer(self) -> None:
        result = await self._coordinator(_adapter(self.clock)).resume(_parsed())
        context = result.session.context
        gate = ConnectionEpochGate(connection_index=self.index)

        for message_type in (
            "task.dispatch",
            "delivery.ack",
            "delivery.nack",
            "delivery.defer",
        ):
            with self.subTest(message_type=message_type):
                with self.assertRaises(NsRuntimeProtocolViolationError) as old_epoch:
                    await gate.validate(
                        connection_id=CONNECTION_ID,
                        session_id=SESSION_ID,
                        connection_epoch=0,
                        message_type=message_type,
                    )
                self.assertIn(
                    old_epoch.exception.details["reason"],
                    {"session_not_current", "connection_epoch_not_current"},
                )
        validation = await gate.validate(
            connection_id=CONNECTION_ID,
            session_id=context.session_id,
            connection_epoch=1,
            message_type="connection.heartbeat",
        )
        self.assertEqual(1, validation.connection_epoch)

    async def test_invalid_resume_refs_do_not_consume_grace_but_candidate_closes(self) -> None:
        coordinator = self._coordinator(_adapter(self.clock))
        parsed = _parsed(epoch=9)

        with self.assertRaises(NsStateError):
            await coordinator.resume(parsed)

        self.assertEqual(1, self.new_transport.close_calls)
        self.assertIs(LogicalConnectionState.ACTIVE, self.machine.state)
        self.assertFalse((await self.index.lookup_connection(CONNECTION_ID)).active_target_eligible)
        self.assertEqual("waiting", (await self.grace.snapshot()).phase.value)

    async def test_pre_publish_failure_delegates_candidate_close_once(self) -> None:
        terminal_reasons: list[LogicalConnectionCloseReason] = []

        async def retain_candidate(
            reason: LogicalConnectionCloseReason,
        ) -> bool:
            terminal_reasons.append(reason)
            return False

        adapter = DeterministicTestIamAdapter(
            (TestIamOutcome(action=TestIamAction.DENY),),
            clock=self.clock,
        )
        coordinator = self._coordinator(
            adapter,
            candidate_terminator=retain_candidate,
        )

        with self.assertRaises(NsRuntimeIamDeniedError):
            await coordinator.resume(_parsed())

        self.assertEqual(
            [LogicalConnectionCloseReason.AUTH_FAILED],
            terminal_reasons,
        )
        self.assertEqual(0, self.new_transport.close_calls)

    async def test_resume_result_and_errors_do_not_retain_token_or_old_transport(self) -> None:
        parsed = _parsed(token="resume-super-secret")
        result = await self._coordinator(_adapter(self.clock)).resume(parsed)

        self.assertFalse(parsed.credential.available)
        combined = repr(result) + repr(result.session) + repr(result.session.context)
        self.assertNotIn("resume-super-secret", combined)
        mapping = await self.mapping.snapshot()
        assert mapping.transport is not None
        self.assertNotEqual(
            self.old_transport.identity.transport_session_id,
            mapping.transport.transport_session_id,
        )

    def _coordinator(
        self,
        adapter,
        *,
        transport=None,
        session_uuid: UUID = UUID("123e4567-e89b-42d3-a456-426614174111"),
        task_sequence: int = 111,
        timeout_seconds: float = 10,
        candidate_terminator=None,
    ) -> ConnectionResumeCoordinator:
        return ConnectionResumeCoordinator(
            current_context=self.current,
            grace_service=self.grace,
            connection_index=self.index,
            transport_mapping=self.mapping,
            new_transport_session=transport or self.new_transport,
            iam_adapter=adapter,
            logical_identity_factory=LogicalSessionIdentityFactory(
                IdentifierFactory(uuid_factory=lambda: session_uuid),
            ),
            accepted_builder=_builder(self.clock),
            clock=self.clock,
            task_supervisor=self.supervisor,
            task_sequence=task_sequence,
            timeout_seconds=timeout_seconds,
            expected_principal_type=IamPrincipalType.CLIENT,
            candidate_terminator=candidate_terminator,
            audit_boundary=ConnectionLifecycleAuditBoundary(
                session_context=self.current,
                clock=self.clock,
                sink=DeterministicTestConnectionAuditSink(),
            ),
        )

    async def _reset_after_terminal_if_needed(self) -> None:
        if self.machine.state is not LogicalConnectionState.CLOSED:
            return
        self.current = _context(self.old_transport, clock=self.clock)
        await self._rebuild_active_grace()

    async def _rebuild_active_grace(self) -> None:
        await self.supervisor.shutdown(timeout_seconds=1)
        self.supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        self.machine = await _authenticated_machine()
        self.index = LocalConnectionIndex()
        await self.index.add_authenticated(
            session_context=self.current,
            state_machine=self.machine,
        )
        await self.index.transition(CONNECTION_ID, LogicalConnectionState.ACTIVE)
        self.mapping = LogicalConnectionTransportMap(
            session_context=self.current,
            transport_session=self.old_transport,
        )
        self.grace = ReconnectGraceService(
            session_context=self.current,
            connection_index=self.index,
            transport_mapping=self.mapping,
            clock=self.clock,
            task_supervisor=self.supervisor,
            task_sequence=110,
        )
        await self.grace.enter(
            transport_session_id=self.old_transport.identity.transport_session_id,
        )
        self.new_transport = _ResumeTransport()


def _parsed(
    *,
    token: str = "resume-token",
    epoch: int = 0,
    capabilities: frozenset[str] = frozenset({"runtime.connection"}),
) -> ParsedHello:
    return ParsedHello(
        claims=PendingHelloClaims(
            component_type="client",
            requested_version=ProtocolVersion(1, 0, 0),
            minimum_version=ProtocolVersion(1, 0, 0),
            requested_capabilities=capabilities,
            resume=HelloResumeRequest(
                connection_id=CONNECTION_ID,
                connection_epoch=epoch,
                session_id=SESSION_ID,
            ),
        ),
        credential=HandshakeCredential(token),
    )


def _resume_authority(
    *,
    capabilities: frozenset[str] = frozenset({"runtime.connection"}),
):
    return _authority(capabilities=capabilities)


def _adapter(clock, *, authority=None):
    return DeterministicTestIamAdapter(
        (
            TestIamOutcome(
                action=TestIamAction.ALLOW,
                authority=authority or _resume_authority(),
            ),
        ),
        clock=clock,
    )


async def _wait_until(predicate) -> None:
    for _ in range(100):
        if predicate():
            return
        await asyncio.sleep(0)
    raise AssertionError("condition was not reached")


if __name__ == "__main__":
    unittest.main()
