# -*- coding: utf-8 -*-
from __future__ import annotations

from .base import NsRuntimeError
from .metadata import (
    NsErrorCategory,
    NsErrorDefinition,
    NsErrorSeverity,
)


class NsRuntimeProcessorTimeoutError(NsRuntimeError):
    code = "RUNTIME_PROCESSOR_TIMEOUT"
    numeric_code = 200143
    default_message = "Runtime processor timed out."


class NsRuntimeProcessorFailedError(NsRuntimeError):
    code = "RUNTIME_PROCESSOR_FAILED"
    numeric_code = 200144
    default_message = "Runtime processor failed."


PROCESSOR_ERROR_DEFINITIONS: tuple[NsErrorDefinition, ...] = (
    NsErrorDefinition.for_error_type(
        NsRuntimeProcessorTimeoutError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.PROCESSOR,
        retryable=True,
        audit_required=True,
        action="retry_processor_execution",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeProcessorFailedError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.PROCESSOR,
        audit_required=True,
        action="isolate_processor_failure",
    ),
)
