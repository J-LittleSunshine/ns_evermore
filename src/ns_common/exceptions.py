# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    Mapping,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    pass


class NsEvermoreError(Exception):
    code: str = "NS_ERROR"
    numeric_code: int = 100000
    default_message: str = "NsEvermore error."

    def __init__(self, message: str | None = None, *, code: str | None = None, numeric_code: int | None = None, details: Mapping[str, Any] | None = None) -> None:
        self.message: str = message or self.default_message
        self.code: str = code or self.code
        self.numeric_code: int = numeric_code or self.numeric_code
        self.details: dict[str, Any] = dict(details or {})

        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "numeric_code": self.numeric_code,
            "message": self.message,
            "details": self.details,
        }

    def __str__(self) -> str:
        if not self.details:
            return f"[{self.code}/{self.numeric_code}] {self.message}"

        return f"[{self.code}/{self.numeric_code}] {self.message} details={self.details}"


class NsConfigError(NsEvermoreError):
    code = "NS_CONFIG_ERROR"
    numeric_code = 100100
    default_message = "Invalid ns_evermore configuration."


class NsValidationError(NsEvermoreError):
    code = "NS_VALIDATION_ERROR"
    numeric_code = 100200
    default_message = "Validation failed."


class NsRuntimeError(NsEvermoreError):
    code = "NS_RUNTIME_ERROR"
    numeric_code = 100300
    default_message = "NsEvermore runtime error."


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


class NsRuntimeProtocolError(NsRuntimeError):
    code = "RUNTIME_PROTOCOL_ERROR"
    numeric_code = 200100
    default_message = "Runtime protocol error."


class NsRuntimeEnvelopeSchemaError(NsRuntimeProtocolError):
    code = "RUNTIME_ENVELOPE_SCHEMA_ERROR"
    numeric_code = 200101
    default_message = "Runtime envelope schema error."


class NsRuntimeProtocolVersionError(NsRuntimeProtocolError):
    code = "RUNTIME_PROTOCOL_VERSION_ERROR"
    numeric_code = 200102
    default_message = "Runtime protocol version is incompatible."


class NsRuntimeSourceForgedError(NsRuntimeProtocolError):
    code = "RUNTIME_SOURCE_FORGED"
    numeric_code = 200103
    default_message = "Inbound envelope must not contain source."


class NsRuntimeAuthContextForgedError(NsRuntimeProtocolError):
    code = "RUNTIME_AUTH_CONTEXT_FORGED"
    numeric_code = 200104
    default_message = "Inbound envelope must not contain auth_context."


class NsRuntimeUnsupportedMessageTypeError(NsRuntimeProtocolError):
    code = "RUNTIME_UNSUPPORTED_MESSAGE_TYPE"
    numeric_code = 200105
    default_message = "Runtime message type is not registered."


class NsRuntimeUnauthorizedMessageTypeError(NsRuntimeProtocolError):
    code = "RUNTIME_UNAUTHORIZED_MESSAGE_TYPE"
    numeric_code = 200106
    default_message = "Runtime message type is not allowed by current capability."


class NsRuntimeTenantMismatchError(NsRuntimeProtocolError):
    code = "RUNTIME_TENANT_MISMATCH"
    numeric_code = 200107
    default_message = "Runtime tenant boundary is violated."


class NsRuntimePayloadRefDeniedError(NsRuntimeProtocolError):
    code = "RUNTIME_PAYLOAD_REF_DENIED"
    numeric_code = 200108
    default_message = "Runtime payload reference is denied."


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


class NsRuntimeClusterCoordinationError(NsRuntimeError):
    code = "RUNTIME_CLUSTER_COORDINATION_ERROR"
    numeric_code = 200115
    default_message = "Runtime cluster coordination error."


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
    default_message = (
        "Runtime payload reference checksum does not match."
    )


class NsRuntimePayloadRefVersionMismatchError(NsRuntimeProtocolError):
    code = "RUNTIME_PAYLOAD_REF_VERSION_MISMATCH"
    numeric_code = 200119
    default_message = (
        "Runtime payload reference version does not match."
    )


class NsRuntimePayloadRefValidationUnavailableError(NsRuntimeError):
    code = "RUNTIME_PAYLOAD_REF_VALIDATION_UNAVAILABLE"
    numeric_code = 200120
    default_message = (
        "Runtime payload reference validation is unavailable."
    )


class NsRuntimePayloadRefValidationTimeoutError(NsRuntimePayloadRefValidationUnavailableError):
    code = "RUNTIME_PAYLOAD_REF_VALIDATION_TIMEOUT"
    numeric_code = 200121
    default_message = (
        "Runtime payload reference validation timed out."
    )

class NsRuntimeClusterStateError(NsRuntimeClusterCoordinationError):
    code = "RUNTIME_CLUSTER_STATE_ERROR"
    numeric_code = 200122
    default_message = (
        "Runtime cluster state transition is invalid."
    )


class NsRuntimeClusterFencingError(NsRuntimeClusterCoordinationError):
    code = "RUNTIME_CLUSTER_FENCING_ERROR"
    numeric_code = 200123
    default_message = (
        "Runtime cluster fencing validation failed."
    )

RUNTIME_NACK_REASON_ERROR_CODES: tuple[tuple[str, str], ...] = (
    ("target_overloaded", NsRuntimeBackpressureError.code),
    ("temporarily_unavailable", NsRuntimeTargetUnavailableError.code),
    ("queue_full", NsRuntimeBackpressureError.code),
    ("dependency_unavailable", NsDependencyError.code),
    ("target_draining", NsRuntimeTargetUnavailableError.code),
    ("node_degraded", NsRuntimeClusterCoordinationError.code),
    ("permission_denied", NsRuntimeUnauthorizedMessageTypeError.code),
    ("tenant_mismatch", NsRuntimeTenantMismatchError.code),
    ("invalid_payload_ref", NsRuntimePayloadRefDeniedError.code),
    ("payload_ref_denied", NsRuntimePayloadRefDeniedError.code),
    ("source_forged", NsRuntimeSourceForgedError.code),
    ("auth_context_forged", NsRuntimeAuthContextForgedError.code),
    ("protocol_violation", NsRuntimeProtocolError.code),
)
