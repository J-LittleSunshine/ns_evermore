# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from iam.application.authorization import AuthorizationApplicationService
from iam.services.crud import (
    DepartmentPermissionCrudService,
    RolePermissionCrudService,
    SubsidiaryPermissionCrudService,
    UserPermissionCrudService,
    UserRoleCrudService,
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
    service_class = UserRoleCrudService
    validator_class = UserRoleValidator

    list_fields = detail_fields = ("id", "user_id", "role_id")
    update_fields = ("user_id", "role_id")

    async def bind_user_role(self, request, *args, **kwargs):
        data = self.validator_class.validate_create(request.data)
        result = await AuthorizationApplicationService.bind_user_role(
            data,
            operator_id=self.get_operator_id(request),
        )
        return self.success_response(result)

    async def unbind_user_role(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        role_id = request.data.get("role_id")

        await AuthorizationApplicationService.unbind_user_role(
            user_id=user_id,
            role_id=role_id,
        )

        return self.success_response()


class RolePermissionViewSet(BaseIamViewSet):
    service_class = RolePermissionCrudService
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
        result = await AuthorizationApplicationService.grant_role_permission(
            data,
            operator_id=self.get_operator_id(request),
        )
        return self.success_response(result)

    async def revoke_role_permission(self, request, *args, **kwargs):
        role_id = request.data.get("role_id")
        permission_id = request.data.get("permission_id")

        await AuthorizationApplicationService.revoke_role_permission(
            role_id=role_id,
            permission_id=permission_id,
        )

        return self.success_response()


class UserPermissionViewSet(BaseIamViewSet):
    service_class = UserPermissionCrudService
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
        result = await AuthorizationApplicationService.grant_user_permission(
            data,
            operator_id=self.get_operator_id(request),
        )
        return self.success_response(result)

    async def revoke_user_permission(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        permission_id = request.data.get("permission_id")

        await AuthorizationApplicationService.revoke_user_permission(
            user_id=user_id,
            permission_id=permission_id,
        )

        return self.success_response()


class DepartmentPermissionViewSet(BaseIamViewSet):
    service_class = DepartmentPermissionCrudService
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
        result = await AuthorizationApplicationService.grant_department_permission(
            data,
            operator_id=self.get_operator_id(request),
        )
        return self.success_response(result)

    async def revoke_department_permission(self, request, *args, **kwargs):
        department_id = request.data.get("department_id")
        permission_id = request.data.get("permission_id")

        await AuthorizationApplicationService.revoke_department_permission(
            department_id=department_id,
            permission_id=permission_id,
        )

        return self.success_response()


class SubsidiaryPermissionViewSet(BaseIamViewSet):
    service_class = SubsidiaryPermissionCrudService
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
        result = await AuthorizationApplicationService.grant_subsidiary_permission(
            data,
            operator_id=self.get_operator_id(request),
        )
        return self.success_response(result)

    async def revoke_subsidiary_permission(self, request, *args, **kwargs):
        subsidiary_id = request.data.get("subsidiary_id")
        permission_id = request.data.get("permission_id")

        await AuthorizationApplicationService.revoke_subsidiary_permission(
            subsidiary_id=subsidiary_id,
            permission_id=permission_id,
        )

        return self.success_response()
