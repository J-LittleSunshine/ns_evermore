# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    TYPE_CHECKING,
)

from backend.common import NsViewSet
from ns_backend.iam.errors import IamRuntimeAccessDeniedError
from ns_backend.iam.services import RuntimeIamInternalAuthService

if TYPE_CHECKING:
    from rest_framework.request import Request


class RuntimeIamInternalViewSet(NsViewSet):
    logger_name = "ns_backend.iam.runtime.api"

    allowed_actions = {
        "introspect_token",
        "authorize",
        "batch_authorize",
    }

    service_class = RuntimeIamInternalAuthService

    def check_action_access(self, request: "Request", *args: Any, **kwargs: Any) -> None:
        token = self.get_bearer_token_from_request(request)

        if not self.service_class.verify_internal_service_token(token):
            raise IamRuntimeAccessDeniedError(
                "runtime internal service token is invalid.",
            )

    async def introspect_token(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await self.service_class.introspect_token(
            self.get_request_data(request),
        )

    async def authorize(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await self.service_class.authorize(
            self.get_request_data(request),
            trace_id=self.get_trace_id(request),
        )

    async def batch_authorize(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await self.service_class.batch_authorize(
            self.get_request_data(request),
            trace_id=self.get_trace_id(request),
        )

    @staticmethod
    def get_bearer_token_from_request(request: "Request") -> str | None:
        authorization = str(request.headers.get("Authorization", "") or "").strip()

        if not authorization.startswith("Bearer "):
            return None

        token = authorization.removeprefix("Bearer ").strip()
        return token or None

    @staticmethod
    def get_trace_id(request: "Request") -> str | None:
        trace_id = request.headers.get("X-Trace-Id") or request.headers.get("X-Request-ID")
        return str(trace_id).strip() if trace_id is not None and str(trace_id).strip() else None
