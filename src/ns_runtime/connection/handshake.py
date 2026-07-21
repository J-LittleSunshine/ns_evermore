# -*- coding: utf-8 -*-
"""Hello-first application handshake boundary with an explicit deadline."""

from __future__ import annotations

import asyncio
import math

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import (
    NsRuntimeProtocolViolationError,
    NsStateError,
    NsValidationError,
)
from ns_common.time import Clock
from ns_runtime.protocol import (
    BUILTIN_MESSAGE_REGISTRY,
    CURRENT_PROTOCOL_SCHEMA_KEY,
    Envelope,
    InboundEnvelope,
    JsonV1Codec,
    MessageTypeRegistry,
)
from ns_runtime.transport import TransportMessage, TransportSession

from .state import (
    LogicalConnectionCloseReason,
    LogicalConnectionState,
    LogicalConnectionStateMachine,
)


class ConnectionHelloReceiver:
    """Read and validate exactly one first ``connection.hello`` Envelope."""

    def __init__(
        self,
        *,
        transport_session: TransportSession,
        state_machine: LogicalConnectionStateMachine,
        clock: Clock,
        task_supervisor: TaskSupervisor,
        task_sequence: int,
        timeout_seconds: float,
        codec: JsonV1Codec,
        registry: MessageTypeRegistry = BUILTIN_MESSAGE_REGISTRY,
        schema_key: str = CURRENT_PROTOCOL_SCHEMA_KEY,
    ) -> None:
        if not isinstance(transport_session, TransportSession):
            _invalid("transport_session")
        if not isinstance(state_machine, LogicalConnectionStateMachine):
            _invalid("state_machine")
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
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or not 0 < float(timeout_seconds) < float("inf")
        ):
            _invalid("timeout_seconds")
        if not isinstance(codec, JsonV1Codec):
            _invalid("codec")
        if not isinstance(registry, MessageTypeRegistry):
            _invalid("registry")
        if not isinstance(schema_key, str) or not schema_key:
            _invalid("schema_key")
        self._transport_session = transport_session
        self._state_machine = state_machine
        self._clock = clock
        self._task_supervisor = task_supervisor
        self._task_sequence = task_sequence
        self._timeout_seconds = float(timeout_seconds)
        self._codec = codec
        self._registry = registry
        self._schema_key = schema_key
        self._claim_lock = asyncio.Lock()
        self._claimed = False

    @property
    def state_machine(self) -> LogicalConnectionStateMachine:
        return self._state_machine

    async def terminate(self, reason: LogicalConnectionCloseReason) -> None:
        if not isinstance(reason, LogicalConnectionCloseReason):
            _invalid("close_reason")
        await self._terminate(reason)

    async def receive(self) -> InboundEnvelope:
        if not await self._claim_once():
            await self._terminate_isolated(
                LogicalConnectionCloseReason.PROTOCOL_FAILED,
            )
            raise _handshake_error("duplicate_hello")

        await self._state_machine.transition(LogicalConnectionState.HANDSHAKING)
        receive_task: asyncio.Task[object] | None = None
        deadline_task: asyncio.Task[object] | None = None
        try:
            started_at = self._clock.monotonic()
            deadline = started_at + self._timeout_seconds
            if not math.isfinite(started_at) or not math.isfinite(deadline):
                raise NsStateError(
                    "Logical connection handshake deadline is invalid.",
                    details={
                        "component": "logical_connection",
                        "operation": "handshake",
                        "reason": "invalid_clock_deadline",
                    },
                )
            receive_task = self._task_supervisor.create_task(
                self._transport_session.receive(),
                name=f"logical-handshake-{self._task_sequence}-receive",
                cancel_order=20,
            )
            deadline_task = self._task_supervisor.create_task(
                self._clock.sleep(self._timeout_seconds),
                name=f"logical-handshake-{self._task_sequence}-deadline",
                cancel_order=10,
            )
            await asyncio.wait(
                (receive_task, deadline_task),
                return_when=asyncio.FIRST_COMPLETED,
            )

            if deadline_task.done() or self._clock.monotonic() >= deadline:
                if deadline_task.done():
                    deadline_task.result()
                await _cancel_and_join(receive_task)
                await self._terminate_isolated(
                    LogicalConnectionCloseReason.TIMEOUT_CLOSED,
                )
                raise _handshake_error("hello_timeout")

            await _cancel_and_join(deadline_task)
            try:
                message = receive_task.result()
            except Exception:
                await self._terminate_isolated(
                    LogicalConnectionCloseReason.TRANSPORT_DISCONNECTED,
                )
                raise

            try:
                if not isinstance(message, TransportMessage):
                    _invalid("transport_message")
                inbound = self._codec.decode_inbound(message.text)
                if inbound.message.type != "connection.hello":
                    raise _handshake_error("hello_required_first")
                normalized_shape = Envelope(
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
                self._registry.validate_envelope(
                    normalized_shape,
                    self._schema_key,
                )
            except Exception:
                await self._terminate_isolated(
                    LogicalConnectionCloseReason.PROTOCOL_FAILED,
                )
                raise
            return inbound
        except asyncio.CancelledError:
            await _cancel_and_join(receive_task)
            await _cancel_and_join(deadline_task)
            try:
                await self._terminate(LogicalConnectionCloseReason.SHUTDOWN)
            except Exception:
                pass
            raise
        except Exception:
            await _cancel_and_join(receive_task)
            await _cancel_and_join(deadline_task)
            await self._terminate_isolated(
                LogicalConnectionCloseReason.INTERNAL_ERROR,
            )
            raise

    async def _claim_once(self) -> bool:
        async with self._claim_lock:
            if self._claimed:
                return False
            self._claimed = True
            return True

    async def _terminate(self, reason: LogicalConnectionCloseReason) -> None:
        snapshot = await self._state_machine.snapshot()
        if snapshot.state is LogicalConnectionState.CLOSED:
            return
        if snapshot.state not in {
            LogicalConnectionState.CLOSING,
        }:
            try:
                await self._state_machine.transition(
                    LogicalConnectionState.CLOSING,
                    close_reason=reason,
                )
            except NsStateError:
                snapshot = await self._state_machine.snapshot()
                if snapshot.state not in {
                    LogicalConnectionState.CLOSING,
                }:
                    raise
        await self._transport_session.close()
        snapshot = await self._state_machine.snapshot()
        if snapshot.state is LogicalConnectionState.CLOSING:
            await self._state_machine.transition(LogicalConnectionState.CLOSED)

    async def _terminate_isolated(
        self,
        reason: LogicalConnectionCloseReason,
    ) -> None:
        try:
            await self._terminate(reason)
        except Exception:
            # The original protocol/transport outcome stays authoritative.
            # A retryable transport close owner may finish the CLOSING state.
            pass


async def _cancel_and_join(task: asyncio.Task[object] | None) -> None:
    if task is None:
        return
    if not task.done():
        task.cancel()
    await asyncio.gather(task, return_exceptions=True)


def _handshake_error(reason: str) -> NsRuntimeProtocolViolationError:
    return NsRuntimeProtocolViolationError(
        details={
            "component": "logical_connection",
            "operation": "handshake",
            "reason": reason,
        },
    )


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Logical connection handshake dependency is invalid.",
        details={"component": "logical_connection", "field": field_name},
    )


__all__ = ("ConnectionHelloReceiver",)
