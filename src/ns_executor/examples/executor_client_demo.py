# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import sys
import time
from importlib import import_module
from pathlib import Path

# 仅用于本地示例直接运行：将 src 目录加入 sys.path，便于 `python src/ns_executor/examples/executor_client_demo.py` 执行。
PROJECT_SRC_PATH = Path(__file__).resolve().parents[2]
if str(PROJECT_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC_PATH))

from ns_common.protocol import RuntimePacket, RuntimePacketType, RuntimeTask  # noqa: E402
from ns_executor import ExecutorClient, ExecutorClientConfig  # noqa: E402
from ns_runtime import (  # noqa: E402
    MemoryBroker,
    MemoryTaskStore,
    RuntimeService,
    RuntimeTaskContext,
    RuntimeTaskDispatcher,
    RuntimeTaskSubmitRequest,
    RuntimeTaskSubmitter,
    WebSocketGateway,
    WebSocketGatewayConfig,
)


async def _run_demo() -> None:
    try:
        client_module = import_module("websockets.asyncio.client")
        getattr(client_module, "connect")
    except (ImportError, AttributeError) as exc:
        raise RuntimeError("websockets is not installed, please install package 'websockets'") from exc

    broker = MemoryBroker()
    service = RuntimeService(broker=broker)
    task_store = MemoryTaskStore()
    gateway = WebSocketGateway(
        runtime_service=service,
        config=WebSocketGatewayConfig(host="127.0.0.1", port=8769, path="/runtime"),
    )
    dispatcher = RuntimeTaskDispatcher(
        broker=broker,
        task_store=task_store,
        endpoint_registry=service.endpoint_registry,
        gateway=gateway,
        ack_timeout_seconds=5.0,
    )

    result_packets: list[RuntimePacket] = []

    def on_result(packet: RuntimePacket) -> RuntimePacket | None:
        result_packets.append(packet)
        print("[result packet received]", packet.payload)
        return RuntimePacket.create(
            packet_type=RuntimePacketType.SYSTEM,
            source_endpoint_id="runtime-demo",
            target_endpoint_id=packet.source_endpoint_id,
            trace_id=packet.trace_id,
            tenant_id=packet.tenant_id,
            operator_id=packet.operator_id,
            payload={
                "ok": True,
                "action": "result_received",
                "task_id": packet.payload.get("task_id"),
            },
        )

    service.router.register_handler(RuntimePacketType.SYSTEM, dispatcher.handle_system_packet)
    service.router.register_handler(RuntimePacketType.RESULT, on_result)

    executor_client = ExecutorClient(
        config=ExecutorClientConfig(
            endpoint_id="executor-client-demo",
            gateway_url="ws://127.0.0.1:8769/runtime",
            capabilities=("demo.echo",),
        )
    )

    def demo_echo_handler(task: RuntimeTask) -> dict[str, str | None]:
        return {"echo": str(task.payload.get("message")) if task.payload.get("message") is not None else None}

    executor_client.register_handler("demo.echo", demo_echo_handler)

    io_process = None
    try:
        await gateway.start()

        io_process = executor_client.start_io_process()
        print("executor io process started", io_process.pid)

        # 给予 IO 子进程短暂时间完成 websocket 建连与 REGISTER。
        await asyncio.sleep(0.8)

        submitter = RuntimeTaskSubmitter(
            broker=broker,
            task_store=task_store,
            use_stream=False,
        )
        submit_result = submitter.submit_task(
            RuntimeTaskSubmitRequest(
                task_type="demo.echo",
                payload={"message": "hello executor client"},
                context=RuntimeTaskContext(
                    trace_id="executor-client-demo-trace-1",
                    tenant_id="tenant-demo",
                    operator_id="operator-demo",
                    source_endpoint_id="frontend-demo",
                ),
                required_capabilities=("demo.echo",),
            )
        )

        dispatch_results = await dispatcher.dispatch_once()
        if not dispatch_results:
            raise RuntimeError("dispatcher returned no result")

        dispatch_result = dispatch_results[0]
        print("dispatch result", dispatch_result.dispatched, dispatch_result.reason)

        accepted = False
        deadline = time.time() + 8.0
        while time.time() < deadline:
            executor_client.run_main_once(timeout_seconds=0.5)
            await asyncio.sleep(0.1)
            stored_task = task_store.get(submit_result.task.task_id)
            if stored_task is not None and stored_task.status.value == "ACCEPTED":
                accepted = True
                print("task status ACCEPTED", stored_task.task_id)
                break

        if not accepted:
            raise RuntimeError("task was not accepted in expected time")

        result_deadline = time.time() + 6.0
        while time.time() < result_deadline and not result_packets:
            await asyncio.sleep(0.1)

        if not result_packets:
            raise RuntimeError("result packet was not received in expected time")

        print("result payload", result_packets[0].payload)
    finally:
        executor_client.stop(io_process)
        await gateway.stop()
        service.stop()


def main() -> None:
    try:
        asyncio.run(_run_demo())
    except RuntimeError as exc:
        print("[runtime error]", exc)
        print("请先安装 websockets，再执行 executor_client_demo.py。")
    except Exception as exc:
        print("[demo error]", exc)
        print("请确认本地端口可用，且进程具备 multiprocessing 与 WebSocket 运行条件。")


if __name__ == "__main__":
    main()

