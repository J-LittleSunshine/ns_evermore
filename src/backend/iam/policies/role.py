# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.models import IamRole
from iam.policies.tenant import TenantPolicy
from iam.repositories.role import RoleRepository
from ns_backend.exceptions import BusinessError
from ns_backend.policies import BasePolicy


class RolePolicy(BasePolicy):
    """IAM 角色边界策略。"""

    @classmethod
    async def build_create_payload(
        cls,
        *,
        context,
        data: dict,
    ) -> dict:
        role_scope = data.get("role_scope")
        role_code = data.get("role_code")
        final_data = data.copy()

        if role_scope == IamRole.SCOPE_PERSONAL:
            if not TenantPolicy.is_platform_admin(context):
                raise BusinessError("只有平台管理员可以创建个人体系角色", 14014)

            if final_data.get("company_id") is not None:
                raise BusinessError("个人体系角色不能绑定公司", 14011)

            if await RoleRepository.exists_personal_role_code(role_code=role_code):
                raise BusinessError("角色编码已存在", 14012)

            final_data["company_id"] = None
            return final_data

        if role_scope == IamRole.SCOPE_ENTERPRISE:
            if TenantPolicy.is_platform_admin(context):
                company_id = final_data.get("company_id")

                if not company_id:
                    raise BusinessError("企业角色必须绑定公司", 14013)
            else:
                TenantPolicy.ensure_enterprise_context(context)
                company_id = context.company_id

            if await RoleRepository.exists_enterprise_role_code(
                company_id=company_id,
                role_code=role_code,
            ):
                raise BusinessError("角色编码已存在", 14012)

            final_data["company_id"] = company_id
            return final_data

        raise BusinessError("role_scope 取值非法", 12004)

    @classmethod
    def ensure_can_update_fields(cls, data: dict) -> None:
        if "company_id" in data:
            cls.deny("不允许更新字段：company_id", 12005)

        if "role_scope" in data:
            cls.deny("不允许更新字段：role_scope", 12005)

    @classmethod
    def ensure_can_manage_role_company(
        cls,
        context,
        role_company_id: int | None,
    ) -> None:
        if TenantPolicy.is_platform_admin(context):
            return

        TenantPolicy.ensure_enterprise_context(context)

        if role_company_id != context.company_id:
            cls.deny("数据不存在", 10002)


__all__ = ["RolePolicy"]

