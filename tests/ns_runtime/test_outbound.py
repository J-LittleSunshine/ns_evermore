# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import unittest
from datetime import (
    datetime,
    timedelta,
    timezone
)
from typing import (
    Any,
    TYPE_CHECKING
)

from ns_common.exceptions import NsRuntimeTargetUnavailableError
from ns_runtime import (
    EnvelopeCodec,
    RuntimeDeliveryRegistry,
    RuntimeRouteDecision,
    RuntimeRouteTarget
)
from ns_runtime.models import (
    RuntimeSessionContext,
    utc_now_iso
)
from ns_runtime.outbound import (
    RuntimeConnectionWriterRegistry,
    RuntimeLocalEnvelopeForwarder
)

if TYPE_CHECKING:
    pass


class _MemoryWebSocket:
    def __init__(self) -> None:
        self.sent: list[str] = []

    async def send(self, value: str) -> None:
        self.sent.append(value)


class FakeWebSocket:
    def __init__(self) -> None:
        self.frames: list[str] = []

    async def send(self, frame: str) -> None:
        self.frames.append(frame)


class RuntimeConnectionWriterRegistryTestCase(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.target = RuntimeRouteTarget(
            kind="connection",
            runtime_id="runtime-test",
            connection_id="target-1",
            session_id="target-session-1",
            connection_epoch=0,
            identity="target-identity",
            tenant_id="tenant-1",
            component_type="client",
            capabilities=("task.execute",),
            role="singleton",
        )
        self.decision = RuntimeRouteDecision(
            source_connection_id="source-1",
            source_tenant_id="tenant-1",
            message_id="msg-1",
            message_type="task.dispatch",
            target_kind="connection",
            strategy="single",
            local_only=True,
            targets=(self.target,),
        )
        self.session = RuntimeSessionContext(
            runtime_id="runtime-test",
            connection_id="source-1",
            session_id="session-1",
            identity="source-identity",
            tenant_id="tenant-1",
            component_type="management",
            capabilities=("task.dispatch",),
            auth_snapshot_id="snapshot-1",
            auth_issued_at=utc_now_iso(),
            auth_expires_at=utc_now_iso(),
            connection_epoch=0,
            role="singleton",
            iam_mode="cached",
        )
        self.codec = EnvelopeCodec(runtime_id="runtime-test")
        self.envelope = self.codec.parse_inbound(
            self._build_task_dispatch_frame(),
            self.session,
        )

    async def test_send_to_registered_writer(self) -> None:
        registry = RuntimeConnectionWriterRegistry()
        websocket = FakeWebSocket()
        registry.register(
            connection_id="conn-1",
            connection_epoch=0,
            websocket=websocket,
        )

        result = await registry.send_to_connection(
            connection_id="conn-1",
            connection_epoch=0,
            envelope={
                "message": {
                    "message_id": "msg-1",
                    "type": "task.dispatch",
                },
            },
        )

        self.assertEqual(result.status, "sent")
        self.assertEqual(result.connection_id, "conn-1")
        self.assertEqual(len(websocket.frames), 1)
        self.assertEqual(json.loads(websocket.frames[0])["message"]["message_id"], "msg-1")

    async def test_missing_writer_raises_target_unavailable(self) -> None:
        registry = RuntimeConnectionWriterRegistry()

        with self.assertRaises(NsRuntimeTargetUnavailableError):
            await registry.send_to_connection(
                connection_id="missing",
                connection_epoch=0,
                envelope={
                    "message": {
                        "message_id": "msg-1",
                    },
                },
            )

    async def test_stale_epoch_raises_target_unavailable(self) -> None:
        registry = RuntimeConnectionWriterRegistry()
        websocket = FakeWebSocket()
        registry.register(
            connection_id="conn-1",
            connection_epoch=1,
            websocket=websocket,
        )

        with self.assertRaises(NsRuntimeTargetUnavailableError):
            await registry.send_to_connection(
                connection_id="conn-1",
                connection_epoch=0,
                envelope={
                    "message": {
                        "message_id": "msg-1",
                    },
                },
            )

    def test_retry_scheduled_delivery_replays_cached_envelope_to_transport(self) -> None:
        asyncio.run(self._run_retry_scheduled_delivery_replays_cached_envelope_to_transport())

    async def _run_retry_scheduled_delivery_replays_cached_envelope_to_transport(self) -> None:
        writer_registry = RuntimeConnectionWriterRegistry()
        delivery_registry = RuntimeDeliveryRegistry(default_ack_timeout_ms=1000)
        forwarder = RuntimeLocalEnvelopeForwarder(
            writer_registry=writer_registry,
            delivery_registry=delivery_registry,
        )

        websocket = _MemoryWebSocket()
        writer_registry.register(
            connection_id=self.target.connection_id,
            connection_epoch=self.target.connection_epoch,
            websocket=websocket,
        )

        results = await forwarder.forward(
            decision=self.decision,
            envelope=self.envelope,
        )
        delivery_id = results[0].delivery_id
        record = delivery_registry.get_record(delivery_id)
        self.assertIsNotNone(record)
        record.state = "retry_scheduled"

        retry_result = await forwarder.scan_retry_scheduled()

        self.assertEqual(retry_result.scanned_count, 1)
        self.assertEqual(retry_result.retried_count, 1)
        self.assertEqual(retry_result.expired_count, 0)
        self.assertEqual(retry_result.write_failed_count, 0)
        self.assertEqual(record.state, "ack_waiting")
        self.assertEqual(record.attempt_count, 2)
        self.assertEqual(len(websocket.sent), 2)

        replayed = json.loads(websocket.sent[-1])
        self.assertEqual(replayed["delivery"]["delivery_id"], delivery_id)
        self.assertEqual(replayed["delivery"]["attempt"], 2)

    def test_retry_scheduled_delivery_stays_retry_scheduled_when_writer_missing(self) -> None:
        asyncio.run(self._run_retry_scheduled_delivery_stays_retry_scheduled_when_writer_missing())

    async def _run_retry_scheduled_delivery_stays_retry_scheduled_when_writer_missing(self) -> None:
        writer_registry = RuntimeConnectionWriterRegistry()
        delivery_registry = RuntimeDeliveryRegistry(default_ack_timeout_ms=1000)
        forwarder = RuntimeLocalEnvelopeForwarder(
            writer_registry=writer_registry,
            delivery_registry=delivery_registry,
        )

        websocket = _MemoryWebSocket()
        writer_registry.register(
            connection_id=self.target.connection_id,
            connection_epoch=self.target.connection_epoch,
            websocket=websocket,
        )
        results = await forwarder.forward(
            decision=self.decision,
            envelope=self.envelope,
        )
        delivery_id = results[0].delivery_id
        record = delivery_registry.get_record(delivery_id)
        self.assertIsNotNone(record)
        record.state = "retry_scheduled"

        writer_registry.unregister(
            connection_id=self.target.connection_id,
            connection_epoch=self.target.connection_epoch,
        )

        retry_result = await forwarder.scan_retry_scheduled()

        self.assertEqual(retry_result.scanned_count, 1)
        self.assertEqual(retry_result.write_failed_count, 1)
        self.assertEqual(record.state, "retry_scheduled")
        self.assertEqual(record.attempt_count, 2)
        self.assertEqual(retry_result.retry_results[0].status, "retry_write_failed")

    def test_retry_scheduled_expired_delivery_moves_to_expired_without_replay(self) -> None:
        asyncio.run(self._run_retry_scheduled_expired_delivery_moves_to_expired_without_replay())

    def test_retry_scheduled_expired_delivery_refreshes_message_summary(self) -> None:
        asyncio.run(self._run_retry_scheduled_expired_delivery_refreshes_message_summary())

    def test_duplicate_forward_does_not_write_or_create_second_attempt(self) -> None:
        asyncio.run(
            self._run_duplicate_forward_does_not_write_or_create_second_attempt()
        )

    async def _run_duplicate_forward_does_not_write_or_create_second_attempt(self) -> None:
        writer_registry = (
            RuntimeConnectionWriterRegistry()
        )
        delivery_registry = RuntimeDeliveryRegistry(
            default_ack_timeout_ms=1000
        )
        forwarder = RuntimeLocalEnvelopeForwarder(
            writer_registry=writer_registry,
            delivery_registry=delivery_registry,
        )

        websocket = _MemoryWebSocket()
        writer_registry.register(
            connection_id=self.target.connection_id,
            connection_epoch=(
                self.target.connection_epoch
            ),
            websocket=websocket,
        )

        first = await forwarder.forward(
            decision=self.decision,
            envelope=self.envelope,
        )
        second = await forwarder.forward(
            decision=self.decision,
            envelope=self.envelope,
        )

        self.assertEqual(
            first[0].status,
            "sent_to_transport",
        )
        self.assertEqual(
            second[0].status,
            "duplicate",
        )
        self.assertEqual(
            second[0].duplicate_status,
            "delivery_in_progress",
        )
        self.assertEqual(
            first[0].delivery_id,
            second[0].delivery_id,
        )
        self.assertEqual(len(websocket.sent), 1)

        records = delivery_registry.list_records()

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].attempt_count, 1)
        self.assertEqual(
            len(
                delivery_registry.list_attempts_for_delivery(
                    records[0].delivery_id
                )
            ),
            1,
        )

    async def _run_retry_scheduled_expired_delivery_refreshes_message_summary(self) -> None:
        writer_registry = RuntimeConnectionWriterRegistry()
        delivery_registry = RuntimeDeliveryRegistry(default_ack_timeout_ms=1000)
        forwarder = RuntimeLocalEnvelopeForwarder(
            writer_registry=writer_registry,
            delivery_registry=delivery_registry,
        )

        websocket = _MemoryWebSocket()
        writer_registry.register(
            connection_id=self.target.connection_id,
            connection_epoch=self.target.connection_epoch,
            websocket=websocket,
        )
        results = await forwarder.forward(
            decision=self.decision,
            envelope=self.envelope,
        )
        delivery_id = results[0].delivery_id
        record = delivery_registry.get_record(delivery_id)
        self.assertIsNotNone(record)
        record.state = "retry_scheduled"
        delivery_registry.refresh_message_summary_for_delivery(record.delivery_id)

        record.expires_at = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(timespec="milliseconds")

        await forwarder.scan_retry_scheduled()

        summary = delivery_registry.get_message_summary(record.message_id)

        self.assertIsNotNone(summary)
        self.assertEqual(summary.expired_count, 1)
        self.assertEqual(summary.pending_count, 0)
        self.assertEqual(summary.state, "failed")

    async def _run_retry_scheduled_expired_delivery_moves_to_expired_without_replay(self) -> None:
        writer_registry = RuntimeConnectionWriterRegistry()
        delivery_registry = RuntimeDeliveryRegistry(default_ack_timeout_ms=1000)
        forwarder = RuntimeLocalEnvelopeForwarder(
            writer_registry=writer_registry,
            delivery_registry=delivery_registry,
        )

        websocket = _MemoryWebSocket()
        writer_registry.register(
            connection_id=self.target.connection_id,
            connection_epoch=self.target.connection_epoch,
            websocket=websocket,
        )
        results = await forwarder.forward(
            decision=self.decision,
            envelope=self.envelope,
        )
        delivery_id = results[0].delivery_id
        record = delivery_registry.get_record(delivery_id)
        self.assertIsNotNone(record)
        record.state = "retry_scheduled"
        record.expires_at = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(timespec="milliseconds")

        retry_result = await forwarder.scan_retry_scheduled()

        self.assertEqual(retry_result.scanned_count, 1)
        self.assertEqual(retry_result.expired_count, 1)
        self.assertEqual(retry_result.retried_count, 0)
        self.assertEqual(record.state, "expired")
        self.assertEqual(len(websocket.sent), 1)

    @staticmethod
    def _build_task_dispatch_frame() -> str:
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
                "connection_id": "target-1",
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
