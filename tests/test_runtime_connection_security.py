# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import dataclasses
import unittest

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import NsRuntimeIamDeniedError
from ns_common.time import ControlledClock
from ns_runtime.connection import (
    DeterministicTestSecurityAuditSink,
    LocalConnectionIndex,
    LogicalConnectionCloseReason,
    LogicalConnectionState,
    LogicalConnectionTransportMap,
    NonResumableCloseKind,
    NonResumableConnectionGuard,
    NonResumablePublicError,
    ReconnectGracePhase,
    ReconnectGraceService,
)
from ns_runtime.transport import WEBSOCKET_TCP_CAPABILITIES

from tests.test_runtime_connection_binding import CONNECTION_ID, UTC_START, _context
from tests.test_runtime_connection_handshake import _FakeTransportSession
from tests.test_runtime_connection_index import _authenticated_machine


class _BlockingTransport(_FakeTransportSession):
    def __init__(self) -> None:
        super().__init__(capabilities=WEBSOCKET_TCP_CAPABILITIES)
        self.close_started = asyncio.Event()
        self.close_release = asyncio.Event()

    async def close(self):
        self.close_started.set()
        await self.close_release.wait()
        return await super().close()


class NonResumableConnectionTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_all_security_classifications_have_consistent_fixed_outcomes(self) -> None:
        cases = (
            (
                NonResumableCloseKind.KICK,
                LogicalConnectionCloseReason.KICKED,
                NonResumablePublicError.CONNECTION_KICKED,
            ),
            (
                NonResumableCloseKind.SECURITY_VIOLATION,
                LogicalConnectionCloseReason.SECURITY_CLOSED,
                NonResumablePublicError.SECURITY_CLOSED,
            ),
            (
                NonResumableCloseKind.SEVERE_PROTOCOL_VIOLATION,
                LogicalConnectionCloseReason.PROTOCOL_FAILED,
                NonResumablePublicError.PROTOCOL_CLOSED,
            ),
            (
                NonResumableCloseKind.MALICIOUS_DUPLICATE_CONFIRMATION,
                LogicalConnectionCloseReason.SECURITY_CLOSED,
                NonResumablePublicError.DUPLICATE_CONFIRMATION_REJECTED,
            ),
            (
                NonResumableCloseKind.POLICY_NON_RECOVERABLE,
                LogicalConnectionCloseReason.ISOLATED_CLOSED,
                NonResumablePublicError.NON_RECOVERABLE_CLOSED,
            ),
        )
        for kind, close_reason, public_error in cases:
            with self.subTest(kind=kind.value):
                fixture = await _active_fixture()
                snapshot = await fixture.guard.close(kind)
                self.assertTrue(snapshot.non_resumable)
                assert snapshot.decision is not None
                self.assertIs(close_reason, snapshot.decision.close_reason)
                self.assertIs(public_error, snapshot.decision.public_error)
                self.assertIs(close_reason, fixture.machine.close_reason)
                self.assertIs(LogicalConnectionState.CLOSED, snapshot.state)
                self.assertEqual(1, len(fixture.audit.events))
                event = fixture.audit.events[0]
                self.assertIs(kind, event.classification)
                self.assertIs(close_reason, event.close_reason)
                self.assertIs(public_error, event.public_error)

    async def test_resume_eligibility_is_revoked_before_retryable_close_finishes(self) -> None:
        fixture = await _active_fixture()
        fixture.transport.close_failures_remaining = 1

        snapshot = await fixture.guard.close(
            NonResumableCloseKind.SECURITY_VIOLATION,
        )

        self.assertIs(LogicalConnectionState.CLOSING, snapshot.state)
        entry = await fixture.index.lookup_connection(CONNECTION_ID)
        assert entry is not None
        self.assertFalse(entry.session_context.resume_eligible)
        self.assertFalse(entry.active_target_eligible)
        with self.assertRaises(NsRuntimeIamDeniedError) as context:
            await fixture.guard.require_resumable()
        self.assertEqual("connection_non_resumable", context.exception.details["reason"])
        self.assertTrue(await fixture.guard.retry_cleanup())
        self.assertIsNone(await fixture.index.lookup_connection(CONNECTION_ID))

    async def test_security_close_during_grace_cancels_deadline_and_forbids_resume(self) -> None:
        fixture = await _active_fixture(with_grace=True)
        assert fixture.grace is not None
        await fixture.grace.enter(
            transport_session_id=fixture.transport.identity.transport_session_id,
        )
        await _wait_until(lambda: fixture.clock.pending_sleep_count == 1)

        snapshot = await fixture.guard.close(NonResumableCloseKind.KICK)

        self.assertIs(LogicalConnectionState.CLOSED, snapshot.state)
        self.assertIs(ReconnectGracePhase.CLOSED, (await fixture.grace.snapshot()).phase)
        self.assertEqual(0, fixture.clock.pending_sleep_count)
        self.assertIsNone(await fixture.index.lookup_connection(CONNECTION_ID))
        with self.assertRaises(NsRuntimeIamDeniedError):
            await fixture.guard.require_resumable()
        await fixture.supervisor.shutdown(timeout_seconds=1)

    async def test_audit_sink_ordinary_failure_never_allows_or_blocks_security_close(self) -> None:
        fixture = await _active_fixture()
        fixture.audit.failure = RuntimeError("audit-storage-secret")

        snapshot = await fixture.guard.close(
            NonResumableCloseKind.MALICIOUS_DUPLICATE_CONFIRMATION,
        )

        self.assertTrue(snapshot.non_resumable)
        self.assertTrue(snapshot.audit_attempted)
        self.assertFalse(snapshot.audit_succeeded)
        self.assertIs(LogicalConnectionState.CLOSED, fixture.machine.state)
        self.assertIsNone(await fixture.index.lookup_connection(CONNECTION_ID))

    async def test_repeated_security_close_is_idempotent_and_audited_once(self) -> None:
        fixture = await _active_fixture()

        first = await fixture.guard.close(NonResumableCloseKind.KICK)
        second = await fixture.guard.close(
            NonResumableCloseKind.SECURITY_VIOLATION,
        )

        self.assertEqual(first, second)
        assert second.decision is not None
        self.assertIs(NonResumableCloseKind.KICK, second.decision.kind)
        self.assertEqual(1, len(fixture.audit.events))
        self.assertEqual(1, fixture.transport.close_calls)

    async def test_cancelled_transport_close_keeps_revocation_and_audit_then_retries(self) -> None:
        transport = _BlockingTransport()
        fixture = await _active_fixture(transport=transport)
        task = asyncio.create_task(
            fixture.guard.close(NonResumableCloseKind.SECURITY_VIOLATION),
        )
        await transport.close_started.wait()

        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task

        entry = await fixture.index.lookup_connection(CONNECTION_ID)
        assert entry is not None
        self.assertIs(LogicalConnectionState.CLOSING, entry.state)
        self.assertFalse(entry.session_context.resume_eligible)
        self.assertEqual(1, len(fixture.audit.events))
        transport.close_release.set()
        self.assertTrue(await fixture.guard.retry_cleanup())

    async def test_security_audit_is_typed_bounded_and_contains_no_attacker_data(self) -> None:
        fixture = await _active_fixture()
        await fixture.guard.close(NonResumableCloseKind.SEVERE_PROTOCOL_VIOLATION)
        event = fixture.audit.events[0]
        combined = repr(event) + repr(await fixture.guard.snapshot())

        self.assertTrue(event.connection_summary.startswith("sha256:"))
        self.assertNotIn(CONNECTION_ID, combined)
        for forbidden in (
            "token", "payload", "peer", "Authorization", "attacker reason",
        ):
            self.assertNotIn(forbidden, combined)
        self.assertFalse(hasattr(event, "raw_reason"))
        self.assertFalse(hasattr(event, "transport"))

    async def test_ordinary_disconnect_does_not_set_non_resumable_flag(self) -> None:
        fixture = await _active_fixture(with_grace=True)
        assert fixture.grace is not None
        await fixture.grace.enter(
            transport_session_id=fixture.transport.identity.transport_session_id,
        )

        snapshot = await fixture.guard.snapshot()

        self.assertFalse(snapshot.non_resumable)
        self.assertIsNone(snapshot.decision)
        self.assertEqual(0, len(fixture.audit.events))
        self.assertIs(ReconnectGracePhase.WAITING, (await fixture.grace.snapshot()).phase)
        await fixture.grace.terminate(LogicalConnectionCloseReason.SHUTDOWN)
        await fixture.supervisor.shutdown(timeout_seconds=1)

    async def test_snapshot_is_frozen_and_sink_is_explicit(self) -> None:
        fixture = await _active_fixture()
        snapshot = await fixture.guard.snapshot()
        with self.assertRaises((dataclasses.FrozenInstanceError, TypeError)):
            snapshot.non_resumable = True  # type: ignore[misc]
        with self.assertRaises(TypeError):
            NonResumableConnectionGuard(  # type: ignore[call-arg]
                session_context=fixture.context,
                connection_index=fixture.index,
                clock=fixture.clock,
                transport_session=fixture.transport,
            )


