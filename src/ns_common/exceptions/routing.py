# -*- coding: utf-8 -*-
from __future__ import annotations

from .base import NsRuntimeError
from .metadata import (
    NsErrorCategory,
    NsErrorDefinition,
    NsErrorSeverity,
)


class NsRuntimeTargetNotFoundError(NsRuntimeError):
    code = "RUNTIME_TARGET_NOT_FOUND"
    numeric_code = 200131
    default_message = "Runtime target does not exist."


class NsRuntimeRouteUnavailableError(NsRuntimeError):
    code = "RUNTIME_ROUTE_UNAVAILABLE"
    numeric_code = 200132
    default_message = "Runtime route is unavailable."


class NsRuntimeRouteRejectedError(NsRuntimeError):
    code = "RUNTIME_ROUTE_REJECTED"
    numeric_code = 200177
    default_message = "Runtime routing policy rejected the request."


class NsRuntimeRouteLoopError(NsRuntimeError):
    code = "RUNTIME_ROUTE_LOOP"
    numeric_code = 200133
    default_message = "Runtime route loop is detected."


class NsRuntimeRouteHopLimitExceededError(NsRuntimeError):
    code = "RUNTIME_ROUTE_HOP_LIMIT_EXCEEDED"
    numeric_code = 200134
    default_message = "Runtime route hop limit is exceeded."


ROUTING_ERROR_DEFINITIONS: tuple[NsErrorDefinition, ...] = (
    NsErrorDefinition.for_error_type(
        NsRuntimeTargetNotFoundError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.ROUTING,
        action="reject_missing_target",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeRouteUnavailableError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.ROUTING,
        retryable=True,
        action="retry_route_resolution",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeRouteRejectedError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.ROUTING,
        action="reject_routing_policy",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeRouteLoopError,
        severity=NsErrorSeverity.CRITICAL,
        category=NsErrorCategory.ROUTING,
        audit_required=True,
        action="stop_route_loop",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeRouteHopLimitExceededError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.ROUTING,
        audit_required=True,
        action="stop_route_forwarding",
    ),
)
