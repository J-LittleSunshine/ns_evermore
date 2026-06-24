# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import (
    Any,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from ns_backend.iam.models import IamUser


@dataclass(slots=True, kw_only=True)
class AuthLoginResult:
    user: "IamUser"
    data: dict[str, Any]


@dataclass(slots=True, kw_only=True)
class TokenRotationResult:
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    session_id: str | None


@dataclass(slots=True, kw_only=True)
class TokenRotationOutcome:
    status: str
    result: TokenRotationResult | None = None


@dataclass(slots=True, kw_only=True)
class TenantContext:
    user_id: int
    user_type: str
    company_id: int | None = None
    subsidiary_id: int | None = None
    department_id: int | None = None
    is_staff: bool = False
    is_superuser: bool = False


@dataclass(slots=True, kw_only=True)
class DataScopeResult:
    allowed: bool
    scope: str | None = None
    company_id: int | None = None
    subsidiary_id: int | None = None
    department_id: int | None = None
    department_ids: list[int] | None = None
    user_id: int | None = None
    is_platform_scope: bool = False


@dataclass(slots=True, kw_only=True)
class DataScopeFieldMap:
    self_field: str | None = None
    company_field: str | None = None
    subsidiary_field: str | None = None
    department_field: str | None = None


@dataclass(slots=True, kw_only=True)
class DataScopeFilterPlan:
    allowed: bool
    filters: dict[str, Any] | None = None
    reason: str | None = None
    is_platform_scope: bool = False
