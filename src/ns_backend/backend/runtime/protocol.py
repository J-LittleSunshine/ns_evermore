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
    "ack",
]


@dataclass(slots=True, frozen=True, kw_only=True)
class NsBackendRuntimeFrame:
    """Wire frame exchanged between backend runtime connector and ns_runtime master."""

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

        return cls(
            frame_type=frame_type,  # type: ignore[arg-type]
            message_id=str(data.get("message_id") or "").strip() or uuid.uuid4().hex,
            trace_id=str(data.get("trace_id")).strip() if data.get("trace_id") is not None and str(data.get("trace_id")).strip() else None,
            created_at_epoch_ms=int(data.get("created_at_epoch_ms") or int(time.time() * 1000)),
            payload=dict(data.get("payload") or {}),
        )


def build_backend_register_frame(*, node_id: str, service_name: str = "ns_backend", version: str = "", environment: str = "") -> NsBackendRuntimeFrame:
    """Build backend.register frame."""
    return NsBackendRuntimeFrame(
        frame_type="backend.register",
        payload={
            "instance_id": node_id,
            "service_name": service_name,
            "version": version,
            "environment": environment,
            "capabilities": [
                "health_report",
                "business_publish",
                "outbox_drain",
            ],
        },
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
