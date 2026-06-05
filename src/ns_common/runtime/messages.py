# -*- coding: utf-8 -*-
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Literal, Any

from ns_common.runtime.constants import (
    RUNTIME_TARGET_USER,
    RUNTIME_TARGET_SESSION,
    RUNTIME_TARGET_CONNECTION,
    RUNTIME_TARGET_ROOM,
    RUNTIME_TARGET_BROADCAST,
    RUNTIME_TARGET_RESOURCE,
    RUNTIME_PRODUCER_FRONTEND,
    RUNTIME_PRODUCER_BACKEND,
    RUNTIME_PRODUCER_RUNTIME,
    RUNTIME_PRODUCER_BUSINESS_CLIENT,
    RUNTIME_ACK_STATUS_RECEIVED,
    RUNTIME_ACK_STATUS_ACCEPTED,
    RUNTIME_ACK_STATUS_FORWARDED,
    RUNTIME_ACK_STATUS_DELIVERED,
    RUNTIME_ACK_STATUS_REJECTED
)
from ns_common.runtime.errors import NsRuntimeValidationError

if TYPE_CHECKING:
    pass

RuntimeTargetType = Literal["user", "session", "connection", "room", "broadcast", "resource"]
RuntimeProducerType = Literal["frontend", "backend", "runtime", "business_client"]
RuntimeAckStatus = Literal["received", "accepted", "forwarded", "delivered", "rejected"]

_ALLOWED_TARGET_TYPES: set[str] = {
    RUNTIME_TARGET_USER,
    RUNTIME_TARGET_SESSION,
    RUNTIME_TARGET_CONNECTION,
    RUNTIME_TARGET_ROOM,
    RUNTIME_TARGET_BROADCAST,
    RUNTIME_TARGET_RESOURCE,
}

_ALLOWED_PRODUCER_TYPES: set[str] = {
    RUNTIME_PRODUCER_FRONTEND,
    RUNTIME_PRODUCER_BACKEND,
    RUNTIME_PRODUCER_RUNTIME,
    RUNTIME_PRODUCER_BUSINESS_CLIENT,
}

_ALLOWED_ACK_STATUSES: set[str] = {
    RUNTIME_ACK_STATUS_RECEIVED,
    RUNTIME_ACK_STATUS_ACCEPTED,
    RUNTIME_ACK_STATUS_FORWARDED,
    RUNTIME_ACK_STATUS_DELIVERED,
    RUNTIME_ACK_STATUS_REJECTED,
}


@dataclass(slots=True, frozen=True, kw_only=True)
class NsRuntimeTarget:
    """Normalized runtime message target."""

    target_type: RuntimeTargetType
    target_id: str | int | None = None

    def normalized(self) -> "NsRuntimeTarget":
        """Return normalized target payload."""
        target_type: str = str(self.target_type or "").strip().lower()
        if target_type not in _ALLOWED_TARGET_TYPES:
            raise NsRuntimeValidationError(f"runtime target_type is invalid: {self.target_type}")

        normalized_target_id: str | None = None
        if self.target_id is not None and str(self.target_id).strip():
            normalized_target_id = str(self.target_id).strip()

        if target_type != RUNTIME_TARGET_BROADCAST and normalized_target_id is None:
            raise NsRuntimeValidationError("runtime target_id is required unless target_type is broadcast")

        return NsRuntimeTarget(target_type=target_type, target_id=normalized_target_id)  # type: ignore[arg-type]

    def to_dict(self) -> dict[str, Any]:
        """Serialize target payload."""
        normalized_target: NsRuntimeTarget = self.normalized()
        return {
            "type": normalized_target.target_type,
            "id": normalized_target.target_id,
        }


