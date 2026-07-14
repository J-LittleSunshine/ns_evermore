# -*- coding: utf-8 -*-
from __future__ import annotations

from abc import (
    ABC,
    abstractmethod,
)
from dataclasses import dataclass
from threading import RLock
from typing import Literal

RuntimeAuditOutcome = Literal[
    "responded",
    "rejected",
    "continued",
    "exception",
]

RuntimeAuditResultAction = Literal[
    "respond",
    "reject",
    "continue",
    "exception",
]

_AUDIT_OUTCOMES: frozenset[str] = frozenset(
    {
        "responded",
        "rejected",
        "continued",
        "exception",
    }
)

_AUDIT_RESULT_ACTIONS: frozenset[str] = frozenset(
    {
        "respond",
        "reject",
        "continue",
        "exception",
    }
)


@dataclass(
    slots=True,
    frozen=True,
    kw_only=True,
)
class RuntimeAuditEvent:
    audit_id: str
    audit_action: str
    outcome: RuntimeAuditOutcome

    message_id: str
    message_type: str
    message_category: str
    message_reliability: str

    runtime_id: str
    connection_id: str
    connection_epoch: int
    session_id: str
    identity: str
    tenant_id: str
    component_type: str

    auth_snapshot_id: str
    iam_mode: str
    capabilities_summary: tuple[str, ...]

    processor_name: str
    result_action: RuntimeAuditResultAction
    response_message_type: str
    error_code: str
    should_close: bool

    exception_class: str
    exception_message: str

    trace_id: str
    request_id: str

    received_at: str
    completed_at: str
    config_version: str
    policy_version: str

    def __post_init__(self) -> None:
        required_fields = (
            "audit_id",
            "audit_action",
            "message_id",
            "message_type",
            "message_category",
            "message_reliability",
            "runtime_id",
            "connection_id",
            "session_id",
            "identity",
            "tenant_id",
            "component_type",
            "auth_snapshot_id",
            "iam_mode",
            "processor_name",
            "trace_id",
            "request_id",
            "received_at",
            "completed_at",
            "config_version",
            "policy_version",
        )

        for field_name in required_fields:
            value = getattr(
                self,
                field_name,
            )

            if (
                    not isinstance(value, str)
                    or not value.strip()
            ):
                raise ValueError(
                    f"{field_name} must be non-empty."
                )

        if (
                isinstance(self.connection_epoch, bool)
                or not isinstance(
            self.connection_epoch,
            int,
        )
                or self.connection_epoch < 0
        ):
            raise ValueError(
                "connection_epoch must be a "
                "non-negative integer."
            )

        if self.outcome not in _AUDIT_OUTCOMES:
            raise ValueError(
                "outcome is invalid."
            )

        if (
                self.result_action
                not in _AUDIT_RESULT_ACTIONS
        ):
            raise ValueError(
                "result_action is invalid."
            )

        if not isinstance(self.should_close, bool):
            raise ValueError(
                "should_close must be bool."
            )

        normalized_capabilities: list[str] = []

        for capability in self.capabilities_summary:
            if (
                    not isinstance(capability, str)
                    or not capability.strip()
            ):
                raise ValueError(
                    "capabilities_summary must contain "
                    "non-empty strings."
                )

            normalized_capabilities.append(
                capability.strip()
            )

        object.__setattr__(
            self,
            "capabilities_summary",
            tuple(
                sorted(
                    set(normalized_capabilities)
                )
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "audit_id": self.audit_id,
            "audit_action": self.audit_action,
            "outcome": self.outcome,
            "message_id": self.message_id,
            "message_type": self.message_type,
            "message_category": (
                self.message_category
            ),
            "message_reliability": (
                self.message_reliability
            ),
            "runtime_id": self.runtime_id,
            "connection_id": self.connection_id,
            "connection_epoch": (
                self.connection_epoch
            ),
            "session_id": self.session_id,
            "identity": self.identity,
            "tenant_id": self.tenant_id,
            "component_type": self.component_type,
            "auth_snapshot_id": (
                self.auth_snapshot_id
            ),
            "iam_mode": self.iam_mode,
            "capabilities_summary": list(
                self.capabilities_summary
            ),
            "processor_name": self.processor_name,
            "result_action": self.result_action,
            "response_message_type": (
                self.response_message_type
            ),
            "error_code": self.error_code,
            "should_close": self.should_close,
            "exception_class": (
                self.exception_class
            ),
            "exception_message": (
                self.exception_message
            ),
            "trace_id": self.trace_id,
            "request_id": self.request_id,
            "received_at": self.received_at,
            "completed_at": self.completed_at,
            "config_version": self.config_version,
            "policy_version": self.policy_version,
        }


class RuntimeAuditSink(ABC):
    @abstractmethod
    async def append(
            self,
            event: RuntimeAuditEvent,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_events(
            self,
            *,
            message_id: str | None = None,
            tenant_id: str | None = None,
            audit_action: str | None = None,
            outcome: RuntimeAuditOutcome | None = None,
    ) -> tuple[RuntimeAuditEvent, ...]:
        raise NotImplementedError


class InMemoryRuntimeAuditSink(
    RuntimeAuditSink
):
    def __init__(self) -> None:
        self._events: list[
            RuntimeAuditEvent
        ] = []
        self._audit_ids: set[str] = set()
        self._lock = RLock()

    async def append(
            self,
            event: RuntimeAuditEvent,
    ) -> None:
        if not isinstance(
                event,
                RuntimeAuditEvent,
        ):
            raise TypeError(
                "event must be RuntimeAuditEvent."
            )

        with self._lock:
            if event.audit_id in self._audit_ids:
                raise ValueError(
                    "audit_id already exists."
                )

            self._events.append(event)
            self._audit_ids.add(
                event.audit_id
            )

    def list_events(
            self,
            *,
            message_id: str | None = None,
            tenant_id: str | None = None,
            audit_action: str | None = None,
            outcome: RuntimeAuditOutcome | None = None,
    ) -> tuple[RuntimeAuditEvent, ...]:
        with self._lock:
            return tuple(
                event
                for event in self._events
                if (
                        message_id is None
                        or event.message_id
                        == message_id
                )
                and (
                        tenant_id is None
                        or event.tenant_id
                        == tenant_id
                )
                and (
                        audit_action is None
                        or event.audit_action
                        == audit_action
                )
                and (
                        outcome is None
                        or event.outcome
                        == outcome
                )
            )

    def clear(self) -> None:
        with self._lock:
            self._events.clear()
            self._audit_ids.clear()
