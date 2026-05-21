# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.infrastructure.jwt import JwtService
from iam.repositories.session import SessionRepository
from iam.repositories.token import TokenRepository
from iam.repositories.user import UserRepository


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

        token_record = await TokenRepository.get_valid_access_token(
            user_id=user_id,
            access_jti=access_jti,
        )

        if not token_record:
            return None

        if token_record.session_id:
            session = await SessionRepository.get_available_by_id(token_record.session_id)

            if not session:
                return None

        return await UserRepository.get_active_by_id(user_id)
