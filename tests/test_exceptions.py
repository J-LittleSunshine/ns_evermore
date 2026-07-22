# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
import inspect
import json
import os
import subprocess
import sys
import types
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import ns_common
import ns_common.exceptions as exceptions_facade
from ns_common.async_runtime import NsEventLoopSelector
from ns_common.config import NsConfigGroupMetadata, NsRuntimeEventLoopConfig
from ns_common.exceptions import (
    ALL_ERROR_DEFINITIONS,
    ERROR_REGISTRY,
    RUNTIME_ERROR_COVERAGE_MATRIX,
    RUNTIME_NACK_REASON_ERROR_CODES,
    NsConfigError,
    NsErrorCategory,
    NsErrorDefinition,
    NsErrorRegistry,
    NsErrorSeverity,
    NsEvermoreError,
    NsDependencyError,
    NsHttpClientError,
    NsRuntimeError,
    NsRuntimePayloadRefValidationTimeoutError,
    NsRuntimePayloadRefValidationUnavailableError,
    NsRuntimeStartupSecurityError,
    NsValidationError,
    get_error_definition,
    get_error_definition_by_code,
    get_error_definition_by_numeric_code,
    list_error_definitions,
    validate_error_registry,
    validate_runtime_error_coverage_matrix,
    validate_runtime_nack_reason_error_codes,
)
from ns_common.http_client import NsHttpResponse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEPTIONS_PACKAGE = PROJECT_ROOT / "src" / "ns_common" / "exceptions"

EXCEPTION_SUBMODULES = (
    "ns_common.exceptions.base",
    "ns_common.exceptions.metadata",
    "ns_common.exceptions.common",
    "ns_common.exceptions.configuration",
    "ns_common.exceptions.protocol",
    "ns_common.exceptions.iam",
    "ns_common.exceptions.routing",
    "ns_common.exceptions.payload_ref",
    "ns_common.exceptions.delivery",
    "ns_common.exceptions.processor",
    "ns_common.exceptions.transport",
    "ns_common.exceptions.cluster",
    "ns_common.exceptions.state_store",
    "ns_common.exceptions.registry",
    "ns_common.exceptions.nack",
)

EXCEPTION_SNAPSHOTS = {
    "NsEvermoreError": (
        "Exception",
        "NS_ERROR",
        100000,
        "NsEvermore error.",
    ),
    "NsConfigError": (
        "NsEvermoreError",
        "NS_CONFIG_ERROR",
        100100,
        "Invalid ns_evermore configuration.",
    ),
    "NsValidationError": (
        "NsEvermoreError",
        "NS_VALIDATION_ERROR",
        100200,
        "Validation failed.",
    ),
    "NsRuntimeError": (
        "NsEvermoreError",
        "NS_RUNTIME_ERROR",
        100300,
        "NsEvermore runtime error.",
    ),
    "NsDependencyError": (
        "NsEvermoreError",
        "NS_DEPENDENCY_ERROR",
        100400,
        "NsEvermore dependency error.",
    ),
    "NsStateError": (
        "NsEvermoreError",
        "NS_STATE_ERROR",
        100500,
        "Invalid ns_evermore internal state.",
    ),
    "NsHttpClientError": (
        "NsEvermoreError",
        "NS_HTTP_CLIENT_ERROR",
        100600,
        "NsEvermore HTTP client error.",
    ),
    "NsRuntimeProtocolError": (
        "NsRuntimeError",
        "RUNTIME_PROTOCOL_ERROR",
        200100,
        "Runtime protocol error.",
    ),
    "NsRuntimeEnvelopeSchemaError": (
        "NsRuntimeProtocolError",
        "RUNTIME_ENVELOPE_SCHEMA_ERROR",
        200101,
        "Runtime envelope schema error.",
    ),
    "NsRuntimeProtocolVersionError": (
        "NsRuntimeProtocolError",
        "RUNTIME_PROTOCOL_VERSION_ERROR",
        200102,
        "Runtime protocol version is incompatible.",
    ),
    "NsRuntimeSourceForgedError": (
        "NsRuntimeProtocolError",
        "RUNTIME_SOURCE_FORGED",
        200103,
        "Inbound envelope must not contain source.",
    ),
    "NsRuntimeAuthContextForgedError": (
        "NsRuntimeProtocolError",
        "RUNTIME_AUTH_CONTEXT_FORGED",
        200104,
        "Inbound envelope must not contain auth_context.",
    ),
    "NsRuntimeUnsupportedMessageTypeError": (
        "NsRuntimeProtocolError",
        "RUNTIME_UNSUPPORTED_MESSAGE_TYPE",
        200105,
        "Runtime message type is not registered.",
    ),
    "NsRuntimeUnauthorizedMessageTypeError": (
        "NsRuntimeProtocolError",
        "RUNTIME_UNAUTHORIZED_MESSAGE_TYPE",
        200106,
        "Runtime message type is not allowed by current capability.",
    ),
    "NsRuntimeTenantMismatchError": (
        "NsRuntimeProtocolError",
        "RUNTIME_TENANT_MISMATCH",
        200107,
        "Runtime tenant boundary is violated.",
    ),
    "NsRuntimePayloadRefDeniedError": (
        "NsRuntimeProtocolError",
        "RUNTIME_PAYLOAD_REF_DENIED",
        200108,
        "Runtime payload reference is denied.",
    ),
    "NsRuntimeTargetUnavailableError": (
        "NsRuntimeError",
        "RUNTIME_TARGET_UNAVAILABLE",
        200109,
        "Runtime target is unavailable.",
    ),
    "NsRuntimeDeliveryStateError": (
        "NsRuntimeError",
        "RUNTIME_DELIVERY_STATE_ERROR",
        200110,
        "Runtime delivery state transition is invalid.",
    ),
    "NsRuntimeAckRejectedError": (
        "NsRuntimeDeliveryStateError",
        "RUNTIME_ACK_REJECTED",
        200111,
        "Runtime ACK is rejected.",
    ),
    "NsRuntimeNackRejectedError": (
        "NsRuntimeDeliveryStateError",
        "RUNTIME_NACK_REJECTED",
        200112,
        "Runtime NACK is rejected.",
    ),
    "NsRuntimeDeferRejectedError": (
        "NsRuntimeDeliveryStateError",
        "RUNTIME_DEFER_REJECTED",
        200113,
        "Runtime Defer is rejected.",
    ),
    "NsRuntimeBackpressureError": (
        "NsRuntimeError",
        "RUNTIME_BACKPRESSURE",
        200114,
        "Runtime backpressure policy rejected the message.",
    ),
    "NsRuntimeClusterCoordinationError": (
        "NsRuntimeError",
        "RUNTIME_CLUSTER_COORDINATION_ERROR",
        200115,
        "Runtime cluster coordination error.",
    ),
    "NsRuntimePayloadRefInvalidError": (
        "NsRuntimeProtocolError",
        "RUNTIME_PAYLOAD_REF_INVALID",
        200116,
        "Runtime payload reference is invalid.",
    ),
    "NsRuntimePayloadRefExpiredError": (
        "NsRuntimeProtocolError",
        "RUNTIME_PAYLOAD_REF_EXPIRED",
        200117,
        "Runtime payload reference has expired.",
    ),
    "NsRuntimePayloadRefChecksumMismatchError": (
        "NsRuntimeProtocolError",
        "RUNTIME_PAYLOAD_REF_CHECKSUM_MISMATCH",
        200118,
        "Runtime payload reference checksum does not match.",
    ),
    "NsRuntimePayloadRefVersionMismatchError": (
        "NsRuntimeProtocolError",
        "RUNTIME_PAYLOAD_REF_VERSION_MISMATCH",
        200119,
        "Runtime payload reference version does not match.",
    ),
    "NsRuntimePayloadRefValidationUnavailableError": (
        "NsRuntimeError",
        "RUNTIME_PAYLOAD_REF_VALIDATION_UNAVAILABLE",
        200120,
        "Runtime payload reference validation is unavailable.",
    ),
    "NsRuntimePayloadRefValidationTimeoutError": (
        "NsRuntimePayloadRefValidationUnavailableError",
        "RUNTIME_PAYLOAD_REF_VALIDATION_TIMEOUT",
        200121,
        "Runtime payload reference validation timed out.",
    ),
    "NsRuntimeClusterStateError": (
        "NsRuntimeClusterCoordinationError",
        "RUNTIME_CLUSTER_STATE_ERROR",
        200122,
        "Runtime cluster state transition is invalid.",
    ),
    "NsRuntimeClusterFencingError": (
        "NsRuntimeClusterCoordinationError",
        "RUNTIME_CLUSTER_FENCING_ERROR",
        200123,
        "Runtime cluster fencing validation failed.",
    ),
    "NsRuntimeRoleAdmissionError": (
        "NsRuntimeError",
        "RUNTIME_ROLE_ADMISSION_REJECTED",
        200124,
        "Runtime role admission rejected the operation.",
    ),
    "NsRuntimeStartupSecurityError": (
        "NsConfigError",
        "RUNTIME_STARTUP_SECURITY_ERROR",
        200125,
        "Runtime startup security validation failed.",
    ),
}

