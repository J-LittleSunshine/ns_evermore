# -*- coding: utf-8 -*-
"""Distinct transport-native and Envelope heartbeat lifecycle boundaries."""

from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import (
    NsRuntimeProtocolViolationError,
    NsStateError,
    NsValidationError,
)
from ns_common.identifiers import IdentifierFactory, NsIdentifierKind
from ns_common.time import Clock
from ns_runtime.protocol import (
    BUILTIN_MESSAGE_REGISTRY,
    Envelope,
    JsonV1Codec,
    MessageGroup,
    MessageTypeRegistry,
    PayloadGroup,
    ProtocolGroup,
    WIRE_CODEC_JSON_V1,
    canonical_serialize,
)
from ns_runtime.transport import TransportSession

from .accepted import _iso_utc
from .index import LocalConnectionIndex
from .session import SessionContext
from .state import LogicalConnectionCloseReason, LogicalConnectionState


HEARTBEAT_PAYLOAD_FIELDS = frozenset({
    "connection_id",
    "session_id",
    "connection_epoch",
    "sequence",
    "sent_at",
})
HEARTBEAT_ACK_PAYLOAD_FIELDS = frozenset({
    "connection_id",
    "session_id",
    "connection_epoch",
    "sequence",
    "server_time",
})


@dataclass(frozen=True, slots=True, kw_only=True)
class HeartbeatPolicy:
    native_interval_seconds: float
    envelope_timeout_seconds: float

    def __post_init__(self) -> None:
        for name in ("native_interval_seconds", "envelope_timeout_seconds"):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or float(value) <= 0
            ):
                _invalid(name)


class EnvelopeHeartbeatOutcome(str, Enum):
    ACCEPTED = "accepted"
    DUPLICATE = "duplicate"


@dataclass(frozen=True, slots=True, kw_only=True)
class HeartbeatSnapshot:
    running: bool
    last_envelope_sequence: int | None
    last_envelope_monotonic: float
    native_ping_count: int
    envelope_accepted_count: int
    envelope_duplicate_count: int
    terminal_reason: LogicalConnectionCloseReason | None


