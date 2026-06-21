# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.backend.common import BaseRepository
from ns_backend.iam.models import IamDepartment, IamSubsidiary

if TYPE_CHECKING:
    pass


class OrganizationRepository:
    """Repository for IAM organization ownership lookup."""

    @staticmethod
    async def get_subsidiary_company_id(subsidiary_id: int) -> int | None:
        """Load subsidiary company id."""
        db_alias = BaseRepository.resolve_db_alias(model_class=IamSubsidiary)
        item = await IamSubsidiary.objects.using(db_alias).filter(id=subsidiary_id).values("company_id").afirst()
        return None if not item else item.get("company_id")

    @staticmethod
    async def get_department_company_id(department_id: int) -> int | None:
        """Load department company id."""
        db_alias = BaseRepository.resolve_db_alias(model_class=IamDepartment)
        item = await IamDepartment.objects.using(db_alias).filter(id=department_id).values("company_id").afirst()
        return None if not item else item.get("company_id")
