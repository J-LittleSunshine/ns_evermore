# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    TYPE_CHECKING,
)

from backend.common import NsViewSet
from ns_backend.iam.services import (
    AccessDecisionService,
    AuthService,
)

if TYPE_CHECKING:
    from rest_framework.request import Request


class AccessViewSet(NsViewSet):
    logger_name = "ns_backend.iam.access.api"

    allowed_actions = {
        "check",
        "batch_check",
    }

    async def check(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        user, _ = await AuthService.resolve_user_from_request(request)
        self.set_current_user(user)

        return await AccessDecisionService.check_with_audit(
            user=user,
            data=self.get_request_data(request),
            trace_id=self.get_trace_id(request),
        )

    async def batch_check(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        user, _ = await AuthService.resolve_user_from_request(request)
        self.set_current_user(user)

        return await AccessDecisionService.batch_check_with_audit(
            user=user,
            data=self.get_request_data(request),
            trace_id=self.get_trace_id(request),
        )

    @staticmethod
    def get_trace_id(request: "Request") -> str | None:
        trace_id = request.headers.get("X-Trace-Id") or request.headers.get("X-Request-ID")
        return str(trace_id).strip() if trace_id is not None and str(trace_id).strip() else None
