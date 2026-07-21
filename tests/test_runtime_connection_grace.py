# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import dataclasses
import unittest

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import NsStateError
from ns_common.time import ControlledClock
from ns_runtime.connection import (
    HelloResumeRequest,
    LocalConnectionIndex,
    LogicalConnectionCloseReason,
    LogicalConnectionState,
    LogicalConnectionTransportMap,
    ReconnectGracePhase,
    ReconnectGracePolicy,
    ReconnectGraceService,
)
from ns_runtime.transport import WEBSOCKET_TCP_CAPABILITIES

from tests.test_runtime_connection_binding import (
    CONNECTION_ID,
    RESUMED_SESSION_ID,
    SESSION_ID,
    UTC_START,
    _context,
    _transport,
)
from tests.test_runtime_connection_handshake import _FakeTransportSession
from tests.test_runtime_connection_index import _authenticated_machine


class ReconnectGraceTestCase(unittest.IsolatedAsyncioTestCase):
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
        self.mapping = LogicalConnectionTransportMap(
            session_context=self.context,
            transport_session=self.transport,
        )
        self.service = _service(
            context=self.context,
            index=self.index,
            mapping=self.mapping,
            clock=self.clock,
            supervisor=self.supervisor,
        )

    async def asyncTearDown(self) -> None:
        await self.supervisor.shutdown(timeout_seconds=1)

    async def test_disconnect_enters_default_30_second_grace_and_detaches_transport(self) -> None:
        snapshot = await self._enter()

        self.assertIs(ReconnectGracePhase.WAITING, snapshot.phase)
        self.assertEqual(0.0, snapshot.started_monotonic)
        self.assertEqual(30.0, snapshot.deadline_monotonic)
        self.assertEqual(0, snapshot.connection_epoch)
        self.assertTrue(snapshot.deadline_pending)
        self.assertEqual((), await self.index.active_targets())
        entry = await self.index.lookup_connection(CONNECTION_ID)
        assert entry is not None
        self.assertIs(LogicalConnectionState.ACTIVE, entry.state)
        self.assertFalse(entry.active_target_eligible)
        self.assertIsNone((await self.mapping.snapshot()).transport)
        self.assertEqual(0, self.transport.close_calls)

    async def test_repeated_disconnect_is_idempotent_without_second_deadline(self) -> None:
        first = await self._enter()
        second = await self._enter()

        self.assertEqual(first, second)
        self.assertEqual(
            ("logical-grace-101-deadline",),
            self.supervisor.pending_task_names,
        )

    async def test_grace_expiry_closes_logical_connection_and_all_indexes(self) -> None:
        await self._enter()
        await _wait_until(lambda: self.clock.pending_sleep_count == 1)

        self.clock.advance(30)
        await _wait_until(lambda: self.machine.state is LogicalConnectionState.CLOSED)

        snapshot = await self.service.snapshot()
        self.assertIs(ReconnectGracePhase.CLOSED, snapshot.phase)
        self.assertIs(
            LogicalConnectionCloseReason.TRANSPORT_DISCONNECTED,
            snapshot.terminal_reason,
        )
        self.assertIsNone(await self.index.lookup_connection(CONNECTION_ID))
        await _wait_until(lambda: not self.supervisor.pending_task_names)
        self.assertEqual(0, self.clock.pending_sleep_count)

    async def test_resume_claim_before_deadline_is_single_use_and_cancels_timer(self) -> None:
        await self._enter()

        claim = await self.service.claim_resume(_request())

        self.assertEqual(CONNECTION_ID, claim.connection_id)
        self.assertEqual(SESSION_ID, claim.session_id)
        self.assertEqual(0, claim.connection_epoch)
        self.assertNotIn(CONNECTION_ID, repr(claim))
        with self.assertRaises(NsStateError):
            await self.service.claim_resume(_request())
        await _wait_until(lambda: not self.supervisor.pending_task_names)
        self.assertEqual(0, self.clock.pending_sleep_count)

    async def test_resume_at_deadline_loses_to_expiry(self) -> None:
        await self._enter()
        self.clock.advance(30)

        with self.assertRaises(NsStateError) as context:
            await self.service.claim_resume(_request())

        self.assertEqual("grace_expired", context.exception.details["reason"])
        self.assertIs(LogicalConnectionState.CLOSED, self.machine.state)
        self.assertIsNone(await self.index.lookup_connection(CONNECTION_ID))

    async def test_resume_reference_mismatches_are_rejected_without_consuming_grace(self) -> None:
        await self._enter()
        cases = (
            (
                HelloResumeRequest(
                    connection_id="connection_123e4567e89b42d3a456426614174090",
                    connection_epoch=0,
                    session_id=SESSION_ID,
                ),
                "resume_connection_mismatch",
            ),
            (
                HelloResumeRequest(
                    connection_id=CONNECTION_ID,
                    connection_epoch=1,
                    session_id=SESSION_ID,
                ),
                "resume_epoch_mismatch",
            ),
            (
                HelloResumeRequest(
                    connection_id=CONNECTION_ID,
                    connection_epoch=0,
                    session_id="session_123e4567e89b42d3a456426614174091",
                ),
                "resume_session_mismatch",
            ),
        )
        for request, reason in cases:
            with self.subTest(reason=reason):
                with self.assertRaises(NsStateError) as context:
                    await self.service.claim_resume(request)
                self.assertEqual(reason, context.exception.details["reason"])
        self.assertIs(ReconnectGracePhase.WAITING, (await self.service.snapshot()).phase)

    async def test_concurrent_resume_claims_allow_exactly_one(self) -> None:
        await self._enter()

        outcomes = await asyncio.gather(
            self.service.claim_resume(_request()),
            self.service.claim_resume(_request()),
            return_exceptions=True,
        )

        self.assertEqual(1, sum(not isinstance(item, BaseException) for item in outcomes))
        self.assertEqual(1, sum(isinstance(item, NsStateError) for item in outcomes))
        self.assertIs(ReconnectGracePhase.CLAIMED, (await self.service.snapshot()).phase)

    async def test_shutdown_kick_or_drain_can_end_grace_early(self) -> None:
        await self._enter()

        await self.service.terminate(LogicalConnectionCloseReason.SHUTDOWN)

        self.assertIs(LogicalConnectionState.CLOSED, self.machine.state)
        self.assertIs(LogicalConnectionCloseReason.SHUTDOWN, self.machine.close_reason)
        self.assertEqual((), await self.index.active_targets())
        await _wait_until(lambda: not self.supervisor.pending_task_names)

    async def test_complete_resume_requires_new_mapping_index_and_active_target(self) -> None:
        await self._enter()
        await self.service.claim_resume(_request())
        resumed = dataclasses.replace(
            self.context,
            session_id=RESUMED_SESSION_ID,
            connection_epoch=1,
        )
        replacement = _transport(suffix="70")
        with self.assertRaises(NsStateError):
            await self.service.complete_resume(resumed)

        await self.index.replace_session_context(resumed)
        await self.mapping.replace_transport_session(
            session_context=resumed,
            transport_session=replacement,
        )
        await self.index.restore_active_target(CONNECTION_ID)
        await self.service.complete_resume(resumed)

        snapshot = await self.service.snapshot()
        self.assertIs(ReconnectGracePhase.RESUMED, snapshot.phase)
        self.assertEqual(1, snapshot.connection_epoch)
        self.assertEqual(1, len(await self.index.active_targets()))
        self.assertIsNotNone((await self.mapping.snapshot()).transport)

    async def test_disconnect_from_draining_is_not_a_reconnect_grace(self) -> None:
        await self.index.transition(CONNECTION_ID, LogicalConnectionState.DRAINING)

        with self.assertRaises(NsStateError) as context:
            await self._enter()

        self.assertEqual("active_session_required", context.exception.details["reason"])
        self.assertEqual((), self.supervisor.pending_task_names)
        self.assertIsNotNone((await self.mapping.snapshot()).transport)

    async def test_snapshot_is_frozen_and_contains_only_minimal_grace_state(self) -> None:
        snapshot = await self._enter()
        with self.assertRaises((dataclasses.FrozenInstanceError, TypeError)):
            snapshot.phase = ReconnectGracePhase.CLOSED  # type: ignore[misc]
        self.assertFalse(hasattr(snapshot, "transport"))
        self.assertFalse(hasattr(snapshot, "payload"))
        self.assertFalse(hasattr(snapshot, "permissions"))

    async def _enter(self):
        return await self.service.enter(
            transport_session_id=self.transport.identity.transport_session_id,
        )


def _service(
    *,
    context,
    index,
    mapping,
    clock,
    supervisor,
) -> ReconnectGraceService:
    return ReconnectGraceService(
        session_context=context,
        connection_index=index,
        transport_mapping=mapping,
        clock=clock,
        task_supervisor=supervisor,
        task_sequence=101,
        policy=ReconnectGracePolicy(),
    )


def _request() -> HelloResumeRequest:
    return HelloResumeRequest(
        connection_id=CONNECTION_ID,
        connection_epoch=0,
        session_id=SESSION_ID,
    )


async def _wait_until(predicate) -> None:
    for _ in range(100):
        if predicate():
            return
        await asyncio.sleep(0)
    raise AssertionError("condition was not reached")


if __name__ == "__main__":
    unittest.main()
