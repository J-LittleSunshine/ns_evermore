# -*- coding: utf-8 -*-
"""Declarative base and message-type Envelope schema validation."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from ns_common.exceptions import NsRuntimeEnvelopeSchemaError

from .models import ENVELOPE_GROUP_NAMES, Envelope, PayloadGroup
from .extensions import ExtensionNamespaceRegistry


def _schema_error(group: str, field: str, reason: str) -> NsRuntimeEnvelopeSchemaError:
    return NsRuntimeEnvelopeSchemaError(
        "Runtime envelope schema validation failed.",
        details={"group": group, "field": field, "reason": reason},
    )


_TARGET_REQUIRED_FIELD: Mapping[str, str] = MappingProxyType({
    "connection": "connection_id",
    "identity": "identity",
    "tenant": "tenant_id",
    "capability": "capabilities",
    "component_type": "component_type",
    "runtime": "runtime_id",
    "broadcast": "scope",
})


@dataclass(frozen=True, slots=True)
class InlinePayloadSchema:
    required_fields: tuple[str, ...] = ()
    optional_fields: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_field_names(self.required_fields, "required_fields")
        _validate_field_names(self.optional_fields, "optional_fields")
        if set(self.required_fields) & set(self.optional_fields):
            raise ValueError("payload required and optional fields must be disjoint")

    @property
    def allowed_fields(self) -> frozenset[str]:
        return frozenset((*self.required_fields, *self.optional_fields))


@dataclass(frozen=True, slots=True)
class MessageTypeSchema:
    message_type: str
    required_groups: tuple[str, ...] = ()
    forbidden_groups: tuple[str, ...] = ()
    inline_payload: InlinePayloadSchema | None = None
    extension_registry: ExtensionNamespaceRegistry | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.message_type, str) or not self.message_type:
            raise ValueError("message_type must be a non-empty string")
        _validate_group_names(self.required_groups, "required_groups")
        _validate_group_names(self.forbidden_groups, "forbidden_groups")
        if set(self.required_groups) & set(self.forbidden_groups):
            raise ValueError("required and forbidden groups must be disjoint")
        if self.inline_payload is not None and not isinstance(
            self.inline_payload,
            InlinePayloadSchema,
        ):
            raise TypeError("inline_payload must be InlinePayloadSchema")
        if self.inline_payload is not None and "payload" not in self.required_groups:
            raise ValueError("inline payload schema requires the payload group")
        if self.extension_registry is not None and not isinstance(
            self.extension_registry,
            ExtensionNamespaceRegistry,
        ):
            raise TypeError("extension_registry must be ExtensionNamespaceRegistry")


class EnvelopeSchemaValidator:
    """Validate core invariants before one exact message schema overlay."""

    def validate(
        self,
        envelope: Envelope,
        *,
        message_schema: MessageTypeSchema,
    ) -> Envelope:
        if not isinstance(envelope, Envelope):
            raise _schema_error("envelope", "envelope", "normalized_envelope_required")
        if not isinstance(message_schema, MessageTypeSchema):
            raise _schema_error("message", "type", "message_schema_required")
        self._validate_base(envelope)
        self._validate_message(envelope, message_schema)
        return envelope

    @staticmethod
    def _validate_base(envelope: Envelope) -> None:
        target = envelope.target
        if target is not None:
            required_field = _TARGET_REQUIRED_FIELD.get(target.kind)
            if required_field is None:
                raise _schema_error("target", "kind", "unsupported_target_kind")
            if getattr(target, required_field) is None:
                raise _schema_error("target", required_field, "required_for_target_kind")
        route = envelope.route
        if route is not None and route.route_segment is not None:
            if len(set(route.route_segment)) != len(route.route_segment):
                raise _schema_error("route", "route_segment", "duplicate_route_segment")
        delivery = envelope.delivery
        if delivery is not None and delivery.attempt < 1:
            raise _schema_error("delivery", "attempt", "positive_integer_required")

    @staticmethod
    def _validate_message(
        envelope: Envelope,
        schema: MessageTypeSchema,
    ) -> None:
        if envelope.message.type != schema.message_type:
            raise _schema_error("message", "type", "message_schema_mismatch")
        for group in schema.required_groups:
            if getattr(envelope, group) is None:
                raise _schema_error(group, group, "required_group_missing")
        for group in schema.forbidden_groups:
            if getattr(envelope, group) is not None:
                raise _schema_error(group, group, "group_not_allowed")
        if schema.inline_payload is not None:
            _validate_inline_payload(envelope.payload, schema.inline_payload)
        if schema.extension_registry is not None:
            schema.extension_registry.validate(
                envelope.extensions,
                authorized_capabilities=frozenset(),
            )


def _validate_inline_payload(
    payload: PayloadGroup | None,
    schema: InlinePayloadSchema,
) -> None:
    if payload is None or payload.mode != "inline" or not isinstance(payload.inline, Mapping):
        raise _schema_error("payload", "inline", "inline_object_required")
    keys = set(payload.inline)
    missing = set(schema.required_fields) - keys
    if missing:
        raise _schema_error("payload", "$required", "message_field_missing")
    unknown = keys - schema.allowed_fields
    if unknown:
        raise _schema_error("payload", "$unknown", "message_field_not_allowed")


def _validate_field_names(names: tuple[str, ...], field_name: str) -> None:
    if not isinstance(names, tuple) or any(
        not isinstance(name, str) or not name for name in names
    ):
        raise TypeError(f"{field_name} must be a tuple of non-empty strings")
    if len(set(names)) != len(names):
        raise ValueError(f"{field_name} must not contain duplicates")


def _validate_group_names(names: tuple[str, ...], field_name: str) -> None:
    _validate_field_names(names, field_name)
    invalid = set(names) - set(ENVELOPE_GROUP_NAMES)
    if invalid:
        raise ValueError(f"{field_name} contains an unknown Envelope group")
    if {"protocol", "message"} & set(names):
        raise ValueError(f"{field_name} must not repeat mandatory base groups")


__all__ = (
    "EnvelopeSchemaValidator",
    "InlinePayloadSchema",
    "MessageTypeSchema",
)
