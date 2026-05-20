# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from iam.services.auth import AuthService
from ns_backend.common import BaseRequestViewSet

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

        data = await AuthService.login(
            username=username,
            password=password,
            client_ip=self.get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )

        return self.success_response(data)

    async def logout(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh_token")
        access_token = AuthService.get_bearer_token_from_request(request)

        success = False

        if refresh_token:
            success = await AuthService.logout(refresh_token)

        elif access_token:
            success = await AuthService.revoke_access_token(access_token)

        else:
            return self.failed_response("token 不能为空", 11004)

        return self.success_response({
            "success": success,
        })


    async def refresh_token(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
            return self.failed_response("refresh_token 不能为空", 11004)

        data = await AuthService.refresh_access_token(refresh_token)

        return self.success_response(data)

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.headers.get("X-Forwarded-For")

        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR")


class AuthPrivateViewSet(BaseRequestViewSet):
    authentication_required = True


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
