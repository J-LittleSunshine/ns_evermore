# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.services import ResourceAclService
from ns_backend.iam.views import IamRequestViewSet

if TYPE_CHECKING:
    pass


def _operator_id(request) -> int | None:
    """Resolve operator id from authenticated request context."""
    return getattr(getattr(request, "current_user", None), "id", None)


class ResourceAclViewSet(IamRequestViewSet):
    """IAM resource ACL API viewset."""

    audit_resource_type = "iam_resource_acl"

    async def grant_acl(self, request, *args, **kwargs):
        result = await ResourceAclService.grant_acl(data=request.data, operator_id=_operator_id(request))
        return self.success_response(result)

    async def revoke_acl(self, request, *args, **kwargs):
        result = await ResourceAclService.revoke_acl(data=request.data)
        return self.success_response(result)

    async def list_acl(self, request, *args, **kwargs):
        result = await ResourceAclService.list_acls(data=request.data)
        return self.success_response(result)
