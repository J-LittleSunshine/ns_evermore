# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from asgiref.sync import sync_to_async
from django.db import transaction
from django.utils import timezone

from iam.constants import IAM_DB_ALIAS
from iam.models import IamUserToken
from ns_backend.exceptions import BusinessError


class TokenRepository:
    """Token 数据访问层。"""

    @staticmethod
    async def create_token(**kwargs) -> IamUserToken:
        return await IamUserToken.objects.using(IAM_DB_ALIAS).acreate(**kwargs)

    @staticmethod
    async def get_valid_access_token(user_id: int, access_jti: str) -> IamUserToken | None:
        return await IamUserToken.objects.using(IAM_DB_ALIAS).filter(
            user_id=user_id,
            access_jti=access_jti,
            revoked_at__isnull=True,
            expired_at__gt=timezone.now(),
        ).afirst()

    @staticmethod
    async def get_refresh_token(
        user_id: int,
        refresh_jti: str,
        refresh_token_hash: str,
    ) -> IamUserToken | None:
        return await IamUserToken.objects.using(IAM_DB_ALIAS).filter(
            user_id=user_id,
            refresh_jti=refresh_jti,
            refresh_token=refresh_token_hash,
        ).afirst()

    @staticmethod
    async def revoke_token(token_id: int) -> int:
        return await IamUserToken.objects.using(IAM_DB_ALIAS).filter(
            id=token_id,
            revoked_at__isnull=True,
        ).aupdate(revoked_at=timezone.now())

    @staticmethod
    async def revoke_user_tokens(user_id: int) -> int:
        return await IamUserToken.objects.using(IAM_DB_ALIAS).filter(
            user_id=user_id,
            revoked_at__isnull=True,
        ).aupdate(revoked_at=timezone.now())

    @classmethod
    async def rotate_refresh_token(
        cls,
        refresh_token_hash: str,
        new_token_data: dict[str, Any],
    ) -> IamUserToken:
        """原子化吊销旧 refresh token 并创建新 token。"""
        return await sync_to_async(
            cls._rotate_refresh_token_sync,
            thread_sensitive=True,
        )(
            refresh_token_hash=refresh_token_hash,
            new_token_data=new_token_data,
        )

    @staticmethod
    def _rotate_refresh_token_sync(
        refresh_token_hash: str,
        new_token_data: dict[str, Any],
    ) -> IamUserToken:
        if not refresh_token_hash:
            raise BusinessError("refresh_token 不能为空", 14000)

        with transaction.atomic(using=IAM_DB_ALIAS):
            old_token = (
                IamUserToken.objects.using(IAM_DB_ALIAS)
                .select_for_update()
                .filter(refresh_token=refresh_token_hash)
                .first()
            )

            if not old_token:
                raise BusinessError("refresh_token 不存在", 14001)

            if old_token.revoked_at:
                raise BusinessError("refresh_token 已失效", 14002)

            if old_token.expired_at <= timezone.now():
                raise BusinessError("refresh_token 已过期", 14003)

            old_token.revoked_at = timezone.now()
            old_token.save(update_fields=["revoked_at"])

            data = new_token_data.copy()
            data.setdefault("user_id", old_token.user_id)
            data.setdefault("session_id", old_token.session_id)
            data.setdefault("client_ip", old_token.client_ip)
            data.setdefault("user_agent", old_token.user_agent)
            data.setdefault("created_at", timezone.now())

            return IamUserToken.objects.using(IAM_DB_ALIAS).create(**data)
