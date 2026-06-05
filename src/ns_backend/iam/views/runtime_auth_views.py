# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from ns_backend.backend.common.viewset import BaseRequestViewSet
from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.services.runtime_auth import RuntimeIamInternalAuthService
from ns_common.error_codes import NsErrorCode


class RuntimeIamInternalViewSet(BaseRequestViewSet):
    """Internal IAM API used by ns_runtime.

    This endpoint is protected by a runtime internal service bearer token, not
    by normal user authentication or route permissions.
    """

    authentication_classes = ()
    permission_classes = ()
    throttle_classes = ()

    service_class = RuntimeIamInternalAuthService

    def perform_authentication(self, request) -> None:
        """Disable DRF default authentication for runtime internal API.

        ns_backend intentionally does not install django.contrib.auth. DRF's
        default unauthenticated-user path imports django.contrib.auth models,
        so this method must not touch request.user.
        """
        _ = request

    def check_permissions(self, request) -> None:
        """Disable DRF permission classes for runtime internal API."""
        _ = request

    def check_throttles(self, request) -> None:
        """Disable DRF throttle classes for runtime internal API."""
        _ = request

    def initial(self, request, *args, **kwargs) -> None:
        """Initialize request and verify internal service token.

        ADRF calls initial() through sync_to_async(), so this method must remain
        synchronous.

        We still call super().initial() to let DRF initialize renderer/content
        negotiation fields such as request.accepted_renderer. Default DRF
        authentication is disabled by perform_authentication().
        """
        super().initial(request, *args, **kwargs)

        token = self.get_bearer_token_from_request(request)
        if not self.service_class.verify_internal_service_token(token):
            raise BusinessError("runtime internal service token is invalid", NsErrorCode.PERMISSION_DENIED)

    async def introspect_token(self, request, *args, **kwargs):
        """Introspect one IAM access token for runtime frontend authentication."""
        result = await self.service_class.introspect_token(self._request_data(request))
        return self.success_response(result)

    async def authorize(self, request, *args, **kwargs):
        """Authorize one runtime action."""
        result = await self.service_class.authorize(
            self._request_data(request),
            trace_id=self._trace_id(request),
        )
        return self.success_response(result)

    async def batch_authorize(self, request, *args, **kwargs):
        """Authorize multiple runtime actions."""
        result = await self.service_class.batch_authorize(
            self._request_data(request),
            trace_id=self._trace_id(request),
        )
        return self.success_response(result)

    @staticmethod
    def get_bearer_token_from_request(request) -> str | None:
        """Extract bearer token from request Authorization header."""
        headers = getattr(request, "headers", None)
        if headers is None:
            return None

        authorization = str(headers.get("Authorization", "")).strip()
        if not authorization.startswith("Bearer "):
            return None

        token = authorization.removeprefix("Bearer ").strip()
        return token or None

    @staticmethod
    def _trace_id(request) -> str | None:
        """Resolve trace id from request headers."""
        headers = getattr(request, "headers", None)
        if headers is None:
            return None

        trace_id = headers.get("X-Trace-Id") or headers.get("X-Request-Id")
        return str(trace_id).strip() if trace_id is not None and str(trace_id).strip() else None

    @staticmethod
    def _request_data(request) -> dict[str, Any]:
        """Return request.data as dict."""
        data = getattr(request, "data", None)
        if not isinstance(data, dict):
            raise BusinessError("request data must be an object", NsErrorCode.INVALID_VALUE)
        return data
