# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    TYPE_CHECKING,
)

from backend.common import NsViewSet
from ns_backend.iam.services import (
    AuthService,
    SessionService,
)

if TYPE_CHECKING:
    from rest_framework.request import Request


class SessionViewSet(NsViewSet):
    logger_name = "ns_backend.iam.session.api"

    allowed_actions = {
        "list",
        "revoke",
    }

    async def list(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        user, _ = await AuthService.resolve_user_from_request(request)
        self.set_current_user(user)

        return await SessionService.list_current_user_sessions(
            user=user,
            access_token=self.get_bearer_token_from_request(request),
        )

    async def revoke(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        user, _ = await AuthService.resolve_user_from_request(request)
        self.set_current_user(user)

        request_data = self.get_request_data(request)

        return await SessionService.revoke_current_user_session(
            user=user,
            session_id=str(request_data.get("session_id") or "").strip(),
        )

    @staticmethod
    def get_bearer_token_from_request(request: "Request") -> str | None:
        authorization = str(request.headers.get("Authorization", "") or "").strip()

        if not authorization.startswith("Bearer "):
            return None

        token = authorization.removeprefix("Bearer ").strip()
        return token or None