EXCEPTION_SNAPSHOTS = {
    **EXCEPTION_SNAPSHOTS,
    "NsRuntimeProtocolParseError": (
        "NsRuntimeProtocolError",
        "RUNTIME_PROTOCOL_PARSE_ERROR",
        200126,
        "Runtime protocol payload cannot be parsed.",
    ),
    "NsRuntimeIamDeniedError": (
        "NsRuntimeError",
        "RUNTIME_IAM_DENIED",
        200127,
        "Runtime IAM denied the operation.",
    ),
    "NsRuntimeIamUnavailableError": (
        "NsRuntimeError",
        "RUNTIME_IAM_UNAVAILABLE",
        200128,
        "Runtime IAM service is unavailable.",
    ),
    "NsRuntimeIamTimeoutError": (
        "NsRuntimeIamUnavailableError",
        "RUNTIME_IAM_TIMEOUT",
        200129,
        "Runtime IAM request timed out.",
    ),
    "NsRuntimeTenantQuotaExceededError": (
        "NsRuntimeError",
        "RUNTIME_TENANT_QUOTA_EXCEEDED",
        200130,
        "Runtime tenant quota is exceeded.",
    ),
    "NsRuntimeTargetNotFoundError": (
        "NsRuntimeError",
        "RUNTIME_TARGET_NOT_FOUND",
        200131,
        "Runtime target does not exist.",
    ),
    "NsRuntimeRouteUnavailableError": (
        "NsRuntimeError",
        "RUNTIME_ROUTE_UNAVAILABLE",
        200132,
        "Runtime route is unavailable.",
    ),
    "NsRuntimeRouteLoopError": (
        "NsRuntimeError",
        "RUNTIME_ROUTE_LOOP",
        200133,
        "Runtime route loop is detected.",
    ),
    "NsRuntimeRouteHopLimitExceededError": (
        "NsRuntimeError",
        "RUNTIME_ROUTE_HOP_LIMIT_EXCEEDED",
        200134,
        "Runtime route hop limit is exceeded.",
    ),
    "NsRuntimeAckTimeoutError": (
        "NsRuntimeDeliveryStateError",
        "RUNTIME_ACK_TIMEOUT",
        200135,
        "Runtime ACK deadline is exceeded.",
    ),
    "NsRuntimeNackNonRetryableError": (
        "NsRuntimeDeliveryStateError",
        "RUNTIME_NACK_NON_RETRYABLE",
        200136,
        "Runtime NACK is not retryable.",
    ),
    "NsRuntimeDeferBudgetExceededError": (
        "NsRuntimeDeliveryStateError",
        "RUNTIME_DEFER_BUDGET_EXCEEDED",
        200137,
        "Runtime Defer budget is exceeded.",
    ),
    "NsRuntimeDeliveryLeaseExpiredError": (
        "NsRuntimeDeliveryStateError",
        "RUNTIME_DELIVERY_LEASE_EXPIRED",
        200138,
        "Runtime delivery lease has expired.",
    ),
    "NsRuntimeDeliveryLeaseRenewFailedError": (
        "NsRuntimeDeliveryStateError",
        "RUNTIME_DELIVERY_LEASE_RENEW_FAILED",
        200139,
        "Runtime delivery lease renewal failed.",
    ),
    "NsRuntimeFencingRejectedError": (
        "NsRuntimeDeliveryStateError",
        "RUNTIME_FENCING_REJECTED",
        200140,
        "Runtime fencing validation rejected the operation.",
    ),
    "NsRuntimeOwnerMismatchError": (
        "NsRuntimeDeliveryStateError",
        "RUNTIME_OWNER_MISMATCH",
        200141,
        "Runtime delivery owner does not match.",
    ),
    "NsRuntimeOwnerTransferRejectedError": (
        "NsRuntimeDeliveryStateError",
        "RUNTIME_OWNER_TRANSFER_REJECTED",
        200142,
        "Runtime delivery owner transfer is rejected.",
    ),
    "NsRuntimeProcessorTimeoutError": (
        "NsRuntimeError",
        "RUNTIME_PROCESSOR_TIMEOUT",
        200143,
        "Runtime processor timed out.",
    ),
    "NsRuntimeProcessorFailedError": (
        "NsRuntimeError",
        "RUNTIME_PROCESSOR_FAILED",
        200144,
        "Runtime processor failed.",
    ),
    "NsRuntimeConfigInvalidError": (
        "NsConfigError",
        "RUNTIME_CONFIG_INVALID",
        200145,
        "Runtime configuration is invalid.",
    ),
    "NsRuntimeConfigVersionConflictError": (
        "NsConfigError",
        "RUNTIME_CONFIG_VERSION_CONFLICT",
        200146,
        "Runtime configuration version conflicts.",
    ),
    "NsRuntimeConfigApplyFailedError": (
        "NsConfigError",
        "RUNTIME_CONFIG_APPLY_FAILED",
        200147,
        "Runtime configuration could not be applied.",
    ),
    "NsRuntimeTransportError": (
        "NsRuntimeError",
        "RUNTIME_TRANSPORT_ERROR",
        200148,
        "Runtime transport error.",
    ),
    "NsRuntimeTransportDisabledError": (
        "NsRuntimeTransportError",
        "RUNTIME_TRANSPORT_DISABLED",
        200149,
        "Runtime transport is disabled.",
    ),
    "NsRuntimeTransportHandshakeFailedError": (
        "NsRuntimeTransportError",
        "RUNTIME_TRANSPORT_HANDSHAKE_FAILED",
        200150,
        "Runtime transport handshake failed.",
    ),
    "NsRuntimeTransportSendFailedError": (
        "NsRuntimeTransportError",
        "RUNTIME_TRANSPORT_SEND_FAILED",
        200151,
        "Runtime transport send failed.",
    ),
    "NsRuntimeTransportReceiveFailedError": (
        "NsRuntimeTransportError",
        "RUNTIME_TRANSPORT_RECEIVE_FAILED",
        200152,
        "Runtime transport receive failed.",
    ),
    "NsRuntimeTransportStreamResetError": (
        "NsRuntimeTransportError",
        "RUNTIME_TRANSPORT_STREAM_RESET",
        200153,
        "Runtime transport stream was reset.",
    ),
    "NsRuntimeTransportFlowControlBlockedError": (
        "NsRuntimeTransportError",
        "RUNTIME_TRANSPORT_FLOW_CONTROL_BLOCKED",
        200154,
        "Runtime transport flow control is blocked.",
    ),
    "NsRuntimeTransportPathMigrationFailedError": (
        "NsRuntimeTransportError",
        "RUNTIME_TRANSPORT_PATH_MIGRATION_FAILED",
        200155,
        "Runtime transport path migration failed.",
    ),
    "NsRuntimeTransportFallbackFailedError": (
        "NsRuntimeTransportError",
        "RUNTIME_TRANSPORT_FALLBACK_FAILED",
        200156,
        "Runtime transport fallback failed.",
    ),
    "NsRuntimeLeaderLeaseLostError": (
        "NsRuntimeClusterCoordinationError",
        "RUNTIME_LEADER_LEASE_LOST",
        200157,
        "Runtime leader lease is lost.",
    ),
    "NsRuntimeClusterMemberUnavailableError": (
        "NsRuntimeClusterCoordinationError",
        "RUNTIME_CLUSTER_MEMBER_UNAVAILABLE",
        200158,
        "Runtime cluster member is unavailable.",
    ),
    "NsRuntimeClusterConfigDriftError": (
        "NsRuntimeClusterCoordinationError",
        "RUNTIME_CLUSTER_CONFIG_DRIFT",
        200159,
        "Runtime cluster configuration drift is detected.",
    ),
    "NsRuntimeTenantPausedError": (
        "NsRuntimeError",
        "RUNTIME_TENANT_PAUSED",
        200160,
        "Runtime tenant processing is paused.",
    ),
    "NsRuntimeTransportCapabilityUnavailableError": (
        "NsRuntimeTransportError",
        "RUNTIME_TRANSPORT_CAPABILITY_UNAVAILABLE",
        200161,
        "Runtime transport capability is unavailable.",
    ),
    "NsRuntimeDeliveryLeaseRejectedError": (
        "NsRuntimeDeliveryStateError",
        "RUNTIME_DELIVERY_LEASE_REJECTED",
        200162,
        "Runtime delivery lease token is rejected.",
    ),
    "NsRuntimeDependencyUnavailableError": (
        "NsRuntimeError",
        "RUNTIME_DEPENDENCY_UNAVAILABLE",
        200163,
        "Runtime dependency is unavailable.",
    ),
    "NsRuntimeProtocolViolationError": (
        "NsRuntimeProtocolError",
        "RUNTIME_PROTOCOL_VIOLATION",
        200164,
        "Runtime protocol violation is detected.",
    ),
    "NsRuntimeFeatureDisabledError": (
        "NsRuntimeError",
        "RUNTIME_FEATURE_DISABLED",
        200165,
        "Runtime feature is disabled.",
    ),
    "NsRuntimeStateStoreError": (
        "NsRuntimeError",
        "RUNTIME_STATE_STORE_ERROR",
        200166,
        "Runtime StateStore operation failed.",
    ),
    "NsRuntimeStateStoreNotReadyError": (
        "NsRuntimeStateStoreError",
        "RUNTIME_STATE_STORE_NOT_READY",
        200167,
        "Runtime StateStore is not ready.",
    ),
    "NsRuntimeStateStoreClosedError": (
        "NsRuntimeStateStoreError",
        "RUNTIME_STATE_STORE_CLOSED",
        200168,
        "Runtime StateStore is closed.",
    ),
    "NsRuntimeStateStoreUnavailableError": (
        "NsRuntimeStateStoreError",
        "RUNTIME_STATE_STORE_UNAVAILABLE",
        200169,
        "Runtime StateStore is unavailable.",
    ),
    "NsRuntimeStateStoreTimeoutError": (
        "NsRuntimeStateStoreError",
        "RUNTIME_STATE_STORE_TIMEOUT",
        200170,
        "Runtime StateStore operation timed out.",
    ),
    "NsRuntimeStateStoreConflictError": (
        "NsRuntimeStateStoreError",
        "RUNTIME_STATE_STORE_CONFLICT",
        200171,
        "Runtime StateStore assertion conflicted.",
    ),
    "NsRuntimeStateStoreStaleReadError": (
        "NsRuntimeStateStoreError",
        "RUNTIME_STATE_STORE_STALE_READ",
        200172,
        "Runtime StateStore read is stale.",
    ),
    "NsRuntimeStateStoreCapabilityUnavailableError": (
        "NsRuntimeStateStoreError",
        "RUNTIME_STATE_STORE_CAPABILITY_UNAVAILABLE",
        200173,
        "Runtime StateStore capability is unavailable.",
    ),
    "NsRuntimeStateStoreNamespaceViolationError": (
        "NsRuntimeStateStoreError",
        "RUNTIME_STATE_STORE_NAMESPACE_VIOLATION",
        200174,
        "Runtime StateStore namespace access was rejected.",
    ),
    "NsRuntimeStateStoreVersionMismatchError": (
        "NsRuntimeStateStoreError",
        "RUNTIME_STATE_STORE_VERSION_MISMATCH",
        200175,
        "Runtime StateStore version is incompatible.",
    ),
    "NsRuntimeStateStoreIndeterminateWriteError": (
        "NsRuntimeStateStoreError",
        "RUNTIME_STATE_STORE_INDETERMINATE_WRITE",
        200176,
        "Runtime StateStore write outcome is indeterminate.",
    ),
}

