# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.constants import IAM_DB_ALIAS
from iam.models import IamDepartment, IamSubsidiary


class OrganizationRepository:
    """组织归属数据访问层。"""

    @staticmethod
    async def get_subsidiary_company_id(subsidiary_id: int) -> int | None:
        item = await IamSubsidiary.objects.using(IAM_DB_ALIAS).filter(
            id=subsidiary_id,
        ).values("company_id").afirst()
        return None if not item else item.get("company_id")

    @staticmethod
    async def get_department_company_id(department_id: int) -> int | None:
        item = await IamDepartment.objects.using(IAM_DB_ALIAS).filter(
            id=department_id,
        ).values("company_id").afirst()
        return None if not item else item.get("company_id")


__all__ = ["OrganizationRepository"]

