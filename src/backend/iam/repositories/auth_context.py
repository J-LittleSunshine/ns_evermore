# -*- coding: utf-8 -*-
from __future__ import annotations

from django.db.models import Q

from iam.constants import IAM_DB_ALIAS
from iam.models import (
    IamDepartmentPermission,
    IamPermission,
    IamRolePermission,
    IamSubsidiaryPermission,
    IamUserPermission,
    IamUserRole,
)


class AuthContextRepository:
    EFFECT_ALLOW = "ALLOW"
    EFFECT_DENY = "DENY"

    @staticmethod
    def valid_time_filter(now):
        return Q(expired_at__isnull=True) | Q(expired_at__gt=now)

    @staticmethod
    async def list_active_permissions() -> list[dict]:
        queryset = IamPermission.objects.using(IAM_DB_ALIAS).filter(
            status=1,
        ).values(
            "id",
            "permission_code",
            "permission_name",
            "permission_type",
            "parent_id",
        ).order_by("permission_code")
        return [row async for row in queryset]

    @classmethod
    async def list_user_allow_permission_ids(cls, user_id: int, now) -> set[int]:
        queryset = IamUserPermission.objects.using(IAM_DB_ALIAS).filter(
            cls.valid_time_filter(now),
            user_id=user_id,
            permission__status=1,
            effect=cls.EFFECT_ALLOW,
        ).values_list("permission_id", flat=True)
        return {permission_id async for permission_id in queryset}

    @classmethod
    async def list_user_deny_permission_ids(cls, user_id: int, now) -> set[int]:
        queryset = IamUserPermission.objects.using(IAM_DB_ALIAS).filter(
            cls.valid_time_filter(now),
            user_id=user_id,
            permission__status=1,
            effect=cls.EFFECT_DENY,
        ).values_list("permission_id", flat=True)
        return {permission_id async for permission_id in queryset}

    @classmethod
    async def list_role_allow_permission_ids(
        cls,
        user_id: int,
        now,
        role_scope: str,
        company_id: int | None = None,
    ) -> set[int]:
        role_filter = {
            "user_id": user_id,
            "role__status": 1,
            "role__role_scope": role_scope,
        }

        if company_id is not None:
            role_filter["role__company_id"] = company_id
        if role_scope == "PERSONAL":
            role_filter["role__company_id__isnull"] = True

        role_ids = IamUserRole.objects.using(IAM_DB_ALIAS).filter(
            **role_filter,
        ).values("role_id")

        queryset = IamRolePermission.objects.using(IAM_DB_ALIAS).filter(
            cls.valid_time_filter(now),
            role_id__in=role_ids,
            permission__status=1,
        ).values_list("permission_id", flat=True)
        return {permission_id async for permission_id in queryset}

    @classmethod
    async def list_department_allow_permission_ids(
        cls,
        department_id: int,
        now,
    ) -> set[int]:
        queryset = IamDepartmentPermission.objects.using(IAM_DB_ALIAS).filter(
            cls.valid_time_filter(now),
            department_id=department_id,
            permission__status=1,
            effect=cls.EFFECT_ALLOW,
        ).values_list("permission_id", flat=True)
        return {permission_id async for permission_id in queryset}

    @classmethod
    async def list_department_deny_permission_ids(
        cls,
        department_id: int,
        now,
    ) -> set[int]:
        queryset = IamDepartmentPermission.objects.using(IAM_DB_ALIAS).filter(
            cls.valid_time_filter(now),
            department_id=department_id,
            permission__status=1,
            effect=cls.EFFECT_DENY,
        ).values_list("permission_id", flat=True)
        return {permission_id async for permission_id in queryset}

    @classmethod
    async def list_subsidiary_allow_permission_ids(
        cls,
        subsidiary_id: int,
        now,
    ) -> set[int]:
        queryset = IamSubsidiaryPermission.objects.using(IAM_DB_ALIAS).filter(
            cls.valid_time_filter(now),
            subsidiary_id=subsidiary_id,
            permission__status=1,
            effect=cls.EFFECT_ALLOW,
        ).values_list("permission_id", flat=True)
        return {permission_id async for permission_id in queryset}

    @classmethod
    async def list_subsidiary_deny_permission_ids(
        cls,
        subsidiary_id: int,
        now,
    ) -> set[int]:
        queryset = IamSubsidiaryPermission.objects.using(IAM_DB_ALIAS).filter(
            cls.valid_time_filter(now),
            subsidiary_id=subsidiary_id,
            permission__status=1,
            effect=cls.EFFECT_DENY,
        ).values_list("permission_id", flat=True)
        return {permission_id async for permission_id in queryset}


__all__ = ["AuthContextRepository"]

