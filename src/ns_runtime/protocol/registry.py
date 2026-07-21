# -*- coding: utf-8 -*-
"""Explicit, immutable registry of built-in runtime message contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Iterable, Mapping

from ns_common.exceptions import NsRuntimeUnsupportedMessageTypeError

from .schema import InlinePayloadSchema, MessageTypeSchema
from .schema import EnvelopeSchemaValidator
from .extensions import (
    ExtensionNamespaceContract,
    ExtensionNamespaceRegistry,
    ExtensionObjectSchema,
)


CURRENT_PROTOCOL_SCHEMA_KEY = "json.v1/protocol-1.0"
CONNECTION_HELLO_RESUME_NAMESPACE = "ns.connection_resume"
CONNECTION_HELLO_EXTENSION_REGISTRY = ExtensionNamespaceRegistry((
    ExtensionNamespaceContract(
        namespace=CONNECTION_HELLO_RESUME_NAMESPACE,
        schema=ExtensionObjectSchema(
            required_fields=("connection_id", "connection_epoch"),
            optional_fields=("session_id",),
        ),
        enabled=True,
    ),
))

BUILTIN_MESSAGE_FAMILIES: tuple[str, ...] = (
    "connection",
    "task",
    "delivery",
    "stream",
    "runtime.control",
    "cluster.event",
    "config",
    "dead_letter",
    "replay",
    "cancel",
    "hold",
    "status",
    "runtime.error",
)


class MessageCategory(str, Enum):
    CONNECTION = "connection"
    TASK = "task"
    DELIVERY = "delivery"
    STREAM = "stream"
    CONTROL = "control"
    CLUSTER = "cluster"
    CONFIG = "config"
    MANAGEMENT = "management"
    ERROR = "error"


class MessageReliability(str, Enum):
    BEST_EFFORT = "best_effort"
    RELIABLE = "reliable"


class MessageAuditLevel(str, Enum):
    NONE = "none"
    STANDARD = "standard"
    SECURITY = "security"


class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


@dataclass(frozen=True, slots=True)
class MessageTypeContract:
    message_type: str
    family: str
    schemas: Mapping[str, MessageTypeSchema]
    category: MessageCategory
    default_reliability: MessageReliability
    required_capabilities: tuple[str, ...]
    processor_key: str
    audit_level: MessageAuditLevel
    direction: MessageDirection
    feature_flag: str
    feature_enabled: bool
    response_types: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.message_type, str) or not self.message_type:
            raise ValueError("message_type must be a non-empty string")
        if self.family not in BUILTIN_MESSAGE_FAMILIES:
            raise ValueError("family must be a registered built-in family")
        if not isinstance(self.category, MessageCategory):
            raise TypeError("category must be MessageCategory")
        if not isinstance(self.default_reliability, MessageReliability):
            raise TypeError("default_reliability must be MessageReliability")
        _validate_string_tuple(self.required_capabilities, "required_capabilities")
        _validate_string_tuple(self.response_types, "response_types")
        for name in ("processor_key", "feature_flag"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.audit_level, MessageAuditLevel):
            raise TypeError("audit_level must be MessageAuditLevel")
        if not isinstance(self.direction, MessageDirection):
            raise TypeError("direction must be MessageDirection")
        if type(self.feature_enabled) is not bool:
            raise TypeError("feature_enabled must be a boolean")
        if not isinstance(self.schemas, Mapping) or not self.schemas:
            raise ValueError("schemas must be a non-empty mapping")
        frozen: dict[str, MessageTypeSchema] = {}
        for schema_key, schema in self.schemas.items():
            if not isinstance(schema_key, str) or not schema_key:
                raise ValueError("schema key must be a non-empty string")
            if not isinstance(schema, MessageTypeSchema):
                raise TypeError("schema must be MessageTypeSchema")
            if schema.message_type != self.message_type:
                raise ValueError("schema message type must match contract")
            frozen[schema_key] = schema
        object.__setattr__(self, "schemas", MappingProxyType(frozen))

    def schema_for(self, schema_key: str) -> MessageTypeSchema:
        schema = self.schemas.get(schema_key)
        if schema is None:
            raise NsRuntimeUnsupportedMessageTypeError(
                details={"component": "message_registry", "reason": "schema_not_registered"},
            )
        return schema

    def metadata_dict(self) -> dict[str, object]:
        return {
            "message_type": self.message_type,
            "family": self.family,
            "schema_keys": tuple(self.schemas),
            "category": self.category.value,
            "default_reliability": self.default_reliability.value,
            "required_capabilities": self.required_capabilities,
            "processor_key": self.processor_key,
            "audit_level": self.audit_level.value,
            "direction": self.direction.value,
            "feature_flag": self.feature_flag,
            "feature_enabled": self.feature_enabled,
            "response_types": self.response_types,
        }


@dataclass(frozen=True, slots=True, init=False)
class MessageTypeRegistry:
    _contracts: tuple[MessageTypeContract, ...] = field(repr=False)
    _by_type: Mapping[str, MessageTypeContract] = field(repr=False)

    def __init__(self, contracts: Iterable[MessageTypeContract]) -> None:
        values = tuple(contracts)
        by_type: dict[str, MessageTypeContract] = {}
        for contract in values:
            if not isinstance(contract, MessageTypeContract):
                raise TypeError("registry entries must be MessageTypeContract")
            if contract.message_type in by_type:
                raise ValueError("message types must be unique")
            by_type[contract.message_type] = contract
        object.__setattr__(self, "_contracts", values)
        object.__setattr__(self, "_by_type", MappingProxyType(by_type))

    @property
    def contracts(self) -> tuple[MessageTypeContract, ...]:
        return self._contracts

    def get(self, message_type: str) -> MessageTypeContract | None:
        return self._by_type.get(message_type)

    def require(self, message_type: str) -> MessageTypeContract:
        contract = self.get(message_type)
        if contract is None:
            raise NsRuntimeUnsupportedMessageTypeError(
                details={"component": "message_registry", "reason": "message_type_not_registered"},
            )
        return contract

    def schema_for(self, message_type: str, schema_key: str) -> MessageTypeSchema:
        return self.require(message_type).schema_for(schema_key)

    def validate_envelope(self, envelope: object, schema_key: str):
        from .models import Envelope

        if not isinstance(envelope, Envelope):
            raise TypeError("envelope must be Envelope")
        contract = self.require(envelope.message.type)
        if envelope.message.category != contract.category.value:
            from ns_common.exceptions import NsRuntimeEnvelopeSchemaError

            raise NsRuntimeEnvelopeSchemaError(
                "Runtime message category does not match its registration.",
                details={
                    "group": "message",
                    "field": "category",
                    "reason": "registered_category_mismatch",
                },
            )
        if envelope.message.reliability not in {
            reliability.value for reliability in MessageReliability
        }:
            from ns_common.exceptions import NsRuntimeEnvelopeSchemaError

            raise NsRuntimeEnvelopeSchemaError(
                "Runtime message reliability is invalid.",
                details={
                    "group": "message",
                    "field": "reliability",
                    "reason": "unsupported_reliability",
                },
            )
        return EnvelopeSchemaValidator().validate(
            envelope,
            message_schema=contract.schema_for(schema_key),
        )


def _contract(
    message_type: str,
    family: str,
    *,
    required_groups: tuple[str, ...] = (),
    forbidden_groups: tuple[str, ...] = (),
    payload_required: tuple[str, ...] | None = None,
    payload_optional: tuple[str, ...] = (),
    extension_registry: ExtensionNamespaceRegistry | None = None,
) -> MessageTypeContract:
    inline_payload = (
        None
        if payload_required is None
        else InlinePayloadSchema(
            required_fields=payload_required,
            optional_fields=payload_optional,
        )
    )
    schema = MessageTypeSchema(
        message_type=message_type,
        required_groups=required_groups,
        forbidden_groups=forbidden_groups,
        inline_payload=inline_payload,
        extension_registry=extension_registry,
    )
    return MessageTypeContract(
        message_type=message_type,
        family=family,
        schemas={CURRENT_PROTOCOL_SCHEMA_KEY: schema},
        category=_CATEGORY_BY_FAMILY[family],
        default_reliability=_default_reliability(message_type, family),
        required_capabilities=_required_capabilities(message_type, family),
        processor_key=message_type,
        audit_level=_audit_level(message_type, family),
        direction=_DIRECTION_BY_TYPE.get(
            message_type,
            MessageDirection.BIDIRECTIONAL,
        ),
        feature_flag=_FEATURE_FLAG_BY_FAMILY[family],
        feature_enabled=message_type in _ENABLED_MESSAGE_TYPES,
        response_types=_RESPONSE_TYPES.get(message_type, ()),
    )


_CATEGORY_BY_FAMILY: Mapping[str, MessageCategory] = MappingProxyType({
    "connection": MessageCategory.CONNECTION,
    "task": MessageCategory.TASK,
    "delivery": MessageCategory.DELIVERY,
    "stream": MessageCategory.STREAM,
    "runtime.control": MessageCategory.CONTROL,
    "cluster.event": MessageCategory.CLUSTER,
    "config": MessageCategory.CONFIG,
    "dead_letter": MessageCategory.MANAGEMENT,
    "replay": MessageCategory.MANAGEMENT,
    "cancel": MessageCategory.MANAGEMENT,
    "hold": MessageCategory.MANAGEMENT,
    "status": MessageCategory.MANAGEMENT,
    "runtime.error": MessageCategory.ERROR,
})

_FEATURE_FLAG_BY_FAMILY: Mapping[str, str] = MappingProxyType({
    family: (
        "protocol.error_envelope"
        if family == "runtime.error"
        else f"message_family.{family}"
    )
    for family in BUILTIN_MESSAGE_FAMILIES
})

_RESPONSE_TYPES: Mapping[str, tuple[str, ...]] = MappingProxyType({
    "connection.hello": ("connection.accepted", "connection.rejected"),
    "connection.reauth": ("connection.reauth_accepted", "connection.reauth_rejected"),
    "connection.heartbeat": ("connection.heartbeat_ack",),
    "task.dispatch": ("delivery.accepted", "delivery.rejected", "delivery.duplicate"),
    "runtime.control.health": ("status.result", "runtime.error"),
    "dead_letter.query": ("dead_letter.result", "runtime.error"),
    "dead_letter.cleanup": ("dead_letter.cleanup_result", "runtime.error"),
    "replay.request": ("replay.result", "runtime.error"),
    "cancel.request": ("cancel.result", "runtime.error"),
    "hold.request": ("hold.result", "runtime.error"),
    "hold.release": ("hold.result", "runtime.error"),
    "status.query": ("status.result", "runtime.error"),
    "config.update": ("config.updated", "config.rejected", "runtime.error"),
})

_P05_CONNECTION_MESSAGE_TYPES = frozenset({
    "connection.hello",
    "connection.accepted",
    "connection.rejected",
    "connection.reauth",
    "connection.reauth_accepted",
    "connection.reauth_rejected",
    "connection.heartbeat",
    "connection.heartbeat_ack",
    "connection.drain",
})
_ENABLED_MESSAGE_TYPES = frozenset({
    *_P05_CONNECTION_MESSAGE_TYPES,
    "runtime.error",
})
_DIRECTION_BY_TYPE: Mapping[str, MessageDirection] = MappingProxyType({
    "connection.hello": MessageDirection.INBOUND,
    "connection.accepted": MessageDirection.OUTBOUND,
    "connection.rejected": MessageDirection.OUTBOUND,
    "connection.reauth": MessageDirection.INBOUND,
    "connection.reauth_accepted": MessageDirection.OUTBOUND,
    "connection.reauth_rejected": MessageDirection.OUTBOUND,
    "connection.heartbeat": MessageDirection.INBOUND,
    "connection.heartbeat_ack": MessageDirection.OUTBOUND,
    "connection.drain": MessageDirection.INBOUND,
    "runtime.error": MessageDirection.OUTBOUND,
})


def _default_reliability(message_type: str, family: str) -> MessageReliability:
    if message_type in {
        "connection.hello", "connection.accepted", "connection.rejected",
        "connection.reauth", "connection.reauth_accepted", "connection.reauth_rejected",
        "connection.heartbeat", "connection.heartbeat_ack", "runtime.control.health",
        "runtime.error",
    }:
        return MessageReliability.BEST_EFFORT
    return MessageReliability.RELIABLE


def _required_capabilities(message_type: str, family: str) -> tuple[str, ...]:
    if message_type in _P05_CONNECTION_MESSAGE_TYPES:
        return ()
    if family == "connection":
        return ("runtime.connection",)
    if family == "task":
        return ("runtime.task.send",)
    if family == "delivery":
        return ("runtime.delivery.respond",)
    if family == "stream":
        return ("runtime.stream.send",)
    if family == "cluster.event":
        return ("runtime.cluster.event",)
    if family == "runtime.error":
        return ()
    return ("runtime.management",)


def _audit_level(message_type: str, family: str) -> MessageAuditLevel:
    if message_type in {"connection.heartbeat", "connection.heartbeat_ack"}:
        return MessageAuditLevel.NONE
    if message_type in {"connection.hello", "connection.reauth", "connection.rejected"}:
        return MessageAuditLevel.SECURITY
    if family in {
        "runtime.control", "cluster.event", "config", "dead_letter",
        "replay", "cancel", "hold",
    }:
        return MessageAuditLevel.SECURITY
    return MessageAuditLevel.STANDARD


def _validate_string_tuple(value: tuple[str, ...], field_name: str) -> None:
    if not isinstance(value, tuple) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise TypeError(f"{field_name} must be a tuple of non-empty strings")
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must not contain duplicates")


BUILTIN_MESSAGE_CONTRACTS: tuple[MessageTypeContract, ...] = (
    _contract(
        "connection.hello", "connection", required_groups=("payload",),
        forbidden_groups=(
            "source", "target", "route", "delivery", "stream",
            "auth_context", "callback", "trace",
        ),
        payload_required=("token", "component_type", "requested_version"),
        payload_optional=("min_version", "requested_capabilities"),
        extension_registry=CONNECTION_HELLO_EXTENSION_REGISTRY,
    ),
    _contract(
        "connection.accepted", "connection", required_groups=("payload",),
        forbidden_groups=(
            "source", "target", "route", "delivery", "stream",
            "auth_context", "callback", "trace", "extensions",
        ),
        payload_required=(
            "connection_id", "session_id", "protocol_version", "heartbeat",
            "session_expires_at", "server_time", "runtime_id", "role",
        ),
    ),
    _contract(
        "connection.rejected", "connection", required_groups=("payload",),
        forbidden_groups=(
            "source", "target", "route", "delivery", "stream",
            "auth_context", "callback", "trace", "extensions",
        ),
        payload_required=("reason", "server_time", "retryable"),
    ),
    _contract(
        "connection.reauth", "connection", required_groups=("payload",),
        forbidden_groups=(
            "source", "target", "route", "delivery", "stream",
            "auth_context", "callback", "trace", "extensions",
        ),
        payload_required=("token",),
        payload_optional=("requested_capabilities",),
    ),
    _contract(
        "connection.reauth_accepted", "connection", required_groups=("payload",),
        forbidden_groups=(
            "source", "target", "route", "delivery", "stream",
            "auth_context", "callback", "trace", "extensions",
        ),
        payload_required=(
            "session_id", "connection_epoch", "session_expires_at",
            "server_time", "capabilities_changed",
        ),
    ),
    _contract(
        "connection.reauth_rejected", "connection", required_groups=("payload",),
        forbidden_groups=(
            "source", "target", "route", "delivery", "stream",
            "auth_context", "callback", "trace", "extensions",
        ),
        payload_required=("reason", "server_time", "connection_closing"),
    ),
    _contract(
        "connection.heartbeat", "connection", required_groups=("payload",),
        forbidden_groups=(
            "source", "target", "route", "delivery", "stream",
            "auth_context", "callback", "trace", "extensions",
        ),
        payload_required=(
            "connection_id", "session_id", "connection_epoch", "sequence",
            "sent_at",
        ),
    ),
    _contract(
        "connection.heartbeat_ack", "connection", required_groups=("payload",),
        forbidden_groups=(
            "source", "target", "route", "delivery", "stream",
            "auth_context", "callback", "trace", "extensions",
        ),
        payload_required=(
            "connection_id", "session_id", "connection_epoch", "sequence",
            "server_time",
        ),
    ),
    _contract(
        "connection.drain", "connection",
        forbidden_groups=(
            "source", "target", "route", "delivery", "stream",
            "auth_context", "payload", "callback", "trace", "extensions",
        ),
    ),
    _contract("task.dispatch", "task", required_groups=("target", "payload")),
    _contract("task.result", "task", required_groups=("target", "payload")),
    _contract("task.callback", "task", required_groups=("target", "payload")),
    _contract("delivery.accepted", "delivery", required_groups=("payload",)),
    _contract("delivery.rejected", "delivery", required_groups=("payload",)),
    _contract("delivery.duplicate", "delivery", required_groups=("payload",)),
    _contract("delivery.ack", "delivery", required_groups=("delivery",)),
    _contract("delivery.nack", "delivery", required_groups=("delivery", "payload")),
    _contract("delivery.defer", "delivery", required_groups=("delivery", "payload")),
    _contract("stream.start", "stream", required_groups=("stream", "target")),
    _contract("stream.chunk", "stream", required_groups=("stream", "payload")),
    _contract("stream.end", "stream", required_groups=("stream",)),
    _contract("runtime.control.health", "runtime.control"),
    _contract("runtime.control.kick_connection", "runtime.control", required_groups=("payload",)),
    _contract("runtime.control.drain_node", "runtime.control", required_groups=("payload",)),
    _contract("runtime.control.switch_master", "runtime.control", required_groups=("payload",)),
    _contract("runtime.control.isolate_node", "runtime.control", required_groups=("payload",)),
    _contract("runtime.control.recover_node", "runtime.control", required_groups=("payload",)),
    _contract("cluster.event.node_joined", "cluster.event", required_groups=("payload",)),
    _contract("cluster.event.node_left", "cluster.event", required_groups=("payload",)),
    _contract("cluster.event.role_changed", "cluster.event", required_groups=("payload",)),
    _contract("cluster.event.health_changed", "cluster.event", required_groups=("payload",)),
    _contract("cluster.event.config_drift", "cluster.event", required_groups=("payload",)),
    _contract("cluster.event.leader_changed", "cluster.event", required_groups=("payload",)),
    _contract("config.update", "config", required_groups=("payload",)),
    _contract("config.updated", "config", required_groups=("payload",)),
    _contract("config.rejected", "config", required_groups=("payload",)),
    _contract("dead_letter.query", "dead_letter", required_groups=("payload",)),
    _contract("dead_letter.result", "dead_letter", required_groups=("payload",)),
    _contract("dead_letter.cleanup", "dead_letter", required_groups=("payload",)),
    _contract("dead_letter.cleanup_result", "dead_letter", required_groups=("payload",)),
    _contract("replay.request", "replay", required_groups=("payload",)),
    _contract("replay.result", "replay", required_groups=("payload",)),
    _contract("cancel.request", "cancel", required_groups=("payload",)),
    _contract("cancel.result", "cancel", required_groups=("payload",)),
    _contract("hold.request", "hold", required_groups=("payload",)),
    _contract("hold.release", "hold", required_groups=("payload",)),
    _contract("hold.result", "hold", required_groups=("payload",)),
    _contract("status.query", "status", required_groups=("payload",)),
    _contract("status.result", "status", required_groups=("payload",)),
    _contract(
        "runtime.error", "runtime.error", required_groups=("payload",),
        payload_required=(
            "error_code", "numeric_code", "message", "severity", "category",
            "retryable", "disconnect_required", "audit_required", "action", "detail",
        ),
        payload_optional=("message_id", "delivery_id"),
    ),
)

BUILTIN_MESSAGE_REGISTRY = MessageTypeRegistry(BUILTIN_MESSAGE_CONTRACTS)


__all__ = (
    "BUILTIN_MESSAGE_CONTRACTS",
    "BUILTIN_MESSAGE_FAMILIES",
    "BUILTIN_MESSAGE_REGISTRY",
    "CURRENT_PROTOCOL_SCHEMA_KEY",
    "CONNECTION_HELLO_EXTENSION_REGISTRY",
    "CONNECTION_HELLO_RESUME_NAMESPACE",
    "MessageAuditLevel",
    "MessageCategory",
    "MessageDirection",
    "MessageReliability",
    "MessageTypeContract",
    "MessageTypeRegistry",
)
