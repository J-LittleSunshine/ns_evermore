# -*- coding: utf-8 -*-
"""Strict, transport-independent models for the grouped runtime Envelope."""

from __future__ import annotations

import re
from dataclasses import MISSING, dataclass, fields
from types import MappingProxyType
from typing import Any, ClassVar, Mapping, TypeVar

from ns_common.exceptions import NsRuntimeEnvelopeSchemaError


JSONValue = None | bool | int | float | str | tuple["JSONValue", ...] | Mapping[str, "JSONValue"]
_MESSAGE_TYPE_PATTERN = re.compile(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+")
_NON_EMPTY_PATTERN = re.compile(r"\S+")
_T = TypeVar("_T", bound="StrictGroup")


def _schema_error(group: str, field: str, reason: str) -> NsRuntimeEnvelopeSchemaError:
    return NsRuntimeEnvelopeSchemaError(
        "Runtime envelope group is invalid.",
        details={"group": group, "field": field, "reason": reason},
    )


def _require_string(group: str, field: str, value: object) -> None:
    if not isinstance(value, str) or _NON_EMPTY_PATTERN.fullmatch(value) is None:
        raise _schema_error(group, field, "non_empty_string_required")


def _optional_string(group: str, field: str, value: object | None) -> None:
    if value is not None:
        _require_string(group, field, value)


def _optional_non_negative_integer(
    group: str,
    field: str,
    value: object | None,
) -> None:
    if value is not None and (
        isinstance(value, bool) or not isinstance(value, int) or value < 0
    ):
        raise _schema_error(group, field, "non_negative_integer_required")


def _require_non_negative_integer(group: str, field: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise _schema_error(group, field, "non_negative_integer_required")


def _freeze_json(value: Any, *, group: str, field: str) -> JSONValue:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        frozen: dict[str, JSONValue] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key:
                raise _schema_error(group, field, "string_object_keys_required")
            frozen[key] = _freeze_json(item, group=group, field=field)
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item, group=group, field=field) for item in value)
    raise _schema_error(group, field, "json_value_required")


def _thaw_json(value: JSONValue) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


class StrictGroup:
    """Construct a frozen group from an exact field set."""

    GROUP_NAME: ClassVar[str]

    @classmethod
    def from_mapping(cls: type[_T], value: object) -> _T:
        if not isinstance(value, Mapping) or not value:
            raise _schema_error(cls.GROUP_NAME, cls.GROUP_NAME, "non_empty_object_required")
        field_definitions = fields(cls)
        allowed = {definition.name for definition in field_definitions}
        if any(key not in allowed for key in value):
            raise _schema_error(cls.GROUP_NAME, "$unknown", "unknown_field")
        missing = [
            definition.name
            for definition in field_definitions
            if definition.default is MISSING
            and definition.default_factory is MISSING
            and definition.name not in value
        ]
        if missing:
            raise _schema_error(cls.GROUP_NAME, missing[0], "required_field_missing")
        return cls(**dict(value))

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for definition in fields(self):
            value = getattr(self, definition.name)
            if value is None:
                continue
            if isinstance(value, tuple):
                result[definition.name] = [_thaw_json(item) for item in value]
            elif isinstance(value, Mapping):
                result[definition.name] = _thaw_json(value)
            else:
                result[definition.name] = value
        return result


@dataclass(frozen=True, slots=True)
class ProtocolGroup(StrictGroup):
    GROUP_NAME: ClassVar[str] = "protocol"
    major: int
    minor: int
    patch: int
    min_version: str | None = None

    def __post_init__(self) -> None:
        for name in ("major", "minor", "patch"):
            _require_non_negative_integer(self.GROUP_NAME, name, getattr(self, name))
        _optional_string(self.GROUP_NAME, "min_version", self.min_version)


