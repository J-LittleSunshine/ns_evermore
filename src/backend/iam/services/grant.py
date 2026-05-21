# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.repositories.grant import GrantRepository
from iam.services.tenant import TenantService
from ns_backend.exceptions import BusinessError
from ns_backend.utils.audit import AuditDataMixin


class GrantService(AuditDataMixin):
    """IAM 授权关系服务。"""

    @classmethod
    async def bind_user_role(cls, data: dict, operator, operator_id: int | None = None) -> dict:
        user_id = data.get("user_id")
        role_id = data.get("role_id")
        cls.ensure_required_pair(user_id, role_id, "user_id 和 role_id 不能为空", 13011)
        await cls.ensure_can_operate_user_role_pair(user_id=user_id, role_id=role_id, operator=operator)
        create_data = cls.fill_create_audit_fields(data, operator_id=operator_id)
        item = await GrantRepository.create_user_role(create_data)
        return {"id": item.id}

    @classmethod
    async def unbind_user_role(cls, user_id: int, role_id: int, operator) -> None:
        cls.ensure_required_pair(user_id, role_id, "user_id 和 role_id 不能为空", 13011)
        await cls.ensure_can_operate_user_role_pair(user_id=user_id, role_id=role_id, operator=operator)
        deleted_count = await GrantRepository.delete_user_role(user_id=user_id, role_id=role_id)
        cls.ensure_deleted_rows(deleted_count, "用户角色关系不存在", 13002)

    @classmethod
    async def grant_role_permission(cls, data: dict, operator, operator_id: int | None = None) -> dict:
        role_id = data.get("role_id")

        if not role_id:
            raise BusinessError("role_id 和 permission_id 不能为空", 13012)

        await cls.ensure_can_operate_role(role_id=role_id, operator=operator)
        create_data = cls.fill_grant_audit_fields(data, operator_id=operator_id)
        item = await GrantRepository.create_role_permission(create_data)
        return {"id": item.id}

    @classmethod
    async def revoke_role_permission(cls, role_id: int, permission_id: int, operator) -> None:
        cls.ensure_required_pair(role_id, permission_id, "role_id 和 permission_id 不能为空", 13012)
        await cls.ensure_can_operate_role(role_id=role_id, operator=operator)
        deleted_count = await GrantRepository.delete_role_permission(role_id=role_id, permission_id=permission_id)
        cls.ensure_deleted_rows(deleted_count, "角色权限关系不存在", 13004)

    @classmethod
    async def grant_user_permission(cls, data: dict, operator, operator_id: int | None = None) -> dict:
        user_id = data.get("user_id")

        if not user_id:
            raise BusinessError("user_id 和 permission_id 不能为空", 13013)

        await cls.ensure_can_operate_user(user_id=user_id, operator=operator)
        create_data = cls.fill_grant_audit_fields(data, operator_id=operator_id)
        item = await GrantRepository.create_user_permission(create_data)
        return {"id": item.id}

    @classmethod
    async def revoke_user_permission(cls, user_id: int, permission_id: int, operator) -> None:
        cls.ensure_required_pair(user_id, permission_id, "user_id 和 permission_id 不能为空", 13013)
        await cls.ensure_can_operate_user(user_id=user_id, operator=operator)
        deleted_count = await GrantRepository.delete_user_permission(user_id=user_id, permission_id=permission_id)
        cls.ensure_deleted_rows(deleted_count, "用户权限关系不存在", 13006)

    @classmethod
    async def grant_department_permission(cls, data: dict, operator, operator_id: int | None = None) -> dict:
        department_id = data.get("department_id")

        if not department_id:
            raise BusinessError("department_id 和 permission_id 不能为空", 13014)

        await cls.ensure_can_operate_department(department_id=department_id, operator=operator)
        create_data = cls.fill_grant_audit_fields(data, operator_id=operator_id)
        item = await GrantRepository.create_department_permission(create_data)
        return {"id": item.id}

    @classmethod
    async def revoke_department_permission(cls, department_id: int, permission_id: int, operator) -> None:
        cls.ensure_required_pair(department_id, permission_id, "department_id 和 permission_id 不能为空", 13014)
        await cls.ensure_can_operate_department(department_id=department_id, operator=operator)
        deleted_count = await GrantRepository.delete_department_permission(
            department_id=department_id,
            permission_id=permission_id,
        )
        cls.ensure_deleted_rows(deleted_count, "部门权限关系不存在", 13008)

    @classmethod
    async def grant_subsidiary_permission(cls, data: dict, operator, operator_id: int | None = None) -> dict:
        subsidiary_id = data.get("subsidiary_id")

        if not subsidiary_id:
            raise BusinessError("subsidiary_id 和 permission_id 不能为空", 13015)

        await cls.ensure_can_operate_subsidiary(subsidiary_id=subsidiary_id, operator=operator)
        create_data = cls.fill_grant_audit_fields(data, operator_id=operator_id)
        item = await GrantRepository.create_subsidiary_permission(create_data)
        return {"id": item.id}

    @classmethod
    async def revoke_subsidiary_permission(cls, subsidiary_id: int, permission_id: int, operator) -> None:
        cls.ensure_required_pair(subsidiary_id, permission_id, "subsidiary_id 和 permission_id 不能为空", 13015)
        await cls.ensure_can_operate_subsidiary(subsidiary_id=subsidiary_id, operator=operator)
        deleted_count = await GrantRepository.delete_subsidiary_permission(
            subsidiary_id=subsidiary_id,
            permission_id=permission_id,
        )
        cls.ensure_deleted_rows(deleted_count, "子公司权限关系不存在", 13010)

    @classmethod
    async def ensure_can_operate_user_role_pair(cls, user_id: int, role_id: int, operator) -> None:
        if not await GrantRepository.user_exists(user_id):
            raise BusinessError("用户不存在", 10103)

        role_info = await GrantRepository.get_role_scope_and_company_id(role_id)

        if not role_info:
            raise BusinessError("角色不存在", 10002)

        user_company_id = await GrantRepository.get_user_company_id(user_id)
        role_scope, role_company_id = role_info
        context = TenantService.from_user(operator)

        if TenantService.is_platform_admin(context):
            if role_scope == "PERSONAL" and user_company_id is not None:
                raise BusinessError("不能跨公司绑定用户角色", 14031)

            if role_scope == "ENTERPRISE" and user_company_id != role_company_id:
                raise BusinessError("不能跨公司绑定用户角色", 14031)

            return

        TenantService.ensure_enterprise_context(context)
        operator_company_id = context.company_id

        if user_company_id != operator_company_id:
            raise BusinessError("不能操作其他公司的用户", 14033)

        if role_company_id != operator_company_id:
            raise BusinessError("不能操作其他公司的角色", 14032)

        if user_company_id != role_company_id:
            raise BusinessError("不能跨公司绑定用户角色", 14031)

    @classmethod
    async def ensure_can_operate_role(cls, role_id: int, operator) -> None:
        role_info = await GrantRepository.get_role_scope_and_company_id(role_id)

        if not role_info:
            raise BusinessError("角色不存在", 10002)

        _, role_company_id = role_info
        context = TenantService.from_user(operator)

        if TenantService.is_platform_admin(context):
            return

        TenantService.ensure_enterprise_context(context)

        if role_company_id != context.company_id:
            raise BusinessError("不能操作其他公司的角色", 14032)

    @classmethod
    async def ensure_can_operate_user(cls, user_id: int, operator) -> None:
        if not await GrantRepository.user_exists(user_id):
            raise BusinessError("用户不存在", 10103)

        user_company_id = await GrantRepository.get_user_company_id(user_id)
        context = TenantService.from_user(operator)

        if TenantService.is_platform_admin(context):
            return

        TenantService.ensure_enterprise_context(context)

        if user_company_id != context.company_id:
            raise BusinessError("不能操作其他公司的用户", 14033)

    @classmethod
    async def ensure_can_operate_department(cls, department_id: int, operator) -> None:
        department_company_id = await GrantRepository.get_department_company_id(department_id)

        if department_company_id is None:
            raise BusinessError("数据不存在", 10002)

        context = TenantService.from_user(operator)

        if TenantService.is_platform_admin(context):
            return

        TenantService.ensure_enterprise_context(context)

        if department_company_id != context.company_id:
            raise BusinessError("不能操作其他公司的部门", 14034)

    @classmethod
    async def ensure_can_operate_subsidiary(cls, subsidiary_id: int, operator) -> None:
        subsidiary_company_id = await GrantRepository.get_subsidiary_company_id(subsidiary_id)

        if subsidiary_company_id is None:
            raise BusinessError("数据不存在", 10002)

        context = TenantService.from_user(operator)

        if TenantService.is_platform_admin(context):
            return

        TenantService.ensure_enterprise_context(context)

        if subsidiary_company_id != context.company_id:
            raise BusinessError("不能操作其他公司的子公司", 14035)

    @staticmethod
    def ensure_deleted_rows(deleted_count: int, message: str, code: int) -> None:
        if deleted_count <= 0:
            raise BusinessError(message, code)

    @staticmethod
    def ensure_required_pair(left_value, right_value, message: str, code: int) -> None:
        if not left_value or not right_value:
            raise BusinessError(message, code)


__all__ = ["GrantService"]

