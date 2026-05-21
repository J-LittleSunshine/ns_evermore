# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.repositories.base import CrudRepository
from iam.repositories.organization import OrganizationRepository
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

        if TenantService.is_platform_admin(context):
            company_id = create_data.get("company_id")

            if not company_id:
                raise BusinessError("company_id 不能为空", 10001)
        elif TenantService.is_enterprise_user(context):
            TenantService.ensure_enterprise_context(context)
            company_id = context.company_id
            create_data["company_id"] = company_id
        else:
            raise BusinessError("个人用户不能访问企业组织资源", 14002)

        subsidiary_id = create_data.get("subsidiary_id")

        if subsidiary_id:
            subsidiary_company_id = await OrganizationRepository.get_subsidiary_company_id(subsidiary_id)

            if subsidiary_company_id != company_id:
                raise BusinessError("子公司不属于当前公司", 14041)

        parent_id = create_data.get("parent_id")

        if parent_id:
            parent_company_id = await OrganizationRepository.get_department_company_id(parent_id)

            if parent_company_id != company_id:
                raise BusinessError("上级部门不属于当前公司", 14043)

        return await CrudRepository.create_item_with_audit(
            model_class=model_class,
            data=create_data,
            operator_id=operator_id,
            tenant_create_values={"company_id": company_id},
        )


__all__ = ["DepartmentService"]