@dataclass(frozen=True, slots=True)
class MessageGroup(StrictGroup):
    GROUP_NAME: ClassVar[str] = "message"
    message_id: str
    type: str
    category: str
    priority: int
    created_at: str
    expires_at: str | None = None
    reliability: str = "best_effort"

    def __post_init__(self) -> None:
        for name in ("message_id", "category", "created_at", "reliability"):
            _require_string(self.GROUP_NAME, name, getattr(self, name))
        if not isinstance(self.type, str) or _MESSAGE_TYPE_PATTERN.fullmatch(self.type) is None:
            raise _schema_error(self.GROUP_NAME, "type", "dotted_message_type_required")
        if isinstance(self.priority, bool) or not isinstance(self.priority, int):
            raise _schema_error(self.GROUP_NAME, "priority", "integer_required")
        _optional_string(self.GROUP_NAME, "expires_at", self.expires_at)


@dataclass(frozen=True, slots=True)
class SourceGroup(StrictGroup):
    GROUP_NAME: ClassVar[str] = "source"
    runtime_id: str
    connection_id: str
    identity_digest: str
    tenant_id: str
    component_type: str
    capabilities_digest: str

    def __post_init__(self) -> None:
        for definition in fields(self):
            _require_string(self.GROUP_NAME, definition.name, getattr(self, definition.name))


@dataclass(frozen=True, slots=True)
class TargetGroup(StrictGroup):
    GROUP_NAME: ClassVar[str] = "target"
    kind: str
    connection_id: str | None = None
    connection_epoch: int | None = None
    identity: str | None = None
    tenant_id: str | None = None
    capabilities: tuple[str, ...] | list[str] | None = None
    component_type: str | None = None
    runtime_id: str | None = None
    scope: str | None = None
    multi_connection_policy: str | None = None
    rebind_policy: str | None = None
    fanout_count: int | None = None
    required_count: int | None = None
    subset_size: int | None = None

    def __post_init__(self) -> None:
        _require_string(self.GROUP_NAME, "kind", self.kind)
        for name in (
            "connection_id", "identity", "tenant_id", "component_type",
            "runtime_id", "scope", "multi_connection_policy", "rebind_policy",
        ):
            _optional_string(self.GROUP_NAME, name, getattr(self, name))
        _optional_non_negative_integer(
            self.GROUP_NAME,
            "connection_epoch",
            self.connection_epoch,
        )
        for name in ("fanout_count", "required_count", "subset_size"):
            value = getattr(self, name)
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value <= 0
            ):
                raise _schema_error(
                    self.GROUP_NAME,
                    name,
                    "positive_integer_required",
                )
        if self.capabilities is not None:
            if not isinstance(self.capabilities, (list, tuple)):
                raise _schema_error(self.GROUP_NAME, "capabilities", "array_required")
            normalized = tuple(self.capabilities)
            if not normalized:
                raise _schema_error(self.GROUP_NAME, "capabilities", "non_empty_array_required")
            for item in normalized:
                _require_string(self.GROUP_NAME, "capabilities", item)
            if len(set(normalized)) != len(normalized):
                raise _schema_error(
                    self.GROUP_NAME,
                    "capabilities",
                    "duplicate_capability",
                )
            object.__setattr__(self, "capabilities", tuple(sorted(normalized)))
        _validate_target_contract(self)


