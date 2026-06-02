# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.services.authorize import AuthorizeService
from ns_backend.iam.views import IamRequestViewSet

if TYPE_CHECKING:
    pass


class AuthorizeViewSet(IamRequestViewSet):
    """IAM unified authorize API viewset."""

    audit_resource_type = "iam_authorize"

    @staticmethod
    def _trace_id(request) -> str | None:
        headers = getattr(request, "headers", None)
        if headers is None:
            return None
        return headers.get("X-Trace-Id") or headers.get("X-Request-Id")

    async def check(self, request, *args, **kwargs):
        decision = await AuthorizeService.check(user=request.current_user, data=request.data, trace_id=self._trace_id(request))
        return self.success_response(decision)

    async def batch_check(self, request, *args, **kwargs):
        result = await AuthorizeService.batch_check(user=request.current_user, data=request.data, trace_id=self._trace_id(request))
        return self.success_response(result)

