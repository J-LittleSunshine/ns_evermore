# -*- coding: utf-8 -*-
"""Safe normalization boundary for adapter and third-party failures."""

from __future__ import annotations

import asyncio
import ssl
from dataclasses import dataclass

from ns_common.exceptions import (
    NsRuntimeTransportError,
    NsRuntimeTransportFlowControlBlockedError,
    NsRuntimeTransportHandshakeFailedError,
    NsRuntimeTransportReceiveFailedError,
    NsRuntimeTransportSendFailedError,
    NsRuntimeTransportStreamResetError,
    NsValidationError,
)

from .models import TransportError, TransportErrorKind


@dataclass(frozen=True, slots=True)
class NormalizedTransportFailure:
    error: TransportError
    exception: NsRuntimeTransportError

    def __post_init__(self) -> None:
        if not isinstance(self.error, TransportError) or not isinstance(
            self.exception,
            NsRuntimeTransportError,
        ):
            raise NsValidationError(
                "Normalized transport failure is invalid.",
                details={"component": "transport", "field": "failure"},
            )


def normalize_transport_exception(
    error: BaseException,
    *,
    operation: str,
    close_code: int | None = None,
) -> NormalizedTransportFailure:
    """Map a library exception without copying its message, repr, or object."""

    if not isinstance(error, Exception):
        raise error
    if operation not in {"accept", "close", "keepalive", "listen", "receive", "send", "tls"}:
        raise NsValidationError(
            "Transport normalization operation is invalid.",
            details={"component": "transport", "field": "operation"},
        )

    classes = _websocket_exception_classes()
    resolved_close_code = close_code
    if isinstance(error, classes.connection_closed):
        library_close_code = _safe_close_code(error)
        if library_close_code is not None:
            resolved_close_code = library_close_code

    if isinstance(error, ssl.SSLError):
        kind = TransportErrorKind.TLS_FAILED
        reason = "tls_failed"
    elif isinstance(error, classes.payload_too_big) or resolved_close_code == 1009:
        kind = TransportErrorKind.MESSAGE_TOO_LARGE
        reason = "message_too_large"
    elif resolved_close_code in {1002, 1003, 1007, 1008}:
        kind = TransportErrorKind.PROTOCOL_ERROR
        reason = "protocol_error"
    elif isinstance(error, classes.connection_closed_ok):
        kind = TransportErrorKind.REMOTE_CLOSED
        reason = "remote_closed"
    elif isinstance(error, classes.connection_closed):
        kind = TransportErrorKind.REMOTE_CLOSED
        reason = "remote_closed_abnormally"
    elif isinstance(error, classes.invalid_handshake):
        kind = TransportErrorKind.HANDSHAKE_FAILED
        reason = "handshake_failed"
    elif isinstance(error, asyncio.TimeoutError):
        if operation == "send":
            kind = TransportErrorKind.SEND_TIMEOUT
            reason = "send_timeout"
        elif operation == "keepalive":
            kind = TransportErrorKind.KEEPALIVE_FAILED
            reason = "keepalive_timeout"
        else:
            kind = TransportErrorKind.RECEIVE_FAILED
            reason = "operation_timeout"
    elif operation == "listen":
        kind = TransportErrorKind.LISTENER_FAILED
        reason = "listener_failed"
    elif operation == "tls":
        kind = TransportErrorKind.TLS_FAILED
        reason = "tls_failed"
    elif operation == "send":
        kind = TransportErrorKind.SEND_FAILED
        reason = "write_failed"
    elif operation == "keepalive":
        kind = TransportErrorKind.KEEPALIVE_FAILED
        reason = "keepalive_failed"
    elif operation == "receive":
        kind = TransportErrorKind.RECEIVE_FAILED
        reason = "read_failed"
    else:
        kind = TransportErrorKind.HANDSHAKE_FAILED
        reason = "accept_failed"

    code, exception_type, retryable, close_required = _public_mapping(kind)
    details = {
        "reason": reason,
        "transport_type": "websocket_tcp",
    }
    transport_error = TransportError(
        kind=kind,
        code=code,
        operation=operation,
        retryable=retryable,
        close_required=close_required,
        details=details,
    )
    public_exception = exception_type(
        _safe_message(kind),
        details={
            "component": "transport",
            "operation": operation,
            **details,
        },
    )
    return NormalizedTransportFailure(
        error=transport_error,
        exception=public_exception,
    )


@dataclass(frozen=True, slots=True)
class _WebSocketExceptionClasses:
    connection_closed: type[Exception]
    connection_closed_ok: type[Exception]
    invalid_handshake: type[Exception]
    payload_too_big: type[Exception]


def _websocket_exception_classes() -> _WebSocketExceptionClasses:
    # P04-W08 verifies this lazy import never occurs for disabled adapters or
    # transport facade inspection.
    from websockets.exceptions import (
        ConnectionClosed,
        ConnectionClosedOK,
        InvalidHandshake,
        PayloadTooBig,
    )

    return _WebSocketExceptionClasses(
        connection_closed=ConnectionClosed,
        connection_closed_ok=ConnectionClosedOK,
        invalid_handshake=InvalidHandshake,
        payload_too_big=PayloadTooBig,
    )


def _safe_close_code(error: Exception) -> int | None:
    try:
        received = getattr(error, "rcvd", None)
        code = getattr(received, "code", None)
        if code is None:
            sent = getattr(error, "sent", None)
            code = getattr(sent, "code", None)
    except Exception:
        return None
    if isinstance(code, bool) or not isinstance(code, int):
        return None
    return code


def _public_mapping(
    kind: TransportErrorKind,
) -> tuple[str, type[NsRuntimeTransportError], bool, bool]:
    if kind in {TransportErrorKind.HANDSHAKE_FAILED, TransportErrorKind.LISTENER_FAILED, TransportErrorKind.TLS_FAILED}:
        return (
            "RUNTIME_TRANSPORT_HANDSHAKE_FAILED",
            NsRuntimeTransportHandshakeFailedError,
            False,
            True,
        )
    if kind is TransportErrorKind.WRITE_QUEUE_FULL:
        return (
            "RUNTIME_TRANSPORT_FLOW_CONTROL_BLOCKED",
            NsRuntimeTransportFlowControlBlockedError,
            True,
            False,
        )
    if kind in {TransportErrorKind.SEND_TIMEOUT, TransportErrorKind.SEND_FAILED}:
        return (
            "RUNTIME_TRANSPORT_SEND_FAILED",
            NsRuntimeTransportSendFailedError,
            True,
            False,
        )
    if kind is TransportErrorKind.KEEPALIVE_FAILED:
        return (
            "RUNTIME_TRANSPORT_STREAM_RESET",
            NsRuntimeTransportStreamResetError,
            True,
            True,
        )
    return (
        "RUNTIME_TRANSPORT_RECEIVE_FAILED",
        NsRuntimeTransportReceiveFailedError,
        False,
        True,
    )


def _safe_message(kind: TransportErrorKind) -> str:
    if kind in {TransportErrorKind.HANDSHAKE_FAILED, TransportErrorKind.LISTENER_FAILED}:
        return "Runtime transport handshake failed."
    if kind is TransportErrorKind.TLS_FAILED:
        return "Runtime transport TLS failed."
    if kind in {TransportErrorKind.SEND_FAILED, TransportErrorKind.SEND_TIMEOUT}:
        return "Runtime transport send failed."
    if kind is TransportErrorKind.KEEPALIVE_FAILED:
        return "Runtime transport keepalive failed."
    return "Runtime transport receive failed."


__all__ = (
    "NormalizedTransportFailure",
    "normalize_transport_exception",
)
