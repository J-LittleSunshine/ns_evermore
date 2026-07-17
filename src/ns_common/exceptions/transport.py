# -*- coding: utf-8 -*-
from __future__ import annotations

from .base import NsRuntimeError
from .metadata import (
    NsErrorCategory,
    NsErrorDefinition,
    NsErrorSeverity,
)


class NsRuntimeTransportError(NsRuntimeError):
    code = "RUNTIME_TRANSPORT_ERROR"
    numeric_code = 200148
    default_message = "Runtime transport error."


class NsRuntimeTransportDisabledError(NsRuntimeTransportError):
    code = "RUNTIME_TRANSPORT_DISABLED"
    numeric_code = 200149
    default_message = "Runtime transport is disabled."


class NsRuntimeTransportHandshakeFailedError(NsRuntimeTransportError):
    code = "RUNTIME_TRANSPORT_HANDSHAKE_FAILED"
    numeric_code = 200150
    default_message = "Runtime transport handshake failed."


class NsRuntimeTransportSendFailedError(NsRuntimeTransportError):
    code = "RUNTIME_TRANSPORT_SEND_FAILED"
    numeric_code = 200151
    default_message = "Runtime transport send failed."


class NsRuntimeTransportReceiveFailedError(NsRuntimeTransportError):
    code = "RUNTIME_TRANSPORT_RECEIVE_FAILED"
    numeric_code = 200152
    default_message = "Runtime transport receive failed."


class NsRuntimeTransportStreamResetError(NsRuntimeTransportError):
    code = "RUNTIME_TRANSPORT_STREAM_RESET"
    numeric_code = 200153
    default_message = "Runtime transport stream was reset."


class NsRuntimeTransportFlowControlBlockedError(NsRuntimeTransportError):
    code = "RUNTIME_TRANSPORT_FLOW_CONTROL_BLOCKED"
    numeric_code = 200154
    default_message = "Runtime transport flow control is blocked."


class NsRuntimeTransportPathMigrationFailedError(NsRuntimeTransportError):
    code = "RUNTIME_TRANSPORT_PATH_MIGRATION_FAILED"
    numeric_code = 200155
    default_message = "Runtime transport path migration failed."


class NsRuntimeTransportFallbackFailedError(NsRuntimeTransportError):
    code = "RUNTIME_TRANSPORT_FALLBACK_FAILED"
    numeric_code = 200156
    default_message = "Runtime transport fallback failed."


class NsRuntimeTransportCapabilityUnavailableError(NsRuntimeTransportError):
    code = "RUNTIME_TRANSPORT_CAPABILITY_UNAVAILABLE"
    numeric_code = 200161
    default_message = "Runtime transport capability is unavailable."


TRANSPORT_ERROR_DEFINITIONS: tuple[NsErrorDefinition, ...] = (
    NsErrorDefinition.for_error_type(
        NsRuntimeTransportError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.TRANSPORT,
        action="handle_transport_failure",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeTransportDisabledError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.TRANSPORT,
        audit_required=True,
        action="reject_disabled_transport",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeTransportHandshakeFailedError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.TRANSPORT,
        disconnect_required=True,
        audit_required=True,
        action="close_failed_handshake",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeTransportSendFailedError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.TRANSPORT,
        retryable=True,
        action="retry_transport_send",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeTransportReceiveFailedError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.TRANSPORT,
        disconnect_required=True,
        action="close_failed_transport_receive",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeTransportStreamResetError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.TRANSPORT,
        retryable=True,
        action="retry_after_stream_reset",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeTransportFlowControlBlockedError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.TRANSPORT,
        retryable=True,
        action="wait_for_transport_capacity",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeTransportPathMigrationFailedError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.TRANSPORT,
        retryable=True,
        action="reconnect_after_path_failure",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeTransportFallbackFailedError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.TRANSPORT,
        action="report_transport_fallback_failure",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeTransportCapabilityUnavailableError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.TRANSPORT,
        action="reject_transport_capability",
    ),
)
