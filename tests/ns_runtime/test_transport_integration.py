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

    @staticmethod
    def _build_hello_frame(*, token: str) -> str:
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
                        "requested_capabilities": [
                            "runtime.management",
                            "task.dispatch",
                        ],
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
