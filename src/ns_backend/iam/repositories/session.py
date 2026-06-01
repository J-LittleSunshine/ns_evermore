# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from asgiref.sync import sync_to_async
from django.db import transaction

from ns_backend.iam.models import IamUserSession, IamUserToken

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
        """List sessions owned by one user with device metadata."""
        items: list[IamUserSession] = []
        queryset = IamUserSession.objects.select_related("device").filter(user_id=user_id).order_by("-last_active_at", "-id")

        async for item in queryset.aiterator():
            items.append(item)

        return items

    @staticmethod
    async def list_valid_token_session_ids(*, user_id: int, now) -> set[int]:
        """List session primary keys that still have valid tokens."""
        queryset = IamUserToken.objects.filter(
            user_id=user_id,
            revoked_at__isnull=True,
            expired_at__gt=now,
            session_id__isnull=False,
        ).values_list("session_id", flat=True)
        return {item async for item in queryset}

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

    @classmethod
    async def revoke_session_and_tokens_by_id(cls, *, session_pk: int, revoked_at) -> int:
        """Revoke one session and all tokens under this session atomically."""
        return await sync_to_async(cls._revoke_session_and_tokens_by_id_sync, thread_sensitive=True)(session_pk=session_pk, revoked_at=revoked_at)

    @staticmethod
    def _revoke_session_and_tokens_by_id_sync(*, session_pk: int, revoked_at) -> int:
        """Synchronous transaction for session-token revocation."""
        with transaction.atomic():
            session_ids = list(IamUserSession.objects.select_for_update().filter(id=session_pk).values_list("id", flat=True))
            if not session_ids:
                return 0

            updated_count = IamUserSession.objects.filter(id__in=session_ids, revoked_at__isnull=True).update(revoked_at=revoked_at)
            IamUserToken.objects.filter(session_id__in=session_ids, revoked_at__isnull=True).update(revoked_at=revoked_at)
            return updated_count

    @staticmethod
    async def update_activity(session: IamUserSession, data: dict[str, Any]) -> None:
        """Update session activity fields."""
        for field, value in data.items():
            setattr(session, field, value)

        await session.asave(update_fields=list(data.keys()))
