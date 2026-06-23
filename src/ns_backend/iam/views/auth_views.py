# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    TYPE_CHECKING,
)

from backend.common import NsViewSet
from ns_backend.iam.services import AuthService

if TYPE_CHECKING:
    from rest_framework.request import Request


class AuthViewSet(NsViewSet):
    logger_name = "ns_backend.iam.auth.api"

    allowed_actions = {
        "login",
        "refresh",
        "logout",
    }

    async def login(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        result = await AuthService.login(data=self.get_request_data(request), request=request, )
        return result.data

    async def refresh(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await AuthService.refresh(data=self.get_request_data(request), )

    async def logout(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await AuthService.logout(data=self.get_request_data(request), request=request)

    @staticmethod
    def get_request_data(request: "Request") -> dict[str, Any]:
        data = getattr(request, "data", None)

        if isinstance(data, dict):
            return dict(data)

        return {}
