# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping
from uuid import uuid4

from ns_runtime.packets import RuntimePacket
from ns_runtime.tasks.enums import RuntimeTaskStatus


@dataclass(frozen=True)
class RuntimeTaskContext:
    tenant_id: str | None = None
    operator_id: str | None = None
    trace_id: str | None = None
    source_endpoint_id: str | None = None
    correlation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        tenant_id = _to_optional_text(self.tenant_id)
        operator_id = _to_optional_text(self.operator_id)
        trace_id = _to_optional_text(self.trace_id)
        source_endpoint_id = _to_optional_text(self.source_endpoint_id)
        correlation_id = _to_optional_text(self.correlation_id)

        # tenant_id/operator_id/trace_id 是平台级上下文字段，用于多租户与链路追踪，不是业务字段。
        object.__setattr__(self, "tenant_id", tenant_id)
        object.__setattr__(self, "operator_id", operator_id)
        object.__setattr__(self, "trace_id", trace_id)
        object.__setattr__(self, "source_endpoint_id", source_endpoint_id)
        object.__setattr__(self, "correlation_id", correlation_id)
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "operator_id": self.operator_id,
            "trace_id": self.trace_id,
            "source_endpoint_id": self.source_endpoint_id,
            "correlation_id": self.correlation_id,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> RuntimeTaskContext:
        metadata_raw = data.get("metadata", {})
        if not isinstance(metadata_raw, Mapping):
            raise ValueError("metadata must be mapping")

        return cls(
            tenant_id=_to_optional_text(data.get("tenant_id")),
            operator_id=_to_optional_text(data.get("operator_id")),
            trace_id=_to_optional_text(data.get("trace_id")),
            source_endpoint_id=_to_optional_text(data.get("source_endpoint_id")),
            correlation_id=_to_optional_text(data.get("correlation_id")),
            metadata=dict(metadata_raw),
        )


@dataclass(frozen=True)
class RuntimeTask:
    task_id: str
    task_type: str
    status: RuntimeTaskStatus
    payload: dict[str, Any]
    context: RuntimeTaskContext
    required_capabilities: tuple[str, ...]
    priority: int
    created_at: datetime
    updated_at: datetime
    queued_at: datetime | None = None

    def __post_init__(self) -> None:
        task_id = str(self.task_id).strip()
        task_type = str(self.task_type).strip()
        if not task_id:
            raise ValueError("task_id must be non-empty")
        if not task_type:
            raise ValueError("task_type must be non-empty")
        if not isinstance(self.payload, dict):
            raise ValueError("payload must be dict")
        if self.priority < 0:
            raise ValueError("priority must be >= 0")
        if not isinstance(self.created_at, datetime):
            raise ValueError("created_at must be datetime")
        if not isinstance(self.updated_at, datetime):
            raise ValueError("updated_at must be datetime")
        if self.queued_at is not None and not isinstance(self.queued_at, datetime):
            raise ValueError("queued_at must be datetime or None")

        object.__setattr__(self, "task_id", task_id)
        object.__setattr__(self, "task_type", task_type)
        object.__setattr__(self, "payload", dict(self.payload))
        object.__setattr__(self, "required_capabilities", _normalize_capabilities(self.required_capabilities))

    @classmethod
    def create(
        cls,
        *,
        task_type: str,
        payload: Mapping[str, Any] | None = None,
        context: RuntimeTaskContext | None = None,
        required_capabilities: Iterable[str] = (),
        priority: int = 0,
    ) -> RuntimeTask:
        now = datetime.now(timezone.utc)
        return cls(
            task_id=uuid4().hex,
            task_type=task_type,
            status=RuntimeTaskStatus.CREATED,
            payload=dict(payload or {}),
            context=context or RuntimeTaskContext(),
            required_capabilities=tuple(required_capabilities),
            priority=priority,
            created_at=now,
            updated_at=now,
            queued_at=None,
        )

    def mark_queued(self) -> RuntimeTask:
        now = datetime.now(timezone.utc)
        return replace(
            self,
            status=RuntimeTaskStatus.QUEUED,
            queued_at=now,
            updated_at=now,
        )

    def with_status(self, status: RuntimeTaskStatus) -> RuntimeTask:
        now = datetime.now(timezone.utc)
        return replace(self, status=status, updated_at=now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status.value,
            "payload": dict(self.payload),
            "context": self.context.to_dict(),
            "required_capabilities": list(self.required_capabilities),
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "queued_at": self.queued_at.isoformat() if self.queued_at else None,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> RuntimeTask:
        payload_raw = data.get("payload", {})
        if not isinstance(payload_raw, dict):
            raise ValueError("payload must be dict")

        context_raw = data.get("context", {})
        if not isinstance(context_raw, Mapping):
            raise ValueError("context must be mapping")

        required_capabilities_raw = data.get("required_capabilities", ())
        if not isinstance(required_capabilities_raw, (list, tuple, set)):
            raise ValueError("required_capabilities must be list/tuple/set")

        created_at = _parse_iso_datetime(data.get("created_at"), field_name="created_at")
        updated_at = _parse_iso_datetime(data.get("updated_at"), field_name="updated_at")
        queued_at_raw = data.get("queued_at")
        queued_at = None if queued_at_raw is None else _parse_iso_datetime(queued_at_raw, field_name="queued_at")

        status_raw = str(data.get("status") or "").strip()
        if not status_raw:
            raise ValueError("status must be non-empty")

        priority_raw = data.get("priority", 0)
        try:
            priority = int(priority_raw)
        except (TypeError, ValueError) as exc:
            raise ValueError("priority must be integer") from exc

        return cls(
            task_id=str(data.get("task_id") or "").strip(),
            task_type=str(data.get("task_type") or "").strip(),
            status=RuntimeTaskStatus(status_raw),
            payload=dict(payload_raw),
            context=RuntimeTaskContext.from_dict(context_raw),
            required_capabilities=tuple(str(item) for item in required_capabilities_raw),
            priority=priority,
            created_at=created_at,
            updated_at=updated_at,
            queued_at=queued_at,
        )


@dataclass(frozen=True)
class RuntimeTaskSubmitRequest:
    task_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    context: RuntimeTaskContext = field(default_factory=RuntimeTaskContext)
    required_capabilities: tuple[str, ...] = ()
    priority: int = 0
    topic: str | None = None
    stream: str | None = None

    def __post_init__(self) -> None:
        task_type = str(self.task_type).strip()
        if not task_type:
            raise ValueError("task_type must be non-empty")
        if not isinstance(self.payload, dict):
            raise ValueError("payload must be dict")
        if self.priority < 0:
            raise ValueError("priority must be >= 0")

        object.__setattr__(self, "task_type", task_type)
        object.__setattr__(self, "payload", dict(self.payload))
        object.__setattr__(self, "required_capabilities", _normalize_capabilities(self.required_capabilities))
        object.__setattr__(self, "topic", _to_optional_text(self.topic))
        object.__setattr__(self, "stream", _to_optional_text(self.stream))


@dataclass(frozen=True)
class RuntimeTaskSubmitResult:
    task: RuntimeTask
    packet: RuntimePacket
    queued: bool
    broker_message_id: str | None = None


def _to_optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_capabilities(values: Iterable[str]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return tuple(result)


def _parse_iso_datetime(raw_value: object, *, field_name: str) -> datetime:
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise ValueError(f"{field_name} must be ISO 8601 string")

    try:
        return datetime.fromisoformat(raw_value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid {field_name}: {raw_value}") from exc

