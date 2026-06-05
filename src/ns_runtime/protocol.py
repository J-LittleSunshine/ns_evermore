# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

from ns_common.runtime.errors import NsRuntimeValidationError
from ns_common.runtime.messages import NsRuntimeAck, NsRuntimeMessage

RuntimeWireFrameType = Literal[
    "backend.register",
    "backend.heartbeat",
    "backend.publish",
    "runtime.register",
    "runtime.heartbeat",
    "runtime.forward",
    "ack",
]

RUNTIME_FRAME_BACKEND_REGISTER = "backend.register"
RUNTIME_FRAME_BACKEND_HEARTBEAT = "backend.heartbeat"
RUNTIME_FRAME_BACKEND_PUBLISH = "backend.publish"
RUNTIME_FRAME_RUNTIME_REGISTER = "runtime.register"
RUNTIME_FRAME_RUNTIME_HEARTBEAT = "runtime.heartbeat"
RUNTIME_FRAME_RUNTIME_FORWARD = "runtime.forward"
RUNTIME_FRAME_ACK = "ack"


@dataclass(slots=True, frozen=True, kw_only=True)
class NsRuntimeWireFrame:
    """Wire frame exchanged by backend connectors and runtime nodes."""

    frame_type: str
    message_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    trace_id: str | None = None
    created_at_epoch_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    payload: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NsRuntimeWireFrame":
        """Deserialize one runtime wire frame."""
        if not isinstance(data, dict):
            raise NsRuntimeValidationError("runtime wire frame must be a JSON object")

        frame_type: str = str(data.get("type") or "").strip()
        if not frame_type:
            raise NsRuntimeValidationError("runtime wire frame type is required")

        payload_raw: Any = data.get("payload") or {}
        if not isinstance(payload_raw, dict):
            raise NsRuntimeValidationError("runtime wire frame payload must be a JSON object")

        return cls(
            frame_type=frame_type,
            message_id=str(data.get("message_id") or "").strip() or uuid.uuid4().hex,
            trace_id=str(data.get("trace_id")).strip() if data.get("trace_id") is not None and str(data.get("trace_id")).strip() else None,
            created_at_epoch_ms=int(data.get("created_at_epoch_ms") or int(time.time() * 1000)),
            payload=dict(payload_raw),
        )

    @classmethod
    def from_json(cls, raw_message: str | bytes) -> "NsRuntimeWireFrame":
        """Deserialize one runtime wire frame from JSON text."""
        if isinstance(raw_message, bytes):
            raw_text: str = raw_message.decode("utf-8")
        else:
            raw_text = str(raw_message)

        try:
            data: Any = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise NsRuntimeValidationError("runtime websocket frame is invalid JSON") from exc

        if not isinstance(data, dict):
            raise NsRuntimeValidationError("runtime websocket frame must be a JSON object")

        return cls.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        """Serialize runtime wire frame to dict."""
        frame_type: str = str(self.frame_type or "").strip()
        if not frame_type:
            raise NsRuntimeValidationError("runtime wire frame type is required")

        message_id: str = str(self.message_id or "").strip()
        if not message_id:
            raise NsRuntimeValidationError("runtime wire frame message_id is required")

        return {
            "type": frame_type,
            "message_id": message_id,
            "trace_id": self.trace_id,
            "created_at_epoch_ms": int(self.created_at_epoch_ms),
            "payload": dict(self.payload),
        }

    def to_json(self) -> str:
        """Serialize runtime wire frame to compact JSON text."""
        return json.dumps(self.to_dict(), ensure_ascii=False, separators=(",", ":"))


def build_ack_frame(ack: NsRuntimeAck) -> NsRuntimeWireFrame:
    """Build generic ack wire frame."""
    normalized_ack: NsRuntimeAck = ack.normalized()
    return NsRuntimeWireFrame(
        frame_type=RUNTIME_FRAME_ACK,
        message_id=normalized_ack.message_id,
        trace_id=normalized_ack.trace_id,
        payload=normalized_ack.to_dict(),
    )


def parse_ack_frame(frame: NsRuntimeWireFrame) -> NsRuntimeAck:
    """Parse generic ack wire frame."""
    if frame.frame_type != RUNTIME_FRAME_ACK:
        raise NsRuntimeValidationError(f"runtime frame is not ack: {frame.frame_type}")

    payload: dict[str, Any] = dict(frame.payload)
    return NsRuntimeAck(
        message_id=str(payload.get("message_id") or frame.message_id),
        status=str(payload.get("status") or "accepted"),  # type: ignore[arg-type]
        reason=str(payload.get("reason")).strip() if payload.get("reason") is not None and str(payload.get("reason")).strip() else None,
        handled_by=str(payload.get("handled_by")).strip() if payload.get("handled_by") is not None and str(payload.get("handled_by")).strip() else None,
        trace_id=str(payload.get("trace_id") or frame.trace_id).strip() if payload.get("trace_id") is not None or frame.trace_id is not None else None,
        acked_at_epoch_ms=int(payload.get("acked_at_epoch_ms") or int(time.time() * 1000)),
    ).normalized()


