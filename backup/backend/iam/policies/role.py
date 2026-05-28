# -*- coding: utf-8 -*-
from __future__ import annotations

from ns_common.error_codes import NsErrorCode
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
                raise BusinessError("Only platform administrators can create PERSONAL roles", NsErrorCode.ROLE_PERSONAL_PLATFORM_ADMIN_ONLY)

            if final_data.get("company_id") is not None:
                raise BusinessError("PERSONAL roles cannot be bound to a company", NsErrorCode.ROLE_PERSONAL_COMPANY_FORBIDDEN)

            if await RoleRepository.exists_personal_role_code(role_code=role_code):
                raise BusinessError("Role code already exists", NsErrorCode.ROLE_CODE_ALREADY_EXISTS)

            final_data["company_id"] = None
            return final_data

        if role_scope == IamRole.SCOPE_ENTERPRISE:
            if TenantPolicy.is_platform_admin(context):
                company_id = final_data.get("company_id")

                if not company_id:
                    raise BusinessError("ENTERPRISE roles must be bound to a company", NsErrorCode.ROLE_ENTERPRISE_COMPANY_REQUIRED)
            else:
                TenantPolicy.ensure_enterprise_context(context)
                company_id = context.company_id

            if await RoleRepository.exists_enterprise_role_code(
                company_id=company_id,
                role_code=role_code,
            ):
                raise BusinessError("Role code already exists", NsErrorCode.ROLE_CODE_ALREADY_EXISTS)

            final_data["company_id"] = company_id
            return final_data

        raise BusinessError("Invalid role_scope value", NsErrorCode.INVALID_VALUE)

    @classmethod
    def ensure_can_update_fields(cls, data: dict) -> None:
        if "company_id" in data:
            cls.deny("Updating field is not allowed: company_id", NsErrorCode.UPDATE_FIELD_NOT_ALLOWED)

        if "role_scope" in data:
            cls.deny("Updating field is not allowed: role_scope", NsErrorCode.UPDATE_FIELD_NOT_ALLOWED)

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
            cls.deny("Data not found", NsErrorCode.DATA_NOT_FOUND)


__all__ = ["RolePolicy"]

