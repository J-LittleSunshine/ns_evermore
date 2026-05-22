# -*- coding: utf-8 -*-
from __future__ import annotations

from django.db import IntegrityError

from iam.constants import IAM_DB_ALIAS
from iam.models import (
    IamDepartment,
    IamDepartmentPermission,
    IamPermission,
    IamRole,
    IamRolePermission,
    IamSubsidiary,
    IamUser,
    IamSubsidiaryPermission,
    IamUserPermission,
    IamUserRole,
)
from ns_backend.exceptions import BusinessError


class GrantRepository:
    """授权关系数据访问层。"""

    @staticmethod
    async def create_user_role(data: dict) -> IamUserRole:
        try:
            return await IamUserRole.objects.using(IAM_DB_ALIAS).acreate(**data)
        except IntegrityError as exc:
            raise BusinessError(f"Failed to bind user role: {exc}", 13001)

    @staticmethod
    async def delete_user_role(user_id: int, role_id: int) -> int:
        deleted_count, _ = await IamUserRole.objects.using(IAM_DB_ALIAS).filter(
            user_id=user_id,
            role_id=role_id,
        ).adelete()
        return deleted_count

    @staticmethod
    async def create_role_permission(data: dict) -> IamRolePermission:
        try:
            return await IamRolePermission.objects.using(IAM_DB_ALIAS).acreate(**data)
        except IntegrityError as exc:
            raise BusinessError(f"Failed to grant role permission: {exc}", 13003)

    @staticmethod
    async def delete_role_permission(role_id: int, permission_id: int) -> int:
        deleted_count, _ = await IamRolePermission.objects.using(IAM_DB_ALIAS).filter(
            role_id=role_id,
            permission_id=permission_id,
        ).adelete()
        return deleted_count

    @staticmethod
    async def create_user_permission(data: dict) -> IamUserPermission:
        try:
            return await IamUserPermission.objects.using(IAM_DB_ALIAS).acreate(**data)
        except IntegrityError as exc:
            raise BusinessError(f"Failed to grant user permission: {exc}", 13005)

    @staticmethod
    async def delete_user_permission(user_id: int, permission_id: int) -> int:
        deleted_count, _ = await IamUserPermission.objects.using(IAM_DB_ALIAS).filter(
            user_id=user_id,
            permission_id=permission_id,
        ).adelete()
        return deleted_count

    @staticmethod
    async def create_department_permission(data: dict) -> IamDepartmentPermission:
        try:
            return await IamDepartmentPermission.objects.using(IAM_DB_ALIAS).acreate(**data)
        except IntegrityError as exc:
            raise BusinessError(f"Failed to grant department permission: {exc}", 13007)

    @staticmethod
    async def delete_department_permission(department_id: int, permission_id: int) -> int:
        deleted_count, _ = await IamDepartmentPermission.objects.using(IAM_DB_ALIAS).filter(
            department_id=department_id,
            permission_id=permission_id,
        ).adelete()
        return deleted_count

    @staticmethod
    async def create_subsidiary_permission(data: dict) -> IamSubsidiaryPermission:
        try:
            return await IamSubsidiaryPermission.objects.using(IAM_DB_ALIAS).acreate(**data)
        except IntegrityError as exc:
            raise BusinessError(f"Failed to grant subsidiary permission: {exc}", 13009)

    @staticmethod
    async def delete_subsidiary_permission(subsidiary_id: int, permission_id: int) -> int:
        deleted_count, _ = await IamSubsidiaryPermission.objects.using(IAM_DB_ALIAS).filter(
            subsidiary_id=subsidiary_id,
            permission_id=permission_id,
        ).adelete()
        return deleted_count

    @staticmethod
    async def get_user_company_id(user_id: int) -> int | None:
        item = await IamUser.objects.using(IAM_DB_ALIAS).filter(id=user_id).values("company_id").afirst()
        return None if not item else item.get("company_id")

    @staticmethod
    async def user_exists(user_id: int) -> bool:
        return await IamUser.objects.using(IAM_DB_ALIAS).filter(id=user_id).aexists()

    @staticmethod
    async def get_role_company_id(role_id: int) -> int | None:
        item = await IamRole.objects.using(IAM_DB_ALIAS).filter(id=role_id).values("company_id").afirst()
        return None if not item else item.get("company_id")

    @staticmethod
    async def get_department_company_id(department_id: int) -> int | None:
        item = await IamDepartment.objects.using(IAM_DB_ALIAS).filter(id=department_id).values("company_id").afirst()
        return None if not item else item.get("company_id")

    @staticmethod
    async def get_subsidiary_company_id(subsidiary_id: int) -> int | None:
        item = await IamSubsidiary.objects.using(IAM_DB_ALIAS).filter(id=subsidiary_id).values("company_id").afirst()
        return None if not item else item.get("company_id")

    @staticmethod
    async def get_role_scope_and_company_id(role_id: int) -> tuple[str, int | None] | None:
        item = await IamRole.objects.using(IAM_DB_ALIAS).filter(id=role_id).values("role_scope", "company_id").afirst()

        if not item:
            return None

        return item["role_scope"], item.get("company_id")

    @staticmethod
    async def get_permission_type(permission_id: int) -> str | None:
        row = await IamPermission.objects.using(IAM_DB_ALIAS).filter(
            id=permission_id,
        ).values("permission_type").afirst()

        if not row:
            return None

        return row.get("permission_type")

