# -*- coding: utf-8 -*-
from __future__ import annotations

from multiprocessing.queues import Queue as MpQueue
from queue import Empty

from ns_common.protocol import RuntimePacket, RuntimePacketType, RuntimeTask
from ns_executor.config import ExecutorClientConfig
from ns_executor.handlers import TaskHandlerRegistry
from ns_executor.ipc import ExecutorIpcMessage, ExecutorIpcMessageType


class ExecutorMainProcessRunner:
    def __init__(
        self,
        config: ExecutorClientConfig,
        handler_registry: TaskHandlerRegistry,
        inbound_queue: MpQueue,
        outbound_queue: MpQueue,
    ) -> None:
        self._config = config
        self._handler_registry = handler_registry
        self._inbound_queue = inbound_queue
        self._outbound_queue = outbound_queue
        self._stopped = False

    @property
    def stopped(self) -> bool:
        return self._stopped

    def run_once(self, timeout_seconds: float = 1.0) -> bool:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")

        try:
            raw_message = self._inbound_queue.get(True, timeout_seconds)
        except Empty:
            return False

        try:
            message = ExecutorIpcMessage.from_dict(raw_message)
        except Exception as exc:
            print(f"[executor main] invalid inbound ipc message: {exc}")
            return True

        if message.message_type == ExecutorIpcMessageType.STOP:
            self._stopped = True
            return True

        if message.message_type != ExecutorIpcMessageType.PACKET:
            return True

        if message.packet is None:
            return True

        try:
            packet = RuntimePacket.from_dict(message.packet)
        except Exception as exc:
            print(f"[executor main] invalid packet payload: {exc}")
            return True

        if packet.packet_type != RuntimePacketType.TASK:
            return True

        task_payload = packet.payload.get("task")
        if not isinstance(task_payload, dict):
            print("[executor main] missing task payload")
            return True

        try:
            task = RuntimeTask.from_dict(task_payload)
        except Exception as exc:
            print(f"[executor main] invalid task payload: {exc}")
            return True

        # 主进程负责 CPU/阻塞型 handler 调用，IO 子进程只负责网络收发与重连。
        accept_ack_packet = RuntimePacket.create(
            packet_type=RuntimePacketType.SYSTEM,
            source_endpoint_id=self._config.endpoint_id,
            target_endpoint_id="dispatcher",
            trace_id=task.context.trace_id,
            tenant_id=task.context.tenant_id,
            operator_id=task.context.operator_id,
            payload={
                "action": "accept_ack",
                "task_id": task.task_id,
                "accepted": True,
            },
        )
        self._outbound_queue.put(ExecutorIpcMessage.from_packet(accept_ack_packet).to_dict())

        try:
            handler_result = self._handler_registry.handle(task)
            result_packet = RuntimePacket.create(
                packet_type=RuntimePacketType.RESULT,
                source_endpoint_id=self._config.endpoint_id,
                target_endpoint_id="dispatcher",
                trace_id=task.context.trace_id,
                tenant_id=task.context.tenant_id,
                operator_id=task.context.operator_id,
                payload={
                    "task_id": task.task_id,
                    "ok": True,
                    "result": dict(handler_result or {}),
                },
            )
            self._outbound_queue.put(ExecutorIpcMessage.from_packet(result_packet).to_dict())
        except Exception as exc:
            error_packet = RuntimePacket.create(
                packet_type=RuntimePacketType.ERROR,
                source_endpoint_id=self._config.endpoint_id,
                target_endpoint_id="dispatcher",
                trace_id=task.context.trace_id,
                tenant_id=task.context.tenant_id,
                operator_id=task.context.operator_id,
                payload={
                    "task_id": task.task_id,
                    "ok": False,
                    "error_message": str(exc),
                },
            )
            self._outbound_queue.put(ExecutorIpcMessage.from_packet(error_packet).to_dict())

        return True

    def run_forever(self) -> None:
        while not self._stopped:
            self.run_once(timeout_seconds=1.0)

    def stop(self) -> None:
        self._stopped = True

        stop_message = ExecutorIpcMessage.stop().to_dict()
        self._outbound_queue.put(dict(stop_message))
        self._inbound_queue.put(dict(stop_message))


