# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Iterable, Mapping

from .base import NsEvermoreError
from .cluster import CLUSTER_ERROR_DEFINITIONS
from .common import COMMON_ERROR_DEFINITIONS
from .configuration import CONFIGURATION_ERROR_DEFINITIONS
from .delivery import DELIVERY_ERROR_DEFINITIONS
from .iam import IAM_ERROR_DEFINITIONS
from .metadata import NsErrorDefinition
from .payload_ref import PAYLOAD_REF_ERROR_DEFINITIONS
from .processor import PROCESSOR_ERROR_DEFINITIONS
from .protocol import PROTOCOL_ERROR_DEFINITIONS
from .routing import ROUTING_ERROR_DEFINITIONS
from .state_store import STATE_STORE_ERROR_DEFINITIONS
from .transport import TRANSPORT_ERROR_DEFINITIONS


ALL_ERROR_DEFINITIONS: tuple[NsErrorDefinition, ...] = (
    *COMMON_ERROR_DEFINITIONS,
    *PROTOCOL_ERROR_DEFINITIONS,
    *IAM_ERROR_DEFINITIONS,
    *ROUTING_ERROR_DEFINITIONS,
    *PAYLOAD_REF_ERROR_DEFINITIONS,
    *DELIVERY_ERROR_DEFINITIONS,
    *PROCESSOR_ERROR_DEFINITIONS,
    *CONFIGURATION_ERROR_DEFINITIONS,
    *TRANSPORT_ERROR_DEFINITIONS,
    *CLUSTER_ERROR_DEFINITIONS,
    *STATE_STORE_ERROR_DEFINITIONS,
)


