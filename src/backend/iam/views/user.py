# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.policies.user import UserPolicy
from iam.services.user import UserService
from iam.validators import UserValidator
from iam.views.base import BaseIamViewSet


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

    async def list_item(self, request, *args, **kwargs):
        page = request.data.get("page", 1)
        page_size = request.data.get("page_size", 20)
        include_staff = await UserPolicy.has_admin_user_permission(request.current_user)
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

        await UserPolicy.ensure_can_operate_user(
            operator=request.current_user,
            target_user=user,
        )

        return self.success_response(UserService.serialize(user, self.detail_fields))

    async def create_item(self, request, *args, **kwargs):
        data = self.validate_create_data(request.data)
        operator_id = self.get_operator_id(request)

        await UserPolicy.ensure_can_update_critical_fields(
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

        await UserPolicy.ensure_can_operate_user(
            operator=request.current_user,
            target_user=user,
        )

        await UserPolicy.ensure_can_update_critical_fields(
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

        await UserPolicy.ensure_can_operate_user(
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

        await UserPolicy.ensure_can_operate_user(
            operator=request.current_user,
            target_user=user,
        )

        await UserService.reset_password(
            user_id=user_id,
            raw_password=raw_password,
            operator_id=operator_id,
        )

        return self.success_response()
