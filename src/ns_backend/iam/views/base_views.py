# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.services import CompanyCrudService, SubsidiaryCrudService, DepartmentCrudService, PermissionCrudService, RoleCrudService, UserCrudService
from ns_backend.iam.views import BaseIamCrudViewSet

if TYPE_CHECKING:
    pass


class CompanyViewSet(BaseIamCrudViewSet):
    crud_service_class = CompanyCrudService


class SubsidiaryViewSet(BaseIamCrudViewSet):
    crud_service_class = SubsidiaryCrudService


class DepartmentViewSet(BaseIamCrudViewSet):
    crud_service_class = DepartmentCrudService


class PermissionViewSet(BaseIamCrudViewSet):
    crud_service_class = PermissionCrudService


class RoleViewSet(BaseIamCrudViewSet):
    crud_service_class = RoleCrudService


class UserViewSet(BaseIamCrudViewSet):
    crud_service_class = UserCrudService

    async def reset_password(self, request, *args, **kwargs):
        operator = getattr(request, "current_user", None)
        await self.crud.reset_password(
            item_id=request.data.get("id"),
            password=request.data.get("password"),
            operator_id=getattr(operator, "id", None),
            tenant_context=self._tenant_context(request),
        )
        return self.success_response()
