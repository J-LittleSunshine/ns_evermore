# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    TYPE_CHECKING,
)

from backend.common import NsViewSet
from ns_backend.iam.services import (
    AuthContextService,
    AuthService,
)

if TYPE_CHECKING:
    from rest_framework.request import Request


class AuthViewSet(NsViewSet):
    logger_name = "ns_backend.iam.auth.api"

    allowed_actions = {
        "login",
        "refresh",
        "logout",
        "profile",
        "current_user",
        "permissions",
    }

    async def login(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        result = await AuthService.login(
            data=self.get_request_data(request),
            request=request,
        )
        request.current_user = result.user
        self.set_current_user(result.user)

        return result.data

    async def refresh(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await AuthService.refresh(
            data=self.get_request_data(request),
        )

    async def logout(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await AuthService.logout(
            data=self.get_request_data(request),
            request=request,
        )

    async def profile(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        user, _ = await AuthService.resolve_user_from_request(request)
        self.set_current_user(user)

        return AuthContextService.build_profile(user)

    async def current_user(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        user, _ = await AuthService.resolve_user_from_request(request)
        self.set_current_user(user)

        return AuthService.build_current_user_payload(user)

    async def permissions(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        user, _ = await AuthService.resolve_user_from_request(request)
        self.set_current_user(user)

        permission_codes = await AuthContextService.list_permission_codes(user)

        return {
            "permissions": permission_codes,
        }