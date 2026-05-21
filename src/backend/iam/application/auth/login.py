# -*- coding: utf-8 -*-
from __future__ import annotations

import uuid
from datetime import timedelta

from django.contrib.auth.hashers import check_password
from django.utils import timezone

from iam.domain.services.login_failure import LoginFailureDomainService
from iam.domain.services.session import SessionDomainService
from iam.infrastructure.jwt import JwtService
from iam.repositories.session import SessionRepository
from iam.repositories.user import UserRepository
from ns_backend.exceptions import BusinessError
from ns_backend.logger import get_logger

_logger = get_logger("ns_backend")


class LoginApplicationService:
    """登录应用服务。"""

    @classmethod
    async def execute(
        cls,
        username: str,
        password: str,
        client_ip: str | None = None,
        user_agent: str | None = None,
        device_name: str | None = None,
        device_type: str | None = None,
        fingerprint_raw: str | None = None,
        os_name: str | None = None,
        browser_name: str | None = None,
    ) -> dict:
        if not isinstance(username, str):
            raise BusinessError("username 不能为空", 11001)

        if not isinstance(password, str):
            raise BusinessError("password 不能为空", 11002)

        username = username.strip()

        if not username:
            raise BusinessError("username 不能为空", 11001)

        if not password:
            raise BusinessError("password 不能为空", 11002)

        await LoginFailureDomainService.ensure_not_locked(username=username)

        user = await UserRepository.get_active_by_username(username)

        if not user:
            await LoginFailureDomainService.record_failed(
                username=username,
                user=None,
                client_ip=client_ip,
                user_agent=user_agent,
            )
            raise BusinessError("Username or password is incorrect.", 11003)

        if not check_password(password, user.password):
            await LoginFailureDomainService.record_failed(
                username=username,
                user=user,
                client_ip=client_ip,
                user_agent=user_agent,
            )
            raise BusinessError("Username or password is incorrect.", 11003)

        fingerprint_raw = fingerprint_raw or cls.build_fallback_fingerprint(
            username=username,
            client_ip=client_ip,
            user_agent=user_agent,
        )

        access_token, access_jti = JwtService.create_access_token(
            user_id=user.id,
            user_type=user.user_type,
        )

        refresh_token, refresh_token_hash, refresh_jti, refresh_expired_at = (
            JwtService.create_refresh_token(user_id=user.id)
        )

        session_id = uuid.uuid4().hex
        session_now = timezone.now()
        session, device = await SessionRepository.create_login_bundle_with_device(
            user_id=user.id,
            device_name=device_name or "Unknown Device",
            device_type=device_type or "WEB",
            fingerprint_raw=fingerprint_raw,
            user_agent=user_agent,
            client_ip=client_ip,
            os_name=os_name,
            browser_name=browser_name,
            session_id=session_id,
            risk_level=0,
            last_active_at=session_now,
            session_expired_at=session_now + timedelta(minutes=SessionDomainService.DEFAULT_EXPIRED_MINUTES),
            refresh_token_hash=refresh_token_hash,
            access_jti=access_jti,
            refresh_jti=refresh_jti,
            token_expired_at=refresh_expired_at,
        )

        try:
            await LoginFailureDomainService.clear(username=username)
        except Exception as exc:  # noqa
            try:
                await LoginFailureDomainService.clear(username=username)
            except Exception as retry_exc:  # noqa
                # Successful login should not be rolled back by cleanup failure.
                _logger.warning(
                    "failed to clear login failure record username=%s err=%s retry_err=%s",
                    username,
                    exc,
                    retry_exc,
                )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": JwtService.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "session_id": session.session_id,
            "device_id": device.device_id,
        }

    @staticmethod
    def build_fallback_fingerprint(
        username: str,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> str:
        return "|".join(
            [
                username,
                client_ip or "",
                user_agent or "",
            ]
        )
