# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import (
    asdict,
    dataclass,
    field,
)
from typing import Any

from ns_runtime.protocol.constants import (
    BACKPRESSURE_TIMEOUT_QUEUE,
    DELIVERY_MODE_AT_LEAST_ONCE,
    MESSAGE_TYPE_REQUEST,
    REPLY_MODE_SYNC,
    RUNTIME_PROTOCOL_VERSION,
    RuntimeBackpressurePolicy,
    RuntimeClientType,
    RuntimeDeliveryMode,
    RuntimeMessageType,
    RuntimeReplyMode,
    RuntimeTargetType,
)


@dataclass(slots=True, kw_only=True)
class RuntimeRouteContext:
    hop_count: int = 0
    max_hops: int = 8
    route_trace: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, raw: dict[str, Any] | None) -> "RuntimeRouteContext":
        if raw is None:
            return cls()

        if not isinstance(raw, dict):
            raise TypeError("route_context must be a dict.")

        data = dict(raw)
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True, kw_only=True)
class RuntimeAttachment:
    type: str
    storage: str | None = None
    bucket: str | None = None
    object_key: str | None = None
    content_type: str | None = None
    size_bytes: int | None = None
    checksum: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> "RuntimeAttachment":
        if not isinstance(raw, dict):
            raise TypeError("attachment item must be a dict.")

        data = dict(raw)
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True, kw_only=True)
class RuntimeEnvelope:
    protocol_version: str = RUNTIME_PROTOCOL_VERSION

    message_id: str
    correlation_id: str | None = None

    message_type: RuntimeMessageType = MESSAGE_TYPE_REQUEST
    client_type: RuntimeClientType = "biz_client"
    target_type: RuntimeTargetType = "biz_client"

    target_id: str | None = None
    node_id: str | None = None
    node_name: str | None = None
    node_group: str | None = None

    action: str | None = None

    reply_mode: RuntimeReplyMode = REPLY_MODE_SYNC
    delivery_mode: RuntimeDeliveryMode = DELIVERY_MODE_AT_LEAST_ONCE
    backpressure_policy: RuntimeBackpressurePolicy = BACKPRESSURE_TIMEOUT_QUEUE

    priority: int = 5
    ordering_key: str | None = None
    timeout_ms: int = 30000
    queue_timeout_ms: int | None = None

    codec: str = "json"

    metadata: dict[str, Any] = field(default_factory=dict)
    route_context: RuntimeRouteContext = field(default_factory=RuntimeRouteContext)
    payload: Any = field(default_factory=dict)
    attachments: list[RuntimeAttachment] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> "RuntimeEnvelope":
        if not isinstance(raw, dict):
            raise TypeError("runtime envelope must be a dict.")

        data = dict(raw)

        route_context_raw = data.pop("route_context", None)
        attachments_raw = data.pop("attachments", [])

        if attachments_raw is None:
            attachments_raw = []

        if not isinstance(attachments_raw, list):
            raise TypeError("attachments must be a list.")

        return cls(
            route_context=RuntimeRouteContext.from_mapping(route_context_raw),
            attachments=[RuntimeAttachment.from_mapping(item) for item in attachments_raw],
            **data,
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return data

    def with_hop(self, *, runtime_id: str, action: str, node_id: str | None = None) -> "RuntimeEnvelope":
        trace_item = {
            "runtime_id": runtime_id,
            "action": action,
        }
        if node_id:
            trace_item["node_id"] = node_id

        route_context = RuntimeRouteContext(
            hop_count=self.route_context.hop_count + 1,
            max_hops=self.route_context.max_hops,
            route_trace=[
                *self.route_context.route_trace,
                trace_item,
            ],
        )

        data = self.to_dict()
        data["route_context"] = route_context.to_dict()
        return RuntimeEnvelope.from_mapping(data)
