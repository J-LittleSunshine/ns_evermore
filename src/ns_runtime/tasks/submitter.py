# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Callable, cast

from ns_runtime.brokers import RuntimeBroker
from ns_runtime.packets import RuntimePacket, RuntimePacketCodec, RuntimePacketType
from ns_runtime.tasks.memory import MemoryTaskStore
from ns_runtime.tasks.models import RuntimeTask, RuntimeTaskSubmitRequest, RuntimeTaskSubmitResult
from ns_runtime.tasks.store import RuntimeTaskStore


class RuntimeTaskSubmitter:
    def __init__(
        self,
        broker: RuntimeBroker,
        task_store: RuntimeTaskStore | None = None,
        codec: RuntimePacketCodec | None = None,
        default_topic: str = "runtime.task.queue",
        default_stream: str = "runtime.task.stream",
        use_stream: bool = False,
    ) -> None:
        default_topic_text = str(default_topic).strip()
        default_stream_text = str(default_stream).strip()
        if not default_topic_text:
            raise ValueError("default_topic must be non-empty")
        if not default_stream_text:
            raise ValueError("default_stream must be non-empty")

        self._broker = broker
        self._task_store = task_store or MemoryTaskStore()
        self._codec = codec or RuntimePacketCodec()
        self._default_topic = default_topic_text
        self._default_stream = default_stream_text
        self._use_stream = use_stream

    @property
    def task_store(self) -> RuntimeTaskStore:
        return self._task_store

    def submit_task(self, request: RuntimeTaskSubmitRequest) -> RuntimeTaskSubmitResult:
        created_task = RuntimeTask.create(
            task_type=request.task_type,
            payload=request.payload,
            context=request.context,
            required_capabilities=request.required_capabilities,
            priority=request.priority,
        )
        self._task_store.save(created_task)

        queued_task = created_task.mark_queued()
        self._task_store.save(queued_task)

        topic = request.topic or self._default_topic
        packet = RuntimePacket.create(
            packet_type=RuntimePacketType.TASK,
            source_endpoint_id=request.context.source_endpoint_id,
            topic=topic,
            trace_id=request.context.trace_id,
            tenant_id=request.context.tenant_id,
            operator_id=request.context.operator_id,
            payload={
                "task": queued_task.to_dict(),
            },
        )

        # submitter 仅负责任务入队，不负责后续分发和执行。
        broker_message_id: str | None = None
        if self._use_stream:
            stream = request.stream or self._default_stream
            append_stream = getattr(self._broker, "append_stream", None)
            if not callable(append_stream):
                raise RuntimeError("broker does not support append_stream")
            append_stream_callable = cast(Callable[[str, RuntimePacket], Any], append_stream)
            raw_message_id = append_stream_callable(stream, packet)
            broker_message_id = str(raw_message_id)
        else:
            self._broker.publish(topic, packet)

        return RuntimeTaskSubmitResult(
            task=queued_task,
            packet=packet,
            queued=True,
            broker_message_id=broker_message_id,
        )

