# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.constants import TenantContext
from ns_backend.policies import BasePolicy


class TenantPolicy(BasePolicy):
    """IAM 租户边界策略。"""

    USER_TYPE_PERSONAL = "PERSONAL"
    USER_TYPE_ENTERPRISE = "ENTERPRISE"

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
            cls.deny("个人用户不能访问企业组织资源", 14002)

        if cls.is_enterprise_user(context) and not context.company_id:
            cls.deny("企业用户未绑定公司", 14001)

    @classmethod
    def ensure_platform_admin(
        cls,
        context: TenantContext,
        message: str,
        code: int,
    ) -> None:
        if not cls.is_platform_admin(context):
            cls.deny(message, code)

    @classmethod
    def ensure_same_company(
        cls,
        left_company_id: int | None,
        right_company_id: int | None,
        message: str,
        code: int,
    ) -> None:
        if left_company_id != right_company_id:
            cls.deny(message, code)

    @classmethod
    def get_company_scope(cls, context: TenantContext) -> int | None:
        if cls.is_platform_admin(context):
            return None

        if cls.is_enterprise_user(context):
            cls.ensure_enterprise_context(context)
            return context.company_id

        return None


__all__ = ["TenantPolicy"]

