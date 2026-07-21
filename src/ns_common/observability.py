# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import math
import re
from collections import deque
from collections.abc import Mapping as MappingABC
from dataclasses import InitVar, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import RLock
from types import MappingProxyType
from typing import (
    Generic,
    Mapping,
    Protocol,
    TypeVar,
    runtime_checkable,
)

from ns_common.exceptions import NsValidationError
from ns_common.security import REDACTED, Sanitizer


DEFAULT_IN_MEMORY_SINK_CAPACITY = 1024
MAX_METRIC_ATTRIBUTES = 32
MAX_METRIC_ATTRIBUTE_KEY_LENGTH = 128
MAX_METRIC_ATTRIBUTE_VALUE_LENGTH = 256
# Maximum UTF-8 bytes of the complete public to_dict() record encoded with
# allow_nan=False, ensure_ascii=False, compact separators, and sorted keys.
MAX_OBSERVABILITY_RECORD_BYTES = 262144

RUNTIME_EVENT_LOOP_METRIC_NAMES: tuple[str, ...] = (
    "runtime_event_loop_implementation",
    "runtime_event_loop_lag_ms",
    "runtime_event_loop_lag_p95_ms",
    "runtime_event_loop_lag_p99_ms",
    "runtime_slow_callback_total",
    "runtime_pending_task_count",
    "runtime_cancelled_task_total",
    "runtime_executor_queue_depth",
)

RUNTIME_TRANSPORT_METRIC_NAMES: tuple[str, ...] = (
    "runtime_transport_connections",
    "runtime_transport_handshake_duration_ms",
    "runtime_transport_bytes_received_total",
    "runtime_transport_bytes_sent_total",
    "runtime_transport_receive_errors_total",
    "runtime_transport_send_errors_total",
    "runtime_transport_close_total",
    "runtime_transport_backpressure_duration_ms",
    "runtime_transport_read_queue_depth",
    "runtime_transport_write_queue_depth",
)

RUNTIME_QUIC_METRIC_NAMES: tuple[str, ...] = (
    "runtime_transport_rtt_ms",
    "runtime_transport_smoothed_rtt_ms",
    "runtime_transport_packet_loss_ratio",
    "runtime_transport_bytes_in_flight",
    "runtime_transport_congestion_window_bytes",
    "runtime_transport_flow_control_blocked_duration_ms",
    "runtime_transport_streams_active",
    "runtime_transport_streams_blocked",
    "runtime_transport_path_migration_total",
    "runtime_transport_path_migration_success_total",
    "runtime_transport_path_migration_failed_total",
    "runtime_transport_path_validation_duration_ms",
    "runtime_transport_datagrams_sent_total",
    "runtime_transport_datagrams_received_total",
    "runtime_transport_datagrams_dropped_total",
    "runtime_transport_zero_rtt_attempt_total",
    "runtime_transport_zero_rtt_rejected_total",
)

RUNTIME_STANDARD_METRIC_NAMES = frozenset(
    RUNTIME_EVENT_LOOP_METRIC_NAMES
    + RUNTIME_TRANSPORT_METRIC_NAMES
    + RUNTIME_QUIC_METRIC_NAMES
)

# These identifiers are valid in traces or an on-demand diagnostic snapshot,
# but create unbounded time-series cardinality when used as metric attributes.
HIGH_CARDINALITY_METRIC_ATTRIBUTE_KEYS = frozenset({
    "connection_id",
    "correlation_id",
    "delivery_id",
    "message_id",
    "operation_id",
    "parent_span_id",
    "path_id",
    "plan_id",
    "request_id",
    "session_id",
    "span_id",
    "stream_id",
    "summary_id",
    "tenant_id",
    "trace_id",
    "transport_connection_id",
    "transport_session_id",
    "transport_stream_id",
})

_HIGH_CARDINALITY_COMPACT_KEYS = frozenset(
    re.sub(r"[^a-z0-9]", "", key.casefold())
    for key in HIGH_CARDINALITY_METRIC_ATTRIBUTE_KEYS
)
_HIGH_CARDINALITY_COMPACT_SUFFIXES = frozenset({
    "connectionid",
    "correlationid",
    "deliveryid",
    "messageid",
    "operationid",
    "pathid",
    "planid",
    "requestid",
    "sessionid",
    "spanid",
    "streamid",
    "summaryid",
    "tenantid",
    "traceid",
    "transportconnectionid",
    "transportsessionid",
    "transportstreamid",
})
_METRIC_NAME_PATTERN = re.compile(r"[A-Za-z_:][A-Za-z0-9_:]{0,254}\Z")
_METRIC_ATTRIBUTE_KEY_PATTERN = re.compile(
    r"[A-Za-z_][A-Za-z0-9_.-]{0,127}\Z"
)
_SANITIZATION_FAILED_RECORD = {
    "observability_status": "sanitization_failed",
}
_SIZE_LIMIT_RECORD = {
    "observability_status": "size_limit_exceeded",
}


