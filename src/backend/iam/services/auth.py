# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.application.auth.login import LoginApplicationService
from iam.application.auth.logout import LogoutApplicationService
from iam.application.auth.refresh import RefreshApplicationService
from iam.application.auth.revoke import RevokeApplicationService
from iam.application.auth.verify import VerifyApplicationService
from iam.domain.services.login_failure import LoginFailureDomainService


class AuthService:
    """认证服务兼容门面。

    新代码应优先调用 iam.application.auth 下的应用服务。
    该类仅用于兼容现有 View / Middleware 的方法入口。
    """

    @classmethod
    async def login(
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
        return await LoginApplicationService.execute(
            username=username,
            password=password,
            client_ip=client_ip,
            user_agent=user_agent,
            device_name=device_name,
            device_type=device_type,
            fingerprint_raw=fingerprint_raw,
            os_name=os_name,
            browser_name=browser_name,
        )

    @classmethod
    async def refresh_access_token(cls, refresh_token: str) -> dict:
        return await RefreshApplicationService.execute(refresh_token=refresh_token)

    @classmethod
    async def logout(cls, refresh_token: str) -> bool:
        return await LogoutApplicationService.execute(refresh_token=refresh_token)

    @classmethod
    async def get_user_by_access_token(cls, access_token: str):
        return await VerifyApplicationService.get_user_by_access_token(access_token)

    @classmethod
    async def revoke_access_token(cls, access_token: str) -> bool:
        return await RevokeApplicationService.revoke_access_token(access_token)

    @classmethod
    async def revoke_all_user_tokens(cls, user_id: int) -> None:
        await RevokeApplicationService.revoke_user_tokens(user_id=user_id)

    @classmethod
    async def check_login_locked(cls, username: str) -> None:
        await LoginFailureDomainService.ensure_not_locked(username=username)

    @classmethod
    async def record_login_failed(
        cls,
        username: str,
        user,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        await LoginFailureDomainService.record_failed(
            username=username,
            user=user,
            client_ip=client_ip,
            user_agent=user_agent,
        )

    @classmethod
    async def clear_login_failed(cls, username: str) -> None:
        await LoginFailureDomainService.clear(username=username)

    @staticmethod
    def get_bearer_token_from_request(request) -> str | None:
        authorization = request.headers.get("Authorization", "")

        if not authorization.startswith("Bearer "):
            return None

        token = authorization.removeprefix("Bearer ").strip()
        return token or None

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
