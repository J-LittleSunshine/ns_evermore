# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.domain.services.authorization import AuthorizationDomainService
from iam.repositories.grant import GrantRepository


class AuthorizationApplicationService:
    """IAM 授权关系应用服务。"""

    @classmethod
    async def bind_user_role(cls, data: dict, operator_id: int | None = None) -> dict:
        data = AuthorizationDomainService.build_relation_create_data(
            data=data,
            operator_id=operator_id,
        )
        item = await GrantRepository.create_user_role(data)
        return {"id": item.id}

    @classmethod
    async def unbind_user_role(cls, user_id: int, role_id: int) -> None:
        AuthorizationDomainService.ensure_required_pair(
            user_id,
            role_id,
            "user_id 和 role_id 不能为空",
            13011,
        )
        deleted_count = await GrantRepository.delete_user_role(
            user_id=user_id,
            role_id=role_id,
        )
        AuthorizationDomainService.ensure_deleted_rows(
            deleted_count,
            "用户角色关系不存在",
            13002,
        )

    @classmethod
    async def grant_role_permission(cls, data: dict, operator_id: int | None = None) -> dict:
        data = AuthorizationDomainService.build_permission_create_data(
            data=data,
            operator_id=operator_id,
        )
        item = await GrantRepository.create_role_permission(data)
        return {"id": item.id}

    @classmethod
    async def revoke_role_permission(cls, role_id: int, permission_id: int) -> None:
        AuthorizationDomainService.ensure_required_pair(
            role_id,
            permission_id,
            "role_id 和 permission_id 不能为空",
            13012,
        )
        deleted_count = await GrantRepository.delete_role_permission(
            role_id=role_id,
            permission_id=permission_id,
        )
        AuthorizationDomainService.ensure_deleted_rows(
            deleted_count,
            "角色权限关系不存在",
            13004,
        )

    @classmethod
    async def grant_user_permission(cls, data: dict, operator_id: int | None = None) -> dict:
        data = AuthorizationDomainService.build_permission_create_data(
            data=data,
            operator_id=operator_id,
        )
        item = await GrantRepository.create_user_permission(data)
        return {"id": item.id}

    @classmethod
    async def revoke_user_permission(cls, user_id: int, permission_id: int) -> None:
        AuthorizationDomainService.ensure_required_pair(
            user_id,
            permission_id,
            "user_id 和 permission_id 不能为空",
            13013,
        )
        deleted_count = await GrantRepository.delete_user_permission(
            user_id=user_id,
            permission_id=permission_id,
        )
        AuthorizationDomainService.ensure_deleted_rows(
            deleted_count,
            "用户权限关系不存在",
            13006,
        )

    @classmethod
    async def grant_department_permission(cls, data: dict, operator_id: int | None = None) -> dict:
        data = AuthorizationDomainService.build_permission_create_data(
            data=data,
            operator_id=operator_id,
        )
        item = await GrantRepository.create_department_permission(data)
        return {"id": item.id}

    @classmethod
    async def revoke_department_permission(cls, department_id: int, permission_id: int) -> None:
        AuthorizationDomainService.ensure_required_pair(
            department_id,
            permission_id,
            "department_id 和 permission_id 不能为空",
            13014,
        )
        deleted_count = await GrantRepository.delete_department_permission(
            department_id=department_id,
            permission_id=permission_id,
        )
        AuthorizationDomainService.ensure_deleted_rows(
            deleted_count,
            "部门权限关系不存在",
            13008,
        )

    @classmethod
    async def grant_subsidiary_permission(cls, data: dict, operator_id: int | None = None) -> dict:
        data = AuthorizationDomainService.build_permission_create_data(
            data=data,
            operator_id=operator_id,
        )
        item = await GrantRepository.create_subsidiary_permission(data)
        return {"id": item.id}

    @classmethod
    async def revoke_subsidiary_permission(cls, subsidiary_id: int, permission_id: int) -> None:
        AuthorizationDomainService.ensure_required_pair(
            subsidiary_id,
            permission_id,
            "subsidiary_id 和 permission_id 不能为空",
            13015,
        )
        deleted_count = await GrantRepository.delete_subsidiary_permission(
            subsidiary_id=subsidiary_id,
            permission_id=permission_id,
        )
        AuthorizationDomainService.ensure_deleted_rows(
            deleted_count,
            "子公司权限关系不存在",
            13010,
        )
