# -*- coding: utf-8 -*-
from __future__ import annotations

from .base import NsRuntimeError
from .metadata import (
    NsErrorCategory,
    NsErrorDefinition,
    NsErrorSeverity,
)


class NsRuntimeTargetUnavailableError(NsRuntimeError):
    code = "RUNTIME_TARGET_UNAVAILABLE"
    numeric_code = 200109
    default_message = "Runtime target is unavailable."


class NsRuntimeDeliveryStateError(NsRuntimeError):
    code = "RUNTIME_DELIVERY_STATE_ERROR"
    numeric_code = 200110
    default_message = "Runtime delivery state transition is invalid."


class NsRuntimeAckRejectedError(NsRuntimeDeliveryStateError):
    code = "RUNTIME_ACK_REJECTED"
    numeric_code = 200111
    default_message = "Runtime ACK is rejected."


class NsRuntimeNackRejectedError(NsRuntimeDeliveryStateError):
    code = "RUNTIME_NACK_REJECTED"
    numeric_code = 200112
    default_message = "Runtime NACK is rejected."


class NsRuntimeDeferRejectedError(NsRuntimeDeliveryStateError):
    code = "RUNTIME_DEFER_REJECTED"
    numeric_code = 200113
    default_message = "Runtime Defer is rejected."


class NsRuntimeBackpressureError(NsRuntimeError):
    code = "RUNTIME_BACKPRESSURE"
    numeric_code = 200114
    default_message = "Runtime backpressure policy rejected the message."


class NsRuntimeAckTimeoutError(NsRuntimeDeliveryStateError):
    code = "RUNTIME_ACK_TIMEOUT"
    numeric_code = 200135
    default_message = "Runtime ACK deadline is exceeded."


class NsRuntimeNackNonRetryableError(NsRuntimeDeliveryStateError):
    code = "RUNTIME_NACK_NON_RETRYABLE"
    numeric_code = 200136
    default_message = "Runtime NACK is not retryable."


class NsRuntimeDeferBudgetExceededError(NsRuntimeDeliveryStateError):
    code = "RUNTIME_DEFER_BUDGET_EXCEEDED"
    numeric_code = 200137
    default_message = "Runtime Defer budget is exceeded."


class NsRuntimeDeliveryLeaseExpiredError(NsRuntimeDeliveryStateError):
    code = "RUNTIME_DELIVERY_LEASE_EXPIRED"
    numeric_code = 200138
    default_message = "Runtime delivery lease has expired."


class NsRuntimeDeliveryLeaseRenewFailedError(NsRuntimeDeliveryStateError):
    code = "RUNTIME_DELIVERY_LEASE_RENEW_FAILED"
    numeric_code = 200139
    default_message = "Runtime delivery lease renewal failed."


class NsRuntimeFencingRejectedError(NsRuntimeDeliveryStateError):
    code = "RUNTIME_FENCING_REJECTED"
    numeric_code = 200140
    default_message = "Runtime fencing validation rejected the operation."


class NsRuntimeOwnerMismatchError(NsRuntimeDeliveryStateError):
    code = "RUNTIME_OWNER_MISMATCH"
    numeric_code = 200141
    default_message = "Runtime delivery owner does not match."


class NsRuntimeOwnerTransferRejectedError(NsRuntimeDeliveryStateError):
    code = "RUNTIME_OWNER_TRANSFER_REJECTED"
    numeric_code = 200142
    default_message = "Runtime delivery owner transfer is rejected."


class NsRuntimeDeliveryLeaseRejectedError(NsRuntimeDeliveryStateError):
    code = "RUNTIME_DELIVERY_LEASE_REJECTED"
    numeric_code = 200162
    default_message = "Runtime delivery lease token is rejected."


DELIVERY_ERROR_DEFINITIONS: tuple[NsErrorDefinition, ...] = (
    NsErrorDefinition.for_error_type(
        NsRuntimeTargetUnavailableError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.DELIVERY,
        retryable=True,
        action="retry_target_delivery",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeDeliveryStateError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.DELIVERY,
        action="reject_delivery_transition",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeAckRejectedError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.DELIVERY,
        action="reject_ack",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeNackRejectedError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.DELIVERY,
        action="reject_nack",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeDeferRejectedError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.DELIVERY,
        action="reject_defer",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeBackpressureError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.BACKPRESSURE,
        retryable=True,
        action="retry_after_backpressure",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeAckTimeoutError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.ACK,
        retryable=True,
        action="schedule_ack_timeout_retry",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeNackNonRetryableError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.NACK,
        action="dead_letter_non_retryable_nack",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeDeferBudgetExceededError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.DEFER,
        retryable=True,
        action="handle_defer_as_ack_timeout",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeDeliveryLeaseExpiredError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.LEASE,
        retryable=True,
        audit_required=True,
        action="recover_expired_delivery_lease",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeDeliveryLeaseRenewFailedError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.LEASE,
        retryable=True,
        action="retry_delivery_lease_renewal",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeFencingRejectedError,
        severity=NsErrorSeverity.CRITICAL,
        category=NsErrorCategory.FENCING,
        disconnect_required=True,
        audit_required=True,
        action="reject_stale_fencing",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeOwnerMismatchError,
        severity=NsErrorSeverity.CRITICAL,
        category=NsErrorCategory.OWNER,
        audit_required=True,
        action="reject_non_owner_write",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeOwnerTransferRejectedError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.OWNER,
        audit_required=True,
        action="reject_owner_transfer",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeDeliveryLeaseRejectedError,
        severity=NsErrorSeverity.CRITICAL,
        category=NsErrorCategory.LEASE,
        audit_required=True,
        action="reject_delivery_lease",
    ),
)
