# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.policies.tenant import TenantPolicy
from iam.services.permission import PermissionService
from iam.services.tenant import TenantService
from ns_backend.policies import BasePolicy
from ns_backend.exceptions import BusinessError


class UserPolicy(BasePolicy):
    """IAM 用户操作权限策略。"""

    ADMIN_USER_PERMISSION = "iam:user:update_staff"
    SUPERUSER_PERMISSION = "iam:user:update_superuser"

    @classmethod
    async def ensure_can_operate_user(cls, operator, target_user) -> None:
        """校验操作者是否允许操作目标用户。"""
        if target_user.is_superuser and not operator.is_superuser:
            raise BusinessError("Staff administrators cannot operate on superusers", 11010)

        if target_user.is_staff or target_user.is_superuser:
            has_permission = await cls.has_admin_user_permission(operator)

            if not has_permission:
                raise BusinessError(f"Permission denied: {cls.ADMIN_USER_PERMISSION}", 11009)

    @classmethod
    async def ensure_can_update_critical_fields(cls, operator, update_data: dict) -> None:
        """校验关键字段更新权限。"""
        if cls.is_truthy(update_data.get("is_superuser")) and not operator.is_superuser:
            raise BusinessError("Staff administrators cannot operate on superusers", 11010)

        if operator.is_superuser:
            return

        critical_field_permissions = {
            "is_staff": cls.ADMIN_USER_PERMISSION,
            "is_superuser": cls.SUPERUSER_PERMISSION,
        }

        for field, permission_code in critical_field_permissions.items():
            if field not in update_data:
                continue

            if not cls.is_truthy(update_data.get(field)):
                continue

            has_permission = await PermissionService.has_permission(
                user=operator,
                permission_code=permission_code,
            )

            if not has_permission:
                raise BusinessError(f"Permission denied: {permission_code}", 11009)

    @classmethod
    async def has_admin_user_permission(cls, operator) -> bool:
        """检查后台管理员权限。"""
        if operator.is_superuser:
            return True

        return await PermissionService.has_permission(
            user=operator,
            permission_code=cls.ADMIN_USER_PERMISSION,
        )

    @classmethod
    def get_user_tenant_filter(cls, operator) -> dict | None:
        context = TenantService.from_user(operator)

        if TenantPolicy.is_platform_admin(context):
            return None

        if TenantPolicy.is_enterprise_user(context):
            TenantPolicy.ensure_enterprise_context(context)
            return {"company_id": context.company_id}

        return {"id": context.user_id}

    @classmethod
    def get_operator_company_scope(cls, operator) -> int | None:
        context = TenantService.from_user(operator)
        return TenantPolicy.get_company_scope(context)

    @classmethod
    def build_create_payload(cls, operator, data: dict) -> dict:
        context = TenantService.from_user(operator)
        create_payload = data.copy()

        if not TenantPolicy.is_platform_admin(context) and cls.is_truthy(create_payload.get("is_superuser")):
            raise BusinessError("Staff administrators cannot operate on superusers", 11010)

        if TenantPolicy.is_platform_admin(context):
            return create_payload

        if TenantPolicy.is_enterprise_user(context):
            TenantPolicy.ensure_enterprise_context(context)
            create_payload["company_id"] = context.company_id
            create_payload["user_type"] = TenantService.USER_TYPE_ENTERPRISE
            create_payload["is_superuser"] = 0
            return create_payload

        raise BusinessError("Personal users cannot create users", 14021)

    @classmethod
    def ensure_can_update_user_fields(cls, operator, data: dict) -> None:
        context = TenantService.from_user(operator)

        if "company_id" in data and not TenantPolicy.is_platform_admin(context):
            raise BusinessError("Updating field is not allowed: company_id", 12005)

