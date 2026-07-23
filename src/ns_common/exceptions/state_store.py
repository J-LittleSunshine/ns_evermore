# -*- coding: utf-8 -*-
"""Stable, provider-neutral StateStore contract errors."""

from __future__ import annotations

from .base import NsRuntimeError
from .metadata import NsErrorCategory, NsErrorDefinition, NsErrorSeverity


class NsRuntimeStateStoreError(NsRuntimeError):
    code = "RUNTIME_STATE_STORE_ERROR"
    numeric_code = 200166
    default_message = "Runtime StateStore operation failed."


class NsRuntimeStateStoreNotReadyError(NsRuntimeStateStoreError):
    code = "RUNTIME_STATE_STORE_NOT_READY"
    numeric_code = 200167
    default_message = "Runtime StateStore is not ready."


class NsRuntimeStateStoreClosedError(NsRuntimeStateStoreError):
    code = "RUNTIME_STATE_STORE_CLOSED"
    numeric_code = 200168
    default_message = "Runtime StateStore is closed."


class NsRuntimeStateStoreUnavailableError(NsRuntimeStateStoreError):
    code = "RUNTIME_STATE_STORE_UNAVAILABLE"
    numeric_code = 200169
    default_message = "Runtime StateStore is unavailable."


class NsRuntimeStateStoreTimeoutError(NsRuntimeStateStoreError):
    code = "RUNTIME_STATE_STORE_TIMEOUT"
    numeric_code = 200170
    default_message = "Runtime StateStore operation timed out."


class NsRuntimeStateStoreConflictError(NsRuntimeStateStoreError):
    code = "RUNTIME_STATE_STORE_CONFLICT"
    numeric_code = 200171
    default_message = "Runtime StateStore assertion conflicted."


class NsRuntimeStateStoreStaleReadError(NsRuntimeStateStoreError):
    code = "RUNTIME_STATE_STORE_STALE_READ"
    numeric_code = 200172
    default_message = "Runtime StateStore read is stale."


class NsRuntimeStateStoreCapabilityUnavailableError(NsRuntimeStateStoreError):
    code = "RUNTIME_STATE_STORE_CAPABILITY_UNAVAILABLE"
    numeric_code = 200173
    default_message = "Runtime StateStore capability is unavailable."


class NsRuntimeStateStoreNamespaceViolationError(NsRuntimeStateStoreError):
    code = "RUNTIME_STATE_STORE_NAMESPACE_VIOLATION"
    numeric_code = 200174
    default_message = "Runtime StateStore namespace access was rejected."


class NsRuntimeStateStoreVersionMismatchError(NsRuntimeStateStoreError):
    code = "RUNTIME_STATE_STORE_VERSION_MISMATCH"
    numeric_code = 200175
    default_message = "Runtime StateStore version is incompatible."


class NsRuntimeStateStoreIndeterminateWriteError(NsRuntimeStateStoreError):
    code = "RUNTIME_STATE_STORE_INDETERMINATE_WRITE"
    numeric_code = 200176
    default_message = "Runtime StateStore write outcome is indeterminate."


STATE_STORE_ERROR_DEFINITIONS: tuple[NsErrorDefinition, ...] = (
    NsErrorDefinition.for_error_type(
        NsRuntimeStateStoreError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.STATE,
        action="handle_state_store_failure",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeStateStoreNotReadyError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.STATE,
        action="reject_state_store_not_ready",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeStateStoreClosedError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.STATE,
        action="reject_closed_state_store",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeStateStoreUnavailableError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.STATE,
        retryable=True,
        action="probe_state_store_recovery",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeStateStoreTimeoutError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.STATE,
        action="handle_state_store_timeout",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeStateStoreConflictError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.STATE,
        action="reconcile_state_store_conflict",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeStateStoreStaleReadError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.STATE,
        action="reject_stale_state_read",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeStateStoreCapabilityUnavailableError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.STATE,
        action="reject_state_store_capability",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeStateStoreNamespaceViolationError,
        severity=NsErrorSeverity.CRITICAL,
        category=NsErrorCategory.STATE,
        audit_required=True,
        action="reject_state_store_namespace",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeStateStoreVersionMismatchError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.STATE,
        action="reject_state_store_version",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeStateStoreIndeterminateWriteError,
        severity=NsErrorSeverity.CRITICAL,
        category=NsErrorCategory.STATE,
        audit_required=True,
        action="reconcile_indeterminate_write",
    ),
)


__all__ = (
    "NsRuntimeStateStoreCapabilityUnavailableError",
    "NsRuntimeStateStoreClosedError",
    "NsRuntimeStateStoreConflictError",
    "NsRuntimeStateStoreError",
    "NsRuntimeStateStoreIndeterminateWriteError",
    "NsRuntimeStateStoreNamespaceViolationError",
    "NsRuntimeStateStoreNotReadyError",
    "NsRuntimeStateStoreStaleReadError",
    "NsRuntimeStateStoreTimeoutError",
    "NsRuntimeStateStoreUnavailableError",
    "NsRuntimeStateStoreVersionMismatchError",
    "STATE_STORE_ERROR_DEFINITIONS",
)
