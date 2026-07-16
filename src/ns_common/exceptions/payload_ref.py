# -*- coding: utf-8 -*-
from __future__ import annotations

from .base import NsRuntimeError
from .metadata import (
    NsErrorCategory,
    NsErrorDefinition,
    NsErrorSeverity,
)
from .protocol import NsRuntimeProtocolError


class NsRuntimePayloadRefDeniedError(NsRuntimeProtocolError):
    code = "RUNTIME_PAYLOAD_REF_DENIED"
    numeric_code = 200108
    default_message = "Runtime payload reference is denied."


class NsRuntimePayloadRefInvalidError(NsRuntimeProtocolError):
    code = "RUNTIME_PAYLOAD_REF_INVALID"
    numeric_code = 200116
    default_message = "Runtime payload reference is invalid."


class NsRuntimePayloadRefExpiredError(NsRuntimeProtocolError):
    code = "RUNTIME_PAYLOAD_REF_EXPIRED"
    numeric_code = 200117
    default_message = "Runtime payload reference has expired."


class NsRuntimePayloadRefChecksumMismatchError(NsRuntimeProtocolError):
    code = "RUNTIME_PAYLOAD_REF_CHECKSUM_MISMATCH"
    numeric_code = 200118
    default_message = "Runtime payload reference checksum does not match."


class NsRuntimePayloadRefVersionMismatchError(NsRuntimeProtocolError):
    code = "RUNTIME_PAYLOAD_REF_VERSION_MISMATCH"
    numeric_code = 200119
    default_message = "Runtime payload reference version does not match."


class NsRuntimePayloadRefValidationUnavailableError(NsRuntimeError):
    code = "RUNTIME_PAYLOAD_REF_VALIDATION_UNAVAILABLE"
    numeric_code = 200120
    default_message = "Runtime payload reference validation is unavailable."


class NsRuntimePayloadRefValidationTimeoutError(
    NsRuntimePayloadRefValidationUnavailableError
):
    code = "RUNTIME_PAYLOAD_REF_VALIDATION_TIMEOUT"
    numeric_code = 200121
    default_message = "Runtime payload reference validation timed out."


PAYLOAD_REF_ERROR_DEFINITIONS: tuple[NsErrorDefinition, ...] = (
    NsErrorDefinition.for_error_type(
        NsRuntimePayloadRefDeniedError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.PAYLOAD_REF,
        audit_required=True,
        action="reject_payload_ref",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimePayloadRefInvalidError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.PAYLOAD_REF,
        action="reject_invalid_payload_ref",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimePayloadRefExpiredError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.PAYLOAD_REF,
        action="refresh_payload_ref",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimePayloadRefChecksumMismatchError,
        severity=NsErrorSeverity.CRITICAL,
        category=NsErrorCategory.PAYLOAD_REF,
        audit_required=True,
        action="reject_payload_checksum",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimePayloadRefVersionMismatchError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.PAYLOAD_REF,
        action="reject_payload_version",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimePayloadRefValidationUnavailableError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.PAYLOAD_REF,
        retryable=True,
        action="retry_payload_validation",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimePayloadRefValidationTimeoutError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.PAYLOAD_REF,
        retryable=True,
        action="retry_payload_validation",
    ),
)
