# -*- coding: utf-8 -*-
from __future__ import annotations

from collections.abc import Iterable

from .cluster import NsRuntimeClusterCoordinationError
from .common import NsDependencyError
from .delivery import (
    NsRuntimeBackpressureError,
    NsRuntimeTargetUnavailableError,
)
from .payload_ref import NsRuntimePayloadRefDeniedError
from .protocol import (
    NsRuntimeAuthContextForgedError,
    NsRuntimeProtocolError,
    NsRuntimeSourceForgedError,
    NsRuntimeTenantMismatchError,
    NsRuntimeUnauthorizedMessageTypeError,
)
from .registry import ERROR_REGISTRY


def validate_runtime_nack_reason_error_codes(
    entries: Iterable[tuple[str, str]] | None = None,
) -> tuple[tuple[str, str], ...]:
    if entries is None:
        entries = RUNTIME_NACK_REASON_ERROR_CODES
    normalized_entries = tuple(entries)
    seen_reasons: set[str] = set()

    for entry in normalized_entries:
        if not isinstance(entry, tuple) or len(entry) != 2:
            raise TypeError("NACK mapping entries must be (reason, code) tuples")
        reason, code = entry
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("NACK reason must be a non-empty string")
        if reason in seen_reasons:
            raise ValueError(f"duplicate NACK reason: {reason}")
        if not isinstance(code, str) or not code.strip():
            raise ValueError("NACK error code must be a non-empty string")
        if ERROR_REGISTRY.get_by_code(code) is None:
            raise ValueError(f"unregistered NACK error code: {code}")
        seen_reasons.add(reason)

    return normalized_entries


RUNTIME_NACK_REASON_ERROR_CODES: tuple[tuple[str, str], ...] = (
    validate_runtime_nack_reason_error_codes(
        (
            ("target_overloaded", NsRuntimeBackpressureError.code),
            ("temporarily_unavailable", NsRuntimeTargetUnavailableError.code),
            ("queue_full", NsRuntimeBackpressureError.code),
            ("dependency_unavailable", NsDependencyError.code),
            ("target_draining", NsRuntimeTargetUnavailableError.code),
            ("node_degraded", NsRuntimeClusterCoordinationError.code),
            (
                "permission_denied",
                NsRuntimeUnauthorizedMessageTypeError.code,
            ),
            ("tenant_mismatch", NsRuntimeTenantMismatchError.code),
            ("invalid_payload_ref", NsRuntimePayloadRefDeniedError.code),
            ("payload_ref_denied", NsRuntimePayloadRefDeniedError.code),
            ("source_forged", NsRuntimeSourceForgedError.code),
            (
                "auth_context_forged",
                NsRuntimeAuthContextForgedError.code,
            ),
            ("protocol_violation", NsRuntimeProtocolError.code),
        )
    )
)
