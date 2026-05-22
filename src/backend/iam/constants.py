# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    pass

IAM_DB_ALIAS = settings.DATABASE_ROUTER_MAP.get("iam", "default")


@dataclass(frozen=True)
class TenantContext:
    user_id: int
    user_type: str
    company_id: int | None
    subsidiary_id: int | None
    department_id: int | None
    is_staff: bool
    is_superuser: bool
