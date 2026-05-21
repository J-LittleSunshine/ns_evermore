# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from asgiref.sync import sync_to_async
from django.db import transaction
from django.utils import timezone

from iam.constants import IAM_DB_ALIAS
from iam.models import IamUserSession, IamUserToken


class SessionRepository:
    """会话数据访问层。"""

    @staticmethod
    async def create_session(**kwargs) -> IamUserSession:
        return await IamUserSession.objects.using(IAM_DB_ALIAS).acreate(**kwargs)

    @staticmethod
    async def get_by_id(session_pk: int) -> IamUserSession | None:
        return await IamUserSession.objects.using(IAM_DB_ALIAS).filter(
            id=session_pk,
        ).afirst()

    @staticmethod
    async def get_by_session_id(session_id: str) -> IamUserSession | None:
        return await IamUserSession.objects.using(IAM_DB_ALIAS).filter(
            session_id=session_id,
        ).afirst()

    @staticmethod
    async def get_available_by_id(session_id: int) -> IamUserSession | None:
        return await IamUserSession.objects.using(IAM_DB_ALIAS).filter(
            id=session_id,
            revoked_at__isnull=True,
            expired_at__gt=timezone.now(),
        ).afirst()

    @staticmethod
    async def revoke_by_id(session_id: int) -> int:
        return await IamUserSession.objects.using(IAM_DB_ALIAS).filter(
            id=session_id,
            revoked_at__isnull=True,
        ).aupdate(revoked_at=timezone.now())

    @staticmethod
    async def revoke_token_by_session_id(session_id: int) -> int:
        return await IamUserToken.objects.using(IAM_DB_ALIAS).filter(
            session_id=session_id,
            revoked_at__isnull=True,
        ).aupdate(revoked_at=timezone.now())

    @classmethod
    async def revoke_session_and_tokens_by_id(cls, session_id: int) -> int:
        """原子化撤销单个会话及其全部 Token。"""
        return await sync_to_async(
            cls._revoke_session_and_tokens_by_id_sync,
            thread_sensitive=True,
        )(session_id=session_id)

    @staticmethod
    def _revoke_session_and_tokens_by_id_sync(session_id: int) -> int:
        now = timezone.now()

        with transaction.atomic(using=IAM_DB_ALIAS):
            locked_sessions = (
                IamUserSession.objects.using(IAM_DB_ALIAS)
                .select_for_update()
                .filter(id=session_id)
            )
            session_ids = list(locked_sessions.values_list("id", flat=True))

            if not session_ids:
                return 0

            updated_count = IamUserSession.objects.using(IAM_DB_ALIAS).filter(
                id__in=session_ids,
                revoked_at__isnull=True,
            ).update(revoked_at=now)

            IamUserToken.objects.using(IAM_DB_ALIAS).filter(
                session_id__in=session_ids,
                revoked_at__isnull=True,
            ).update(revoked_at=now)

            return updated_count

    @classmethod
    async def revoke_user_sessions_and_tokens(cls, user_id: int) -> int:
        """原子化撤销用户全部会话及全部 Token。"""
        return await sync_to_async(
            cls._revoke_user_sessions_and_tokens_sync,
            thread_sensitive=True,
        )(user_id=user_id)

    @staticmethod
    def _revoke_user_sessions_and_tokens_sync(user_id: int) -> int:
        now = timezone.now()

        with transaction.atomic(using=IAM_DB_ALIAS):
            locked_sessions = (
                IamUserSession.objects.using(IAM_DB_ALIAS)
                .select_for_update()
                .filter(user_id=user_id)
            )
            session_ids = list(locked_sessions.values_list("id", flat=True))

            updated_count = IamUserSession.objects.using(IAM_DB_ALIAS).filter(
                id__in=session_ids,
                revoked_at__isnull=True,
            ).update(revoked_at=now)

            IamUserToken.objects.using(IAM_DB_ALIAS).filter(
                user_id=user_id,
                revoked_at__isnull=True,
            ).update(revoked_at=now)

            return updated_count

    @classmethod
    async def revoke_device_sessions_and_tokens(cls, device_id: int) -> int:
        """原子化撤销设备全部会话及其全部 Token。"""
        return await sync_to_async(
            cls._revoke_device_sessions_and_tokens_sync,
            thread_sensitive=True,
        )(device_id=device_id)

    @staticmethod
    def _revoke_device_sessions_and_tokens_sync(device_id: int) -> int:
        now = timezone.now()

        with transaction.atomic(using=IAM_DB_ALIAS):
            locked_sessions = (
                IamUserSession.objects.using(IAM_DB_ALIAS)
                .select_for_update()
                .filter(device_id=device_id)
            )
            session_ids = list(locked_sessions.values_list("id", flat=True))

            if not session_ids:
                return 0

            updated_count = IamUserSession.objects.using(IAM_DB_ALIAS).filter(
                id__in=session_ids,
                revoked_at__isnull=True,
            ).update(revoked_at=now)

            IamUserToken.objects.using(IAM_DB_ALIAS).filter(
                session_id__in=session_ids,
                revoked_at__isnull=True,
            ).update(revoked_at=now)

            return updated_count

    @staticmethod
    async def list_active_ids_by_user_id(user_id: int) -> list[int]:
        return [
            item.id
            async for item in IamUserSession.objects.using(IAM_DB_ALIAS).filter(
                user_id=user_id,
                revoked_at__isnull=True,
            ).only("id")
        ]

    @staticmethod
    async def list_active_ids_by_device_id(device_id: int) -> list[int]:
        return [
            item.id
            async for item in IamUserSession.objects.using(IAM_DB_ALIAS).filter(
                device_id=device_id,
                revoked_at__isnull=True,
            ).only("id")
        ]

    @staticmethod
    async def revoke_by_ids(session_ids: list[int]) -> int:
        if not session_ids:
            return 0

        return await IamUserSession.objects.using(IAM_DB_ALIAS).filter(
            id__in=session_ids,
            revoked_at__isnull=True,
        ).aupdate(revoked_at=timezone.now())

    @staticmethod
    async def revoke_tokens_by_session_ids(session_ids: list[int]) -> int:
        if not session_ids:
            return 0

        return await IamUserToken.objects.using(IAM_DB_ALIAS).filter(
            session_id__in=session_ids,
            revoked_at__isnull=True,
        ).aupdate(revoked_at=timezone.now())

    @staticmethod
    async def touch_session(session_id: str, update_data: dict[str, Any]) -> int:
        return await IamUserSession.objects.using(IAM_DB_ALIAS).filter(
            session_id=session_id,
            revoked_at__isnull=True,
            expired_at__gt=timezone.now(),
        ).aupdate(**update_data)

    @staticmethod
    async def touch_session_by_id(session_id: int, update_data: dict[str, Any]) -> int:
        return await IamUserSession.objects.using(IAM_DB_ALIAS).filter(
            id=session_id,
            revoked_at__isnull=True,
            expired_at__gt=timezone.now(),
        ).aupdate(**update_data)

    @staticmethod
    async def update_risk_level(session_id: int, risk_level: int) -> int:
        return await IamUserSession.objects.using(IAM_DB_ALIAS).filter(
            id=session_id,
        ).aupdate(risk_level=risk_level)

    @staticmethod
    async def list_by_user_id(user_id: int):
        return IamUserSession.objects.using(IAM_DB_ALIAS).filter(
            user_id=user_id,
        ).order_by("-last_active_at")
