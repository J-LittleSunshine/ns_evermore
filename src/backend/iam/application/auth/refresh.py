# -*- coding: utf-8 -*-
from __future__ import annotations

from django.utils import timezone

from iam.domain.services.session import SessionDomainService
from iam.repositories.token import TokenRepository
from iam.repositories.user import UserRepository
from iam.services.jwt import JwtService
from ns_backend.exceptions import BusinessError


class RefreshApplicationService:
    """刷新令牌应用服务。"""

    @classmethod
    async def execute(cls, refresh_token: str) -> dict:
        payload = JwtService.decode_refresh_token(refresh_token)

        if not payload:
            raise BusinessError("Refresh Token 无效或已过期", 11005)

        refresh_jti = payload.get("jti")
        user_id = payload.get("uid")

        if not refresh_jti or not user_id:
            raise BusinessError("Refresh Token 无效", 11005)

        refresh_token_hash = JwtService.hash_token(refresh_token)

        token_record = await TokenRepository.get_refresh_token(
            user_id=user_id,
            refresh_jti=refresh_jti,
            refresh_token_hash=refresh_token_hash,
        )

        if not token_record:
            raise BusinessError("Refresh Token 已失效", 11005)

        if token_record.revoked_at:
            if token_record.session_id:
                await SessionDomainService.revoke_session(token_record.session.session_id)
            else:
                await TokenRepository.revoke_user_tokens(user_id=user_id)
            raise BusinessError("检测到 Refresh Token 重放攻击，当前会话已强制下线", 11013)

        user = await UserRepository.get_active_by_id(user_id)

        if not user:
            raise BusinessError("用户不存在或已禁用", 11010)

        session_public_id = None

        if token_record.session_id:
            session = await SessionDomainService.ensure_available(token_record.session.session_id)
            session_public_id = session.session_id

        access_token, access_jti = JwtService.create_access_token(
            user_id=user.id,
            user_type=user.user_type,
        )

        new_refresh_token, new_refresh_token_hash, new_refresh_jti, new_refresh_expired_at = (
            JwtService.create_refresh_token(user_id=user.id)
        )

        await TokenRepository.rotate_refresh_token(
            refresh_token_hash=refresh_token_hash,
            new_token_data={
                "refresh_token": new_refresh_token_hash,
                "access_jti": access_jti,
                "refresh_jti": new_refresh_jti,
                "expired_at": new_refresh_expired_at,
                "created_at": timezone.now(),
            },
        )

        if session_public_id:
            await SessionDomainService.touch_activity(
                session_id=session_public_id,
                client_ip=token_record.client_ip,
                user_agent=token_record.user_agent,
            )

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "Bearer",
            "expires_in": JwtService.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "session_id": session_public_id,
        }
