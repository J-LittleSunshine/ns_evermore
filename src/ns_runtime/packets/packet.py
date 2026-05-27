# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

from ns_runtime.packets.enums import RuntimePacketType


@dataclass(frozen=True)
class RuntimePacket:
    packet_id: str
    packet_type: RuntimePacketType
    source_endpoint_id: str | None
    target_endpoint_id: str | None
    topic: str | None
    trace_id: str | None
    tenant_id: str | None
    operator_id: str | None
    payload: dict[str, Any]
    headers: dict[str, str]
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        packet_type: RuntimePacketType,
        source_endpoint_id: str | None = None,
        target_endpoint_id: str | None = None,
        topic: str | None = None,
        trace_id: str | None = None,
        tenant_id: str | None = None,
        operator_id: str | None = None,
        payload: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> RuntimePacket:
        payload_dict = dict(payload or {})
        if not isinstance(payload_dict, dict):
            raise ValueError("payload must be dict")

        # tenant_id/operator_id/trace_id 是平台级上下文字段，用于租户、操作者和链路追踪透传。
        normalized_headers = {str(key): str(value) for key, value in (headers or {}).items()}
        return cls(
            packet_id=uuid4().hex,
            packet_type=packet_type,
            source_endpoint_id=source_endpoint_id,
            target_endpoint_id=target_endpoint_id,
            topic=topic,
            trace_id=trace_id,
            tenant_id=tenant_id,
            operator_id=operator_id,
            payload=payload_dict,
            headers=normalized_headers,
            created_at=datetime.now(timezone.utc),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "packet_type": self.packet_type.value,
            "source_endpoint_id": self.source_endpoint_id,
            "target_endpoint_id": self.target_endpoint_id,
            "topic": self.topic,
            "trace_id": self.trace_id,
            "tenant_id": self.tenant_id,
            "operator_id": self.operator_id,
            "payload": dict(self.payload),
            "headers": dict(self.headers),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> RuntimePacket:
        raw_payload = data.get("payload", {})
        if not isinstance(raw_payload, dict):
            raise ValueError("payload must be dict")

        raw_headers = data.get("headers", {})
        if isinstance(raw_headers, Mapping):
            headers = {str(key): str(value) for key, value in raw_headers.items()}
        else:
            raise ValueError("headers must be mapping")

        raw_created_at = data.get("created_at")
        if not isinstance(raw_created_at, str) or not raw_created_at.strip():
            raise ValueError("created_at must be ISO 8601 string")

        created_at_text = raw_created_at.strip().replace("Z", "+00:00")
        try:
            created_at = datetime.fromisoformat(created_at_text)
        except ValueError as exc:
            raise ValueError(f"invalid created_at: {raw_created_at}") from exc

        return cls(
            packet_id=str(data.get("packet_id") or "").strip(),
            packet_type=RuntimePacketType(str(data.get("packet_type") or "")),
            source_endpoint_id=_to_optional_str(data.get("source_endpoint_id")),
            target_endpoint_id=_to_optional_str(data.get("target_endpoint_id")),
            topic=_to_optional_str(data.get("topic")),
            trace_id=_to_optional_str(data.get("trace_id")),
            tenant_id=_to_optional_str(data.get("tenant_id")),
            operator_id=_to_optional_str(data.get("operator_id")),
            payload=dict(raw_payload),
            headers=headers,
            created_at=created_at,
        )


def _to_optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None

