# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from ns_runtime.brokers import RuntimeBroker
from ns_runtime.dispatching.ack import MemoryTaskAckRegistry, RuntimeTaskAckRegistry, RuntimeTaskPendingDispatch
from ns_runtime.dispatching.models import RuntimeTaskDispatchResult
from ns_runtime.dispatching.strategies import CapabilityMatchDispatchStrategy, RuntimeTaskDispatchStrategy
from ns_runtime.endpoints import EndpointRegistry
from ns_runtime.gateway import WebSocketGateway
from ns_runtime.packets import RuntimePacket, RuntimePacketType
from ns_runtime.tasks import RuntimeTask, RuntimeTaskContext, RuntimeTaskStatus, RuntimeTaskStore


class RuntimeTaskDispatcher:
    def __init__(
        self,
        broker: RuntimeBroker,
        task_store: RuntimeTaskStore,
        endpoint_registry: EndpointRegistry,
        gateway: WebSocketGateway,
        strategy: RuntimeTaskDispatchStrategy | None = None,
        task_topic: str = "runtime.task.queue",
        max_batch_size: int = 1,
        ack_registry: RuntimeTaskAckRegistry | None = None,
        ack_timeout_seconds: float = 10.0,
    ) -> None:
        task_topic_text = str(task_topic).strip()
        if not task_topic_text:
            raise ValueError("task_topic must be non-empty")
        if max_batch_size <= 0:
            raise ValueError("max_batch_size must be greater than 0")
        if ack_timeout_seconds <= 0:
            raise ValueError("ack_timeout_seconds must be greater than 0")

        self._broker = broker
        self._task_store = task_store
        self._endpoint_registry = endpoint_registry
        self._gateway = gateway
        self._strategy = strategy or CapabilityMatchDispatchStrategy()
        self._task_topic = task_topic_text
        self._max_batch_size = max_batch_size
        self._ack_registry = ack_registry or MemoryTaskAckRegistry()
        self._ack_timeout_seconds = float(ack_timeout_seconds)

    async def dispatch_once(self) -> tuple[RuntimeTaskDispatchResult, ...]:
        packets = self._broker.poll(self._task_topic, self._max_batch_size)
        if not packets:
            return ()

        results: list[RuntimeTaskDispatchResult] = []
        for packet in packets:
            if packet.packet_type != RuntimePacketType.TASK:
                fallback_task = self._build_fallback_task(packet)
                results.append(
                    RuntimeTaskDispatchResult(
                        task=fallback_task,
                        packet=packet,
                        selected_endpoint=None,
                        dispatched=False,
                        reason="not_task_packet",
                    )
                )
                continue

            task_payload = packet.payload.get("task")
            if not isinstance(task_payload, Mapping):
                fallback_task = self._build_fallback_task(packet)
                results.append(
                    RuntimeTaskDispatchResult(
                        task=fallback_task,
                        packet=packet,
                        selected_endpoint=None,
                        dispatched=False,
                        reason="invalid_task_payload",
                    )
                )
                continue

            try:
                task = RuntimeTask.from_dict(task_payload)
            except ValueError:
                fallback_task = self._build_fallback_task(packet, task_payload=task_payload)
                results.append(
                    RuntimeTaskDispatchResult(
                        task=fallback_task,
                        packet=packet,
                        selected_endpoint=None,
                        dispatched=False,
                        reason="invalid_task_payload",
                    )
                )
                continue

            endpoints = self._endpoint_registry.list_all()
            selected_endpoint = self._strategy.select_endpoint(task, endpoints)
            if selected_endpoint is None:
                self._requeue_task_packet(packet)
                results.append(
                    RuntimeTaskDispatchResult(
                        task=task,
                        packet=packet,
                        selected_endpoint=None,
                        dispatched=False,
                        reason="no_matched_executor",
                    )
                )
                continue

            dispatch_packet = RuntimePacket.create(
                packet_type=RuntimePacketType.TASK,
                source_endpoint_id="dispatcher",
                target_endpoint_id=selected_endpoint.endpoint_id,
                topic=packet.topic,
                trace_id=task.context.trace_id,
                tenant_id=task.context.tenant_id,
                operator_id=task.context.operator_id,
                payload={
                    "task": task.to_dict(),
                    "dispatch": {
                        "selected_endpoint_id": selected_endpoint.endpoint_id,
                    },
                },
            )

            send_error_detail: str | None = None
            try:
                sent = await self._gateway.send_packet_to_endpoint(selected_endpoint.endpoint_id, dispatch_packet)
            except Exception as exc:
                sent = False
                # 保留 send 异常细节，避免失败路径完全静默，便于调用方诊断下发失败原因。
                send_error_detail = str(exc)

            if not sent:
                self._requeue_task_packet(packet)
                result_packet = dispatch_packet
                if send_error_detail:
                    result_packet = RuntimePacket.create(
                        packet_type=dispatch_packet.packet_type,
                        source_endpoint_id=dispatch_packet.source_endpoint_id,
                        target_endpoint_id=dispatch_packet.target_endpoint_id,
                        topic=dispatch_packet.topic,
                        trace_id=dispatch_packet.trace_id,
                        tenant_id=dispatch_packet.tenant_id,
                        operator_id=dispatch_packet.operator_id,
                        payload={
                            **dispatch_packet.payload,
                            "dispatch": {
                                "selected_endpoint_id": selected_endpoint.endpoint_id,
                                "send_error": send_error_detail,
                            },
                        },
                    )
                results.append(
                    RuntimeTaskDispatchResult(
                        task=task,
                        packet=result_packet,
                        selected_endpoint=selected_endpoint,
                        dispatched=False,
                        reason="send_failed",
                    )
                )
                continue

            # Phase 6B 中 DISPATCHING 表示“已下发且等待 accept_ack”，不表示任务已进入执行态。
            dispatched_task = self._task_store.update_status(task.task_id, RuntimeTaskStatus.DISPATCHING)
            dispatched_at = datetime.now(timezone.utc)
            pending = RuntimeTaskPendingDispatch(
                task_id=task.task_id,
                executor_endpoint_id=selected_endpoint.endpoint_id,
                original_task_packet=packet,
                dispatch_packet=dispatch_packet,
                dispatched_at=dispatched_at,
                deadline_at=dispatched_at + timedelta(seconds=self._ack_timeout_seconds),
                dispatch_attempts=1,
            )
            # Phase 6B 中 DISPATCHING 表示任务已下发，正在等待 executor accept_ack。
            self._ack_registry.register_pending(pending)
            results.append(
                RuntimeTaskDispatchResult(
                    task=dispatched_task,
                    packet=dispatch_packet,
                    selected_endpoint=selected_endpoint,
                    dispatched=True,
                    reason=None,
                )
            )

        return tuple(results)

    def _requeue_task_packet(self, packet: RuntimePacket) -> None:
        # Phase 6A 只做失败保留：将原始 TASK 消息放回队列，不做 retry 计数、backoff 或 DLQ。
        self._broker.publish(self._task_topic, packet)

    def handle_accept_ack(self, packet: RuntimePacket) -> RuntimeTaskDispatchResult | None:
        if packet.packet_type != RuntimePacketType.SYSTEM:
            return None

        action = str(packet.payload.get("action") or "").strip()
        if action != "accept_ack":
            return None

        task_id = str(packet.payload.get("task_id") or "").strip()
        executor_endpoint_id = str(packet.source_endpoint_id or "").strip()
        if not task_id:
            raise ValueError("accept_ack payload.task_id is required")
        if not executor_endpoint_id:
            raise ValueError("accept_ack source_endpoint_id is required")

        self._ack_registry.accept(task_id, executor_endpoint_id)
        accepted_task = self._task_store.update_status(task_id, RuntimeTaskStatus.ACCEPTED)
        return RuntimeTaskDispatchResult(
            task=accepted_task,
            packet=packet,
            selected_endpoint=None,
            dispatched=True,
            reason="accepted",
        )

    def requeue_expired_ack(self, now: datetime | None = None) -> tuple[RuntimeTaskDispatchResult, ...]:
        expired_items = self._ack_registry.list_expired(now)
        results: list[RuntimeTaskDispatchResult] = []
        for pending in expired_items:
            removed = self._ack_registry.remove(pending.task_id)
            if removed is None:
                continue

            queued_task = self._task_store.update_status(removed.task_id, RuntimeTaskStatus.QUEUED)
            # Phase 6B 只做 ACK 超时回收：恢复 QUEUED 并回队，不做完整 retry/backoff/DLQ 策略。
            self._broker.publish(self._task_topic, removed.original_task_packet)
            results.append(
                RuntimeTaskDispatchResult(
                    task=queued_task,
                    packet=removed.original_task_packet,
                    selected_endpoint=None,
                    dispatched=False,
                    reason="ack_timeout_requeued",
                )
            )

        return tuple(results)

    @staticmethod
    def _build_fallback_task(packet: RuntimePacket, task_payload: Mapping[str, Any] | None = None) -> RuntimeTask:
        payload_dict: dict[str, Any] = {
            "invalid_task_payload": True,
            "packet_id": packet.packet_id,
        }
        if task_payload is not None:
            payload_dict["task_payload"] = dict(task_payload)

        context = RuntimeTaskContext(
            tenant_id=packet.tenant_id,
            operator_id=packet.operator_id,
            trace_id=packet.trace_id,
            source_endpoint_id=packet.source_endpoint_id,
        )
        return RuntimeTask.create(
            task_type="invalid_task_payload",
            payload=payload_dict,
            context=context,
        )


