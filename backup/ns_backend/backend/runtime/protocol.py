# -*- coding: utf-8 -*-
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

from ns_common.runtime.errors import NsRuntimeValidationError
from ns_common.runtime.messages import NsRuntimeAck, NsRuntimeMessage

BackendRuntimeFrameType = Literal[
    "backend.register",
    "backend.heartbeat",
    "backend.publish",
    "backend.deliver",
    "ack",
]


@dataclass(slots=True, frozen=True, kw_only=True)
class NsBackendRuntimeFrame:
    """Wire frame exchanged between backend runtime connector and ns_runtime."""

    frame_type: BackendRuntimeFrameType
    message_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    trace_id: str | None = None
    created_at_epoch_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize wire frame."""
        frame_type: str = str(self.frame_type or "").strip()
        if not frame_type:
            raise NsRuntimeValidationError("runtime frame_type is required")

        message_id: str = str(self.message_id or "").strip()
        if not message_id:
            raise NsRuntimeValidationError("runtime frame message_id is required")

        return {
            "type": frame_type,
            "message_id": message_id,
            "trace_id": self.trace_id,
            "created_at_epoch_ms": int(self.created_at_epoch_ms),
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NsBackendRuntimeFrame":
        """Deserialize wire frame."""
        if not isinstance(data, dict):
            raise NsRuntimeValidationError("runtime frame must be a JSON object")

        frame_type: str = str(data.get("type") or "").strip()
        if not frame_type:
            raise NsRuntimeValidationError("runtime frame type is required")

        payload_raw = data.get("payload") or {}
        if not isinstance(payload_raw, dict):
            raise NsRuntimeValidationError("runtime frame payload must be a JSON object")

        return cls(
            frame_type=frame_type,  # type: ignore[arg-type]
            message_id=str(data.get("message_id") or "").strip() or uuid.uuid4().hex,
            trace_id=str(data.get("trace_id")).strip() if data.get("trace_id") is not None and str(data.get("trace_id")).strip() else None,
            created_at_epoch_ms=int(data.get("created_at_epoch_ms") or int(time.time() * 1000)),
            payload=dict(payload_raw),
        )


def build_backend_register_frame(*, node_id: str, service_name: str = "ns_backend", version: str = "", environment: str = "", auth_token: str | None = None) -> NsBackendRuntimeFrame:
    """Build backend.register frame."""
    payload: dict[str, Any] = {
        "instance_id": node_id,
        "service_name": service_name,
        "version": version,
        "environment": environment,
        "capabilities": [
            "health_report",
            "business_publish",
            "outbox_drain",
            "backend_inbox",
            "request_reply_inbound",
        ],
    }

    normalized_auth_token = str(auth_token or "").strip()
    if normalized_auth_token:
        payload["auth"] = {
            "scheme": "bearer",
            "token": normalized_auth_token,
        }

    return NsBackendRuntimeFrame(
        frame_type="backend.register",
        payload=payload,
    )


def build_backend_heartbeat_frame(*, node_id: str, health: dict[str, Any] | None = None) -> NsBackendRuntimeFrame:
    """Build backend.heartbeat frame."""
    return NsBackendRuntimeFrame(
        frame_type="backend.heartbeat",
        payload={
            "instance_id": node_id,
            "status": "healthy",
            "health": health or {},
        },
    )


def build_backend_publish_frame(message: NsRuntimeMessage) -> NsBackendRuntimeFrame:
    """Build backend.publish frame from runtime message."""
    normalized_message: NsRuntimeMessage = message.normalized()
    return NsBackendRuntimeFrame(
        frame_type="backend.publish",
        message_id=str(normalized_message.message_id),
        trace_id=normalized_message.trace_id,
        created_at_epoch_ms=int(normalized_message.created_at_epoch_ms or int(time.time() * 1000)),
        payload=normalized_message.to_dict(),
    )


def build_backend_ack_frame(ack: NsRuntimeAck) -> NsBackendRuntimeFrame:
    """Build generic ack frame from backend connector to ns_runtime."""
    normalized_ack = ack.normalized()
    return NsBackendRuntimeFrame(
        frame_type="ack",
        message_id=normalized_ack.message_id,
        trace_id=normalized_ack.trace_id,
        payload=normalized_ack.to_dict(),
    )


def build_backend_deliver_frame(
        *,
        message: NsRuntimeMessage,
        correlation_id: str | None = None,
        reply_to_message_id: str | None = None,
        source_node_id: str | None = None,
) -> NsBackendRuntimeFrame:
    """Build backend.deliver frame from runtime to backend connector."""
    normalized_message = message.normalized()
    normalized_correlation_id = str(correlation_id).strip() if correlation_id is not None and str(correlation_id).strip() else normalized_message.headers.get("correlation_id")
    normalized_reply_to_message_id = str(reply_to_message_id).strip() if reply_to_message_id is not None and str(reply_to_message_id).strip() else normalized_message.headers.get("reply_to_message_id")

    return NsBackendRuntimeFrame(
        frame_type="backend.deliver",
        message_id=str(normalized_message.message_id),
        trace_id=normalized_message.trace_id,
        created_at_epoch_ms=int(normalized_message.created_at_epoch_ms or int(time.time() * 1000)),
        payload={
            "source_node_id": str(source_node_id).strip() if source_node_id is not None and str(source_node_id).strip() else None,
            "correlation_id": normalized_correlation_id,
            "reply_to_message_id": normalized_reply_to_message_id,
            "message": normalized_message.to_dict(),
        },
    )


def parse_ack_frame(data: dict[str, Any]) -> NsRuntimeAck:
    """Parse runtime ack frame."""
    frame: NsBackendRuntimeFrame = NsBackendRuntimeFrame.from_dict(data)

    if frame.frame_type != "ack":
        raise NsRuntimeValidationError(f"runtime frame is not ack: {frame.frame_type}")

    payload: dict[str, Any] = dict(frame.payload)
    return NsRuntimeAck(
        message_id=str(payload.get("message_id") or frame.message_id),
        status=str(payload.get("status") or "accepted"),  # type: ignore[arg-type]
        reason=str(payload.get("reason")).strip() if payload.get("reason") is not None and str(payload.get("reason")).strip() else None,
        handled_by=str(payload.get("handled_by")).strip() if payload.get("handled_by") is not None and str(payload.get("handled_by")).strip() else None,
        trace_id=frame.trace_id,
        acked_at_epoch_ms=int(payload.get("acked_at_epoch_ms") or int(time.time() * 1000)),
    ).normalized()


def parse_backend_deliver_frame(data: dict[str, Any]) -> tuple[NsRuntimeMessage, str | None, str | None]:
    """Parse backend.deliver frame into runtime message and reply metadata."""
    frame = NsBackendRuntimeFrame.from_dict(data)
    if frame.frame_type != "backend.deliver":
        raise NsRuntimeValidationError(f"runtime frame is not backend.deliver: {frame.frame_type}")

    payload = dict(frame.payload)
    message_payload = payload.get("message") or {}
    if not isinstance(message_payload, dict):
        raise NsRuntimeValidationError("backend.deliver payload.message must be a JSON object")

    message = _runtime_message_from_payload(dict(message_payload))
    correlation_id = _normalize_optional(payload.get("correlation_id")) or message.headers.get("correlation_id")
    reply_to_message_id = _normalize_optional(payload.get("reply_to_message_id")) or message.headers.get("reply_to_message_id")
    return message, correlation_id, reply_to_message_id


def _runtime_message_from_payload(payload: dict[str, Any]) -> NsRuntimeMessage:
    """Build NsRuntimeMessage from serialized message payload."""
    target = dict(payload.get("target") or {})
    producer = dict(payload.get("producer") or {})

    message_payload = payload.get("payload") or {}
    if not isinstance(message_payload, dict):
        raise NsRuntimeValidationError("runtime message payload.payload must be a JSON object")

    headers = payload.get("headers") or {}
    if not isinstance(headers, dict):
        raise NsRuntimeValidationError("runtime message payload.headers must be a JSON object")

    return NsRuntimeMessage(
        topic=str(payload.get("topic") or ""),
        event=str(payload.get("event") or ""),
        payload=dict(message_payload),
        target_type=str(target.get("type") or "user"),  # type: ignore[arg-type]
        target_id=target.get("id"),
        producer_type=str(producer.get("type") or "runtime"),  # type: ignore[arg-type]
        producer_id=str(producer.get("id")).strip() if producer.get("id") is not None and str(producer.get("id")).strip() else None,
        message_id=str(payload.get("message_id") or ""),
        trace_id=_normalize_optional(payload.get("trace_id")),
        idempotency_key=_normalize_optional(payload.get("idempotency_key")),
        ttl_seconds=payload.get("ttl_seconds"),
        require_ack=bool(payload.get("require_ack", True)),
        created_at_epoch_ms=int(payload.get("created_at_epoch_ms") or int(time.time() * 1000)),
        headers={str(key).strip(): str(value).strip() for key, value in headers.items() if str(key).strip()},
    ).normalized()


def _normalize_optional(value: Any) -> str | None:
    """Normalize optional string."""
    if value is None:
        return None

    normalized = str(value).strip()
    return normalized or None
