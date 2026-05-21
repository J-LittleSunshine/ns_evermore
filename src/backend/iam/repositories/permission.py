# -*- coding: utf-8 -*-
from __future__ import annotations

from django.db.models import Q

from iam.constants import IAM_DB_ALIAS
from iam.models import (
    IamPermission,
    IamDepartmentPermission,
    IamRolePermission,
    IamSubsidiaryPermission,
    IamUserPermission,
    IamUserRole,
)


class PermissionRepository:
    """权限判定数据访问层。"""

    EFFECT_ALLOW = "ALLOW"
    EFFECT_DENY = "DENY"
    MAX_ANCESTOR_DEPTH = 20

    @staticmethod
    def valid_time_filter(now):
        """权限有效期过滤条件。"""
        return Q(expired_at__isnull=True) | Q(expired_at__gt=now)

    @classmethod
    async def get_active_permission_ids_with_ancestors(
        cls,
        permission_code: str,
    ) -> list[int]:
        permission = await IamPermission.objects.using(IAM_DB_ALIAS).filter(
            status=1,
            permission_code=permission_code,
        ).only("id", "parent_id").afirst()
        if not permission:
            return []

        permission_ids: list[int] = []
        seen_ids: set[int] = set()
        current = permission

        # Prevent circular parent references from causing infinite loops.
        for _ in range(cls.MAX_ANCESTOR_DEPTH):
            current_id = current.id
            if current_id in seen_ids:
                break

            seen_ids.add(current_id)
            permission_ids.append(current_id)

            if not current.parent_id:
                break

            current = await IamPermission.objects.using(IAM_DB_ALIAS).filter(
                id=current.parent_id,
                status=1,
            ).only("id", "parent_id").afirst()
            if not current:
                break

        return permission_ids

    @classmethod
    async def has_user_allow(cls, user_id: int, permission_ids: list[int], now) -> bool:
        return await IamUserPermission.objects.using(IAM_DB_ALIAS).filter(
            cls.valid_time_filter(now),
            user_id=user_id,
            permission_id__in=permission_ids,
            permission__status=1,
            effect=cls.EFFECT_ALLOW,
        ).aexists()

    @classmethod
    async def has_user_deny(cls, user_id: int, permission_ids: list[int], now) -> bool:
        return await IamUserPermission.objects.using(IAM_DB_ALIAS).filter(
            cls.valid_time_filter(now),
            user_id=user_id,
            permission_id__in=permission_ids,
            permission__status=1,
            effect=cls.EFFECT_DENY,
        ).aexists()

    @classmethod
    async def has_role_allow(
        cls,
        user_id: int,
        permission_ids: list[int],
        now,
        role_scope: str,
    ) -> bool:
        role_ids = IamUserRole.objects.using(IAM_DB_ALIAS).filter(
            user_id=user_id,
            role__status=1,
            role__role_scope=role_scope,
        ).values("role_id")

        return await IamRolePermission.objects.using(IAM_DB_ALIAS).filter(
            cls.valid_time_filter(now),
            role_id__in=role_ids,
            permission_id__in=permission_ids,
            permission__status=1,
        ).aexists()

    @classmethod
    async def has_department_allow(
        cls,
        department_id: int,
        permission_ids: list[int],
        now,
    ) -> bool:
        return await IamDepartmentPermission.objects.using(IAM_DB_ALIAS).filter(
            cls.valid_time_filter(now),
            department_id=department_id,
            permission_id__in=permission_ids,
            permission__status=1,
            effect=cls.EFFECT_ALLOW,
        ).aexists()

    @classmethod
    async def has_department_deny(
        cls,
        department_id: int,
        permission_ids: list[int],
        now,
    ) -> bool:
        return await IamDepartmentPermission.objects.using(IAM_DB_ALIAS).filter(
            cls.valid_time_filter(now),
            department_id=department_id,
            permission_id__in=permission_ids,
            permission__status=1,
            effect=cls.EFFECT_DENY,
        ).aexists()

    @classmethod
    async def has_subsidiary_allow(
        cls,
        subsidiary_id: int,
        permission_ids: list[int],
        now,
    ) -> bool:
        return await IamSubsidiaryPermission.objects.using(IAM_DB_ALIAS).filter(
            cls.valid_time_filter(now),
            subsidiary_id=subsidiary_id,
            permission_id__in=permission_ids,
            permission__status=1,
            effect=cls.EFFECT_ALLOW,
        ).aexists()

    @classmethod
    async def has_subsidiary_deny(
        cls,
        subsidiary_id: int,
        permission_ids: list[int],
        now,
    ) -> bool:
        return await IamSubsidiaryPermission.objects.using(IAM_DB_ALIAS).filter(
            cls.valid_time_filter(now),
            subsidiary_id=subsidiary_id,
            permission_id__in=permission_ids,
            permission__status=1,
            effect=cls.EFFECT_DENY,
        ).aexists()