_TARGET_PRIMARY_FIELD = {
    "connection": "connection_id",
    "identity": "identity",
    "tenant": "tenant_id",
    "capability": "capabilities",
    "component_type": "component_type",
    "runtime": "runtime_id",
    "broadcast": "scope",
}
_TARGET_SELECTOR_FIELDS = frozenset(_TARGET_PRIMARY_FIELD.values())
_TARGET_ALLOWED_FIELDS = {
    "connection": frozenset({
        "connection_id", "connection_epoch", "tenant_id", "capabilities",
        "component_type", "multi_connection_policy", "rebind_policy",
    }),
    "identity": frozenset({
        "identity", "tenant_id", "capabilities", "component_type",
        "multi_connection_policy", "rebind_policy", "fanout_count",
        "required_count", "subset_size",
    }),
    "tenant": frozenset({
        "tenant_id", "capabilities", "component_type",
        "multi_connection_policy", "rebind_policy", "fanout_count",
        "required_count", "subset_size",
    }),
    "capability": frozenset({
        "capabilities", "tenant_id", "component_type",
        "multi_connection_policy", "rebind_policy", "fanout_count",
        "required_count", "subset_size",
    }),
    "component_type": frozenset({
        "component_type", "tenant_id", "capabilities",
        "multi_connection_policy", "rebind_policy", "fanout_count",
        "required_count", "subset_size",
    }),
    "runtime": frozenset({
        "runtime_id", "tenant_id", "capabilities", "component_type",
        "multi_connection_policy", "rebind_policy", "fanout_count",
        "required_count", "subset_size",
    }),
    "broadcast": frozenset({
        "scope", "tenant_id", "capabilities", "component_type",
        "multi_connection_policy",
    }),
}
_TARGET_STRATEGIES = frozenset({
    "single", "all", "broadcast", "quorum", "all_required",
    "weighted_subset",
})
_TARGET_REBIND_POLICIES = frozenset({
    "fixed_connection", "same_identity", "same_capability", "same_tenant",
    "no_rebind_for_control",
})


def _validate_target_contract(target: TargetGroup) -> None:
    primary = _TARGET_PRIMARY_FIELD.get(target.kind)
    if primary is None:
        raise _schema_error("target", "kind", "unsupported_target_kind")
    if getattr(target, primary) is None:
        raise _schema_error("target", primary, "required_for_target_kind")
    values = {
        name: getattr(target, name)
        for name in (
            "connection_id", "connection_epoch", "identity", "tenant_id",
            "capabilities", "component_type", "runtime_id", "scope",
            "multi_connection_policy", "rebind_policy", "fanout_count",
            "required_count", "subset_size",
        )
    }
    unused = {
        name for name, value in values.items()
        if value is not None and name not in _TARGET_ALLOWED_FIELDS[target.kind]
    }
    if unused:
        raise _schema_error("target", "$combination", "field_not_allowed_for_kind")

    present_selectors = {
        name for name in _TARGET_SELECTOR_FIELDS
        if values.get(name) is not None
    }
    allowed_selector_constraints = {
        name for name in ("tenant_id", "capabilities", "component_type")
        if name in _TARGET_ALLOWED_FIELDS[target.kind]
    }
    conflicting = present_selectors - {primary} - allowed_selector_constraints
    if conflicting:
        raise _schema_error("target", "$selector", "multiple_primary_selectors")

    strategy = target.multi_connection_policy or "single"
    if strategy not in _TARGET_STRATEGIES:
        raise _schema_error("target", "multi_connection_policy", "unsupported_strategy")
    if target.rebind_policy is not None and target.rebind_policy not in _TARGET_REBIND_POLICIES:
        raise _schema_error("target", "rebind_policy", "unsupported_rebind_policy")
    if target.kind == "connection" and strategy != "single":
        raise _schema_error("target", "multi_connection_policy", "connection_requires_single")
    if target.kind == "broadcast":
        if target.scope != "tenant" or target.tenant_id is None:
            raise _schema_error("target", "scope", "tenant_broadcast_required")
        if target.multi_connection_policy != "broadcast":
            raise _schema_error("target", "multi_connection_policy", "broadcast_strategy_required")
        if target.rebind_policy is not None:
            raise _schema_error("target", "rebind_policy", "broadcast_rebind_forbidden")
    elif strategy == "broadcast":
        raise _schema_error("target", "multi_connection_policy", "broadcast_kind_required")

    if strategy == "quorum":
        if target.fanout_count is None or target.required_count is None:
            raise _schema_error("target", "fanout_count", "quorum_counts_required")
        if target.required_count > target.fanout_count:
            raise _schema_error("target", "required_count", "quorum_count_order")
        if target.subset_size is not None:
            raise _schema_error("target", "subset_size", "field_not_allowed_for_strategy")
    elif strategy == "weighted_subset":
        if target.subset_size is None:
            raise _schema_error("target", "subset_size", "subset_size_required")
        if target.fanout_count is not None or target.required_count is not None:
            raise _schema_error("target", "$strategy", "field_not_allowed_for_strategy")
    elif any(
        value is not None
        for value in (target.fanout_count, target.required_count, target.subset_size)
    ):
        raise _schema_error("target", "$strategy", "field_not_allowed_for_strategy")


