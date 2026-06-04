# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.http import JsonResponse

from backend.common.viewset import AuthenticatedRequestViewSet
from ns_backend.storage.services import StorageObjectService

if TYPE_CHECKING:
    pass


class StorageRequestViewSet(AuthenticatedRequestViewSet):
    """Base storage API viewset with IAM route-level authorization."""

    authorize_resource_type = "storage.object"
    audit_resource_type = "storage.object"
    audit_request_summary_fields = (
        "bucket",
        "object_name",
        "module_code",
        "resource_type",
        "resource_id",
        "original_filename",
        "content_type",
        "expires_seconds",
    )

    @classmethod
    def get_authorize_resource_type(cls, request, permission_code: str) -> str:
        """Resolve IAM resource type for storage route permission."""
        _ = request
        normalized_permission_code = str(permission_code or "").strip().lower()

        if normalized_permission_code.startswith("storage:object_ref:"):
            return "storage.object_ref"

        if normalized_permission_code.startswith("storage:object:"):
            return "storage.object"

        return super().get_authorize_resource_type(request, permission_code)

    def get_audit_resource_type(self) -> str:
        """Resolve audit resource type by current action."""
        action = str(getattr(self, "action", "") or "").strip()

        if action in {"list_object_refs", "detail_object_ref", "delete_object_ref"}:
            return "storage.object_ref"

        return "storage.object"


class StorageObjectViewSet(StorageRequestViewSet):
    """Generic storage object APIs.

    These APIs expose technical storage capabilities only.
    They must not encode business attachment semantics.
    """

    async def upload_object(self, request, *args, **kwargs) -> JsonResponse:
        """Upload one object and persist object reference."""
        _ = (args, kwargs)
        operator = getattr(request, "current_user", None)
        data = await StorageObjectService.upload_object(
            request=request,
            operator=operator,
        )
        return self.success_response(data)

    async def presigned_get_url(self, request, *args, **kwargs):
        """Create presigned GET URL for one object reference."""
        _ = (args, kwargs)
        data = await StorageObjectService.presigned_get_url(
            data=request.data,
        )
        return self.success_response(data)

    async def list_object_refs(self, request, *args, **kwargs):
        """List object references by resource identity."""
        _ = (args, kwargs)
        data = await StorageObjectService.list_object_refs(
            data=request.data,
        )
        return self.success_response(data)

    async def detail_object_ref(self, request, *args, **kwargs):
        """Get object reference detail."""
        _ = (args, kwargs)
        data = await StorageObjectService.detail_object_ref(
            data=request.data,
        )
        return self.success_response(data)

    async def delete_object_ref(self, request, *args, **kwargs):
        """Soft delete object reference metadata only."""
        _ = (args, kwargs)
        data = await StorageObjectService.delete_object_ref(
            data=request.data,
        )
        return self.success_response(data)
