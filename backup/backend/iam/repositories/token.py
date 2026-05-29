# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from asgiref.sync import sync_to_async
from django.db.models import Q
from django.db import transaction
from django.utils import timezone

from iam.constants import IAM_DB_ALIAS
from ns_common.error_codes import NsErrorCode
from iam.models import IamUser, IamUserSession, IamUserToken
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
    async def get_valid_access_token_with_session(user_id: int, access_jti: str) -> IamUserToken | None:
        now = timezone.now()
        return await IamUserToken.objects.using(IAM_DB_ALIAS).select_related("user").filter(
            user_id=user_id,
            access_jti=access_jti,
            revoked_at__isnull=True,
            expired_at__gt=now,
            user__is_active=1,
        ).filter(
            Q(session_id__isnull=True)
            | Q(
                session__revoked_at__isnull=True,
                session__expired_at__gt=now,
            )
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
            refresh_token_hash=refresh_token_hash,
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
        """兼容保留：禁止调用无 guard 的旧刷新旋转路径。"""
        raise BusinessError(
            "rotate_refresh_token is deprecated, use rotate_refresh_token_with_guard instead",
            NsErrorCode.TOKEN_ROTATION_DEPRECATED,
        )

    @staticmethod
    def _rotate_refresh_token_sync(
        refresh_token_hash: str,
        new_token_data: dict[str, Any],
    ) -> IamUserToken:
        raise BusinessError("_rotate_refresh_token_sync is deprecated", NsErrorCode.TOKEN_ROTATION_DEPRECATED)

    @classmethod
    async def rotate_refresh_token_with_guard(
        cls,
        *,
        user_id: int,
        refresh_jti: str,
        refresh_token_hash: str,
        new_token_data: dict[str, Any],
    ) -> tuple[str, IamUserToken | None, int | None, str | None, str | None]:
        """加锁旋转 refresh token，并在同一事务内检测重放。"""
        return await sync_to_async(
            cls._rotate_refresh_token_with_guard_sync,
            thread_sensitive=True,
        )(
            user_id=user_id,
            refresh_jti=refresh_jti,
            refresh_token_hash=refresh_token_hash,
            new_token_data=new_token_data,
        )

    @staticmethod
    def _rotate_refresh_token_with_guard_sync(
        *,
        user_id: int,
        refresh_jti: str,
        refresh_token_hash: str,
        new_token_data: dict[str, Any],
    ) -> tuple[str, IamUserToken | None, int | None, str | None, str | None]:
        if not refresh_token_hash:
            raise BusinessError("refresh_token cannot be empty", NsErrorCode.TOKEN_ROTATION_INVALID)

        with transaction.atomic(using=IAM_DB_ALIAS):
            old_token = (
                IamUserToken.objects.using(IAM_DB_ALIAS)
                .select_for_update()
                .filter(
                    user_id=user_id,
                    refresh_jti=refresh_jti,
                    refresh_token_hash=refresh_token_hash,
                )
                .first()
            )

            if not old_token:
                raise BusinessError("refresh_token does not exist", NsErrorCode.TOKEN_ROTATION_REVOKED)

            if old_token.expired_at <= timezone.now():
                raise BusinessError("refresh_token has expired", NsErrorCode.TOKEN_ROTATION_REPLAYED)

            if old_token.revoked_at:
                return "replayed", None, old_token.session_id, None, None

            session_public_id = None
            if old_token.session_id:
                session = (
                    IamUserSession.objects.using(IAM_DB_ALIAS)
                    .select_for_update()
                    .filter(id=old_token.session_id)
                    .first()
                )

                if (not session) or session.revoked_at or session.expired_at <= timezone.now():
                    old_token.revoked_at = timezone.now()
                    old_token.save(update_fields=["revoked_at"])
                    return "session_unavailable", None, old_token.session_id, None, None

                session_public_id = session.session_id


            user = (
                IamUser.objects.using(IAM_DB_ALIAS)
                .select_for_update()
                .filter(id=old_token.user_id)
                .first()
            )

            if not user or not user.is_active:
                return "user_inactive", None, old_token.session_id, session_public_id, None

            old_token.revoked_at = timezone.now()
            old_token.save(update_fields=["revoked_at"])

            data = new_token_data.copy()
            data.setdefault("user_id", old_token.user_id)
            data.setdefault("session_id", old_token.session_id)
            data.setdefault("client_ip", old_token.client_ip)
            data.setdefault("user_agent", old_token.user_agent)
            data.setdefault("created_at", timezone.now())

            new_token = IamUserToken.objects.using(IAM_DB_ALIAS).create(**data)
            return "rotated", new_token, old_token.session_id, session_public_id, user.user_type

