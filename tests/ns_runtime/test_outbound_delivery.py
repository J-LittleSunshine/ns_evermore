# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import unittest
from typing import (
    TYPE_CHECKING
)

from ns_runtime.auth import RuntimeAuthResult
from ns_runtime.delivery import RuntimeDeliveryRegistry
from ns_runtime.models import (
    RuntimeSessionContext,
    utc_now_iso
)
from ns_runtime.outbound import (
    RuntimeConnectionWriterRegistry,
    RuntimeLocalEnvelopeForwarder
)
from ns_runtime.protocol import EnvelopeCodec
from ns_runtime.routing import RuntimeTargetResolver
from ns_runtime.session import RuntimeSessionRegistry

if TYPE_CHECKING:
    pass


class FakeWebSocket:
    def __init__(self) -> None:
        self.frames: list[str] = []

    async def send(self, frame: str) -> None:
        self.frames.append(frame)


class RuntimeOutboundDeliveryTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_forwarder_creates_delivery_metadata_and_sends_delivery_group(self) -> None:
        runtime_id = "runtime-test"
        codec = EnvelopeCodec(runtime_id=runtime_id)
        session_registry = RuntimeSessionRegistry(runtime_id=runtime_id)
        writer_registry = RuntimeConnectionWriterRegistry()
        delivery_registry = RuntimeDeliveryRegistry(default_ack_timeout_ms=1000)
        forwarder = RuntimeLocalEnvelopeForwarder(
            writer_registry=writer_registry,
            delivery_registry=delivery_registry,
        )
        target_resolver = RuntimeTargetResolver(
            runtime_id=runtime_id,
            session_registry=session_registry,
        )

        source_session = self._activate(
            session_registry,
            identity="source-1",
            tenant_id="tenant-1",
            component_type="management",
            capabilities=("task.dispatch",),
        )
        target_session = self._activate(
            session_registry,
            identity="target-1",
            tenant_id="tenant-1",
            component_type="client",
            capabilities=("task.execute",),
        )
        websocket = FakeWebSocket()
        writer_registry.register(
            connection_id=target_session.connection_id,
            connection_epoch=target_session.connection_epoch,
            websocket=websocket,
        )

        envelope = codec.parse_inbound(
            self._build_task_dispatch_frame(
                target_connection_id=target_session.connection_id,
            ),
            source_session,
        )
        decision = target_resolver.resolve(envelope, source_session)
        self.assertIsNotNone(decision)

        results = await forwarder.forward(
            decision=decision,
            envelope=envelope,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, "sent_to_transport")
        self.assertEqual(results[0].delivery_state, "ack_waiting")
        self.assertTrue(results[0].delivery_id)
        self.assertTrue(results[0].attempt_id)

        self.assertEqual(len(websocket.frames), 1)
        forwarded = json.loads(websocket.frames[0])
        self.assertEqual(forwarded["delivery"]["delivery_id"], results[0].delivery_id)
        self.assertEqual(forwarded["delivery"]["attempt"], 1)
        self.assertEqual(delivery_registry.build_delivery_snapshot()["by_state"]["ack_waiting"], 1)

    @staticmethod
    def _activate(
            registry: RuntimeSessionRegistry,
            *,
            identity: str,
            tenant_id: str,
            component_type: str,
            capabilities: tuple[str, ...],
    ) -> RuntimeSessionContext:
        record = registry.create_handshaking(remote_address="test")
        return registry.activate(
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
        return json.dumps(
            {
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
            },
            ensure_ascii=False,
        )


if __name__ == "__main__":
    unittest.main()
