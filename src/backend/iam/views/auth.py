# -*- coding: utf-8 -*-
from __future__ import annotations

import ipaddress
from typing import TYPE_CHECKING

from django.conf import settings

from iam.application.auth.login import LoginApplicationService
from iam.application.auth.logout import LogoutApplicationService
from iam.application.auth.refresh import RefreshApplicationService
from iam.application.auth.revoke import RevokeApplicationService
from iam.infrastructure.jwt import JwtService
from ns_backend.common import BaseRequestViewSet
from ns_backend.exceptions import BusinessError

if TYPE_CHECKING:
    pass


class AuthPublicViewSet(BaseRequestViewSet):
    authentication_required = False

    async def login(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username:
            return self.failed_response("username 不能为空", 11001)

        if not password:
            return self.failed_response("password 不能为空", 11002)

        data = await LoginApplicationService.execute(
            username=username,
            password=password,
            client_ip=self.get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            device_name=request.data.get("device_name"),
            device_type=request.data.get("device_type"),
            fingerprint_raw=request.data.get("fingerprint"),
            os_name=request.data.get("os_name"),
            browser_name=request.data.get("browser_name"),
        )

        return self.success_response(data)

    async def refresh_token(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
            return self.failed_response("refresh_token 不能为空", 11004)

        data = await RefreshApplicationService.execute(refresh_token=refresh_token)

        return self.success_response(data)

    @staticmethod
    def get_client_ip(request):
        trust_xff = bool(getattr(settings, "TRUST_X_FORWARDED_FOR", False))

        if trust_xff:
            x_forwarded_for = request.headers.get("X-Forwarded-For")
            if x_forwarded_for:
                candidate = x_forwarded_for.split(",")[0].strip()
                try:
                    ipaddress.ip_address(candidate)
                    return candidate
                except ValueError:
                    pass

        remote_addr = request.META.get("REMOTE_ADDR")
        if not remote_addr:
            return None

        try:
            ipaddress.ip_address(remote_addr)
            return remote_addr
        except ValueError:
            return None


class AuthPrivateViewSet(BaseRequestViewSet):
    authentication_required = True

    async def logout(self, request, *args, **kwargs):
        current_user = request.current_user
        access_token = self.get_bearer_token_from_request(request)
        refresh_token = request.data.get("refresh_token")

        if not access_token:
            return self.failed_response("access_token 不能为空", 11004)

        if refresh_token:
            payload = JwtService.decode_refresh_token(refresh_token)

            if not payload:
                raise BusinessError("Refresh Token 无效或已过期", 11005)

            refresh_user_id = payload.get("uid")

            if refresh_user_id != current_user.id:
                raise BusinessError("Refresh Token 与当前登录用户不匹配", 11012)

        success = await RevokeApplicationService.revoke_access_token(access_token)

        if refresh_token:
            refresh_success = await LogoutApplicationService.execute(refresh_token)
            success = success or refresh_success

        return self.success_response({
            "success": success,
        })

    async def current_user(self, request, *args, **kwargs):
        user = request.current_user

        if not user:
            return self.failed_response("用户未登录或登录状态已失效", 11007)

        return self.success_response({
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "email": user.email,
            "phone": user.phone,
            "user_type": user.user_type,
            "company_id": user.company_id,
            "subsidiary_id": user.subsidiary_id,
            "department_id": user.department_id,
            "is_active": user.is_active,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        })

    @staticmethod
    def get_bearer_token_from_request(request) -> str | None:
        authorization = request.headers.get("Authorization", "")

        if not authorization.startswith("Bearer "):
            return None

        token = authorization.removeprefix("Bearer ").strip()
        return token or None