@dataclass(slots=True, frozen=True, kw_only=True)
class NsRuntimeMessage:
    """Normalized runtime message used by backend, runtime nodes and realtime clients."""

    topic: str
    event: str
    payload: dict[str, Any] = field(default_factory=dict)
    target_type: RuntimeTargetType = RUNTIME_TARGET_USER  # type: ignore[assignment]
    target_id: str | int | None = None
    producer_type: RuntimeProducerType = RUNTIME_PRODUCER_BACKEND  # type: ignore[assignment]
    producer_id: str | None = None
    message_id: str | None = None
    trace_id: str | None = None
    idempotency_key: str | None = None
    ttl_seconds: int | None = 300
    require_ack: bool = True
    created_at_epoch_ms: int | None = None
    headers: dict[str, str] = field(default_factory=dict)

    @classmethod
    def new(
            cls,
            *,
            topic: str,
            event: str,
            payload: dict[str, Any] | None = None,
            target_type: RuntimeTargetType = RUNTIME_TARGET_USER,  # type: ignore[assignment]
            target_id: str | int | None = None,
            producer_type: RuntimeProducerType = RUNTIME_PRODUCER_BACKEND,  # type: ignore[assignment]
            producer_id: str | None = None,
            trace_id: str | None = None,
            idempotency_key: str | None = None,
            ttl_seconds: int | None = 300,
            require_ack: bool = True,
            headers: dict[str, str] | None = None,
    ) -> "NsRuntimeMessage":
        """Build one runtime message with generated id and timestamp."""
        return cls(
            topic=topic,
            event=event,
            payload=payload or {},
            target_type=target_type,
            target_id=target_id,
            producer_type=producer_type,
            producer_id=producer_id,
            message_id=uuid.uuid4().hex,
            trace_id=trace_id,
            idempotency_key=idempotency_key,
            ttl_seconds=ttl_seconds,
            require_ack=require_ack,
            created_at_epoch_ms=int(time.time() * 1000),
            headers=headers or {},
        ).normalized()

    def normalized(self) -> "NsRuntimeMessage":
        """Return normalized runtime message payload."""
        topic: str = str(self.topic or "").strip()
        event: str = str(self.event or "").strip()
        if not topic:
            raise NsRuntimeValidationError("runtime message topic is required")
        if not event:
            raise NsRuntimeValidationError("runtime message event is required")

        producer_type: str = str(self.producer_type or "").strip().lower()
        if producer_type not in _ALLOWED_PRODUCER_TYPES:
            raise NsRuntimeValidationError(f"runtime producer_type is invalid: {self.producer_type}")

        target: NsRuntimeTarget = NsRuntimeTarget(target_type=self.target_type, target_id=self.target_id).normalized()
        normalized_message_id: str = str(self.message_id or "").strip() or uuid.uuid4().hex
        normalized_created_at_epoch_ms: int = self.created_at_epoch_ms if self.created_at_epoch_ms is not None else int(time.time() * 1000)

        normalized_ttl_seconds: int | None = self.ttl_seconds
        if isinstance(normalized_ttl_seconds, bool):
            raise NsRuntimeValidationError("runtime ttl_seconds must be int or None")
        if normalized_ttl_seconds is not None and normalized_ttl_seconds <= 0:
            raise NsRuntimeValidationError("runtime ttl_seconds must be positive or None")

        return replace(
            self,
            topic=topic,
            event=event,
            payload=dict(self.payload),
            target_type=target.target_type,
            target_id=target.target_id,
            producer_type=producer_type,  # type: ignore[arg-type]
            producer_id=str(self.producer_id).strip() if self.producer_id is not None and str(self.producer_id).strip() else None,
            message_id=normalized_message_id,
            trace_id=str(self.trace_id).strip() if self.trace_id is not None and str(self.trace_id).strip() else None,
            idempotency_key=str(self.idempotency_key).strip() if self.idempotency_key is not None and str(self.idempotency_key).strip() else None,
            ttl_seconds=normalized_ttl_seconds,
            require_ack=bool(self.require_ack),
            created_at_epoch_ms=normalized_created_at_epoch_ms,
            headers={str(key).strip(): str(value).strip() for key, value in self.headers.items() if str(key).strip()},
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize runtime message to dict."""
        message: NsRuntimeMessage = self.normalized()
        return {
            "message_id": message.message_id,
            "topic": message.topic,
            "event": message.event,
            "payload": dict(message.payload),
            "target": NsRuntimeTarget(target_type=message.target_type, target_id=message.target_id).to_dict(),
            "producer": {
                "type": message.producer_type,
                "id": message.producer_id,
            },
            "trace_id": message.trace_id,
            "idempotency_key": message.idempotency_key,
            "ttl_seconds": message.ttl_seconds,
            "require_ack": message.require_ack,
            "created_at_epoch_ms": message.created_at_epoch_ms,
            "headers": dict(message.headers),
        }


@dataclass(slots=True, frozen=True, kw_only=True)
class NsRuntimeAck:
    """Runtime message ack returned by ns_runtime master."""

    message_id: str
    status: RuntimeAckStatus = RUNTIME_ACK_STATUS_ACCEPTED  # type: ignore[assignment]
    reason: str | None = None
    handled_by: str | None = None
    trace_id: str | None = None
    acked_at_epoch_ms: int | None = None

    def normalized(self) -> "NsRuntimeAck":
        """Return normalized ack payload."""
        message_id: str = str(self.message_id or "").strip()
        if not message_id:
            raise NsRuntimeValidationError("runtime ack message_id is required")

        status: str = str(self.status or "").strip().lower()
        if status not in _ALLOWED_ACK_STATUSES:
            raise NsRuntimeValidationError(f"runtime ack status is invalid: {self.status}")

        return replace(
            self,
            message_id=message_id,
            status=status,  # type: ignore[arg-type]
            reason=str(self.reason).strip() if self.reason is not None and str(self.reason).strip() else None,
            handled_by=str(self.handled_by).strip() if self.handled_by is not None and str(self.handled_by).strip() else None,
            trace_id=str(self.trace_id).strip() if self.trace_id is not None and str(self.trace_id).strip() else None,
            acked_at_epoch_ms=self.acked_at_epoch_ms if self.acked_at_epoch_ms is not None else int(time.time() * 1000),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize ack payload to dict."""
        ack: NsRuntimeAck = self.normalized()
        return {
            "message_id": ack.message_id,
            "status": ack.status,
            "reason": ack.reason,
            "handled_by": ack.handled_by,
            "trace_id": ack.trace_id,
            "acked_at_epoch_ms": ack.acked_at_epoch_ms,
        }
