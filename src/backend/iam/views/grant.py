# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from iam.services.grant import GrantService
from iam.models import (
    IamDepartmentPermission,
    IamRolePermission,
    IamSubsidiaryPermission,
    IamUserPermission,
    IamUserRole,
)
from iam.validators import (
    DepartmentPermissionValidator,
    RolePermissionValidator,
    SubsidiaryPermissionValidator,
    UserPermissionValidator,
    UserRoleValidator,
)
from iam.views.base import BaseIamViewSet

if TYPE_CHECKING:
    pass


class UserRoleViewSet(BaseIamViewSet):
    audit_resource_type = "iam_user_role"
    model_class = IamUserRole
    validator_class = UserRoleValidator

    list_fields = detail_fields = ("id", "user_id", "role_id")
    update_fields = ("user_id", "role_id")

    async def bind_user_role(self, request, *args, **kwargs):
        data = self.validator_class.validate_create(request.data)
        operator_id = self.get_operator_id(request)
        result = await GrantService.bind_user_role(
            data=data,
            operator=request.current_user,
            operator_id=operator_id,
        )
        return self.success_response(result)

    async def unbind_user_role(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        role_id = request.data.get("role_id")

        await GrantService.unbind_user_role(
            user_id=user_id,
            role_id=role_id,
            operator=request.current_user,
        )

        return self.success_response()


class RolePermissionViewSet(BaseIamViewSet):
    audit_resource_type = "iam_role_permission"
    model_class = IamRolePermission
    validator_class = RolePermissionValidator

    list_fields = detail_fields = (
        "id",
        "role_id",
        "permission_id",
        "granted_by_id",
        "expired_at",
    )
    update_fields = (
        "role_id",
        "permission_id",
        "granted_by_id",
        "expired_at",
    )

    async def grant_role_permission(self, request, *args, **kwargs):
        data = self.validator_class.validate_create(request.data)
        operator_id = self.get_operator_id(request)
        result = await GrantService.grant_role_permission(
            data=data,
            operator=request.current_user,
            operator_id=operator_id,
        )
        return self.success_response(result)

    async def revoke_role_permission(self, request, *args, **kwargs):
        role_id = request.data.get("role_id")
        permission_id = request.data.get("permission_id")

        await GrantService.revoke_role_permission(
            role_id=role_id,
            permission_id=permission_id,
            operator=request.current_user,
        )

        return self.success_response()


class UserPermissionViewSet(BaseIamViewSet):
    audit_resource_type = "iam_user_permission"
    model_class = IamUserPermission
    validator_class = UserPermissionValidator

    list_fields = detail_fields = (
        "id",
        "user_id",
        "permission_id",
        "effect",
        "granted_by_id",
        "expired_at",
    )
    update_fields = (
        "user_id",
        "permission_id",
        "effect",
        "granted_by_id",
        "expired_at",
    )

    async def grant_user_permission(self, request, *args, **kwargs):
        data = self.validator_class.validate_create(request.data)
        operator_id = self.get_operator_id(request)
        result = await GrantService.grant_user_permission(
            data=data,
            operator=request.current_user,
            operator_id=operator_id,
        )
        return self.success_response(result)

    async def revoke_user_permission(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        permission_id = request.data.get("permission_id")

        await GrantService.revoke_user_permission(
            user_id=user_id,
            permission_id=permission_id,
            operator=request.current_user,
        )

        return self.success_response()


class DepartmentPermissionViewSet(BaseIamViewSet):
    audit_resource_type = "iam_department_permission"
    model_class = IamDepartmentPermission
    validator_class = DepartmentPermissionValidator

    list_fields = detail_fields = (
        "id",
        "department_id",
        "permission_id",
        "effect",
        "granted_by_id",
        "expired_at",
    )
    update_fields = (
        "department_id",
        "permission_id",
        "effect",
        "granted_by_id",
        "expired_at",
    )

    async def grant_department_permission(self, request, *args, **kwargs):
        data = self.validator_class.validate_create(request.data)
        operator_id = self.get_operator_id(request)
        result = await GrantService.grant_department_permission(
            data=data,
            operator=request.current_user,
            operator_id=operator_id,
        )
        return self.success_response(result)

    async def revoke_department_permission(self, request, *args, **kwargs):
        department_id = request.data.get("department_id")
        permission_id = request.data.get("permission_id")

        await GrantService.revoke_department_permission(
            department_id=department_id,
            permission_id=permission_id,
            operator=request.current_user,
        )

        return self.success_response()


class SubsidiaryPermissionViewSet(BaseIamViewSet):
    audit_resource_type = "iam_subsidiary_permission"
    model_class = IamSubsidiaryPermission
    validator_class = SubsidiaryPermissionValidator

    list_fields = detail_fields = (
        "id",
        "subsidiary_id",
        "permission_id",
        "effect",
        "granted_by_id",
        "expired_at",
    )
    update_fields = (
        "subsidiary_id",
        "permission_id",
        "effect",
        "granted_by_id",
        "expired_at",
    )

    async def grant_subsidiary_permission(self, request, *args, **kwargs):
        data = self.validator_class.validate_create(request.data)
        operator_id = self.get_operator_id(request)
        result = await GrantService.grant_subsidiary_permission(
            data=data,
            operator=request.current_user,
            operator_id=operator_id,
        )
        return self.success_response(result)

    async def revoke_subsidiary_permission(self, request, *args, **kwargs):
        subsidiary_id = request.data.get("subsidiary_id")
        permission_id = request.data.get("permission_id")

        await GrantService.revoke_subsidiary_permission(
            subsidiary_id=subsidiary_id,
            permission_id=permission_id,
            operator=request.current_user,
        )

        return self.success_response()
