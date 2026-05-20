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

    admin_user_permission = "iam:user:update_staff"
    superuser_permission = "iam:user:update_superuser"

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
        "is_staff": admin_user_permission,
        "is_superuser": superuser_permission,
    }

    async def list_item(self, request, *args, **kwargs):
        page = request.data.get("page", 1)
        page_size = request.data.get("page_size", 20)
        include_staff = await self.has_admin_user_permission(request.current_user)
        include_superuser = bool(request.current_user.is_superuser)

        data = await UserService.list_users(
            fields=self.list_fields,
            page=page,
            page_size=page_size,
            include_staff=include_staff,
            include_superuser=include_superuser,
        )

        return self.success_response(data)

    async def detail_item(self, request, *args, **kwargs):
        user = await UserService.get_user(request.data.get("id"))

        await self.check_admin_user_operation_permissions(
            operator=request.current_user,
            target_user=user,
        )

        return self.success_response(UserService.serialize(user, self.detail_fields))

    async def create_item(self, request, *args, **kwargs):
        data = self.validate_create_data(request.data)
        operator_id = self.get_operator_id(request)

        await self.check_critical_update_permissions(
            operator=request.current_user,
            update_data=data,
        )

        result = await UserService.create_user(
            data=data,
            operator_id=operator_id,
        )

        return self.success_response(result)

    async def update_item(self, request, *args, **kwargs):
        item_id = request.data.get("id")
        user = await UserService.get_user(item_id)
        data = self.validate_update_data(request.data)
        operator_id = self.get_operator_id(request)

        await self.check_admin_user_operation_permissions(
            operator=request.current_user,
            target_user=user,
        )

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

    async def delete_item(self, request, *args, **kwargs):
        item_id = request.data.get("id")
        user = await UserService.get_user(item_id)

        await self.check_admin_user_operation_permissions(
            operator=request.current_user,
            target_user=user,
        )

        await self.service_class.delete_item(item_id=item_id)

        return self.success_response()

    async def reset_password(self, request, *args, **kwargs):
        user_id = request.data.get("id")
        raw_password = request.data.get("password")
        operator_id = self.get_operator_id(request)
        user = await UserService.get_user(user_id)

        await self.check_admin_user_operation_permissions(
            operator=request.current_user,
            target_user=user,
        )

        await UserService.reset_password(
            user_id=user_id,
            raw_password=raw_password,
            operator_id=operator_id,
        )

        return self.success_response()

    async def check_critical_update_permissions(self, operator, update_data: dict) -> None:
        if self._is_truthy(update_data.get("is_superuser")) and not operator.is_superuser:
            raise BusinessError("后台管理员不能操作超级管理员", 11010)

        if operator.is_superuser:
            return

        for field, permission_code in self.critical_field_permissions.items():
            if field not in update_data:
                continue

            if not self._is_truthy(update_data.get(field)):
                continue

            has_permission = await PermissionService.has_permission(
                user=operator,
                permission_code=permission_code,
            )

            if not has_permission:
                raise BusinessError(f"权限不足：{permission_code}", 11009)

    async def check_admin_user_operation_permissions(self, operator, target_user) -> None:
        if target_user.is_superuser and not operator.is_superuser:
            raise BusinessError("后台管理员不能操作超级管理员", 11010)

        if target_user.is_staff or target_user.is_superuser:
            has_permission = await self.has_admin_user_permission(operator)

            if not has_permission:
                raise BusinessError(f"权限不足：{self.admin_user_permission}", 11009)

    async def has_admin_user_permission(self, operator) -> bool:
        if operator.is_superuser:
            return True

        return await PermissionService.has_permission(
            user=operator,
            permission_code=self.admin_user_permission,
        )

    @staticmethod
    def _is_truthy(value) -> bool:
        return value in (True, 1, "1", "true", "True")
