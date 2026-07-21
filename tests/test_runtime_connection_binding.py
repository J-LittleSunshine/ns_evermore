# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import dataclasses
import unittest
from datetime import datetime, timedelta, timezone
from uuid import UUID

from ns_common.exceptions import NsStateError
from ns_common.identifiers import IdentifierFactory
from ns_common.time import ControlledClock
from ns_runtime.connection import (
    HandshakeSessionNegotiator,
    LogicalConnectionState,
    LogicalConnectionTransportMap,
    LogicalSessionIdentity,
    LogicalSessionIdentityFactory,
    NetworkPathBinding,
    SessionContext,
    TransportSessionBinding,
)
from ns_runtime.transport import (
    TransportCapabilities,
    TransportCapability,
    TransportIdentity,
    TransportPathSnapshot,
    TransportSession,
    WEBSOCKET_TCP_CAPABILITIES,
)

from tests.test_runtime_connection_session import _authority, _claims
from tests.test_runtime_connection_handshake import _FakeTransportSession


UTC_START = datetime(2026, 7, 21, tzinfo=timezone.utc)
CONNECTION_ID = "connection_123e4567e89b42d3a456426614174000"
SESSION_ID = "session_123e4567e89b42d3a456426614174001"
RESUMED_SESSION_ID = "session_123e4567e89b42d3a456426614174002"


class LogicalTransportMappingTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.clock = ControlledClock(utc_start=UTC_START)
        self.transport = _FakeTransportSession(
            capabilities=WEBSOCKET_TCP_CAPABILITIES,
        )
        self.context = _context(self.transport, clock=self.clock)
        self.mapping = LogicalConnectionTransportMap(
            session_context=self.context,
            transport_session=self.transport,
        )

    async def test_snapshot_keeps_three_identity_layers_distinct(self) -> None:
        snapshot = await self.mapping.snapshot()
        binding = snapshot.transport
        assert binding is not None

        self.assertEqual(CONNECTION_ID, snapshot.session_context.connection_id)
        self.assertEqual(SESSION_ID, snapshot.session_context.session_id)
        self.assertNotEqual(CONNECTION_ID, binding.transport_connection_id)
        self.assertNotEqual(SESSION_ID, binding.transport_session_id)
        self.assertNotEqual(binding.transport_session_id, binding.path.path_id)
        self.assertIsInstance(binding.path, NetworkPathBinding)
        self.assertIsInstance(binding, TransportSessionBinding)
        self.assertFalse(any(
            isinstance(getattr(binding, field.name), TransportSession)
            for field in dataclasses.fields(binding)
        ))

    async def test_path_update_does_not_increment_logical_epoch(self) -> None:
        self.transport._capabilities = TransportCapabilities(frozenset({
            TransportCapability.RELIABLE_ORDERED_MESSAGES,
            TransportCapability.CONNECTION_PATH_MIGRATION,
        }))
        self.mapping = LogicalConnectionTransportMap(
            session_context=self.context,
            transport_session=self.transport,
        )
        original = self.transport.identity
        self.transport._identity = TransportIdentity(
            transport_connection_id=original.transport_connection_id,
            transport_session_id=original.transport_session_id,
            transport_stream_id=original.transport_stream_id,
            path=_path(suffix="11", path_epoch=1, migration_count=1),
        )

        snapshot = await self.mapping.update_network_path(self.transport)

        assert snapshot.transport is not None
        self.assertEqual(0, snapshot.session_context.connection_epoch)
        self.assertEqual(SESSION_ID, snapshot.session_context.session_id)
        self.assertEqual(1, snapshot.transport.path.path_epoch)
        self.assertEqual(1, snapshot.binding_sequence)

    async def test_path_change_requires_adapter_capability(self) -> None:
        original = self.transport.identity
        self.transport._identity = TransportIdentity(
            transport_connection_id=original.transport_connection_id,
            transport_session_id=original.transport_session_id,
            transport_stream_id=original.transport_stream_id,
            path=_path(suffix="12", path_epoch=1, migration_count=1),
        )

        with self.assertRaises(NsStateError) as context:
            await self.mapping.update_network_path(self.transport)

        self.assertEqual("path_migration_not_supported", context.exception.details["reason"])
        self.assertEqual(0, (await self.mapping.snapshot()).binding_sequence)

    async def test_path_update_cannot_replace_transport_session(self) -> None:
        replacement = _transport(suffix="20")

        with self.assertRaises(NsStateError) as context:
            await self.mapping.update_network_path(replacement)

        self.assertEqual(
            "path_update_changed_transport_identity",
            context.exception.details["reason"],
        )

    async def test_transport_replacement_is_explicit_and_advances_logical_view(self) -> None:
        replacement = _transport(suffix="30")
        resumed = dataclasses.replace(
            self.context,
            session_id=RESUMED_SESSION_ID,
            connection_epoch=1,
        )

        snapshot = await self.mapping.replace_transport_session(
            session_context=resumed,
            transport_session=replacement,
        )

        assert snapshot.transport is not None
        self.assertEqual(CONNECTION_ID, snapshot.session_context.connection_id)
        self.assertEqual(RESUMED_SESSION_ID, snapshot.session_context.session_id)
        self.assertEqual(1, snapshot.session_context.connection_epoch)
        self.assertEqual(replacement.identity.transport_session_id, snapshot.transport.transport_session_id)
        self.assertEqual(1, snapshot.binding_sequence)

    async def test_replacement_rejects_logical_connection_change_or_epoch_skip(self) -> None:
        replacement = _transport(suffix="31")
        changed_connection = dataclasses.replace(
            self.context,
            connection_id="connection_123e4567e89b42d3a456426614174003",
            session_id=RESUMED_SESSION_ID,
            connection_epoch=1,
        )
        with self.assertRaises(NsStateError) as changed:
            await self.mapping.replace_transport_session(
                session_context=changed_connection,
                transport_session=replacement,
            )
        self.assertEqual("logical_connection_changed", changed.exception.details["reason"])

        skipped = dataclasses.replace(
            self.context,
            session_id=RESUMED_SESSION_ID,
            connection_epoch=2,
        )
        with self.assertRaises(NsStateError) as epoch:
            await self.mapping.replace_transport_session(
                session_context=skipped,
                transport_session=replacement,
            )
        self.assertEqual("connection_epoch_not_next", epoch.exception.details["reason"])

    async def test_detach_is_owned_and_leaves_no_path_binding(self) -> None:
        session_id = self.transport.identity.transport_session_id
        snapshot = await self.mapping.detach_transport_session(
            transport_session_id=session_id,
        )
        self.assertIsNone(snapshot.transport)
        self.assertEqual(1, snapshot.binding_sequence)

        with self.assertRaises(NsStateError):
            await self.mapping.update_network_path(self.transport)
        with self.assertRaises(NsStateError):
            await self.mapping.detach_transport_session(
                transport_session_id=session_id,
            )

    async def test_concurrent_replacements_allow_only_one_next_epoch(self) -> None:
        context_a = dataclasses.replace(
            self.context,
            session_id=RESUMED_SESSION_ID,
            connection_epoch=1,
        )
        context_b = dataclasses.replace(
            self.context,
            session_id="session_123e4567e89b42d3a456426614174004",
            connection_epoch=1,
        )
        outcomes = await asyncio.gather(
            self.mapping.replace_transport_session(
                session_context=context_a,
                transport_session=_transport(suffix="40"),
            ),
            self.mapping.replace_transport_session(
                session_context=context_b,
                transport_session=_transport(suffix="50"),
            ),
            return_exceptions=True,
        )

        self.assertEqual(1, sum(not isinstance(item, BaseException) for item in outcomes))
        self.assertEqual(1, sum(isinstance(item, NsStateError) for item in outcomes))
        self.assertEqual(1, (await self.mapping.snapshot()).session_context.connection_epoch)

    async def test_peer_digest_never_becomes_identity_or_authority(self) -> None:
        snapshot = await self.mapping.snapshot()
        assert snapshot.transport is not None
        self.assertTrue(snapshot.transport.path.peer_summary.startswith("sha256:"))
        self.assertEqual("identity:test-user", snapshot.session_context.identity)
        self.assertEqual("tenant:test", snapshot.session_context.tenant_id)
        self.assertNotEqual(
            snapshot.transport.path.peer_summary,
            snapshot.session_context.identity,
        )

    def test_logical_factory_uses_p01_ids_and_resume_keeps_connection(self) -> None:
        values = iter((
            UUID("123e4567-e89b-42d3-a456-426614174010"),
            UUID("123e4567-e89b-42d3-a456-426614174011"),
            UUID("123e4567-e89b-42d3-a456-426614174012"),
        ))
        factory = LogicalSessionIdentityFactory(
            IdentifierFactory(uuid_factory=lambda: next(values)),
        )

        created = factory.create()
        resumed = factory.resume(created)

        self.assertTrue(created.connection_id.startswith("connection_"))
        self.assertTrue(created.session_id.startswith("session_"))
        self.assertEqual(created.connection_id, resumed.connection_id)
        self.assertNotEqual(created.session_id, resumed.session_id)
        self.assertEqual(0, created.connection_epoch)
        self.assertEqual(1, resumed.connection_epoch)


