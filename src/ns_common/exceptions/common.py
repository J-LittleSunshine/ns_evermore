# -*- coding: utf-8 -*-
from __future__ import annotations

from .base import NsEvermoreError, NsRuntimeError
from .metadata import (
    NsErrorCategory,
    NsErrorDefinition,
    NsErrorSeverity,
)


class NsConfigError(NsEvermoreError):
    code = "NS_CONFIG_ERROR"
    numeric_code = 100100
    default_message = "Invalid ns_evermore configuration."


class NsValidationError(NsEvermoreError):
    code = "NS_VALIDATION_ERROR"
    numeric_code = 100200
    default_message = "Validation failed."


class NsDependencyError(NsEvermoreError):
    code = "NS_DEPENDENCY_ERROR"
    numeric_code = 100400
    default_message = "NsEvermore dependency error."


class NsStateError(NsEvermoreError):
    code = "NS_STATE_ERROR"
    numeric_code = 100500
    default_message = "Invalid ns_evermore internal state."


class NsHttpClientError(NsEvermoreError):
    code = "NS_HTTP_CLIENT_ERROR"
    numeric_code = 100600
    default_message = "NsEvermore HTTP client error."


class NsRuntimeDependencyUnavailableError(NsRuntimeError):
    code = "RUNTIME_DEPENDENCY_UNAVAILABLE"
    numeric_code = 200163
    default_message = "Runtime dependency is unavailable."


COMMON_ERROR_DEFINITIONS: tuple[NsErrorDefinition, ...] = (
    NsErrorDefinition.for_error_type(
        NsEvermoreError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.COMMON,
        action="report_error",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.RUNTIME,
        action="report_runtime_error",
    ),
    NsErrorDefinition.for_error_type(
        NsConfigError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.CONFIGURATION,
        action="fix_configuration",
    ),
    NsErrorDefinition.for_error_type(
        NsValidationError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.VALIDATION,
        action="reject_invalid_input",
    ),
    NsErrorDefinition.for_error_type(
        NsDependencyError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.DEPENDENCY,
        retryable=False,
        disconnect_required=False,
        audit_required=False,
        safe_detail=False,
        action="inspect_dependency",
    ),
    NsErrorDefinition.for_error_type(
        NsStateError,
        severity=NsErrorSeverity.CRITICAL,
        category=NsErrorCategory.STATE,
        action="investigate_state",
    ),
    NsErrorDefinition.for_error_type(
        NsHttpClientError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.HTTP,
        retryable=False,
        disconnect_required=False,
        audit_required=False,
        safe_detail=False,
        action="handle_http_failure",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeDependencyUnavailableError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.DEPENDENCY,
        retryable=True,
        action="retry_runtime_dependency",
    ),
)
