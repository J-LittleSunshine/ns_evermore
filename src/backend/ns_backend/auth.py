# -*- coding: utf-8 -*-
from __future__ import annotations

from ns_backend.common import BaseRequestViewSet
from ns_backend.exceptions import BusinessError


class AuthenticatedRequestViewSet(BaseRequestViewSet):
    authentication_required = True
    required_permissions: tuple[str, ...] = ()
    verify_service = None
    permission_service = None

    async def initial(self, request, *args, **kwargs):
        await super().initial(request, *args, **kwargs)  # noqa

        if not self.authentication_required:
            return

        user = await self.get_current_user(request)

        if not user:
            raise BusinessError("用户未登录或登录状态已失效", 11007)

        if not user.is_active:
            raise BusinessError("用户已被禁用", 11008)

        request.current_user = user

        for permission_code in self.required_permissions:
            has_permission = await self.has_permission(
                user=user,
                permission_code=permission_code,
            )

            if not has_permission:
                raise BusinessError(f"权限不足：{permission_code}", 11009)

    @classmethod
    async def get_current_user(cls, request):
        token = cls.get_bearer_token_from_request(request)

        if not token:
            return None

        verify_service = cls.get_verify_service()

        if verify_service is None:
            return None

        return await verify_service.get_user_by_access_token(token)

    @classmethod
    def get_verify_service(cls):
        return cls.verify_service

    @classmethod
    def get_permission_service(cls):
        return cls.permission_service

    @classmethod
    async def has_permission(cls, user, permission_code: str) -> bool:
        permission_service = cls.get_permission_service()

        if permission_service is None:
            return False

        return await permission_service.has_permission(
            user=user,
            permission_code=permission_code,
        )

    @staticmethod
    def get_bearer_token_from_request(request) -> str | None:
        authorization = request.headers.get("Authorization", "")

        if not authorization.startswith("Bearer "):
            return None

        token = authorization.removeprefix("Bearer ").strip()
        return token or None

