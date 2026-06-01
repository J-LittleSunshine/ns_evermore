# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils import timezone

from ns_backend.backend.utils.jwt import JwtService
from ns_backend.iam.repositories import AuthUserRepository, UserTokenRepository

if TYPE_CHECKING:
    pass


class VerifyService:
    """Access token verification service."""

    @classmethod
    async def get_user_by_access_token(cls, access_token: str):
        payload = JwtService.decode_access_token(access_token)
        if not payload:
            return None

        user_id = payload.get("uid")
        access_jti = payload.get("jti")

        if not isinstance(user_id, int) or not isinstance(access_jti, str):
            return None

        now = timezone.now()
        token_record = await UserTokenRepository.get_active_access_token_record(user_id=user_id, access_jti=access_jti, now=now)
        if token_record is None:
            return None

        session = getattr(token_record, "session", None)
        if session is not None:
            if session.revoked_at is not None:
                return None
            if session.expired_at <= now:
                return None

        user = getattr(token_record, "user", None)
        if user is None:
            user = await AuthUserRepository.get_user_by_id(user_id)

        if user is None or not bool(getattr(user, "is_active", False)):
            return None

        return user
