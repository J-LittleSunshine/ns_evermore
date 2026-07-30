# -*- coding: utf-8 -*-
"""Transport-independent immutable values shared with upper runtime layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from ns_common.exceptions import NsValidationError


class TransportCapability(str, Enum):
    RELIABLE_ORDERED_MESSAGES = "reliable_ordered_messages"
    RELIABLE_BIDIRECTIONAL_STREAMS = "reliable_bidirectional_streams"
    RELIABLE_UNIDIRECTIONAL_STREAMS = "reliable_unidirectional_streams"
    UNRELIABLE_DATAGRAMS = "unreliable_datagrams"
    STREAM_MULTIPLEXING = "stream_multiplexing"
    CONNECTION_PATH_MIGRATION = "connection_path_migration"
    TRANSPORT_FLOW_CONTROL = "transport_flow_control"
    PER_STREAM_FLOW_CONTROL = "per_stream_flow_control"
    NATIVE_KEEPALIVE = "native_keepalive"
    ZERO_RTT = "zero_rtt"
    TRANSPORT_RESUME = "transport_resume"


@dataclass(frozen=True, slots=True)
class TransportCapabilities:
    """The authoritative capability set declared by one adapter."""

    supported: frozenset[TransportCapability] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        try:
            normalized = frozenset(self.supported)
        except (TypeError, ValueError):
            raise NsValidationError(
                "Transport capabilities are invalid.",
                details={
                    "component": "transport",
                    "field": "capabilities",
                    "reason": "invalid_collection",
                },
            ) from None
        if any(not isinstance(item, TransportCapability) for item in normalized):
            raise NsValidationError(
                "Transport capabilities are invalid.",
                details={
                    "component": "transport",
                    "field": "capabilities",
                    "reason": "invalid_capability",
                },
            )
        object.__setattr__(self, "supported", normalized)

    def supports(self, capability: TransportCapability) -> bool:
        if not isinstance(capability, TransportCapability):
            raise NsValidationError(
                "Transport capability query is invalid.",
                details={
                    "component": "transport",
                    "field": "capability",
                    "reason": "invalid_capability",
                },
            )
        return capability in self.supported


class TransportSessionState(str, Enum):
    HANDSHAKING = "handshaking"
    CLOSING = "closing"
    CLOSED = "closed"


class TransportWriteState(str, Enum):
    NOT_STARTED = "not_started"
    UNCERTAIN = "uncertain"
    SUCCEEDED = "succeeded"


@dataclass(frozen=True, slots=True)
class TransportWriteResult:
    state: TransportWriteState
    failure_reason: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.state, TransportWriteState):
            raise NsValidationError(
                "Transport write result is invalid.",
                details={"component": "transport", "field": "write_result.state"},
            )
        if self.failure_reason is not None and (
            type(self.failure_reason) is not str
            or not self.failure_reason
            or len(self.failure_reason) > 128
        ):
            raise NsValidationError(
                "Transport write result is invalid.",
                details={"component": "transport", "field": "write_result.failure_reason"},
            )
        if (
            self.state is TransportWriteState.SUCCEEDED
            and self.failure_reason is not None
        ):
            raise NsValidationError(
                "Transport write result is invalid.",
                details={"component": "transport", "field": "write_result.success"},
            )


class TransportCloseInitiator(str, Enum):
    LOCAL = "local"
    REMOTE = "remote"
    ADAPTER = "adapter"


class TransportCloseReason(str, Enum):
    NORMAL = "normal"
    REMOTE_CLOSED = "remote_closed"
    PROTOCOL_ERROR = "protocol_error"
    MESSAGE_TOO_LARGE = "message_too_large"
    READ_QUEUE_FULL = "read_queue_full"
    WRITE_QUEUE_FULL = "write_queue_full"
    SEND_TIMEOUT = "send_timeout"
    SEND_FAILED = "send_failed"
    RECEIVE_FAILED = "receive_failed"
    KEEPALIVE_FAILED = "keepalive_failed"
    ADAPTER_SHUTDOWN = "adapter_shutdown"
    LISTENER_FAILED = "listener_failed"
    TLS_FAILED = "tls_failed"


@dataclass(frozen=True, slots=True)
class TransportClose:
    reason: TransportCloseReason
    initiator: TransportCloseInitiator
    clean: bool
    protocol_code: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.reason, TransportCloseReason):
            raise NsValidationError(
                "Transport close reason is invalid.",
                details={"component": "transport", "field": "close.reason"},
            )
        if not isinstance(self.initiator, TransportCloseInitiator):
            raise NsValidationError(
                "Transport close initiator is invalid.",
                details={"component": "transport", "field": "close.initiator"},
            )
        if not isinstance(self.clean, bool):
            raise NsValidationError(
                "Transport close clean flag is invalid.",
                details={"component": "transport", "field": "close.clean"},
            )
        if self.protocol_code is not None and (
            isinstance(self.protocol_code, bool)
            or not isinstance(self.protocol_code, int)
            or not 0 <= self.protocol_code <= 65535
        ):
            raise NsValidationError(
                "Transport close protocol code is invalid.",
                details={"component": "transport", "field": "close.protocol_code"},
            )


@dataclass(frozen=True, slots=True)
class TransportMessage:
    """One complete UTF-8 text application message.

    The text itself is deliberately excluded from repr so diagnostics cannot
    accidentally expose an Envelope or payload.
    """

    text: str = field(repr=False)
    byte_size: int
    received_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise NsValidationError(
                "Transport message must be text.",
                details={"component": "transport", "field": "message.text"},
            )
        encoded_size = len(self.text.encode("utf-8"))
        if (
            isinstance(self.byte_size, bool)
            or not isinstance(self.byte_size, int)
            or self.byte_size != encoded_size
        ):
            raise NsValidationError(
                "Transport message byte size is invalid.",
                details={"component": "transport", "field": "message.byte_size"},
            )
        if not isinstance(self.received_at, datetime):
            raise NsValidationError(
                "Transport message timestamp is invalid.",
                details={"component": "transport", "field": "message.received_at"},
            )
        try:
            offset = self.received_at.utcoffset()
            normalized = self.received_at.astimezone(timezone.utc)
        except Exception:
            offset = None
        if offset is None:
            raise NsValidationError(
                "Transport message timestamp must be timezone-aware.",
                details={"component": "transport", "field": "message.received_at"},
            )
        object.__setattr__(self, "received_at", normalized)


class TransportErrorKind(str, Enum):
    DISABLED = "disabled"
    HANDSHAKE_FAILED = "handshake_failed"
    LISTENER_FAILED = "listener_failed"
    TLS_FAILED = "tls_failed"
    PROTOCOL_ERROR = "protocol_error"
    MESSAGE_TOO_LARGE = "message_too_large"
    READ_QUEUE_FULL = "read_queue_full"
    WRITE_QUEUE_FULL = "write_queue_full"
    SEND_TIMEOUT = "send_timeout"
    SEND_FAILED = "send_failed"
    RECEIVE_FAILED = "receive_failed"
    REMOTE_CLOSED = "remote_closed"
    CLOSED = "closed"
    KEEPALIVE_FAILED = "keepalive_failed"


@dataclass(frozen=True, slots=True)
class TransportError:
    """Safe, normalized transport failure information.

    ``details`` is restricted to fixed scalar classifications. Adapter/library
    exceptions are never retained, chained, or represented here.
    """

    kind: TransportErrorKind
    code: str
    operation: str
    retryable: bool = False
    close_required: bool = False
    details: Mapping[str, str | int | bool] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.kind, TransportErrorKind):
            raise NsValidationError(
                "Transport error kind is invalid.",
                details={"component": "transport", "field": "error.kind"},
            )
        if not isinstance(self.code, str) or not self.code.startswith("RUNTIME_TRANSPORT_"):
            raise NsValidationError(
                "Transport error code is invalid.",
                details={"component": "transport", "field": "error.code"},
            )
        if self.operation not in {
            "accept", "close", "keepalive", "listen", "receive", "send", "tls"
        }:
            raise NsValidationError(
                "Transport error operation is invalid.",
                details={"component": "transport", "field": "error.operation"},
            )
        if not isinstance(self.retryable, bool) or not isinstance(self.close_required, bool):
            raise NsValidationError(
                "Transport error flags are invalid.",
                details={"component": "transport", "field": "error.flags"},
            )
        if not isinstance(self.details, Mapping):
            raise NsValidationError(
                "Transport error details are invalid.",
                details={"component": "transport", "field": "error.details"},
            )
        safe_details: dict[str, str | int | bool] = {}
        for key, value in self.details.items():
            if (
                not isinstance(key, str)
                or key not in {"limit", "reason", "state", "transport_type"}
                or not isinstance(value, (str, int, bool))
            ):
                raise NsValidationError(
                    "Transport error details are not allowlisted.",
                    details={"component": "transport", "field": "error.details"},
                )
            safe_details[key] = value
        object.__setattr__(self, "details", MappingProxyType(safe_details))
