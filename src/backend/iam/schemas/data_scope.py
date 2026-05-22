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


__all__ = ["DataScopeResult"]

