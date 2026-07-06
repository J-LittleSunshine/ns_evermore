# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import unittest
from typing import (
    Any,
    TYPE_CHECKING
)

from ns_runtime.auth import RuntimeAuthResult
from ns_runtime.delivery import RuntimeDeliveryRegistry
from ns_runtime.models import (
    RuntimeSessionContext,
    utc_now_iso
)
from ns_runtime.outbound import RuntimeLocalWriteResult
from ns_runtime.protocol import EnvelopeCodec
from ns_runtime.routing import RuntimeTargetResolver
from ns_runtime.session import RuntimeSessionRegistry

if TYPE_CHECKING:
    pass


class RuntimeDeliveryRegistryTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime_id = "runtime-test"
        self.codec = EnvelopeCodec(runtime_id=self.runtime_id)
        self.session_registry = RuntimeSessionRegistry(runtime_id=self.runtime_id)
        self.target_resolver = RuntimeTargetResolver(
            runtime_id=self.runtime_id,
            session_registry=self.session_registry,
        )
        self.delivery_registry = RuntimeDeliveryRegistry(default_ack_timeout_ms=1000)
        self.source_session = self._activate(
            identity="source-1",
            tenant_id="tenant-1",
            component_type="management",
            capabilities=("task.dispatch",),
        )
        self.target_session = self._activate(
            identity="target-1",
            tenant_id="tenant-1",
            component_type="client",
            capabilities=("task.execute",),
        )

    def test_delivery_record_moves_to_ack_waiting_after_transport_send(self) -> None:
        envelope = self.codec.parse_inbound(
            self._build_task_dispatch_frame(
                target_connection_id=self.target_session.connection_id,
            ),
            self.source_session,
        )
        decision = self.target_resolver.resolve(envelope, self.source_session)
        self.assertIsNotNone(decision)

        record = self.delivery_registry.create_prepared_record(
            decision=decision,
            envelope=envelope,
            target=decision.targets[0],
        )
        self.assertEqual(record.state, "prepared")

        attempt = self.delivery_registry.start_sending(record=record)
        self.assertEqual(record.state, "sending")
        self.assertEqual(attempt.write_status, "sending")

        forwarded = self.delivery_registry.inject_delivery_group(
            envelope=envelope,
            record=record,
            attempt=attempt,
        )
        self.assertEqual(forwarded["delivery"]["delivery_id"], record.delivery_id)
        self.assertEqual(forwarded["delivery"]["attempt"], 1)

        self.delivery_registry.mark_sent_to_transport(
            record=record,
            attempt=attempt,
            write_result=RuntimeLocalWriteResult(
                connection_id=self.target_session.connection_id,
                connection_epoch=0,
                status="sent",
            ),
        )

        self.assertEqual(record.state, "ack_waiting")
        self.assertEqual(attempt.write_status, "sent_to_transport")
        self.assertTrue(record.ack_deadline_at)
        self.assertEqual(self.delivery_registry.list_attempts_for_delivery(record.delivery_id), (attempt,))
        self.assertEqual(self.delivery_registry.build_delivery_snapshot()["by_state"]["ack_waiting"], 1)

    def _activate(self, *, identity: str, tenant_id: str, component_type: str, capabilities: tuple[str, ...]) -> RuntimeSessionContext:
        record = self.session_registry.create_handshaking(remote_address="test")
        return self.session_registry.activate(
            record,
            RuntimeAuthResult(
                accepted=True,
                identity=identity,
                tenant_id=tenant_id,
                component_type=component_type,  # type: ignore[arg-type]
                capabilities=capabilities,
                snapshot_id=f"snapshot:{identity}",
                issued_at=utc_now_iso(),
                expires_at=utc_now_iso(),
                iam_mode="cached",
                role="singleton",
            ),
        )

    @staticmethod
    def _build_task_dispatch_frame(*, target_connection_id: str) -> str:
        raw: dict[str, Any] = {
            "protocol": {
                "version": "1.0.0",
            },
            "message": {
                "message_id": "msg-1",
                "type": "task.dispatch",
                "category": "task",
                "priority": 100,
                "created_at": utc_now_iso(),
                "reliability": "critical",
            },
            "target": {
                "kind": "connection",
                "connection_id": target_connection_id,
            },
            "payload": {
                "mode": "inline",
                "inline": {
                    "task_name": "demo-task",
                },
            },
        }
        return json.dumps(raw, ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()
