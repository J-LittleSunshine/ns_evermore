# -*- coding: utf-8 -*-
"""Typed P05 lifecycle audit handoff without a durability claim."""

from __future__ import annotations

import asyncio
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from ns_common.exceptions import (
    NsRuntimeStateStoreUnavailableError,
    NsValidationError,
)
from ns_common.time import Clock

from .session import SessionContext
from .state import LogicalConnectionCloseReason


class ConnectionAuditKind(str, Enum):
    RESUME = "resume"
    KICK = "kick"
    SECURITY_CLOSE = "security_close"
    REAUTH_REJECTION = "reauth_rejection"
    NON_RESUMABLE_CLOSE = "non_resumable_close"


class ConnectionAuditOutcome(str, Enum):
    SUCCEEDED = "succeeded"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ENFORCED = "enforced"


class ConnectionAuditConsistency(str, Enum):
    STRONG_REQUIRED = "strong_required"


@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionLifecycleAuditEvent:
    kind: ConnectionAuditKind
    outcome: ConnectionAuditOutcome
    required_consistency: ConnectionAuditConsistency
    connection_summary: str
    component_type: str
    connection_epoch: int
    close_reason: LogicalConnectionCloseReason | None
    occurred_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ConnectionAuditKind):
            _invalid("audit.kind")
        if not isinstance(self.outcome, ConnectionAuditOutcome):
            _invalid("audit.outcome")
        if self.required_consistency is not ConnectionAuditConsistency.STRONG_REQUIRED:
            _invalid("audit.required_consistency")
        _validate_summary(self.connection_summary)
        if not isinstance(self.component_type, str) or not self.component_type:
            _invalid("audit.component_type")
        if (
            isinstance(self.connection_epoch, bool)
            or not isinstance(self.connection_epoch, int)
            or self.connection_epoch < 0
        ):
            _invalid("audit.connection_epoch")
        if self.close_reason is not None and not isinstance(
            self.close_reason,
            LogicalConnectionCloseReason,
        ):
            _invalid("audit.close_reason")
        object.__setattr__(
            self,
            "occurred_at",
            _utc(self.occurred_at, "audit.occurred_at"),
        )


class ConnectionLifecycleAuditSink(ABC):
    """P05 handoff only; implementations must not be assumed durable."""

    @abstractmethod
    async def emit(self, event: ConnectionLifecycleAuditEvent) -> None:
        raise NotImplementedError


class DeterministicTestConnectionAuditSink(ConnectionLifecycleAuditSink):
    """Explicit in-memory test sink, never a P07/P08 storage substitute."""

    def __init__(self) -> None:
        self._events: list[ConnectionLifecycleAuditEvent] = []
        self.failure: Exception | None = None

    @property
    def events(self) -> tuple[ConnectionLifecycleAuditEvent, ...]:
        return tuple(self._events)

    async def emit(self, event: ConnectionLifecycleAuditEvent) -> None:
        if not isinstance(event, ConnectionLifecycleAuditEvent):
            _invalid("audit.event")
        if self.failure is not None:
            raise self.failure
        self._events.append(event)


