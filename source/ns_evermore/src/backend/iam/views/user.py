# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.services.permission import PermissionService
from iam.services.user import UserService
from iam.validators import UserValidator
from iam.views.base import BaseIamViewSet
from ns_backend.exceptions import BusinessError


class UserViewSet(BaseIamViewSet):
    service_class = UserService
    validator_class = UserValidator

    list_fields = detail_fields = (
        "id",
        "username",
        "email",
        "phone",
        "display_name",
        "user_type",
        "company_id",
        "subsidiary_id",
        "department_id",
        "is_active",
        "is_staff",
        "is_superuser",
        "created_by",
        "updated_by",
        "created_at",
        "updated_at",
    )

    update_fields = (
        "email",
        "phone",
        "display_name",
        "company_id",
        "subsidiary_id",
        "department_id",
        "is_active",
        "is_staff",
        "is_superuser",
    )

    critical_field_permissions = {
        "is_staff": "iam:user:update_staff",
        "is_superuser": "iam:user:update_superuser",
    }

    async def create_item(self, request, *args, **kwargs):
        data = self.validate_create_data(request.data)
        operator_id = self.get_operator_id(request)

        result = await UserService.create_user(
            data=data,
            operator_id=operator_id,
        )

        return self.success_response(result)

    async def update_item(self, request, *args, **kwargs):
        item_id = request.data.get("id")

        if not item_id:
            raise BusinessError("id 不能为空", 10001)

        data = self.validate_update_data(request.data)
        operator_id = self.get_operator_id(request)

        await self.check_critical_update_permissions(
            operator=request.current_user,
            update_data=data,
        )

        await self.service_class.update_item(
            item_id=item_id,
            data=data,
            operator_id=operator_id,
        )

        return self.success_response()

    async def check_critical_update_permissions(self, operator, update_data: dict) -> None:
        if operator.is_superuser:
            return

        for field, permission_code in self.critical_field_permissions.items():
            if field not in update_data:
                continue

            has_permission = await PermissionService.has_permission(
                user=operator,
                permission_code=permission_code,
            )

            if not has_permission:
                raise BusinessError(f"权限不足：{permission_code}", 11009)

    async def reset_password(self, request, *args, **kwargs):
        user_id = request.data.get("id")
        raw_password = request.data.get("password")
        operator_id = self.get_operator_id(request)

        await UserService.reset_password(
            user_id=user_id,
            raw_password=raw_password,
            operator_id=operator_id,
        )

        return self.success_response()
