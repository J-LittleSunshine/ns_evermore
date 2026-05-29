# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.urls import path

from ns_backend.iam.views.auth_views import AuthViewSet
from ns_backend.iam.views.base_views import (
    CompanyViewSet,
    SubsidiaryViewSet,
    DepartmentViewSet,
    PermissionViewSet,
    RoleViewSet,
    UserViewSet
)
from ns_backend.iam.views.grant_views import (
    UserRoleGrantViewSet,
    RolePermissionGrantViewSet,
    UserPermissionGrantViewSet,
    DepartmentPermissionGrantViewSet,
    SubsidiaryPermissionGrantViewSet
)
from ns_backend.iam.views.session_views import SessionViewSet

if TYPE_CHECKING:
    pass

urlpatterns = [
    path("company/list", CompanyViewSet.as_view({"post": "list_item"}, required_permissions=("iam:company:list",))),
    path("company/detail", CompanyViewSet.as_view({"post": "detail_item"}, required_permissions=("iam:company:detail",))),
    path("company/create", CompanyViewSet.as_view({"post": "create_item"}, required_permissions=("iam:company:create",))),
    path("company/update", CompanyViewSet.as_view({"post": "update_item"}, required_permissions=("iam:company:update",))),
    path("company/delete", CompanyViewSet.as_view({"post": "delete_item"}, required_permissions=("iam:company:delete",))),

    path("subsidiary/list", SubsidiaryViewSet.as_view({"post": "list_item"}, required_permissions=("iam:subsidiary:list",))),
    path("subsidiary/detail", SubsidiaryViewSet.as_view({"post": "detail_item"}, required_permissions=("iam:subsidiary:detail",))),
    path("subsidiary/create", SubsidiaryViewSet.as_view({"post": "create_item"}, required_permissions=("iam:subsidiary:create",))),
    path("subsidiary/update", SubsidiaryViewSet.as_view({"post": "update_item"}, required_permissions=("iam:subsidiary:update",))),
    path("subsidiary/delete", SubsidiaryViewSet.as_view({"post": "delete_item"}, required_permissions=("iam:subsidiary:delete",))),

    path("department/list", DepartmentViewSet.as_view({"post": "list_item"}, required_permissions=("iam:department:list",))),
    path("department/detail", DepartmentViewSet.as_view({"post": "detail_item"}, required_permissions=("iam:department:detail",))),
    path("department/create", DepartmentViewSet.as_view({"post": "create_item"}, required_permissions=("iam:department:create",))),
    path("department/update", DepartmentViewSet.as_view({"post": "update_item"}, required_permissions=("iam:department:update",))),
    path("department/delete", DepartmentViewSet.as_view({"post": "delete_item"}, required_permissions=("iam:department:delete",))),

    path("permission/list", PermissionViewSet.as_view({"post": "list_item"}, required_permissions=("iam:permission:list",))),
    path("permission/detail", PermissionViewSet.as_view({"post": "detail_item"}, required_permissions=("iam:permission:detail",))),
    path("permission/create", PermissionViewSet.as_view({"post": "create_item"}, required_permissions=("iam:permission:create",))),
    path("permission/update", PermissionViewSet.as_view({"post": "update_item"}, required_permissions=("iam:permission:update",))),
    path("permission/delete", PermissionViewSet.as_view({"post": "delete_item"}, required_permissions=("iam:permission:delete",))),

    path("role/list", RoleViewSet.as_view({"post": "list_item"}, required_permissions=("iam:role:list",))),
    path("role/detail", RoleViewSet.as_view({"post": "detail_item"}, required_permissions=("iam:role:detail",))),
    path("role/create", RoleViewSet.as_view({"post": "create_item"}, required_permissions=("iam:role:create",))),
    path("role/update", RoleViewSet.as_view({"post": "update_item"}, required_permissions=("iam:role:update",))),
    path("role/delete", RoleViewSet.as_view({"post": "delete_item"}, required_permissions=("iam:role:delete",))),

    path("user/list", UserViewSet.as_view({"post": "list_item"}, required_permissions=("iam:user:list",))),
    path("user/detail", UserViewSet.as_view({"post": "detail_item"}, required_permissions=("iam:user:detail",))),
    path("user/create", UserViewSet.as_view({"post": "create_item"}, required_permissions=("iam:user:create",))),
    path("user/update", UserViewSet.as_view({"post": "update_item"}, required_permissions=("iam:user:update",))),
    path("user/delete", UserViewSet.as_view({"post": "delete_item"}, required_permissions=("iam:user:delete",))),
    path("user/reset-password", UserViewSet.as_view({"post": "reset_password"}, required_permissions=("iam:user:reset_password",))),

    path("auth/login", AuthViewSet.as_view({"post": "login"})),
    path("auth/refresh", AuthViewSet.as_view({"post": "refresh"})),
    path("auth/refresh-token", AuthViewSet.as_view({"post": "refresh_token"})),
    path("auth/logout", AuthViewSet.as_view({"post": "logout"})),
    path("auth/profile", AuthViewSet.as_view({"post": "profile"})),
    path("auth/current-user", AuthViewSet.as_view({"post": "current_user"})),
    path("auth/permissions", AuthViewSet.as_view({"post": "permissions"})),
    path("auth/menus", AuthViewSet.as_view({"post": "menus"})),
    path("auth/data-scopes", AuthViewSet.as_view({"post": "data_scopes"})),

    path("grant/user-role/bind", UserRoleGrantViewSet.as_view({"post": "bind_user_role"}, required_permissions=("iam:grant:user_role:bind",))),
    path("grant/user-role/unbind", UserRoleGrantViewSet.as_view({"post": "unbind_user_role"}, required_permissions=("iam:grant:user_role:unbind",))),
    path("grant/role-permission/grant", RolePermissionGrantViewSet.as_view({"post": "grant_role_permission"}, required_permissions=("iam:grant:role_permission:grant",))),
    path("grant/role-permission/revoke", RolePermissionGrantViewSet.as_view({"post": "revoke_role_permission"}, required_permissions=("iam:grant:role_permission:revoke",))),
    path("grant/user-permission/grant", UserPermissionGrantViewSet.as_view({"post": "grant_user_permission"}, required_permissions=("iam:grant:user_permission:grant",))),
    path("grant/user-permission/revoke", UserPermissionGrantViewSet.as_view({"post": "revoke_user_permission"}, required_permissions=("iam:grant:user_permission:revoke",))),
    path("grant/department-permission/grant", DepartmentPermissionGrantViewSet.as_view({"post": "grant_department_permission"}, required_permissions=("iam:grant:department_permission:grant",))),
    path("grant/department-permission/revoke", DepartmentPermissionGrantViewSet.as_view({"post": "revoke_department_permission"}, required_permissions=("iam:grant:department_permission:revoke",))),
    path("grant/subsidiary-permission/grant", SubsidiaryPermissionGrantViewSet.as_view({"post": "grant_subsidiary_permission"}, required_permissions=("iam:grant:subsidiary_permission:grant",))),
    path("grant/subsidiary-permission/revoke", SubsidiaryPermissionGrantViewSet.as_view({"post": "revoke_subsidiary_permission"}, required_permissions=("iam:grant:subsidiary_permission:revoke",))),

    path("session/list", SessionViewSet.as_view({"post": "list_sessions"})),
    path("session/revoke", SessionViewSet.as_view({"post": "revoke_session"})),
]
