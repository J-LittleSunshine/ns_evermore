# -*- coding: utf-8 -*-
from __future__ import annotations

from .base import NsRuntimeError
from .metadata import (
    NsErrorCategory,
    NsErrorDefinition,
    NsErrorSeverity,
)


class NsRuntimeProtocolError(NsRuntimeError):
    code = "RUNTIME_PROTOCOL_ERROR"
    numeric_code = 200100
    default_message = "Runtime protocol error."


class NsRuntimeEnvelopeSchemaError(NsRuntimeProtocolError):
    code = "RUNTIME_ENVELOPE_SCHEMA_ERROR"
    numeric_code = 200101
    default_message = "Runtime envelope schema error."


class NsRuntimeProtocolVersionError(NsRuntimeProtocolError):
    code = "RUNTIME_PROTOCOL_VERSION_ERROR"
    numeric_code = 200102
    default_message = "Runtime protocol version is incompatible."


class NsRuntimeSourceForgedError(NsRuntimeProtocolError):
    code = "RUNTIME_SOURCE_FORGED"
    numeric_code = 200103
    default_message = "Inbound envelope must not contain source."


class NsRuntimeAuthContextForgedError(NsRuntimeProtocolError):
    code = "RUNTIME_AUTH_CONTEXT_FORGED"
    numeric_code = 200104
    default_message = "Inbound envelope must not contain auth_context."


class NsRuntimeUnsupportedMessageTypeError(NsRuntimeProtocolError):
    code = "RUNTIME_UNSUPPORTED_MESSAGE_TYPE"
    numeric_code = 200105
    default_message = "Runtime message type is not registered."


class NsRuntimeUnauthorizedMessageTypeError(NsRuntimeProtocolError):
    code = "RUNTIME_UNAUTHORIZED_MESSAGE_TYPE"
    numeric_code = 200106
    default_message = (
        "Runtime message type is not allowed by current capability."
    )


class NsRuntimeTenantMismatchError(NsRuntimeProtocolError):
    code = "RUNTIME_TENANT_MISMATCH"
    numeric_code = 200107
    default_message = "Runtime tenant boundary is violated."


PROTOCOL_ERROR_DEFINITIONS: tuple[NsErrorDefinition, ...] = (
    NsErrorDefinition.for_error_type(
        NsRuntimeProtocolError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.PROTOCOL,
        disconnect_required=True,
        action="reject_protocol_message",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeEnvelopeSchemaError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.PROTOCOL,
        disconnect_required=True,
        action="reject_invalid_envelope",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeProtocolVersionError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.PROTOCOL,
        disconnect_required=True,
        action="reject_protocol_version",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeSourceForgedError,
        severity=NsErrorSeverity.CRITICAL,
        category=NsErrorCategory.SECURITY,
        disconnect_required=True,
        audit_required=True,
        action="reject_forged_source",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeAuthContextForgedError,
        severity=NsErrorSeverity.CRITICAL,
        category=NsErrorCategory.SECURITY,
        disconnect_required=True,
        audit_required=True,
        action="reject_forged_auth_context",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeUnsupportedMessageTypeError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.PROTOCOL,
        action="reject_unsupported_message",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeUnauthorizedMessageTypeError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.SECURITY,
        audit_required=True,
        action="reject_unauthorized_message",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeTenantMismatchError,
        severity=NsErrorSeverity.CRITICAL,
        category=NsErrorCategory.SECURITY,
        disconnect_required=True,
        audit_required=True,
        action="reject_tenant_mismatch",
    ),
)
