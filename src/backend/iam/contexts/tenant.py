from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TenantContext:
    user_id: int
    user_type: str
    company_id: int | None
    subsidiary_id: int | None
    department_id: int | None
    is_staff: bool
    is_superuser: bool


__all__ = ["TenantContext"]

