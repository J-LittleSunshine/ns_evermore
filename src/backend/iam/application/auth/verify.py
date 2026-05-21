# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.infrastructure.jwt import JwtService
from iam.repositories.token import TokenRepository


class VerifyApplicationService:
    """访问令牌校验应用服务。"""

    @classmethod
    async def get_user_by_access_token(cls, access_token: str):
        payload = JwtService.decode_access_token(access_token)

        if not payload:
            return None

        user_id = payload.get("uid")
        access_jti = payload.get("jti")

        if not user_id or not access_jti:
            return None

        token_record = await TokenRepository.get_valid_access_token_with_session(
            user_id=user_id,
            access_jti=access_jti,
        )

        if not token_record:
            return None

        return token_record.user
