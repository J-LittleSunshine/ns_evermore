# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Mapping

from ns_runtime.brokers import RuntimeBroker
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
    ) -> None:
        task_topic_text = str(task_topic).strip()
        if not task_topic_text:
            raise ValueError("task_topic must be non-empty")
        if max_batch_size <= 0:
            raise ValueError("max_batch_size must be greater than 0")

        self._broker = broker
        self._task_store = task_store
        self._endpoint_registry = endpoint_registry
        self._gateway = gateway
        self._strategy = strategy or CapabilityMatchDispatchStrategy()
        self._task_topic = task_topic_text
        self._max_batch_size = max_batch_size

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

            try:
                sent = await self._gateway.send_packet_to_endpoint(selected_endpoint.endpoint_id, dispatch_packet)
            except Exception:
                sent = False

            if not sent:
                results.append(
                    RuntimeTaskDispatchResult(
                        task=task,
                        packet=dispatch_packet,
                        selected_endpoint=None,
                        dispatched=False,
                        reason="send_failed",
                    )
                )
                continue

            # Phase 6A 中 DISPATCHING 仅表示“已下发到 gateway 目标端点”，不表示 executor 已接收或已 ACK。
            dispatched_task = self._task_store.update_status(task.task_id, RuntimeTaskStatus.DISPATCHING)
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


