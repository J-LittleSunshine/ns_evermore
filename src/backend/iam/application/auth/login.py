# -*- coding: utf-8 -*-
from __future__ import annotations

from django.contrib.auth.hashers import check_password
from django.utils import timezone

from iam.domain.services.device import DeviceDomainService
from iam.domain.services.login_failure import LoginFailureDomainService
from iam.domain.services.session import SessionDomainService
from iam.repositories.token import TokenRepository
from iam.repositories.user import UserRepository
from iam.services.jwt import JwtService
from ns_backend.exceptions import BusinessError


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
        username = username.strip()

        await LoginFailureDomainService.ensure_not_locked(username=username)

        user = await UserRepository.get_active_by_username(username)

        if not user:
            await LoginFailureDomainService.record_failed(
                username=username,
                user=None,
                client_ip=client_ip,
                user_agent=user_agent,
            )
            raise BusinessError("Username or password is incorrect.")

        if not check_password(password, user.password):
            await LoginFailureDomainService.record_failed(
                username=username,
                user=user,
                client_ip=client_ip,
                user_agent=user_agent,
            )
            raise BusinessError("Username or password is incorrect.")

        await LoginFailureDomainService.clear(username=username)

        fingerprint_raw = fingerprint_raw or cls.build_fallback_fingerprint(
            username=username,
            client_ip=client_ip,
            user_agent=user_agent,
        )

        device = await DeviceDomainService.get_or_create_device(
            user_id=user.id,
            device_name=device_name or "Unknown Device",
            device_type=device_type or "WEB",
            fingerprint_raw=fingerprint_raw,
            client_ip=client_ip,
            os_name=os_name,
            browser_name=browser_name,
        )

        session = await SessionDomainService.create_session(
            user_id=user.id,
            device_id=device.id,
            login_ip=client_ip,
            user_agent=user_agent,
        )

        access_token, access_jti = JwtService.create_access_token(
            user_id=user.id,
            user_type=user.user_type,
        )

        now = timezone.now()

        refresh_token, refresh_token_hash, refresh_jti, refresh_expired_at = (
            JwtService.create_refresh_token(user_id=user.id)
        )

        await TokenRepository.create_token(
            user_id=user.id,
            session_id=session.id,
            refresh_token=refresh_token_hash,
            access_jti=access_jti,
            refresh_jti=refresh_jti,
            client_ip=client_ip,
            user_agent=user_agent,
            expired_at=refresh_expired_at,
            created_at=now,
        )

        await UserRepository.mark_login_success(user)

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
