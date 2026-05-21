# -*- coding: utf-8 -*-
from __future__ import annotations

from django.utils import timezone

from iam.constants import IAM_DB_ALIAS
from iam.models import IamUserToken


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
