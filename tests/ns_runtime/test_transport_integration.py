# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import unittest
import uuid
from typing import (
    Any,
    TYPE_CHECKING
)

from ns_runtime.auth import LocalTokenRuntimeAuthenticator
from ns_runtime.models import utc_now_iso
from ns_runtime.service import RuntimeService
from ns_runtime.transport import RuntimeWebSocketTransportConfig

if TYPE_CHECKING:
    pass


class RuntimeTransportIntegrationTestCase(unittest.TestCase):
    def test_websocket_connection_hello_then_runtime_health(self) -> None:
        asyncio.run(self._run_websocket_connection_hello_then_runtime_health())

    def test_websocket_task_dispatch_forwards_to_local_connection(self) -> None:
        asyncio.run(self._run_websocket_task_dispatch_forwards_to_local_connection())

    def test_websocket_task_dispatch_then_nack_moves_delivery_to_retry_scheduled(self) -> None:
        asyncio.run(self._run_websocket_task_dispatch_then_nack_moves_delivery_to_retry_scheduled())

    def test_websocket_task_dispatch_then_defer_extends_ack_deadline(self) -> None:
        asyncio.run(self._run_websocket_task_dispatch_then_defer_extends_ack_deadline())

    async def _run_websocket_task_dispatch_forwards_to_local_connection(self) -> None:
        try:
            from websockets.asyncio.client import connect
            from websockets.asyncio.server import serve
        except ImportError as exc:
            raise RuntimeError("Install requirements-runtime.txt before running runtime integration tests.") from exc

        service = RuntimeService.build_default(
            runtime_id="runtime-test",
            authenticator=LocalTokenRuntimeAuthenticator(expected_token="secret"),
        )
        config = RuntimeWebSocketTransportConfig(
            host="127.0.0.1",
            port=0,
            handshake_timeout_seconds=2.0,
        )
        transport = service.build_transport(config)

        async with serve(
                transport.handle_connection,
                config.host,
                0,
                compression=None,
                max_size=config.max_frame_bytes,
                max_queue=config.read_queue_high_water,
                write_limit=config.write_limit_bytes,
                ping_interval=None,
                server_header=None,
        ) as server:
            port = server.sockets[0].getsockname()[1]
            async with connect(f"ws://127.0.0.1:{port}", max_size=config.max_frame_bytes) as receiver:
                await receiver.send(self._build_hello_frame(token="secret", capabilities=[
                    "task.execute"
                ]
                )
                )
                receiver_accepted = self._read_json(await receiver.recv())
                receiver_connection_id = receiver_accepted["payload"]["inline"]["connection_id"]

                async with connect(f"ws://127.0.0.1:{port}", max_size=config.max_frame_bytes) as sender:
                    await sender.send(self._build_hello_frame(token="secret", capabilities=[
                        "task.dispatch"
                    ]
                    )
                    )
                    sender_accepted = self._read_json(await sender.recv())
                    sender_connection_id = sender_accepted["payload"]["inline"]["connection_id"]

                    await sender.send(self._build_task_dispatch_frame(target_connection_id=receiver_connection_id))

                    forwarded = self._read_json(await receiver.recv())
                    forward_result = self._read_json(await sender.recv())

                    self.assertEqual(forwarded["message"]["type"], "task.dispatch")
                    self.assertEqual(forwarded["source"]["connection_id"], sender_connection_id)
                    self.assertEqual(forwarded["target"]["connection_id"], receiver_connection_id)
                    self.assertEqual(forwarded["payload"]["inline"]["task_name"], "demo-task")
                    self.assertIn("delivery", forwarded)
                    self.assertIn("delivery_id", forwarded["delivery"])
                    self.assertEqual(forwarded["delivery"]["attempt"], 1)
                    self.assertEqual(forwarded["delivery"]["replay_epoch"], 0)

                    self.assertEqual(forward_result["message"]["type"], "runtime.control.forward_result")
                    self.assertEqual(forward_result["payload"]["inline"]["status"], "forwarded")
                    self.assertEqual(forward_result["payload"]["inline"]["write_count"], 1)
                    self.assertEqual(forward_result["payload"]["inline"]["writes"][0]["status"], "sent_to_transport")
                    self.assertEqual(forward_result["payload"]["inline"]["writes"][0]["delivery_state"], "ack_waiting")
                    self.assertEqual(forward_result["payload"]["inline"]["writes"][0]["delivery_id"], forwarded["delivery"]["delivery_id"])
                    self.assertEqual(
                        forward_result["payload"]["inline"]["reliability_note"],
                        "websocket_send_only_no_delivery_ack",
                    )
                    delivery_id = forwarded["delivery"]["delivery_id"]
                    await receiver.send(self._build_ack_frame(delivery_id=delivery_id))
                    ack_result = self._read_json(await receiver.recv())

                    self.assertEqual(ack_result["message"]["type"], "delivery.ack_result")
                    self.assertEqual(ack_result["payload"]["inline"]["status"], "acked")
                    self.assertEqual(ack_result["payload"]["inline"]["delivery_state"], "acked")
                    self.assertEqual(ack_result["payload"]["inline"]["delivery_id"], delivery_id)
                    self.assertFalse(ack_result["payload"]["inline"]["duplicate"])

                    delivery_record = service.delivery_registry.get_record(delivery_id)
                    self.assertIsNotNone(delivery_record)
                    self.assertEqual(delivery_record.state, "acked")

    async def _run_websocket_connection_hello_then_runtime_health(self) -> None:
        try:
            from websockets.asyncio.client import connect
            from websockets.asyncio.server import serve
        except ImportError as exc:
            raise RuntimeError("Install requirements-runtime.txt before running runtime integration tests.") from exc

        service = RuntimeService.build_default(
            runtime_id="runtime-test",
            authenticator=LocalTokenRuntimeAuthenticator(expected_token="secret"),
        )
        config = RuntimeWebSocketTransportConfig(
            host="127.0.0.1",
            port=0,
            handshake_timeout_seconds=2.0,
        )
        transport = service.build_transport(config)

        async with serve(
                transport.handle_connection,
                config.host,
                0,
                compression=None,
                max_size=config.max_frame_bytes,
                max_queue=config.read_queue_high_water,
                write_limit=config.write_limit_bytes,
                ping_interval=None,
                server_header=None,
        ) as server:
            port = server.sockets[0].getsockname()[1]
            async with connect(f"ws://127.0.0.1:{port}", max_size=config.max_frame_bytes) as websocket:
                await websocket.send(self._build_hello_frame(token="secret"))
                accepted = self._read_json(await websocket.recv())

                self.assertEqual(accepted["message"]["type"], "connection.accepted")
                self.assertIn("connection_id", accepted["payload"]["inline"])
                self.assertNotIn("tenant_id", accepted["payload"]["inline"])
                self.assertNotIn("identity", accepted["payload"]["inline"])

                await websocket.send(self._build_health_frame())
                health_result = self._read_json(await websocket.recv())

                self.assertEqual(health_result["message"]["type"], "runtime.control.health_result")
                self.assertEqual(health_result["payload"]["inline"]["status"], "ok")
                self.assertEqual(health_result["payload"]["inline"]["runtime"]["active_connection_count"], 1)

    async def _run_websocket_task_dispatch_then_nack_moves_delivery_to_retry_scheduled(self) -> None:
        try:
            from websockets.asyncio.client import connect
            from websockets.asyncio.server import serve
        except ImportError as exc:
            raise RuntimeError("Install requirements-runtime.txt before running runtime integration tests.") from exc

        service = RuntimeService.build_default(
            runtime_id="runtime-test",
            authenticator=LocalTokenRuntimeAuthenticator(expected_token="secret"),
        )
        config = RuntimeWebSocketTransportConfig(
            host="127.0.0.1",
            port=0,
            handshake_timeout_seconds=2.0,
        )
        transport = service.build_transport(config)

        async with serve(
                transport.handle_connection,
                config.host,
                0,
                compression=None,
                max_size=config.max_frame_bytes,
                max_queue=config.read_queue_high_water,
                write_limit=config.write_limit_bytes,
                ping_interval=None,
                server_header=None,
        ) as server:
            port = server.sockets[0].getsockname()[1]
            async with connect(f"ws://127.0.0.1:{port}", max_size=config.max_frame_bytes) as receiver:
                await receiver.send(self._build_hello_frame(token="secret", capabilities=[
                    "task.execute"
                ]
                )
                )
                receiver_accepted = self._read_json(await receiver.recv())
                receiver_connection_id = receiver_accepted["payload"]["inline"]["connection_id"]

                async with connect(f"ws://127.0.0.1:{port}", max_size=config.max_frame_bytes) as sender:
                    await sender.send(self._build_hello_frame(token="secret", capabilities=[
                        "task.dispatch"
                    ]
                    )
                    )
                    await sender.recv()

                    await sender.send(self._build_task_dispatch_frame(target_connection_id=receiver_connection_id))

                    forwarded = self._read_json(await receiver.recv())
                    await sender.recv()

                    delivery_id = forwarded["delivery"]["delivery_id"]
                    await receiver.send(
                        self._build_nack_frame(
                            delivery_id=delivery_id,
                            reason="temporarily_unavailable",
                        )
                    )
                    nack_result = self._read_json(await receiver.recv())

                    self.assertEqual(nack_result["message"]["type"], "delivery.nack_result")
                    self.assertEqual(nack_result["payload"]["inline"]["status"], "nacked_retry_scheduled")
                    self.assertEqual(nack_result["payload"]["inline"]["delivery_state"], "retry_scheduled")
                    self.assertEqual(nack_result["payload"]["inline"]["delivery_id"], delivery_id)
                    self.assertEqual(nack_result["payload"]["inline"]["reason"], "temporarily_unavailable")
                    self.assertTrue(nack_result["payload"]["inline"]["retryable"])
                    self.assertFalse(nack_result["payload"]["inline"]["duplicate"])

                    delivery_record = service.delivery_registry.get_record(delivery_id)
                    self.assertIsNotNone(delivery_record)
                    self.assertEqual(delivery_record.state, "retry_scheduled")

    async def _run_websocket_task_dispatch_then_defer_extends_ack_deadline(self) -> None:
        try:
            from websockets.asyncio.client import connect
            from websockets.asyncio.server import serve
        except ImportError as exc:
            raise RuntimeError("Install requirements-runtime.txt before running runtime integration tests.") from exc

        service = RuntimeService.build_default(
            runtime_id="runtime-test",
            authenticator=LocalTokenRuntimeAuthenticator(expected_token="secret"),
        )
        config = RuntimeWebSocketTransportConfig(
            host="127.0.0.1",
            port=0,
            handshake_timeout_seconds=2.0,
        )
        transport = service.build_transport(config)

        async with serve(
                transport.handle_connection,
                config.host,
                0,
                compression=None,
                max_size=config.max_frame_bytes,
                max_queue=config.read_queue_high_water,
                write_limit=config.write_limit_bytes,
                ping_interval=None,
                server_header=None,
        ) as server:
            port = server.sockets[0].getsockname()[1]
            async with connect(f"ws://127.0.0.1:{port}", max_size=config.max_frame_bytes) as receiver:
                await receiver.send(self._build_hello_frame(token="secret", capabilities=["task.execute"]))
                receiver_accepted = self._read_json(await receiver.recv())
                receiver_connection_id = receiver_accepted["payload"]["inline"]["connection_id"]

                async with connect(f"ws://127.0.0.1:{port}", max_size=config.max_frame_bytes) as sender:
                    await sender.send(self._build_hello_frame(token="secret", capabilities=["task.dispatch"]))
                    await sender.recv()

                    await sender.send(self._build_task_dispatch_frame(target_connection_id=receiver_connection_id))

                    forwarded = self._read_json(await receiver.recv())
                    await sender.recv()

                    delivery_id = forwarded["delivery"]["delivery_id"]
                    original_record = service.delivery_registry.get_record(delivery_id)
                    self.assertIsNotNone(original_record)
                    original_deadline = original_record.ack_deadline_at

                    await receiver.send(
                        self._build_defer_frame(
                            delivery_id=delivery_id,
                            defer_ms=1000,
                        )
                    )
                    defer_result = self._read_json(await receiver.recv())

                    self.assertEqual(defer_result["message"]["type"], "delivery.defer_result")
                    self.assertEqual(defer_result["payload"]["inline"]["status"], "deferred")
                    self.assertEqual(defer_result["payload"]["inline"]["delivery_state"], "ack_waiting")
                    self.assertEqual(defer_result["payload"]["inline"]["delivery_id"], delivery_id)
                    self.assertEqual(defer_result["payload"]["inline"]["defer_ms"], 1000)
                    self.assertEqual(defer_result["payload"]["inline"]["defer_sequence"], 1)
                    self.assertEqual(defer_result["payload"]["inline"]["defer_count"], 1)
                    self.assertEqual(defer_result["payload"]["inline"]["total_defer_ms"], 1000)

                    delivery_record = service.delivery_registry.get_record(delivery_id)
                    self.assertIsNotNone(delivery_record)
                    self.assertEqual(delivery_record.state, "ack_waiting")
                    self.assertNotEqual(delivery_record.ack_deadline_at, original_deadline)

    @staticmethod
    def _build_hello_frame(*, token: str, capabilities: list[str] | None = None) -> str:
        return json.dumps(
            {
                "protocol": {
                    "version": "1.0.0",
                },
                "message": {
                    "message_id": str(uuid.uuid4()),
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
                        "requested_capabilities": capabilities or [
                            "runtime.management",
                            "task.dispatch",
                        ],
                    },
                },
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _build_task_dispatch_frame(*, target_connection_id: str) -> str:
        return json.dumps(
            {
                "protocol": {
                    "version": "1.0.0",
                },
                "message": {
                    "message_id": str(uuid.uuid4()),
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

    @staticmethod
    def _build_ack_frame(*, delivery_id: str) -> str:
        return json.dumps(
            {
                "protocol": {
                    "version": "1.0.0",
                },
                "message": {
                    "message_id": str(uuid.uuid4()),
                    "type": "delivery.ack",
                    "category": "delivery",
                    "priority": 100,
                    "created_at": utc_now_iso(),
                    "reliability": "critical",
                },
                "delivery": {
                    "delivery_id": delivery_id,
                },
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _build_nack_frame(*, delivery_id: str, reason: str) -> str:
        return json.dumps(
            {
                "protocol": {
                    "version": "1.0.0",
                },
                "message": {
                    "message_id": str(uuid.uuid4()),
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
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _build_defer_frame(*, delivery_id: str, defer_ms: int) -> str:
        return json.dumps(
            {
                "protocol": {
                    "version": "1.0.0",
                },
                "message": {
                    "message_id": str(uuid.uuid4()),
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
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _build_health_frame() -> str:
        return json.dumps(
            {
                "protocol": {
                    "version": "1.0.0",
                },
                "message": {
                    "message_id": str(uuid.uuid4()),
                    "type": "runtime.control.health",
                    "category": "control",
                    "priority": 100,
                    "created_at": utc_now_iso(),
                    "reliability": "best_effort",
                },
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _read_json(frame: Any) -> dict[str, Any]:
        if not isinstance(frame, str):
            raise AssertionError("Expected text WebSocket frame.")

        value = json.loads(frame)
        if not isinstance(value, dict):
            raise AssertionError("Expected object JSON frame.")

        return value


if __name__ == "__main__":
    unittest.main()