class ConnectionHeartbeatService:
    """P05-only heartbeat handler; never dispatches to a business pipeline."""

    def __init__(
        self,
        *,
        session_context: SessionContext,
        connection_index: LocalConnectionIndex,
        transport_session: TransportSession,
        clock: Clock,
        task_supervisor: TaskSupervisor,
        task_sequence: int,
        identifier_factory: IdentifierFactory,
        policy: HeartbeatPolicy,
        codec: JsonV1Codec,
        registry: MessageTypeRegistry = BUILTIN_MESSAGE_REGISTRY,
    ) -> None:
        if not isinstance(session_context, SessionContext):
            _invalid("session_context")
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
        if not isinstance(identifier_factory, IdentifierFactory):
            _invalid("identifier_factory")
        if not isinstance(policy, HeartbeatPolicy):
            _invalid("policy")
        if not isinstance(codec, JsonV1Codec) or codec.name != session_context.wire_codec:
            _invalid("codec")
        if not isinstance(registry, MessageTypeRegistry):
            _invalid("registry")
        if session_context.wire_codec != WIRE_CODEC_JSON_V1:
            _invalid("session_codec")
        self._context = session_context
        self._index = connection_index
        self._transport = transport_session
        self._clock = clock
        self._supervisor = task_supervisor
        self._task_sequence = task_sequence
        self._identifier_factory = identifier_factory
        self._policy = policy
        self._codec = codec
        self._registry = registry
        self._lifecycle_lock = asyncio.Lock()
        self._start_lock = asyncio.Lock()
        self._started = False
        self._running = True
        self._last_sequence: int | None = None
        self._last_envelope_at = clock.monotonic()
        self._native_ping_count = 0
        self._envelope_accepted_count = 0
        self._envelope_duplicate_count = 0
        self._terminal_reason: LogicalConnectionCloseReason | None = None
        self._native_task: asyncio.Task[object] | None = None
        self._watchdog_task: asyncio.Task[object] | None = None

    async def start(self) -> None:
        async with self._start_lock:
            if self._started:
                _state_error("heartbeat_already_started")
            entry = await self._index.lookup_connection(self._context.connection_id)
            if (
                entry is None
                or entry.session_context != self._context
                or entry.state is not LogicalConnectionState.ACTIVE
            ):
                _state_error("active_session_required")
            self._started = True
            self._running = True
            self._last_envelope_at = self._clock.monotonic()
            self._native_task = self._supervisor.create_task(
                self._native_loop(),
                name=f"logical-heartbeat-{self._task_sequence}-native",
                cancel_order=30,
            )
            self._watchdog_task = self._supervisor.create_task(
                self._watchdog_loop(),
                name=f"logical-heartbeat-{self._task_sequence}-watchdog",
                cancel_order=20,
            )

    async def handle_text(self, text: str) -> EnvelopeHeartbeatOutcome:
        inbound = self._codec.decode_inbound(text)
        shape = Envelope(
            protocol=inbound.protocol,
            message=inbound.message,
            target=inbound.target,
            route=inbound.route,
            delivery=inbound.delivery,
            stream=inbound.stream,
            payload=inbound.payload,
            callback=inbound.callback,
            trace=inbound.trace,
            extensions=inbound.extensions,
        )
        validated = self._registry.validate_envelope(
            shape,
            self._context.protocol_schema_key,
        )
        return await self.process_envelope(validated)

    async def process_envelope(
        self,
        envelope: Envelope,
    ) -> EnvelopeHeartbeatOutcome:
        """Execute one already P03-validated heartbeat Envelope."""

        if not isinstance(envelope, Envelope):
            _invalid("envelope")
        if envelope.message.type != "connection.heartbeat":
            raise _heartbeat_error("heartbeat_message_required")
        payload = _parse_heartbeat_payload(envelope.payload)

        async with self._lifecycle_lock:
            if self._terminal_reason is not None:
                _state_error("heartbeat_terminal")
            entry = await self._index.lookup_connection(self._context.connection_id)
            if entry is None or entry.session_context != self._context:
                raise _heartbeat_error("logical_session_not_current")
            if entry.state not in {
                LogicalConnectionState.ACTIVE,
                LogicalConnectionState.DRAINING,
            }:
                raise _heartbeat_error("heartbeat_state_not_allowed")
            now = self._clock.monotonic()
            if now - self._last_envelope_at >= self._policy.envelope_timeout_seconds:
                await self._terminate_unlocked(
                    LogicalConnectionCloseReason.TIMEOUT_CLOSED,
                )
                raise _heartbeat_error("envelope_heartbeat_timeout")
            self._validate_session_payload(payload)
            sequence = payload["sequence"]
            assert isinstance(sequence, int)
            if self._last_sequence is not None:
                if sequence == self._last_sequence:
                    self._envelope_duplicate_count += 1
                    return EnvelopeHeartbeatOutcome.DUPLICATE
                if sequence < self._last_sequence:
                    raise _heartbeat_error("heartbeat_sequence_out_of_order")
            ack = self._build_ack(sequence)
            text_out = canonical_serialize(ack).decode("utf-8")
            try:
                await self._transport.send(text_out)
            except asyncio.CancelledError:
                await self._terminate_unlocked(LogicalConnectionCloseReason.SHUTDOWN)
                raise
            except Exception:
                await self._terminate_unlocked(LogicalConnectionCloseReason.SEND_FAILED)
                raise
            finally:
                del text_out
            self._last_sequence = sequence
            self._last_envelope_at = now
            self._envelope_accepted_count += 1
            return EnvelopeHeartbeatOutcome.ACCEPTED

    async def shutdown(self) -> None:
        async with self._lifecycle_lock:
            if self._terminal_reason is None:
                await self._terminate_unlocked(LogicalConnectionCloseReason.SHUTDOWN)
        await self._cancel_background_tasks()

    async def detach_for_reconnect(self) -> None:
        """Stop transport-bound heartbeat tasks without closing logical state."""

        async with self._lifecycle_lock:
            self._running = False
        await self._cancel_background_tasks()

    async def replace_session_context(self, session_context: SessionContext) -> None:
        """Adopt a successfully published same-session reauth authority."""

        if not isinstance(session_context, SessionContext):
            _invalid("session_context")
        async with self._lifecycle_lock:
            if (
                session_context.connection_id != self._context.connection_id
                or session_context.session_id != self._context.session_id
                or session_context.connection_epoch != self._context.connection_epoch
            ):
                _state_error("heartbeat_context_identity_changed")
            entry = await self._index.lookup_connection(
                session_context.connection_id,
            )
            if entry is None or entry.session_context != session_context:
                _state_error("heartbeat_context_not_published")
            self._context = session_context

    async def snapshot(self) -> HeartbeatSnapshot:
        async with self._lifecycle_lock:
            return HeartbeatSnapshot(
                running=self._running,
                last_envelope_sequence=self._last_sequence,
                last_envelope_monotonic=self._last_envelope_at,
                native_ping_count=self._native_ping_count,
                envelope_accepted_count=self._envelope_accepted_count,
                envelope_duplicate_count=self._envelope_duplicate_count,
                terminal_reason=self._terminal_reason,
            )

    async def _native_loop(self) -> None:
        try:
            while True:
                await self._clock.sleep(self._policy.native_interval_seconds)
                try:
                    await self._transport.ping()
                except asyncio.CancelledError:
                    raise
                except Exception:
                    async with self._lifecycle_lock:
                        await self._terminate_unlocked(
                            LogicalConnectionCloseReason.TRANSPORT_DISCONNECTED,
                        )
                    return
                async with self._lifecycle_lock:
                    if not self._running:
                        return
                    self._native_ping_count += 1
        except asyncio.CancelledError:
            raise

    async def _watchdog_loop(self) -> None:
        try:
            while True:
                async with self._lifecycle_lock:
                    if not self._running:
                        return
                    remaining = max(
                        0.0,
                        self._policy.envelope_timeout_seconds
                        - (self._clock.monotonic() - self._last_envelope_at),
                    )
                await self._clock.sleep(remaining)
                async with self._lifecycle_lock:
                    if not self._running:
                        return
                    if (
                        self._clock.monotonic() - self._last_envelope_at
                        < self._policy.envelope_timeout_seconds
                    ):
                        continue
                    await self._terminate_unlocked(
                        LogicalConnectionCloseReason.TIMEOUT_CLOSED,
                    )
                    return
        except asyncio.CancelledError:
            raise

    def _validate_session_payload(self, payload: Mapping[str, object]) -> None:
        if payload["connection_id"] != self._context.connection_id:
            raise _heartbeat_error("connection_id_mismatch")
        if payload["session_id"] != self._context.session_id:
            raise _heartbeat_error("session_id_mismatch")
        if payload["connection_epoch"] != self._context.connection_epoch:
            raise _heartbeat_error("connection_epoch_mismatch")

    def _build_ack(self, sequence: int) -> Envelope:
        now = self._clock.utc_now()
        payload_value = {
            "connection_id": self._context.connection_id,
            "session_id": self._context.session_id,
            "connection_epoch": self._context.connection_epoch,
            "sequence": sequence,
            "server_time": _iso_utc(now),
        }
        if frozenset(payload_value) != HEARTBEAT_ACK_PAYLOAD_FIELDS:
            _state_error("heartbeat_ack_field_mismatch")
        envelope = Envelope(
            protocol=ProtocolGroup(
                major=self._context.protocol_version.major,
                minor=self._context.protocol_version.minor,
                patch=self._context.protocol_version.patch,
            ),
            message=MessageGroup(
                message_id=self._identifier_factory.generate(
                    NsIdentifierKind.MESSAGE_ID,
                ),
                type="connection.heartbeat_ack",
                category="connection",
                priority=0,
                created_at=_iso_utc(now),
                reliability="best_effort",
            ),
            payload=PayloadGroup(mode="inline", inline=payload_value),
        )
        return self._registry.validate_envelope(
            envelope,
            self._context.protocol_schema_key,
        )

    async def _terminate_unlocked(
        self,
        reason: LogicalConnectionCloseReason,
    ) -> None:
        if self._terminal_reason is None:
            self._terminal_reason = reason
        self._running = False
        self._cancel_other_tasks_now()
        entry = await self._index.lookup_connection(self._context.connection_id)
        if entry is not None and entry.state is not LogicalConnectionState.CLOSING:
            try:
                await self._index.transition(
                    self._context.connection_id,
                    LogicalConnectionState.CLOSING,
                    close_reason=self._terminal_reason,
                )
            except Exception:
                return
        try:
            await self._transport.close()
        except Exception:
            return
        entry = await self._index.lookup_connection(self._context.connection_id)
        if entry is not None and entry.state is LogicalConnectionState.CLOSING:
            await self._index.transition(
                self._context.connection_id,
                LogicalConnectionState.CLOSED,
            )

    def _cancel_other_tasks_now(self) -> None:
        current = asyncio.current_task()
        for task in (self._native_task, self._watchdog_task):
            if task is not None and task is not current and not task.done():
                task.cancel()

    async def _cancel_background_tasks(self) -> None:
        current = asyncio.current_task()
        tasks = tuple(
            task
            for task in (self._native_task, self._watchdog_task)
            if task is not None and task is not current
        )
        for task in tasks:
            if not task.done():
                task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


