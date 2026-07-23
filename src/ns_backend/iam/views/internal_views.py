# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    TYPE_CHECKING,
)

from backend.common import NsViewSet
from ns_backend.iam.errors import IamRuntimeAccessDeniedError
from ns_backend.iam.services import InternalIamService

if TYPE_CHECKING:
    from rest_framework.request import Request


class InternalIamViewSet(NsViewSet):
    logger_name = "ns_backend.iam.internal.api"

    allowed_actions = {
        "introspect_token",
        "access_check",
        "runtime_access_check",
        "permission_snapshot",
        "issue_runtime_node_credential",
        "refresh_runtime_node_credential",
        "revoke_runtime_node_credential",
        "runtime_bootstrap",
        "validate_payload_ref",
        "revalidate_payload_ref",
        "batch_access_check",
        "resolve_resource_filter",
    }

    service_class = InternalIamService

    def check_action_access(self, request: "Request", *args: Any, **kwargs: Any) -> None:
        token = self.get_bearer_token_from_request(request)

        if not self.service_class.verify_internal_service_token(token):
            raise IamRuntimeAccessDeniedError(
                "internal service token is invalid.",
            )

    async def introspect_token(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await self.service_class.introspect_token(
            self.get_request_data(request),
        )

    async def access_check(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await self.service_class.access_check(
            self.get_request_data(request),
            trace_id=self.get_trace_id(request),
        )

    async def runtime_access_check(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await self.service_class.runtime_access_check(
            self.get_request_data(request),
            trace_id=self.get_trace_id(request),
        )

    async def revalidate_payload_ref(
        self,
        request: "Request",
        *args: Any,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return await self.service_class.revalidate_payload_ref(
            self.get_request_data(request),
            trace_id=self.get_trace_id(request),
        )

    async def permission_snapshot(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await self.service_class.permission_snapshot(
            self.get_request_data(request),
        )

    async def issue_runtime_node_credential(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await self.service_class.issue_runtime_node_credential(self.get_request_data(request))

    async def refresh_runtime_node_credential(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await self.service_class.refresh_runtime_node_credential(self.get_request_data(request))

    async def revoke_runtime_node_credential(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await self.service_class.revoke_runtime_node_credential(self.get_request_data(request))

    async def runtime_bootstrap(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await self.service_class.runtime_bootstrap(self.get_request_data(request))

    async def validate_payload_ref(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await self.service_class.validate_payload_ref(self.get_request_data(request))

    async def batch_access_check(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await self.service_class.batch_access_check(
            self.get_request_data(request),
            trace_id=self.get_trace_id(request),
        )

    async def resolve_resource_filter(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await self.service_class.resolve_resource_filter(
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
