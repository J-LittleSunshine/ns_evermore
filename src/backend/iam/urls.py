# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.urls import path

from iam.views.auth import AuthPublicViewSet, AuthPrivateViewSet

if TYPE_CHECKING:
    pass

from iam.views import (
    CompanyViewSet,
    DepartmentViewSet,
    DepartmentPermissionViewSet,
    PermissionViewSet,
    RolePermissionViewSet,
    RoleViewSet,
    SubsidiaryPermissionViewSet,
    SubsidiaryViewSet,
    UserPermissionViewSet,
    UserRoleViewSet,
    UserViewSet,
)

urlpatterns = [
    # company crud api
    path("company/list/", CompanyViewSet.as_view({"post": "list_item"}, required_permissions=("iam:company:list",))),
    path("company/detail/", CompanyViewSet.as_view({"post": "detail_item"}, required_permissions=("iam:company:detail",))),
    path("company/create/", CompanyViewSet.as_view({"post": "create_item"}, required_permissions=("iam:company:create",))),
    path("company/update/", CompanyViewSet.as_view({"post": "update_item"}, required_permissions=("iam:company:update",))),
    path("company/delete/", CompanyViewSet.as_view({"post": "delete_item"}, required_permissions=("iam:company:delete",))),

    # subsidiary crud api
    path("subsidiary/list/", SubsidiaryViewSet.as_view({"post": "list_item"}, required_permissions=("iam:subsidiary:list",))),
    path("subsidiary/detail/", SubsidiaryViewSet.as_view({"post": "detail_item"}, required_permissions=("iam:subsidiary:detail",))),
    path("subsidiary/create/", SubsidiaryViewSet.as_view({"post": "create_item"}, required_permissions=("iam:subsidiary:create",))),
    path("subsidiary/update/", SubsidiaryViewSet.as_view({"post": "update_item"}, required_permissions=("iam:subsidiary:update",))),
    path("subsidiary/delete/", SubsidiaryViewSet.as_view({"post": "delete_item"}, required_permissions=("iam:subsidiary:delete",))),

    # department crud api
    path("department/list/", DepartmentViewSet.as_view({"post": "list_item"}, required_permissions=("iam:department:list",))),
    path("department/detail/", DepartmentViewSet.as_view({"post": "detail_item"}, required_permissions=("iam:department:detail",))),
    path("department/create/", DepartmentViewSet.as_view({"post": "create_item"}, required_permissions=("iam:department:create",))),
    path("department/update/", DepartmentViewSet.as_view({"post": "update_item"}, required_permissions=("iam:department:update",))),
    path("department/delete/", DepartmentViewSet.as_view({"post": "delete_item"}, required_permissions=("iam:department:delete",))),

    # permission crud api
    path("permission/list/", PermissionViewSet.as_view({"post": "list_item"}, required_permissions=("iam:permission:list",))),
    path("permission/detail/", PermissionViewSet.as_view({"post": "detail_item"}, required_permissions=("iam:permission:detail",))),
    path("permission/create/", PermissionViewSet.as_view({"post": "create_item"}, required_permissions=("iam:permission:create",))),
    path("permission/update/", PermissionViewSet.as_view({"post": "update_item"}, required_permissions=("iam:permission:update",))),
    path("permission/delete/", PermissionViewSet.as_view({"post": "delete_item"}, required_permissions=("iam:permission:delete",))),

    # role crud api
    path("role/list/", RoleViewSet.as_view({"post": "list_item"}, required_permissions=("iam:role:list",))),
    path("role/detail/", RoleViewSet.as_view({"post": "detail_item"}, required_permissions=("iam:role:detail",))),
    path("role/create/", RoleViewSet.as_view({"post": "create_item"}, required_permissions=("iam:role:create",))),
    path("role/update/", RoleViewSet.as_view({"post": "update_item"}, required_permissions=("iam:role:update",))),
    path("role/delete/", RoleViewSet.as_view({"post": "delete_item"}, required_permissions=("iam:role:delete",))),

    # user crud api
    path("user/list/", UserViewSet.as_view({"post": "list_item"}, required_permissions=("iam:user:list",))),
    path("user/detail/", UserViewSet.as_view({"post": "detail_item"}, required_permissions=("iam:user:detail",))),
    path("user/create/", UserViewSet.as_view({"post": "create_item"}, required_permissions=("iam:user:create",))),
    path("user/update/", UserViewSet.as_view({"post": "update_item"}, required_permissions=("iam:user:update",))),
    path("user/delete/", UserViewSet.as_view({"post": "delete_item"}, required_permissions=("iam:user:delete",))),
    path("user/reset-password/", UserViewSet.as_view({"post": "reset_password"}, required_permissions=("iam:user:reset_password",))),

    # grant user crud api
    path("grant/bind-user-role", UserRoleViewSet.as_view({"post": "bind_user_role"}, required_permissions=("iam:grant:user_role:bind",))),
    path("grant/unbind-user-role", UserRoleViewSet.as_view({"post": "unbind_user_role"}, required_permissions=("iam:grant:user_role:unbind",))),
    path("grant/grant-role-permission", RolePermissionViewSet.as_view({"post": "grant_role_permission"}, required_permissions=("iam:grant:role_permission:grant",))),
    path("grant/revoke-role-permission", RolePermissionViewSet.as_view({"post": "revoke_role_permission"}, required_permissions=("iam:grant:role_permission:revoke",))),
    path("grant/grant-user-permission", UserPermissionViewSet.as_view({"post": "grant_user_permission"}, required_permissions=("iam:grant:user_permission:grant",))),
    path("grant/revoke-user-permission", UserPermissionViewSet.as_view({"post": "revoke_user_permission"}, required_permissions=("iam:grant:user_permission:revoke",))),
    path("grant/grant-department-permission", DepartmentPermissionViewSet.as_view({"post": "grant_department_permission"}, required_permissions=("iam:grant:department_permission:grant",))),
    path("grant/revoke-department-permission", DepartmentPermissionViewSet.as_view({"post": "revoke_department_permission"}, required_permissions=("iam:grant:department_permission:revoke",))),
    path("grant/grant-subsidiary-permission", SubsidiaryPermissionViewSet.as_view({"post": "grant_subsidiary_permission"}, required_permissions=("iam:grant:subsidiary_permission:grant",))),
    path("grant/revoke-subsidiary-permission", SubsidiaryPermissionViewSet.as_view({"post": "revoke_subsidiary_permission"}, required_permissions=("iam:grant:subsidiary_permission:revoke",))),

    # auth api
    path("auth/login/", AuthPublicViewSet.as_view({"post": "login"})),
    path("auth/refresh-token/", AuthPublicViewSet.as_view({"post": "refresh_token"})),
    path("auth/logout/", AuthPrivateViewSet.as_view({"post": "logout"})),
    path("auth/current-user/", AuthPrivateViewSet.as_view({"post": "current_user"})),
]
