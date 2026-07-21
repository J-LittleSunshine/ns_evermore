# -*- coding: utf-8 -*-
"""Minimal runtime permission snapshot; no credential or raw IAM response."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from ns_common.exceptions import NsValidationError
from ns_common.iam import IamCredentialStatus, IamIntrospectionResult, IamPrincipalType
from ns_runtime.protocol import AuthContextGroup


@dataclass(frozen=True, slots=True, kw_only=True)
class PermissionSnapshot:
    identity: str = field(repr=False)
    tenant_id: str = field(repr=False)
    principal_type: IamPrincipalType
    component_type: str
    capabilities: frozenset[str] = field(repr=False)
    permission_snapshot_ref: str = field(repr=False)
    permission_digest: str = field(repr=False)
    permission_version: str = field(repr=False)
    iam_mode: str
    issued_at: datetime
    expires_at: datetime
    resume_eligible: bool

    @classmethod
    def from_introspection(
        cls,
        result: IamIntrospectionResult,
        *,
        iam_mode: str,
    ) -> "PermissionSnapshot":
        if result.credential_status is not IamCredentialStatus.ACTIVE:
            _invalid("credential_status")
        return cls(
            identity=result.identity,
            tenant_id=result.tenant_id,
            principal_type=result.principal_type,
            component_type=result.component_type,
            capabilities=result.capabilities,
            permission_snapshot_ref=result.permission_snapshot_ref,
            permission_digest=result.permission_digest,
            permission_version=result.permission_version,
            iam_mode=iam_mode,
            issued_at=result.issued_at,
            expires_at=result.expires_at,
            resume_eligible=result.resume_eligible,
        )

    def __post_init__(self) -> None:
        for name in (
            "identity", "tenant_id", "component_type", "permission_snapshot_ref",
            "permission_digest", "permission_version", "iam_mode",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                _invalid(name)
        if not isinstance(self.principal_type, IamPrincipalType):
            _invalid("principal_type")
        if not isinstance(self.capabilities, frozenset) or any(
            not isinstance(item, str) or not item for item in self.capabilities
        ):
            _invalid("capabilities")
        issued = _utc(self.issued_at, "issued_at")
        expires = _utc(self.expires_at, "expires_at")
        if expires <= issued:
            _invalid("expires_at")
        if not isinstance(self.resume_eligible, bool):
            _invalid("resume_eligible")
        object.__setattr__(self, "issued_at", issued)
        object.__setattr__(self, "expires_at", expires)

    def auth_context(self) -> AuthContextGroup:
        return AuthContextGroup(
            permission_snapshot_ref=self.permission_snapshot_ref,
            permission_digest=self.permission_digest,
            iam_mode=self.iam_mode,
            issued_at=_iso(self.issued_at),
            expires_at=_iso(self.expires_at),
        )

    def is_current(self, now: datetime) -> bool:
        current = _utc(now, "now")
        return self.issued_at <= current < self.expires_at


def _utc(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        _invalid(field_name)
    return value.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Runtime permission snapshot is invalid.",
        details={"component": "runtime_iam", "field": field_name},
    )


__all__ = ("PermissionSnapshot",)