TOP_LEVEL_EXCEPTION_EXPORTS = (
    "NsConfigError",
    "NsDependencyError",
    "NsEvermoreError",
    "NsHttpClientError",
    "NsRuntimeAckRejectedError",
    "NsRuntimeAuthContextForgedError",
    "NsRuntimeBackpressureError",
    "NsRuntimeClusterCoordinationError",
    "NsRuntimeDeferRejectedError",
    "NsRuntimeDeliveryStateError",
    "NsRuntimeEnvelopeSchemaError",
    "NsRuntimeError",
    "NsRuntimeNackRejectedError",
    "NsRuntimePayloadRefDeniedError",
    "NsRuntimeProtocolError",
    "NsRuntimeProtocolVersionError",
    "NsRuntimeSourceForgedError",
    "NsRuntimeTargetUnavailableError",
    "NsRuntimeTenantMismatchError",
    "NsRuntimeUnauthorizedMessageTypeError",
    "NsRuntimeUnsupportedMessageTypeError",
    "NsStateError",
    "NsValidationError",
)


REQUIRED_RUNTIME_ERROR_SCENARIOS = {
    "feature_disabled": "RUNTIME_FEATURE_DISABLED",
    "protocol_parse": "RUNTIME_PROTOCOL_PARSE_ERROR",
    "protocol_violation": "RUNTIME_PROTOCOL_VIOLATION",
    "envelope_schema": "RUNTIME_ENVELOPE_SCHEMA_ERROR",
    "protocol_version": "RUNTIME_PROTOCOL_VERSION_ERROR",
    "source_forged": "RUNTIME_SOURCE_FORGED",
    "auth_context_forged": "RUNTIME_AUTH_CONTEXT_FORGED",
    "iam_denied": "RUNTIME_IAM_DENIED",
    "tenant_mismatch": "RUNTIME_TENANT_MISMATCH",
    "target_not_found": "RUNTIME_TARGET_NOT_FOUND",
    "route_unavailable": "RUNTIME_ROUTE_UNAVAILABLE",
    "ack_timeout": "RUNTIME_ACK_TIMEOUT",
    "nack_non_retryable": "RUNTIME_NACK_NON_RETRYABLE",
    "defer_budget_exceeded": "RUNTIME_DEFER_BUDGET_EXCEEDED",
    "fencing_rejected": "RUNTIME_FENCING_REJECTED",
    "owner_mismatch": "RUNTIME_OWNER_MISMATCH",
    "payload_ref_invalid": "RUNTIME_PAYLOAD_REF_INVALID",
    "leader_lease_lost": "RUNTIME_LEADER_LEASE_LOST",
    "processor_timeout": "RUNTIME_PROCESSOR_TIMEOUT",
    "illegal_delivery_transition": "RUNTIME_DELIVERY_STATE_ERROR",
}


def validate_required_runtime_error_scenarios(
    scenarios: dict[str, str] = REQUIRED_RUNTIME_ERROR_SCENARIOS,
    coverage_matrix: tuple[tuple[str, tuple[str, ...]], ...] = (
        RUNTIME_ERROR_COVERAGE_MATRIX
    ),
    registry: NsErrorRegistry = ERROR_REGISTRY,
) -> dict[str, str]:
    if not isinstance(scenarios, dict):
        raise TypeError("required runtime error scenarios must be a dict")
    if not isinstance(registry, NsErrorRegistry):
        raise TypeError("registry must be NsErrorRegistry")

    scenario_names = tuple(scenarios)
    if len(scenario_names) != len(set(scenario_names)):
        raise ValueError("required runtime scenario names must be unique")

    scenario_codes = tuple(scenarios.values())
    if len(scenario_codes) != len(set(scenario_codes)):
        raise ValueError("required runtime scenario codes must be unique")

    covered_codes = {
        code
        for _, codes in coverage_matrix
        for code in codes
    }
    for scenario_name, code in scenarios.items():
        if not isinstance(scenario_name, str) or not scenario_name.strip():
            raise ValueError("required runtime scenario name must be non-empty")
        if not isinstance(code, str) or not code.startswith("RUNTIME_"):
            raise ValueError(
                "required runtime scenario code must start with RUNTIME_"
            )
        if registry.get_by_code(code) is None:
            raise ValueError(
                f"required runtime scenario code is not registered: {code}"
            )
        if code not in covered_codes:
            raise ValueError(
                f"required runtime scenario code is not covered: {code}"
            )

    return scenarios


def expected_policy(
    severity: NsErrorSeverity,
    category: NsErrorCategory,
    action: str,
    *,
    retryable: bool = False,
    disconnect_required: bool = False,
    audit_required: bool = False,
    safe_detail: bool = False,
) -> dict[str, object]:
    return {
        "severity": severity,
        "category": category,
        "retryable": retryable,
        "disconnect_required": disconnect_required,
        "audit_required": audit_required,
        "safe_detail": safe_detail,
        "action": action,
    }


