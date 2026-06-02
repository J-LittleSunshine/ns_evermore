# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam import AuthenticatedRequestViewSet, AuditRequestMixin
from ns_backend.iam.services import TenantService, VerifyService, PermissionService
from ns_backend.iam.services.authorize import AuthorizeService

if TYPE_CHECKING:
    pass


class IamRequestViewSet(AuditRequestMixin, AuthenticatedRequestViewSet):
    verify_service = VerifyService
    permission_service = PermissionService
    authorize_service = AuthorizeService
    authentication_required = True


class BaseIamViewSet(IamRequestViewSet):
    service_class = None

    @property
    def service(self):
        """Return configured service class for current IAM view."""
        if self.service_class is None:
            raise RuntimeError("service_class is not configured")
        return self.service_class

    @staticmethod
    def _current_user(request):
        """Return current authenticated user bound to request."""
        return getattr(request, "current_user", None)

    @classmethod
    def _tenant_context(cls, request):
        """Build tenant context from request user."""
        user = getattr(request, "current_user", None)
        if user is None:
            return None
        return TenantService.from_user(user)

    async def list_item(self, request, *args, **kwargs):
        """List IAM domain entities by paging and filter conditions."""
        user = self._current_user(request)
        data = await self.service.list_items(
            page=request.data.get("page", 1),
            page_size=request.data.get("page_size", 20),
            filters=request.data.get("filters"),
            keyword=request.data.get("keyword"),
            order_by=request.data.get("order_by"),
            include_staff=request.data.get("include_staff"),
            include_superuser=request.data.get("include_superuser"),
            operator=user,
            tenant_context=self._tenant_context(request),
        )
        return self.success_response(data)

    async def detail_item(self, request, *args, **kwargs):
        """Query one IAM domain entity by identifier."""
        user = self._current_user(request)
        data = await self.service.detail_item(
            item_id=request.data.get("id"),
            operator=user,
            tenant_context=self._tenant_context(request),
        )
        return self.success_response(data)

    async def create_item(self, request, *args, **kwargs):
        """Create one IAM domain entity."""
        user = self._current_user(request)
        result = await self.service.create_item(
            data=request.data,
            operator=user,
            operator_id=getattr(user, "id", None),
            tenant_context=self._tenant_context(request),
        )
        return self.success_response(result)

    async def update_item(self, request, *args, **kwargs):
        """Update one IAM domain entity."""
        user = self._current_user(request)
        await self.service.update_item(
            item_id=request.data.get("id"),
            data=request.data,
            operator=user,
            operator_id=getattr(user, "id", None),
            tenant_context=self._tenant_context(request),
        )
        return self.success_response()

    async def delete_item(self, request, *args, **kwargs):
        """Delete one IAM domain entity."""
        user = self._current_user(request)
        await self.service.delete_item(
            item_id=request.data.get("id"),
            operator=user,
            tenant_context=self._tenant_context(request),
        )
        return self.success_response()
