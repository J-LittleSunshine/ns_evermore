# -*- coding: utf-8 -*-
from __future__ import annotations

import ipaddress
from typing import TYPE_CHECKING

from django.conf import settings

from iam.services.auth import LoginService, LogoutService, RefreshService, RevokeService
from iam.views.base import IamRequestViewSet

if TYPE_CHECKING:
    pass


class AuthPublicViewSet(IamRequestViewSet):
    authentication_required = False

    async def login(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username:
            return self.failed_response("username cannot be empty", 11001)

        if not password:
            return self.failed_response("password cannot be empty", 11002)

        data = await LoginService.execute(
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
            return self.failed_response("refresh_token cannot be empty", 11004)

        data = await RefreshService.execute(refresh_token=refresh_token)

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


class AuthPrivateViewSet(IamRequestViewSet):
    authentication_required = True

    async def logout(self, request, *args, **kwargs):
        current_user = request.current_user
        access_token = self.get_bearer_token_from_request(request)
        refresh_token = request.data.get("refresh_token")

        if not access_token:
            return self.failed_response("access_token cannot be empty", 11004)

        success = await RevokeService.revoke_access_token(access_token)

        if refresh_token:
            refresh_success = await LogoutService.execute(
                refresh_token=refresh_token,
                current_user_id=current_user.id,
            )
            success = success or refresh_success

        return self.success_response({
            "success": success,
        })

    async def current_user(self, request, *args, **kwargs):
        user = request.current_user

        if not user:
            return self.failed_response("User is not logged in or session has expired", 11007)

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