def _parse_heartbeat_payload(payload_group) -> Mapping[str, object]:
    if (
        payload_group is None
        or payload_group.mode != "inline"
        or not isinstance(payload_group.inline, Mapping)
        or frozenset(payload_group.inline) != HEARTBEAT_PAYLOAD_FIELDS
    ):
        raise _heartbeat_error("heartbeat_payload_field_mismatch")
    payload = payload_group.inline
    for name in ("connection_id", "session_id", "sent_at"):
        if not isinstance(payload[name], str) or not payload[name]:
            raise _heartbeat_error(f"{name}_invalid")
    for name in ("connection_epoch", "sequence"):
        value = payload[name]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise _heartbeat_error(f"{name}_invalid")
    return payload


def _heartbeat_error(reason: str) -> NsRuntimeProtocolViolationError:
    return NsRuntimeProtocolViolationError(
        details={
            "component": "logical_connection",
            "operation": "envelope_heartbeat",
            "reason": reason,
        },
    )


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Connection heartbeat dependency is invalid.",
        details={"component": "logical_connection", "field": field_name},
    )


def _state_error(reason: str) -> None:
    raise NsStateError(
        "Connection heartbeat operation is invalid.",
        details={
            "component": "logical_connection",
            "operation": "heartbeat_lifecycle",
            "reason": reason,
        },
    )


__all__ = (
    "ConnectionHeartbeatService",
    "EnvelopeHeartbeatOutcome",
    "HEARTBEAT_ACK_PAYLOAD_FIELDS",
    "HEARTBEAT_PAYLOAD_FIELDS",
    "HeartbeatPolicy",
    "HeartbeatSnapshot",
)
