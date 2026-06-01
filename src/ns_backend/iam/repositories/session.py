# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ns_backend.iam.models import IamUserSession

if TYPE_CHECKING:
    pass


class UserSessionRepository:
    """Repository for IAM user sessions."""

    @staticmethod
    async def create_session(data: dict[str, Any]) -> IamUserSession:
        return await IamUserSession.objects.acreate(**data)

    @staticmethod
    async def revoke_by_user_id(*, user_id: int, revoked_at) -> int:
        return await IamUserSession.objects.filter(user_id=user_id, revoked_at__isnull=True).aupdate(revoked_at=revoked_at)

    @staticmethod
    async def revoke_by_id(*, session_pk: int, revoked_at) -> int:
        return await IamUserSession.objects.filter(id=session_pk, revoked_at__isnull=True).aupdate(revoked_at=revoked_at)

    @staticmethod
    async def update_activity(session: IamUserSession, data: dict[str, Any]) -> None:
        for field, value in data.items():
            setattr(session, field, value)
        await session.asave(update_fields=list(data.keys()))
