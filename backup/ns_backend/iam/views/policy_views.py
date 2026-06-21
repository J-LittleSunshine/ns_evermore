# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.services import PolicyService
from ns_backend.iam.views import IamRequestViewSet

if TYPE_CHECKING:
    pass


def _operator_id(request) -> int | None:
    """Resolve operator id from authenticated request context."""
    return getattr(getattr(request, "current_user", None), "id", None)


class PolicyViewSet(IamRequestViewSet):
    """IAM policy management API viewset."""

    audit_resource_type = "iam_policy"

    async def create_policy(self, request, *args, **kwargs):
        result = await PolicyService.create_policy(data=request.data, operator_id=_operator_id(request))
        return self.success_response(result)

    async def update_policy(self, request, *args, **kwargs):
        result = await PolicyService.update_policy(data=request.data, operator_id=_operator_id(request))
        return self.success_response(result)

    async def publish_policy(self, request, *args, **kwargs):
        result = await PolicyService.publish_policy(data=request.data, operator_id=_operator_id(request))
        return self.success_response(result)

    async def disable_policy(self, request, *args, **kwargs):
        result = await PolicyService.disable_policy(data=request.data, operator_id=_operator_id(request))
        return self.success_response(result)

    async def add_rule(self, request, *args, **kwargs):
        result = await PolicyService.add_rule(data=request.data, operator_id=_operator_id(request))
        return self.success_response(result)

    async def remove_rule(self, request, *args, **kwargs):
        result = await PolicyService.remove_rule(data=request.data)
        return self.success_response(result)

    async def list_rules(self, request, *args, **kwargs):
        result = await PolicyService.list_rules(data=request.data)
        return self.success_response(result)
