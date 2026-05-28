# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field


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


__all__ = [
    "DataScopeResult",
    "DataScopeFieldMap",
    "DataScopeFilterPlan",
]

