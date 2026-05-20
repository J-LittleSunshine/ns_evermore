# -*- coding: utf-8 -*-
from __future__ import annotations

from django.db import IntegrityError
from django.utils import timezone

from iam.constants import IAM_DB_ALIAS
from iam.models import (
    IamDepartmentPermission,
    IamRolePermission,
    IamSubsidiaryPermission,
    IamUserPermission,
    IamUserRole,
)
from ns_backend.exceptions import BusinessError


class GrantService:
    @staticmethod
    def prepare_grant_data(data: dict, operator_id: int | None = None) -> dict:
        now = timezone.now()
        data = data.copy()
        data["granted_by_id"] = operator_id
        data["created_by"] = operator_id
        data["updated_by"] = operator_id
        data.setdefault("created_at", now)
        data["updated_at"] = now
        return data

    @staticmethod
    def prepare_relation_data(data: dict, operator_id: int | None = None) -> dict:
        now = timezone.now()
        data = data.copy()
        data["created_by"] = operator_id
        data["updated_by"] = operator_id
        data.setdefault("created_at", now)
        data["updated_at"] = now
        return data

    @classmethod
    async def bind_user_role(cls, data: dict, operator_id: int | None = None) -> dict:
        data = cls.prepare_relation_data(data, operator_id=operator_id)

        try:
            item = await IamUserRole.objects.using(IAM_DB_ALIAS).acreate(**data)
        except IntegrityError as exc:
            raise BusinessError(f"绑定用户角色失败：{exc}", 13001)

        return {"id": item.id}

    @classmethod
    async def unbind_user_role(cls, user_id: int, role_id: int) -> None:
        deleted_count, _ = await IamUserRole.objects.using(IAM_DB_ALIAS).filter(
            user_id=user_id,
            role_id=role_id,
        ).adelete()

        if deleted_count <= 0:
            raise BusinessError("用户角色关系不存在", 13002)

    @classmethod
    async def grant_role_permission(cls, data: dict, operator_id: int | None = None) -> dict:
        data = cls.prepare_grant_data(data, operator_id=operator_id)

        try:
            item = await IamRolePermission.objects.using(IAM_DB_ALIAS).acreate(**data)
        except IntegrityError as exc:
            raise BusinessError(f"授予角色权限失败：{exc}", 13003)

        return {"id": item.id}

    @classmethod
    async def revoke_role_permission(cls, role_id: int, permission_id: int) -> None:
        deleted_count, _ = await IamRolePermission.objects.using(IAM_DB_ALIAS).filter(
            role_id=role_id,
            permission_id=permission_id,
        ).adelete()

        if deleted_count <= 0:
            raise BusinessError("角色权限关系不存在", 13004)

    @classmethod
    async def grant_user_permission(cls, data: dict, operator_id: int | None = None) -> dict:
        data = cls.prepare_grant_data(data, operator_id=operator_id)

        try:
            item = await IamUserPermission.objects.using(IAM_DB_ALIAS).acreate(**data)
        except IntegrityError as exc:
            raise BusinessError(f"授予用户权限失败：{exc}", 13005)

        return {"id": item.id}

    @classmethod
    async def revoke_user_permission(cls, user_id: int, permission_id: int) -> None:
        deleted_count, _ = await IamUserPermission.objects.using(IAM_DB_ALIAS).filter(
            user_id=user_id,
            permission_id=permission_id,
        ).adelete()

        if deleted_count <= 0:
            raise BusinessError("用户权限关系不存在", 13006)

    @classmethod
    async def grant_department_permission(cls, data: dict, operator_id: int | None = None) -> dict:
        data = cls.prepare_grant_data(data, operator_id=operator_id)

        try:
            item = await IamDepartmentPermission.objects.using(IAM_DB_ALIAS).acreate(**data)
        except IntegrityError as exc:
            raise BusinessError(f"授予部门权限失败：{exc}", 13007)

        return {"id": item.id}

    @classmethod
    async def revoke_department_permission(
        cls,
        department_id: int,
        permission_id: int,
    ) -> None:
        deleted_count, _ = await IamDepartmentPermission.objects.using(IAM_DB_ALIAS).filter(
            department_id=department_id,
            permission_id=permission_id,
        ).adelete()

        if deleted_count <= 0:
            raise BusinessError("部门权限关系不存在", 13008)

    @classmethod
    async def grant_subsidiary_permission(cls, data: dict, operator_id: int | None = None) -> dict:
        data = cls.prepare_grant_data(data, operator_id=operator_id)

        try:
            item = await IamSubsidiaryPermission.objects.using(IAM_DB_ALIAS).acreate(**data)
        except IntegrityError as exc:
            raise BusinessError(f"授予子公司权限失败：{exc}", 13009)

        return {"id": item.id}

    @classmethod
    async def revoke_subsidiary_permission(
        cls,
        subsidiary_id: int,
        permission_id: int,
    ) -> None:
        deleted_count, _ = await IamSubsidiaryPermission.objects.using(IAM_DB_ALIAS).filter(
            subsidiary_id=subsidiary_id,
            permission_id=permission_id,
        ).adelete()

        if deleted_count <= 0:
            raise BusinessError("子公司权限关系不存在", 13010)
