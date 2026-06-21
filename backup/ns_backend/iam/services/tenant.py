# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ns_backend.iam.schemas import TenantContext

if TYPE_CHECKING:
    pass


class TenantService:
    """Tenant context service.

    Service responsibilities:
    1. Build immutable TenantContext from authenticated user object.
    2. Avoid persistence access and keep tenant context construction deterministic.
    """

    @staticmethod
    def from_user(user: Any) -> TenantContext:
        """Build tenant context from user."""
        return TenantContext(
            user_id=user.id,
            user_type=getattr(user, "user_type", ""),
            company_id=getattr(user, "company_id", None),
            subsidiary_id=getattr(user, "subsidiary_id", None),
            department_id=getattr(user, "department_id", None),
            is_staff=bool(getattr(user, "is_staff", False)),
            is_superuser=bool(getattr(user, "is_superuser", False)),
        )
