# -*- coding: utf-8 -*-
"""One-way non-resumable close policy and typed security audit boundary."""

from __future__ import annotations

import asyncio
import dataclasses
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from ns_common.exceptions import NsRuntimeIamDeniedError, NsStateError, NsValidationError
from ns_common.time import Clock
from ns_runtime.transport import TransportSession

from .audit import (
    ConnectionAuditKind,
    ConnectionAuditOutcome,
    ConnectionLifecycleAuditBoundary,
    logical_id_summary,
)
from .grace import ReconnectGracePhase, ReconnectGraceService
from .index import LocalConnectionIndex
from .session import SessionContext
from .state import LogicalConnectionCloseReason, LogicalConnectionState


class NonResumableCloseKind(str, Enum):
    KICK = "kick"
    SECURITY_VIOLATION = "security_violation"
    SEVERE_PROTOCOL_VIOLATION = "severe_protocol_violation"
    MALICIOUS_DUPLICATE_CONFIRMATION = "malicious_duplicate_confirmation"
    POLICY_NON_RECOVERABLE = "policy_non_recoverable"


class NonResumablePublicError(str, Enum):
    CONNECTION_KICKED = "connection_kicked"
    SECURITY_CLOSED = "security_closed"
    PROTOCOL_CLOSED = "protocol_closed"
    DUPLICATE_CONFIRMATION_REJECTED = "duplicate_confirmation_rejected"
    NON_RECOVERABLE_CLOSED = "non_recoverable_closed"


@dataclass(frozen=True, slots=True, kw_only=True)
class NonResumableCloseDecision:
    kind: NonResumableCloseKind
    close_reason: LogicalConnectionCloseReason
    public_error: NonResumablePublicError

    def __post_init__(self) -> None:
        if not isinstance(self.kind, NonResumableCloseKind):
            _invalid("decision.kind")
        if not isinstance(self.close_reason, LogicalConnectionCloseReason):
            _invalid("decision.close_reason")
        if not isinstance(self.public_error, NonResumablePublicError):
            _invalid("decision.public_error")


_DECISIONS: Mapping[
    NonResumableCloseKind,
    NonResumableCloseDecision,
] = MappingProxyType({
    NonResumableCloseKind.KICK: NonResumableCloseDecision(
        kind=NonResumableCloseKind.KICK,
        close_reason=LogicalConnectionCloseReason.KICKED,
        public_error=NonResumablePublicError.CONNECTION_KICKED,
    ),
    NonResumableCloseKind.SECURITY_VIOLATION: NonResumableCloseDecision(
        kind=NonResumableCloseKind.SECURITY_VIOLATION,
        close_reason=LogicalConnectionCloseReason.SECURITY_CLOSED,
        public_error=NonResumablePublicError.SECURITY_CLOSED,
    ),
    NonResumableCloseKind.SEVERE_PROTOCOL_VIOLATION: NonResumableCloseDecision(
        kind=NonResumableCloseKind.SEVERE_PROTOCOL_VIOLATION,
        close_reason=LogicalConnectionCloseReason.PROTOCOL_FAILED,
        public_error=NonResumablePublicError.PROTOCOL_CLOSED,
    ),
    NonResumableCloseKind.MALICIOUS_DUPLICATE_CONFIRMATION: (
        NonResumableCloseDecision(
            kind=NonResumableCloseKind.MALICIOUS_DUPLICATE_CONFIRMATION,
            close_reason=LogicalConnectionCloseReason.SECURITY_CLOSED,
            public_error=(
                NonResumablePublicError.DUPLICATE_CONFIRMATION_REJECTED
            ),
        )
    ),
    NonResumableCloseKind.POLICY_NON_RECOVERABLE: NonResumableCloseDecision(
        kind=NonResumableCloseKind.POLICY_NON_RECOVERABLE,
        close_reason=LogicalConnectionCloseReason.ISOLATED_CLOSED,
        public_error=NonResumablePublicError.NON_RECOVERABLE_CLOSED,
    ),
})


