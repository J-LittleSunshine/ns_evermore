# -*- coding: utf-8 -*-
"""SC-1 session context and explicit handshake negotiation policy."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Iterable, Mapping

from ns_common.exceptions import (
    NsRuntimeIamDeniedError,
    NsRuntimeProtocolVersionError,
    NsRuntimeTransportCapabilityUnavailableError,
    NsValidationError,
)
from ns_common.identifiers import NsIdentifierKind, validate_identifier
from ns_common.time import Clock
from ns_runtime.protocol import (
    JSON_V1_PROTOCOL_MATRIX,
    NegotiatedProtocol,
    ProtocolCompatibilityMatrix,
    ProtocolVersion,
    WIRE_CODEC_JSON_V1,
)
from ns_runtime.transport import (
    TransportCapability,
    TransportSession,
)

from .hello import PendingHelloClaims
from .iam import HandshakeIamAuthority
from .state import LogicalConnectionState


@dataclass(frozen=True, slots=True, kw_only=True)
class LogicalSessionIdentity:
    connection_id: str = field(repr=False)
    session_id: str = field(repr=False)
    connection_epoch: int = 0

    def __post_init__(self) -> None:
        validate_identifier(
            self.connection_id,
            expected_kind=NsIdentifierKind.CONNECTION_ID,
        )
        validate_identifier(
            self.session_id,
            expected_kind=NsIdentifierKind.SESSION_ID,
        )
        if (
            isinstance(self.connection_epoch, bool)
            or not isinstance(self.connection_epoch, int)
            or self.connection_epoch < 0
        ):
            _invalid("connection_epoch")


@dataclass(frozen=True, slots=True, kw_only=True)
class SessionContext:
    """Deeply immutable authority used after one successful handshake."""

    connection_id: str = field(repr=False)
    session_id: str = field(repr=False)
    connection_epoch: int
    identity: str = field(repr=False)
    tenant_id: str = field(repr=False)
    component_type: str
    protocol_version: ProtocolVersion
    protocol_schema_key: str
    wire_codec: str
    capabilities: frozenset[str] = field(repr=False)
    permission_snapshot_ref: str = field(repr=False)
    permission_digest: str = field(repr=False)
    permission_version: str = field(repr=False)
    iam_mode: str
    authorization_issued_at: datetime
    session_expires_at: datetime
    resume_eligible: bool
    established_state: LogicalConnectionState
    created_at: datetime

    def __post_init__(self) -> None:
        identity = LogicalSessionIdentity(
            connection_id=self.connection_id,
            session_id=self.session_id,
            connection_epoch=self.connection_epoch,
        )
        object.__setattr__(self, "connection_id", identity.connection_id)
        object.__setattr__(self, "session_id", identity.session_id)
        for name in (
            "identity", "tenant_id", "component_type", "protocol_schema_key",
            "permission_snapshot_ref", "permission_digest", "permission_version",
            "iam_mode",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                _invalid(name)
        if not isinstance(self.protocol_version, ProtocolVersion):
            _invalid("protocol_version")
        if self.wire_codec != WIRE_CODEC_JSON_V1:
            _invalid("wire_codec")
        if not isinstance(self.capabilities, frozenset) or any(
            not isinstance(item, str) or not item
            for item in self.capabilities
        ):
            _invalid("capabilities")
        if not isinstance(self.resume_eligible, bool):
            _invalid("resume_eligible")
        if self.established_state is not LogicalConnectionState.AUTHENTICATED:
            _invalid("established_state")
        issued = _utc(self.authorization_issued_at, "authorization_issued_at")
        expires = _utc(self.session_expires_at, "session_expires_at")
        created = _utc(self.created_at, "created_at")
        if expires <= issued or expires <= created:
            _invalid("session_expires_at")
        object.__setattr__(self, "authorization_issued_at", issued)
        object.__setattr__(self, "session_expires_at", expires)
        object.__setattr__(self, "created_at", created)


@dataclass(frozen=True, slots=True, kw_only=True)
class CapabilityRule:
    name: str
    schema_keys: frozenset[str]
    required_transport_capabilities: frozenset[TransportCapability]

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            _invalid("capability_rule.name")
        if not isinstance(self.schema_keys, frozenset) or any(
            not isinstance(item, str) or not item for item in self.schema_keys
        ):
            _invalid("capability_rule.schema_keys")
        if not isinstance(self.required_transport_capabilities, frozenset) or any(
            not isinstance(item, TransportCapability)
            for item in self.required_transport_capabilities
        ):
            _invalid("capability_rule.transport_capabilities")


@dataclass(frozen=True, slots=True, init=False)
class CapabilityPolicy:
    _rules: tuple[CapabilityRule, ...] = field(repr=False)
    _by_name: Mapping[str, CapabilityRule] = field(repr=False)

    def __init__(self, rules: Iterable[CapabilityRule]) -> None:
        values = tuple(rules)
        by_name: dict[str, CapabilityRule] = {}
        for rule in values:
            if not isinstance(rule, CapabilityRule):
                _invalid("capability_policy.rules")
            if rule.name in by_name:
                _invalid("capability_policy.duplicate_rule")
            by_name[rule.name] = rule
        object.__setattr__(self, "_rules", values)
        object.__setattr__(self, "_by_name", MappingProxyType(by_name))

    @property
    def rules(self) -> tuple[CapabilityRule, ...]:
        return self._rules

    def get(self, name: str) -> CapabilityRule | None:
        if not isinstance(name, str):
            _invalid("capability_name")
        return self._by_name.get(name)


_JSON_V1_SCHEMA_KEYS = frozenset({"json.v1/protocol-1.0"})
_RELIABLE_ORDERED = frozenset({
    TransportCapability.RELIABLE_ORDERED_MESSAGES,
})

P05_CAPABILITY_POLICY = CapabilityPolicy((
    CapabilityRule(
        name="runtime.connection",
        schema_keys=_JSON_V1_SCHEMA_KEYS,
        required_transport_capabilities=_RELIABLE_ORDERED,
    ),
    CapabilityRule(
        name="runtime.heartbeat",
        schema_keys=_JSON_V1_SCHEMA_KEYS,
        required_transport_capabilities=_RELIABLE_ORDERED,
    ),
    CapabilityRule(
        name="runtime.resume",
        schema_keys=_JSON_V1_SCHEMA_KEYS,
        required_transport_capabilities=_RELIABLE_ORDERED,
    ),
    CapabilityRule(
        name="runtime.management",
        schema_keys=_JSON_V1_SCHEMA_KEYS,
        required_transport_capabilities=_RELIABLE_ORDERED,
    ),
))


@dataclass(frozen=True, slots=True, kw_only=True)
class NegotiatedSession:
    context: SessionContext = field(repr=False)
    protocol: NegotiatedProtocol = field(repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.context, SessionContext):
            _invalid("context")
        if not isinstance(self.protocol, NegotiatedProtocol):
            _invalid("protocol")


class HandshakeSessionNegotiator:
    def __init__(
        self,
        *,
        transport_session: TransportSession,
        logical_identity: LogicalSessionIdentity,
        clock: Clock,
        protocol_matrix: ProtocolCompatibilityMatrix = JSON_V1_PROTOCOL_MATRIX,
        capability_policy: CapabilityPolicy = P05_CAPABILITY_POLICY,
    ) -> None:
        if not isinstance(transport_session, TransportSession):
            _invalid("transport_session")
        if not isinstance(logical_identity, LogicalSessionIdentity):
            _invalid("logical_identity")
        if not isinstance(clock, Clock):
            _invalid("clock")
        if not isinstance(protocol_matrix, ProtocolCompatibilityMatrix):
            _invalid("protocol_matrix")
        if not isinstance(capability_policy, CapabilityPolicy):
            _invalid("capability_policy")
        self._transport_session = transport_session
        self._logical_identity = logical_identity
        self._clock = clock
        self._protocol_matrix = protocol_matrix
        self._capability_policy = capability_policy

    def negotiate(
        self,
        *,
        claims: PendingHelloClaims,
        authority: HandshakeIamAuthority,
    ) -> NegotiatedSession:
        if not isinstance(claims, PendingHelloClaims):
            _invalid("claims")
        if type(authority) is not HandshakeIamAuthority:
            _invalid("authority")
        protocol = self._protocol_matrix.negotiate(
            claims.requested_version,
            minimum=claims.minimum_version,
        )
        capabilities = self._negotiate_capabilities(
            requested=claims.requested_capabilities,
            authorized=authority.capabilities,
            schema_key=protocol.schema_key,
        )
        created_at = self._clock.utc_now()
        context = SessionContext(
            connection_id=self._logical_identity.connection_id,
            session_id=self._logical_identity.session_id,
            connection_epoch=self._logical_identity.connection_epoch,
            identity=authority.identity,
            tenant_id=authority.tenant_id,
            component_type=authority.component_type,
            protocol_version=protocol.selected,
            protocol_schema_key=protocol.schema_key,
            wire_codec=WIRE_CODEC_JSON_V1,
            capabilities=capabilities,
            permission_snapshot_ref=authority.permission_snapshot_ref,
            permission_digest=authority.permission_digest,
            permission_version=authority.permission_version,
            iam_mode=authority.iam_mode,
            authorization_issued_at=authority.issued_at,
            session_expires_at=authority.expires_at,
            resume_eligible=authority.resume_eligible,
            established_state=LogicalConnectionState.AUTHENTICATED,
            created_at=created_at,
        )
        return NegotiatedSession(context=context, protocol=protocol)

    def _negotiate_capabilities(
        self,
        *,
        requested: frozenset[str],
        authorized: frozenset[str],
        schema_key: str,
    ) -> frozenset[str]:
        if not requested.issubset(authorized):
            raise NsRuntimeIamDeniedError(
                details={
                    "component": "logical_connection",
                    "operation": "capability_negotiation",
                    "reason": "requested_capability_not_authorized",
                },
            )
        transport_supported = self._transport_session.capabilities.supported
        for capability in requested:
            rule = self._capability_policy.get(capability)
            if rule is None:
                raise NsRuntimeProtocolVersionError(
                    details={
                        "component": "logical_connection",
                        "operation": "capability_negotiation",
                        "reason": "capability_not_registered",
                    },
                )
            if schema_key not in rule.schema_keys:
                raise NsRuntimeProtocolVersionError(
                    details={
                        "component": "logical_connection",
                        "operation": "capability_negotiation",
                        "reason": "capability_protocol_incompatible",
                    },
                )
            if not rule.required_transport_capabilities.issubset(
                transport_supported,
            ):
                raise NsRuntimeTransportCapabilityUnavailableError(
                    details={
                        "component": "logical_connection",
                        "operation": "capability_negotiation",
                        "reason": "capability_transport_incompatible",
                    },
                )
        return frozenset(requested)


def _utc(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        _invalid(field_name)
    try:
        offset = value.utcoffset()
        normalized = value.astimezone(timezone.utc)
    except Exception:
        offset = None
    if offset is None:
        _invalid(field_name)
    return normalized


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Logical session value is invalid.",
        details={
            "component": "logical_connection",
            "field": field_name,
        },
    )


__all__ = (
    "CapabilityPolicy",
    "CapabilityRule",
    "HandshakeSessionNegotiator",
    "LogicalSessionIdentity",
    "NegotiatedSession",
    "P05_CAPABILITY_POLICY",
    "SessionContext",
)
