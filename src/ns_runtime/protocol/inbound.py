# -*- coding: utf-8 -*-
"""Inbound/raw and runtime-authoritative normalized Envelope boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ns_common.exceptions import (
    NsRuntimeAuthContextForgedError,
    NsRuntimeEnvelopeSchemaError,
    NsRuntimeSourceForgedError,
)

from .models import (
    AuthContextGroup,
    CallbackGroup,
    DeliveryGroup,
    Envelope,
    ExtensionsGroup,
    MessageGroup,
    PayloadGroup,
    ProtocolGroup,
    RouteGroup,
    SourceGroup,
    StreamGroup,
    TargetGroup,
    TraceGroup,
    envelope_from_mapping,
)


_INBOUND_GROUP_NAMES = (
    "protocol", "message", "target", "route", "delivery", "stream",
    "payload", "callback", "trace", "extensions",
)


def _inbound_error(field: str, reason: str) -> NsRuntimeEnvelopeSchemaError:
    return NsRuntimeEnvelopeSchemaError(
        "Inbound runtime envelope is invalid.",
        details={"group": "envelope", "field": field, "reason": reason},
    )


@dataclass(frozen=True, slots=True)
class InboundEnvelope:
    """Validated sender-controlled data before authority injection."""

    protocol: ProtocolGroup
    message: MessageGroup
    target: TargetGroup | None = None
    route: RouteGroup | None = None
    delivery: DeliveryGroup | None = None
    stream: StreamGroup | None = None
    payload: PayloadGroup | None = None
    callback: CallbackGroup | None = None
    trace: TraceGroup | None = None
    extensions: ExtensionsGroup | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            name: value.to_dict()
            for name in _INBOUND_GROUP_NAMES
            if (value := getattr(self, name)) is not None
        }


@dataclass(frozen=True, slots=True)
class RuntimeAuthority:
    """Already-established authority supplied by a later IAM/session layer.

    P03 validates only the typed injection boundary. It does not create,
    authenticate, refresh, or persist this authority.
    """

    source: SourceGroup
    auth_context: AuthContextGroup

    def __post_init__(self) -> None:
        if not isinstance(self.source, SourceGroup):
            raise _inbound_error("source", "runtime_source_type_required")
        if not isinstance(self.auth_context, AuthContextGroup):
            raise _inbound_error(
                "auth_context",
                "runtime_auth_context_type_required",
            )


def inbound_envelope_from_mapping(value: object) -> InboundEnvelope:
    """Validate sender-controlled groups and reject authority forgery first."""

    if not isinstance(value, Mapping) or not value:
        raise _inbound_error("envelope", "non_empty_object_required")
    if "source" in value:
        raise NsRuntimeSourceForgedError(
            details={
                "group": "envelope",
                "field": "source",
                "reason": "runtime_authority_only",
            }
        )
    if "auth_context" in value:
        raise NsRuntimeAuthContextForgedError(
            details={
                "group": "envelope",
                "field": "auth_context",
                "reason": "runtime_authority_only",
            }
        )
    unknown = set(value) - set(_INBOUND_GROUP_NAMES)
    if unknown:
        raise _inbound_error("$unknown", "unknown_field")

    parsed = envelope_from_mapping(value)
    return InboundEnvelope(
        protocol=parsed.protocol,
        message=parsed.message,
        target=parsed.target,
        route=parsed.route,
        delivery=parsed.delivery,
        stream=parsed.stream,
        payload=parsed.payload,
        callback=parsed.callback,
        trace=parsed.trace,
        extensions=parsed.extensions,
    )


def normalize_inbound(
    inbound: InboundEnvelope,
    *,
    authority: RuntimeAuthority,
) -> Envelope:
    """Inject authority without consulting globals or sender-controlled data."""

    if not isinstance(inbound, InboundEnvelope):
        raise _inbound_error("envelope", "inbound_model_required")
    if not isinstance(authority, RuntimeAuthority):
        raise _inbound_error("authority", "runtime_authority_required")
    return Envelope(
        protocol=inbound.protocol,
        message=inbound.message,
        source=authority.source,
        target=inbound.target,
        route=inbound.route,
        delivery=inbound.delivery,
        stream=inbound.stream,
        auth_context=authority.auth_context,
        payload=inbound.payload,
        callback=inbound.callback,
        trace=inbound.trace,
        extensions=inbound.extensions,
    )


__all__ = (
    "InboundEnvelope",
    "RuntimeAuthority",
    "inbound_envelope_from_mapping",
    "normalize_inbound",
)