@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionSecurityAuditEvent:
    classification: NonResumableCloseKind
    close_reason: LogicalConnectionCloseReason
    public_error: NonResumablePublicError
    connection_summary: str
    component_type: str
    connection_epoch: int
    occurred_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.classification, NonResumableCloseKind):
            _invalid("audit.classification")
        if not isinstance(self.close_reason, LogicalConnectionCloseReason):
            _invalid("audit.close_reason")
        if not isinstance(self.public_error, NonResumablePublicError):
            _invalid("audit.public_error")
        if (
            not isinstance(self.connection_summary, str)
            or self.connection_summary[:7] != "sha256:"
            or len(self.connection_summary) != 23
        ):
            _invalid("connection_summary")
        if not isinstance(self.component_type, str) or not self.component_type:
            _invalid("audit.component_type")
        if (
            isinstance(self.connection_epoch, bool)
            or not isinstance(self.connection_epoch, int)
            or self.connection_epoch < 0
        ):
            _invalid("audit.connection_epoch")
        if not isinstance(self.occurred_at, datetime):
            _invalid("occurred_at")
        try:
            offset = self.occurred_at.utcoffset()
            normalized = self.occurred_at.astimezone(timezone.utc)
        except Exception:
            offset = None
        if offset is None:
            _invalid("occurred_at")
        object.__setattr__(self, "occurred_at", normalized)


class ConnectionSecurityAuditSink(ABC):
    @abstractmethod
    async def emit(self, event: ConnectionSecurityAuditEvent) -> None:
        raise NotImplementedError


class DeterministicTestSecurityAuditSink(ConnectionSecurityAuditSink):
    """Explicit P05 test sink; not a P07/P08 durable audit implementation."""

    def __init__(self) -> None:
        self._events: list[ConnectionSecurityAuditEvent] = []
        self.failure: Exception | None = None

    @property
    def events(self) -> tuple[ConnectionSecurityAuditEvent, ...]:
        return tuple(self._events)

    async def emit(self, event: ConnectionSecurityAuditEvent) -> None:
        if not isinstance(event, ConnectionSecurityAuditEvent):
            _invalid("audit_event")
        if self.failure is not None:
            raise self.failure
        self._events.append(event)


@dataclass(frozen=True, slots=True, kw_only=True)
class NonResumableConnectionSnapshot:
    non_resumable: bool
    decision: NonResumableCloseDecision | None
    state: LogicalConnectionState
    audit_attempted: bool
    audit_succeeded: bool


