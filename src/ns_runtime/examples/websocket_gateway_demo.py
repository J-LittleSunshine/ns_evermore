# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import sys
from importlib import import_module
from pathlib import Path

# 仅用于本地示例直接运行：将 src 目录加入 sys.path，便于 `python src/ns_runtime/examples/websocket_gateway_demo.py` 执行。
PROJECT_SRC_PATH = Path(__file__).resolve().parents[2]
if str(PROJECT_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC_PATH))

from ns_runtime import (  # noqa: E402
    RuntimePacket,
    RuntimePacketCodec,
    RuntimePacketType,
    RuntimeService,
    WebSocketGateway,
    WebSocketGatewayConfig,
)


async def _run_demo() -> None:
    service = RuntimeService()

    def on_event(packet: RuntimePacket) -> RuntimePacket | None:
        return RuntimePacket.create(
            packet_type=RuntimePacketType.RESULT,
            source_endpoint_id="demo-router",
            target_endpoint_id=packet.source_endpoint_id,
            trace_id=packet.trace_id,
            payload={
                "ok": True,
                "action": "event_handled",
                "payload": dict(packet.payload),
            },
        )

    service.router.register_handler(RuntimePacketType.EVENT, on_event)
    gateway = WebSocketGateway(
        runtime_service=service,
        config=WebSocketGatewayConfig(host="127.0.0.1", port=8765, path="/runtime"),
    )
    codec = RuntimePacketCodec()

    try:
        client_module = import_module("websockets.asyncio.client")
        connect = getattr(client_module, "connect")
    except (ImportError, AttributeError) as exc:
        raise RuntimeError("websockets is not installed, please install package 'websockets'") from exc

    await gateway.start()
    print("[gateway] started", gateway.config.host, gateway.config.port, gateway.config.path)

    try:
        async with connect(f"ws://{gateway.config.host}:{gateway.config.port}{gateway.config.path}") as websocket:
            register_packet = RuntimePacket.create(
                packet_type=RuntimePacketType.REGISTER,
                source_endpoint_id="frontend-demo",
                payload={
                    "endpoint_id": "frontend-demo",
                    "endpoint_type": "FRONTEND",
                    "capabilities": ["event.send"],
                    "metadata": {"env": "local-demo"},
                },
            )
            await websocket.send(codec.encode(register_packet))
            register_response = codec.decode(await websocket.recv())
            print("[register]", register_response.packet_type.value, register_response.payload)

            heartbeat_packet = RuntimePacket.create(
                packet_type=RuntimePacketType.HEARTBEAT,
                source_endpoint_id="frontend-demo",
                payload={"tick": 1},
            )
            await websocket.send(codec.encode(heartbeat_packet))
            heartbeat_response = codec.decode(await websocket.recv())
            print("[heartbeat]", heartbeat_response.packet_type.value, heartbeat_response.payload)

            event_packet = RuntimePacket.create(
                packet_type=RuntimePacketType.EVENT,
                source_endpoint_id="frontend-demo",
                trace_id="ws-demo-trace-1",
                payload={"message": "hello websocket gateway"},
            )
            await websocket.send(codec.encode(event_packet))
            event_response = codec.decode(await websocket.recv())
            print("[event result]", event_response.packet_type.value, event_response.payload)
    finally:
        await gateway.stop()
        print("[gateway] stopped")


def main() -> None:
    try:
        asyncio.run(_run_demo())
    except RuntimeError as exc:
        print("[runtime error]", exc)
        print("请先安装 websockets，再执行 websocket_gateway_demo.py。")
    except Exception as exc:
        print("[connection or operation error]", exc)
        print("请确认本地端口可用，且网络环境允许建立 WebSocket 连接。")


if __name__ == "__main__":
    main()

