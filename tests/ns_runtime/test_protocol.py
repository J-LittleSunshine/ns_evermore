# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import unittest
from typing import (
    Any,
    TYPE_CHECKING
)

from ns_common.exceptions import (
    NsRuntimeAuthContextForgedError,
    NsRuntimeEnvelopeSchemaError,
    NsRuntimeSourceForgedError,
)
from ns_runtime.models import (
    RuntimeSessionContext,
    utc_now_iso
)
from ns_runtime.protocol import EnvelopeCodec

if TYPE_CHECKING:
    pass


class RuntimeProtocolTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.codec = EnvelopeCodec(runtime_id="runtime-test")
        self.session = RuntimeSessionContext(
            runtime_id="runtime-test",
            connection_id="conn-1",
            session_id="sess-1",
            identity="user-1",
            tenant_id="tenant-1",
            component_type="client",
            capabilities=("runtime.management",),
            auth_snapshot_id="auth-1",
            auth_issued_at=utc_now_iso(),
            auth_expires_at=utc_now_iso(),
        )

    def test_parse_inbound_injects_source_and_auth_context(self) -> None:
        frame = self._build_frame("connection.heartbeat")
        envelope = self.codec.parse_inbound(frame, self.session)

        self.assertEqual(envelope.raw["source"]["connection_id"], "conn-1")
        self.assertEqual(envelope.raw["auth_context"]["tenant_id"], "tenant-1")
        self.assertEqual(envelope.message_type, "connection.heartbeat")

    def test_inbound_source_is_rejected(self) -> None:
        raw = self._build_raw("connection.heartbeat")
        raw["source"] = {"identity": "forged"}

        with self.assertRaises(NsRuntimeSourceForgedError):
            self.codec.parse_inbound(json.dumps(raw), self.session)

    def test_inbound_auth_context_is_rejected(self) -> None:
        raw = self._build_raw("connection.heartbeat")
        raw["auth_context"] = {"snapshot_id": "forged"}

        with self.assertRaises(NsRuntimeAuthContextForgedError):
            self.codec.parse_inbound(json.dumps(raw), self.session)

    def test_unknown_top_level_group_is_rejected(self) -> None:
        raw = self._build_raw("connection.heartbeat")
        raw["private_command"] = {"unsafe": True}

        with self.assertRaises(NsRuntimeEnvelopeSchemaError):
            self.codec.parse_inbound(json.dumps(raw), self.session)

    def test_unregistered_extension_namespace_is_rejected_by_default(self) -> None:
        raw = self._build_raw("connection.heartbeat")
        raw["extensions"] = {
            "demo": {
                "enabled": True,
            },
        }

        with self.assertRaises(NsRuntimeEnvelopeSchemaError):
            self.codec.parse_inbound(json.dumps(raw), self.session)

    def test_delivery_must_not_repeat_message_id(self) -> None:
        raw = self._build_raw("delivery.ack")
        raw["delivery"] = {
            "delivery_id": "delivery-1",
            "message_id": "duplicated",
        }

        with self.assertRaises(NsRuntimeEnvelopeSchemaError):
            self.codec.parse_inbound(json.dumps(raw), self.session)

    def _build_frame(self, message_type: str) -> str:
        return json.dumps(self._build_raw(message_type), ensure_ascii=False)

    @staticmethod
    def _build_raw(message_type: str) -> dict[str, Any]:
        return {
            "protocol": {
                "version": "1.0.0",
            },
            "message": {
                "message_id": "msg-1",
                "type": message_type,
                "category": "control",
                "priority": 100,
                "created_at": utc_now_iso(),
                "reliability": "best_effort",
            },
        }


if __name__ == "__main__":
    unittest.main()
