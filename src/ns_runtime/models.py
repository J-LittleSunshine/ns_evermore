# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import (
    dataclass,
    field
)
from datetime import (
    datetime,
    timezone
)
from typing import (
    Any,
    Literal,
    Mapping,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    pass

RuntimeComponentType = Literal[
    "frontend",
    "client",
    "node",
    "backend",
    "runtime",
    "sub_node",
    "management",
]

RuntimeRole = Literal[
    "singleton",
    "sub_node",
    "standby_master",
    "active_master",
    "transitioning",
    "draining",
]

MessageReliability = Literal[
    "best_effort",
    "reliable",
    "critical",
]

ProcessorResultAction = Literal[
    "continue",
    "respond",
    "reject",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


@dataclass(slots=True, kw_only=True)
class RuntimeSourceContext:
    runtime_id: str
    connection_id: str
    session_id: str
    identity: str
    tenant_id: str
    component_type: RuntimeComponentType
    capabilities_summary: tuple[str, ...] = field(default_factory=tuple)
    connection_epoch: int = 0

    def to_group(self) -> dict[str, Any]:
        return {
            "runtime_id": self.runtime_id,
            "connection_id": self.connection_id,
            "session_id": self.session_id,
            "identity": self.identity,
            "tenant_id": self.tenant_id,
            "component_type": self.component_type,
            "capabilities_summary": list(self.capabilities_summary),
            "connection_epoch": self.connection_epoch,
        }


@dataclass(slots=True, kw_only=True)
class RuntimeAuthContext:
    tenant_id: str
    snapshot_id: str
    iam_mode: Literal["strict", "cached", "node_trusted"]
    issued_at: str
    expires_at: str
    capabilities_summary: tuple[str, ...] = field(default_factory=tuple)

    def to_group(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "snapshot_id": self.snapshot_id,
            "iam_mode": self.iam_mode,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "capabilities_summary": list(self.capabilities_summary),
        }


@dataclass(slots=True, kw_only=True)
class RuntimeSessionContext:
    runtime_id: str
    connection_id: str
    session_id: str
    identity: str
    tenant_id: str
    component_type: RuntimeComponentType
    capabilities: tuple[str, ...]
    auth_snapshot_id: str
    auth_issued_at: str
    auth_expires_at: str
    connection_epoch: int = 0
    role: RuntimeRole = "singleton"
    iam_mode: Literal["strict", "cached", "node_trusted"] = "cached"

    def build_source_context(self) -> RuntimeSourceContext:
        return RuntimeSourceContext(
            runtime_id=self.runtime_id,
            connection_id=self.connection_id,
            session_id=self.session_id,
            identity=self.identity,
            tenant_id=self.tenant_id,
            component_type=self.component_type,
            capabilities_summary=tuple(sorted(self.capabilities)),
            connection_epoch=self.connection_epoch,
        )

    def build_auth_context(self) -> RuntimeAuthContext:
        return RuntimeAuthContext(
            tenant_id=self.tenant_id,
            snapshot_id=self.auth_snapshot_id,
            iam_mode=self.iam_mode,
            issued_at=self.auth_issued_at,
            expires_at=self.auth_expires_at,
            capabilities_summary=tuple(sorted(self.capabilities)),
        )


@dataclass(slots=True, kw_only=True)
class Envelope:
    raw: dict[str, Any]
    protocol_version: tuple[int, int, int]
    message_id: str
    message_type: str
    category: str
    reliability: MessageReliability

    def to_dict(self) -> dict[str, Any]:
        return dict(self.raw)


@dataclass(slots=True, kw_only=True)
class MessageTypeSpec:
    message_type: str
    category: str
    required_groups: tuple[str, ...] = field(default_factory=tuple)
    allowed_groups: tuple[str, ...] = field(default_factory=tuple)
    required_capabilities: tuple[str, ...] = field(default_factory=tuple)
    reliability: MessageReliability = "best_effort"
    audit_action: str = "runtime.message.process"
    implemented: bool = False


@dataclass(slots=True, kw_only=True)
class ProcessorRequest:
    envelope: Envelope
    session: RuntimeSessionContext
    received_at: str
    config_version: str
    policy_version: str


@dataclass(slots=True, kw_only=True)
class ProcessorResponse:
    action: ProcessorResultAction
    envelope: dict[str, Any] | None = None
    should_close: bool = False
    audit_event: Mapping[str, Any] | None = None

    @classmethod
    def continue_next(cls) -> "ProcessorResponse":
        return cls(action="continue")

    @classmethod
    def respond(cls, envelope: dict[str, Any], *, should_close: bool = False) -> "ProcessorResponse":
        return cls(action="respond", envelope=envelope, should_close=should_close)

    @classmethod
    def reject(cls, envelope: dict[str, Any], *, should_close: bool = False) -> "ProcessorResponse":
        return cls(action="reject", envelope=envelope, should_close=should_close)
