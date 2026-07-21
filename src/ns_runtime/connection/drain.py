# -*- coding: utf-8 -*-
"""One-way bounded logical connection drain lifecycle."""

from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass
from enum import Enum

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import (
    NsRuntimeProtocolViolationError,
    NsStateError,
    NsValidationError,
)
from ns_common.time import Clock
from ns_runtime.protocol import (
    BUILTIN_MESSAGE_REGISTRY,
    Envelope,
    JsonV1Codec,
    MessageTypeRegistry,
)
from ns_runtime.transport import TransportSession

from .index import LocalConnectionIndex
from .state import LogicalConnectionCloseReason, LogicalConnectionState


DRAIN_ALLOWED_MESSAGE_TYPES = frozenset({
    "connection.heartbeat",
    "connection.heartbeat_ack",
    "connection.reauth",
    "delivery.ack",
    "delivery.nack",
    "delivery.defer",
    "runtime.control.health",
    "runtime.error",
})


class DrainingMessageDisposition(str, Enum):
    ALLOWED_LIFECYCLE_OR_EXISTING_DELIVERY = "allowed_lifecycle_or_existing_delivery"
    REJECT_NEW_WORK = "reject_new_work"


@dataclass(frozen=True, slots=True, kw_only=True)
class DrainPolicy:
    timeout_seconds: float

    def __post_init__(self) -> None:
        value = self.timeout_seconds
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) <= 0
        ):
            _invalid("timeout_seconds")


@dataclass(frozen=True, slots=True, kw_only=True)
class DrainSnapshot:
    state: LogicalConnectionState
    started_monotonic: float | None
    deadline_monotonic: float | None
    terminal_reason: LogicalConnectionCloseReason | None
    timeout_pending: bool


class DrainingMessageGate:
    """Classify only; this does not implement delivery or control processors."""

    def __init__(
        self,
        registry: MessageTypeRegistry = BUILTIN_MESSAGE_REGISTRY,
    ) -> None:
        if not isinstance(registry, MessageTypeRegistry):
            _invalid("registry")
        self._registry = registry
        for message_type in DRAIN_ALLOWED_MESSAGE_TYPES:
            self._registry.require(message_type)

    def classify(self, message_type: str) -> DrainingMessageDisposition:
        if not isinstance(message_type, str) or not message_type:
            _invalid("message_type")
        self._registry.require(message_type)
        if message_type in DRAIN_ALLOWED_MESSAGE_TYPES:
            return DrainingMessageDisposition.ALLOWED_LIFECYCLE_OR_EXISTING_DELIVERY
        return DrainingMessageDisposition.REJECT_NEW_WORK


class ConnectionDrainEnvelopeHandler:
    """Accept only a self-scoped P03 connection.drain lifecycle Envelope."""

    def __init__(
        self,
        *,
        drain_service: "ConnectionDrainService",
        codec: JsonV1Codec,
        schema_key: str,
        registry: MessageTypeRegistry = BUILTIN_MESSAGE_REGISTRY,
    ) -> None:
        if not isinstance(drain_service, ConnectionDrainService):
            _invalid("drain_service")
        if not isinstance(codec, JsonV1Codec):
            _invalid("codec")
        if not isinstance(schema_key, str) or not schema_key:
            _invalid("schema_key")
        if not isinstance(registry, MessageTypeRegistry):
            _invalid("registry")
        self._drain_service = drain_service
        self._codec = codec
        self._schema_key = schema_key
        self._registry = registry

    async def handle_text(self, text: str) -> DrainSnapshot:
        inbound = self._codec.decode_inbound(text)
        if inbound.message.type != "connection.drain":
            raise _drain_protocol_error("connection_drain_required")
        if any(
            value is not None
            for value in (
                inbound.target,
                inbound.route,
                inbound.delivery,
                inbound.stream,
                inbound.payload,
                inbound.callback,
                inbound.trace,
                inbound.extensions,
            )
        ):
            raise _drain_protocol_error("self_scoped_empty_drain_required")
        shape = Envelope(protocol=inbound.protocol, message=inbound.message)
        self._registry.validate_envelope(shape, self._schema_key)
        return await self._drain_service.begin()