EXPECTED_ERROR_POLICIES: dict[
    type[NsEvermoreError], dict[str, object]
] = {
    exceptions_facade.NsEvermoreError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.COMMON,
        "report_error",
    ),
    exceptions_facade.NsRuntimeError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.RUNTIME,
        "report_runtime_error",
    ),
    exceptions_facade.NsConfigError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.CONFIGURATION,
        "fix_configuration",
    ),
    exceptions_facade.NsValidationError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.VALIDATION,
        "reject_invalid_input",
    ),
    exceptions_facade.NsDependencyError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.DEPENDENCY,
        "inspect_dependency",
    ),
    exceptions_facade.NsStateError: expected_policy(
        NsErrorSeverity.CRITICAL,
        NsErrorCategory.STATE,
        "investigate_state",
    ),
    exceptions_facade.NsHttpClientError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.HTTP,
        "handle_http_failure",
    ),
    exceptions_facade.NsRuntimeProtocolError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.PROTOCOL,
        "reject_protocol_message",
    ),
    exceptions_facade.NsRuntimeEnvelopeSchemaError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.PROTOCOL,
        "reject_invalid_envelope",
        disconnect_required=True,
    ),
    exceptions_facade.NsRuntimeProtocolVersionError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.PROTOCOL,
        "reject_protocol_version",
        disconnect_required=True,
    ),
    exceptions_facade.NsRuntimeSourceForgedError: expected_policy(
        NsErrorSeverity.CRITICAL,
        NsErrorCategory.SECURITY,
        "reject_forged_source",
        disconnect_required=True,
        audit_required=True,
    ),
    exceptions_facade.NsRuntimeAuthContextForgedError: expected_policy(
        NsErrorSeverity.CRITICAL,
        NsErrorCategory.SECURITY,
        "reject_forged_auth_context",
        disconnect_required=True,
        audit_required=True,
    ),
    exceptions_facade.NsRuntimeUnsupportedMessageTypeError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.PROTOCOL,
        "reject_unsupported_message",
    ),
    exceptions_facade.NsRuntimeUnauthorizedMessageTypeError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.SECURITY,
        "reject_unauthorized_message",
        audit_required=True,
    ),
    exceptions_facade.NsRuntimeTenantMismatchError: expected_policy(
        NsErrorSeverity.CRITICAL,
        NsErrorCategory.SECURITY,
        "reject_tenant_mismatch",
        disconnect_required=True,
        audit_required=True,
    ),
    exceptions_facade.NsRuntimePayloadRefDeniedError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.PAYLOAD_REF,
        "reject_payload_ref",
        audit_required=True,
    ),
    exceptions_facade.NsRuntimePayloadRefInvalidError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.PAYLOAD_REF,
        "reject_invalid_payload_ref",
    ),
    exceptions_facade.NsRuntimePayloadRefExpiredError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.PAYLOAD_REF,
        "refresh_payload_ref",
    ),
    exceptions_facade.NsRuntimePayloadRefChecksumMismatchError: expected_policy(
        NsErrorSeverity.CRITICAL,
        NsErrorCategory.PAYLOAD_REF,
        "reject_payload_checksum",
        audit_required=True,
    ),
    exceptions_facade.NsRuntimePayloadRefVersionMismatchError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.PAYLOAD_REF,
        "reject_payload_version",
    ),
    exceptions_facade.NsRuntimePayloadRefValidationUnavailableError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.PAYLOAD_REF,
        "retry_payload_validation",
        retryable=True,
    ),
    exceptions_facade.NsRuntimePayloadRefValidationTimeoutError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.PAYLOAD_REF,
        "retry_payload_validation",
        retryable=True,
    ),
    exceptions_facade.NsRuntimeTargetUnavailableError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.DELIVERY,
        "retry_target_delivery",
        retryable=True,
    ),
    exceptions_facade.NsRuntimeDeliveryStateError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.DELIVERY,
        "reject_delivery_transition",
    ),
    exceptions_facade.NsRuntimeAckRejectedError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.DELIVERY,
        "reject_ack",
    ),
    exceptions_facade.NsRuntimeNackRejectedError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.DELIVERY,
        "reject_nack",
    ),
    exceptions_facade.NsRuntimeDeferRejectedError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.DELIVERY,
        "reject_defer",
    ),
    exceptions_facade.NsRuntimeBackpressureError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.BACKPRESSURE,
        "retry_after_backpressure",
        retryable=True,
    ),
    exceptions_facade.NsRuntimeClusterCoordinationError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.CLUSTER,
        "investigate_cluster_coordination",
    ),
    exceptions_facade.NsRuntimeClusterStateError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.CLUSTER,
        "reject_cluster_transition",
        audit_required=True,
    ),
    exceptions_facade.NsRuntimeClusterFencingError: expected_policy(
        NsErrorSeverity.CRITICAL,
        NsErrorCategory.CLUSTER,
        "reject_stale_fencing",
        disconnect_required=True,
        audit_required=True,
    ),
    exceptions_facade.NsRuntimeRoleAdmissionError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.CLUSTER,
        "reject_role_admission",
        audit_required=True,
    ),
    exceptions_facade.NsRuntimeStartupSecurityError: expected_policy(
        NsErrorSeverity.CRITICAL,
        NsErrorCategory.SECURITY,
        "stop_insecure_startup",
        audit_required=True,
    ),
}

EXPECTED_ERROR_POLICIES = {
    **EXPECTED_ERROR_POLICIES,
    exceptions_facade.NsRuntimeProtocolParseError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.PROTOCOL,
        "reject_unparseable_message",
    ),
    exceptions_facade.NsRuntimeProtocolViolationError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.PROTOCOL,
        "reject_protocol_violation",
        audit_required=True,
    ),
    exceptions_facade.NsRuntimeIamDeniedError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.IAM,
        "reject_iam_denied",
        audit_required=True,
    ),
    exceptions_facade.NsRuntimeIamUnavailableError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.IAM,
        "retry_iam_request",
        retryable=True,
    ),
    exceptions_facade.NsRuntimeIamTimeoutError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.IAM,
        "retry_iam_request",
        retryable=True,
    ),
    exceptions_facade.NsRuntimeTenantQuotaExceededError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.TENANT,
        "defer_for_tenant_quota",
        retryable=True,
    ),
    exceptions_facade.NsRuntimeTargetNotFoundError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.ROUTING,
        "reject_missing_target",
    ),
    exceptions_facade.NsRuntimeRouteUnavailableError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.ROUTING,
        "retry_route_resolution",
        retryable=True,
    ),
    exceptions_facade.NsRuntimeRouteLoopError: expected_policy(
        NsErrorSeverity.CRITICAL,
        NsErrorCategory.ROUTING,
        "stop_route_loop",
        audit_required=True,
    ),
    exceptions_facade.NsRuntimeRouteHopLimitExceededError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.ROUTING,
        "stop_route_forwarding",
        audit_required=True,
    ),
    exceptions_facade.NsRuntimeAckTimeoutError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.ACK,
        "schedule_ack_timeout_retry",
        retryable=True,
    ),
    exceptions_facade.NsRuntimeNackNonRetryableError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.NACK,
        "dead_letter_non_retryable_nack",
    ),
    exceptions_facade.NsRuntimeDeferBudgetExceededError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.DEFER,
        "handle_defer_as_ack_timeout",
        retryable=True,
    ),
    exceptions_facade.NsRuntimeDeliveryLeaseExpiredError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.LEASE,
        "recover_expired_delivery_lease",
        retryable=True,
        audit_required=True,
    ),
    exceptions_facade.NsRuntimeDeliveryLeaseRenewFailedError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.LEASE,
        "retry_delivery_lease_renewal",
        retryable=True,
    ),
    exceptions_facade.NsRuntimeFencingRejectedError: expected_policy(
        NsErrorSeverity.CRITICAL,
        NsErrorCategory.FENCING,
        "reject_stale_fencing",
        disconnect_required=True,
        audit_required=True,
    ),
    exceptions_facade.NsRuntimeOwnerMismatchError: expected_policy(
        NsErrorSeverity.CRITICAL,
        NsErrorCategory.OWNER,
        "reject_non_owner_write",
        audit_required=True,
    ),
    exceptions_facade.NsRuntimeOwnerTransferRejectedError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.OWNER,
        "reject_owner_transfer",
        audit_required=True,
    ),
    exceptions_facade.NsRuntimeProcessorTimeoutError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.PROCESSOR,
        "isolate_processor_timeout",
        audit_required=True,
    ),
    exceptions_facade.NsRuntimeProcessorFailedError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.PROCESSOR,
        "isolate_processor_failure",
        audit_required=True,
    ),
    exceptions_facade.NsRuntimeConfigInvalidError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.CONFIGURATION,
        "reject_runtime_configuration",
    ),
    exceptions_facade.NsRuntimeConfigVersionConflictError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.CONFIGURATION,
        "reject_config_version_conflict",
        audit_required=True,
    ),
    exceptions_facade.NsRuntimeConfigApplyFailedError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.CONFIGURATION,
        "rollback_runtime_configuration",
        audit_required=True,
    ),
    exceptions_facade.NsRuntimeTransportError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.TRANSPORT,
        "handle_transport_failure",
    ),
    exceptions_facade.NsRuntimeTransportDisabledError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.TRANSPORT,
        "reject_disabled_transport",
        audit_required=True,
    ),
    exceptions_facade.NsRuntimeTransportHandshakeFailedError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.TRANSPORT,
        "close_failed_handshake",
        disconnect_required=True,
        audit_required=True,
    ),
    exceptions_facade.NsRuntimeTransportSendFailedError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.TRANSPORT,
        "retry_transport_send",
        retryable=True,
    ),
    exceptions_facade.NsRuntimeTransportReceiveFailedError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.TRANSPORT,
        "close_failed_transport_receive",
        disconnect_required=True,
    ),
    exceptions_facade.NsRuntimeTransportStreamResetError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.TRANSPORT,
        "retry_after_stream_reset",
        retryable=True,
    ),
    exceptions_facade.NsRuntimeTransportFlowControlBlockedError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.TRANSPORT,
        "wait_for_transport_capacity",
        retryable=True,
    ),
    exceptions_facade.NsRuntimeTransportPathMigrationFailedError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.TRANSPORT,
        "reconnect_after_path_failure",
        retryable=True,
    ),
    exceptions_facade.NsRuntimeTransportFallbackFailedError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.TRANSPORT,
        "report_transport_fallback_failure",
    ),
    exceptions_facade.NsRuntimeLeaderLeaseLostError: expected_policy(
        NsErrorSeverity.CRITICAL,
        NsErrorCategory.LEASE,
        "stop_leader_writes",
        audit_required=True,
    ),
    exceptions_facade.NsRuntimeClusterMemberUnavailableError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.CLUSTER,
        "retry_cluster_member",
        retryable=True,
    ),
    exceptions_facade.NsRuntimeClusterConfigDriftError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.CLUSTER,
        "isolate_config_drift",
        audit_required=True,
    ),
    exceptions_facade.NsRuntimeTenantPausedError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.TENANT,
        "wait_for_tenant_resume",
        retryable=True,
    ),
    exceptions_facade.NsRuntimeTransportCapabilityUnavailableError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.TRANSPORT,
        "reject_transport_capability",
    ),
    exceptions_facade.NsRuntimeDeliveryLeaseRejectedError: expected_policy(
        NsErrorSeverity.CRITICAL,
        NsErrorCategory.LEASE,
        "reject_delivery_lease",
        audit_required=True,
    ),
    exceptions_facade.NsRuntimeDependencyUnavailableError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.DEPENDENCY,
        "retry_runtime_dependency",
        retryable=True,
    ),
    exceptions_facade.NsRuntimeFeatureDisabledError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.RUNTIME,
        "reject_disabled_feature",
        audit_required=True,
    ),
    exceptions_facade.NsRuntimeStateStoreError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.STATE,
        "handle_state_store_failure",
    ),
    exceptions_facade.NsRuntimeStateStoreNotReadyError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.STATE,
        "reject_state_store_not_ready",
    ),
    exceptions_facade.NsRuntimeStateStoreClosedError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.STATE,
        "reject_closed_state_store",
    ),
    exceptions_facade.NsRuntimeStateStoreUnavailableError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.STATE,
        "probe_state_store_recovery",
        retryable=True,
    ),
    exceptions_facade.NsRuntimeStateStoreTimeoutError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.STATE,
        "handle_state_store_timeout",
    ),
    exceptions_facade.NsRuntimeStateStoreConflictError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.STATE,
        "reconcile_state_store_conflict",
    ),
    exceptions_facade.NsRuntimeStateStoreStaleReadError: expected_policy(
        NsErrorSeverity.WARNING,
        NsErrorCategory.STATE,
        "reject_stale_state_read",
    ),
    exceptions_facade.NsRuntimeStateStoreCapabilityUnavailableError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.STATE,
        "reject_state_store_capability",
    ),
    exceptions_facade.NsRuntimeStateStoreNamespaceViolationError: expected_policy(
        NsErrorSeverity.CRITICAL,
        NsErrorCategory.STATE,
        "reject_state_store_namespace",
        audit_required=True,
    ),
    exceptions_facade.NsRuntimeStateStoreVersionMismatchError: expected_policy(
        NsErrorSeverity.ERROR,
        NsErrorCategory.STATE,
        "reject_state_store_version",
    ),
    exceptions_facade.NsRuntimeStateStoreIndeterminateWriteError: expected_policy(
        NsErrorSeverity.CRITICAL,
        NsErrorCategory.STATE,
        "reconcile_indeterminate_write",
        audit_required=True,
    ),
}


