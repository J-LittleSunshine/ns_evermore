# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.services import ResourceRegistryService
from ns_backend.iam.views import IamRequestViewSet

if TYPE_CHECKING:
    pass


def _operator_id(request) -> int | None:
    """Resolve operator id from authenticated request context."""
    return getattr(getattr(request, "current_user", None), "id", None)


class ResourceViewSet(IamRequestViewSet):
    """IAM resource registry API viewset."""

    audit_resource_type = "iam_resource"

    async def register_resource(self, request, *args, **kwargs):
        result = await ResourceRegistryService.register_resource(data=request.data, operator_id=_operator_id(request))
        return self.success_response(result)

    async def register_resource_action(self, request, *args, **kwargs):
        result = await ResourceRegistryService.register_resource_action(data=request.data, operator_id=_operator_id(request))
        return self.success_response(result)

    async def list_resources(self, request, *args, **kwargs):
        result = await ResourceRegistryService.list_resources(data=request.data)
        return self.success_response(result)