class NonResumableConnectionGuard:
    def __init__(
        self,
        *,
        session_context: SessionContext,
        connection_index: LocalConnectionIndex,
        clock: Clock,
        audit_sink: ConnectionSecurityAuditSink,
        lifecycle_audit: ConnectionLifecycleAuditBoundary | None = None,
        transport_session: TransportSession | None = None,
        grace_service: ReconnectGraceService | None = None,
    ) -> None:
        if not isinstance(session_context, SessionContext):
            _invalid("session_context")
        if not isinstance(connection_index, LocalConnectionIndex):
            _invalid("connection_index")
        if not isinstance(clock, Clock):
            _invalid("clock")
        if not isinstance(audit_sink, ConnectionSecurityAuditSink):
            _invalid("audit_sink")
        if lifecycle_audit is not None and not isinstance(
            lifecycle_audit,
            ConnectionLifecycleAuditBoundary,
        ):
            _invalid("lifecycle_audit")
        if transport_session is not None and not isinstance(
            transport_session,
            TransportSession,
        ):
            _invalid("transport_session")
        if grace_service is not None and not isinstance(
            grace_service,
            ReconnectGraceService,
        ):
            _invalid("grace_service")
        if transport_session is None and grace_service is None:
            _invalid("close_owner")
        self._context = session_context
        self._index = connection_index
        self._clock = clock
        self._audit_sink = audit_sink
        self._lifecycle_audit = lifecycle_audit
        self._transport = transport_session
        self._grace = grace_service
        self._lock = asyncio.Lock()
        self._decision: NonResumableCloseDecision | None = None
        self._audit_attempted = False
        self._audit_succeeded = False

    async def close(
        self,
        kind: NonResumableCloseKind,
    ) -> NonResumableConnectionSnapshot:
        if not isinstance(kind, NonResumableCloseKind):
            _invalid("close_kind")
        async with self._lock:
            if self._decision is not None:
                return await self._snapshot_unlocked()
            decision = _DECISIONS[kind]
            self._decision = decision
            revoked = dataclasses.replace(self._context, resume_eligible=False)
            entry = await self._index.lookup_connection(self._context.connection_id)
            if entry is not None:
                if (
                    entry.session_context.session_id != self._context.session_id
                    or entry.session_context.connection_epoch
                    != self._context.connection_epoch
                ):
                    _state_error("logical_session_owner_mismatch")
                await self._index.replace_authority_context(revoked)
                self._context = revoked

            cancelled: asyncio.CancelledError | None = None
            try:
                await self._close_connection_unlocked(decision.close_reason)
            except asyncio.CancelledError as error:
                cancelled = error
            await self._emit_audit_unlocked(decision)
            try:
                await self._emit_lifecycle_audit_unlocked(decision)
            except asyncio.CancelledError as error:
                if cancelled is None:
                    cancelled = error
            if cancelled is not None:
                raise cancelled
            return await self._snapshot_unlocked()

    async def require_resumable(self) -> None:
        async with self._lock:
            if self._decision is not None:
                raise NsRuntimeIamDeniedError(
                    details={
                        "component": "logical_connection",
                        "operation": "connection_resume",
                        "reason": "connection_non_resumable",
                    },
                )

    async def retry_cleanup(self) -> bool:
        async with self._lock:
            entry = await self._index.lookup_connection(self._context.connection_id)
            if entry is None:
                return True
            if entry.state is not LogicalConnectionState.CLOSING:
                _state_error("closing_state_required")
            if self._transport is None:
                _state_error("transport_close_owner_missing")
            try:
                await self._transport.close()
            except asyncio.CancelledError:
                raise
            except Exception:
                return False
            await self._index.transition(
                self._context.connection_id,
                LogicalConnectionState.CLOSED,
            )
            return True

    async def snapshot(self) -> NonResumableConnectionSnapshot:
        async with self._lock:
            return await self._snapshot_unlocked()

    async def _close_connection_unlocked(
        self,
        reason: LogicalConnectionCloseReason,
    ) -> None:
        if self._grace is not None:
            grace = await self._grace.snapshot()
            if grace.phase in {
                ReconnectGracePhase.WAITING,
                ReconnectGracePhase.CLAIMED,
            }:
                await self._grace.terminate(reason)
                return
        entry = await self._index.lookup_connection(self._context.connection_id)
        if entry is not None and entry.state is not LogicalConnectionState.CLOSING:
            await self._index.transition(
                self._context.connection_id,
                LogicalConnectionState.CLOSING,
                close_reason=reason,
            )
        if self._transport is None:
            return
        try:
            await self._transport.close()
        except asyncio.CancelledError:
            raise
        except Exception:
            return
        entry = await self._index.lookup_connection(self._context.connection_id)
        if entry is not None and entry.state is LogicalConnectionState.CLOSING:
            await self._index.transition(
                self._context.connection_id,
                LogicalConnectionState.CLOSED,
            )

    async def _emit_audit_unlocked(
        self,
        decision: NonResumableCloseDecision,
    ) -> None:
        self._audit_attempted = True
        event = ConnectionSecurityAuditEvent(
            classification=decision.kind,
            close_reason=decision.close_reason,
            public_error=decision.public_error,
            connection_summary=logical_id_summary(self._context.connection_id),
            component_type=self._context.component_type,
            connection_epoch=self._context.connection_epoch,
            occurred_at=self._clock.utc_now(),
        )
        try:
            await self._audit_sink.emit(event)
        except Exception:
            self._audit_succeeded = False
            return
        self._audit_succeeded = True

    async def _emit_lifecycle_audit_unlocked(
        self,
        decision: NonResumableCloseDecision,
    ) -> None:
        if self._lifecycle_audit is None:
            return
        if decision.kind is NonResumableCloseKind.KICK:
            kind = ConnectionAuditKind.KICK
        elif decision.kind is NonResumableCloseKind.POLICY_NON_RECOVERABLE:
            kind = ConnectionAuditKind.NON_RESUMABLE_CLOSE
        else:
            kind = ConnectionAuditKind.SECURITY_CLOSE
        await self._lifecycle_audit.emit(
            kind=kind,
            outcome=ConnectionAuditOutcome.ENFORCED,
            connection_epoch=self._context.connection_epoch,
            close_reason=decision.close_reason,
        )

    async def _snapshot_unlocked(self) -> NonResumableConnectionSnapshot:
        entry = await self._index.lookup_connection(self._context.connection_id)
        state = entry.state if entry is not None else LogicalConnectionState.CLOSED
        return NonResumableConnectionSnapshot(
            non_resumable=self._decision is not None,
            decision=self._decision,
            state=state,
            audit_attempted=self._audit_attempted,
            audit_succeeded=self._audit_succeeded,
        )


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Non-resumable close dependency is invalid.",
        details={"component": "logical_connection", "field": field_name},
    )


def _state_error(reason: str) -> None:
    raise NsStateError(
        "Non-resumable close operation is invalid.",
        details={
            "component": "logical_connection",
            "operation": "non_resumable_close",
            "reason": reason,
        },
    )


__all__ = (
    "ConnectionSecurityAuditEvent",
    "ConnectionSecurityAuditSink",
    "DeterministicTestSecurityAuditSink",
    "NonResumableCloseDecision",
    "NonResumableCloseKind",
    "NonResumableConnectionGuard",
    "NonResumableConnectionSnapshot",
    "NonResumablePublicError",
)
