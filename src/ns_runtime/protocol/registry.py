# -*- coding: utf-8 -*-
"""Explicit, immutable registry of built-in runtime message contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Iterable, Mapping

from ns_common.exceptions import NsRuntimeUnsupportedMessageTypeError

from .schema import InlinePayloadSchema, MessageTypeSchema


CURRENT_PROTOCOL_SCHEMA_KEY = "json.v1/protocol-1.0"

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


@dataclass(frozen=True, slots=True)
class MessageTypeContract:
    message_type: str
    family: str
    schemas: Mapping[str, MessageTypeSchema]

    def __post_init__(self) -> None:
        if not isinstance(self.message_type, str) or not self.message_type:
            raise ValueError("message_type must be a non-empty string")
        if self.family not in BUILTIN_MESSAGE_FAMILIES:
            raise ValueError("family must be a registered built-in family")
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


def _contract(
    message_type: str,
    family: str,
    *,
    required_groups: tuple[str, ...] = (),
    forbidden_groups: tuple[str, ...] = (),
    payload_required: tuple[str, ...] | None = None,
    payload_optional: tuple[str, ...] = (),
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
    )
    return MessageTypeContract(
        message_type=message_type,
        family=family,
        schemas={CURRENT_PROTOCOL_SCHEMA_KEY: schema},
    )


BUILTIN_MESSAGE_CONTRACTS: tuple[MessageTypeContract, ...] = (
    _contract(
        "connection.hello", "connection", required_groups=("payload",),
        forbidden_groups=("delivery", "stream", "route"),
        payload_required=("token", "component_type", "requested_version"),
        payload_optional=("min_version", "requested_capabilities"),
    ),
    _contract("connection.accepted", "connection", required_groups=("payload",)),
    _contract("connection.rejected", "connection", required_groups=("payload",)),
    _contract("connection.reauth", "connection", required_groups=("payload",)),
    _contract("connection.reauth_accepted", "connection", required_groups=("payload",)),
    _contract("connection.reauth_rejected", "connection", required_groups=("payload",)),
    _contract("connection.heartbeat", "connection"),
    _contract("connection.heartbeat_ack", "connection"),
    _contract("connection.drain", "connection"),
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
    _contract("runtime.error", "runtime.error", required_groups=("payload",)),
)

BUILTIN_MESSAGE_REGISTRY = MessageTypeRegistry(BUILTIN_MESSAGE_CONTRACTS)


__all__ = (
    "BUILTIN_MESSAGE_CONTRACTS",
    "BUILTIN_MESSAGE_FAMILIES",
    "BUILTIN_MESSAGE_REGISTRY",
    "CURRENT_PROTOCOL_SCHEMA_KEY",
    "MessageTypeContract",
    "MessageTypeRegistry",
)