class UnavailableConnectionLifecycleAuditSink(ConnectionLifecycleAuditSink):
    """Explicit production fail-closed boundary until an authority is wired."""

    async def emit(self, event: ConnectionLifecycleAuditEvent) -> None:
        if not isinstance(event, ConnectionLifecycleAuditEvent):
            _invalid("audit.event")
        raise NsRuntimeStateStoreUnavailableError(
            details={
                "component": "logical_connection_audit",
                "operation": "commit",
                "reason": "strong_audit_authority_unavailable",
            },
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionLifecycleAuditSnapshot:
    attempted_count: int
    succeeded_count: int
    failed_count: int
    last_kind: ConnectionAuditKind | None

    def __post_init__(self) -> None:
        for name in ("attempted_count", "succeeded_count", "failed_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                _invalid(f"audit.{name}")
        if self.succeeded_count + self.failed_count != self.attempted_count:
            _invalid("audit.counts")
        if self.last_kind is not None and not isinstance(
            self.last_kind,
            ConnectionAuditKind,
        ):
            _invalid("audit.last_kind")
        if (self.attempted_count == 0) != (self.last_kind is None):
            _invalid("audit.last_kind")


class ConnectionLifecycleAuditBoundary:
    """Serialize strong audit commits and fail closed on sink failure."""

    def __init__(
        self,
        *,
        session_context: SessionContext,
        clock: Clock,
        sink: ConnectionLifecycleAuditSink,
    ) -> None:
        if not isinstance(session_context, SessionContext):
            _invalid("session_context")
        if not isinstance(clock, Clock):
            _invalid("clock")
        if not isinstance(sink, ConnectionLifecycleAuditSink):
            _invalid("audit.sink")
        self._connection_summary = logical_id_summary(
            session_context.connection_id,
        )
        self._component_type = session_context.component_type
        self._clock = clock
        self._sink = sink
        self._lock = asyncio.Lock()
        self._attempted = 0
        self._succeeded = 0
        self._failed = 0
        self._last_kind: ConnectionAuditKind | None = None

    async def emit(
        self,
        *,
        kind: ConnectionAuditKind,
        outcome: ConnectionAuditOutcome,
        connection_epoch: int,
        close_reason: LogicalConnectionCloseReason | None = None,
    ) -> None:
        if not isinstance(kind, ConnectionAuditKind):
            _invalid("audit.kind")
        if not isinstance(outcome, ConnectionAuditOutcome):
            _invalid("audit.outcome")
        if (
            isinstance(connection_epoch, bool)
            or not isinstance(connection_epoch, int)
            or connection_epoch < 0
        ):
            _invalid("audit.connection_epoch")
        if close_reason is not None and not isinstance(
            close_reason,
            LogicalConnectionCloseReason,
        ):
            _invalid("audit.close_reason")
        async with self._lock:
            self._attempted += 1
            self._last_kind = kind
            try:
                event = ConnectionLifecycleAuditEvent(
                    kind=kind,
                    outcome=outcome,
                    required_consistency=(
                        ConnectionAuditConsistency.STRONG_REQUIRED
                    ),
                    connection_summary=self._connection_summary,
                    component_type=self._component_type,
                    connection_epoch=connection_epoch,
                    close_reason=close_reason,
                    occurred_at=self._clock.utc_now(),
                )
                await self._sink.emit(event)
            except asyncio.CancelledError:
                self._failed += 1
                raise
            except NsRuntimeStateStoreUnavailableError:
                self._failed += 1
                raise
            except Exception:
                self._failed += 1
                raise NsRuntimeStateStoreUnavailableError(
                    details={
                        "component": "logical_connection_audit",
                        "operation": "commit",
                        "reason": "strong_audit_commit_failed",
                        "enforcement_outcome": outcome.value,
                    },
                ) from None
            self._succeeded += 1

    async def snapshot(self) -> ConnectionLifecycleAuditSnapshot:
        async with self._lock:
            return ConnectionLifecycleAuditSnapshot(
                attempted_count=self._attempted,
                succeeded_count=self._succeeded,
                failed_count=self._failed,
                last_kind=self._last_kind,
            )


def logical_id_summary(value: str) -> str:
    if not isinstance(value, str) or not value:
        _invalid("logical_id")
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _validate_summary(value: object) -> None:
    if (
        not isinstance(value, str)
        or not value.startswith("sha256:")
        or len(value) != 23
    ):
        _invalid("connection_summary")


def _utc(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        _invalid(field_name)
    try:
        offset = value.utcoffset()
        normalized = value.astimezone(timezone.utc)
    except Exception:
        offset = None
    if offset is None:
        _invalid(field_name)
    return normalized


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Connection lifecycle audit value is invalid.",
        details={"component": "logical_connection", "field": field_name},
    )


__all__ = (
    "ConnectionAuditConsistency",
    "ConnectionAuditKind",
    "ConnectionAuditOutcome",
    "ConnectionLifecycleAuditBoundary",
    "ConnectionLifecycleAuditEvent",
    "ConnectionLifecycleAuditSink",
    "ConnectionLifecycleAuditSnapshot",
    "DeterministicTestConnectionAuditSink",
    "UnavailableConnectionLifecycleAuditSink",
    "logical_id_summary",
)