def validate_fix_07_policy_invariants(
    definitions: dict[
        type[NsEvermoreError], NsErrorDefinition
    ] | None = None,
) -> None:
    expected = {
        exceptions_facade.NsRuntimeProcessorTimeoutError: (
            False,
            False,
            True,
            False,
            "isolate_processor_timeout",
        ),
        exceptions_facade.NsRuntimeProtocolParseError: (
            False,
            False,
            False,
            False,
            "reject_unparseable_message",
        ),
        exceptions_facade.NsRuntimeProtocolViolationError: (
            False,
            False,
            True,
            False,
            "reject_protocol_violation",
        ),
    }

    for error_type, expected_policy_values in expected.items():
        definition = (
            get_error_definition(error_type)
            if definitions is None
            else definitions.get(error_type)
        )
        if definition is None:
            raise ValueError(
                f"missing FIX-07 definition: {error_type.__name__}"
            )
        actual_policy_values = (
            definition.retryable,
            definition.disconnect_required,
            definition.audit_required,
            definition.safe_detail,
            definition.action,
        )
        if actual_policy_values != expected_policy_values:
            raise ValueError(
                f"FIX-07 policy mismatch: {error_type.__name__}"
            )


def make_definition(
    error_type: type[NsEvermoreError],
    **overrides: object,
) -> NsErrorDefinition:
    values: dict[str, object] = {
        "error_type": error_type,
        "code": error_type.code,
        "numeric_code": error_type.numeric_code,
        "severity": NsErrorSeverity.ERROR,
        "category": NsErrorCategory.COMMON,
        "retryable": False,
        "disconnect_required": False,
        "audit_required": False,
        "safe_detail": False,
        "action": "report_error",
    }
    values.update(overrides)
    return NsErrorDefinition(**values)  # type: ignore[arg-type]


class NsExceptionsPackageStructureTestCase(unittest.TestCase):

    def test_exceptions_is_package_with_required_structure(self) -> None:
        self.assertTrue(hasattr(exceptions_facade, "__path__"))
        self.assertEqual("__init__.py", Path(exceptions_facade.__file__).name)
        self.assertFalse(
            (PROJECT_ROOT / "src" / "ns_common" / "exceptions.py").exists()
        )

        expected_files = {
            "__init__.py",
            "base.py",
            "cluster.py",
            "common.py",
            "configuration.py",
            "delivery.py",
            "iam.py",
            "metadata.py",
            "nack.py",
            "payload_ref.py",
            "processor.py",
            "protocol.py",
            "registry.py",
            "routing.py",
            "transport.py",
            "state_store.py",
        }
        actual_files = {
            path.relative_to(EXCEPTIONS_PACKAGE).as_posix()
            for path in EXCEPTIONS_PACKAGE.rglob("*.py")
        }
        self.assertEqual(expected_files, actual_files)

    def test_facade_and_ns_common_preserve_authoritative_objects(self) -> None:
        for class_name in EXCEPTION_SNAPSHOTS:
            with self.subTest(class_name=class_name):
                error_type = getattr(exceptions_facade, class_name)
                self.assertIsInstance(error_type, type)
                self.assertIn(class_name, exceptions_facade.__all__)

        for symbol_name in TOP_LEVEL_EXCEPTION_EXPORTS:
            with self.subTest(symbol_name=symbol_name):
                self.assertIs(
                    getattr(ns_common, symbol_name),
                    getattr(exceptions_facade, symbol_name),
                )

        self.assertIs(
            ns_common.RUNTIME_NACK_REASON_ERROR_CODES,
            RUNTIME_NACK_REASON_ERROR_CODES,
        )

    def test_all_submodules_import_in_fresh_interpreter(self) -> None:
        source = "import importlib; " + "; ".join(
            f"importlib.import_module({module_name!r})"
            for module_name in reversed(EXCEPTION_SUBMODULES)
        )
        environment = os.environ.copy()
        src_path = str(PROJECT_ROOT / "src")
        environment["PYTHONPATH"] = os.pathsep.join(
            part
            for part in (src_path, environment.get("PYTHONPATH", ""))
            if part
        )
        completed = subprocess.run(
            [sys.executable, "-c", source],
            cwd=PROJECT_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_production_callers_only_import_exceptions_facade(self) -> None:
        violations: list[str] = []
        source_root = PROJECT_ROOT / "src"
        for source_path in source_root.rglob("*.py"):
            if EXCEPTIONS_PACKAGE in source_path.parents:
                continue
            source = source_path.read_text(encoding="utf-8")
            if "ns_common.exceptions." in source:
                violations.append(source_path.relative_to(PROJECT_ROOT).as_posix())
        self.assertEqual([], violations)

    def test_dependency_boundaries_do_not_create_cycles(self) -> None:
        base_source = (EXCEPTIONS_PACKAGE / "base.py").read_text(encoding="utf-8")
        metadata_source = (EXCEPTIONS_PACKAGE / "metadata.py").read_text(
            encoding="utf-8"
        )
        registry_source = (EXCEPTIONS_PACKAGE / "registry.py").read_text(
            encoding="utf-8"
        )
        all_source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in EXCEPTIONS_PACKAGE.glob("*.py")
        )

        for forbidden in ("registry", "security", "logger", "config"):
            self.assertNotIn(forbidden, base_source)
        for domain_module in (
            ".common",
            ".configuration",
            ".protocol",
            ".iam",
            ".routing",
            ".payload_ref",
            ".delivery",
            ".processor",
            ".transport",
            ".cluster",
            ".state_store",
        ):
            self.assertNotIn(domain_module, metadata_source)
        for forbidden in ("__subclasses__", "sys.modules", "importlib"):
            self.assertNotIn(forbidden, registry_source)
        for forbidden_import in (
            "ns_common.security",
            "ns_common.logger",
            "ns_common.config",
            "from ..security",
            "from ..logger",
            "from ..config",
        ):
            self.assertNotIn(forbidden_import, all_source)


