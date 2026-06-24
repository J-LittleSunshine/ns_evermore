# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    ClassVar,
    TYPE_CHECKING,
)

from backend.common import NsViewSet
from ns_backend.iam.errors import IamManagementRequestInvalidError
from ns_backend.iam.services import (
    AuthService,
    CompanyManagementService,
    DepartmentManagementService,
    IamManagementService,
    PermissionManagementService,
    RoleManagementService,
    RolePermissionManagementService,
    SubsidiaryManagementService,
    UserManagementService,
    UserRoleManagementService,
)

if TYPE_CHECKING:
    from rest_framework.request import Request


class IamManagementViewSet(NsViewSet):
    logger_name = "ns_backend.iam.management.api"
    service_class: ClassVar[type[IamManagementService] | None] = None

    allowed_actions = {
        "list",
        "detail",
        "create",
        "update",
        "delete",
    }

    required_permissions: ClassVar[dict[str, tuple[str, ...]]] = {}

    async def list(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        operator = await self.get_operator(request)

        return await self.get_service_class().list_items(
            data=self.get_request_data(request),
            operator=operator,
        )

    async def detail(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        operator = await self.get_operator(request)

        return await self.get_service_class().detail_item(
            data=self.get_request_data(request),
            operator=operator,
        )

    async def create(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        operator = await self.get_operator(request)

        return await self.get_service_class().create_item(
            data=self.get_request_data(request),
            operator=operator,
        )

    async def update(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        operator = await self.get_operator(request)

        return await self.get_service_class().update_item(
            data=self.get_request_data(request),
            operator=operator,
        )

    async def delete(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        operator = await self.get_operator(request)

        return await self.get_service_class().delete_item(
            data=self.get_request_data(request),
            operator=operator,
        )

    async def get_operator(self, request: "Request") -> Any:
        user, _ = await AuthService.resolve_user_from_request(request)
        self.set_current_user(user)

        return user

    @classmethod
    def get_service_class(cls) -> type[IamManagementService]:
        if cls.service_class is None:
            raise IamManagementRequestInvalidError(
                "service_class is not configured.",
                details={
                    "view_set": cls.__name__,
                },
            )

        return cls.service_class


class CompanyViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.company.api"
    service_class = CompanyManagementService

    required_permissions = {
        "list": ("iam:company:read",),
        "detail": ("iam:company:read",),
        "create": ("iam:company:create",),
        "update": ("iam:company:update",),
        "delete": ("iam:company:delete",),
    }


class SubsidiaryViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.subsidiary.api"
    service_class = SubsidiaryManagementService

    required_permissions = {
        "list": ("iam:subsidiary:read",),
        "detail": ("iam:subsidiary:read",),
        "create": ("iam:subsidiary:create",),
        "update": ("iam:subsidiary:update",),
        "delete": ("iam:subsidiary:delete",),
    }


class DepartmentViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.department.api"
    service_class = DepartmentManagementService

    required_permissions = {
        "list": ("iam:department:read",),
        "detail": ("iam:department:read",),
        "create": ("iam:department:create",),
        "update": ("iam:department:update",),
        "delete": ("iam:department:delete",),
    }


class PermissionViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.permission.api"
    service_class = PermissionManagementService

    required_permissions = {
        "list": ("iam:permission:read",),
        "detail": ("iam:permission:read",),
        "create": ("iam:permission:create",),
        "update": ("iam:permission:update",),
        "delete": ("iam:permission:delete",),
    }


class RoleViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.role.api"
    service_class = RoleManagementService

    required_permissions = {
        "list": ("iam:role:read",),
        "detail": ("iam:role:read",),
        "create": ("iam:role:create",),
        "update": ("iam:role:update",),
        "delete": ("iam:role:delete",),
    }


class UserViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.user.api"
    service_class = UserManagementService

    allowed_actions = IamManagementViewSet.allowed_actions | {
        "reset_password",
    }

    required_permissions = {
        "list": ("iam:user:read",),
        "detail": ("iam:user:read",),
        "create": ("iam:user:create",),
        "update": ("iam:user:update",),
        "delete": ("iam:user:delete",),
        "reset_password": ("iam:user:reset_password",),
    }

    async def reset_password(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        operator = await self.get_operator(request)

        return await self.get_service_class().reset_password(
            data=self.get_request_data(request),
            operator=operator,
        )


class UserRoleViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.user_role.api"
    service_class = UserRoleManagementService

    allowed_actions = {
        "list",
        "create",
        "delete",
    }

    required_permissions = {
        "list": ("iam:user_role:read",),
        "create": ("iam:user_role:create",),
        "delete": ("iam:user_role:delete",),
    }


class RolePermissionViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.role_permission.api"
    service_class = RolePermissionManagementService

    allowed_actions = {
        "list",
        "create",
        "delete",
    }

    required_permissions = {
        "list": ("iam:role_permission:read",),
        "create": ("iam:role_permission:create",),
        "delete": ("iam:role_permission:delete",),
    }
