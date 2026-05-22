# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.error_codes import IamErrorCode
from iam.policies.organization import OrganizationPolicy
from iam.policies.tenant import TenantPolicy
from iam.repositories.crud import CrudRepository
from iam.services.tenant import TenantService
from ns_backend.exceptions import BusinessError


class DepartmentService:
    """部门服务。"""

    @classmethod
    async def create_department(
        cls,
        *,
        model_class,
        data: dict,
        operator,
        operator_id: int | None,
    ) -> dict:
        context = TenantService.from_user(operator)
        create_data = data.copy()

        if TenantPolicy.is_platform_admin(context):
            company_id = create_data.get("company_id")

            if not company_id:
                raise BusinessError("company_id cannot be empty", IamErrorCode.ID_EMPTY)
        else:
            TenantPolicy.ensure_enterprise_context(context)
            company_id = context.company_id
            create_data["company_id"] = company_id

        await OrganizationPolicy.ensure_subsidiary_belongs_to_company(
            subsidiary_id=create_data.get("subsidiary_id"),
            company_id=company_id,
        )
        await OrganizationPolicy.ensure_parent_department_belongs_to_company(
            parent_id=create_data.get("parent_id"),
            company_id=company_id,
        )

        return await CrudRepository.create_item_with_audit(
            model_class=model_class,
            data=create_data,
            operator_id=operator_id,
            tenant_create_values={"company_id": company_id},
        )


__all__ = ["DepartmentService"]