@dataclass(frozen=True, slots=True)
class RouteGroup(StrictGroup):
    GROUP_NAME: ClassVar[str] = "route"
    root_runtime_id: str
    current_runtime_id: str
    hop: int
    max_hops: int
    previous_runtime_id: str | None = None
    next_runtime_id: str | None = None
    route_segment: tuple[str, ...] | list[str] | None = None
    routing_plan_id: str | None = None

    def __post_init__(self) -> None:
        for name in ("root_runtime_id", "current_runtime_id"):
            _require_string(self.GROUP_NAME, name, getattr(self, name))
        for name in ("previous_runtime_id", "next_runtime_id", "routing_plan_id"):
            _optional_string(self.GROUP_NAME, name, getattr(self, name))
        for name in ("hop", "max_hops"):
            _require_non_negative_integer(self.GROUP_NAME, name, getattr(self, name))
        if self.hop > self.max_hops:
            raise _schema_error(self.GROUP_NAME, "hop", "hop_exceeds_max_hops")
        if self.route_segment is not None:
            if not isinstance(self.route_segment, (list, tuple)):
                raise _schema_error(self.GROUP_NAME, "route_segment", "array_required")
            normalized = tuple(self.route_segment)
            if not normalized:
                raise _schema_error(self.GROUP_NAME, "route_segment", "non_empty_array_required")
            for item in normalized:
                _require_string(self.GROUP_NAME, "route_segment", item)
            object.__setattr__(self, "route_segment", normalized)


@dataclass(frozen=True, slots=True)
class DeliveryGroup(StrictGroup):
    GROUP_NAME: ClassVar[str] = "delivery"
    delivery_id: str
    attempt: int
    summary_id: str | None = None
    root_delivery_id: str | None = None
    parent_delivery_id: str | None = None
    ack_timeout_ms: int | None = None
    replay_epoch: int | None = None

    def __post_init__(self) -> None:
        _require_string(self.GROUP_NAME, "delivery_id", self.delivery_id)
        for name in ("summary_id", "root_delivery_id", "parent_delivery_id"):
            _optional_string(self.GROUP_NAME, name, getattr(self, name))
        _require_non_negative_integer(self.GROUP_NAME, "attempt", self.attempt)
        for name in ("ack_timeout_ms", "replay_epoch"):
            _optional_non_negative_integer(self.GROUP_NAME, name, getattr(self, name))


@dataclass(frozen=True, slots=True)
class StreamGroup(StrictGroup):
    GROUP_NAME: ClassVar[str] = "stream"
    stream_id: str
    sequence: int | None = None
    ack_sequence: int | None = None
    ack_ranges: tuple[tuple[int, int], ...] | list[list[int]] | None = None
    missing_sequences: tuple[int, ...] | list[int] | None = None
    received_sequences: tuple[int, ...] | list[int] | None = None
    end_reason: str | None = None

    def __post_init__(self) -> None:
        _require_string(self.GROUP_NAME, "stream_id", self.stream_id)
        for name in ("sequence", "ack_sequence"):
            _optional_non_negative_integer(self.GROUP_NAME, name, getattr(self, name))
        _optional_string(self.GROUP_NAME, "end_reason", self.end_reason)
        for name in ("missing_sequences", "received_sequences"):
            value = getattr(self, name)
            if value is not None:
                if not isinstance(value, (list, tuple)):
                    raise _schema_error(self.GROUP_NAME, name, "array_required")
                normalized = tuple(value)
                for item in normalized:
                    _require_non_negative_integer(self.GROUP_NAME, name, item)
                object.__setattr__(self, name, normalized)
        if self.ack_ranges is not None:
            if not isinstance(self.ack_ranges, (list, tuple)):
                raise _schema_error(
                    self.GROUP_NAME,
                    "ack_ranges",
                    "array_required",
                )
            normalized_ranges: list[tuple[int, int]] = []
            for item in self.ack_ranges:
                if not isinstance(item, (list, tuple)) or len(item) != 2:
                    raise _schema_error(self.GROUP_NAME, "ack_ranges", "integer_pair_required")
                start, end = item
                _require_non_negative_integer(self.GROUP_NAME, "ack_ranges", start)
                _require_non_negative_integer(self.GROUP_NAME, "ack_ranges", end)
                if start > end:
                    raise _schema_error(self.GROUP_NAME, "ack_ranges", "invalid_range")
                normalized_ranges.append((start, end))
            object.__setattr__(self, "ack_ranges", tuple(normalized_ranges))


