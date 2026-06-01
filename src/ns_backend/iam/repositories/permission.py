# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import Q

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
    """Repository for IAM permission resolution."""

    SUBJECT_USER = "user"
    SUBJECT_DEPARTMENT = "department"
    SUBJECT_SUBSIDIARY = "subsidiary"

    @staticmethod
    def valid_time_q(now) -> Q:
        """Build validity time query."""
        return Q(expired_at__isnull=True) | Q(expired_at__gt=now)

    @staticmethod
    async def get_active_permission_by_code(permission_code: str) -> IamPermission | None:
        """Load one active permission by code."""
        return await IamPermission.objects.filter(status=1, permission_code=permission_code).only("id", "parent_id").afirst()

    @staticmethod
    async def get_active_permission_by_id(permission_id: int) -> IamPermission | None:
        """Load one active permission by id."""
        return await IamPermission.objects.filter(id=permission_id, status=1).only("id", "parent_id").afirst()

    @staticmethod
    async def list_active_permissions() -> list[dict]:
        """List active permissions for permission-code and menu resolution."""
        queryset = IamPermission.objects.filter(status=1).values(
            "id",
            "permission_code",
            "permission_name",
            "permission_type",
            "parent_id",
        ).order_by("permission_code")
        return [row async for row in queryset]

    @classmethod
    async def has_direct_effect(cls, *, subject_type: str, subject_id: int, permission_ids: list[int], effect: str, now) -> bool:
        """Check direct user/department/subsidiary permission effect."""
        model_class, subject_field = cls._resolve_subject_model(subject_type)
        return await model_class.objects.filter(
            cls.valid_time_q(now),
            **{subject_field: subject_id},
            permission_id__in=permission_ids,
            permission__status=1,
            effect=effect,
        ).aexists()

    @classmethod
    async def has_role_permission(cls, *, user_id: int, permission_ids: list[int], now, role_scope: str, company_id: int | None) -> bool:
        """Check role permission allow status."""
        role_filter = cls._build_role_filter(user_id=user_id, role_scope=role_scope, company_id=company_id)
        role_ids = IamUserRole.objects.filter(**role_filter).values("role_id")

        return await IamRolePermission.objects.filter(
            cls.valid_time_q(now),
            role_id__in=role_ids,
            permission_id__in=permission_ids,
            permission__status=1,
        ).aexists()

    @classmethod
    async def list_user_permission_ids(cls, *, user_id: int, now, effect: str) -> set[int]:
        """List direct user permission ids by effect."""
        queryset = IamUserPermission.objects.filter(
            cls.valid_time_q(now),
            user_id=user_id,
            permission__status=1,
            effect=effect,
        ).values_list("permission_id", flat=True)
        return {item async for item in queryset}

    @classmethod
    async def list_department_permission_ids(cls, *, department_id: int, now, effect: str) -> set[int]:
        """List department permission ids by effect."""
        queryset = IamDepartmentPermission.objects.filter(
            cls.valid_time_q(now),
            department_id=department_id,
            permission__status=1,
            effect=effect,
        ).values_list("permission_id", flat=True)
        return {item async for item in queryset}

    @classmethod
    async def list_subsidiary_permission_ids(cls, *, subsidiary_id: int, now, effect: str) -> set[int]:
        """List subsidiary permission ids by effect."""
        queryset = IamSubsidiaryPermission.objects.filter(
            cls.valid_time_q(now),
            subsidiary_id=subsidiary_id,
            permission__status=1,
            effect=effect,
        ).values_list("permission_id", flat=True)
        return {item async for item in queryset}

    @classmethod
    async def list_role_permission_ids(cls, *, user_id: int, now, role_scope: str, company_id: int | None) -> set[int]:
        """List role permission ids by role scope."""
        role_filter = cls._build_role_filter(user_id=user_id, role_scope=role_scope, company_id=company_id)
        role_ids = IamUserRole.objects.filter(**role_filter).values("role_id")
        queryset = IamRolePermission.objects.filter(
            cls.valid_time_q(now),
            role_id__in=role_ids,
            permission__status=1,
        ).values_list("permission_id", flat=True)
        return {item async for item in queryset}

    @staticmethod
    def _build_role_filter(*, user_id: int, role_scope: str, company_id: int | None) -> dict:
        """Build role lookup filter."""
        role_filter = {
            "user_id": user_id,
            "role__status": 1,
            "role__role_scope": role_scope,
        }

        if role_scope == "PERSONAL":
            role_filter["role__company_id__isnull"] = True
        elif company_id is not None:
            role_filter["role__company_id"] = company_id

        return role_filter

    @classmethod
    def _resolve_subject_model(cls, subject_type: str):
        """Resolve subject type to model and subject id field."""
        if subject_type == cls.SUBJECT_USER:
            return IamUserPermission, "user_id"

        if subject_type == cls.SUBJECT_DEPARTMENT:
            return IamDepartmentPermission, "department_id"

        if subject_type == cls.SUBJECT_SUBSIDIARY:
            return IamSubsidiaryPermission, "subsidiary_id"

        raise ValueError(f"Unsupported permission subject type: {subject_type}")
