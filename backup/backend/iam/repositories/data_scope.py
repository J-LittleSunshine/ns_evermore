# -*- coding: utf-8 -*-
from __future__ import annotations

from django.db.models import Q

from iam.constants import IAM_DB_ALIAS
from iam.models import (
    IamDepartment,
    IamDepartmentPermission,
    IamRolePermission,
    IamSubsidiaryPermission,
    IamUserPermission,
    IamUserRole,
)


class DataScopeRepository:
    EFFECT_ALLOW = "ALLOW"
    EFFECT_DENY = "DENY"
    MAX_DEPARTMENT_TREE_DEPTH = 20

    @staticmethod
    def valid_time_filter(now):
        return Q(expired_at__isnull=True) | Q(expired_at__gt=now)

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

    @classmethod
    async def get_user_allow_scopes(
        cls,
        user_id: int,
        permission_ids: list[int],
        now,
    ) -> list[str]:
        queryset = IamUserPermission.objects.using(IAM_DB_ALIAS).filter(
            cls.valid_time_filter(now),
            user_id=user_id,
            permission_id__in=permission_ids,
            permission__status=1,
            effect=cls.EFFECT_ALLOW,
            data_scope__isnull=False,
        ).values_list("data_scope", flat=True)
        return [scope async for scope in queryset if scope]

    @classmethod
    async def get_role_allow_scopes(
        cls,
        user_id: int,
        permission_ids: list[int],
        now,
        role_scope: str,
        company_id: int | None = None,
    ) -> list[str]:
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
            permission_id__in=permission_ids,
            permission__status=1,
            data_scope__isnull=False,
        ).values_list("data_scope", flat=True)
        return [scope async for scope in queryset if scope]

    @classmethod
    async def get_department_allow_scopes(
        cls,
        department_id: int,
        permission_ids: list[int],
        now,
    ) -> list[str]:
        queryset = IamDepartmentPermission.objects.using(IAM_DB_ALIAS).filter(
            cls.valid_time_filter(now),
            department_id=department_id,
            permission_id__in=permission_ids,
            permission__status=1,
            effect=cls.EFFECT_ALLOW,
            data_scope__isnull=False,
        ).values_list("data_scope", flat=True)
        return [scope async for scope in queryset if scope]

    @classmethod
    async def get_subsidiary_allow_scopes(
        cls,
        subsidiary_id: int,
        permission_ids: list[int],
        now,
    ) -> list[str]:
        queryset = IamSubsidiaryPermission.objects.using(IAM_DB_ALIAS).filter(
            cls.valid_time_filter(now),
            subsidiary_id=subsidiary_id,
            permission_id__in=permission_ids,
            permission__status=1,
            effect=cls.EFFECT_ALLOW,
            data_scope__isnull=False,
        ).values_list("data_scope", flat=True)
        return [scope async for scope in queryset if scope]

    @classmethod
    async def get_descendant_department_ids(
        cls,
        company_id: int,
        department_id: int | None,
    ) -> list[int]:
        if not department_id:
            return []

        seen_ids: set[int] = {department_id}
        result: list[int] = [department_id]
        current_level_ids: list[int] = [department_id]

        for _ in range(cls.MAX_DEPARTMENT_TREE_DEPTH):
            if not current_level_ids:
                break

            queryset = IamDepartment.objects.using(IAM_DB_ALIAS).filter(
                company_id=company_id,
                parent_id__in=current_level_ids,
            ).values_list("id", flat=True)
            child_ids = [department_id async for department_id in queryset]

            next_level_ids: list[int] = []
            for child_id in child_ids:
                if child_id in seen_ids:
                    continue
                seen_ids.add(child_id)
                result.append(child_id)
                next_level_ids.append(child_id)

            current_level_ids = next_level_ids

        return result


__all__ = ["DataScopeRepository"]