RUNTIME_ERROR_COVERAGE_MATRIX: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "runtime",
        (
            "RUNTIME_FEATURE_DISABLED",
        ),
    ),
    (
        "protocol",
        (
            "RUNTIME_PROTOCOL_ERROR",
            "RUNTIME_PROTOCOL_PARSE_ERROR",
            "RUNTIME_PROTOCOL_VIOLATION",
            "RUNTIME_ENVELOPE_SCHEMA_ERROR",
            "RUNTIME_PROTOCOL_VERSION_ERROR",
            "RUNTIME_SOURCE_FORGED",
            "RUNTIME_AUTH_CONTEXT_FORGED",
            "RUNTIME_UNSUPPORTED_MESSAGE_TYPE",
            "RUNTIME_UNAUTHORIZED_MESSAGE_TYPE",
        ),
    ),
    (
        "iam",
        (
            "RUNTIME_IAM_DENIED",
            "RUNTIME_IAM_UNAVAILABLE",
            "RUNTIME_IAM_TIMEOUT",
        ),
    ),
    (
        "dependency",
        (
            "RUNTIME_DEPENDENCY_UNAVAILABLE",
        ),
    ),
    (
        "tenant",
        (
            "RUNTIME_TENANT_MISMATCH",
            "RUNTIME_TENANT_QUOTA_EXCEEDED",
            "RUNTIME_TENANT_PAUSED",
        ),
    ),
    (
        "target",
        (
            "RUNTIME_TARGET_NOT_FOUND",
            "RUNTIME_TARGET_UNAVAILABLE",
        ),
    ),
    (
        "route",
        (
            "RUNTIME_ROUTE_UNAVAILABLE",
            "RUNTIME_ROUTE_LOOP",
            "RUNTIME_ROUTE_HOP_LIMIT_EXCEEDED",
        ),
    ),
    (
        "payload_ref",
        (
            "RUNTIME_PAYLOAD_REF_DENIED",
            "RUNTIME_PAYLOAD_REF_INVALID",
            "RUNTIME_PAYLOAD_REF_EXPIRED",
            "RUNTIME_PAYLOAD_REF_CHECKSUM_MISMATCH",
            "RUNTIME_PAYLOAD_REF_VERSION_MISMATCH",
            "RUNTIME_PAYLOAD_REF_VALIDATION_UNAVAILABLE",
            "RUNTIME_PAYLOAD_REF_VALIDATION_TIMEOUT",
        ),
    ),
    (
        "ack",
        (
            "RUNTIME_ACK_REJECTED",
            "RUNTIME_ACK_TIMEOUT",
        ),
    ),
    (
        "nack",
        (
            "RUNTIME_NACK_REJECTED",
            "RUNTIME_NACK_NON_RETRYABLE",
        ),
    ),
    (
        "defer",
        (
            "RUNTIME_DEFER_REJECTED",
            "RUNTIME_DEFER_BUDGET_EXCEEDED",
        ),
    ),
    (
        "lease",
        (
            "RUNTIME_DELIVERY_LEASE_EXPIRED",
            "RUNTIME_DELIVERY_LEASE_RENEW_FAILED",
            "RUNTIME_DELIVERY_LEASE_REJECTED",
            "RUNTIME_LEADER_LEASE_LOST",
        ),
    ),
    (
        "fencing",
        (
            "RUNTIME_FENCING_REJECTED",
            "RUNTIME_CLUSTER_FENCING_ERROR",
        ),
    ),
    (
        "owner",
        (
            "RUNTIME_OWNER_MISMATCH",
            "RUNTIME_OWNER_TRANSFER_REJECTED",
        ),
    ),
    (
        "processor",
        (
            "RUNTIME_PROCESSOR_TIMEOUT",
            "RUNTIME_PROCESSOR_FAILED",
        ),
    ),
    (
        "configuration",
        (
            "RUNTIME_CONFIG_INVALID",
            "RUNTIME_CONFIG_VERSION_CONFLICT",
            "RUNTIME_CONFIG_APPLY_FAILED",
            "RUNTIME_STARTUP_SECURITY_ERROR",
        ),
    ),
    (
        "transport",
        (
            "RUNTIME_TRANSPORT_ERROR",
            "RUNTIME_TRANSPORT_DISABLED",
            "RUNTIME_TRANSPORT_HANDSHAKE_FAILED",
            "RUNTIME_TRANSPORT_SEND_FAILED",
            "RUNTIME_TRANSPORT_RECEIVE_FAILED",
            "RUNTIME_TRANSPORT_STREAM_RESET",
            "RUNTIME_TRANSPORT_FLOW_CONTROL_BLOCKED",
            "RUNTIME_TRANSPORT_PATH_MIGRATION_FAILED",
            "RUNTIME_TRANSPORT_FALLBACK_FAILED",
            "RUNTIME_TRANSPORT_CAPABILITY_UNAVAILABLE",
        ),
    ),
    (
        "cluster",
        (
            "RUNTIME_CLUSTER_COORDINATION_ERROR",
            "RUNTIME_CLUSTER_STATE_ERROR",
            "RUNTIME_ROLE_ADMISSION_REJECTED",
            "RUNTIME_CLUSTER_MEMBER_UNAVAILABLE",
            "RUNTIME_CLUSTER_CONFIG_DRIFT",
        ),
    ),
    (
        "delivery",
        (
            "RUNTIME_DELIVERY_STATE_ERROR",
            "RUNTIME_BACKPRESSURE",
        ),
    ),
    (
        "state_store",
        (
            "RUNTIME_STATE_STORE_ERROR",
            "RUNTIME_STATE_STORE_NOT_READY",
            "RUNTIME_STATE_STORE_CLOSED",
            "RUNTIME_STATE_STORE_UNAVAILABLE",
            "RUNTIME_STATE_STORE_TIMEOUT",
            "RUNTIME_STATE_STORE_CONFLICT",
            "RUNTIME_STATE_STORE_STALE_READ",
            "RUNTIME_STATE_STORE_CAPABILITY_UNAVAILABLE",
            "RUNTIME_STATE_STORE_NAMESPACE_VIOLATION",
            "RUNTIME_STATE_STORE_VERSION_MISMATCH",
            "RUNTIME_STATE_STORE_INDETERMINATE_WRITE",
        ),
    ),
)


def _build_registry_indices(
    definitions: tuple[NsErrorDefinition, ...],
) -> tuple[
    Mapping[type[NsEvermoreError], NsErrorDefinition],
    Mapping[str, NsErrorDefinition],
    Mapping[int, NsErrorDefinition],
]:
    by_error_type: dict[type[NsEvermoreError], NsErrorDefinition] = {}
    by_code: dict[str, NsErrorDefinition] = {}
    by_numeric_code: dict[int, NsErrorDefinition] = {}

    for definition in definitions:
        if not isinstance(definition, NsErrorDefinition):
            raise TypeError("definitions must contain NsErrorDefinition values")
        if definition.code != definition.error_type.code:
            raise ValueError(
                "definition code must match the current error_type.code"
            )
        if definition.numeric_code != definition.error_type.numeric_code:
            raise ValueError(
                "definition numeric_code must match the current "
                "error_type.numeric_code"
            )
        if definition.error_type in by_error_type:
            raise ValueError(
                f"duplicate error type: {definition.error_type.__name__}"
            )
        if definition.code in by_code:
            raise ValueError(f"duplicate error code: {definition.code}")
        if definition.numeric_code in by_numeric_code:
            raise ValueError(
                f"duplicate numeric error code: {definition.numeric_code}"
            )
        by_error_type[definition.error_type] = definition
        by_code[definition.code] = definition
        by_numeric_code[definition.numeric_code] = definition

    return (
        MappingProxyType(by_error_type),
        MappingProxyType(by_code),
        MappingProxyType(by_numeric_code),
    )


