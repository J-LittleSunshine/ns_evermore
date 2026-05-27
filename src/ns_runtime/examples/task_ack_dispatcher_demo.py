# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import sys
from importlib import import_module
from pathlib import Path

# 仅用于本地示例直接运行：将 src 目录加入 sys.path，便于 `python src/ns_runtime/examples/task_ack_dispatcher_demo.py` 执行。
PROJECT_SRC_PATH = Path(__file__).resolve().parents[2]
if str(PROJECT_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC_PATH))

from ns_runtime import (  # noqa: E402
    MemoryBroker,
    MemoryTaskStore,
    RuntimePacket,
    RuntimePacketCodec,
    RuntimePacketType,
    RuntimeService,
    RuntimeTaskContext,
    RuntimeTaskDispatcher,
    RuntimeTaskSubmitRequest,
    RuntimeTaskSubmitter,
    WebSocketGateway,
    WebSocketGatewayConfig,
)


async def _run_demo() -> None:
    broker = MemoryBroker()
    service = RuntimeService(broker=broker)
    task_store = MemoryTaskStore()
    gateway = WebSocketGateway(
        runtime_service=service,
        config=WebSocketGatewayConfig(host="127.0.0.1", port=8768, path="/runtime"),
    )
    codec = RuntimePacketCodec()

    try:
        client_module = import_module("websockets.asyncio.client")
        connect = getattr(client_module, "connect")
    except (ImportError, AttributeError) as exc:
        raise RuntimeError("websockets is not installed, please install package 'websockets'") from exc

    await gateway.start()
    try:
        async with connect(f"ws://{gateway.config.host}:{gateway.config.port}{gateway.config.path}") as websocket:
            register_packet = RuntimePacket.create(
                packet_type=RuntimePacketType.REGISTER,
                source_endpoint_id="executor-ack-demo",
                payload={
                    "endpoint_id": "executor-ack-demo",
                    "endpoint_type": "EXECUTOR",
                    "capabilities": ["demo.echo"],
                },
            )
            await websocket.send(codec.encode(register_packet))
            register_response = codec.decode(await websocket.recv())
            print("[register]", register_response.packet_type.value, register_response.payload)

            submitter = RuntimeTaskSubmitter(
                broker=broker,
                task_store=task_store,
                use_stream=False,
            )
            submit_result = submitter.submit_task(
                RuntimeTaskSubmitRequest(
                    task_type="demo.echo",
                    payload={"message": "hello ack"},
                    context=RuntimeTaskContext(
                        trace_id="ack-demo-trace-1",
                        tenant_id="tenant-demo",
                        operator_id="operator-demo",
                        source_endpoint_id="frontend-demo",
                    ),
                    required_capabilities=("demo.echo",),
                )
            )

            dispatcher = RuntimeTaskDispatcher(
                broker=broker,
                task_store=task_store,
                endpoint_registry=service.endpoint_registry,
                gateway=gateway,
                ack_timeout_seconds=5.0,
            )
            service.router.register_handler(RuntimePacketType.SYSTEM, dispatcher.handle_system_packet)

            wait_packet = asyncio.create_task(websocket.recv())
            dispatch_results = await dispatcher.dispatch_once()
            dispatched_raw_packet = await asyncio.wait_for(wait_packet, timeout=3.0)
            dispatched_packet = codec.decode(dispatched_raw_packet)

            dispatch_result = dispatch_results[0]
            task_payload = dispatched_packet.payload.get("task", {})
            task_id = str(task_payload.get("task_id") or "") if isinstance(task_payload, dict) else ""

            print("[dispatch result] dispatched=", dispatch_result.dispatched)
            print("[received task_id]", task_id)

            ack_packet = RuntimePacket.create(
                packet_type=RuntimePacketType.SYSTEM,
                source_endpoint_id="executor-ack-demo",
                target_endpoint_id="dispatcher",
                trace_id="ack-demo-trace-1",
                tenant_id="tenant-demo",
                operator_id="operator-demo",
                payload={
                    "action": "accept_ack",
                    "task_id": task_id,
                    "accepted": True,
                },
            )
            await websocket.send(codec.encode(ack_packet))
            ack_response = codec.decode(await websocket.recv())
            print("[ack response]", ack_response.packet_type.value, ack_response.payload)

            stored_task = task_store.get(submit_result.task.task_id)
            print("[task status]", stored_task.status.value if stored_task else None)

            timeout_submit_result = submitter.submit_task(
                RuntimeTaskSubmitRequest(
                    task_type="demo.echo",
                    payload={"message": "timeout demo"},
                    context=RuntimeTaskContext(
                        trace_id="ack-demo-trace-timeout",
                        tenant_id="tenant-demo",
                        operator_id="operator-demo",
                        source_endpoint_id="frontend-demo",
                    ),
                    required_capabilities=("demo.echo",),
                )
            )

            timeout_dispatcher = RuntimeTaskDispatcher(
                broker=broker,
                task_store=task_store,
                endpoint_registry=service.endpoint_registry,
                gateway=gateway,
                ack_timeout_seconds=0.1,
            )
            wait_timeout_packet = asyncio.create_task(websocket.recv())
            await timeout_dispatcher.dispatch_once()
            await asyncio.wait_for(wait_timeout_packet, timeout=3.0)
            await asyncio.sleep(0.2)
            timeout_results = timeout_dispatcher.requeue_expired_ack()
            if timeout_results:
                print("[timeout]", timeout_results[0].reason)
                timeout_task = task_store.get(timeout_submit_result.task.task_id)
                print("[timeout task status]", timeout_task.status.value if timeout_task else None)
    finally:
        await gateway.stop()
        service.stop()


def main() -> None:
    try:
        asyncio.run(_run_demo())
    except RuntimeError as exc:
        print("[runtime error]", exc)
        print("请先安装 websockets，再执行 task_ack_dispatcher_demo.py。")
    except Exception as exc:
        print("[connection or operation error]", exc)
        print("请确认本地端口可用，且网络环境允许建立 WebSocket 连接。")


if __name__ == "__main__":
    main()

