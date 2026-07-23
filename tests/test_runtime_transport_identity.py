# -*- coding: utf-8 -*-
from __future__ import annotations

import unittest
from datetime import datetime, timezone
from uuid import UUID

from ns_common.exceptions import NsStateError
from ns_runtime.transport import TransportIdentityFactory


class _HostileAddress:
    def __repr__(self) -> str:
        raise AssertionError("address repr must not be called")

    def __str__(self) -> str:
        raise AssertionError("address str must not be called")


class TransportIdentityTestCase(unittest.TestCase):
    def test_factory_separates_transport_ids_and_only_exposes_digests(self) -> None:
        values = iter(
            UUID(f"00000000-0000-4000-8000-{index:012x}")
            for index in range(1, 5)
        )
        factory = TransportIdentityFactory(uuid_factory=lambda: next(values))
        identity = factory.create(
            local_address=("127.0.0.1", 8765),
            peer_address=("203.0.113.42", 54321),
            validated_at=datetime.now(timezone.utc),
        )

        self.assertTrue(identity.transport_connection_id.startswith("transport_connection_"))
        self.assertTrue(identity.transport_session_id.startswith("transport_session_"))
        self.assertTrue(identity.transport_stream_id.startswith("transport_stream_"))
        self.assertTrue(identity.path.path_id.startswith("transport_path_"))
        self.assertEqual(0, identity.path.path_epoch)
        self.assertEqual(0, identity.path.migration_count)
        self.assertNotIn("203.0.113.42", repr(identity))
        self.assertNotIn("54321", repr(identity))

        summary = identity.diagnostic_summary(
            transport_type="websocket_tcp",
            tls=True,
        )
        self.assertTrue(summary.peer_summary.startswith("sha256:"))
        self.assertTrue(summary.transport_connection_summary.startswith("sha256:"))
        self.assertNotIn(identity.transport_connection_id, repr(summary))
        self.assertNotIn("203.0.113.42", repr(summary))

    def test_address_digest_does_not_call_unknown_object_repr_or_str(self) -> None:
        identity = TransportIdentityFactory().create(
            local_address=None,
            peer_address=_HostileAddress(),
            validated_at=datetime.now(timezone.utc),
        )
        self.assertRegex(identity.path.peer_summary, r"sha256:[0-9a-f]{16}")

    def test_invalid_uuid_factory_fails_without_value_disclosure(self) -> None:
        factory = TransportIdentityFactory(
            uuid_factory=lambda: UUID("00000000-0000-1000-8000-000000000001"),
        )
        with self.assertRaises(NsStateError) as raised:
            factory.create(
                local_address=None,
                peer_address=None,
                validated_at=datetime.now(timezone.utc),
            )
        self.assertNotIn("00000000", repr(raised.exception.details))

