# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    TYPE_CHECKING,
)

from ns_backend.iam.services import IamSyncService
from ns_backend.iam.views.management_views import IamManagementViewSet

if TYPE_CHECKING:
    from rest_framework.request import Request


class ResourceSyncViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.resource_sync.api"
    service_class = IamSyncService
    audit_resource_type = "iam_resource_sync"

    allowed_actions = {
        "sync",
        "batch_sync",
    }

    required_permissions = {
        "sync": ("iam:resource:sync",),
        "batch_sync": ("iam:resource:sync",),
    }

    async def sync(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await self.execute_with_operation_audit(
            request=request,
            operation_type="sync",
            handler=lambda operator, data: self.get_service_class().sync_resource(
                data=data,
                operator=operator,
            ),
        )

    async def batch_sync(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await self.execute_with_operation_audit(
            request=request,
            operation_type="sync",
            handler=lambda operator, data: self.get_service_class().batch_sync_resources(
                data=data,
                operator=operator,
            ),
        )


class PermissionSyncViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.permission_sync.api"
    service_class = IamSyncService
    audit_resource_type = "iam_permission_sync"

    allowed_actions = {
        "sync",
        "batch_sync",
    }

    required_permissions = {
        "sync": ("iam:permission:sync",),
        "batch_sync": ("iam:permission:sync",),
    }

    async def sync(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await self.execute_with_operation_audit(
            request=request,
            operation_type="sync",
            handler=lambda operator, data: self.get_service_class().sync_permission(
                data=data,
                operator=operator,
            ),
        )

    async def batch_sync(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await self.execute_with_operation_audit(
            request=request,
            operation_type="sync",
            handler=lambda operator, data: self.get_service_class().batch_sync_permissions(
                data=data,
                operator=operator,
            ),
        )
