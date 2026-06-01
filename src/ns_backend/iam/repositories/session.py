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
        """Create one user session."""
        return await IamUserSession.objects.acreate(**data)

    @staticmethod
    async def list_by_user_id(*, user_id: int) -> list[IamUserSession]:
        """List sessions owned by one user."""
        items: list[IamUserSession] = []
        queryset = IamUserSession.objects.filter(user_id=user_id).order_by("-id")

        async for item in queryset.aiterator():
            items.append(item)

        return items

    @staticmethod
    async def get_by_user_and_public_id(*, user_id: int, session_id: str) -> IamUserSession | None:
        """Get one session by user id and public session id."""
        return await IamUserSession.objects.filter(user_id=user_id, session_id=session_id).afirst()

    @staticmethod
    async def revoke_by_user_id(*, user_id: int, revoked_at) -> int:
        """Revoke all active sessions of one user."""
        return await IamUserSession.objects.filter(user_id=user_id, revoked_at__isnull=True).aupdate(revoked_at=revoked_at)

    @staticmethod
    async def revoke_by_id(*, session_pk: int, revoked_at) -> int:
        """Revoke one active session by primary key."""
        return await IamUserSession.objects.filter(id=session_pk, revoked_at__isnull=True).aupdate(revoked_at=revoked_at)

    @staticmethod
    async def update_activity(session: IamUserSession, data: dict[str, Any]) -> None:
        """Update session activity fields."""
        for field, value in data.items():
            setattr(session, field, value)

        await session.asave(update_fields=list(data.keys()))
