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
        self.assertIn("delivery.accepted", message_types)
        self.assertIn("delivery.rejected", message_types)
        self.assertIn("delivery.ack", message_types)
        self.assertIn("delivery.nack", message_types)
        self.assertIn("delivery.defer", message_types)
        self.assertIn("delivery.duplicate", message_types)
        self.assertIn("stream.start", message_types)
        self.assertIn("runtime.control.health", message_types)
        self.assertIn("cluster.event.node_joined", message_types)
        self.assertIn("runtime.control.config_update", message_types)
        self.assertIn("runtime.error", message_types)
        self.assertNotIn("runtime.control.forward_result", message_types)

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

    def test_task_dispatch_with_unavailable_connection_returns_delivery_rejected(self) -> None:
        response = asyncio.run(
            self.service.process_frame(
                self._build_frame(
                    "task.dispatch",
                    category="task",
                    target={
                        "kind": "connection",
                        "connection_id": "missing-conn",
                    },
                ),
                self.session,
            )
        )

        self.assertEqual(response.action, "reject")
        self.assertIsNotNone(response.envelope)
        self.assertEqual(
            response.envelope["message"]["type"],
            "delivery.rejected",
        )
        self.assertEqual(
            response.envelope["payload"]["inline"]["reason_code"],
            "RUNTIME_TARGET_UNAVAILABLE",
        )

        inline = response.envelope["payload"]["inline"]

        self.assertEqual(inline["message_id"], "msg-1")
        self.assertEqual(inline["summary_id"], "summary:msg-1")
        self.assertEqual(
            inline["reason_code"],
            "RUNTIME_TARGET_UNAVAILABLE",
        )
        self.assertTrue(inline["retryable"])
        self.assertEqual(
            inline["status_query_hint"],
            "delivery.status_query",
        )
        self.assertNotIn("details", inline)
        self.assertNotIn("delivery", response.envelope)

        summary = self.service.get_message_summary("msg-1")

        self.assertIsNotNone(summary)
        self.assertEqual(summary.rejected_count, 1)
        self.assertEqual(summary.delivery_count, 0)
        self.assertEqual(summary.state, "failed")
        self.assertEqual(
            self.service.delivery_registry.list_records(),
            (),
        )

    def test_task_dispatch_to_runtime_target_returns_delivery_rejected(self) -> None:
        response = asyncio.run(
            self.service.process_frame(
                self._build_frame(
                    "task.dispatch",
                    category="task",
                    target={
                        "kind": "runtime",
                        "runtime_id": "runtime-test",
                    },
                ),
                self.session,
            )
        )

        self.assertEqual(response.action, "reject")
        self.assertIsNotNone(response.envelope)
        self.assertEqual(
            response.envelope["message"]["type"],
            "delivery.rejected",
        )

        inline = response.envelope["payload"]["inline"]

        self.assertEqual(
            inline["message_id"],
            "msg-1",
        )
        self.assertEqual(
            inline["summary_id"],
            "summary:msg-1",
        )
        self.assertEqual(
            inline["reason_code"],
            "RUNTIME_TARGET_UNAVAILABLE",
        )
        self.assertTrue(inline["retryable"])
        self.assertEqual(
            inline["status_query_hint"],
            "delivery.status_query",
        )

        summary = self.service.get_message_summary("msg-1")

        self.assertIsNotNone(summary)
        self.assertEqual(summary.target_count, 1)
        self.assertEqual(summary.accepted_count, 0)
        self.assertEqual(summary.rejected_count, 1)
        self.assertEqual(summary.delivery_count, 0)
        self.assertEqual(summary.pending_count, 0)
        self.assertEqual(summary.state, "failed")

    def test_delivery_ack_with_unknown_delivery_is_rejected_by_ack_processor(self) -> None:
        response = asyncio.run(
            self.service.process_frame(
                self._build_ack_frame(delivery_id="missing-delivery"),
                self.session,
            )
        )

        self.assertEqual(response.action, "reject")
        self.assertIsNotNone(response.envelope)
        self.assertEqual(response.envelope["message"]["type"], "runtime.error")
        self.assertEqual(response.envelope["payload"]["inline"]["error"]["code"], "RUNTIME_ACK_REJECTED")

    def test_delivery_nack_with_unknown_delivery_is_rejected_by_nack_processor(self) -> None:
        response = asyncio.run(
            self.service.process_frame(
                self._build_nack_frame(
                    delivery_id="missing-delivery",
                    reason="temporarily_unavailable",
                ),
                self.session,
            )
        )

        self.assertEqual(response.action, "reject")
        self.assertIsNotNone(response.envelope)
        self.assertEqual(response.envelope["message"]["type"], "runtime.error")
        self.assertEqual(response.envelope["payload"]["inline"]["error"]["code"], "RUNTIME_NACK_REJECTED")

    def test_delivery_defer_with_unknown_delivery_is_rejected_by_defer_processor(self) -> None:
        response = asyncio.run(
            self.service.process_frame(
                self._build_defer_frame(
                    delivery_id="missing-delivery",
                    defer_ms=1000,
                ),
                self.session,
            )
        )

        self.assertEqual(response.action, "reject")
        self.assertIsNotNone(response.envelope)
        self.assertEqual(response.envelope["message"]["type"], "runtime.error")
        self.assertEqual(response.envelope["payload"]["inline"]["error"]["code"], "RUNTIME_DEFER_REJECTED")

    def test_delivery_accepted_is_registered_as_best_effort_outbound_type(self) -> None:
        specs = {
            item["message_type"]: item
            for item in self.service.list_message_type_specs()
        }

        accepted_spec = specs["delivery.accepted"]

        self.assertEqual(accepted_spec["category"], "delivery")
        self.assertEqual(accepted_spec["reliability"], "best_effort")
        self.assertFalse(accepted_spec["implemented"])
        self.assertEqual(accepted_spec["required_groups"], [])

    def test_task_dispatch_with_cross_tenant_target_returns_non_retryable_delivery_rejected(self) -> None:
        response = asyncio.run(
            self.service.process_frame(
                self._build_frame(
                    "task.dispatch",
                    category="task",
                    target={
                        "kind": "connection",
                        "connection_id": "missing-conn",
                        "tenant_id": "tenant-2",
                    },
                ),
                self.session,
            )
        )

        self.assertEqual(response.action, "reject")
        self.assertIsNotNone(response.envelope)
        self.assertEqual(
            response.envelope["message"]["type"],
            "delivery.rejected",
        )

        inline = response.envelope["payload"]["inline"]

        self.assertEqual(
            inline["reason_code"],
            "RUNTIME_TENANT_MISMATCH",
        )
        self.assertFalse(inline["retryable"])

        summary = self.service.get_message_summary("msg-1")

        self.assertIsNotNone(summary)
        self.assertEqual(summary.rejected_count, 1)
        self.assertEqual(summary.state, "failed")

    def test_task_dispatch_with_unsupported_target_kind_remains_runtime_error(self) -> None:
        response = asyncio.run(
            self.service.process_frame(
                self._build_frame(
                    "task.dispatch",
                    category="task",
                    target={
                        "kind": "unsupported",
                    },
                ),
                self.session,
            )
        )

        self.assertEqual(response.action, "reject")
        self.assertIsNotNone(response.envelope)
        self.assertEqual(
            response.envelope["message"]["type"],
            "runtime.error",
        )
        self.assertEqual(
            response.envelope["payload"]["inline"]["error"]["code"],
            "RUNTIME_ENVELOPE_SCHEMA_ERROR",
        )
        self.assertIsNone(
            self.service.get_message_summary("msg-1")
        )

    def test_delivery_rejected_is_registered_as_best_effort_outbound_type(self) -> None:
        specs = {
            item["message_type"]: item
            for item in self.service.list_message_type_specs()
        }

        rejected_spec = specs["delivery.rejected"]

        self.assertEqual(
            rejected_spec["category"],
            "delivery",
        )
        self.assertEqual(
            rejected_spec["reliability"],
            "best_effort",
        )
        self.assertFalse(rejected_spec["implemented"])
        self.assertEqual(
            rejected_spec["required_groups"],
            [],
        )

    def test_delivery_duplicate_is_registered_as_best_effort_outbound_type(self) -> None:
        specs = {
            item["message_type"]: item
            for item in (
                self.service.list_message_type_specs()
            )
        }

        duplicate_spec = specs["delivery.duplicate"]

        self.assertEqual(
            duplicate_spec["category"],
            "delivery",
        )
        self.assertEqual(
            duplicate_spec["reliability"],
            "best_effort",
        )
        self.assertFalse(
            duplicate_spec["implemented"]
        )
        self.assertEqual(
            duplicate_spec["required_groups"],
            [],
        )

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

    @staticmethod
    def _build_nack_frame(*, delivery_id: str, reason: str) -> str:
        raw: dict[str, Any] = {
            "protocol": {
                "version": "1.0.0",
            },
            "message": {
                "message_id": "nack-1",
                "type": "delivery.nack",
                "category": "delivery",
                "priority": 100,
                "created_at": utc_now_iso(),
                "reliability": "critical",
            },
            "delivery": {
                "delivery_id": delivery_id,
            },
            "payload": {
                "mode": "inline",
                "inline": {
                    "reason": reason,
                },
            },
        }
        return json.dumps(raw, ensure_ascii=False)

    @staticmethod
    def _build_defer_frame(*, delivery_id: str, defer_ms: int) -> str:
        raw: dict[str, Any] = {
            "protocol": {
                "version": "1.0.0",
            },
            "message": {
                "message_id": "defer-1",
                "type": "delivery.defer",
                "category": "delivery",
                "priority": 100,
                "created_at": utc_now_iso(),
                "reliability": "critical",
            },
            "delivery": {
                "delivery_id": delivery_id,
            },
            "payload": {
                "mode": "inline",
                "inline": {
                    "defer_ms": defer_ms,
                },
            },
        }
        return json.dumps(raw, ensure_ascii=False)

    @staticmethod
    def _build_ack_frame(*, delivery_id: str) -> str:
        raw: dict[str, Any] = {
            "protocol": {
                "version": "1.0.0",
            },
            "message": {
                "message_id": "ack-1",
                "type": "delivery.ack",
                "category": "delivery",
                "priority": 100,
                "created_at": utc_now_iso(),
                "reliability": "critical",
            },
            "delivery": {
                "delivery_id": delivery_id,
            },
        }
        return json.dumps(raw, ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()
