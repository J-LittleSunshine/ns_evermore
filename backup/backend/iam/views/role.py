# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from iam.models import IamRole
from iam.services.role import RoleService
from iam.validators import RoleValidator
from iam.views.base import BaseIamViewSet

if TYPE_CHECKING:
    pass


class RoleViewSet(BaseIamViewSet):
    model_class = IamRole
    validator_class = RoleValidator
    tenant_scope_field = "company_id"
    tenant_create_field = "company_id"
    enterprise_resource_required = False
    detail_fields = ("id", "company_id", "role_code", "role_name", "role_scope", "status")
    list_fields = detail_fields
    create_fields = ("company_id", "role_code", "role_name", "role_scope", "status")
    update_fields = ("role_name", "status")

    async def list_item(self, request, *args, **kwargs):
        page = request.data.get("page", 1)
        page_size = request.data.get("page_size", 20)

        data = await RoleService.list_roles(
            fields=self.list_fields,
            page=page,
            page_size=page_size,
            operator=request.current_user,
        )

        return self.success_response(data)

    async def detail_item(self, request, *args, **kwargs):
        role = await RoleService.get_role(
            role_id=request.data.get("id"),
            operator=request.current_user,
        )
        return self.success_response(RoleService.serialize(role, self.detail_fields))

    async def create_item(self, request, *args, **kwargs):
        data = self.validate_create_data(request.data)
        operator_id = self.get_operator_id(request)
        result = await RoleService.create_role(
            data=data,
            operator=request.current_user,
            operator_id=operator_id,
        )
        return self.success_response(result)

    async def update_item(self, request, *args, **kwargs):
        item_id = request.data.get("id")
        data = self.validate_update_data(request.data)
        operator_id = self.get_operator_id(request)

        await RoleService.update_role(
            role_id=item_id,
            data=data,
            operator=request.current_user,
            operator_id=operator_id,
        )

        return self.success_response()

    async def delete_item(self, request, *args, **kwargs):
        await RoleService.delete_role(
            role_id=request.data.get("id"),
            operator=request.current_user,
        )
        return self.success_response()
