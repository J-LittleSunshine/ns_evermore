# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import unittest
from typing import (
    Any,
    TYPE_CHECKING
)

from ns_runtime.models import (
    RuntimeSessionContext,
    utc_now_iso
)
from ns_runtime.service import RuntimeService

if TYPE_CHECKING:
    pass


class RuntimeProcessorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.service = RuntimeService.build_default(runtime_id="runtime-test")
        self.session = RuntimeSessionContext(
            runtime_id="runtime-test",
            connection_id="conn-1",
            session_id="sess-1",
            identity="manager-1",
            tenant_id="tenant-1",
            component_type="management",
            capabilities=("runtime.management", "task.dispatch"),
            auth_snapshot_id="auth-1",
            auth_issued_at=utc_now_iso(),
            auth_expires_at=utc_now_iso(),
        )

    def test_builtin_message_type_registry_contains_required_families(self) -> None:
        message_types = {item["message_type"] for item in self.service.list_message_type_specs()}

        self.assertIn("connection.heartbeat", message_types)
        self.assertIn("task.dispatch", message_types)
        self.assertIn("delivery.ack", message_types)
        self.assertIn("delivery.nack", message_types)
        self.assertIn("delivery.defer", message_types)
        self.assertIn("stream.start", message_types)
        self.assertIn("runtime.control.health", message_types)
        self.assertIn("cluster.event.node_joined", message_types)
        self.assertIn("runtime.control.config_update", message_types)
        self.assertIn("runtime.error", message_types)

    def test_connection_heartbeat_returns_heartbeat_ack(self) -> None:
        response = asyncio.run(
            self.service.process_frame(
                self._build_frame("connection.heartbeat", category="control"),
                self.session,
            )
        )

        self.assertEqual(response.action, "respond")
        self.assertIsNotNone(response.envelope)
        self.assertEqual(response.envelope["message"]["type"], "connection.heartbeat_ack")

    def test_task_dispatch_without_target_is_rejected_by_type_schema(self) -> None:
        response = asyncio.run(
            self.service.process_frame(
                self._build_frame("task.dispatch", category="task"),
                self.session,
            )
        )

        self.assertEqual(response.action, "reject")
        self.assertIsNotNone(response.envelope)
        self.assertEqual(response.envelope["message"]["type"], "runtime.error")
        self.assertEqual(response.envelope["payload"]["inline"]["error"]["code"], "RUNTIME_ENVELOPE_SCHEMA_ERROR")

    def test_task_dispatch_with_wrong_category_is_rejected_by_type_schema(self) -> None:
        response = asyncio.run(
            self.service.process_frame(
                self._build_frame("task.dispatch", category="control", target={"kind": "runtime", "runtime_id": "runtime-test"}),
                self.session,
            )
        )

        self.assertEqual(response.action, "reject")
        self.assertIsNotNone(response.envelope)
        self.assertEqual(response.envelope["message"]["type"], "runtime.error")
        self.assertEqual(response.envelope["payload"]["inline"]["error"]["code"], "RUNTIME_ENVELOPE_SCHEMA_ERROR")

    def test_task_dispatch_with_unavailable_connection_target_is_rejected_by_target_lookup(self) -> None:
        response = asyncio.run(
            self.service.process_frame(
                self._build_frame("task.dispatch", category="task", target={"kind": "connection", "connection_id": "missing-conn"}),
                self.session,
            )
        )

        self.assertEqual(response.action, "reject")
        self.assertIsNotNone(response.envelope)
        self.assertEqual(response.envelope["message"]["type"], "runtime.error")
        self.assertEqual(response.envelope["payload"]["inline"]["error"]["code"], "RUNTIME_TARGET_UNAVAILABLE")

    def test_registered_only_type_returns_standard_error_after_target_lookup_passed(self) -> None:
        response = asyncio.run(
            self.service.process_frame(
                self._build_frame("task.dispatch", category="task", target={"kind": "runtime", "runtime_id": "runtime-test"}),
                self.session,
            )
        )

        self.assertEqual(response.action, "respond")
        self.assertIsNotNone(response.envelope)
        self.assertEqual(response.envelope["message"]["type"], "runtime.error")
        self.assertEqual(response.envelope["payload"]["inline"]["error"]["code"], "RUNTIME_ENVELOPE_SCHEMA_ERROR")

    def _build_frame(self, message_type: str, *, category: str, target: dict[str, Any] | None = None) -> str:
        raw: dict[str, Any] = {
            "protocol": {
                "version": "1.0.0",
            },
            "message": {
                "message_id": "msg-1",
                "type": message_type,
                "category": category,
                "priority": 100,
                "created_at": utc_now_iso(),
                "reliability": "best_effort",
            },
        }

        if target is not None:
            raw["target"] = target

        return json.dumps(raw, ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()
