# -*- coding: utf-8 -*-
"""Controlled parsing of untrusted ``connection.hello`` claims."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Mapping

from ns_common.exceptions import NsRuntimeEnvelopeSchemaError, NsValidationError
from ns_common.identifiers import NsIdentifierKind, validate_identifier
from ns_runtime.protocol import (
    ExtensionNamespaceRegistry,
    CONNECTION_HELLO_EXTENSION_REGISTRY,
    CONNECTION_HELLO_RESUME_NAMESPACE,
    InboundEnvelope,
    ProtocolVersion,
)


HELLO_RESUME_NAMESPACE = CONNECTION_HELLO_RESUME_NAMESPACE
HELLO_EXTENSION_REGISTRY = CONNECTION_HELLO_EXTENSION_REGISTRY

_CAPABILITY_PATTERN = re.compile(
    r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+"
)
_COMPONENT_TYPES = frozenset({
    "frontend", "client", "node", "backend", "runtime", "management",
})


class HandshakeCredential:
    """Single-use credential storage limited to the handshake call stack."""

    __slots__ = ("_token",)

    def __init__(self, token: str) -> None:
        if not isinstance(token, str) or not token or len(token) > 65_536:
            _hello_error("token", "non_empty_bounded_string_required")
        self._token: str | None = token

    @property
    def available(self) -> bool:
        return self._token is not None

    def take(self) -> str:
        token = self._token
        if token is None:
            raise NsValidationError(
                "Handshake credential is unavailable.",
                details={
                    "component": "logical_connection",
                    "field": "credential",
                    "reason": "already_released",
                },
            )
        self._token = None
        return token

    def clear(self) -> None:
        self._token = None

    def __repr__(self) -> str:
        return "HandshakeCredential(redacted=True)"


@dataclass(frozen=True, slots=True, kw_only=True)
class HelloResumeRequest:
    connection_id: str = field(repr=False)
    connection_epoch: int
    session_id: str | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        validate_identifier(
            self.connection_id,
            expected_kind=NsIdentifierKind.CONNECTION_ID,
        )
        if (
            isinstance(self.connection_epoch, bool)
            or not isinstance(self.connection_epoch, int)
            or self.connection_epoch < 0
        ):
            _hello_error(
                "resume.connection_epoch",
                "non_negative_integer_required",
            )
        if self.session_id is not None:
            validate_identifier(
                self.session_id,
                expected_kind=NsIdentifierKind.SESSION_ID,
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class PendingHelloClaims:
    component_type: str
    requested_version: ProtocolVersion
    minimum_version: ProtocolVersion | None
    requested_capabilities: frozenset[str] = field(repr=False)
    resume: HelloResumeRequest | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.component_type not in _COMPONENT_TYPES:
            _hello_error("component_type", "unsupported_component_type")
        if not isinstance(self.requested_version, ProtocolVersion):
            _hello_error("requested_version", "protocol_version_required")
        if self.minimum_version is not None and not isinstance(
            self.minimum_version,
            ProtocolVersion,
        ):
            _hello_error("min_version", "protocol_version_required")
        if not isinstance(self.requested_capabilities, frozenset) or any(
            not isinstance(item, str)
            or _CAPABILITY_PATTERN.fullmatch(item) is None
            for item in self.requested_capabilities
        ):
            _hello_error(
                "requested_capabilities",
                "capability_set_required",
            )
        if self.resume is not None and not isinstance(
            self.resume,
            HelloResumeRequest,
        ):
            _hello_error("resume", "resume_request_required")


@dataclass(frozen=True, slots=True, kw_only=True, repr=False)
class ParsedHello:
    claims: PendingHelloClaims
    credential: HandshakeCredential

    def __post_init__(self) -> None:
        if not isinstance(self.claims, PendingHelloClaims):
            _hello_error("claims", "pending_claims_required")
        if not isinstance(self.credential, HandshakeCredential):
            _hello_error("credential", "handshake_credential_required")

    def __repr__(self) -> str:
        return "ParsedHello(redacted=True)"


class HelloClaimParser:
    """Convert one P03-validated hello into typed, non-authoritative claims."""

    def __init__(
        self,
        *,
        extension_registry: ExtensionNamespaceRegistry = HELLO_EXTENSION_REGISTRY,
    ) -> None:
        if not isinstance(extension_registry, ExtensionNamespaceRegistry):
            raise NsValidationError(
                "Hello extension registry is invalid.",
                details={
                    "component": "logical_connection",
                    "field": "extension_registry",
                },
            )
        self._extension_registry = extension_registry

    def parse(self, inbound: InboundEnvelope) -> ParsedHello:
        if not isinstance(inbound, InboundEnvelope):
            _hello_error("envelope", "inbound_envelope_required")
        if inbound.message.type != "connection.hello":
            _hello_error("message.type", "connection_hello_required")
        payload_group = inbound.payload
        if (
            payload_group is None
            or payload_group.mode != "inline"
            or not isinstance(payload_group.inline, Mapping)
        ):
            _hello_error("payload", "inline_object_required")
        payload = payload_group.inline

        token = payload.get("token")
        if not isinstance(token, str) or not token or len(token) > 65_536:
            _hello_error("token", "non_empty_bounded_string_required")
        credential = HandshakeCredential(token)
        del token
        try:
            component_type = payload.get("component_type")
            if not isinstance(component_type, str):
                _hello_error("component_type", "string_required")
            requested_raw = payload.get("requested_version")
            requested = ProtocolVersion.parse(requested_raw)
            envelope_requested = ProtocolVersion.from_group(inbound.protocol)
            if requested != envelope_requested:
                _hello_error(
                    "requested_version",
                    "protocol_group_mismatch",
                )
            minimum = self._minimum_version(payload, inbound=inbound)
            requested_capabilities = self._requested_capabilities(payload)
            resume = self._resume_request(inbound)
            return ParsedHello(
                claims=PendingHelloClaims(
                    component_type=component_type,
                    requested_version=requested,
                    minimum_version=minimum,
                    requested_capabilities=requested_capabilities,
                    resume=resume,
                ),
                credential=credential,
            )
        except BaseException:
            credential.clear()
            raise

    @staticmethod
    def _minimum_version(
        payload: Mapping[str, object],
        *,
        inbound: InboundEnvelope,
    ) -> ProtocolVersion | None:
        payload_raw = payload.get("min_version")
        group_raw = inbound.protocol.min_version
        payload_minimum = (
            ProtocolVersion.parse(payload_raw)
            if payload_raw is not None
            else None
        )
        group_minimum = (
            ProtocolVersion.parse(group_raw)
            if group_raw is not None
            else None
        )
        if (
            payload_minimum is not None
            and group_minimum is not None
            and payload_minimum != group_minimum
        ):
            _hello_error("min_version", "protocol_group_mismatch")
        return payload_minimum or group_minimum

    @staticmethod
    def _requested_capabilities(
        payload: Mapping[str, object],
    ) -> frozenset[str]:
        raw = payload.get("requested_capabilities", ())
        if not isinstance(raw, tuple):
            _hello_error("requested_capabilities", "array_required")
        if any(
            not isinstance(item, str)
            or _CAPABILITY_PATTERN.fullmatch(item) is None
            for item in raw
        ):
            _hello_error(
                "requested_capabilities",
                "capability_name_invalid",
            )
        if len(set(raw)) != len(raw):
            _hello_error(
                "requested_capabilities",
                "duplicate_capability",
            )
        return frozenset(raw)

    def _resume_request(
        self,
        inbound: InboundEnvelope,
    ) -> HelloResumeRequest | None:
        validation = self._extension_registry.validate(
            inbound.extensions,
            authorized_capabilities=frozenset(),
        )
        raw = validation.accepted.get(HELLO_RESUME_NAMESPACE)
        if raw is None:
            return None
        connection_id = raw.get("connection_id")
        connection_epoch = raw.get("connection_epoch")
        session_id = raw.get("session_id")
        return HelloResumeRequest(
            connection_id=connection_id,  # type: ignore[arg-type]
            connection_epoch=connection_epoch,  # type: ignore[arg-type]
            session_id=session_id,  # type: ignore[arg-type]
        )


def _hello_error(field_name: str, reason: str) -> None:
    raise NsRuntimeEnvelopeSchemaError(
        "Runtime connection hello is invalid.",
        details={
            "group": "connection.hello",
            "field": field_name,
            "reason": reason,
        },
    )


__all__ = (
    "HELLO_EXTENSION_REGISTRY",
    "HELLO_RESUME_NAMESPACE",
    "HandshakeCredential",
    "HelloClaimParser",
    "HelloResumeRequest",
    "ParsedHello",
    "PendingHelloClaims",
)
