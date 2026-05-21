# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.services.permission import PermissionService
from ns_backend.exceptions import BusinessError


class UserPolicy:
    """IAM 用户操作权限策略。"""

    ADMIN_USER_PERMISSION = "iam:user:update_staff"
    SUPERUSER_PERMISSION = "iam:user:update_superuser"

    @classmethod
    async def ensure_can_operate_user(cls, operator, target_user) -> None:
        """校验操作者是否允许操作目标用户。"""
        if target_user.is_superuser and not operator.is_superuser:
            raise BusinessError("后台管理员不能操作超级管理员", 11010)

        if target_user.is_staff or target_user.is_superuser:
            has_permission = await cls.has_admin_user_permission(operator)

            if not has_permission:
                raise BusinessError(f"权限不足：{cls.ADMIN_USER_PERMISSION}", 11009)

    @classmethod
    async def ensure_can_update_critical_fields(cls, operator, update_data: dict) -> None:
        """校验关键字段更新权限。"""
        if cls.is_truthy(update_data.get("is_superuser")) and not operator.is_superuser:
            raise BusinessError("后台管理员不能操作超级管理员", 11010)

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
                raise BusinessError(f"权限不足：{permission_code}", 11009)

    @classmethod
    async def has_admin_user_permission(cls, operator) -> bool:
        """检查后台管理员权限。"""
        if operator.is_superuser:
            return True

        return await PermissionService.has_permission(
            user=operator,
            permission_code=cls.ADMIN_USER_PERMISSION,
        )

    @staticmethod
    def is_truthy(value) -> bool:
        """统一 truthy 判断。"""
        return value in (True, 1, "1", "true", "True")