@dataclass(frozen=True, slots=True)
class AuthContextGroup(StrictGroup):
    GROUP_NAME: ClassVar[str] = "auth_context"
    permission_snapshot_ref: str
    permission_digest: str
    iam_mode: str
    issued_at: str
    expires_at: str

    def __post_init__(self) -> None:
        for definition in fields(self):
            _require_string(self.GROUP_NAME, definition.name, getattr(self, definition.name))


@dataclass(frozen=True, slots=True)
class PayloadGroup(StrictGroup):
    GROUP_NAME: ClassVar[str] = "payload"
    mode: str
    inline: JSONValue | None = None
    payload_ref: Mapping[str, JSONValue] | None = None
    content_type: str | None = None
    size_bytes: int | None = None
    checksum: str | None = None
    version: str | None = None

    def __post_init__(self) -> None:
        if self.mode not in {"inline", "reference"}:
            raise _schema_error(self.GROUP_NAME, "mode", "unsupported_payload_mode")
        if (self.inline is None) == (self.payload_ref is None):
            raise _schema_error(self.GROUP_NAME, "mode", "exactly_one_payload_value_required")
        if self.mode == "inline" and self.inline is None:
            raise _schema_error(self.GROUP_NAME, "inline", "required_for_mode")
        if self.mode == "reference" and self.payload_ref is None:
            raise _schema_error(self.GROUP_NAME, "payload_ref", "required_for_mode")
        if self.inline is not None:
            object.__setattr__(self, "inline", _freeze_json(self.inline, group=self.GROUP_NAME, field="inline"))
        if self.payload_ref is not None:
            frozen = _freeze_json(self.payload_ref, group=self.GROUP_NAME, field="payload_ref")
            if not isinstance(frozen, Mapping) or not frozen:
                raise _schema_error(self.GROUP_NAME, "payload_ref", "non_empty_object_required")
            object.__setattr__(self, "payload_ref", frozen)
        for name in ("content_type", "checksum", "version"):
            _optional_string(self.GROUP_NAME, name, getattr(self, name))
        _optional_non_negative_integer(self.GROUP_NAME, "size_bytes", self.size_bytes)


@dataclass(frozen=True, slots=True)
class CallbackGroup(StrictGroup):
    GROUP_NAME: ClassVar[str] = "callback"
    mode: str
    message_type: str | None = None
    target: Mapping[str, JSONValue] | None = None

    def __post_init__(self) -> None:
        _require_string(self.GROUP_NAME, "mode", self.mode)
        _optional_string(self.GROUP_NAME, "message_type", self.message_type)
        if self.target is not None:
            frozen = _freeze_json(self.target, group=self.GROUP_NAME, field="target")
            if not isinstance(frozen, Mapping) or not frozen:
                raise _schema_error(self.GROUP_NAME, "target", "non_empty_object_required")
            object.__setattr__(self, "target", frozen)


