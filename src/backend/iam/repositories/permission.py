# -*- coding: utf-8 -*-
from __future__ import annotations

from django.db.models import Q

from iam.constants import IAM_DB_ALIAS
from iam.models import (
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

    @staticmethod
    def valid_time_filter(now):
        """权限有效期过滤条件。"""
        return Q(expired_at__isnull=True) | Q(expired_at__gt=now)

    @classmethod
    async def has_user_allow(cls, user_id: int, permission_code: str, now) -> bool:
        return await IamUserPermission.objects.using(IAM_DB_ALIAS).filter(
            cls.valid_time_filter(now),
            user_id=user_id,
            permission__permission_code=permission_code,
            permission__status=1,
            effect=cls.EFFECT_ALLOW,
        ).aexists()

    @classmethod
    async def has_user_deny(cls, user_id: int, permission_code: str, now) -> bool:
        return await IamUserPermission.objects.using(IAM_DB_ALIAS).filter(
            cls.valid_time_filter(now),
            user_id=user_id,
            permission__permission_code=permission_code,
            permission__status=1,
            effect=cls.EFFECT_DENY,
        ).aexists()

    @classmethod
    async def has_role_allow(cls, user_id: int, permission_code: str, now) -> bool:
        role_ids = IamUserRole.objects.using(IAM_DB_ALIAS).filter(
            user_id=user_id,
            role__status=1,
        ).values("role_id")

        return await IamRolePermission.objects.using(IAM_DB_ALIAS).filter(
            cls.valid_time_filter(now),
            role_id__in=role_ids,
            permission__permission_code=permission_code,
            permission__status=1,
        ).aexists()

    @classmethod
    async def has_department_allow(
        cls,
        department_id: int,
        permission_code: str,
        now,
    ) -> bool:
        return await IamDepartmentPermission.objects.using(IAM_DB_ALIAS).filter(
            cls.valid_time_filter(now),
            department_id=department_id,
            permission__permission_code=permission_code,
            permission__status=1,
            effect=cls.EFFECT_ALLOW,
        ).aexists()

    @classmethod
    async def has_department_deny(
        cls,
        department_id: int,
        permission_code: str,
        now,
    ) -> bool:
        return await IamDepartmentPermission.objects.using(IAM_DB_ALIAS).filter(
            cls.valid_time_filter(now),
            department_id=department_id,
            permission__permission_code=permission_code,
            permission__status=1,
            effect=cls.EFFECT_DENY,
        ).aexists()

    @classmethod
    async def has_subsidiary_allow(
        cls,
        subsidiary_id: int,
        permission_code: str,
        now,
    ) -> bool:
        return await IamSubsidiaryPermission.objects.using(IAM_DB_ALIAS).filter(
            cls.valid_time_filter(now),
            subsidiary_id=subsidiary_id,
            permission__permission_code=permission_code,
            permission__status=1,
            effect=cls.EFFECT_ALLOW,
        ).aexists()

    @classmethod
    async def has_subsidiary_deny(
        cls,
        subsidiary_id: int,
        permission_code: str,
        now,
    ) -> bool:
        return await IamSubsidiaryPermission.objects.using(IAM_DB_ALIAS).filter(
            cls.valid_time_filter(now),
            subsidiary_id=subsidiary_id,
            permission__permission_code=permission_code,
            permission__status=1,
            effect=cls.EFFECT_DENY,
        ).aexists()
