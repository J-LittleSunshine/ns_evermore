# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_common.error_codes import NsErrorCode
from ..backend.common.viewset import BaseRequestViewSet
from ..backend.exceptions import BusinessError

if TYPE_CHECKING:
    pass


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
            raise BusinessError("User is not logged in or session has expired", NsErrorCode.USER_NOT_LOGGED_IN_OR_SESSION_EXPIRED)

        if not bool(getattr(user, "is_active", False)):
            raise BusinessError("User is disabled", NsErrorCode.USER_DISABLED)

        request.current_user = user

        for permission_code in self.required_permissions:
            has_permission = await self.has_permission(user=user, permission_code=permission_code)
            if not has_permission:
                raise BusinessError(f"Permission denied: {permission_code}", NsErrorCode.PERMISSION_DENIED)

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
        return await permission_service.has_permission(user=user, permission_code=permission_code)

    @staticmethod
    def get_bearer_token_from_request(request) -> str | None:
        headers = getattr(request, "headers", None)
        if headers is None:
            return None

        authorization = str(headers.get("Authorization", "")).strip()
        if not authorization.startswith("Bearer "):
            return None

        token = authorization.removeprefix("Bearer ").strip()
        return token or None
