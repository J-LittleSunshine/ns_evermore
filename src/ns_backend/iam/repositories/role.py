# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.backend.common import BaseRepository
from ns_backend.iam.models import IamRole

if TYPE_CHECKING:
    pass


class RoleRepository:
    """Repository for IAM role boundary lookup."""

    @staticmethod
    async def exists_personal_role_code(*, role_code: str) -> bool:
        """Check whether a PERSONAL role code already exists globally."""
        db_alias = BaseRepository.resolve_db_alias(model_class=IamRole)
        return await IamRole.objects.using(db_alias).filter(role_scope=IamRole.SCOPE_PERSONAL, role_code=role_code).aexists()

    @staticmethod
    async def exists_enterprise_role_code(*, company_id: int, role_code: str) -> bool:
        """Check whether an ENTERPRISE role code already exists within one company."""
        db_alias = BaseRepository.resolve_db_alias(model_class=IamRole)
        return await IamRole.objects.using(db_alias).filter(role_scope=IamRole.SCOPE_ENTERPRISE, company_id=company_id, role_code=role_code).aexists()
