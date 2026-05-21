# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass

from ns_backend.exceptions import BusinessError


@dataclass(frozen=True)
class TenantContext:
    user_id: int
    user_type: str
    company_id: int | None
    subsidiary_id: int | None
    department_id: int | None
    is_staff: bool
    is_superuser: bool


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

    @classmethod
    def is_platform_admin(cls, context: TenantContext) -> bool:
        return bool(context.is_superuser)

    @classmethod
    def is_enterprise_user(cls, context: TenantContext) -> bool:
        return context.user_type == cls.USER_TYPE_ENTERPRISE

    @classmethod
    def is_personal_user(cls, context: TenantContext) -> bool:
        return context.user_type == cls.USER_TYPE_PERSONAL

    @classmethod
    def ensure_enterprise_context(cls, context: TenantContext) -> None:
        if cls.is_platform_admin(context):
            return

        if cls.is_personal_user(context):
            raise BusinessError("个人用户不能访问企业组织资源", 14002)

        if cls.is_enterprise_user(context) and not context.company_id:
            raise BusinessError("企业用户未绑定公司", 14001)

    @classmethod
    def get_company_id_or_none(cls, context: TenantContext) -> int | None:
        if cls.is_platform_admin(context):
            return None

        if cls.is_enterprise_user(context):
            return context.company_id

        return None

