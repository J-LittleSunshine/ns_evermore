# -*- coding: utf-8 -*-
from __future__ import annotations

from django.utils import timezone

from iam.domain.services.session import SessionDomainService
from iam.infrastructure.jwt import JwtService
from iam.repositories.token import TokenRepository
from ns_backend.exceptions import BusinessError
from ns_backend.logger import get_logger

_logger = get_logger("ns_backend")


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

        access_jti = JwtService.create_access_jti()

        new_refresh_token, new_refresh_token_hash, new_refresh_jti, new_refresh_expired_at = (
            JwtService.create_refresh_token(user_id=user_id)
        )

        try:
            rotate_status, rotated_token, session_pk, session_public_id, locked_user_type = await TokenRepository.rotate_refresh_token_with_guard(
                user_id=user_id,
                refresh_jti=refresh_jti,
                refresh_token_hash=refresh_token_hash,
                new_token_data={
                    "refresh_token": new_refresh_token_hash,
                    "access_jti": access_jti,
                    "refresh_jti": new_refresh_jti,
                    "expired_at": new_refresh_expired_at,
                    "created_at": timezone.now(),
                },
            )
        except BusinessError as exc:
            if exc.code in (14000, 14001, 14003):
                _logger.warning(
                    "refresh rotation rejected user_id=%s refresh_jti=%s internal_code=%s",
                    user_id,
                    refresh_jti,
                    exc.code,
                )
                raise BusinessError("Refresh Token 已失效", 11005)
            raise

        if rotate_status == "replayed":
            if session_pk:
                await SessionDomainService.revoke_session_by_pk(session_pk)
            else:
                await TokenRepository.revoke_user_tokens(user_id=user_id)
            raise BusinessError("检测到 Refresh Token 重放攻击，当前会话已强制下线", 11013)

        if rotate_status == "user_inactive":
            if session_pk:
                await SessionDomainService.revoke_session_by_pk(session_pk)
            else:
                await TokenRepository.revoke_user_tokens(user_id=user_id)
            raise BusinessError("用户不存在或已禁用", 11010)

        if rotate_status == "session_unavailable":
            raise BusinessError("Refresh Token 已失效", 11005)

        if rotate_status != "rotated":
            raise BusinessError("Refresh Token 已失效", 11005)

        if not locked_user_type:
            raise BusinessError("用户不存在或已禁用", 11010)

        access_token, _ = JwtService.create_access_token(
            user_id=user_id,
            user_type=locked_user_type,
            access_jti=access_jti,
        )

        if session_pk:
            await SessionDomainService.touch_activity_by_pk(
                session_pk=session_pk,
                client_ip=rotated_token.client_ip if rotated_token else None,
                user_agent=rotated_token.user_agent if rotated_token else None,
            )

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "Bearer",
            "expires_in": JwtService.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "session_id": session_public_id,
        }
