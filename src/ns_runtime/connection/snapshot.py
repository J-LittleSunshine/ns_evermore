# -*- coding: utf-8 -*-
"""Frozen, redacted, asynchronously readable P05 connection projection."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from ns_common.exceptions import NsValidationError
from ns_common.time import Clock

from .audit import logical_id_summary
from .drain import ConnectionDrainService, DrainSnapshot
from .grace import ReconnectGraceService, ReconnectGraceSnapshot
from .heartbeat import ConnectionHeartbeatService, HeartbeatSnapshot
from .index import LocalConnectionIndex
from .reauth import SessionExpiryController, SessionExpirySnapshot
from .security import NonResumableConnectionGuard, NonResumableConnectionSnapshot
from .session import SessionContext
from .state import LogicalConnectionCloseReason, LogicalConnectionState


class ConnectionCapabilityClass(str, Enum):
    LIFECYCLE = "lifecycle"
    HEARTBEAT = "heartbeat"
    RESUME = "resume"
    MANAGEMENT = "management"
    OTHER = "other"


_CAPABILITY_CLASSES = {
    "runtime.connection": ConnectionCapabilityClass.LIFECYCLE,
    "runtime.heartbeat": ConnectionCapabilityClass.HEARTBEAT,
    "runtime.resume": ConnectionCapabilityClass.RESUME,
    "runtime.management": ConnectionCapabilityClass.MANAGEMENT,
}


@dataclass(frozen=True, slots=True, kw_only=True)
class SafeConnectionSnapshot:
    connection_summary: str
    session_summary: str
    state: LogicalConnectionState
    close_reason: LogicalConnectionCloseReason | None
    active_target_eligible: bool
    component_type: str
    connection_epoch: int
    protocol_version: str
    capability_classes: frozenset[ConnectionCapabilityClass]
    heartbeat: HeartbeatSnapshot | None
    grace: ReconnectGraceSnapshot | None
    drain: DrainSnapshot | None
    reauth: SessionExpirySnapshot | None
    security_close: NonResumableConnectionSnapshot | None
    observed_at: datetime
    index_mutation_sequence: int
    coherent: bool
    complete: bool

    def __post_init__(self) -> None:
        _validate_summary(self.connection_summary, "connection_summary")
        _validate_summary(self.session_summary, "session_summary")
        if not isinstance(self.state, LogicalConnectionState):
            _invalid("state")
        if self.close_reason is not None and not isinstance(
            self.close_reason,
            LogicalConnectionCloseReason,
        ):
            _invalid("close_reason")
        if not isinstance(self.active_target_eligible, bool):
            _invalid("active_target_eligible")
        if not isinstance(self.component_type, str) or not self.component_type:
            _invalid("component_type")
        if (
            isinstance(self.connection_epoch, bool)
            or not isinstance(self.connection_epoch, int)
            or self.connection_epoch < 0
        ):
            _invalid("connection_epoch")
        if not isinstance(self.protocol_version, str) or not self.protocol_version:
            _invalid("protocol_version")
        if not isinstance(self.capability_classes, frozenset) or any(
            not isinstance(item, ConnectionCapabilityClass)
            for item in self.capability_classes
        ):
            _invalid("capability_classes")
        for name, expected in (
            ("heartbeat", HeartbeatSnapshot),
            ("grace", ReconnectGraceSnapshot),
            ("drain", DrainSnapshot),
            ("reauth", SessionExpirySnapshot),
            ("security_close", NonResumableConnectionSnapshot),
        ):
            value = getattr(self, name)
            if value is not None and not isinstance(value, expected):
                _invalid(name)
        object.__setattr__(
            self,
            "observed_at",
            _utc(self.observed_at, "observed_at"),
        )
        if (
            isinstance(self.index_mutation_sequence, bool)
            or not isinstance(self.index_mutation_sequence, int)
            or self.index_mutation_sequence < 0
        ):
            _invalid("index_mutation_sequence")
        for name in ("coherent", "complete"):
            if not isinstance(getattr(self, name), bool):
                _invalid(name)
        if self.active_target_eligible and self.state is not LogicalConnectionState.ACTIVE:
            _invalid("active_target_state")


@dataclass(frozen=True, slots=True, kw_only=True)
class _SafeSessionProjection:
    session_summary: str
    component_type: str
    connection_epoch: int
    protocol_version: str
    capability_classes: frozenset[ConnectionCapabilityClass]


class SafeConnectionSnapshotReader:
    """Read an observational projection; this is not P08 state authority."""

    def __init__(
        self,
        *,
        session_context: SessionContext,
        connection_index: LocalConnectionIndex,
        clock: Clock,
        heartbeat_service: ConnectionHeartbeatService | None = None,
        grace_service: ReconnectGraceService | None = None,
        drain_service: ConnectionDrainService | None = None,
        expiry_controller: SessionExpiryController | None = None,
        security_guard: NonResumableConnectionGuard | None = None,
        max_consistency_attempts: int = 3,
    ) -> None:
        if not isinstance(session_context, SessionContext):
            _invalid("session_context")
        if not isinstance(connection_index, LocalConnectionIndex):
            _invalid("connection_index")
        if not isinstance(clock, Clock):
            _invalid("clock")
        for value, expected, name in (
            (heartbeat_service, ConnectionHeartbeatService, "heartbeat_service"),
            (grace_service, ReconnectGraceService, "grace_service"),
            (drain_service, ConnectionDrainService, "drain_service"),
            (expiry_controller, SessionExpiryController, "expiry_controller"),
            (security_guard, NonResumableConnectionGuard, "security_guard"),
        ):
            if value is not None and not isinstance(value, expected):
                _invalid(name)
        if (
            isinstance(max_consistency_attempts, bool)
            or not isinstance(max_consistency_attempts, int)
            or not 1 <= max_consistency_attempts <= 10
        ):
            _invalid("max_consistency_attempts")
        self._connection_id = session_context.connection_id
        self._connection_summary = logical_id_summary(
            session_context.connection_id,
        )
        self._projection = _project(session_context)
        self._index = connection_index
        self._clock = clock
        self._heartbeat = heartbeat_service
        self._grace = grace_service
        self._drain = drain_service
        self._expiry = expiry_controller
        self._security = security_guard
        self._max_attempts = max_consistency_attempts
        self._lock = asyncio.Lock()

    async def read(self) -> SafeConnectionSnapshot:
        async with self._lock:
            return await self._read_unlocked()

    async def _read_unlocked(self) -> SafeConnectionSnapshot:
        coherent = False
        complete = True
        heartbeat: HeartbeatSnapshot | None = None
        grace: ReconnectGraceSnapshot | None = None
        drain: DrainSnapshot | None = None
        reauth: SessionExpirySnapshot | None = None
        security: NonResumableConnectionSnapshot | None = None
        final_index = await self._index.snapshot()
        for _ in range(self._max_attempts):
            before = await self._index.snapshot()
            entry = before.by_connection_id.get(self._connection_id)
            if entry is not None:
                self._projection = _project(entry.session_context)

            heartbeat, heartbeat_ok = await _optional_snapshot(self._heartbeat)
            grace, grace_ok = await _optional_snapshot(self._grace)
            drain, drain_ok = await _optional_snapshot(self._drain)
            reauth, reauth_ok = await _optional_snapshot(self._expiry)
            security, security_ok = await _optional_snapshot(self._security)
            complete = all((
                heartbeat_ok,
                grace_ok,
                drain_ok,
                reauth_ok,
                security_ok,
            ))

            final_index = await self._index.snapshot()
            coherent = before.mutation_sequence == final_index.mutation_sequence
            if coherent:
                break

        entry = final_index.by_connection_id.get(self._connection_id)
        if entry is not None:
            self._projection = _project(entry.session_context)
            state = entry.state
            active_target_eligible = entry.active_target_eligible
        else:
            state = LogicalConnectionState.CLOSED
            active_target_eligible = False
        return SafeConnectionSnapshot(
            connection_summary=self._connection_summary,
            session_summary=self._projection.session_summary,
            state=state,
            close_reason=_close_reason(
                heartbeat=heartbeat,
                grace=grace,
                drain=drain,
                reauth=reauth,
                security=security,
            ),
            active_target_eligible=active_target_eligible,
            component_type=self._projection.component_type,
            connection_epoch=self._projection.connection_epoch,
            protocol_version=self._projection.protocol_version,
            capability_classes=self._projection.capability_classes,
            heartbeat=heartbeat,
            grace=grace,
            drain=drain,
            reauth=reauth,
            security_close=security,
            observed_at=self._clock.utc_now(),
            index_mutation_sequence=final_index.mutation_sequence,
            coherent=coherent,
            complete=complete,
        )


def _project(context: SessionContext) -> _SafeSessionProjection:
    classes = {
        _CAPABILITY_CLASSES.get(
            capability,
            ConnectionCapabilityClass.OTHER,
        )
        for capability in context.capabilities
    }
    return _SafeSessionProjection(
        session_summary=logical_id_summary(context.session_id),
        component_type=context.component_type,
        connection_epoch=context.connection_epoch,
        protocol_version=str(context.protocol_version),
        capability_classes=frozenset(classes),
    )


async def _optional_snapshot(service):
    if service is None:
        return None, True
    try:
        return await service.snapshot(), True
    except Exception:
        return None, False


def _close_reason(
    *,
    heartbeat: HeartbeatSnapshot | None,
    grace: ReconnectGraceSnapshot | None,
    drain: DrainSnapshot | None,
    reauth: SessionExpirySnapshot | None,
    security: NonResumableConnectionSnapshot | None,
) -> LogicalConnectionCloseReason | None:
    if security is not None and security.decision is not None:
        return security.decision.close_reason
    for snapshot in (drain, heartbeat, grace):
        if snapshot is not None and snapshot.terminal_reason is not None:
            return snapshot.terminal_reason
    if reauth is not None and reauth.expired:
        return LogicalConnectionCloseReason.AUTH_FAILED
    return None


def _validate_summary(value: object, field_name: str) -> None:
    if (
        not isinstance(value, str)
        or not value.startswith("sha256:")
        or len(value) != 23
    ):
        _invalid(field_name)


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
        "Safe connection snapshot value is invalid.",
        details={"component": "logical_connection", "field": field_name},
    )


__all__ = (
    "ConnectionCapabilityClass",
    "SafeConnectionSnapshot",
    "SafeConnectionSnapshotReader",
)
