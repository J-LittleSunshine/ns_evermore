# -*- coding: utf-8 -*-
"""Supervised reconnect grace for an otherwise active logical connection."""

from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass, field
from enum import Enum

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import NsStateError, NsValidationError
from ns_common.time import Clock

from .binding import LogicalConnectionTransportMap
from .hello import HelloResumeRequest
from .index import LocalConnectionIndex
from .session import SessionContext
from .state import LogicalConnectionCloseReason, LogicalConnectionState


@dataclass(frozen=True, slots=True, kw_only=True)
class ReconnectGracePolicy:
    timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        value = self.timeout_seconds
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) <= 0
        ):
            _invalid("timeout_seconds")


class ReconnectGracePhase(str, Enum):
    IDLE = "idle"
    WAITING = "waiting"
    CLAIMED = "claimed"
    RESUMED = "resumed"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True, kw_only=True)
class ReconnectGraceClaim:
    connection_id: str = field(repr=False)
    session_id: str = field(repr=False)
    connection_epoch: int
    deadline_monotonic: float


@dataclass(frozen=True, slots=True, kw_only=True)
class ReconnectGraceSnapshot:
    phase: ReconnectGracePhase
    started_monotonic: float | None
    deadline_monotonic: float | None
    connection_epoch: int
    resume_claimed: bool
    terminal_reason: LogicalConnectionCloseReason | None
    deadline_pending: bool


