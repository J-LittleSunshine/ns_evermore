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
)