def build_runtime_register_frame(*, node_id: str, node_role: str, parent_node_id: str | None = None) -> NsRuntimeWireFrame:
    """Build runtime.register frame for sub node registration."""
    return NsRuntimeWireFrame(
        frame_type=RUNTIME_FRAME_RUNTIME_REGISTER,
        payload={
            "node_id": str(node_id or "").strip(),
            "node_role": str(node_role or "").strip(),
            "parent_node_id": str(parent_node_id).strip() if parent_node_id is not None and str(parent_node_id).strip() else None,
            "capabilities": [
                "backend_publish_forward",
            ],
        },
    )


def build_runtime_heartbeat_frame(*, node_id: str, node_role: str, health: dict[str, Any] | None = None) -> NsRuntimeWireFrame:
    """Build runtime.heartbeat frame for sub node health reports."""
    return NsRuntimeWireFrame(
        frame_type=RUNTIME_FRAME_RUNTIME_HEARTBEAT,
        payload={
            "node_id": str(node_id or "").strip(),
            "node_role": str(node_role or "").strip(),
            "status": "healthy",
            "health": health or {},
        },
    )


def build_runtime_forward_frame(*, source_node_id: str, message: NsRuntimeMessage) -> NsRuntimeWireFrame:
    """Build runtime.forward frame for master to sub node forwarding."""
    normalized_message: NsRuntimeMessage = message.normalized()
    return NsRuntimeWireFrame(
        frame_type=RUNTIME_FRAME_RUNTIME_FORWARD,
        message_id=str(normalized_message.message_id),
        trace_id=normalized_message.trace_id,
        created_at_epoch_ms=int(normalized_message.created_at_epoch_ms or int(time.time() * 1000)),
        payload={
            "source_node_id": str(source_node_id or "").strip(),
            "message": normalized_message.to_dict(),
        },
    )


def runtime_message_from_payload(payload: dict[str, Any]) -> NsRuntimeMessage:
    """Build and validate NsRuntimeMessage from backend.publish payload."""
    if not isinstance(payload, dict):
        raise NsRuntimeValidationError("runtime message payload must be a JSON object")

    target: dict[str, Any] = dict(payload.get("target") or {})
    producer: dict[str, Any] = dict(payload.get("producer") or {})

    message_payload: Any = payload.get("payload") or {}
    if not isinstance(message_payload, dict):
        raise NsRuntimeValidationError("runtime publish payload.payload must be a JSON object")

    headers_raw: Any = payload.get("headers") or {}
    if not isinstance(headers_raw, dict):
        raise NsRuntimeValidationError("runtime publish payload.headers must be a JSON object")

    ttl_raw: Any = payload.get("ttl_seconds", 300)
    ttl_seconds: int | None
    if ttl_raw is None:
        ttl_seconds = None
    else:
        ttl_seconds = int(ttl_raw)

    created_at_raw: Any = payload.get("created_at_epoch_ms")
    created_at_epoch_ms: int | None
    if created_at_raw is None:
        created_at_epoch_ms = None
    else:
        created_at_epoch_ms = int(created_at_raw)

    return NsRuntimeMessage(
        topic=str(payload.get("topic") or ""),
        event=str(payload.get("event") or ""),
        payload=dict(message_payload),
        target_type=str(target.get("type") or "user"),  # type: ignore[arg-type]
        target_id=target.get("id"),
        producer_type=str(producer.get("type") or "backend"),  # type: ignore[arg-type]
        producer_id=str(producer.get("id")).strip() if producer.get("id") is not None and str(producer.get("id")).strip() else None,
        message_id=str(payload.get("message_id") or ""),
        trace_id=str(payload.get("trace_id")).strip() if payload.get("trace_id") is not None and str(payload.get("trace_id")).strip() else None,
        idempotency_key=str(payload.get("idempotency_key")).strip() if payload.get("idempotency_key") is not None and str(payload.get("idempotency_key")).strip() else None,
        ttl_seconds=ttl_seconds,
        require_ack=bool(payload.get("require_ack", True)),
        created_at_epoch_ms=created_at_epoch_ms,
        headers={str(key).strip(): str(value).strip() for key, value in headers_raw.items() if str(key).strip()},
    ).normalized()


def runtime_message_from_forward_payload(payload: dict[str, Any]) -> NsRuntimeMessage:
    """Build and validate NsRuntimeMessage from runtime.forward payload."""
    if not isinstance(payload, dict):
        raise NsRuntimeValidationError("runtime forward payload must be a JSON object")

    message_raw: Any = payload.get("message") or {}
    if not isinstance(message_raw, dict):
        raise NsRuntimeValidationError("runtime forward payload.message must be a JSON object")

    return runtime_message_from_payload(dict(message_raw))
