# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.repositories.token import TokenRepository
from iam.services.jwt import JwtService
from iam.services.session import SessionService


class LogoutApplicationService:
    """登出应用服务。"""

    @classmethod
    async def execute(cls, refresh_token: str) -> bool:
        payload = JwtService.decode_refresh_token(refresh_token)

        if not payload:
            return False

        refresh_jti = payload.get("jti")
        user_id = payload.get("uid")

        if not refresh_jti or not user_id:
            return False

        refresh_token_hash = JwtService.hash_token(refresh_token)

        token_record = await TokenRepository.get_refresh_token(
            user_id=user_id,
            refresh_jti=refresh_jti,
            refresh_token_hash=refresh_token_hash,
        )

        if not token_record or token_record.revoked_at:
            return False

        if token_record.session_id:
            return await SessionService.revoke_session(token_record.session.session_id)

        updated_count = await TokenRepository.revoke_token(token_record.id)

        return updated_count > 0
