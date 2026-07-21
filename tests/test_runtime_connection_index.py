# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import dataclasses
import unittest

from ns_common.exceptions import NsStateError
from ns_common.time import ControlledClock
from ns_runtime.connection import (
    LocalConnectionIndex,
    LogicalConnectionCloseReason,
    LogicalConnectionState,
    LogicalConnectionStateMachine,
)
from ns_runtime.transport import WEBSOCKET_TCP_CAPABILITIES

from tests.test_runtime_connection_binding import (
    CONNECTION_ID,
    RESUMED_SESSION_ID,
    SESSION_ID,
    UTC_START,
    _context,
)
from tests.test_runtime_connection_handshake import _FakeTransportSession


SECOND_CONNECTION_ID = "connection_123e4567e89b42d3a456426614174005"
SECOND_SESSION_ID = "session_123e4567e89b42d3a456426614174006"


class LocalConnectionIndexTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.index = LocalConnectionIndex()
        self.context = _new_context()
        self.machine = await _authenticated_machine()

    async def test_add_and_all_read_only_indexes(self) -> None:
        snapshot = await self.index.add_authenticated(
            session_context=self.context,
            state_machine=self.machine,
        )

        self.assertEqual({CONNECTION_ID}, set(snapshot.by_connection_id))
        self.assertEqual(CONNECTION_ID, snapshot.by_session_id[SESSION_ID])
        self.assertEqual(frozenset({CONNECTION_ID}), snapshot.by_identity["identity:test-user"])
        self.assertEqual(frozenset({CONNECTION_ID}), snapshot.by_tenant["tenant:test"])
        self.assertEqual(frozenset({CONNECTION_ID}), snapshot.by_component_type["client"])
        self.assertEqual(
            frozenset({CONNECTION_ID}),
            snapshot.by_capability["runtime.connection"],
        )
        self.assertEqual(frozenset(), snapshot.active_target_connection_ids)
        self.assertEqual(self.context, (await self.index.lookup_session(SESSION_ID)).session_context)

    async def test_identity_explicitly_supports_multiple_connections(self) -> None:
        await self._add_primary()
        second = dataclasses.replace(
            self.context,
            connection_id=SECOND_CONNECTION_ID,
            session_id=SECOND_SESSION_ID,
        )
        await self.index.add_authenticated(
            session_context=second,
            state_machine=await _authenticated_machine(),
        )

        matches = await self.index.connections_for_identity("identity:test-user")

        self.assertEqual(2, len(matches))
        self.assertEqual(
            {CONNECTION_ID, SECOND_CONNECTION_ID},
            {item.session_context.connection_id for item in matches},
        )

    async def test_duplicate_connection_and_session_ids_are_stable(self) -> None:
        await self._add_primary()
        with self.assertRaises(NsStateError) as duplicate_connection:
            await self.index.add_authenticated(
                session_context=self.context,
                state_machine=await _authenticated_machine(),
            )
        self.assertEqual(
            "duplicate_connection_id",
            duplicate_connection.exception.details["reason"],
        )

        duplicate_session = dataclasses.replace(
            self.context,
            connection_id=SECOND_CONNECTION_ID,
        )
        with self.assertRaises(NsStateError) as duplicate:
            await self.index.add_authenticated(
                session_context=duplicate_session,
                state_machine=await _authenticated_machine(),
            )
        self.assertEqual("duplicate_session_id", duplicate.exception.details["reason"])
        self.assertEqual(1, len((await self.index.snapshot()).by_connection_id))

    async def test_concurrent_duplicate_add_has_one_owner(self) -> None:
        outcomes = await asyncio.gather(
            self.index.add_authenticated(
                session_context=self.context,
                state_machine=await _authenticated_machine(),
            ),
            self.index.add_authenticated(
                session_context=self.context,
                state_machine=await _authenticated_machine(),
            ),
            return_exceptions=True,
        )

        self.assertEqual(1, sum(not isinstance(item, BaseException) for item in outcomes))
        self.assertEqual(1, sum(isinstance(item, NsStateError) for item in outcomes))
        self.assertEqual(1, len((await self.index.snapshot()).by_connection_id))

    async def test_active_eligibility_tracks_owned_state_transitions(self) -> None:
        await self._add_primary()
        await self.index.transition(CONNECTION_ID, LogicalConnectionState.ACTIVE)
        self.assertEqual(1, len(await self.index.active_targets()))

        await self.index.transition(CONNECTION_ID, LogicalConnectionState.DRAINING)

        self.assertEqual((), await self.index.active_targets())
        entry = await self.index.lookup_connection(CONNECTION_ID)
        assert entry is not None
        self.assertIs(LogicalConnectionState.DRAINING, entry.state)
        self.assertFalse(entry.active_target_eligible)

    async def test_suspend_and_restore_active_target_are_idempotent(self) -> None:
        await self._add_primary()
        await self.index.transition(CONNECTION_ID, LogicalConnectionState.ACTIVE)

        suspended = await self.index.suspend_active_target(CONNECTION_ID)
        sequence = suspended.mutation_sequence
        again = await self.index.suspend_active_target(CONNECTION_ID)
        self.assertEqual(sequence, again.mutation_sequence)
        self.assertEqual(frozenset(), again.active_target_connection_ids)

        restored = await self.index.restore_active_target(CONNECTION_ID)
        self.assertEqual(frozenset({CONNECTION_ID}), restored.active_target_connection_ids)

    async def test_inactive_connection_cannot_be_restored_as_target(self) -> None:
        await self._add_primary()
        with self.assertRaises(NsStateError) as context:
            await self.index.restore_active_target(CONNECTION_ID)
        self.assertEqual("active_state_required", context.exception.details["reason"])

    async def test_closed_connection_is_removed_from_every_index(self) -> None:
        await self._add_primary()
        await self.index.transition(CONNECTION_ID, LogicalConnectionState.ACTIVE)
        await self.index.transition(
            CONNECTION_ID,
            LogicalConnectionState.CLOSING,
            close_reason=LogicalConnectionCloseReason.NORMAL,
        )
        await self.index.transition(CONNECTION_ID, LogicalConnectionState.CLOSED)

        snapshot = await self.index.snapshot()
        self.assertEqual({}, dict(snapshot.by_connection_id))
        self.assertEqual({}, dict(snapshot.by_session_id))
        self.assertEqual({}, dict(snapshot.by_identity))
        self.assertEqual({}, dict(snapshot.by_tenant))
        self.assertEqual({}, dict(snapshot.by_component_type))
        self.assertEqual({}, dict(snapshot.by_capability))
        self.assertEqual(frozenset(), snapshot.active_target_connection_ids)

    async def test_session_replace_atomically_removes_old_secondary_values(self) -> None:
        await self._add_primary()
        await self.index.transition(CONNECTION_ID, LogicalConnectionState.ACTIVE)
        resumed = dataclasses.replace(
            self.context,
            session_id=RESUMED_SESSION_ID,
            connection_epoch=1,
            identity="identity:resumed-user",
            tenant_id="tenant:resumed",
            component_type="node",
            capabilities=frozenset({"runtime.heartbeat"}),
        )

        snapshot = await self.index.replace_session_context(resumed)

        self.assertNotIn(SESSION_ID, snapshot.by_session_id)
        self.assertEqual(CONNECTION_ID, snapshot.by_session_id[RESUMED_SESSION_ID])
        self.assertNotIn("identity:test-user", snapshot.by_identity)
        self.assertNotIn("tenant:test", snapshot.by_tenant)
        self.assertNotIn("client", snapshot.by_component_type)
        self.assertNotIn("runtime.connection", snapshot.by_capability)
        self.assertEqual(frozenset(), snapshot.active_target_connection_ids)

    async def test_authority_replace_rebuilds_capability_index_without_identity_change(self) -> None:
        await self._add_primary()
        updated = dataclasses.replace(
            self.context,
            capabilities=frozenset({"runtime.heartbeat"}),
            permission_version="version:2",
        )

        snapshot = await self.index.replace_authority_context(updated)

        self.assertNotIn("runtime.connection", snapshot.by_capability)
        self.assertEqual(
            frozenset({CONNECTION_ID}),
            snapshot.by_capability["runtime.heartbeat"],
        )
        self.assertEqual(
            "version:2",
            snapshot.by_connection_id[CONNECTION_ID].session_context.permission_version,
        )

    async def test_snapshot_is_deeply_immutable_and_has_no_external_owner(self) -> None:
        snapshot = await self._add_primary()
        with self.assertRaises(TypeError):
            snapshot.by_session_id["session_bad"] = CONNECTION_ID  # type: ignore[index]
        with self.assertRaises((dataclasses.FrozenInstanceError, TypeError)):
            snapshot.mutation_sequence = 99  # type: ignore[misc]
        self.assertFalse(hasattr(snapshot, "state_store"))
        self.assertFalse(hasattr(snapshot, "cache_client"))

    async def _add_primary(self):
        return await self.index.add_authenticated(
            session_context=self.context,
            state_machine=self.machine,
        )


async def _authenticated_machine() -> LogicalConnectionStateMachine:
    machine = LogicalConnectionStateMachine()
    await machine.transition(LogicalConnectionState.HANDSHAKING)
    await machine.transition(LogicalConnectionState.AUTHENTICATED)
    return machine


def _new_context():
    transport = _FakeTransportSession(capabilities=WEBSOCKET_TCP_CAPABILITIES)
    return _context(
        transport,
        clock=ControlledClock(utc_start=UTC_START),
    )


if __name__ == "__main__":
    unittest.main()
