# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

# 仅用于本地示例直接运行：将 src 目录加入 sys.path，便于 `python src/ns_runtime/examples/basic_runtime_demo.py` 执行。
PROJECT_SRC_PATH = Path(__file__).resolve().parents[2]
if str(PROJECT_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC_PATH))

from ns_runtime import (  # noqa: E402
    EndpointRegistry,
    MemoryBroker,
    RuntimeEndpoint,
    RuntimeEndpointType,
    RuntimePacket,
    RuntimePacketCodec,
    RuntimePacketRouter,
    RuntimePacketType,
    RuntimeService,
)


def main() -> None:
    codec = RuntimePacketCodec()
    packet = RuntimePacket.create(
        packet_type=RuntimePacketType.EVENT,
        source_endpoint_id="runtime-1",
        topic="runtime.default",
        trace_id="trace-demo-1",
        tenant_id="tenant-a",
        operator_id="operator-1001",
        payload={"message": "hello runtime"},
        headers={"x-source": "demo"},
    )
    encoded = codec.encode(packet)
    decoded = codec.decode(encoded)
    print("[packet codec]", decoded.packet_id, decoded.packet_type.value, decoded.payload.get("message"))

    endpoint_registry = EndpointRegistry()
    endpoint = RuntimeEndpoint.create(
        endpoint_id="runtime-1",
        endpoint_type=RuntimeEndpointType.RUNTIME,
        capabilities=("packet.route", "packet.route", "health"),
        metadata={"zone": "local"},
    )
    endpoint_registry.register(endpoint)
    endpoint_registry.heartbeat("runtime-1")
    endpoints = endpoint_registry.list_all()
    print("[endpoint registry]", len(endpoints), endpoints[0].status.value, endpoints[0].capabilities)

    broker = MemoryBroker()
    broker.start()
    broker.publish("runtime.default", packet)
    polled = broker.poll("runtime.default", max_count=10)
    print("[memory broker]", len(polled), polled[0].packet_type.value if polled else "NONE")
    broker.stop()

    router = RuntimePacketRouter()

    def on_event(incoming: RuntimePacket) -> RuntimePacket | None:
        return RuntimePacket.create(
            packet_type=RuntimePacketType.RESULT,
            source_endpoint_id="router",
            target_endpoint_id=incoming.source_endpoint_id,
            topic=incoming.topic,
            trace_id=incoming.trace_id,
            tenant_id=incoming.tenant_id,
            operator_id=incoming.operator_id,
            payload={"ok": True},
        )

    router.register_handler(RuntimePacketType.EVENT, on_event)
    routed = router.route(packet)
    print("[router]", routed.packet_type.value if routed else "NONE", routed.payload if routed else {})

    service = RuntimeService()
    service.start()
    print("[runtime service]", service.is_running, service.state.value, service.is_master)
    service.stop()
    print("[runtime service]", service.is_running, service.state.value)


if __name__ == "__main__":
    main()