@dataclasses.dataclass
class _Fixture:
    clock: ControlledClock
    supervisor: TaskSupervisor
    transport: _FakeTransportSession
    context: object
    machine: object
    index: LocalConnectionIndex
    audit: DeterministicTestSecurityAuditSink
    guard: NonResumableConnectionGuard
    grace: ReconnectGraceService | None


async def _active_fixture(
    *,
    transport: _FakeTransportSession | None = None,
    with_grace: bool = False,
) -> _Fixture:
    clock = ControlledClock(utc_start=UTC_START)
    supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
    actual_transport = transport or _FakeTransportSession(
        capabilities=WEBSOCKET_TCP_CAPABILITIES,
    )
    context = _context(actual_transport, clock=clock)
    machine = await _authenticated_machine()
    index = LocalConnectionIndex()
    await index.add_authenticated(session_context=context, state_machine=machine)
    await index.transition(CONNECTION_ID, LogicalConnectionState.ACTIVE)
    grace = None
    if with_grace:
        mapping = LogicalConnectionTransportMap(
            session_context=context,
            transport_session=actual_transport,
        )
        grace = ReconnectGraceService(
            session_context=context,
            connection_index=index,
            transport_mapping=mapping,
            clock=clock,
            task_supervisor=supervisor,
            task_sequence=121,
        )
    audit = DeterministicTestSecurityAuditSink()
    guard = NonResumableConnectionGuard(
        session_context=context,
        connection_index=index,
        clock=clock,
        audit_sink=audit,
        transport_session=(None if with_grace else actual_transport),
        grace_service=grace,
    )
    return _Fixture(
        clock=clock,
        supervisor=supervisor,
        transport=actual_transport,
        context=context,
        machine=machine,
        index=index,
        audit=audit,
        guard=guard,
        grace=grace,
    )


async def _wait_until(predicate) -> None:
    for _ in range(100):
        if predicate():
            return
        await asyncio.sleep(0)
    raise AssertionError("condition was not reached")


if __name__ == "__main__":
    unittest.main()
