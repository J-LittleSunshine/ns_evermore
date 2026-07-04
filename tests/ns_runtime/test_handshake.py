# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import unittest
from typing import (
    Any,
    TYPE_CHECKING
)

from ns_runtime.auth import LocalTokenRuntimeAuthenticator
from ns_runtime.handshake import RuntimeHandshakeService
from ns_runtime.models import utc_now_iso
from ns_runtime.protocol import EnvelopeCodec
from ns_runtime.session import RuntimeSessionRegistry

if TYPE_CHECKING:
    pass


class RuntimeHandshakeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime_id = "runtime-test"
        self.codec = EnvelopeCodec(runtime_id=self.runtime_id)
        self.session_registry = RuntimeSessionRegistry(runtime_id=self.runtime_id)
        self.authenticator = LocalTokenRuntimeAuthenticator(expected_token="secret")
        self.handshake_service = RuntimeHandshakeService(
            runtime_id=self.runtime_id,
            codec=self.codec,
            authenticator=self.authenticator,
            session_registry=self.session_registry,
        )

    def test_connection_hello_accepts_valid_local_token(self) -> None:
        record = self.session_registry.create_handshaking(remote_address="test")
        outcome = asyncio.run(
            self.handshake_service.accept(
                frame_text=self._build_hello_frame(token="secret"),
                record=record,
                remote_address="test",
            )
        )

        self.assertTrue(outcome.accepted)
        self.assertIsNotNone(outcome.session)
        self.assertEqual(outcome.envelope["message"]["type"], "connection.accepted")
        self.assertEqual(outcome.envelope["payload"]["inline"]["connection_id"], record.connection_id)
        self.assertNotIn("tenant_id", outcome.envelope["payload"]["inline"])
        self.assertNotIn("identity", outcome.envelope["payload"]["inline"])
        self.assertEqual(record.state, "active")

    def test_connection_hello_rejects_invalid_token(self) -> None:
        record = self.session_registry.create_handshaking(remote_address="test")
        outcome = asyncio.run(
            self.handshake_service.accept(
                frame_text=self._build_hello_frame(token="bad-token"),
                record=record,
                remote_address="test",
            )
        )

        self.assertFalse(outcome.accepted)
        self.assertIsNone(outcome.session)
        self.assertEqual(outcome.envelope["message"]["type"], "connection.rejected")
        self.assertEqual(outcome.envelope["payload"]["inline"]["code"], "RUNTIME_AUTH_FAILED")
        self.assertEqual(record.state, "auth_failed")

    def test_first_frame_must_be_connection_hello(self) -> None:
        record = self.session_registry.create_handshaking(remote_address="test")
        outcome = asyncio.run(
            self.handshake_service.accept(
                frame_text=self._build_non_hello_frame(),
                record=record,
                remote_address="test",
            )
        )

        self.assertFalse(outcome.accepted)
        self.assertIsNone(outcome.session)
        self.assertEqual(outcome.envelope["message"]["type"], "connection.rejected")
        self.assertEqual(outcome.envelope["payload"]["inline"]["code"], "RUNTIME_ENVELOPE_SCHEMA_ERROR")
        self.assertEqual(record.state, "protocol_failed")

    def _build_hello_frame(self, *, token: str) -> str:
        raw: dict[str, Any] = {
            "protocol": {
                "version": "1.0.0",
            },
            "message": {
                "message_id": "hello-1",
                "type": "connection.hello",
                "category": "connection",
                "priority": 100,
                "created_at": utc_now_iso(),
                "reliability": "best_effort",
            },
            "payload": {
                "mode": "inline",
                "inline": {
                    "token": token,
                    "component_type": "management",
                    "requested_capabilities": [
                        "runtime.management",
                        "task.dispatch",
                    ],
                },
            },
        }
        return json.dumps(raw, ensure_ascii=False)

    @staticmethod
    def _build_non_hello_frame() -> str:
        raw: dict[str, Any] = {
            "protocol": {
                "version": "1.0.0",
            },
            "message": {
                "message_id": "heartbeat-1",
                "type": "connection.heartbeat",
                "category": "control",
                "priority": 100,
                "created_at": utc_now_iso(),
                "reliability": "best_effort",
            },
        }
        return json.dumps(raw, ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()
