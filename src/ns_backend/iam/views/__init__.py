# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from .. import AuthenticatedRequestViewSet
from ..services import TenantService, VerifyService, PermissionService

if TYPE_CHECKING:
    pass


class IamRequestViewSet(AuthenticatedRequestViewSet):
    verify_service = VerifyService
    permission_service = PermissionService
    authentication_required = True


class BaseIamCrudViewSet(IamRequestViewSet):
    crud_service_class = None

    @property
    def crud(self):
        if self.crud_service_class is None:
            raise RuntimeError("crud_service_class is not configured")
        return self.crud_service_class

    @staticmethod
    def _current_user(request):
        return getattr(request, "current_user", None)

    @classmethod
    def _tenant_context(cls, request):
        user = getattr(request, "current_user", None)
        if user is None:
            return None
        return TenantService.from_user(user)

    async def list_item(self, request, *args, **kwargs):
        data = await self.crud.list_items(
            page=request.data.get("page", 1),
            page_size=request.data.get("page_size", 20),
            tenant_context=self._tenant_context(request),
        )
        return self.success_response(data)

    async def detail_item(self, request, *args, **kwargs):
        data = await self.crud.detail_item(
            item_id=request.data.get("id"),
            tenant_context=self._tenant_context(request),
        )
        return self.success_response(data)

    async def create_item(self, request, *args, **kwargs):
        user = self._current_user(request)
        result = await self.crud.create_item(
            data=request.data,
            operator_id=getattr(user, "id", None),
            tenant_context=self._tenant_context(request),
        )
        return self.success_response(result)

    async def update_item(self, request, *args, **kwargs):
        user = self._current_user(request)
        await self.crud.update_item(
            item_id=request.data.get("id"),
            data=request.data,
            operator_id=getattr(user, "id", None),
            tenant_context=self._tenant_context(request),
        )
        return self.success_response()

    async def delete_item(self, request, *args, **kwargs):
        await self.crud.delete_item(
            item_id=request.data.get("id"),
            tenant_context=self._tenant_context(request),
        )
        return self.success_response()
