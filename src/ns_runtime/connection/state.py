# -*- coding: utf-8 -*-
"""Atomic state machine for one runtime logical connection."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from ns_common.exceptions import NsStateError, NsValidationError


class LogicalConnectionState(str, Enum):
    ACCEPTED = "accepted"
    HANDSHAKING = "handshaking"
    AUTHENTICATED = "authenticated"
    ACTIVE = "active"
    DRAINING = "draining"
    CLOSING = "closing"
    CLOSED = "closed"


class LogicalConnectionCloseReason(str, Enum):
    """Stable, low-cardinality terminal classifications.

    Values deliberately contain no caller-provided text, transport identity,
    peer information, credential material, or third-party error details.
    """

    NORMAL = "normal"
    REJECTED = "rejected"
    AUTH_FAILED = "auth_failed"
    PROTOCOL_FAILED = "protocol_failed"
    TIMEOUT_CLOSED = "timeout_closed"
    TRANSPORT_DISCONNECTED = "transport_disconnected"
    DRAIN_TIMEOUT = "drain_timeout"
    KICKED = "kicked"
    ISOLATED_CLOSED = "isolated_closed"
    SECURITY_CLOSED = "security_closed"
    SEND_FAILED = "send_failed"
    SHUTDOWN = "shutdown"
    INTERNAL_ERROR = "internal_error"


_TRANSITIONS: Mapping[LogicalConnectionState, tuple[LogicalConnectionState, ...]] = (
    MappingProxyType({
        LogicalConnectionState.ACCEPTED: (
            LogicalConnectionState.HANDSHAKING,
            LogicalConnectionState.CLOSING,
        ),
        LogicalConnectionState.HANDSHAKING: (
            LogicalConnectionState.AUTHENTICATED,
            LogicalConnectionState.CLOSING,
        ),
        LogicalConnectionState.AUTHENTICATED: (
            LogicalConnectionState.ACTIVE,
            LogicalConnectionState.CLOSING,
        ),
        LogicalConnectionState.ACTIVE: (
            LogicalConnectionState.DRAINING,
            LogicalConnectionState.CLOSING,
        ),
        LogicalConnectionState.DRAINING: (
            LogicalConnectionState.CLOSING,
        ),
        LogicalConnectionState.CLOSING: (
            LogicalConnectionState.CLOSED,
        ),
        LogicalConnectionState.CLOSED: (),
    })
)


@dataclass(frozen=True, slots=True, kw_only=True)
class LogicalConnectionStateSnapshot:
    state: LogicalConnectionState
    close_reason: LogicalConnectionCloseReason | None
    transition_sequence: int

    def __post_init__(self) -> None:
        if not isinstance(self.state, LogicalConnectionState):
            raise NsValidationError(
                "Logical connection snapshot state is invalid.",
                details={"component": "logical_connection", "field": "state"},
            )
        if self.close_reason is not None and not isinstance(
            self.close_reason,
            LogicalConnectionCloseReason,
        ):
            raise NsValidationError(
                "Logical connection snapshot close reason is invalid.",
                details={
                    "component": "logical_connection",
                    "field": "close_reason",
                },
            )
        if (
            isinstance(self.transition_sequence, bool)
            or not isinstance(self.transition_sequence, int)
            or self.transition_sequence < 0
        ):
            raise NsValidationError(
                "Logical connection snapshot sequence is invalid.",
                details={
                    "component": "logical_connection",
                    "field": "transition_sequence",
                },
            )


class LogicalConnectionStateMachine:
    """Serialize and validate every logical connection state transition."""

    def __init__(self) -> None:
        self._state = LogicalConnectionState.ACCEPTED
        self._close_reason: LogicalConnectionCloseReason | None = None
        self._transition_sequence = 0
        self._transition_lock = asyncio.Lock()

    @property
    def state(self) -> LogicalConnectionState:
        return self._state

    @property
    def close_reason(self) -> LogicalConnectionCloseReason | None:
        return self._close_reason

    @property
    def transition_sequence(self) -> int:
        return self._transition_sequence

    @property
    def terminal(self) -> bool:
        return self._state is LogicalConnectionState.CLOSED

    async def transition(
        self,
        requested_state: LogicalConnectionState,
        *,
        close_reason: LogicalConnectionCloseReason | None = None,
    ) -> LogicalConnectionStateSnapshot:
        if not isinstance(requested_state, LogicalConnectionState):
            raise NsValidationError(
                "Logical connection requested state is invalid.",
                details={
                    "component": "logical_connection",
                    "field": "requested_state",
                },
            )
        if close_reason is not None and not isinstance(
            close_reason,
            LogicalConnectionCloseReason,
        ):
            raise NsValidationError(
                "Logical connection close reason is invalid.",
                details={
                    "component": "logical_connection",
                    "field": "close_reason",
                },
            )

        async with self._transition_lock:
            self._validate_transition(requested_state, close_reason=close_reason)
            if requested_state is LogicalConnectionState.CLOSING:
                self._close_reason = close_reason
            self._state = requested_state
            self._transition_sequence += 1
            return self._snapshot_unlocked()

    async def snapshot(self) -> LogicalConnectionStateSnapshot:
        async with self._transition_lock:
            return self._snapshot_unlocked()

    def _validate_transition(
        self,
        requested_state: LogicalConnectionState,
        *,
        close_reason: LogicalConnectionCloseReason | None,
    ) -> None:
        allowed = _TRANSITIONS[self._state]
        if requested_state not in allowed:
            raise NsStateError(
                "Logical connection state transition is invalid.",
                details={
                    "component": "logical_connection",
                    "operation": "transition",
                    "current_state": self._state.value,
                    "requested_state": requested_state.value,
                    "allowed_target_states": [item.value for item in allowed],
                },
            )
        if requested_state is LogicalConnectionState.CLOSING:
            if close_reason is None:
                raise NsValidationError(
                    "Logical connection closing requires a close reason.",
                    details={
                        "component": "logical_connection",
                        "field": "close_reason",
                        "reason": "required_for_closing",
                    },
                )
            return
        if close_reason is not None:
            raise NsValidationError(
                "Logical connection close reason is not allowed.",
                details={
                    "component": "logical_connection",
                    "field": "close_reason",
                    "reason": "only_allowed_for_closing",
                },
            )
        if (
            requested_state is LogicalConnectionState.CLOSED
            and self._close_reason is None
        ):
            raise NsStateError(
                "Logical connection cannot close without a reason.",
                details={
                    "component": "logical_connection",
                    "operation": "transition",
                    "current_state": self._state.value,
                    "requested_state": requested_state.value,
                    "reason": "close_reason_missing",
                },
            )

    def _snapshot_unlocked(self) -> LogicalConnectionStateSnapshot:
        return LogicalConnectionStateSnapshot(
            state=self._state,
            close_reason=self._close_reason,
            transition_sequence=self._transition_sequence,
        )


__all__ = (
    "LogicalConnectionCloseReason",
    "LogicalConnectionState",
    "LogicalConnectionStateMachine",
    "LogicalConnectionStateSnapshot",
)