class NsMetricKind(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


class NsMetricAttributeValueType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"


class NsMetricTenantScope(str, Enum):
    """Finite metric classifications; these values are never tenant IDs."""

    SYSTEM = "system"
    TENANT = "tenant"
    CROSS_TENANT = "cross_tenant"
    SHARED = "shared"
    UNKNOWN = "unknown"


class NsTraceStatus(str, Enum):
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


class NsObservabilitySinkState(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


def _compact_metric_attribute_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _is_high_cardinality_metric_attribute_key(value: str) -> bool:
    compact_key = _compact_metric_attribute_key(value)
    return (
        compact_key in _HIGH_CARDINALITY_COMPACT_KEYS
        or any(
            compact_key.endswith(identifier)
            for identifier in _HIGH_CARDINALITY_COMPACT_SUFFIXES
        )
    )


def _strict_json_record_size(value: Mapping[str, object]) -> int:
    try:
        encoded = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except Exception:
        raise NsValidationError(
            "observability record cannot be strictly JSON encoded.",
            details={
                "field": "record",
                "action": "normalize_observability_record",
            },
        ) from None
    return len(encoded)


def _validate_complete_record_size(
    value: Mapping[str, object],
    *,
    record_type: str,
) -> int:
    actual_bytes = _strict_json_record_size(value)
    if actual_bytes > MAX_OBSERVABILITY_RECORD_BYTES:
        raise NsValidationError(
            "observability record exceeds the complete record size boundary.",
            details={
                "field": "record",
                "maximum_bytes": MAX_OBSERVABILITY_RECORD_BYTES,
                "actual_bytes": actual_bytes,
                "record_type": record_type,
            },
        ) from None
    return actual_bytes


def _resolve_sanitizer(value: Sanitizer | None) -> Sanitizer:
    if value is None:
        return Sanitizer()
    if not isinstance(value, Sanitizer):
        raise NsValidationError(
            "sanitizer must be a Sanitizer instance.",
            details={
                "field": "sanitizer",
                "actual_type": type(value).__name__,
            },
        )
    return value


def _normalize_utc_timestamp(value: object, *, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise NsValidationError(
            f"{field_name} must be a datetime.",
            details={
                "field": field_name,
                "actual_type": type(value).__name__,
            },
        )
    try:
        offset = value.utcoffset()
        normalized = value.astimezone(timezone.utc)
    except Exception:
        raise NsValidationError(
            f"{field_name} must have a valid timezone.",
            details={"field": field_name},
        ) from None
    if value.tzinfo is None or offset is None:
        raise NsValidationError(
            f"{field_name} must be timezone-aware.",
            details={"field": field_name},
        )
    return normalized


def _finite_number(
    value: object,
    *,
    field_name: str,
    minimum: float | None = None,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise NsValidationError(
            f"{field_name} must be a number.",
            details={
                "field": field_name,
                "actual_type": type(value).__name__,
            },
        )
    try:
        normalized = float(value)
    except (OverflowError, TypeError, ValueError):
        raise NsValidationError(
            f"{field_name} cannot be represented as a finite number.",
            details={"field": field_name},
        ) from None
    if not math.isfinite(normalized) or (
        minimum is not None and normalized < minimum
    ):
        raise NsValidationError(
            f"{field_name} is outside the allowed range.",
            details={
                "field": field_name,
                "minimum": minimum,
            },
        )
    return normalized


def _sanitize_text(
    value: object,
    *,
    field_name: str,
    sanitizer: Sanitizer,
    maximum_length: int,
    optional: bool = False,
) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise NsValidationError(
            f"{field_name} must be a string.",
            details={
                "field": field_name,
                "actual_type": type(value).__name__,
            },
        )
    if not value or value != value.strip():
        raise NsValidationError(
            f"{field_name} must be a non-empty string without surrounding whitespace.",
            details={"field": field_name},
        )
    if len(value) > maximum_length or any(
        ord(character) < 32 or ord(character) == 127
        for character in value
    ):
        raise NsValidationError(
            f"{field_name} is outside the allowed text range.",
            details={
                "field": field_name,
                "maximum_length": maximum_length,
            },
        )
    try:
        safe_value = sanitizer.sanitize_text(value)
    except Exception:
        safe_value = REDACTED
    if (
        not isinstance(safe_value, str)
        or not safe_value
        or len(safe_value) > maximum_length
        or any(
            ord(character) < 32 or ord(character) == 127
            for character in safe_value
        )
    ):
        return REDACTED
    return safe_value


def _freeze_json(value: object) -> object:
    if isinstance(value, MappingABC):
        return MappingProxyType({
            str(key): _freeze_json(item)
            for key, item in value.items()
        })
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)
    return value


def _thaw_json(value: object) -> object:
    if isinstance(value, MappingABC):
        return {
            str(key): _thaw_json(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _safe_frozen_mapping(
    value: object,
    *,
    field_name: str,
    path: tuple[str, ...],
    sanitizer: Sanitizer,
) -> Mapping[str, object]:
    if not isinstance(value, MappingABC):
        raise NsValidationError(
            f"{field_name} must be a mapping.",
            details={
                "field": field_name,
                "actual_type": type(value).__name__,
            },
        )
    try:
        sanitized = sanitizer.sanitize(value, path=path)
    except Exception:
        sanitized = _SANITIZATION_FAILED_RECORD
    if not isinstance(sanitized, MappingABC):
        sanitized = _SANITIZATION_FAILED_RECORD
    try:
        encoded = json.dumps(
            sanitized,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        normalized: object = json.loads(encoded)
    except Exception:
        normalized = _SANITIZATION_FAILED_RECORD
    if not isinstance(normalized, dict):
        normalized = dict(_SANITIZATION_FAILED_RECORD)
    frozen = _freeze_json(normalized)
    if not isinstance(frozen, MappingABC):
        raise AssertionError("frozen observability mapping must remain a mapping")
    return frozen


@dataclass(frozen=True, slots=True, kw_only=True)
class NsMetricAttributeDefinition:
    key: str
    value_type: NsMetricAttributeValueType
    allowed_values: frozenset[str | int | bool] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.key, str) or (
            _METRIC_ATTRIBUTE_KEY_PATTERN.fullmatch(self.key) is None
        ):
            raise NsValidationError(
                "metric attribute definition key is invalid.",
                details={
                    "field": "key",
                    "maximum_key_length": MAX_METRIC_ATTRIBUTE_KEY_LENGTH,
                },
            )
        if _is_high_cardinality_metric_attribute_key(self.key):
            raise NsValidationError(
                "metric attribute definitions cannot allow high-cardinality identifiers.",
                details={"field": "key"},
            )
        if not isinstance(self.value_type, NsMetricAttributeValueType):
            raise NsValidationError(
                "metric attribute definition value_type is invalid.",
                details={
                    "field": "value_type",
                    "actual_type": type(self.value_type).__name__,
                    "allowed_values": [
                        item.value for item in NsMetricAttributeValueType
                    ],
                },
            )

        if self.allowed_values is None:
            if self.value_type is not NsMetricAttributeValueType.BOOLEAN:
                raise NsValidationError(
                    "string and integer metric attributes require a finite value set.",
                    details={"field": "allowed_values"},
                )
            allowed_values: frozenset[str | int | bool] = frozenset({
                False,
                True,
            })
        else:
            if isinstance(self.allowed_values, (str, bytes)):
                raise NsValidationError(
                    "allowed_values must be a finite collection.",
                    details={"field": "allowed_values"},
                )
            try:
                allowed_values = frozenset(self.allowed_values)
            except Exception:
                raise NsValidationError(
                    "allowed_values must be a finite collection.",
                    details={"field": "allowed_values"},
                ) from None
            if not allowed_values:
                raise NsValidationError(
                    "allowed_values must not be empty.",
                    details={"field": "allowed_values"},
                )

        for allowed_value in allowed_values:
            self._validate_value(allowed_value, field_name="allowed_values")
        object.__setattr__(self, "allowed_values", allowed_values)

    @property
    def is_finite_enum(self) -> bool:
        return True

    def accepts(self, value: object) -> bool:
        try:
            self._validate_value(value, field_name=self.key)
        except NsValidationError:
            return False
        allowed_values = self.allowed_values
        assert allowed_values is not None
        return value in allowed_values

    def _validate_value(self, value: object, *, field_name: str) -> None:
        if self.value_type is NsMetricAttributeValueType.STRING:
            if not isinstance(value, str):
                raise NsValidationError(
                    "metric attribute value type does not match its definition.",
                    details={"field": field_name, "expected_type": "string"},
                )
            if len(value) > MAX_METRIC_ATTRIBUTE_VALUE_LENGTH or any(
                ord(character) < 32 or ord(character) == 127
                for character in value
            ):
                raise NsValidationError(
                    "metric attribute string is outside the allowed text range.",
                    details={
                        "field": field_name,
                        "maximum_length": MAX_METRIC_ATTRIBUTE_VALUE_LENGTH,
                    },
                )
            return
        if self.value_type is NsMetricAttributeValueType.INTEGER:
            if isinstance(value, bool) or not isinstance(value, int):
                raise NsValidationError(
                    "metric attribute value type does not match its definition.",
                    details={"field": field_name, "expected_type": "integer"},
                )
            if value.bit_length() > 63:
                raise NsValidationError(
                    "metric attribute integer is outside the allowed range.",
                    details={"field": field_name, "maximum_bits": 63},
                )
            return
        if not isinstance(value, bool):
            raise NsValidationError(
                "metric attribute value type does not match its definition.",
                details={"field": field_name, "expected_type": "boolean"},
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class NsMetricDefinition:
    name: str
    allowed_attributes: Mapping[str, NsMetricAttributeDefinition] = field(
        default_factory=dict
    )
    expected_kind: NsMetricKind | None = None
    expected_unit: str | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.name, str)
            or self.name != self.name.strip()
            or _METRIC_NAME_PATTERN.fullmatch(self.name) is None
        ):
            raise NsValidationError(
                "metric definition name is invalid.",
                details={"field": "name"},
            )
        if not isinstance(self.allowed_attributes, MappingABC):
            raise NsValidationError(
                "allowed_attributes must be a mapping.",
                details={
                    "field": "allowed_attributes",
                    "actual_type": type(self.allowed_attributes).__name__,
                },
            )
        try:
            attribute_items = tuple(self.allowed_attributes.items())
        except Exception:
            raise NsValidationError(
                "allowed_attributes could not be read.",
                details={"field": "allowed_attributes"},
            ) from None
        if len(attribute_items) > MAX_METRIC_ATTRIBUTES:
            raise NsValidationError(
                "metric definition allows too many attributes.",
                details={
                    "field": "allowed_attributes",
                    "maximum_items": MAX_METRIC_ATTRIBUTES,
                    "actual_items": len(attribute_items),
                },
            )

        frozen_attributes: dict[str, NsMetricAttributeDefinition] = {}
        for key, definition in attribute_items:
            if not isinstance(key, str) or not isinstance(
                definition,
                NsMetricAttributeDefinition,
            ):
                raise NsValidationError(
                    "allowed_attributes entries are invalid.",
                    details={"field": "allowed_attributes"},
                )
            if key in frozen_attributes:
                raise NsValidationError(
                    "metric attribute definition keys must be unique.",
                    details={"field": "allowed_attributes"},
                )
            if key != definition.key:
                raise NsValidationError(
                    "metric attribute registry key must match definition.key.",
                    details={"field": "allowed_attributes"},
                )
            frozen_attributes[key] = definition

        if self.expected_kind is not None and not isinstance(
            self.expected_kind,
            NsMetricKind,
        ):
            raise NsValidationError(
                "metric definition expected_kind is invalid.",
                details={"field": "expected_kind"},
            )
        if self.expected_unit is not None and (
            not isinstance(self.expected_unit, str)
            or not self.expected_unit
            or self.expected_unit != self.expected_unit.strip()
            or len(self.expected_unit) > 64
            or any(
                ord(character) < 32 or ord(character) == 127
                for character in self.expected_unit
            )
        ):
            raise NsValidationError(
                "metric definition expected_unit is invalid.",
                details={"field": "expected_unit"},
            )
        object.__setattr__(
            self,
            "allowed_attributes",
            MappingProxyType(frozen_attributes),
        )


_RUNTIME_COMPONENT_ATTRIBUTE = NsMetricAttributeDefinition(
    key="component_type",
    value_type=NsMetricAttributeValueType.STRING,
    allowed_values=frozenset({"runtime"}),
)
_EVENT_LOOP_IMPLEMENTATION_ATTRIBUTE = NsMetricAttributeDefinition(
    key="implementation",
    value_type=NsMetricAttributeValueType.STRING,
    allowed_values=frozenset({"asyncio", "uvloop"}),
)
_TRANSPORT_TYPE_ATTRIBUTE = NsMetricAttributeDefinition(
    key="transport_type",
    value_type=NsMetricAttributeValueType.STRING,
    allowed_values=frozenset({
        "quic_native",
        "websocket_http3",
        "websocket_tcp",
        "webtransport_http3",
    }),
)
_QUIC_TRANSPORT_TYPE_ATTRIBUTE = NsMetricAttributeDefinition(
    key="transport_type",
    value_type=NsMetricAttributeValueType.STRING,
    allowed_values=frozenset({
        "quic_native",
        "websocket_http3",
        "webtransport_http3",
    }),
)
_TRANSPORT_COMPONENT_ATTRIBUTE = NsMetricAttributeDefinition(
    key="component_type",
    value_type=NsMetricAttributeValueType.STRING,
    allowed_values=frozenset({
        "backend",
        "client",
        "frontend",
        "node",
        "runtime",
        "sub_node",
    }),
)
_TENANT_SCOPE_ATTRIBUTE = NsMetricAttributeDefinition(
    key="tenant_scope",
    value_type=NsMetricAttributeValueType.STRING,
    allowed_values=frozenset(item.value for item in NsMetricTenantScope),
)
_TRANSPORT_CLOSE_REASON_ATTRIBUTE = NsMetricAttributeDefinition(
    key="close_reason",
    value_type=NsMetricAttributeValueType.STRING,
    allowed_values=frozenset({
        "adapter_shutdown",
        "keepalive_failed",
        "listener_failed",
        "message_too_large",
        "normal",
        "protocol_error",
        "read_queue_full",
        "receive_failed",
        "remote_closed",
        "send_failed",
        "send_timeout",
        "tls_failed",
        "write_queue_full",
    }),
)
_TRANSPORT_ERROR_CODE_ATTRIBUTE = NsMetricAttributeDefinition(
    key="error_code",
    value_type=NsMetricAttributeValueType.STRING,
    allowed_values=frozenset({
        "RUNTIME_TRANSPORT_ERROR",
        "RUNTIME_TRANSPORT_FLOW_CONTROL_BLOCKED",
        "RUNTIME_TRANSPORT_HANDSHAKE_FAILED",
        "RUNTIME_TRANSPORT_RECEIVE_FAILED",
        "RUNTIME_TRANSPORT_SEND_FAILED",
        "RUNTIME_TRANSPORT_STREAM_RESET",
    }),
)


def _build_runtime_standard_metric_definitions(
) -> Mapping[str, NsMetricDefinition]:
    definitions = {
        name: NsMetricDefinition(name=name)
        for name in (
            RUNTIME_EVENT_LOOP_METRIC_NAMES
            + RUNTIME_TRANSPORT_METRIC_NAMES
            + RUNTIME_QUIC_METRIC_NAMES
        )
    }
    definitions["runtime_event_loop_implementation"] = NsMetricDefinition(
        name="runtime_event_loop_implementation",
        allowed_attributes={
            "implementation": _EVENT_LOOP_IMPLEMENTATION_ATTRIBUTE,
        },
    )
    definitions["runtime_pending_task_count"] = NsMetricDefinition(
        name="runtime_pending_task_count",
        allowed_attributes={
            "component_type": _RUNTIME_COMPONENT_ATTRIBUTE,
        },
    )
    for name in RUNTIME_TRANSPORT_METRIC_NAMES:
        definitions[name] = NsMetricDefinition(
            name=name,
            allowed_attributes={
                "transport_type": _TRANSPORT_TYPE_ATTRIBUTE,
            },
        )
    definitions["runtime_transport_connections"] = NsMetricDefinition(
        name="runtime_transport_connections",
        allowed_attributes={
            "component_type": _TRANSPORT_COMPONENT_ATTRIBUTE,
            "tenant_scope": _TENANT_SCOPE_ATTRIBUTE,
            "transport_type": _TRANSPORT_TYPE_ATTRIBUTE,
        },
    )
    definitions["runtime_transport_receive_errors_total"] = NsMetricDefinition(
        name="runtime_transport_receive_errors_total",
        allowed_attributes={
            "error_code": _TRANSPORT_ERROR_CODE_ATTRIBUTE,
            "transport_type": _TRANSPORT_TYPE_ATTRIBUTE,
        },
    )
    definitions["runtime_transport_send_errors_total"] = NsMetricDefinition(
        name="runtime_transport_send_errors_total",
        allowed_attributes={
            "error_code": _TRANSPORT_ERROR_CODE_ATTRIBUTE,
            "transport_type": _TRANSPORT_TYPE_ATTRIBUTE,
        },
    )
    definitions["runtime_transport_close_total"] = NsMetricDefinition(
        name="runtime_transport_close_total",
        allowed_attributes={
            "close_reason": _TRANSPORT_CLOSE_REASON_ATTRIBUTE,
            "transport_type": _TRANSPORT_TYPE_ATTRIBUTE,
        },
    )
    for name in RUNTIME_QUIC_METRIC_NAMES:
        definitions[name] = NsMetricDefinition(
            name=name,
            allowed_attributes={
                "transport_type": _QUIC_TRANSPORT_TYPE_ATTRIBUTE,
            },
        )
    return MappingProxyType(definitions)


RUNTIME_STANDARD_METRIC_DEFINITIONS = (
    _build_runtime_standard_metric_definitions()
)


def _resolve_metric_definition(
    *,
    name: str,
    definition: object,
    has_attributes: bool,
) -> NsMetricDefinition | None:
    if definition is not None and not isinstance(definition, NsMetricDefinition):
        raise NsValidationError(
            "definition must be an NsMetricDefinition.",
            details={
                "field": "definition",
                "actual_type": type(definition).__name__,
            },
        )
    explicit_definition = definition
    standard_definition = RUNTIME_STANDARD_METRIC_DEFINITIONS.get(name)
    if standard_definition is not None:
        if (
            explicit_definition is not None
            and explicit_definition != standard_definition
        ):
            raise NsValidationError(
                "standard metrics must use the authoritative definition.",
                details={"field": "definition"},
            )
        return standard_definition
    if explicit_definition is not None:
        if explicit_definition.name != name:
            raise NsValidationError(
                "metric definition name must match record.name.",
                details={"field": "definition.name"},
            )
        return explicit_definition
    if has_attributes:
        raise NsValidationError(
            "non-standard metrics with attributes require a definition.",
            details={"field": "definition"},
        )
    return None


def _validate_metric_attribute_value(
    *,
    key: str,
    value: object,
    definition: NsMetricAttributeDefinition,
) -> None:
    if not definition.accepts(value):
        raise NsValidationError(
            "metric attribute value is outside its finite definition.",
            details={
                "field": f"attributes.{key}",
                "expected_type": definition.value_type.value,
            },
        )


def _validate_metric_attributes(
    value: object,
    *,
    sanitizer: Sanitizer,
    definition: NsMetricDefinition | None,
) -> Mapping[str, object]:
    if not isinstance(value, MappingABC):
        raise NsValidationError(
            "metric attributes must be a mapping.",
            details={
                "field": "attributes",
                "actual_type": type(value).__name__,
            },
        )
    try:
        items = tuple(value.items())
    except Exception:
        raise NsValidationError(
            "metric attributes could not be read.",
            details={"field": "attributes"},
        ) from None
    if len(items) > MAX_METRIC_ATTRIBUTES:
        raise NsValidationError(
            "metric attributes exceed the cardinality boundary.",
            details={
                "field": "attributes",
                "maximum_items": MAX_METRIC_ATTRIBUTES,
                "actual_items": len(items),
            },
        )

    allowed_attributes = (
        {} if definition is None else definition.allowed_attributes
    )
    raw_attributes: dict[str, object] = {}
    for key, item in items:
        if not isinstance(key, str) or (
            _METRIC_ATTRIBUTE_KEY_PATTERN.fullmatch(key) is None
        ):
            raise NsValidationError(
                "metric attribute keys must use the stable label format.",
                details={
                    "field": "attributes",
                    "actual_type": type(key).__name__,
                    "maximum_key_length": MAX_METRIC_ATTRIBUTE_KEY_LENGTH,
                },
            )
        if _is_high_cardinality_metric_attribute_key(key):
            raise NsValidationError(
                "high-cardinality identifiers cannot be metric attributes.",
                details={
                    "field": f"attributes.{key}",
                    "use_instead": "trace_or_diagnostic_snapshot",
                },
            )
        attribute_definition = allowed_attributes.get(key)
        if attribute_definition is None:
            raise NsValidationError(
                "metric attribute is not allowed by the metric definition.",
                details={"field": f"attributes.{key}"},
            )
        _validate_metric_attribute_value(
            key=key,
            value=item,
            definition=attribute_definition,
        )
        raw_attributes[key] = item

    try:
        sanitized = sanitizer.sanitize(
            raw_attributes,
            path=("observability", "metric", "attributes"),
        )
    except Exception:
        raise NsValidationError(
            "metric attributes could not be sanitized safely.",
            details={"field": "attributes"},
        ) from None
    if not isinstance(sanitized, MappingABC):
        raise NsValidationError(
            "metric attributes could not be sanitized safely.",
            details={"field": "attributes"},
        )
    try:
        encoded = json.dumps(
            sanitized,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        normalized = json.loads(encoded)
    except Exception:
        raise NsValidationError(
            "metric attributes could not be normalized safely.",
            details={"field": "attributes"},
        ) from None
    if not isinstance(normalized, dict) or set(normalized) != set(raw_attributes):
        raise NsValidationError(
            "sanitized metric attributes must preserve the definition schema.",
            details={"field": "attributes"},
        )
    for key, item in normalized.items():
        if _is_high_cardinality_metric_attribute_key(key):
            raise NsValidationError(
                "sanitized metric attributes cannot introduce high-cardinality identifiers.",
                details={"field": f"attributes.{key}"},
            )
        attribute_definition = allowed_attributes.get(key)
        if attribute_definition is None:
            raise NsValidationError(
                "sanitized metric attribute is not allowed by the definition.",
                details={"field": f"attributes.{key}"},
            )
        _validate_metric_attribute_value(
            key=key,
            value=item,
            definition=attribute_definition,
        )
    frozen = _freeze_json(normalized)
    if not isinstance(frozen, MappingABC):
        raise AssertionError("frozen metric attributes must remain a mapping")
    return frozen


@dataclass(frozen=True, slots=True, kw_only=True)
class NsMetricRecord:
    name: str
    kind: NsMetricKind
    value: float
    observed_at: datetime
    unit: str | None = None
    attributes: Mapping[str, object] = field(default_factory=dict)
    definition: NsMetricDefinition | None = field(
        default=None,
        repr=False,
        compare=False,
    )
    sanitizer: InitVar[Sanitizer | None] = None

    def __post_init__(self, sanitizer: Sanitizer | None) -> None:
        safe_sanitizer = _resolve_sanitizer(sanitizer)
        name = _sanitize_text(
            self.name,
            field_name="name",
            sanitizer=safe_sanitizer,
            maximum_length=255,
        )
        if not isinstance(name, str) or _METRIC_NAME_PATTERN.fullmatch(name) is None:
            raise NsValidationError(
                "metric name must use the stable metric name format.",
                details={"field": "name"},
            )
        if not isinstance(self.kind, NsMetricKind):
            raise NsValidationError(
                "metric kind is invalid.",
                details={
                    "field": "kind",
                    "actual_type": type(self.kind).__name__,
                    "allowed_values": [item.value for item in NsMetricKind],
                },
            )
        value = _finite_number(
            self.value,
            field_name="value",
            minimum=(0.0 if self.kind is NsMetricKind.COUNTER else None),
        )
        observed_at = _normalize_utc_timestamp(
            self.observed_at,
            field_name="observed_at",
        )
        unit = _sanitize_text(
            self.unit,
            field_name="unit",
            sanitizer=safe_sanitizer,
            maximum_length=64,
            optional=True,
        )
        if not isinstance(self.attributes, MappingABC):
            raise NsValidationError(
                "metric attributes must be a mapping.",
                details={
                    "field": "attributes",
                    "actual_type": type(self.attributes).__name__,
                },
            )
        try:
            has_attributes = bool(len(self.attributes))
        except Exception:
            raise NsValidationError(
                "metric attributes could not be read.",
                details={"field": "attributes"},
            ) from None
        definition = _resolve_metric_definition(
            name=name,
            definition=self.definition,
            has_attributes=has_attributes,
        )
        if definition is not None:
            if (
                definition.expected_kind is not None
                and definition.expected_kind is not self.kind
            ):
                raise NsValidationError(
                    "metric kind does not match its definition.",
                    details={"field": "kind"},
                )
            if (
                definition.expected_unit is not None
                and definition.expected_unit != unit
            ):
                raise NsValidationError(
                    "metric unit does not match its definition.",
                    details={"field": "unit"},
                )
        attributes = _validate_metric_attributes(
            self.attributes,
            sanitizer=safe_sanitizer,
            definition=definition,
        )

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "observed_at", observed_at)
        object.__setattr__(self, "unit", unit)
        object.__setattr__(self, "attributes", attributes)
        object.__setattr__(self, "definition", definition)
        _validate_complete_record_size(
            self.to_dict(),
            record_type="metric",
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "kind": self.kind.value,
            "value": self.value,
            "observed_at": self.observed_at.isoformat(),
            "unit": self.unit,
            "attributes": _thaw_json(self.attributes),
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class NsTraceRecord:
    name: str
    started_at: datetime
    status: NsTraceStatus = NsTraceStatus.UNSET
    duration_ms: float | None = None
    trace_id: str | None = None
    span_id: str | None = None
    parent_span_id: str | None = None
    correlation_id: str | None = None
    request_id: str | None = None
    attributes: Mapping[str, object] = field(default_factory=dict)
    sanitizer: InitVar[Sanitizer | None] = None

    def __post_init__(self, sanitizer: Sanitizer | None) -> None:
        safe_sanitizer = _resolve_sanitizer(sanitizer)
        name = _sanitize_text(
            self.name,
            field_name="name",
            sanitizer=safe_sanitizer,
            maximum_length=256,
        )
        started_at = _normalize_utc_timestamp(
            self.started_at,
            field_name="started_at",
        )
        if not isinstance(self.status, NsTraceStatus):
            raise NsValidationError(
                "trace status is invalid.",
                details={
                    "field": "status",
                    "actual_type": type(self.status).__name__,
                    "allowed_values": [item.value for item in NsTraceStatus],
                },
            )
        duration_ms = (
            None
            if self.duration_ms is None
            else _finite_number(
                self.duration_ms,
                field_name="duration_ms",
                minimum=0.0,
            )
        )
        identifiers = {
            field_name: _sanitize_text(
                getattr(self, field_name),
                field_name=field_name,
                sanitizer=safe_sanitizer,
                maximum_length=256,
                optional=True,
            )
            for field_name in (
                "trace_id",
                "span_id",
                "parent_span_id",
                "correlation_id",
                "request_id",
            )
        }
        if identifiers["span_id"] is not None and identifiers["trace_id"] is None:
            raise NsValidationError(
                "span_id requires trace_id.",
                details={"field": "span_id", "required_field": "trace_id"},
            )
        if (
            identifiers["parent_span_id"] is not None
            and identifiers["span_id"] is None
        ):
            raise NsValidationError(
                "parent_span_id requires span_id.",
                details={
                    "field": "parent_span_id",
                    "required_field": "span_id",
                },
            )
        attributes = _safe_frozen_mapping(
            self.attributes,
            field_name="attributes",
            path=("observability", "trace", "attributes"),
            sanitizer=safe_sanitizer,
        )

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "started_at", started_at)
        object.__setattr__(self, "duration_ms", duration_ms)
        object.__setattr__(self, "attributes", attributes)
        for field_name, identifier in identifiers.items():
            object.__setattr__(self, field_name, identifier)
        _validate_complete_record_size(
            self.to_dict(),
            record_type="trace",
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "started_at": self.started_at.isoformat(),
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "correlation_id": self.correlation_id,
            "request_id": self.request_id,
            "attributes": _thaw_json(self.attributes),
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class NsDiagnosticSnapshot:
    name: str
    captured_at: datetime
    snapshot: Mapping[str, object]
    sanitizer: InitVar[Sanitizer | None] = None

    def __post_init__(self, sanitizer: Sanitizer | None) -> None:
        safe_sanitizer = _resolve_sanitizer(sanitizer)
        name = _sanitize_text(
            self.name,
            field_name="name",
            sanitizer=safe_sanitizer,
            maximum_length=256,
        )
        captured_at = _normalize_utc_timestamp(
            self.captured_at,
            field_name="captured_at",
        )
        snapshot = _safe_frozen_mapping(
            self.snapshot,
            field_name="snapshot",
            path=("observability", "diagnostic_snapshot"),
            sanitizer=safe_sanitizer,
        )

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "captured_at", captured_at)
        object.__setattr__(self, "snapshot", snapshot)
        actual_bytes = _strict_json_record_size(self.to_dict())
        if actual_bytes > MAX_OBSERVABILITY_RECORD_BYTES:
            size_limit_snapshot = _freeze_json(dict(_SIZE_LIMIT_RECORD))
            if not isinstance(size_limit_snapshot, MappingABC):
                raise AssertionError(
                    "diagnostic size-limit snapshot must remain a mapping"
                )
            object.__setattr__(self, "snapshot", size_limit_snapshot)
            _validate_complete_record_size(
                self.to_dict(),
                record_type="diagnostic_snapshot",
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "captured_at": self.captured_at.isoformat(),
            "snapshot": _thaw_json(self.snapshot),
        }


@runtime_checkable
class MetricsSink(Protocol):
    """Best-effort metric sink injected explicitly by the composition root."""

    def record(self, record: NsMetricRecord) -> bool:
        """Accept locally, or return False when lifecycle state rejects it."""
        ...

    async def flush(self) -> None:
        """Flush any implementation-owned buffer."""
        ...

    async def aclose(self) -> None:
        """Release implementation-owned resources idempotently."""
        ...


@runtime_checkable
class TraceSink(Protocol):
    """Best-effort trace sink injected explicitly by the composition root."""

    def record(self, record: NsTraceRecord) -> bool:
        """Accept locally, or return False when lifecycle state rejects it."""
        ...

    async def flush(self) -> None:
        """Flush any implementation-owned buffer."""
        ...

    async def aclose(self) -> None:
        """Release implementation-owned resources idempotently."""
        ...


@runtime_checkable
class DiagnosticSnapshotSink(Protocol):
    """Best-effort diagnostic snapshot sink for bounded, sanitized records."""

    def record(self, record: NsDiagnosticSnapshot) -> bool:
        """Accept locally, or return False when lifecycle state rejects it."""
        ...

    async def flush(self) -> None:
        """Flush any implementation-owned buffer."""
        ...

    async def aclose(self) -> None:
        """Release implementation-owned resources idempotently."""
        ...


_RecordT = TypeVar("_RecordT")


class _InMemorySink(Generic[_RecordT]):
    def __init__(
        self,
        *,
        capacity: int = DEFAULT_IN_MEMORY_SINK_CAPACITY,
        sink_name: str,
    ) -> None:
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 1:
            raise NsValidationError(
                "capacity must be a positive integer.",
                details={
                    "field": "capacity",
                    "actual_type": type(capacity).__name__,
                },
            )
        self._capacity = capacity
        self._sink_name = sink_name
        self._records: deque[_RecordT] = deque(maxlen=capacity)
        self._dropped_count = 0
        self._rejected_count = 0
        self._state = NsObservabilitySinkState.OPEN
        self._lock = RLock()

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def state(self) -> NsObservabilitySinkState:
        with self._lock:
            return self._state

    @property
    def is_closed(self) -> bool:
        return self.state is NsObservabilitySinkState.CLOSED

    @property
    def dropped_count(self) -> int:
        with self._lock:
            return self._dropped_count

    @property
    def rejected_count(self) -> int:
        with self._lock:
            return self._rejected_count

    @property
    def records(self) -> tuple[_RecordT, ...]:
        with self._lock:
            return tuple(self._records)

    def clear(self) -> int:
        """Clear records and drops; retain lifecycle-level closed rejections."""
        with self._lock:
            removed = len(self._records)
            self._records.clear()
            self._dropped_count = 0
            return removed

    def _append(self, record: _RecordT) -> bool:
        with self._lock:
            if self._state is not NsObservabilitySinkState.OPEN:
                self._rejected_count += 1
                return False
            if len(self._records) == self._capacity:
                self._dropped_count += 1
            self._records.append(record)
            return True

    async def flush(self) -> None:
        # The memory implementation has no exporter or pending I/O.
        return None

    async def aclose(self) -> None:
        with self._lock:
            self._state = NsObservabilitySinkState.CLOSED


class InMemoryMetricsSink(_InMemorySink[NsMetricRecord]):
    def __init__(
        self,
        *,
        capacity: int = DEFAULT_IN_MEMORY_SINK_CAPACITY,
    ) -> None:
        super().__init__(capacity=capacity, sink_name="metrics")

    def record(self, record: NsMetricRecord) -> bool:
        if not isinstance(record, NsMetricRecord):
            raise NsValidationError(
                "record must be an NsMetricRecord.",
                details={
                    "field": "record",
                    "actual_type": type(record).__name__,
                },
            )
        return self._append(record)


class InMemoryTraceSink(_InMemorySink[NsTraceRecord]):
    def __init__(
        self,
        *,
        capacity: int = DEFAULT_IN_MEMORY_SINK_CAPACITY,
    ) -> None:
        super().__init__(capacity=capacity, sink_name="trace")

    def record(self, record: NsTraceRecord) -> bool:
        if not isinstance(record, NsTraceRecord):
            raise NsValidationError(
                "record must be an NsTraceRecord.",
                details={
                    "field": "record",
                    "actual_type": type(record).__name__,
                },
            )
        return self._append(record)


class InMemoryDiagnosticSnapshotSink(_InMemorySink[NsDiagnosticSnapshot]):
    def __init__(
        self,
        *,
        capacity: int = DEFAULT_IN_MEMORY_SINK_CAPACITY,
    ) -> None:
        super().__init__(capacity=capacity, sink_name="diagnostic_snapshot")

    def record(self, record: NsDiagnosticSnapshot) -> bool:
        if not isinstance(record, NsDiagnosticSnapshot):
            raise NsValidationError(
                "record must be an NsDiagnosticSnapshot.",
                details={
                    "field": "record",
                    "actual_type": type(record).__name__,
                },
            )
        return self._append(record)


MetricAttributeDefinition = NsMetricAttributeDefinition
MetricAttributeValueType = NsMetricAttributeValueType
MetricDefinition = NsMetricDefinition
MetricKind = NsMetricKind
MetricTenantScope = NsMetricTenantScope
TraceStatus = NsTraceStatus
ObservabilitySinkState = NsObservabilitySinkState
MetricRecord = NsMetricRecord
TraceRecord = NsTraceRecord
DiagnosticSnapshot = NsDiagnosticSnapshot
NsMetricsSink = MetricsSink
NsTraceSink = TraceSink
NsDiagnosticSnapshotSink = DiagnosticSnapshotSink
NsInMemoryMetricsSink = InMemoryMetricsSink
NsInMemoryTraceSink = InMemoryTraceSink
NsInMemoryDiagnosticSnapshotSink = InMemoryDiagnosticSnapshotSink


__all__ = [
    "DEFAULT_IN_MEMORY_SINK_CAPACITY",
    "DiagnosticSnapshot",
    "DiagnosticSnapshotSink",
    "HIGH_CARDINALITY_METRIC_ATTRIBUTE_KEYS",
    "InMemoryDiagnosticSnapshotSink",
    "InMemoryMetricsSink",
    "InMemoryTraceSink",
    "MAX_METRIC_ATTRIBUTES",
    "MAX_METRIC_ATTRIBUTE_KEY_LENGTH",
    "MAX_METRIC_ATTRIBUTE_VALUE_LENGTH",
    "MAX_OBSERVABILITY_RECORD_BYTES",
    "MetricAttributeDefinition",
    "MetricAttributeValueType",
    "MetricDefinition",
    "MetricKind",
    "MetricRecord",
    "MetricTenantScope",
    "MetricsSink",
    "NsDiagnosticSnapshot",
    "NsDiagnosticSnapshotSink",
    "NsInMemoryDiagnosticSnapshotSink",
    "NsInMemoryMetricsSink",
    "NsInMemoryTraceSink",
    "NsMetricAttributeDefinition",
    "NsMetricAttributeValueType",
    "NsMetricDefinition",
    "NsMetricKind",
    "NsMetricRecord",
    "NsMetricTenantScope",
    "NsMetricsSink",
    "NsObservabilitySinkState",
    "NsTraceRecord",
    "NsTraceSink",
    "NsTraceStatus",
    "ObservabilitySinkState",
    "RUNTIME_EVENT_LOOP_METRIC_NAMES",
    "RUNTIME_QUIC_METRIC_NAMES",
    "RUNTIME_STANDARD_METRIC_DEFINITIONS",
    "RUNTIME_STANDARD_METRIC_NAMES",
    "RUNTIME_TRANSPORT_METRIC_NAMES",
    "TraceRecord",
    "TraceSink",
    "TraceStatus",
]