@dataclass(frozen=True, slots=True)
class TraceGroup(StrictGroup):
    GROUP_NAME: ClassVar[str] = "trace"
    trace_id: str | None = None
    span_id: str | None = None
    parent_span_id: str | None = None
    correlation_id: str | None = None
    request_id: str | None = None

    def __post_init__(self) -> None:
        present = False
        for definition in fields(self):
            value = getattr(self, definition.name)
            _optional_string(self.GROUP_NAME, definition.name, value)
            present = present or value is not None
        if not present:
            raise _schema_error(self.GROUP_NAME, self.GROUP_NAME, "non_empty_object_required")


@dataclass(frozen=True, slots=True)
class ExtensionsGroup(StrictGroup):
    GROUP_NAME: ClassVar[str] = "extensions"
    namespaces: Mapping[str, JSONValue]

    def __post_init__(self) -> None:
        frozen = _freeze_json(self.namespaces, group=self.GROUP_NAME, field="namespaces")
        if not isinstance(frozen, Mapping) or not frozen:
            raise _schema_error(self.GROUP_NAME, "namespaces", "non_empty_object_required")
        object.__setattr__(self, "namespaces", frozen)

    @classmethod
    def from_mapping(cls, value: object) -> "ExtensionsGroup":
        if not isinstance(value, Mapping) or not value:
            raise _schema_error(cls.GROUP_NAME, cls.GROUP_NAME, "non_empty_object_required")
        return cls(namespaces=value)

    def to_dict(self) -> dict[str, Any]:
        return _thaw_json(self.namespaces)


@dataclass(frozen=True, slots=True)
class Envelope:
    protocol: ProtocolGroup
    message: MessageGroup
    source: SourceGroup | None = None
    target: TargetGroup | None = None
    route: RouteGroup | None = None
    delivery: DeliveryGroup | None = None
    stream: StreamGroup | None = None
    auth_context: AuthContextGroup | None = None
    payload: PayloadGroup | None = None
    callback: CallbackGroup | None = None
    trace: TraceGroup | None = None
    extensions: ExtensionsGroup | None = None

    def __post_init__(self) -> None:
        for name, expected_type in _ENVELOPE_GROUP_TYPES.items():
            value = getattr(self, name)
            if name in {"protocol", "message"} or value is not None:
                if not isinstance(value, expected_type):
                    raise _schema_error("envelope", name, "invalid_group_type")

    def to_dict(self) -> dict[str, Any]:
        return {
            name: value.to_dict()
            for name in _ENVELOPE_GROUP_TYPES
            if (value := getattr(self, name)) is not None
        }


_ENVELOPE_GROUP_TYPES: Mapping[str, type[StrictGroup]] = MappingProxyType({
    "protocol": ProtocolGroup,
    "message": MessageGroup,
    "source": SourceGroup,
    "target": TargetGroup,
    "route": RouteGroup,
    "delivery": DeliveryGroup,
    "stream": StreamGroup,
    "auth_context": AuthContextGroup,
    "payload": PayloadGroup,
    "callback": CallbackGroup,
    "trace": TraceGroup,
    "extensions": ExtensionsGroup,
})

ENVELOPE_GROUP_NAMES: tuple[str, ...] = tuple(_ENVELOPE_GROUP_TYPES)


def envelope_from_mapping(value: object) -> Envelope:
    if not isinstance(value, Mapping) or not value:
        raise _schema_error("envelope", "envelope", "non_empty_object_required")
    if any(key not in _ENVELOPE_GROUP_TYPES for key in value):
        raise _schema_error("envelope", "$unknown", "unknown_field")
    for required in ("protocol", "message"):
        if required not in value:
            raise _schema_error("envelope", required, "required_group_missing")
    return Envelope(**{
        name: group_type.from_mapping(group_value)
        for name, group_value in value.items()
        for group_type in (_ENVELOPE_GROUP_TYPES[name],)
    })


__all__ = (
    "AuthContextGroup", "CallbackGroup", "DeliveryGroup", "ENVELOPE_GROUP_NAMES",
    "Envelope", "ExtensionsGroup", "MessageGroup", "PayloadGroup", "ProtocolGroup",
    "RouteGroup", "SourceGroup", "StreamGroup", "TargetGroup", "TraceGroup",
    "envelope_from_mapping",
)
