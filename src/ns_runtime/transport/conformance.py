# -*- coding: utf-8 -*-
"""TC-1 case identifiers shared by every present and future adapter suite."""

from __future__ import annotations

from enum import Enum


class TransportConformanceCase(str, Enum):
    CAPABILITY_DECLARATION = "capability_declaration"
    START_AND_CLOSE = "start_and_close"
    TLS_LOOPBACK = "tls_loopback"
    PLAINTEXT_POLICY = "plaintext_policy"
    TEXT_MESSAGE_BOUNDARY = "text_message_boundary"
    BINARY_REJECTION = "binary_rejection"
    INVALID_UTF8_REJECTION = "invalid_utf8_rejection"
    MAXIMUM_MESSAGE = "maximum_message"
    READ_QUEUE_LIMIT = "read_queue_limit"
    WRITE_QUEUE_LIMIT = "write_queue_limit"
    BACKPRESSURE = "backpressure"
    NATIVE_KEEPALIVE = "native_keepalive"
    ABNORMAL_CLOSE = "abnormal_close"
    REMOTE_CLOSE = "remote_close"
    CONCURRENT_SEND = "concurrent_send"
    CANCEL_SEND = "cancel_send"
    IDEMPOTENT_CLOSE = "idempotent_close"
    SHUTDOWN_ORDER = "shutdown_order"
    DISABLED_DEPENDENCY_ISOLATION = "disabled_dependency_isolation"
    SEND_SUCCESS_IS_NOT_RUNTIME_ACK = "send_success_is_not_runtime_ack"
    ERROR_NORMALIZATION = "error_normalization"
    SAFE_DIAGNOSTICS = "safe_diagnostics"


TRANSPORT_CONFORMANCE_CASES = tuple(TransportConformanceCase)


__all__ = (
    "TRANSPORT_CONFORMANCE_CASES",
    "TransportConformanceCase",
)

