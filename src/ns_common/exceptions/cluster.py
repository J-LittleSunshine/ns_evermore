# -*- coding: utf-8 -*-
from __future__ import annotations

from .base import NsRuntimeError
from .common import NsConfigError
from .metadata import (
    NsErrorCategory,
    NsErrorDefinition,
    NsErrorSeverity,
)


class NsRuntimeClusterCoordinationError(NsRuntimeError):
    code = "RUNTIME_CLUSTER_COORDINATION_ERROR"
    numeric_code = 200115
    default_message = "Runtime cluster coordination error."


class NsRuntimeClusterStateError(NsRuntimeClusterCoordinationError):
    code = "RUNTIME_CLUSTER_STATE_ERROR"
    numeric_code = 200122
    default_message = "Runtime cluster state transition is invalid."


class NsRuntimeClusterFencingError(NsRuntimeClusterCoordinationError):
    code = "RUNTIME_CLUSTER_FENCING_ERROR"
    numeric_code = 200123
    default_message = "Runtime cluster fencing validation failed."


class NsRuntimeRoleAdmissionError(NsRuntimeError):
    code = "RUNTIME_ROLE_ADMISSION_REJECTED"
    numeric_code = 200124
    default_message = "Runtime role admission rejected the operation."


class NsRuntimeStartupSecurityError(NsConfigError):
    code = "RUNTIME_STARTUP_SECURITY_ERROR"
    numeric_code = 200125
    default_message = "Runtime startup security validation failed."


class NsRuntimeLeaderLeaseLostError(NsRuntimeClusterCoordinationError):
    code = "RUNTIME_LEADER_LEASE_LOST"
    numeric_code = 200157
    default_message = "Runtime leader lease is lost."


class NsRuntimeClusterMemberUnavailableError(NsRuntimeClusterCoordinationError):
    code = "RUNTIME_CLUSTER_MEMBER_UNAVAILABLE"
    numeric_code = 200158
    default_message = "Runtime cluster member is unavailable."


class NsRuntimeClusterConfigDriftError(NsRuntimeClusterCoordinationError):
    code = "RUNTIME_CLUSTER_CONFIG_DRIFT"
    numeric_code = 200159
    default_message = "Runtime cluster configuration drift is detected."


CLUSTER_ERROR_DEFINITIONS: tuple[NsErrorDefinition, ...] = (
    NsErrorDefinition.for_error_type(
        NsRuntimeClusterCoordinationError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.CLUSTER,
        retryable=False,
        disconnect_required=False,
        audit_required=False,
        safe_detail=False,
        action="investigate_cluster_coordination",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeClusterStateError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.CLUSTER,
        audit_required=True,
        action="reject_cluster_transition",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeClusterFencingError,
        severity=NsErrorSeverity.CRITICAL,
        category=NsErrorCategory.CLUSTER,
        disconnect_required=True,
        audit_required=True,
        action="reject_stale_fencing",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeRoleAdmissionError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.CLUSTER,
        audit_required=True,
        action="reject_role_admission",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeStartupSecurityError,
        severity=NsErrorSeverity.CRITICAL,
        category=NsErrorCategory.SECURITY,
        audit_required=True,
        action="stop_insecure_startup",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeLeaderLeaseLostError,
        severity=NsErrorSeverity.CRITICAL,
        category=NsErrorCategory.LEASE,
        audit_required=True,
        action="stop_leader_writes",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeClusterMemberUnavailableError,
        severity=NsErrorSeverity.WARNING,
        category=NsErrorCategory.CLUSTER,
        retryable=True,
        action="retry_cluster_member",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeClusterConfigDriftError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.CLUSTER,
        audit_required=True,
        action="isolate_config_drift",
    ),
)