def _context(
    transport: TransportSession,
    *,
    clock: ControlledClock,
) -> SessionContext:
    result = HandshakeSessionNegotiator(
        transport_session=transport,
        logical_identity=LogicalSessionIdentity(
            connection_id=CONNECTION_ID,
            session_id=SESSION_ID,
            connection_epoch=0,
        ),
        clock=clock,
    ).negotiate(claims=_claims(), authority=_authority())
    self_context = result.context
    assert self_context.established_state is LogicalConnectionState.AUTHENTICATED
    return self_context


def _transport(*, suffix: str) -> _FakeTransportSession:
    transport = _FakeTransportSession(capabilities=WEBSOCKET_TCP_CAPABILITIES)
    transport._identity = TransportIdentity(
        transport_connection_id=f"transport_connection_{suffix.zfill(32)}",
        transport_session_id=f"transport_session_{(suffix + '1').zfill(32)}",
        transport_stream_id=f"transport_stream_{(suffix + '2').zfill(32)}",
        path=_path(suffix=suffix + "3"),
    )
    return transport


def _path(
    *,
    suffix: str,
    path_epoch: int = 0,
    migration_count: int = 0,
) -> TransportPathSnapshot:
    return TransportPathSnapshot(
        path_id=f"transport_path_{suffix.zfill(32)}",
        path_epoch=path_epoch,
        local_summary="sha256:1111111111111111",
        peer_summary="sha256:2222222222222222",
        validated_at=UTC_START + timedelta(seconds=path_epoch),
        migration_count=migration_count,
    )


if __name__ == "__main__":
    unittest.main()
