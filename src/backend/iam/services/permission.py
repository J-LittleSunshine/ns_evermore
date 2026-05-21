# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils import timezone

from iam.repositories.permission import PermissionRepository

if TYPE_CHECKING:
    from iam.models import IamUser


class PermissionService:
    """权限判定服务。"""

    USER_TYPE_PERSONAL = "PERSONAL"
    USER_TYPE_ENTERPRISE = "ENTERPRISE"

    @classmethod
    async def has_permission(cls, user: IamUser, permission_code: str) -> bool:
        if not user or not user.is_active:
            return False

        if user.is_superuser:
            return True

        if not permission_code:
            return False

        now = timezone.now()

        if user.user_type == cls.USER_TYPE_PERSONAL:
            return await cls.has_personal_permission(
                user=user,
                permission_code=permission_code,
                now=now,
            )

        if user.user_type == cls.USER_TYPE_ENTERPRISE:
            return await cls.has_enterprise_permission(
                user=user,
                permission_code=permission_code,
                now=now,
            )

        return False

    @classmethod
    async def has_personal_permission(
            cls,
            user: IamUser,
            permission_code: str,
            now,
    ) -> bool:
        if await PermissionRepository.has_user_deny(user.id, permission_code, now):
            return False

        has_user_allow = await PermissionRepository.has_user_allow(
            user.id,
            permission_code,
            now,
        )
        has_role_allow = await PermissionRepository.has_role_allow(
            user.id,
            permission_code,
            now,
            role_scope=cls.USER_TYPE_PERSONAL,
        )

        return has_user_allow or has_role_allow

    @classmethod
    async def has_enterprise_permission(
            cls,
            user: IamUser,
            permission_code: str,
            now,
    ) -> bool:
        has_user_deny = await PermissionRepository.has_user_deny(
            user.id,
            permission_code,
            now,
        )
        has_department_deny = False
        has_subsidiary_deny = False

        if user.department_id:
            has_department_deny = await PermissionRepository.has_department_deny(
                user.department_id,
                permission_code,
                now,
            )

        if user.subsidiary_id:
            has_subsidiary_deny = await PermissionRepository.has_subsidiary_deny(
                user.subsidiary_id,
                permission_code,
                now,
            )

        if has_user_deny or has_department_deny or has_subsidiary_deny:
            return False

        has_user_allow = await PermissionRepository.has_user_allow(
            user.id,
            permission_code,
            now,
        )
        has_role_allow = await PermissionRepository.has_role_allow(
            user.id,
            permission_code,
            now,
            role_scope=cls.USER_TYPE_ENTERPRISE,
        )
        has_department_allow = False
        has_subsidiary_allow = False

        if user.department_id:
            has_department_allow = await PermissionRepository.has_department_allow(
                user.department_id,
                permission_code,
                now,
            )

        if user.subsidiary_id:
            has_subsidiary_allow = await PermissionRepository.has_subsidiary_allow(
                user.subsidiary_id,
                permission_code,
                now,
            )

        return (
                has_user_allow
                or has_role_allow
                or has_department_allow
                or has_subsidiary_allow
        )


__all__ = ["PermissionService"]
