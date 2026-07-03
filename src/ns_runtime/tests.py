# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import unittest

from ns_common.exceptions import (
    NsRuntimeAuthContextForgedError,
    NsRuntimeEnvelopeSchemaError,
    NsRuntimeProtocolVersionError,
    NsRuntimeSourceForgedError,
)
from ns_runtime.processor import BuiltinProcessorRegistryFactory
from ns_runtime.protocol import EnvelopeProtocol
from ns_runtime.service import RuntimeService


class RuntimeEnvelopeProtocolTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = BuiltinProcessorRegistryFactory.build()
        self.protocol = EnvelopeProtocol(registry=self.registry)

    def _hello(self) -> dict[str, object]:
        return {
            "protocol": {
                "major": 1,
                "minor": 0,
                "patch": 0,
            },
            "message": {
                "message_id": "m-1",
                "type": "connection.hello",
                "category": "connection",
                "created_at": "2026-07-03T00:00:00Z",
            },
            "payload": {
                "mode": "inline",
                "inline": {
                    "token": "secret-token",
                    "component_type": "client",
                },
            },
        }

    def test_connection_hello_validates(self) -> None:
        envelope = self.protocol.decode_inbound_text_frame(json.dumps(self._hello()))

        self.assertEqual("connection.hello", envelope.message_type)
        self.assertEqual("m-1", envelope.message_id)

    def test_rejects_inbound_source_and_auth_context(self) -> None:
        source_forged = self._hello()
        source_forged["source"] = {
            "runtime_id": "evil",
        }

        with self.assertRaises(NsRuntimeSourceForgedError):
            self.protocol.validate_inbound(source_forged)

        auth_forged = self._hello()
        auth_forged["auth_context"] = {
            "iam_mode": "strict",
        }

        with self.assertRaises(NsRuntimeAuthContextForgedError):
            self.protocol.validate_inbound(auth_forged)

    def test_rejects_unknown_top_level_group_and_empty_group(self) -> None:
        unknown = self._hello()
        unknown["raw"] = {
            "value": 1,
        }

        with self.assertRaises(NsRuntimeEnvelopeSchemaError):
            self.protocol.validate_inbound(unknown)

        empty = self._hello()
        empty["trace"] = {}

        with self.assertRaises(NsRuntimeEnvelopeSchemaError):
            self.protocol.validate_inbound(empty)

    def test_rejects_major_version_mismatch(self) -> None:
        incompatible = self._hello()
        incompatible["protocol"] = {
            "major": 2,
            "minor": 0,
            "patch": 0,
        }

        with self.assertRaises(NsRuntimeProtocolVersionError):
            self.protocol.validate_inbound(incompatible)

    def test_builtin_registry_covers_required_type_families(self) -> None:
        required_types = {
            "connection.hello",
            "connection.heartbeat",
            "task.dispatch",
            "delivery.ack",
            "delivery.nack",
            "delivery.defer",
            "stream.start",
            "stream.chunk",
            "stream.end",
            "runtime.control.health",
            "runtime.control.config_update",
            "delivery.dead_letter",
            "delivery.replay",
            "delivery.cancel",
            "delivery.hold",
            "runtime.control.state_snapshot",
            "runtime.error",
            "cluster.event.node_joined",
        }

        for message_type in required_types:
            self.assertTrue(self.registry.contains(message_type), message_type)

            registration = self.registry.get(message_type)

            self.assertTrue(registration.processor_name.endswith("Processor"))
            self.assertTrue(registration.audit_event.startswith("runtime."))
            self.assertTrue(registration.standard_error_type)

    def test_runtime_service_self_check(self) -> None:
        snapshot = RuntimeService.bootstrap().self_check()

        self.assertGreater(snapshot.registered_message_type_count, 0)
        self.assertEqual(1, snapshot.protocol_major)


if __name__ == "__main__":
    unittest.main()
