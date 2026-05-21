# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.policies.grant import GrantPolicy
from iam.repositories.grant import GrantRepository
from ns_backend.exceptions import BusinessError
from ns_backend.utils.audit import AuditDataMixin


class GrantService(AuditDataMixin):
    """IAM 授权关系服务。"""

    @classmethod
    async def bind_user_role(cls, data: dict, operator, operator_id: int | None = None) -> dict:
        user_id = data.get("user_id")
        role_id = data.get("role_id")
        cls.ensure_required_pair(user_id, role_id, "user_id 和 role_id 不能为空", 13011)
        await GrantPolicy.ensure_can_bind_user_role(user_id=user_id, role_id=role_id, operator=operator)
        create_data = cls.fill_create_audit_fields(data, operator_id=operator_id)
        item = await GrantRepository.create_user_role(create_data)
        return {"id": item.id}

    @classmethod
    async def unbind_user_role(cls, user_id: int, role_id: int, operator) -> None:
        cls.ensure_required_pair(user_id, role_id, "user_id 和 role_id 不能为空", 13011)
        await GrantPolicy.ensure_can_bind_user_role(user_id=user_id, role_id=role_id, operator=operator)
        deleted_count = await GrantRepository.delete_user_role(user_id=user_id, role_id=role_id)
        cls.ensure_deleted_rows(deleted_count, "用户角色关系不存在", 13002)

    @classmethod
    async def grant_role_permission(cls, data: dict, operator, operator_id: int | None = None) -> dict:
        role_id = data.get("role_id")
        permission_id = data.get("permission_id")
        cls.ensure_required_pair(role_id, permission_id, "role_id 和 permission_id 不能为空", 13012)

        await GrantPolicy.ensure_can_operate_role(role_id=role_id, operator=operator)
        create_data = cls.fill_grant_audit_fields(data, operator_id=operator_id)
        item = await GrantRepository.create_role_permission(create_data)
        return {"id": item.id}

    @classmethod
    async def revoke_role_permission(cls, role_id: int, permission_id: int, operator) -> None:
        cls.ensure_required_pair(role_id, permission_id, "role_id 和 permission_id 不能为空", 13012)
        await GrantPolicy.ensure_can_operate_role(role_id=role_id, operator=operator)
        deleted_count = await GrantRepository.delete_role_permission(role_id=role_id, permission_id=permission_id)
        cls.ensure_deleted_rows(deleted_count, "角色权限关系不存在", 13004)

    @classmethod
    async def grant_user_permission(cls, data: dict, operator, operator_id: int | None = None) -> dict:
        user_id = data.get("user_id")
        permission_id = data.get("permission_id")
        cls.ensure_required_pair(user_id, permission_id, "user_id 和 permission_id 不能为空", 13013)

        await GrantPolicy.ensure_can_operate_user(user_id=user_id, operator=operator)
        create_data = cls.fill_grant_audit_fields(data, operator_id=operator_id)
        item = await GrantRepository.create_user_permission(create_data)
        return {"id": item.id}

    @classmethod
    async def revoke_user_permission(cls, user_id: int, permission_id: int, operator) -> None:
        cls.ensure_required_pair(user_id, permission_id, "user_id 和 permission_id 不能为空", 13013)
        await GrantPolicy.ensure_can_operate_user(user_id=user_id, operator=operator)
        deleted_count = await GrantRepository.delete_user_permission(user_id=user_id, permission_id=permission_id)
        cls.ensure_deleted_rows(deleted_count, "用户权限关系不存在", 13006)

    @classmethod
    async def grant_department_permission(cls, data: dict, operator, operator_id: int | None = None) -> dict:
        department_id = data.get("department_id")
        permission_id = data.get("permission_id")
        cls.ensure_required_pair(department_id, permission_id, "department_id 和 permission_id 不能为空", 13014)

        await GrantPolicy.ensure_can_operate_department(department_id=department_id, operator=operator)
        create_data = cls.fill_grant_audit_fields(data, operator_id=operator_id)
        item = await GrantRepository.create_department_permission(create_data)
        return {"id": item.id}

    @classmethod
    async def revoke_department_permission(cls, department_id: int, permission_id: int, operator) -> None:
        cls.ensure_required_pair(department_id, permission_id, "department_id 和 permission_id 不能为空", 13014)
        await GrantPolicy.ensure_can_operate_department(department_id=department_id, operator=operator)
        deleted_count = await GrantRepository.delete_department_permission(
            department_id=department_id,
            permission_id=permission_id,
        )
        cls.ensure_deleted_rows(deleted_count, "部门权限关系不存在", 13008)

    @classmethod
    async def grant_subsidiary_permission(cls, data: dict, operator, operator_id: int | None = None) -> dict:
        subsidiary_id = data.get("subsidiary_id")
        permission_id = data.get("permission_id")
        cls.ensure_required_pair(subsidiary_id, permission_id, "subsidiary_id 和 permission_id 不能为空", 13015)

        await GrantPolicy.ensure_can_operate_subsidiary(subsidiary_id=subsidiary_id, operator=operator)
        create_data = cls.fill_grant_audit_fields(data, operator_id=operator_id)
        item = await GrantRepository.create_subsidiary_permission(create_data)
        return {"id": item.id}

    @classmethod
    async def revoke_subsidiary_permission(cls, subsidiary_id: int, permission_id: int, operator) -> None:
        cls.ensure_required_pair(subsidiary_id, permission_id, "subsidiary_id 和 permission_id 不能为空", 13015)
        await GrantPolicy.ensure_can_operate_subsidiary(subsidiary_id=subsidiary_id, operator=operator)
        deleted_count = await GrantRepository.delete_subsidiary_permission(
            subsidiary_id=subsidiary_id,
            permission_id=permission_id,
        )
        cls.ensure_deleted_rows(deleted_count, "子公司权限关系不存在", 13010)


    @staticmethod
    def ensure_deleted_rows(deleted_count: int, message: str, code: int) -> None:
        if deleted_count <= 0:
            raise BusinessError(message, code)

    @staticmethod
    def ensure_required_pair(left_value, right_value, message: str, code: int) -> None:
        if not left_value or not right_value:
            raise BusinessError(message, code)


__all__ = ["GrantService"]

