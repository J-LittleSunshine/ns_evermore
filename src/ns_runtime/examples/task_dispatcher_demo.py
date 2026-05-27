# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import sys
from importlib import import_module
from pathlib import Path

# 仅用于本地示例直接运行：将 src 目录加入 sys.path，便于 `python src/ns_runtime/examples/task_dispatcher_demo.py` 执行。
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
        config=WebSocketGatewayConfig(host="127.0.0.1", port=8766, path="/runtime"),
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
                source_endpoint_id="executor-demo",
                payload={
                    "endpoint_id": "executor-demo",
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
                    payload={"message": "hello dispatcher"},
                    context=RuntimeTaskContext(
                        trace_id="dispatcher-demo-trace-1",
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
                task_topic="runtime.task.queue",
                max_batch_size=1,
            )

            receive_task = asyncio.create_task(websocket.recv())
            dispatch_results = await dispatcher.dispatch_once()
            raw_dispatched_packet = await asyncio.wait_for(receive_task, timeout=3.0)
            dispatched_packet = codec.decode(raw_dispatched_packet)

            if not dispatch_results:
                print("[dispatcher] no result")
                return

            dispatch_result = dispatch_results[0]
            print("[dispatcher result] dispatched=", dispatch_result.dispatched)
            print(
                "[dispatcher result] selected_endpoint_id=",
                dispatch_result.selected_endpoint.endpoint_id if dispatch_result.selected_endpoint else None,
            )

            task_payload = dispatched_packet.payload.get("task", {})
            if isinstance(task_payload, dict):
                print("[executor received] task_id=", task_payload.get("task_id"))
                print("[executor received] task_type=", task_payload.get("task_type"))
            else:
                print("[executor received] invalid task payload")

            stored_task = task_store.get(submit_result.task.task_id)
            print(
                "[task store]",
                stored_task.task_id if stored_task else None,
                stored_task.status.value if stored_task else None,
            )
    finally:
        await gateway.stop()
        service.stop()


def main() -> None:
    try:
        asyncio.run(_run_demo())
    except RuntimeError as exc:
        print("[runtime error]", exc)
        print("请先安装 websockets，再执行 task_dispatcher_demo.py。")
    except Exception as exc:
        print("[connection or operation error]", exc)
        print("请确认本地端口可用，且网络环境允许建立 WebSocket 连接。")


if __name__ == "__main__":
    main()


