# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.policies.data_scope import DataScopePolicy
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
        cls.ensure_required_pair(user_id, role_id, "user_id and role_id cannot be empty", 13011)
        await GrantPolicy.ensure_can_bind_user_role(user_id=user_id, role_id=role_id, operator=operator)
        create_data = cls.fill_create_audit_fields(data, operator_id=operator_id)
        item = await GrantRepository.create_user_role(create_data)
        return {"id": item.id}

    @classmethod
    async def unbind_user_role(cls, user_id: int, role_id: int, operator) -> None:
        cls.ensure_required_pair(user_id, role_id, "user_id and role_id cannot be empty", 13011)
        await GrantPolicy.ensure_can_bind_user_role(user_id=user_id, role_id=role_id, operator=operator)
        deleted_count = await GrantRepository.delete_user_role(user_id=user_id, role_id=role_id)
        cls.ensure_deleted_rows(deleted_count, "User-role relationship does not exist", 13002)

    @classmethod
    async def grant_role_permission(cls, data: dict, operator, operator_id: int | None = None) -> dict:
        role_id = data.get("role_id")
        permission_id = data.get("permission_id")
        data_scope = data.get("data_scope")
        cls.ensure_required_pair(role_id, permission_id, "role_id and permission_id cannot be empty", 13012)

        await GrantPolicy.ensure_can_operate_role(role_id=role_id, operator=operator)
        await DataScopePolicy.ensure_grant_data_scope(
            permission_id=permission_id,
            data_scope=data_scope,
            role_permission=True,
        )
        create_data = cls.fill_grant_audit_fields(data, operator_id=operator_id)
        item = await GrantRepository.create_role_permission(create_data)
        return {"id": item.id}

    @classmethod
    async def revoke_role_permission(cls, role_id: int, permission_id: int, operator) -> None:
        cls.ensure_required_pair(role_id, permission_id, "role_id and permission_id cannot be empty", 13012)
        await GrantPolicy.ensure_can_operate_role(role_id=role_id, operator=operator)
        deleted_count = await GrantRepository.delete_role_permission(role_id=role_id, permission_id=permission_id)
        cls.ensure_deleted_rows(deleted_count, "Role-permission relationship does not exist", 13004)

    @classmethod
    async def grant_user_permission(cls, data: dict, operator, operator_id: int | None = None) -> dict:
        user_id = data.get("user_id")
        permission_id = data.get("permission_id")
        effect = data.get("effect")
        data_scope = data.get("data_scope")
        cls.ensure_required_pair(user_id, permission_id, "user_id and permission_id cannot be empty", 13013)

        await GrantPolicy.ensure_can_operate_user(user_id=user_id, operator=operator)
        await DataScopePolicy.ensure_grant_data_scope(
            permission_id=permission_id,
            data_scope=data_scope,
            effect=effect,
        )
        create_data = cls.fill_grant_audit_fields(data, operator_id=operator_id)
        item = await GrantRepository.create_user_permission(create_data)
        return {"id": item.id}

    @classmethod
    async def revoke_user_permission(cls, user_id: int, permission_id: int, operator) -> None:
        cls.ensure_required_pair(user_id, permission_id, "user_id and permission_id cannot be empty", 13013)
        await GrantPolicy.ensure_can_operate_user(user_id=user_id, operator=operator)
        deleted_count = await GrantRepository.delete_user_permission(user_id=user_id, permission_id=permission_id)
        cls.ensure_deleted_rows(deleted_count, "User-permission relationship does not exist", 13006)

    @classmethod
    async def grant_department_permission(cls, data: dict, operator, operator_id: int | None = None) -> dict:
        department_id = data.get("department_id")
        permission_id = data.get("permission_id")
        effect = data.get("effect")
        data_scope = data.get("data_scope")
        cls.ensure_required_pair(department_id, permission_id, "department_id and permission_id cannot be empty", 13014)

        await GrantPolicy.ensure_can_operate_department(department_id=department_id, operator=operator)
        await DataScopePolicy.ensure_grant_data_scope(
            permission_id=permission_id,
            data_scope=data_scope,
            effect=effect,
        )
        create_data = cls.fill_grant_audit_fields(data, operator_id=operator_id)
        item = await GrantRepository.create_department_permission(create_data)
        return {"id": item.id}

    @classmethod
    async def revoke_department_permission(cls, department_id: int, permission_id: int, operator) -> None:
        cls.ensure_required_pair(department_id, permission_id, "department_id and permission_id cannot be empty", 13014)
        await GrantPolicy.ensure_can_operate_department(department_id=department_id, operator=operator)
        deleted_count = await GrantRepository.delete_department_permission(
            department_id=department_id,
            permission_id=permission_id,
        )
        cls.ensure_deleted_rows(deleted_count, "Department-permission relationship does not exist", 13008)

    @classmethod
    async def grant_subsidiary_permission(cls, data: dict, operator, operator_id: int | None = None) -> dict:
        subsidiary_id = data.get("subsidiary_id")
        permission_id = data.get("permission_id")
        effect = data.get("effect")
        data_scope = data.get("data_scope")
        cls.ensure_required_pair(subsidiary_id, permission_id, "subsidiary_id and permission_id cannot be empty", 13015)

        await GrantPolicy.ensure_can_operate_subsidiary(subsidiary_id=subsidiary_id, operator=operator)
        await DataScopePolicy.ensure_grant_data_scope(
            permission_id=permission_id,
            data_scope=data_scope,
            effect=effect,
        )
        create_data = cls.fill_grant_audit_fields(data, operator_id=operator_id)
        item = await GrantRepository.create_subsidiary_permission(create_data)
        return {"id": item.id}

    @classmethod
    async def revoke_subsidiary_permission(cls, subsidiary_id: int, permission_id: int, operator) -> None:
        cls.ensure_required_pair(subsidiary_id, permission_id, "subsidiary_id and permission_id cannot be empty", 13015)
        await GrantPolicy.ensure_can_operate_subsidiary(subsidiary_id=subsidiary_id, operator=operator)
        deleted_count = await GrantRepository.delete_subsidiary_permission(
            subsidiary_id=subsidiary_id,
            permission_id=permission_id,
        )
        cls.ensure_deleted_rows(deleted_count, "Subsidiary-permission relationship does not exist", 13010)


    @staticmethod
    def ensure_deleted_rows(deleted_count: int, message: str, code: int) -> None:
        if deleted_count <= 0:
            raise BusinessError(message, code)

    @staticmethod
    def ensure_required_pair(left_value, right_value, message: str, code: int) -> None:
        if not left_value or not right_value:
            raise BusinessError(message, code)


__all__ = ["GrantService"]