class ConnectionDrainService:
    def __init__(
        self,
        *,
        connection_id: str,
        connection_index: LocalConnectionIndex,
        transport_session: TransportSession,
        clock: Clock,
        task_supervisor: TaskSupervisor,
        task_sequence: int,
        policy: DrainPolicy,
    ) -> None:
        if not isinstance(connection_id, str) or not connection_id:
            _invalid("connection_id")
        if not isinstance(connection_index, LocalConnectionIndex):
            _invalid("connection_index")
        if not isinstance(transport_session, TransportSession):
            _invalid("transport_session")
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
        if not isinstance(policy, DrainPolicy):
            _invalid("policy")
        self._connection_id = connection_id
        self._index = connection_index
        self._transport = transport_session
        self._clock = clock
        self._supervisor = task_supervisor
        self._task_sequence = task_sequence
        self._policy = policy
        self._lock = asyncio.Lock()
        self._started_at: float | None = None
        self._deadline: float | None = None
        self._terminal_reason: LogicalConnectionCloseReason | None = None
        self._timeout_task: asyncio.Task[object] | None = None

    async def begin(self) -> DrainSnapshot:
        async with self._lock:
            entry = await self._index.lookup_connection(self._connection_id)
            if entry is None:
                _state_error("connection_not_indexed")
            assert entry is not None
            if entry.state is LogicalConnectionState.DRAINING:
                return await self._snapshot_unlocked()
            if entry.state is not LogicalConnectionState.ACTIVE:
                _state_error("active_state_required")
            started_at = self._clock.monotonic()
            deadline = started_at + float(self._policy.timeout_seconds)
            if not math.isfinite(started_at) or not math.isfinite(deadline):
                _state_error("invalid_drain_deadline")
            await self._index.transition(
                self._connection_id,
                LogicalConnectionState.DRAINING,
            )
            self._started_at = started_at
            self._deadline = deadline
            try:
                self._timeout_task = self._supervisor.create_task(
                    self._timeout_loop(),
                    name=f"logical-drain-{self._task_sequence}-deadline",
                    cancel_order=15,
                )
            except BaseException:
                await self._terminate_unlocked(
                    LogicalConnectionCloseReason.INTERNAL_ERROR,
                )
                raise
            return await self._snapshot_unlocked()

    async def complete(self) -> bool:
        return await self.terminate(LogicalConnectionCloseReason.NORMAL)

    async def terminate(self, reason: LogicalConnectionCloseReason) -> bool:
        if not isinstance(reason, LogicalConnectionCloseReason):
            _invalid("close_reason")
        async with self._lock:
            return await self._terminate_unlocked(reason)

    async def retry_cleanup(self) -> bool:
        async with self._lock:
            entry = await self._index.lookup_connection(self._connection_id)
            if entry is None:
                return True
            if entry.state is not LogicalConnectionState.CLOSING:
                _state_error("closing_state_required")
            try:
                await self._transport.close()
            except asyncio.CancelledError:
                raise
            except Exception:
                return False
            await self._index.transition(
                self._connection_id,
                LogicalConnectionState.CLOSED,
            )
            return True

    async def snapshot(self) -> DrainSnapshot:
        async with self._lock:
            return await self._snapshot_unlocked()

    async def _timeout_loop(self) -> None:
        try:
            assert self._deadline is not None
            remaining = max(0.0, self._deadline - self._clock.monotonic())
            await self._clock.sleep(remaining)
            async with self._lock:
                if self._terminal_reason is not None:
                    return
                await self._terminate_unlocked(
                    LogicalConnectionCloseReason.DRAIN_TIMEOUT,
                )
        except asyncio.CancelledError:
            raise

    async def _terminate_unlocked(
        self,
        reason: LogicalConnectionCloseReason,
    ) -> bool:
        if self._terminal_reason is None:
            self._terminal_reason = reason
        self._cancel_timeout_now()
        entry = await self._index.lookup_connection(self._connection_id)
        if entry is None:
            return True
        if entry.state is not LogicalConnectionState.CLOSING:
            try:
                await self._index.transition(
                    self._connection_id,
                    LogicalConnectionState.CLOSING,
                    close_reason=self._terminal_reason,
                )
            except NsStateError:
                entry = await self._index.lookup_connection(self._connection_id)
                if entry is None:
                    return True
                if entry.state is not LogicalConnectionState.CLOSING:
                    raise
        try:
            await self._transport.close()
        except asyncio.CancelledError:
            raise
        except Exception:
            return False
        entry = await self._index.lookup_connection(self._connection_id)
        if entry is not None and entry.state is LogicalConnectionState.CLOSING:
            await self._index.transition(
                self._connection_id,
                LogicalConnectionState.CLOSED,
            )
        return True

    def _cancel_timeout_now(self) -> None:
        task = self._timeout_task
        if (
            task is not None
            and task is not asyncio.current_task()
            and not task.done()
        ):
            task.cancel()

    async def _snapshot_unlocked(self) -> DrainSnapshot:
        entry = await self._index.lookup_connection(self._connection_id)
        state = (
            entry.state
            if entry is not None
            else LogicalConnectionState.CLOSED
        )
        task = self._timeout_task
        return DrainSnapshot(
            state=state,
            started_monotonic=self._started_at,
            deadline_monotonic=self._deadline,
            terminal_reason=self._terminal_reason,
            timeout_pending=task is not None and not task.done(),
        )


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Connection drain dependency is invalid.",
        details={"component": "logical_connection", "field": field_name},
    )


def _state_error(reason: str) -> None:
    raise NsStateError(
        "Connection drain operation is invalid.",
        details={
            "component": "logical_connection",
            "operation": "connection_drain",
            "reason": reason,
        },
    )


def _drain_protocol_error(reason: str) -> NsRuntimeProtocolViolationError:
    return NsRuntimeProtocolViolationError(
        details={
            "component": "logical_connection",
            "operation": "connection_drain",
            "reason": reason,
        },
    )


__all__ = (
    "ConnectionDrainService",
    "ConnectionDrainEnvelopeHandler",
    "DRAIN_ALLOWED_MESSAGE_TYPES",
    "DrainPolicy",
    "DrainSnapshot",
    "DrainingMessageDisposition",
    "DrainingMessageGate",
)