class NsExceptionCompatibilityTestCase(unittest.TestCase):

    def test_class_metadata_and_inheritance_match_legacy_contract(self) -> None:
        self.assertEqual(84, len(EXCEPTION_SNAPSHOTS))
        for class_name, snapshot in EXCEPTION_SNAPSHOTS.items():
            with self.subTest(class_name=class_name):
                base_name, code, numeric_code, default_message = snapshot
                error_type = getattr(exceptions_facade, class_name)
                self.assertEqual(base_name, error_type.__bases__[0].__name__)
                self.assertEqual(code, error_type.code)
                self.assertEqual(numeric_code, error_type.numeric_code)
                self.assertEqual(default_message, error_type.default_message)

    def test_constructor_signature_and_behavior_remain_compatible(self) -> None:
        expected_parameters = (
            "message",
            "code",
            "numeric_code",
            "details",
        )
        for class_name, snapshot in EXCEPTION_SNAPSHOTS.items():
            with self.subTest(class_name=class_name):
                error_type = getattr(exceptions_facade, class_name)
                signature = inspect.signature(error_type)
                self.assertEqual(expected_parameters, tuple(signature.parameters))
                self.assertIsNone(signature.parameters["message"].default)
                for parameter_name in expected_parameters[1:]:
                    parameter = signature.parameters[parameter_name]
                    self.assertIsNone(parameter.default)
                    self.assertIs(
                        inspect.Parameter.KEYWORD_ONLY,
                        parameter.kind,
                    )

                default_error = error_type()
                self.assertEqual(snapshot[1], default_error.code)
                self.assertEqual(snapshot[2], default_error.numeric_code)
                self.assertEqual(snapshot[3], default_error.message)
                self.assertEqual({}, default_error.details)
                self.assertEqual(
                    {
                        "code": snapshot[1],
                        "numeric_code": snapshot[2],
                        "message": snapshot[3],
                        "details": {},
                    },
                    default_error.to_dict(),
                )

                custom_error = error_type(
                    "custom message",
                    code="CUSTOM_CODE",
                    numeric_code=900001,
                    details={"field": "value"},
                )
                self.assertEqual("custom message", custom_error.message)
                self.assertEqual("CUSTOM_CODE", custom_error.code)
                self.assertEqual(900001, custom_error.numeric_code)
                self.assertEqual({"field": "value"}, custom_error.details)

    def test_details_to_dict_and_string_behavior_remain_compatible(self) -> None:
        nested = {"item": "value"}
        original_details = {"field": "input", "nested": nested}
        error = NsValidationError("bad input", details=original_details)
        original_details["field"] = "changed"

        self.assertEqual("input", error.details["field"])
        self.assertIs(nested, error.details["nested"])
        self.assertEqual(
            {
                "code": "NS_VALIDATION_ERROR",
                "numeric_code": 100200,
                "message": "bad input",
                "details": {"field": "input", "nested": nested},
            },
            error.to_dict(),
        )
        self.assertEqual(
            "[NS_VALIDATION_ERROR/100200] bad input "
            "details={'field': 'input', 'nested': {'item': 'value'}}",
            str(error),
        )
        self.assertEqual(
            "[NS_VALIDATION_ERROR/100200] Validation failed.",
            str(NsValidationError()),
        )

    def test_falsy_override_behavior_is_not_changed(self) -> None:
        error = NsValidationError(
            "",
            code="",
            numeric_code=0,
            details={},
        )
        self.assertEqual(NsValidationError.default_message, error.message)
        self.assertEqual(NsValidationError.code, error.code)
        self.assertEqual(NsValidationError.numeric_code, error.numeric_code)

    def test_existing_catch_relationships_remain_compatible(self) -> None:
        runtime_error = NsRuntimePayloadRefValidationTimeoutError()
        self.assertIsInstance(runtime_error, NsRuntimeError)
        self.assertIsInstance(
            runtime_error,
            NsRuntimePayloadRefValidationUnavailableError,
        )
        startup_error = NsRuntimeStartupSecurityError()
        self.assertIsInstance(startup_error, NsConfigError)
        self.assertNotIsInstance(startup_error, NsRuntimeError)


