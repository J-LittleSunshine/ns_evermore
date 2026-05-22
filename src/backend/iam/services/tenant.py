# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.contexts import TenantContext


class TenantService:
    USER_TYPE_PERSONAL = "PERSONAL"
    USER_TYPE_ENTERPRISE = "ENTERPRISE"

    @classmethod
    def from_user(cls, user) -> TenantContext:
        return TenantContext(
            user_id=user.id,
            user_type=getattr(user, "user_type", ""),
            company_id=getattr(user, "company_id", None),
            subsidiary_id=getattr(user, "subsidiary_id", None),
            department_id=getattr(user, "department_id", None),
            is_staff=bool(getattr(user, "is_staff", False)),
            is_superuser=bool(getattr(user, "is_superuser", False)),
        )


__all__ = ["TenantService"]

