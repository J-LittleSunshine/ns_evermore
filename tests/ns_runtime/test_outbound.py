# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import unittest
from typing import (
    TYPE_CHECKING
)

from ns_common.exceptions import NsRuntimeTargetUnavailableError
from ns_runtime.outbound import RuntimeConnectionWriterRegistry

if TYPE_CHECKING:
    pass


class FakeWebSocket:
    def __init__(self) -> None:
        self.frames: list[str] = []

    async def send(self, frame: str) -> None:
        self.frames.append(frame)


class RuntimeConnectionWriterRegistryTestCase(unittest.IsolatedAsyncioTestCase):
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


if __name__ == "__main__":
    unittest.main()
