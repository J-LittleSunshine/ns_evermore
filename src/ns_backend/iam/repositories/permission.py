# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    TYPE_CHECKING,
)

from django.db.models import Q

from backend.common import BaseRepository
from ns_backend.iam.constants import (
    ROLE_SCOPE_ENTERPRISE,
    ROLE_SCOPE_PERSONAL,
)
from ns_backend.iam.models import (
    IamDepartmentPermission,
    IamPermission,
    IamRolePermission,
    IamSubsidiaryPermission,
    IamUserPermission,
    IamUserRole,
)

if TYPE_CHECKING:
    pass


class PermissionRepository:

    @staticmethod
    def valid_time_filter(now) -> Q:
        return Q(expired_at__isnull=True) | Q(expired_at__gt=now)

    @staticmethod
    async def get_active_permission_by_code(permission_code: str) -> IamPermission | None:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamPermission)
        return await IamPermission.objects.using(db_alias).filter(
            status=1,
            permission_code=permission_code,
        ).only(
            "id",
            "parent_id",
        ).afirst()

    @staticmethod
    async def get_active_permission_by_id(permission_id: int) -> IamPermission | None:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamPermission)
        return await IamPermission.objects.using(db_alias).filter(
            id=permission_id,
            status=1,
        ).only(
            "id",
            "parent_id",
        ).afirst()

    @staticmethod
    async def list_active_permissions() -> list[dict[str, Any]]:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamPermission)
        queryset = IamPermission.objects.using(db_alias).filter(
            status=1,
        ).values(
            "id",
            "permission_code",
            "permission_name",
            "permission_type",
            "parent_id",
        ).order_by(
            "permission_code",
        )

        return [
            row
            async for row in queryset
        ]

    @classmethod
    async def has_user_effect(cls,*,user_id: int,permission_ids: list[int],effect: str,now) -> bool:
        return await cls._has_direct_effect(
            IamUserPermission,
            subject_field="user_id",
            subject_id=user_id,
            permission_ids=permission_ids,
            effect=effect,
            now=now,
        )

    @classmethod
    async def has_department_effect(cls,*,department_id: int,permission_ids: list[int],effect: str,now) -> bool:
        return await cls._has_direct_effect(
            IamDepartmentPermission,
            subject_field="department_id",
            subject_id=department_id,
            permission_ids=permission_ids,
            effect=effect,
            now=now,
        )

    @classmethod
    async def has_subsidiary_effect(cls,*,subsidiary_id: int,permission_ids: list[int],effect: str,now) -> bool:
        return await cls._has_direct_effect(
            IamSubsidiaryPermission,
            subject_field="subsidiary_id",
            subject_id=subsidiary_id,
            permission_ids=permission_ids,
            effect=effect,
            now=now,
        )

    @classmethod
    async def has_role_allow(cls,*,user_id: int,permission_ids: list[int],now,role_scope: str,company_id: int | None) -> bool:
        role_ids = cls._build_user_role_ids_query(
            user_id=user_id,
            role_scope=role_scope,
            company_id=company_id,
        )
        db_alias = BaseRepository.resolve_db_alias(model_class=IamRolePermission)

        return await IamRolePermission.objects.using(db_alias).filter(
            cls.valid_time_filter(now),
            role_id__in=role_ids,
            permission_id__in=permission_ids,
            permission__status=1,
        ).aexists()

    @classmethod
    async def list_user_permission_ids(cls,*,user_id: int,now,effect: str) -> set[int]:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamUserPermission)
        queryset = IamUserPermission.objects.using(db_alias).filter(
            cls.valid_time_filter(now),
            user_id=user_id,
            permission__status=1,
            effect=effect,
        ).values_list(
            "permission_id",
            flat=True,
        )

        return {
            item
            async for item in queryset
        }

    @classmethod
    async def list_department_permission_ids(cls,*,department_id: int,now,effect: str) -> set[int]:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamDepartmentPermission)
        queryset = IamDepartmentPermission.objects.using(db_alias).filter(
            cls.valid_time_filter(now),
            department_id=department_id,
            permission__status=1,
            effect=effect,
        ).values_list(
            "permission_id",
            flat=True,
        )

        return {
            item
            async for item in queryset
        }

    @classmethod
    async def list_subsidiary_permission_ids(cls,*,subsidiary_id: int,now,effect: str) -> set[int]:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamSubsidiaryPermission)
        queryset = IamSubsidiaryPermission.objects.using(db_alias).filter(
            cls.valid_time_filter(now),
            subsidiary_id=subsidiary_id,
            permission__status=1,
            effect=effect,
        ).values_list(
            "permission_id",
            flat=True,
        )

        return {
            item
            async for item in queryset
        }

    @classmethod
    async def list_role_permission_ids(cls,*,user_id: int,now,role_scope: str, company_id: int | None) -> set[int]:
        role_ids = cls._build_user_role_ids_query(
            user_id=user_id,
            role_scope=role_scope,
            company_id=company_id,
        )
        db_alias = BaseRepository.resolve_db_alias(model_class=IamRolePermission)

        queryset = IamRolePermission.objects.using(db_alias).filter(
            cls.valid_time_filter(now),
            role_id__in=role_ids,
            permission__status=1,
        ).values_list(
            "permission_id",
            flat=True,
        )

        return {
            item
            async for item in queryset
        }

    @classmethod
    async def _has_direct_effect(cls,model_class,*,subject_field: str,subject_id: int,permission_ids: list[int],effect: str,now) -> bool:
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
    def _build_user_role_ids_query(*,user_id: int,role_scope: str,company_id: int | None):
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
