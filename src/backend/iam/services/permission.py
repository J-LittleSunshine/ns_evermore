# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import Q
from django.utils import timezone

from iam.constants import IAM_DB_ALIAS

if TYPE_CHECKING:
    pass

from iam.models import (
    IamUser,
    IamUserPermission,
    IamUserRole,
    IamRolePermission,
    IamDepartmentPermission,
    IamSubsidiaryPermission,
)


class PermissionService:
    USER_TYPE_PERSONAL = "PERSONAL"
    USER_TYPE_ENTERPRISE = "ENTERPRISE"

    EFFECT_ALLOW = "ALLOW"
    EFFECT_DENY = "DENY"

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
            return await cls._has_personal_permission(user=user, permission_code=permission_code, now=now)

        if user.user_type == cls.USER_TYPE_ENTERPRISE:
            return await cls._has_enterprise_permission(user=user, permission_code=permission_code, now=now)

        return False

    @classmethod
    async def _has_personal_permission(cls, user: IamUser, permission_code: str, now, ) -> bool:
        if await cls._has_user_deny(user, permission_code, now):
            return False

        has_user_allow = await cls._has_user_allow(user, permission_code, now)
        has_role_allow = await cls._has_role_allow(user, permission_code, now)
        return has_user_allow or has_role_allow

    @classmethod
    async def _has_enterprise_permission(cls, user: IamUser, permission_code: str, now) -> bool:
        has_user_deny = await cls._has_user_deny(user, permission_code, now)
        has_department_deny = await cls._has_department_deny(user, permission_code, now)
        has_subsidiary_deny = await cls._has_subsidiary_deny(user, permission_code, now)
        if has_user_deny or has_department_deny or has_subsidiary_deny:
            return False

        has_user_allow = await cls._has_user_allow(user, permission_code, now)
        has_role_allow = await cls._has_role_allow(user, permission_code, now)
        has_department_allow = await cls._has_department_allow(user, permission_code, now)
        has_subsidiary_allow = await cls._has_subsidiary_allow(user, permission_code, now)

        return has_user_allow or has_role_allow or has_department_allow or has_subsidiary_allow

    @staticmethod
    def _valid_time_filter(now):
        return Q(expired_at__isnull=True) | Q(expired_at__gt=now)

    @classmethod
    async def _has_user_allow(cls, user: IamUser, permission_code: str, now) -> bool:
        return await IamUserPermission.objects.using(IAM_DB_ALIAS).filter(
            cls._valid_time_filter(now),
            user_id=user.id,
            permission__permission_code=permission_code,
            permission__status=1,
            effect=cls.EFFECT_ALLOW,
        ).aexists()

    @classmethod
    async def _has_user_deny(cls, user: IamUser, permission_code: str, now) -> bool:
        return await IamUserPermission.objects.using(IAM_DB_ALIAS).filter(
            cls._valid_time_filter(now),
            user_id=user.id,
            permission__permission_code=permission_code,
            permission__status=1,
            effect=cls.EFFECT_DENY,
        ).aexists()

    @classmethod
    async def _has_role_allow(cls, user: IamUser, permission_code: str, now) -> bool:
        role_ids = IamUserRole.objects.using(IAM_DB_ALIAS).filter(user_id=user.id, role__status=1).values("role_id")

        return await IamRolePermission.objects.using(IAM_DB_ALIAS).filter(
            cls._valid_time_filter(now),
            role_id__in=role_ids,
            permission__permission_code=permission_code,
            permission__status=1,
        ).aexists()

    @classmethod
    async def _has_department_allow(cls, user: IamUser, permission_code: str, now) -> bool:
        if not user.department_id:
            return False

        return await IamDepartmentPermission.objects.using(IAM_DB_ALIAS).filter(
            cls._valid_time_filter(now),
            department_id=user.department_id,
            permission__permission_code=permission_code,
            permission__status=1,
            effect=cls.EFFECT_ALLOW,
        ).aexists()

    @classmethod
    async def _has_department_deny(cls, user: IamUser, permission_code: str, now) -> bool:
        if not user.department_id:
            return False

        return await IamDepartmentPermission.objects.using(IAM_DB_ALIAS).filter(
            cls._valid_time_filter(now),
            department_id=user.department_id,
            permission__permission_code=permission_code,
            permission__status=1,
            effect=cls.EFFECT_DENY,
        ).aexists()

    @classmethod
    async def _has_subsidiary_allow(cls, user: IamUser, permission_code: str, now) -> bool:
        if not user.subsidiary_id:
            return False

        return await IamSubsidiaryPermission.objects.using(IAM_DB_ALIAS).filter(
            cls._valid_time_filter(now),
            subsidiary_id=user.subsidiary_id,
            permission__permission_code=permission_code,
            permission__status=1,
            effect=cls.EFFECT_ALLOW,
        ).aexists()

    @classmethod
    async def _has_subsidiary_deny(cls, user: IamUser, permission_code: str, now) -> bool:
        if not user.subsidiary_id:
            return False

        return await IamSubsidiaryPermission.objects.using(IAM_DB_ALIAS).filter(
            cls._valid_time_filter(now),
            subsidiary_id=user.subsidiary_id,
            permission__permission_code=permission_code,
            permission__status=1,
            effect=cls.EFFECT_DENY,
        ).aexists()