class NsErrorMetadataRegistryTestCase(unittest.TestCase):

    def test_all_current_error_policies_match_explicit_matrix(self) -> None:
        self.assertEqual(84, len(EXPECTED_ERROR_POLICIES))
        self.assertEqual(
            set(EXPECTED_ERROR_POLICIES),
            {definition.error_type for definition in ALL_ERROR_DEFINITIONS},
        )
        for error_type, expected in EXPECTED_ERROR_POLICIES.items():
            with self.subTest(error_type=error_type.__name__):
                definition = get_error_definition(error_type)
                self.assertIsNotNone(definition)
                assert definition is not None
                actual = {
                    "severity": definition.severity,
                    "category": definition.category,
                    "retryable": definition.retryable,
                    "disconnect_required": definition.disconnect_required,
                    "audit_required": definition.audit_required,
                    "safe_detail": definition.safe_detail,
                    "action": definition.action,
                }
                self.assertEqual(expected, actual)

    def test_general_error_types_have_conservative_side_effect_policy(self) -> None:
        general_error_types = (
            exceptions_facade.NsEvermoreError,
            exceptions_facade.NsRuntimeError,
            exceptions_facade.NsDependencyError,
            exceptions_facade.NsStateError,
            exceptions_facade.NsHttpClientError,
            exceptions_facade.NsRuntimeProtocolError,
            exceptions_facade.NsRuntimeTransportError,
            exceptions_facade.NsRuntimeClusterCoordinationError,
            exceptions_facade.NsRuntimeStateStoreError,
        )
        for error_type in general_error_types:
            with self.subTest(error_type=error_type.__name__):
                definition = get_error_definition(error_type)
                self.assertIsNotNone(definition)
                assert definition is not None
                self.assertFalse(definition.retryable)
                self.assertFalse(definition.disconnect_required)
                self.assertFalse(definition.audit_required)
                self.assertFalse(definition.safe_detail)

    def test_explicit_leaf_error_policies_remain_strong(self) -> None:
        retryable_types = (
            exceptions_facade.NsRuntimePayloadRefValidationUnavailableError,
            exceptions_facade.NsRuntimePayloadRefValidationTimeoutError,
            exceptions_facade.NsRuntimeTargetUnavailableError,
            exceptions_facade.NsRuntimeBackpressureError,
            exceptions_facade.NsRuntimeAckTimeoutError,
            exceptions_facade.NsRuntimeDeferBudgetExceededError,
            exceptions_facade.NsRuntimeDependencyUnavailableError,
            exceptions_facade.NsRuntimeDeliveryLeaseExpiredError,
            exceptions_facade.NsRuntimeDeliveryLeaseRenewFailedError,
            exceptions_facade.NsRuntimeIamUnavailableError,
            exceptions_facade.NsRuntimeIamTimeoutError,
            exceptions_facade.NsRuntimeRouteUnavailableError,
            exceptions_facade.NsRuntimeTenantPausedError,
            exceptions_facade.NsRuntimeTenantQuotaExceededError,
            exceptions_facade.NsRuntimeTransportFlowControlBlockedError,
            exceptions_facade.NsRuntimeTransportPathMigrationFailedError,
            exceptions_facade.NsRuntimeTransportSendFailedError,
            exceptions_facade.NsRuntimeTransportStreamResetError,
            exceptions_facade.NsRuntimeClusterMemberUnavailableError,
        )
        for error_type in retryable_types:
            with self.subTest(error_type=error_type.__name__):
                definition = get_error_definition(error_type)
                self.assertIsNotNone(definition)
                assert definition is not None
                self.assertTrue(definition.retryable)

        security_flags = {
            exceptions_facade.NsRuntimeSourceForgedError: (True, True),
            exceptions_facade.NsRuntimeAuthContextForgedError: (True, True),
            exceptions_facade.NsRuntimeTenantMismatchError: (True, True),
            exceptions_facade.NsRuntimeClusterFencingError: (True, True),
            exceptions_facade.NsRuntimeFencingRejectedError: (True, True),
            exceptions_facade.NsRuntimeStartupSecurityError: (False, True),
        }
        for error_type, expected_flags in security_flags.items():
            with self.subTest(error_type=error_type.__name__):
                definition = get_error_definition(error_type)
                self.assertIsNotNone(definition)
                assert definition is not None
                self.assertEqual(
                    expected_flags,
                    (
                        definition.disconnect_required,
                        definition.audit_required,
                    ),
                )

    def test_fix_07_policy_invariants_reject_unsafe_regressions(self) -> None:
        validate_fix_07_policy_invariants()
        definitions = {
            error_type: get_error_definition(error_type)
            for error_type in (
                exceptions_facade.NsRuntimeProcessorTimeoutError,
                exceptions_facade.NsRuntimeProtocolParseError,
                exceptions_facade.NsRuntimeProtocolViolationError,
            )
        }
        self.assertTrue(all(definitions.values()))
        checked_definitions = {
            error_type: definition
            for error_type, definition in definitions.items()
            if definition is not None
        }

        processor_type = exceptions_facade.NsRuntimeProcessorTimeoutError
        retryable_timeout = dict(checked_definitions)
        retryable_timeout[processor_type] = replace(
            checked_definitions[processor_type],
            retryable=True,
        )
        with self.assertRaisesRegex(ValueError, "ProcessorTimeout"):
            validate_fix_07_policy_invariants(retryable_timeout)

        parse_type = exceptions_facade.NsRuntimeProtocolParseError
        disconnecting_parse = dict(checked_definitions)
        disconnecting_parse[parse_type] = replace(
            checked_definitions[parse_type],
            disconnect_required=True,
        )
        with self.assertRaisesRegex(ValueError, "ProtocolParse"):
            validate_fix_07_policy_invariants(disconnecting_parse)

    def test_current_dependency_scenarios_use_conservative_definition(self) -> None:
        config = NsRuntimeEventLoopConfig(
            implementation="uvloop",
            metadata=NsConfigGroupMetadata(apply_mode="restart_required"),
        )

        with self.assertRaises(NsDependencyError) as windows_context:
            NsEventLoopSelector(
                platform_system=lambda: "Windows",
            ).select(config)

        def broken_policy_factory() -> object:
            raise RuntimeError("broken uvloop policy")

        fake_uvloop = types.SimpleNamespace(
            EventLoopPolicy=broken_policy_factory,
        )
        with self.assertRaises(NsDependencyError) as init_context:
            NsEventLoopSelector(
                platform_system=lambda: "Linux",
                module_loader=lambda _: fake_uvloop,
            ).install(config)

        response = NsHttpResponse(
            status_code=200,
            headers={},
            text="{invalid-json",
            url="https://example.invalid/data",
            method="GET",
        )
        with self.assertRaises(NsDependencyError) as json_context:
            response.json()

        for error in (
            windows_context.exception,
            init_context.exception,
            json_context.exception,
        ):
            with self.subTest(message=error.message):
                definition = get_error_definition(type(error))
                self.assertIsNotNone(definition)
                assert definition is not None
                self.assertFalse(definition.retryable)
                self.assertEqual("inspect_dependency", definition.action)

        broad_expectations = {
            NsHttpClientError: "handle_http_failure",
            exceptions_facade.NsRuntimeProtocolError: "reject_protocol_message",
            exceptions_facade.NsRuntimeClusterCoordinationError: (
                "investigate_cluster_coordination"
            ),
        }
        for error_type, action in broad_expectations.items():
            with self.subTest(error_type=error_type.__name__):
                definition = get_error_definition(type(error_type()))
                self.assertIsNotNone(definition)
                assert definition is not None
                self.assertFalse(definition.retryable)
                self.assertFalse(definition.disconnect_required)
                self.assertEqual(action, definition.action)

        for error_type in (
            exceptions_facade.NsRuntimeSourceForgedError,
            exceptions_facade.NsRuntimeAuthContextForgedError,
            exceptions_facade.NsRuntimeClusterFencingError,
        ):
            with self.subTest(error_type=error_type.__name__):
                definition = get_error_definition(type(error_type()))
                self.assertIsNotNone(definition)
                assert definition is not None
                self.assertTrue(definition.disconnect_required)
                self.assertTrue(definition.audit_required)

    def test_error_type_lookup_does_not_fall_back_through_mro(self) -> None:
        class UnregisteredDependencyError(NsDependencyError):
            pass

        error = UnregisteredDependencyError()
        self.assertIsNone(get_error_definition(type(error)))
        self.assertIsNone(ERROR_REGISTRY.get_by_error_type(type(error)))
        self.assertIsNotNone(get_error_definition(NsDependencyError))

    def test_definition_validation_is_strict(self) -> None:
        valid = make_definition(NsValidationError)
        self.assertEqual("NS_VALIDATION_ERROR", valid.code)
        with self.assertRaises(TypeError):
            NsErrorDefinition.for_error_type(
                object,  # type: ignore[arg-type]
                severity=NsErrorSeverity.ERROR,
                category=NsErrorCategory.COMMON,
                action="report_error",
            )

        invalid_values = (
            {"error_type": object},
            {"code": ""},
            {"code": "OTHER_CODE"},
            {"numeric_code": True},
            {"numeric_code": 0},
            {"numeric_code": 900002},
            {"severity": "error"},
            {"category": "common"},
            {"retryable": 1},
            {"disconnect_required": None},
            {"audit_required": "false"},
            {"safe_detail": 0},
            {"action": ""},
            {"action": "Retry Error"},
        )
        for overrides in invalid_values:
            with self.subTest(overrides=overrides):
                with self.assertRaises((TypeError, ValueError)):
                    make_definition(NsValidationError, **overrides)

    def test_registry_is_complete_unique_queryable_and_json_safe(self) -> None:
        definitions = list_error_definitions()
        self.assertIs(ALL_ERROR_DEFINITIONS, definitions)
        self.assertEqual(84, len(definitions))
        self.assertEqual(84, len({item.error_type for item in definitions}))
        self.assertEqual(84, len({item.code for item in definitions}))
        self.assertEqual(84, len({item.numeric_code for item in definitions}))

        validate_error_registry()
        for definition in definitions:
            with self.subTest(code=definition.code):
                self.assertIs(
                    definition,
                    get_error_definition(definition.error_type),
                )
                self.assertIs(
                    definition,
                    get_error_definition_by_code(definition.code),
                )
                self.assertIs(
                    definition,
                    get_error_definition_by_numeric_code(
                        definition.numeric_code
                    ),
                )
                self.assertEqual(definition.code, definition.error_type.code)
                self.assertEqual(
                    definition.numeric_code,
                    definition.error_type.numeric_code,
                )
                self.assertIsInstance(definition.severity, NsErrorSeverity)
                self.assertIsInstance(definition.category, NsErrorCategory)

        self.assertIsNone(get_error_definition(type("UnknownError", (NsEvermoreError,), {})))
        self.assertIsNone(get_error_definition_by_code("UNKNOWN"))
        self.assertIsNone(get_error_definition_by_numeric_code(999999))
        json.dumps(ERROR_REGISTRY.to_dict(), allow_nan=False)

    def test_runtime_error_coverage_matrix_is_complete_and_validated(self) -> None:
        self.assertEqual(20, len(RUNTIME_ERROR_COVERAGE_MATRIX))
        validated = validate_runtime_error_coverage_matrix()
        self.assertIs(RUNTIME_ERROR_COVERAGE_MATRIX, validated)

        covered_codes = tuple(
            code
            for _, codes in RUNTIME_ERROR_COVERAGE_MATRIX
            for code in codes
        )
        registered_runtime_codes = {
            definition.code
            for definition in ALL_ERROR_DEFINITIONS
            if definition.code.startswith("RUNTIME_")
        }
        self.assertEqual(77, len(covered_codes))
        self.assertEqual(registered_runtime_codes, set(covered_codes))
        self.assertEqual(len(covered_codes), len(set(covered_codes)))

        invalid_matrices = (
            (("", ("RUNTIME_PROTOCOL_ERROR",)),),
            (("protocol", ()),),
            (("protocol", ("NS_ERROR",)),),
            (("protocol", ("RUNTIME_UNKNOWN",)),),
            (
                ("protocol", ("RUNTIME_PROTOCOL_ERROR",)),
                ("protocol", ("RUNTIME_PROTOCOL_PARSE_ERROR",)),
            ),
            (
                (
                    "protocol",
                    (
                        "RUNTIME_PROTOCOL_ERROR",
                        "RUNTIME_PROTOCOL_ERROR",
                    ),
                ),
            ),
        )
        for matrix in invalid_matrices:
            with self.subTest(matrix=matrix):
                with self.assertRaises((TypeError, ValueError)):
                    validate_runtime_error_coverage_matrix(matrix)

        missing_violation_matrix = tuple(
            (
                area,
                tuple(
                    code
                    for code in codes
                    if code != "RUNTIME_PROTOCOL_VIOLATION"
                ),
            )
            for area, codes in RUNTIME_ERROR_COVERAGE_MATRIX
        )
        with self.assertRaisesRegex(ValueError, "PROTOCOL_VIOLATION"):
            validate_runtime_error_coverage_matrix(missing_violation_matrix)

    def test_required_runtime_error_scenarios_are_independent_and_complete(
        self,
    ) -> None:
        self.assertEqual(20, len(REQUIRED_RUNTIME_ERROR_SCENARIOS))
        self.assertEqual(
            len(REQUIRED_RUNTIME_ERROR_SCENARIOS),
            len(set(REQUIRED_RUNTIME_ERROR_SCENARIOS)),
        )
        self.assertEqual(
            len(REQUIRED_RUNTIME_ERROR_SCENARIOS),
            len(set(REQUIRED_RUNTIME_ERROR_SCENARIOS.values())),
        )
        self.assertIs(
            REQUIRED_RUNTIME_ERROR_SCENARIOS,
            validate_required_runtime_error_scenarios(),
        )

        unregistered = dict(REQUIRED_RUNTIME_ERROR_SCENARIOS)
        unregistered["protocol_violation"] = "RUNTIME_UNKNOWN_SCENARIO"
        with self.assertRaisesRegex(ValueError, "not registered"):
            validate_required_runtime_error_scenarios(unregistered)

        missing_violation_matrix = tuple(
            (
                area,
                tuple(
                    code
                    for code in codes
                    if code != "RUNTIME_PROTOCOL_VIOLATION"
                ),
            )
            for area, codes in RUNTIME_ERROR_COVERAGE_MATRIX
        )
        with self.assertRaisesRegex(ValueError, "not covered"):
            validate_required_runtime_error_scenarios(
                coverage_matrix=missing_violation_matrix
            )

        duplicate_code = dict(REQUIRED_RUNTIME_ERROR_SCENARIOS)
        duplicate_code["protocol_parse"] = "RUNTIME_PROTOCOL_VIOLATION"
        with self.assertRaisesRegex(ValueError, "codes must be unique"):
            validate_required_runtime_error_scenarios(duplicate_code)

    def test_every_public_exception_class_has_one_definition(self) -> None:
        registered_types = {definition.error_type for definition in ALL_ERROR_DEFINITIONS}
        public_error_types = {
            getattr(exceptions_facade, name)
            for name in exceptions_facade.__all__
            if name.startswith("Ns")
            and isinstance(getattr(exceptions_facade, name), type)
            and issubclass(getattr(exceptions_facade, name), NsEvermoreError)
        }
        self.assertEqual(
            {getattr(exceptions_facade, name) for name in EXCEPTION_SNAPSHOTS},
            public_error_types,
        )
        self.assertEqual(public_error_types, registered_types)

    def test_registry_rejects_duplicate_class_code_and_numeric_code(self) -> None:
        validation_definition = make_definition(NsValidationError)
        with self.assertRaisesRegex(ValueError, "duplicate error type"):
            NsErrorRegistry((validation_definition, validation_definition))

        class DuplicateCodeError(NsEvermoreError):
            code = NsValidationError.code
            numeric_code = 900010

        duplicate_code_definition = make_definition(DuplicateCodeError)
        with self.assertRaisesRegex(ValueError, "duplicate error code"):
            NsErrorRegistry((validation_definition, duplicate_code_definition))

        class DuplicateNumericCodeError(NsEvermoreError):
            code = "DUPLICATE_NUMERIC_CODE"
            numeric_code = NsValidationError.numeric_code

        duplicate_numeric_definition = make_definition(DuplicateNumericCodeError)
        with self.assertRaisesRegex(ValueError, "duplicate numeric error code"):
            NsErrorRegistry((validation_definition, duplicate_numeric_definition))

        with self.assertRaises(TypeError):
            NsErrorRegistry((object(),))  # type: ignore[arg-type]

    def test_registry_and_definitions_are_immutable(self) -> None:
        definition = get_error_definition(NsValidationError)
        self.assertIsNotNone(definition)
        assert definition is not None
        with self.assertRaises(FrozenInstanceError):
            definition.action = "mutate"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            ERROR_REGISTRY._definitions = ()  # type: ignore[misc]
        with self.assertRaises(TypeError):
            ERROR_REGISTRY._by_code["OTHER"] = definition  # type: ignore[index]

    def test_registry_validation_detects_later_class_metadata_drift(self) -> None:
        class MutableMetadataError(NsEvermoreError):
            code = "MUTABLE_METADATA"
            numeric_code = 900020

        definition = make_definition(MutableMetadataError)
        registry = NsErrorRegistry((definition,))
        MutableMetadataError.code = "CHANGED_METADATA"
        with self.assertRaisesRegex(ValueError, "current error_type.code"):
            registry.validate()

    def test_registry_metadata_never_serializes_error_details_or_string(self) -> None:
        secret = "registry-detail-secret"

        class ExplodingStringError(NsEvermoreError):
            def __str__(self) -> str:
                raise RuntimeError("registry-string-secret")

        error = ExplodingStringError(details={"secret": secret})
        self.assertIsNone(get_error_definition(type(error)))
        serialized = json.dumps(ERROR_REGISTRY.to_dict(), allow_nan=False)
        self.assertNotIn(secret, serialized)
        self.assertNotIn("registry-string-secret", serialized)

    def test_nack_mapping_is_stable_complete_and_validated(self) -> None:
        expected_mapping = (
            ("target_overloaded", "RUNTIME_BACKPRESSURE"),
            ("temporarily_unavailable", "RUNTIME_TARGET_UNAVAILABLE"),
            ("queue_full", "RUNTIME_BACKPRESSURE"),
            ("dependency_unavailable", "RUNTIME_DEPENDENCY_UNAVAILABLE"),
            ("target_draining", "RUNTIME_TARGET_UNAVAILABLE"),
            ("node_degraded", "RUNTIME_CLUSTER_MEMBER_UNAVAILABLE"),
            ("permission_denied", "RUNTIME_IAM_DENIED"),
            ("tenant_mismatch", "RUNTIME_TENANT_MISMATCH"),
            ("invalid_payload_ref", "RUNTIME_PAYLOAD_REF_INVALID"),
            ("payload_ref_denied", "RUNTIME_PAYLOAD_REF_DENIED"),
            ("source_forged", "RUNTIME_SOURCE_FORGED"),
            ("auth_context_forged", "RUNTIME_AUTH_CONTEXT_FORGED"),
            ("protocol_violation", "RUNTIME_PROTOCOL_VIOLATION"),
        )
        self.assertEqual(expected_mapping, RUNTIME_NACK_REASON_ERROR_CODES)
        self.assertEqual(
            len(RUNTIME_NACK_REASON_ERROR_CODES),
            len({reason for reason, _ in RUNTIME_NACK_REASON_ERROR_CODES}),
        )
        self.assertIs(
            RUNTIME_NACK_REASON_ERROR_CODES,
            validate_runtime_nack_reason_error_codes(),
        )
        for _, code in RUNTIME_NACK_REASON_ERROR_CODES:
            self.assertTrue(code.startswith("RUNTIME_"))
            self.assertIsNotNone(get_error_definition_by_code(code))

        invalid_mappings = (
            (("", NsValidationError.code),),
            (("duplicate", NsValidationError.code), ("duplicate", NsConfigError.code)),
            (("unknown", "UNREGISTERED_CODE"),),
            (("missing_code", ""),),
        )
        for entries in invalid_mappings:
            with self.subTest(entries=entries):
                with self.assertRaises((TypeError, ValueError)):
                    validate_runtime_nack_reason_error_codes(entries)

        broad_protocol_mapping = (
            *RUNTIME_NACK_REASON_ERROR_CODES[:-1],
            ("protocol_violation", "RUNTIME_PROTOCOL_ERROR"),
        )
        with self.assertRaisesRegex(ValueError, "PROTOCOL_VIOLATION"):
            validate_runtime_nack_reason_error_codes(broad_protocol_mapping)


if __name__ == "__main__":
    unittest.main()
