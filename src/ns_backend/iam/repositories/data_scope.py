# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import Q

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
    """Repository for IAM data-scope resolution."""

    SUBJECT_USER = "user"
    SUBJECT_DEPARTMENT = "department"
    SUBJECT_SUBSIDIARY = "subsidiary"

    @staticmethod
    def valid_time_q(now) -> Q:
        """Build validity time query."""
        return Q(expired_at__isnull=True) | Q(expired_at__gt=now)

    @classmethod
    async def has_direct_effect(cls, *, subject_type: str, subject_id: int, permission_ids: list[int], effect: str, now) -> bool:
        """Check direct data-scope effect."""
        model_class, subject_field = cls._resolve_subject_model(subject_type)
        return await model_class.objects.filter(
            cls.valid_time_q(now),
            **{subject_field: subject_id},
            permission_id__in=permission_ids,
            permission__status=1,
            effect=effect,
        ).aexists()

    @classmethod
    async def list_user_scopes(cls, *, user_id: int, permission_ids: list[int], now) -> list[str]:
        """List user data scopes."""
        queryset = IamUserPermission.objects.filter(
            cls.valid_time_q(now),
            user_id=user_id,
            permission_id__in=permission_ids,
            permission__status=1,
            effect="ALLOW",
        ).exclude(data_scope__isnull=True).values_list("data_scope", flat=True)
        return [item async for item in queryset if item]

    @classmethod
    async def list_department_scopes(cls, *, department_id: int, permission_ids: list[int], now) -> list[str]:
        """List department data scopes."""
        queryset = IamDepartmentPermission.objects.filter(
            cls.valid_time_q(now),
            department_id=department_id,
            permission_id__in=permission_ids,
            permission__status=1,
            effect="ALLOW",
        ).exclude(data_scope__isnull=True).values_list("data_scope", flat=True)
        return [item async for item in queryset if item]

    @classmethod
    async def list_subsidiary_scopes(cls, *, subsidiary_id: int, permission_ids: list[int], now) -> list[str]:
        """List subsidiary data scopes."""
        queryset = IamSubsidiaryPermission.objects.filter(
            cls.valid_time_q(now),
            subsidiary_id=subsidiary_id,
            permission_id__in=permission_ids,
            permission__status=1,
            effect="ALLOW",
        ).exclude(data_scope__isnull=True).values_list("data_scope", flat=True)
        return [item async for item in queryset if item]

    @classmethod
    async def list_role_scopes(cls, *, user_id: int, permission_ids: list[int], now, role_scope: str, company_id: int | None) -> list[str]:
        """List role data scopes."""
        role_filter = {
            "user_id": user_id,
            "role__status": 1,
            "role__role_scope": role_scope,
        }

        if role_scope == "PERSONAL":
            role_filter["role__company_id__isnull"] = True
        elif company_id is not None:
            role_filter["role__company_id"] = company_id

        role_ids = IamUserRole.objects.filter(**role_filter).values("role_id")
        queryset = IamRolePermission.objects.filter(
            cls.valid_time_q(now),
            role_id__in=role_ids,
            permission_id__in=permission_ids,
            permission__status=1,
        ).exclude(data_scope__isnull=True).values_list("data_scope", flat=True)
        return [item async for item in queryset if item]

    @staticmethod
    async def list_child_department_ids(*, company_id: int, parent_ids: list[int]) -> list[int]:
        """List direct child department ids."""
        queryset = IamDepartment.objects.filter(company_id=company_id, parent_id__in=parent_ids).values_list("id", flat=True)
        return [item async for item in queryset]

    @classmethod
    def _resolve_subject_model(cls, subject_type: str):
        """Resolve subject type to model and subject id field."""
        if subject_type == cls.SUBJECT_USER:
            return IamUserPermission, "user_id"

        if subject_type == cls.SUBJECT_DEPARTMENT:
            return IamDepartmentPermission, "department_id"

        if subject_type == cls.SUBJECT_SUBSIDIARY:
            return IamSubsidiaryPermission, "subsidiary_id"

        raise ValueError(f"Unsupported data-scope subject type: {subject_type}")
