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
    def test_websocket_task_dispatch_to_unavailable_target_returns_delivery_rejected(self) -> None:
        asyncio.run(
            self._run_websocket_task_dispatch_to_unavailable_target_returns_delivery_rejected()
        )

    def test_websocket_connection_hello_then_runtime_health(self) -> None:
        asyncio.run(self._run_websocket_connection_hello_then_runtime_health())

    def test_websocket_task_dispatch_forwards_to_local_connection(self) -> None:
        asyncio.run(self._run_websocket_task_dispatch_forwards_to_local_connection())

    def test_websocket_duplicate_task_dispatch_is_not_forwarded_twice(self) -> None:
        asyncio.run(
            self._run_websocket_duplicate_task_dispatch_is_not_forwarded_twice()
        )

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

                    dispatch_frame = self._build_task_dispatch_frame(
                        target_connection_id=receiver_connection_id
                    )
                    dispatch_request = self._read_json(dispatch_frame)
                    dispatch_message_id = dispatch_request["message"]["message_id"]

                    await sender.send(dispatch_frame)

                    forwarded = self._read_json(await receiver.recv())
                    accepted = self._read_json(await sender.recv())

                    self.assertEqual(forwarded["message"]["type"], "task.dispatch")
                    self.assertEqual(forwarded["source"]["connection_id"], sender_connection_id)
                    self.assertEqual(forwarded["target"]["connection_id"], receiver_connection_id)
                    self.assertEqual(forwarded["payload"]["inline"]["task_name"], "demo-task")
                    self.assertIn("delivery", forwarded)
                    self.assertIn("delivery_id", forwarded["delivery"])
                    self.assertEqual(forwarded["delivery"]["attempt"], 1)
                    self.assertEqual(forwarded["delivery"]["replay_epoch"], 0)

                    accepted_inline = accepted["payload"]["inline"]

                    self.assertEqual(accepted["message"]["type"], "delivery.accepted")
                    self.assertEqual(accepted["message"]["category"], "delivery")
                    self.assertEqual(accepted["message"]["reliability"], "best_effort")
                    self.assertEqual(
                        accepted["target"]["connection_id"],
                        sender_connection_id,
                    )
                    self.assertEqual(
                        accepted_inline["message_id"],
                        dispatch_message_id,
                    )
                    self.assertEqual(
                        accepted_inline["summary_id"],
                        forwarded["delivery"]["summary_id"],
                    )
                    self.assertTrue(accepted_inline["accepted_at"])
                    self.assertEqual(
                        accepted_inline["status_query_hint"],
                        "delivery.status_query",
                    )
                    self.assertEqual(
                        accepted["trace"]["request_id"],
                        dispatch_message_id,
                    )

                    self.assertEqual(
                        set(accepted_inline.keys()),
                        {
                            "message_id",
                            "summary_id",
                            "accepted_at",
                            "status_query_hint",
                        },
                    )
                    self.assertNotIn("delivery", accepted)
                    self.assertNotIn("writes", accepted_inline)
                    self.assertNotIn("write_count", accepted_inline)
                    self.assertNotIn("delivery_id", accepted_inline)

                    summary_before_ack = service.get_message_summary(
                        dispatch_message_id
                    )

                    self.assertIsNotNone(summary_before_ack)
                    self.assertEqual(
                        summary_before_ack.summary_id,
                        accepted_inline["summary_id"],
                    )
                    self.assertEqual(summary_before_ack.acked_count, 0)
                    self.assertEqual(summary_before_ack.ack_waiting_count, 1)
                    self.assertEqual(summary_before_ack.pending_count, 1)
                    self.assertEqual(summary_before_ack.state, "pending")

                    delivery_id = forwarded["delivery"]["delivery_id"]

                    await receiver.send(
                        self._build_ack_frame(
                            delivery_id=delivery_id
                        )
                    )
                    ack_result = self._read_json(await receiver.recv())

                    self.assertEqual(
                        ack_result["message"]["type"],
                        "delivery.ack_result",
                    )
                    self.assertEqual(
                        ack_result["payload"]["inline"]["status"],
                        "acked",
                    )
                    self.assertEqual(
                        ack_result["payload"]["inline"]["delivery_state"],
                        "acked",
                    )
                    self.assertEqual(
                        ack_result["payload"]["inline"]["delivery_id"],
                        delivery_id,
                    )
                    self.assertFalse(
                        ack_result["payload"]["inline"]["duplicate"]
                    )

                    delivery_record = service.delivery_registry.get_record(
                        delivery_id
                    )
                    self.assertIsNotNone(delivery_record)
                    self.assertEqual(delivery_record.state, "acked")

                    summary_after_ack = service.get_message_summary(
                        dispatch_message_id
                    )

                    self.assertIsNotNone(summary_after_ack)
                    self.assertEqual(summary_after_ack.acked_count, 1)
                    self.assertEqual(summary_after_ack.ack_waiting_count, 0)
                    self.assertEqual(summary_after_ack.pending_count, 0)
                    self.assertEqual(summary_after_ack.state, "all_acked")

    async def _run_websocket_duplicate_task_dispatch_is_not_forwarded_twice(self) -> None:
        try:
            from websockets.asyncio.client import connect
            from websockets.asyncio.server import serve
        except ImportError as exc:
            raise RuntimeError(
                "Install requirements-runtime.txt before running runtime integration tests."
            ) from exc

        service = RuntimeService.build_default(
            runtime_id="runtime-test",
            authenticator=LocalTokenRuntimeAuthenticator(
                expected_token="secret"
            ),
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

            # 建立任务接收方连接。
            async with connect(
                    f"ws://127.0.0.1:{port}",
                    max_size=config.max_frame_bytes,
            ) as receiver:
                await receiver.send(
                    self._build_hello_frame(
                        token="secret",
                        capabilities=[
                            "task.execute",
                        ],
                    )
                )
                receiver_accepted = self._read_json(
                    await receiver.recv()
                )
                receiver_connection_id = receiver_accepted[
                    "payload"
                ]["inline"]["connection_id"]

                # 建立任务发送方连接。
                async with connect(
                        f"ws://127.0.0.1:{port}",
                        max_size=config.max_frame_bytes,
                ) as sender:
                    await sender.send(
                        self._build_hello_frame(
                            token="secret",
                            capabilities=[
                                "task.dispatch",
                            ],
                        )
                    )
                    sender_accepted = self._read_json(
                        await sender.recv()
                    )
                    sender_connection_id = sender_accepted[
                        "payload"
                    ]["inline"]["connection_id"]

                    # 这里只构建一次。
                    # 后面三次必须发送同一个 dispatch_frame，
                    # 才能保持 message_id 相同并命中去重。
                    dispatch_frame = self._build_task_dispatch_frame(
                        target_connection_id=receiver_connection_id
                    )
                    dispatch_request = self._read_json(
                        dispatch_frame
                    )
                    dispatch_message_id = dispatch_request[
                        "message"
                    ]["message_id"]

                    # --------------------------------------------------
                    # 第一次发送：正常创建 delivery 并转发给 receiver。
                    # --------------------------------------------------
                    await sender.send(dispatch_frame)

                    forwarded = self._read_json(
                        await receiver.recv()
                    )
                    accepted = self._read_json(
                        await sender.recv()
                    )

                    self.assertEqual(
                        forwarded["message"]["type"],
                        "task.dispatch",
                    )
                    self.assertEqual(
                        forwarded["source"]["connection_id"],
                        sender_connection_id,
                    )
                    self.assertEqual(
                        forwarded["target"]["connection_id"],
                        receiver_connection_id,
                    )
                    self.assertEqual(
                        accepted["message"]["type"],
                        "delivery.accepted",
                    )

                    delivery_id = forwarded[
                        "delivery"
                    ]["delivery_id"]
                    summary_id = forwarded[
                        "delivery"
                    ]["summary_id"]

                    # --------------------------------------------------
                    # 第二次发送同一 frame：
                    # delivery 尚未 ACK，应返回 delivery_in_progress。
                    # receiver 不应该再次收到 task.dispatch。
                    # --------------------------------------------------
                    await sender.send(dispatch_frame)

                    duplicate_in_progress = self._read_json(
                        await sender.recv()
                    )
                    duplicate_inline = duplicate_in_progress[
                        "payload"
                    ]["inline"]

                    self.assertEqual(
                        duplicate_in_progress["message"]["type"],
                        "delivery.duplicate",
                    )
                    self.assertEqual(
                        duplicate_in_progress["target"][
                            "connection_id"
                        ],
                        sender_connection_id,
                    )
                    self.assertEqual(
                        duplicate_inline["message_id"],
                        dispatch_message_id,
                    )
                    self.assertEqual(
                        duplicate_inline["summary_id"],
                        summary_id,
                    )
                    self.assertEqual(
                        duplicate_inline["duplicate_status"],
                        "delivery_in_progress",
                    )
                    self.assertEqual(
                        duplicate_inline["status_query_hint"],
                        "delivery.status_query",
                    )
                    self.assertNotIn(
                        "delivery_id",
                        duplicate_inline,
                    )
                    self.assertNotIn(
                        "delivery",
                        duplicate_in_progress,
                    )

                    records = (
                        service.delivery_registry.list_records()
                    )

                    self.assertEqual(len(records), 1)
                    self.assertEqual(
                        records[0].delivery_id,
                        delivery_id,
                    )
                    self.assertEqual(
                        records[0].attempt_count,
                        1,
                    )
                    self.assertEqual(
                        len(
                            service.delivery_registry.list_attempts_for_delivery(
                                delivery_id
                            )
                        ),
                        1,
                    )

                    # --------------------------------------------------
                    # receiver ACK 第一条 delivery。
                    # --------------------------------------------------
                    await receiver.send(
                        self._build_ack_frame(
                            delivery_id=delivery_id
                        )
                    )
                    ack_result = self._read_json(
                        await receiver.recv()
                    )

                    self.assertEqual(
                        ack_result["message"]["type"],
                        "delivery.ack_result",
                    )
                    self.assertEqual(
                        ack_result["payload"]["inline"]["status"],
                        "acked",
                    )

                    # --------------------------------------------------
                    # 第三次发送同一 frame：
                    # 原 delivery 已 ACK，应返回 already_delivered。
                    # --------------------------------------------------
                    await sender.send(dispatch_frame)

                    duplicate_delivered = self._read_json(
                        await sender.recv()
                    )
                    delivered_inline = duplicate_delivered[
                        "payload"
                    ]["inline"]

                    self.assertEqual(
                        duplicate_delivered["message"]["type"],
                        "delivery.duplicate",
                    )
                    self.assertEqual(
                        delivered_inline["message_id"],
                        dispatch_message_id,
                    )
                    self.assertEqual(
                        delivered_inline["summary_id"],
                        summary_id,
                    )
                    self.assertEqual(
                        delivered_inline["duplicate_status"],
                        "already_delivered",
                    )

                    # 第二次和第三次提交都不能再写给 receiver。
                    with self.assertRaises(
                            asyncio.TimeoutError
                    ):
                        await asyncio.wait_for(
                            receiver.recv(),
                            timeout=0.1,
                        )

                    records_after_duplicate = (
                        service.delivery_registry.list_records()
                    )

                    self.assertEqual(
                        len(records_after_duplicate),
                        1,
                    )
                    self.assertEqual(
                        records_after_duplicate[0].delivery_id,
                        delivery_id,
                    )
                    self.assertEqual(
                        records_after_duplicate[0].attempt_count,
                        1,
                    )

                    summary = service.get_message_summary(
                        dispatch_message_id
                    )

                    self.assertIsNotNone(summary)
                    self.assertEqual(
                        summary.summary_id,
                        summary_id,
                    )
                    self.assertEqual(
                        summary.delivery_count,
                        1,
                    )
                    self.assertEqual(
                        summary.acked_count,
                        1,
                    )
                    self.assertEqual(
                        summary.state,
                        "all_acked",
                    )

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

    async def _run_websocket_task_dispatch_to_unavailable_target_returns_delivery_rejected(self) -> None:
        try:
            from websockets.asyncio.client import connect
            from websockets.asyncio.server import serve
        except ImportError as exc:
            raise RuntimeError(
                "Install requirements-runtime.txt before running runtime integration tests."
            ) from exc

        service = RuntimeService.build_default(
            runtime_id="runtime-test",
            authenticator=LocalTokenRuntimeAuthenticator(
                expected_token="secret"
            ),
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

            async with connect(
                    f"ws://127.0.0.1:{port}",
                    max_size=config.max_frame_bytes,
            ) as sender:
                await sender.send(
                    self._build_hello_frame(
                        token="secret",
                        capabilities=[
                            "task.dispatch"
                        ],
                    )
                )
                sender_accepted = self._read_json(
                    await sender.recv()
                )
                sender_connection_id = sender_accepted[
                    "payload"
                ]["inline"]["connection_id"]

                dispatch_frame = self._build_task_dispatch_frame(
                    target_connection_id="missing-connection"
                )
                dispatch_request = self._read_json(
                    dispatch_frame
                )
                dispatch_message_id = dispatch_request[
                    "message"
                ]["message_id"]

                await sender.send(dispatch_frame)

                rejected = self._read_json(
                    await sender.recv()
                )
                inline = rejected["payload"]["inline"]

                self.assertEqual(
                    rejected["message"]["type"],
                    "delivery.rejected",
                )
                self.assertEqual(
                    rejected["target"]["connection_id"],
                    sender_connection_id,
                )
                self.assertEqual(
                    inline["message_id"],
                    dispatch_message_id,
                )
                self.assertEqual(
                    inline["reason_code"],
                    "RUNTIME_TARGET_UNAVAILABLE",
                )
                self.assertTrue(inline["retryable"])
                self.assertNotIn("delivery", rejected)

                summary = service.get_message_summary(
                    dispatch_message_id
                )

                self.assertIsNotNone(summary)
                self.assertEqual(summary.rejected_count, 1)
                self.assertEqual(summary.delivery_count, 0)
                self.assertEqual(summary.state, "failed")

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
