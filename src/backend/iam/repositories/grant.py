# -*- coding: utf-8 -*-
from __future__ import annotations

from django.db import IntegrityError

from iam.constants import IAM_DB_ALIAS
from iam.models import (
    IamDepartmentPermission,
    IamRolePermission,
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
            raise BusinessError(f"绑定用户角色失败：{exc}", 13001)

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
            raise BusinessError(f"授予角色权限失败：{exc}", 13003)

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
            raise BusinessError(f"授予用户权限失败：{exc}", 13005)

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
            raise BusinessError(f"授予部门权限失败：{exc}", 13007)

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
            raise BusinessError(f"授予子公司权限失败：{exc}", 13009)

    @staticmethod
    async def delete_subsidiary_permission(subsidiary_id: int, permission_id: int) -> int:
        deleted_count, _ = await IamSubsidiaryPermission.objects.using(IAM_DB_ALIAS).filter(
            subsidiary_id=subsidiary_id,
            permission_id=permission_id,
        ).adelete()
        return deleted_count
