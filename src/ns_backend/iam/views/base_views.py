# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.services import CompanyService, DepartmentService, PermissionBaseService, RoleService, SubsidiaryService, UserService
from ns_backend.iam.views import BaseIamViewSet

if TYPE_CHECKING:
    pass


class CompanyViewSet(BaseIamViewSet):
    service_class = CompanyService


class SubsidiaryViewSet(BaseIamViewSet):
    service_class = SubsidiaryService


class DepartmentViewSet(BaseIamViewSet):
    service_class = DepartmentService


class PermissionViewSet(BaseIamViewSet):
    service_class = PermissionBaseService


class RoleViewSet(BaseIamViewSet):
    service_class = RoleService


class UserViewSet(BaseIamViewSet):
    service_class = UserService

    async def reset_password(self, request, *args, **kwargs):
        operator = getattr(request, "current_user", None)
        await self.service.reset_password(
            item_id=request.data.get("id"),
            password=request.data.get("password"),
            operator_id=getattr(operator, "id", None),
            tenant_context=self._tenant_context(request),
        )
        return self.success_response()
