# -*- coding: utf-8 -*-
from __future__ import annotations

from .base import NsRuntimeError
from .metadata import (
    NsErrorCategory,
    NsErrorDefinition,
    NsErrorSeverity,
)


class NsRuntimeIamDeniedError(NsRuntimeError):
    code = "RUNTIME_IAM_DENIED"
    numeric_code = 200127
    default_message = "Runtime IAM denied the operation."


class NsRuntimeIamUnavailableError(NsRuntimeError):
    code = "RUNTIME_IAM_UNAVAILABLE"
    numeric_code = 200128
    default_message = "Runtime IAM service is unavailable."


class NsRuntimeIamTimeoutError(NsRuntimeIamUnavailableError):
    code = "RUNTIME_IAM_TIMEOUT"
    numeric_code = 200129
    default_message = "Runtime IAM request timed out."


class NsRuntimeTenantQuotaExceededError(NsRuntimeError):
    code = "RUNTIME_TENANT_QUOTA_EXCEEDED"
    numeric_code = 200130
    default_message = "Runtime tenant quota is exceeded."


class NsRuntimeTenantPausedError(NsRuntimeError):
    code = "RUNTIME_TENANT_PAUSED"
    numeric_code = 200160
    default_message = "Runtime tenant processing is paused."


IAM_ERROR_DEFINITIONS: tuple[NsErrorDefinition, ...] = (
    NsErrorDefinition.for_error_type(
        NsRuntimeIamDeniedError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.IAM,
        audit_required=True,
        action="reject_iam_denied",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeIamUnavailableError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.IAM,
        retryable=True,
        action="retry_iam_request",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeIamTimeoutError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.IAM,
        retryable=True,
        action="retry_iam_request",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeTenantQuotaExceededError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.TENANT,
        retryable=True,
        action="defer_for_tenant_quota",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeTenantPausedError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.TENANT,
        retryable=True,
        action="wait_for_tenant_resume",
    ),
)
