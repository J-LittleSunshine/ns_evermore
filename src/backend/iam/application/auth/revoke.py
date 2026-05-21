# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.domain.services.session import SessionDomainService
from iam.infrastructure.jwt import JwtService
from iam.repositories.token import TokenRepository


class RevokeApplicationService:
    """令牌吊销应用服务。"""

    @classmethod
    async def revoke_access_token(cls, access_token: str) -> bool:
        """吊销 access token 对应的 session 或 token。"""
        payload = JwtService.decode_access_token(access_token)

        if not payload:
            return False

        user_id = payload.get("uid")
        access_jti = payload.get("jti")

        if not user_id or not access_jti:
            return False

        token_record = await TokenRepository.get_valid_access_token(
            user_id=user_id,
            access_jti=access_jti,
        )

        if not token_record:
            return False

        if token_record.session_id:
            return await SessionDomainService.revoke_session_by_pk(token_record.session_id)

        updated_count = await TokenRepository.revoke_token(token_record.id)

        return updated_count > 0

    @classmethod
    async def revoke_user_tokens(cls, user_id: int) -> None:
        """吊销用户全部 session 和 token。"""
        await SessionDomainService.revoke_user_sessions(user_id=user_id)
        await TokenRepository.revoke_user_tokens(user_id=user_id)