@dataclass(frozen=True, slots=True, init=False)
class NsErrorRegistry:
    _definitions: tuple[NsErrorDefinition, ...] = field(repr=False)
    _by_error_type: Mapping[
        type[NsEvermoreError], NsErrorDefinition
    ] = field(repr=False)
    _by_code: Mapping[str, NsErrorDefinition] = field(repr=False)
    _by_numeric_code: Mapping[int, NsErrorDefinition] = field(repr=False)

    def __init__(self, definitions: Iterable[NsErrorDefinition]) -> None:
        normalized_definitions = tuple(definitions)
        by_error_type, by_code, by_numeric_code = _build_registry_indices(
            normalized_definitions
        )
        object.__setattr__(self, "_definitions", normalized_definitions)
        object.__setattr__(self, "_by_error_type", by_error_type)
        object.__setattr__(self, "_by_code", by_code)
        object.__setattr__(self, "_by_numeric_code", by_numeric_code)

    @property
    def definitions(self) -> tuple[NsErrorDefinition, ...]:
        return self._definitions

    def get_by_error_type(
        self, error_type: type[NsEvermoreError]
    ) -> NsErrorDefinition | None:
        """Return only the definition registered for this exact type."""
        return self._by_error_type.get(error_type)

    def get_by_code(self, code: str) -> NsErrorDefinition | None:
        return self._by_code.get(code)

    def get_by_numeric_code(
        self, numeric_code: int
    ) -> NsErrorDefinition | None:
        return self._by_numeric_code.get(numeric_code)

    def validate(self) -> None:
        _build_registry_indices(self._definitions)

    def to_dict(self) -> list[dict[str, object]]:
        return [definition.to_dict() for definition in self._definitions]


ERROR_REGISTRY = NsErrorRegistry(ALL_ERROR_DEFINITIONS)


def get_error_definition(
    error_type: type[NsEvermoreError],
) -> NsErrorDefinition | None:
    return ERROR_REGISTRY.get_by_error_type(error_type)


def get_error_definition_by_code(code: str) -> NsErrorDefinition | None:
    return ERROR_REGISTRY.get_by_code(code)


def get_error_definition_by_numeric_code(
    numeric_code: int,
) -> NsErrorDefinition | None:
    return ERROR_REGISTRY.get_by_numeric_code(numeric_code)


def list_error_definitions() -> tuple[NsErrorDefinition, ...]:
    return ERROR_REGISTRY.definitions


def validate_error_registry(registry: NsErrorRegistry = ERROR_REGISTRY) -> None:
    if not isinstance(registry, NsErrorRegistry):
        raise TypeError("registry must be NsErrorRegistry")
    registry.validate()


def validate_runtime_error_coverage_matrix(
    matrix: tuple[tuple[str, tuple[str, ...]], ...] = (
        RUNTIME_ERROR_COVERAGE_MATRIX
    ),
    registry: NsErrorRegistry = ERROR_REGISTRY,
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    if not isinstance(matrix, tuple):
        raise TypeError("runtime error coverage matrix must be a tuple")
    if not isinstance(registry, NsErrorRegistry):
        raise TypeError("registry must be NsErrorRegistry")

    areas: set[str] = set()
    covered_codes: set[str] = set()
    for entry in matrix:
        if not isinstance(entry, tuple) or len(entry) != 2:
            raise TypeError("coverage entries must be (area, codes) tuples")
        area, codes = entry
        if not isinstance(area, str) or not area.strip():
            raise ValueError("coverage area must be a non-empty string")
        if area in areas:
            raise ValueError(f"duplicate runtime error coverage area: {area}")
        if not isinstance(codes, tuple) or not codes:
            raise ValueError("coverage codes must be a non-empty tuple")
        areas.add(area)

        for code in codes:
            if not isinstance(code, str) or not code.startswith("RUNTIME_"):
                raise ValueError(
                    "runtime error coverage code must start with RUNTIME_"
                )
            if code in covered_codes:
                raise ValueError(f"duplicate runtime error coverage code: {code}")
            if registry.get_by_code(code) is None:
                raise ValueError(f"unregistered runtime error code: {code}")
            covered_codes.add(code)

    registered_runtime_codes = {
        definition.code
        for definition in registry.definitions
        if definition.code.startswith("RUNTIME_")
    }
    if covered_codes != registered_runtime_codes:
        missing = sorted(registered_runtime_codes - covered_codes)
        extra = sorted(covered_codes - registered_runtime_codes)
        raise ValueError(
            "runtime error coverage matrix mismatch: "
            f"missing={missing}, extra={extra}"
        )
    return matrix


validate_runtime_error_coverage_matrix()
