# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.policies.tenant import TenantPolicy
from iam.repositories.organization import OrganizationRepository
from ns_backend.policies import BasePolicy


class OrganizationPolicy(BasePolicy):
    """IAM 组织边界策略。"""

    @classmethod
    def ensure_can_create_company(cls, context) -> None:
        TenantPolicy.ensure_platform_admin(context, "只有平台管理员可以创建公司", 14003)

    @classmethod
    def ensure_can_delete_company(cls, context) -> None:
        TenantPolicy.ensure_platform_admin(context, "只有平台管理员可以删除公司", 14004)

    @classmethod
    async def ensure_subsidiary_belongs_to_company(
        cls,
        subsidiary_id: int | None,
        company_id: int,
    ) -> None:
        if not subsidiary_id:
            return

        subsidiary_company_id = await OrganizationRepository.get_subsidiary_company_id(subsidiary_id)

        if subsidiary_company_id != company_id:
            cls.deny("子公司不属于当前公司", 14041)

    @classmethod
    async def ensure_department_belongs_to_company(
        cls,
        department_id: int | None,
        company_id: int,
    ) -> None:
        if not department_id:
            return

        department_company_id = await OrganizationRepository.get_department_company_id(department_id)

        if department_company_id != company_id:
            cls.deny("部门不属于当前公司", 14042)

    @classmethod
    async def ensure_parent_department_belongs_to_company(
        cls,
        parent_id: int | None,
        company_id: int,
    ) -> None:
        if not parent_id:
            return

        parent_company_id = await OrganizationRepository.get_department_company_id(parent_id)

        if parent_company_id != company_id:
            cls.deny("上级部门不属于当前公司", 14043)


__all__ = ["OrganizationPolicy"]

