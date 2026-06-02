# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.backend.common import BaseRepository
from ns_backend.iam.models import IamUserRole

if TYPE_CHECKING:
    pass


class AuthorizeRepository:
    """Repository for shared authorize-query helpers."""

    @staticmethod
    async def list_active_role_ids_for_user(*, user_id: int) -> list[int]:
        """List active role ids bound to one user."""
        db_alias: str = BaseRepository.resolve_db_alias(model_class=IamUserRole)
        queryset = IamUserRole.objects.using(db_alias).filter(
            user_id=user_id,
            role__status=1,
        ).values_list("role_id", flat=True)
        return [int(role_id) async for role_id in queryset]

