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
        "menus",
        "data_scopes",
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

    async def menus(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        user, _ = await AuthService.resolve_user_from_request(request)
        self.set_current_user(user)

        menus = await AuthContextService.list_menus(user)

        return {
            "menus": menus,
        }

    async def data_scopes(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        user, _ = await AuthService.resolve_user_from_request(request)
        self.set_current_user(user)

        permission_codes = self.get_permission_codes_from_request(request)
        items = await AuthContextService.list_data_scopes(
            user=user,
            permission_codes=permission_codes,
        )

        return {
            "items": items,
        }

    @classmethod
    def get_permission_codes_from_request(cls, request: "Request") -> list[str]:
        data = cls.get_request_data(request)
        raw_permission_codes = data.get("permission_codes")

        if raw_permission_codes is None:
            raw_permission_codes = data.get("permissions")

        if raw_permission_codes is None:
            raw_permission_codes = data.get("codes")

        if isinstance(raw_permission_codes, str):
            raw_items = raw_permission_codes.split(",")
        elif isinstance(raw_permission_codes, (list, tuple, set)):
            raw_items = list(raw_permission_codes)
        else:
            return []

        clean_codes: list[str] = []
        seen_codes: set[str] = set()

        for item in raw_items:
            code = str(item or "").strip()
            if not code:
                continue

            if len(code) > 128:
                continue

            if code in seen_codes:
                continue

            seen_codes.add(code)
            clean_codes.append(code)

        return clean_codes