class ReconnectGraceService:
    def __init__(
        self,
        *,
        session_context: SessionContext,
        connection_index: LocalConnectionIndex,
        transport_mapping: LogicalConnectionTransportMap,
        clock: Clock,
        task_supervisor: TaskSupervisor,
        task_sequence: int,
        policy: ReconnectGracePolicy = ReconnectGracePolicy(),
    ) -> None:
        if not isinstance(session_context, SessionContext):
            _invalid("session_context")
        if not isinstance(connection_index, LocalConnectionIndex):
            _invalid("connection_index")
        if not isinstance(transport_mapping, LogicalConnectionTransportMap):
            _invalid("transport_mapping")
        if not isinstance(clock, Clock):
            _invalid("clock")
        if not isinstance(task_supervisor, TaskSupervisor):
            _invalid("task_supervisor")
        if (
            isinstance(task_sequence, bool)
            or not isinstance(task_sequence, int)
            or task_sequence < 0
        ):
            _invalid("task_sequence")
        if not isinstance(policy, ReconnectGracePolicy):
            _invalid("policy")
        self._context = session_context
        self._index = connection_index
        self._mapping = transport_mapping
        self._clock = clock
        self._supervisor = task_supervisor
        self._task_sequence = task_sequence
        self._policy = policy
        self._lock = asyncio.Lock()
        self._phase = ReconnectGracePhase.IDLE
        self._started_at: float | None = None
        self._deadline: float | None = None
        self._terminal_reason: LogicalConnectionCloseReason | None = None
        self._deadline_task: asyncio.Task[object] | None = None

    async def enter(
        self,
        *,
        transport_session_id: str,
    ) -> ReconnectGraceSnapshot:
        if not isinstance(transport_session_id, str) or not transport_session_id:
            _invalid("transport_session_id")
        async with self._lock:
            if self._phase is ReconnectGracePhase.WAITING:
                return self._snapshot_unlocked()
            if self._phase is not ReconnectGracePhase.IDLE:
                _state_error("grace_already_resolved")
            entry = await self._index.lookup_connection(self._context.connection_id)
            mapping = await self._mapping.snapshot()
            if (
                entry is None
                or entry.session_context != self._context
                or entry.state is not LogicalConnectionState.ACTIVE
            ):
                _state_error("active_session_required")
            if (
                mapping.session_context != self._context
                or mapping.transport is None
                or mapping.transport.transport_session_id != transport_session_id
            ):
                _state_error("transport_session_owner_mismatch")
            started_at = self._clock.monotonic()
            deadline = started_at + float(self._policy.timeout_seconds)
            if not math.isfinite(started_at) or not math.isfinite(deadline):
                _state_error("invalid_grace_deadline")
            await self._index.suspend_active_target(self._context.connection_id)
            try:
                await self._mapping.detach_transport_session(
                    transport_session_id=transport_session_id,
                )
            except BaseException:
                await self._close_logical_unlocked(
                    LogicalConnectionCloseReason.INTERNAL_ERROR,
                )
                raise
            self._phase = ReconnectGracePhase.WAITING
            self._started_at = started_at
            self._deadline = deadline
            try:
                self._deadline_task = self._supervisor.create_task(
                    self._deadline_loop(),
                    name=f"logical-grace-{self._task_sequence}-deadline",
                    cancel_order=15,
                )
            except BaseException:
                await self._close_logical_unlocked(
                    LogicalConnectionCloseReason.INTERNAL_ERROR,
                )
                raise
            return self._snapshot_unlocked()

    async def claim_resume(
        self,
        request: HelloResumeRequest,
    ) -> ReconnectGraceClaim:
        if not isinstance(request, HelloResumeRequest):
            _invalid("resume_request")
        async with self._lock:
            if self._phase is not ReconnectGracePhase.WAITING:
                _state_error("grace_not_waiting")
            assert self._deadline is not None
            if self._clock.monotonic() >= self._deadline:
                await self._expire_unlocked()
                _state_error("grace_expired")
            if request.connection_id != self._context.connection_id:
                _state_error("resume_connection_mismatch")
            if request.connection_epoch != self._context.connection_epoch:
                _state_error("resume_epoch_mismatch")
            if (
                request.session_id is not None
                and request.session_id != self._context.session_id
            ):
                _state_error("resume_session_mismatch")
            self._phase = ReconnectGracePhase.CLAIMED
            self._cancel_deadline_now()
            return ReconnectGraceClaim(
                connection_id=self._context.connection_id,
                session_id=self._context.session_id,
                connection_epoch=self._context.connection_epoch,
                deadline_monotonic=self._deadline,
            )

    async def complete_resume(self, session_context: SessionContext) -> None:
        if not isinstance(session_context, SessionContext):
            _invalid("session_context")
        async with self._lock:
            if self._phase is not ReconnectGracePhase.CLAIMED:
                _state_error("resume_not_claimed")
            if (
                session_context.connection_id != self._context.connection_id
                or session_context.connection_epoch
                != self._context.connection_epoch + 1
                or session_context.session_id == self._context.session_id
            ):
                _state_error("resumed_context_mismatch")
            entry = await self._index.lookup_connection(
                session_context.connection_id,
            )
            mapping = await self._mapping.snapshot()
            if (
                entry is None
                or entry.session_context != session_context
                or not entry.active_target_eligible
                or mapping.session_context != session_context
                or mapping.transport is None
            ):
                _state_error("resumed_ownership_not_published")
            self._context = session_context
            self._phase = ReconnectGracePhase.RESUMED

    async def terminate(self, reason: LogicalConnectionCloseReason) -> None:
        if not isinstance(reason, LogicalConnectionCloseReason):
            _invalid("close_reason")
        async with self._lock:
            await self._close_logical_unlocked(reason)

    async def snapshot(self) -> ReconnectGraceSnapshot:
        async with self._lock:
            return self._snapshot_unlocked()

    async def _deadline_loop(self) -> None:
        try:
            assert self._deadline is not None
            await self._clock.sleep(
                max(0.0, self._deadline - self._clock.monotonic()),
            )
            async with self._lock:
                if self._phase is ReconnectGracePhase.WAITING:
                    await self._expire_unlocked()
        except asyncio.CancelledError:
            raise

    async def _expire_unlocked(self) -> None:
        await self._close_logical_unlocked(
            LogicalConnectionCloseReason.TRANSPORT_DISCONNECTED,
        )

    async def _close_logical_unlocked(
        self,
        reason: LogicalConnectionCloseReason,
    ) -> None:
        if self._terminal_reason is None:
            self._terminal_reason = reason
        self._cancel_deadline_now()
        entry = await self._index.lookup_connection(self._context.connection_id)
        if entry is not None and entry.state is not LogicalConnectionState.CLOSING:
            await self._index.transition(
                self._context.connection_id,
                LogicalConnectionState.CLOSING,
                close_reason=self._terminal_reason,
            )
        entry = await self._index.lookup_connection(self._context.connection_id)
        if entry is not None and entry.state is LogicalConnectionState.CLOSING:
            await self._index.transition(
                self._context.connection_id,
                LogicalConnectionState.CLOSED,
            )
        self._phase = ReconnectGracePhase.CLOSED

    def _cancel_deadline_now(self) -> None:
        task = self._deadline_task
        if (
            task is not None
            and task is not asyncio.current_task()
            and not task.done()
        ):
            task.cancel()

    def _snapshot_unlocked(self) -> ReconnectGraceSnapshot:
        task = self._deadline_task
        return ReconnectGraceSnapshot(
            phase=self._phase,
            started_monotonic=self._started_at,
            deadline_monotonic=self._deadline,
            connection_epoch=self._context.connection_epoch,
            resume_claimed=self._phase is ReconnectGracePhase.CLAIMED,
            terminal_reason=self._terminal_reason,
            deadline_pending=task is not None and not task.done(),
        )


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Reconnect grace dependency is invalid.",
        details={"component": "logical_connection", "field": field_name},
    )


def _state_error(reason: str) -> None:
    raise NsStateError(
        "Reconnect grace operation is invalid.",
        details={
            "component": "logical_connection",
            "operation": "reconnect_grace",
            "reason": reason,
        },
    )


__all__ = (
    "ReconnectGraceClaim",
    "ReconnectGracePhase",
    "ReconnectGracePolicy",
    "ReconnectGraceService",
    "ReconnectGraceSnapshot",
)
