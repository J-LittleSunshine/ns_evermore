# -*- coding: utf-8 -*-
"""IAM-R1 transport-neutral contracts shared by backend and runtime."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from ns_common.exceptions import NsValidationError


_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:@/-]{0,255}")
_CAPABILITY = re.compile(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+")


class IamPrincipalType(str, Enum):
    FRONTEND_USER = "frontend_user"
    BACKEND_SERVICE = "backend_service"
    CLIENT = "client"
    NODE = "node"
    RUNTIME_NODE = "runtime_node"
    MANAGEMENT = "management"


class IamCredentialStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    INVALID = "invalid"


class RuntimeRoleScope(str, Enum):
    SINGLETON = "singleton"
    SUB_NODE = "sub_node"
    STANDBY_MASTER = "standby_master"
    ACTIVE_MASTER = "active_master"


@dataclass(frozen=True, slots=True, kw_only=True)
class IamIntrospectionRequest:
    token: str = field(repr=False)
    component_type: str
    requested_capabilities: frozenset[str] = field(repr=False)
    protocol_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.token, str) or not self.token or len(self.token) > 65_536:
            _invalid("introspection.token")
        _name(self.component_type, "introspection.component_type")
        _capabilities(self.requested_capabilities, "introspection.requested_capabilities")
        _name(self.protocol_version, "introspection.protocol_version")

    def to_wire(self) -> dict[str, object]:
        return {
            "token": self.token,
            "component_type": self.component_type,
            "requested_capabilities": sorted(self.requested_capabilities),
            "protocol_version": self.protocol_version,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class IamIntrospectionResult:
    identity: str = field(repr=False)
    tenant_id: str = field(repr=False)
    principal_type: IamPrincipalType
    component_type: str
    capabilities: frozenset[str] = field(repr=False)
    permission_snapshot_ref: str = field(repr=False)
    permission_digest: str = field(repr=False)
    permission_version: str = field(repr=False)
    issued_at: datetime
    expires_at: datetime
    credential_status: IamCredentialStatus
    resume_eligible: bool

    def __post_init__(self) -> None:
        for value, name in (
            (self.identity, "introspection.identity"),
            (self.tenant_id, "introspection.tenant_id"),
            (self.component_type, "introspection.component_type"),
            (self.permission_snapshot_ref, "introspection.permission_snapshot_ref"),
            (self.permission_digest, "introspection.permission_digest"),
            (self.permission_version, "introspection.permission_version"),
        ):
            _name(value, name)
        if not isinstance(self.principal_type, IamPrincipalType):
            _invalid("introspection.principal_type")
        _capabilities(self.capabilities, "introspection.capabilities")
        if not isinstance(self.credential_status, IamCredentialStatus):
            _invalid("introspection.credential_status")
        issued = _utc(self.issued_at, "introspection.issued_at")
        expires = _utc(self.expires_at, "introspection.expires_at")
        if expires <= issued:
            _invalid("introspection.expires_at")
        if not isinstance(self.resume_eligible, bool):
            _invalid("introspection.resume_eligible")
        object.__setattr__(self, "issued_at", issued)
        object.__setattr__(self, "expires_at", expires)

    def to_wire(self) -> dict[str, object]:
        return {
            "identity": self.identity,
            "tenant_id": self.tenant_id,
            "principal_type": self.principal_type.value,
            "component_type": self.component_type,
            "capabilities": sorted(self.capabilities),
            "permission_snapshot_ref": self.permission_snapshot_ref,
            "permission_digest": self.permission_digest,
            "permission_version": self.permission_version,
            "issued_at": _iso(self.issued_at),
            "expires_at": _iso(self.expires_at),
            "credential_status": self.credential_status.value,
            "resume_eligible": self.resume_eligible,
        }

    @classmethod
    def from_wire(cls, value: object) -> "IamIntrospectionResult":
        data = _exact_mapping(value, {
            "identity", "tenant_id", "principal_type", "component_type",
            "capabilities", "permission_snapshot_ref", "permission_digest",
            "permission_version", "issued_at", "expires_at",
            "credential_status", "resume_eligible",
        }, "introspection_response")
        return cls(
            identity=data["identity"],  # type: ignore[arg-type]
            tenant_id=data["tenant_id"],  # type: ignore[arg-type]
            principal_type=_enum(IamPrincipalType, data["principal_type"], "principal_type"),
            component_type=data["component_type"],  # type: ignore[arg-type]
            capabilities=_wire_capabilities(data["capabilities"]),
            permission_snapshot_ref=data["permission_snapshot_ref"],  # type: ignore[arg-type]
            permission_digest=data["permission_digest"],  # type: ignore[arg-type]
            permission_version=data["permission_version"],  # type: ignore[arg-type]
            issued_at=_parse_time(data["issued_at"], "issued_at"),
            expires_at=_parse_time(data["expires_at"], "expires_at"),
            credential_status=_enum(IamCredentialStatus, data["credential_status"], "credential_status"),
            resume_eligible=data["resume_eligible"],  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class RuntimeBootstrapRequest:
    runtime_id: str
    requested_role: RuntimeRoleScope
    credential_id: str = field(repr=False)

    def __post_init__(self) -> None:
        _name(self.runtime_id, "bootstrap.runtime_id")
        _name(self.credential_id, "bootstrap.credential_id")
        if not isinstance(self.requested_role, RuntimeRoleScope):
            _invalid("bootstrap.requested_role")


@dataclass(frozen=True, slots=True, kw_only=True)
class RuntimeBootstrapResult:
    role_authorized: bool
    authorized_roles: frozenset[RuntimeRoleScope]
    candidate_master: bool
    config_version: str
    policy_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.role_authorized, bool) or not isinstance(self.candidate_master, bool):
            _invalid("bootstrap.decision")
        if not isinstance(self.authorized_roles, frozenset) or any(
            not isinstance(item, RuntimeRoleScope) for item in self.authorized_roles
        ):
            _invalid("bootstrap.authorized_roles")
        _name(self.config_version, "bootstrap.config_version")
        _name(self.policy_version, "bootstrap.policy_version")


@dataclass(frozen=True, slots=True, kw_only=True)
class IamTargetContext:
    kind: str
    tenant_id: str | None = field(default=None, repr=False)
    reference: str | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        _name(self.kind, "access.target.kind")
        if self.tenant_id is not None:
            _name(self.tenant_id, "access.target.tenant_id")
        if self.reference is not None:
            _name(self.reference, "access.target.reference")

    def to_wire(self) -> dict[str, object]:
        result: dict[str, object] = {"kind": self.kind}
        if self.tenant_id is not None:
            result["tenant_id"] = self.tenant_id
        if self.reference is not None:
            result["reference"] = self.reference
        return result


@dataclass(frozen=True, slots=True, kw_only=True)
class IamAccessCheckRequest:
    identity: str = field(repr=False)
    tenant_id: str = field(repr=False)
    permission_snapshot_ref: str = field(repr=False)
    permission_version: str = field(repr=False)
    message_type: str
    target: IamTargetContext
    cross_tenant: bool = False
    management: bool = False
    task_creation: bool = False

    def __post_init__(self) -> None:
        for value, name in (
            (self.identity, "access.identity"),
            (self.tenant_id, "access.tenant_id"),
            (self.permission_snapshot_ref, "access.permission_snapshot_ref"),
            (self.permission_version, "access.permission_version"),
            (self.message_type, "access.message_type"),
        ):
            _name(value, name)
        if not isinstance(self.target, IamTargetContext):
            _invalid("access.target")
        if any(not isinstance(value, bool) for value in (
            self.cross_tenant, self.management, self.task_creation,
        )):
            _invalid("access.flags")

    def to_wire(self) -> dict[str, object]:
        return {
            "identity": self.identity,
            "tenant_id": self.tenant_id,
            "permission_snapshot_ref": self.permission_snapshot_ref,
            "permission_version": self.permission_version,
            "message_type": self.message_type,
            "target": self.target.to_wire(),
            "cross_tenant": self.cross_tenant,
            "management": self.management,
            "task_creation": self.task_creation,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class IamAccessDecision:
    allowed: bool
    reason: str
    permission_version: str
    decided_at: datetime
    refresh_required: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.allowed, bool) or not isinstance(self.refresh_required, bool):
            _invalid("access.decision")
        _name(self.reason, "access.reason")
        _name(self.permission_version, "access.permission_version")
        object.__setattr__(self, "decided_at", _utc(self.decided_at, "access.decided_at"))

    def to_wire(self) -> dict[str, object]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "permission_version": self.permission_version,
            "decided_at": _iso(self.decided_at),
            "refresh_required": self.refresh_required,
        }

    @classmethod
    def from_wire(cls, value: object) -> "IamAccessDecision":
        data = _exact_mapping(value, {
            "allowed", "reason", "permission_version", "decided_at",
            "refresh_required",
        }, "access_decision")
        return cls(
            allowed=data["allowed"],  # type: ignore[arg-type]
            reason=data["reason"],  # type: ignore[arg-type]
            permission_version=data["permission_version"],  # type: ignore[arg-type]
            decided_at=_parse_time(data["decided_at"], "decided_at"),
            refresh_required=data["refresh_required"],  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class PermissionInvalidation:
    permission_snapshot_ref: str = field(repr=False)
    previous_version: str = field(repr=False)
    current_version: str = field(repr=False)
    invalidated_at: datetime
    reason: str

    def __post_init__(self) -> None:
        for value, name in (
            (self.permission_snapshot_ref, "invalidation.permission_snapshot_ref"),
            (self.previous_version, "invalidation.previous_version"),
            (self.current_version, "invalidation.current_version"),
            (self.reason, "invalidation.reason"),
        ):
            _name(value, name)
        if self.previous_version == self.current_version:
            _invalid("invalidation.current_version")
        object.__setattr__(self, "invalidated_at", _utc(self.invalidated_at, "invalidation.invalidated_at"))


@dataclass(frozen=True, slots=True, kw_only=True)
class PayloadRefValidationRequest:
    object_id: str
    version: str
    checksum: str
    tenant_id: str = field(repr=False)
    owner_identity: str = field(repr=False)
    source_identity: str = field(repr=False)
    target: IamTargetContext
    callback_message_type: str | None = None

    def __post_init__(self) -> None:
        for value, name in (
            (self.object_id, "payload_ref.object_id"),
            (self.version, "payload_ref.version"),
            (self.checksum, "payload_ref.checksum"),
            (self.tenant_id, "payload_ref.tenant_id"),
            (self.owner_identity, "payload_ref.owner_identity"),
            (self.source_identity, "payload_ref.source_identity"),
        ):
            _name(value, name)
        if not isinstance(self.target, IamTargetContext):
            _invalid("payload_ref.target")
        if self.callback_message_type is not None:
            _name(self.callback_message_type, "payload_ref.callback_message_type")

    def to_wire(self) -> dict[str, object]:
        result: dict[str, object] = {
            "object_id": self.object_id,
            "version": self.version,
            "checksum": self.checksum,
            "tenant_id": self.tenant_id,
            "owner_identity": self.owner_identity,
            "source_identity": self.source_identity,
            "target": self.target.to_wire(),
        }
        if self.callback_message_type is not None:
            result["callback_message_type"] = self.callback_message_type
        return result


@dataclass(frozen=True, slots=True, kw_only=True)
class PayloadRefValidationResult:
    valid: bool
    reason: str
    expires_at: datetime
    revoked: bool
    object_id: str | None = None
    version: str | None = None
    checksum: str | None = None
    tenant_id: str | None = field(default=None, repr=False)
    size_bytes: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.valid, bool) or not isinstance(self.revoked, bool):
            _invalid("payload_ref.result")
        _name(self.reason, "payload_ref.reason")
        object.__setattr__(self, "expires_at", _utc(self.expires_at, "payload_ref.expires_at"))
        if self.valid and self.revoked:
            _invalid("payload_ref.revoked")
        metadata = (self.object_id, self.version, self.checksum, self.tenant_id,
                    self.size_bytes)
        if self.valid:
            if any(value is None for value in metadata):
                _invalid("payload_ref.integrity_metadata")
            for value, name in zip(metadata[:4], (
                "object_id", "version", "checksum", "tenant_id",
            )):
                _name(value, f"payload_ref.result.{name}")
            if isinstance(self.size_bytes, bool) or not isinstance(self.size_bytes, int) or self.size_bytes < 0:
                _invalid("payload_ref.result.size_bytes")
        elif any(value is not None for value in metadata):
            if any(value is None for value in metadata):
                _invalid("payload_ref.integrity_metadata")
            for value, name in zip(metadata[:4], (
                "object_id", "version", "checksum", "tenant_id",
            )):
                _name(value, f"payload_ref.result.{name}")
            if isinstance(self.size_bytes, bool) or not isinstance(self.size_bytes, int) or self.size_bytes < 0:
                _invalid("payload_ref.result.size_bytes")

    def to_wire(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "reason": self.reason,
            "expires_at": _iso(self.expires_at),
            "revoked": self.revoked,
            "object_id": self.object_id,
            "version": self.version,
            "checksum": self.checksum,
            "tenant_id": self.tenant_id,
            "size_bytes": self.size_bytes,
        }

    @classmethod
    def from_wire(cls, value: object) -> "PayloadRefValidationResult":
        data = _exact_mapping(value, {
            "valid", "reason", "expires_at", "revoked", "object_id",
            "version", "checksum", "tenant_id", "size_bytes",
        }, "payload_ref_result")
        return cls(
            valid=data["valid"],  # type: ignore[arg-type]
            reason=data["reason"],  # type: ignore[arg-type]
            expires_at=_parse_time(data["expires_at"], "expires_at"),
            revoked=data["revoked"],  # type: ignore[arg-type]
            object_id=data["object_id"],  # type: ignore[arg-type]
            version=data["version"],  # type: ignore[arg-type]
            checksum=data["checksum"],  # type: ignore[arg-type]
            tenant_id=data["tenant_id"],  # type: ignore[arg-type]
            size_bytes=data["size_bytes"],  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class PayloadRefRevalidationRequest:
    """P11 object-bound IAM request; it carries no runtime identity digest."""

    object_id: str
    version: str
    checksum: str
    size_bytes: int
    tenant_id: str = field(repr=False)
    target_principal: str = field(repr=False)
    target_tenant_id: str = field(repr=False)
    target_fingerprint: str
    permission_snapshot_ref: str = field(repr=False)
    permission_version: str = field(repr=False)
    admission_authority_reference: str = field(repr=False)

    def __post_init__(self) -> None:
        for value, name in (
            (self.object_id, "payload_revalidation.object_id"),
            (self.version, "payload_revalidation.version"),
            (self.checksum, "payload_revalidation.checksum"),
            (self.tenant_id, "payload_revalidation.tenant_id"),
            (self.target_principal, "payload_revalidation.target_principal"),
            (self.target_tenant_id, "payload_revalidation.target_tenant_id"),
            (self.target_fingerprint, "payload_revalidation.target_fingerprint"),
            (
                self.permission_snapshot_ref,
                "payload_revalidation.permission_snapshot_ref",
            ),
            (self.permission_version, "payload_revalidation.permission_version"),
            (
                self.admission_authority_reference,
                "payload_revalidation.admission_authority_reference",
            ),
        ):
            _name(value, name)
        if (
            isinstance(self.size_bytes, bool)
            or not isinstance(self.size_bytes, int)
            or self.size_bytes < 0
        ):
            _invalid("payload_revalidation.size_bytes")

    def to_wire(self) -> dict[str, object]:
        return {
            "object_id": self.object_id,
            "version": self.version,
            "checksum": self.checksum,
            "size_bytes": self.size_bytes,
            "tenant_id": self.tenant_id,
            "target_principal": self.target_principal,
            "target_tenant_id": self.target_tenant_id,
            "target_fingerprint": self.target_fingerprint,
            "permission_snapshot_ref": self.permission_snapshot_ref,
            "permission_version": self.permission_version,
            "admission_authority_reference": self.admission_authority_reference,
        }

    @classmethod
    def from_wire(cls, value: object) -> "PayloadRefRevalidationRequest":
        data = _exact_mapping(value, {
            "object_id", "version", "checksum", "size_bytes", "tenant_id",
            "target_principal", "target_tenant_id", "target_fingerprint",
            "permission_snapshot_ref", "permission_version",
            "admission_authority_reference",
        }, "payload_ref_revalidation_request")
        return cls(**data)  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True, kw_only=True)
class PayloadRefRevalidationDecision:
    """Backend-issued object metadata and resource-authorization decision."""

    valid: bool
    allowed: bool
    reason: str
    object_id: str
    version: str
    checksum: str
    size_bytes: int
    tenant_id: str = field(repr=False)
    target_principal: str = field(repr=False)
    target_fingerprint: str
    permission_snapshot_ref: str = field(repr=False)
    permission_version: str = field(repr=False)
    decision_reference: str = field(repr=False)
    decided_at: datetime
    expires_at: datetime
    refresh_required: bool = False

    def __post_init__(self) -> None:
        if any(type(value) is not bool for value in (
            self.valid, self.allowed, self.refresh_required,
        )):
            _invalid("payload_revalidation.decision_flags")
        for value, name in (
            (self.reason, "payload_revalidation.reason"),
            (self.object_id, "payload_revalidation.object_id"),
            (self.version, "payload_revalidation.version"),
            (self.checksum, "payload_revalidation.checksum"),
            (self.tenant_id, "payload_revalidation.tenant_id"),
            (self.target_principal, "payload_revalidation.target_principal"),
            (self.target_fingerprint, "payload_revalidation.target_fingerprint"),
            (
                self.permission_snapshot_ref,
                "payload_revalidation.permission_snapshot_ref",
            ),
            (self.permission_version, "payload_revalidation.permission_version"),
            (self.decision_reference, "payload_revalidation.decision_reference"),
        ):
            _name(value, name)
        if (
            isinstance(self.size_bytes, bool)
            or not isinstance(self.size_bytes, int)
            or self.size_bytes < 0
        ):
            _invalid("payload_revalidation.size_bytes")
        decided_at = _utc(self.decided_at, "payload_revalidation.decided_at")
        expires_at = _utc(self.expires_at, "payload_revalidation.expires_at")
        if expires_at < decided_at or (self.allowed and not self.valid):
            _invalid("payload_revalidation.decision")
        object.__setattr__(self, "decided_at", decided_at)
        object.__setattr__(self, "expires_at", expires_at)

    def to_wire(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "allowed": self.allowed,
            "reason": self.reason,
            "object_id": self.object_id,
            "version": self.version,
            "checksum": self.checksum,
            "size_bytes": self.size_bytes,
            "tenant_id": self.tenant_id,
            "target_principal": self.target_principal,
            "target_fingerprint": self.target_fingerprint,
            "permission_snapshot_ref": self.permission_snapshot_ref,
            "permission_version": self.permission_version,
            "decision_reference": self.decision_reference,
            "decided_at": _iso(self.decided_at),
            "expires_at": _iso(self.expires_at),
            "refresh_required": self.refresh_required,
        }

    @classmethod
    def from_wire(cls, value: object) -> "PayloadRefRevalidationDecision":
        data = _exact_mapping(value, {
            "valid", "allowed", "reason", "object_id", "version", "checksum",
            "size_bytes", "tenant_id", "target_principal",
            "target_fingerprint", "permission_snapshot_ref",
            "permission_version", "decision_reference", "decided_at",
            "expires_at", "refresh_required",
        }, "payload_ref_revalidation_decision")
        return cls(
            **{
                **data,
                "decided_at": _parse_time(data["decided_at"], "decided_at"),
                "expires_at": _parse_time(data["expires_at"], "expires_at"),
            },
        )  # type: ignore[arg-type]


def freeze_metadata(value: Mapping[str, str]) -> Mapping[str, str]:
    if not isinstance(value, Mapping):
        _invalid("metadata")
    result: dict[str, str] = {}
    for key, item in value.items():
        _name(key, "metadata.key")
        _name(item, "metadata.value")
        result[key] = item
    return MappingProxyType(result)


def _name(value: object, field_name: str) -> None:
    if not isinstance(value, str) or _NAME.fullmatch(value) is None:
        _invalid(field_name)


def _capabilities(value: object, field_name: str) -> None:
    if not isinstance(value, frozenset) or any(
        not isinstance(item, str) or _CAPABILITY.fullmatch(item) is None
        for item in value
    ):
        _invalid(field_name)


def _wire_capabilities(value: object) -> frozenset[str]:
    if not isinstance(value, list):
        _invalid("introspection.capabilities")
    try:
        if len(value) != len(set(value)):
            _invalid("introspection.capabilities")
        result = frozenset(value)
    except TypeError:
        _invalid("introspection.capabilities")
    _capabilities(result, "introspection.capabilities")
    return result


def _utc(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        _invalid(field_name)
    return value.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(value: object, field_name: str) -> datetime:
    if not isinstance(value, str):
        _invalid(field_name)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        _invalid(field_name)
    return _utc(parsed, field_name)


def _exact_mapping(value: object, fields: set[str], field_name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        _invalid(field_name)
    return dict(value)


def _enum(enum_type: type[Enum], value: object, field_name: str) -> Any:
    try:
        return enum_type(value)
    except (TypeError, ValueError):
        _invalid(field_name)


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "IAM-R1 contract value is invalid.",
        details={"component": "iam_r1", "field": field_name},
    )


__all__ = (
    "IamAccessCheckRequest", "IamAccessDecision", "IamCredentialStatus",
    "IamIntrospectionRequest", "IamIntrospectionResult", "IamPrincipalType",
    "IamTargetContext", "PayloadRefRevalidationDecision",
    "PayloadRefRevalidationRequest", "PayloadRefValidationRequest",
    "PayloadRefValidationResult", "PermissionInvalidation",
    "RuntimeBootstrapRequest", "RuntimeBootstrapResult", "RuntimeRoleScope",
    "freeze_metadata",
)
