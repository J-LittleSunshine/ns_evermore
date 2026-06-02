# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, Literal

from ns_backend.iam.constants import RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class TenantContext:
    user_id: int
    user_type: str
    company_id: int | None
    subsidiary_id: int | None
    department_id: int | None
    is_staff: bool
    is_superuser: bool


@dataclass(frozen=True)
class DataScopeResult:
    allowed: bool
    scope: str | None = None
    company_id: int | None = None
    subsidiary_id: int | None = None
    department_id: int | None = None
    department_ids: list[int] = field(default_factory=list)
    user_id: int | None = None
    is_platform_scope: bool = False


@dataclass(frozen=True)
class DataScopeFieldMap:
    self_field: str | None = None
    company_field: str | None = "company_id"
    subsidiary_field: str | None = "subsidiary_id"
    department_field: str | None = "department_id"


@dataclass(frozen=True)
class DataScopeFilterPlan:
    allowed: bool
    filters: dict[str, object] = field(default_factory=dict)
    is_platform_scope: bool = False
    reason: str | None = None


@dataclass(frozen=True)
class UserAuthorizationContext:
    user_id: int
    role_ids: list[int] = field(default_factory=list)
    readable_resource_ids: list[str] = field(default_factory=list)
    readable_resource_filters: dict[str, Any] = field(default_factory=dict)
    access_mode: str = RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW
    version: int = 1


@dataclass(frozen=True)
class AuditEvent:
    operation_type: str
    resource_type: str
    operator_id: int | None = None
    company_id: int | None = None
    resource_id: int | None = None
    request_method: str | None = None
    request_path: str | None = None
    client_ip: str | None = None
    user_agent: str | None = None
    request_data: dict[str, Any] | None = None
    before_data: dict[str, Any] | None = None
    after_data: dict[str, Any] | None = None
    extra_data: dict[str, Any] | None = None
    status: str = "SUCCESS"
    error_code: int | None = None
    error_message: str | None = None
    trace_id: str | None = None


@dataclass(frozen=True)
class PermissionSpec:
    code: str
    name: str
    permission_type: str
    parent_code: str | None = None
    status: int = 1


class PermissionProvider(Protocol):
    app_label: str

    def list_permissions(self) -> tuple[PermissionSpec, ...]: ...


@dataclass(frozen=True, slots=True)
class TokenRotationResult:
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    session_id: str | None


@dataclass(frozen=True, slots=True)
class TokenRotationOutcome:
    status: Literal["rotated", "replayed", "invalid", "expired", "user_inactive", "session_unavailable"]
    result: TokenRotationResult | None = None


@dataclass(slots=True)
class AuthLoginResult:
    user: Any
    data: dict[str, Any]

