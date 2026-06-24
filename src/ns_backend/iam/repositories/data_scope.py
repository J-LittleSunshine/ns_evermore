# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    TYPE_CHECKING,
)

from django.db.models import Q

from backend.common import BaseRepository
from ns_backend.iam.constants import (
    PERMISSION_EFFECT_ALLOW,
    ROLE_SCOPE_ENTERPRISE,
    ROLE_SCOPE_PERSONAL,
)
from ns_backend.iam.models import (
    IamDepartment,
    IamDepartmentPermission,
    IamRolePermission,
    IamSubsidiaryPermission,
    IamUserPermission,
    IamUserRole,
)

if TYPE_CHECKING:
    pass


class DataScopeRepository:
    MAX_DEPARTMENT_TREE_DEPTH = 20

    @staticmethod
    def valid_time_filter(now) -> Q:
        return Q(expired_at__isnull=True) | Q(expired_at__gt=now)

    @classmethod
    async def has_user_effect(cls, *, user_id: int, permission_ids: list[int], effect: str, now) -> bool:
        return await cls._has_direct_effect(
            IamUserPermission,
            subject_field="user_id",
            subject_id=user_id,
            permission_ids=permission_ids,
            effect=effect,
            now=now,
        )

    @classmethod
    async def has_department_effect(cls, *, department_id: int, permission_ids: list[int], effect: str, now) -> bool:
        return await cls._has_direct_effect(
            IamDepartmentPermission,
            subject_field="department_id",
            subject_id=department_id,
            permission_ids=permission_ids,
            effect=effect,
            now=now,
        )

    @classmethod
    async def has_subsidiary_effect(cls, *, subsidiary_id: int, permission_ids: list[int], effect: str, now) -> bool:
        return await cls._has_direct_effect(
            IamSubsidiaryPermission,
            subject_field="subsidiary_id",
            subject_id=subsidiary_id,
            permission_ids=permission_ids,
            effect=effect,
            now=now,
        )

    @classmethod
    async def list_user_scopes(cls, *, user_id: int, permission_ids: list[int], now) -> list[str]:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamUserPermission)
        queryset = IamUserPermission.objects.using(db_alias).filter(
            cls.valid_time_filter(now),
            user_id=user_id,
            permission_id__in=permission_ids,
            permission__status=1,
            effect=PERMISSION_EFFECT_ALLOW,
        ).exclude(
            data_scope__isnull=True,
        ).values_list(
            "data_scope",
            flat=True,
        )

        return [
            item
            async for item in queryset
            if item
        ]

    @classmethod
    async def list_department_scopes(cls, *, department_id: int, permission_ids: list[int], now) -> list[str]:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamDepartmentPermission)
        queryset = IamDepartmentPermission.objects.using(db_alias).filter(
            cls.valid_time_filter(now),
            department_id=department_id,
            permission_id__in=permission_ids,
            permission__status=1,
            effect=PERMISSION_EFFECT_ALLOW,
        ).exclude(
            data_scope__isnull=True,
        ).values_list(
            "data_scope",
            flat=True,
        )

        return [
            item
            async for item in queryset
            if item
        ]

    @classmethod
    async def list_subsidiary_scopes(cls, *, subsidiary_id: int, permission_ids: list[int], now) -> list[str]:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamSubsidiaryPermission)
        queryset = IamSubsidiaryPermission.objects.using(db_alias).filter(
            cls.valid_time_filter(now),
            subsidiary_id=subsidiary_id,
            permission_id__in=permission_ids,
            permission__status=1,
            effect=PERMISSION_EFFECT_ALLOW,
        ).exclude(
            data_scope__isnull=True,
        ).values_list(
            "data_scope",
            flat=True,
        )

        return [
            item
            async for item in queryset
            if item
        ]

    @classmethod
    async def list_role_scopes(cls, *, user_id: int, permission_ids: list[int], now, role_scope: str, company_id: int | None) -> list[str]:
        role_ids = cls._build_user_role_ids_query(
            user_id=user_id,
            role_scope=role_scope,
            company_id=company_id,
        )
        db_alias = BaseRepository.resolve_db_alias(model_class=IamRolePermission)

        queryset = IamRolePermission.objects.using(db_alias).filter(
            cls.valid_time_filter(now),
            role_id__in=role_ids,
            permission_id__in=permission_ids,
            permission__status=1,
        ).exclude(
            data_scope__isnull=True,
        ).values_list(
            "data_scope",
            flat=True,
        )

        return [
            item
            async for item in queryset
            if item
        ]

    @classmethod
    async def list_descendant_department_ids(cls, *, company_id: int | None, department_id: int | None) -> list[int]:
        if not company_id or not department_id:
            return []

        seen_ids: set[int] = {
            department_id,
        }
        result_ids: list[int] = [
            department_id,
        ]
        frontier_ids: list[int] = [
            department_id,
        ]

        db_alias = BaseRepository.resolve_db_alias(model_class=IamDepartment)

        for _ in range(cls.MAX_DEPARTMENT_TREE_DEPTH):
            if not frontier_ids:
                break

            queryset = IamDepartment.objects.using(db_alias).filter(
                company_id=company_id,
                parent_id__in=frontier_ids,
            ).values_list(
                "id",
                flat=True,
            )
            child_ids = [
                item
                async for item in queryset
            ]

            next_frontier_ids: list[int] = []
            for child_id in child_ids:
                if child_id in seen_ids:
                    continue

                seen_ids.add(child_id)
                result_ids.append(child_id)
                next_frontier_ids.append(child_id)

            frontier_ids = next_frontier_ids

        return result_ids

    @classmethod
    async def _has_direct_effect(cls, model_class, *, subject_field: str, subject_id: int, permission_ids: list[int], effect: str, now) -> bool:
        db_alias = BaseRepository.resolve_db_alias(model_class=model_class)

        return await model_class.objects.using(db_alias).filter(
            cls.valid_time_filter(now),
            **{
                subject_field: subject_id,
            },
            permission_id__in=permission_ids,
            permission__status=1,
            effect=effect,
        ).aexists()

    @staticmethod
    def _build_user_role_ids_query(*, user_id: int, role_scope: str, company_id: int | None):
        role_filter: dict[str, Any] = {
            "user_id": user_id,
            "role__status": 1,
            "role__role_scope": role_scope,
        }

        if role_scope == ROLE_SCOPE_PERSONAL:
            role_filter["role__company_id__isnull"] = True
        elif role_scope == ROLE_SCOPE_ENTERPRISE and company_id is not None:
            role_filter["role__company_id"] = company_id

        db_alias = BaseRepository.resolve_db_alias(model_class=IamUserRole)

        return IamUserRole.objects.using(db_alias).filter(
            **role_filter,
        ).values(
            "role_id",
        )
