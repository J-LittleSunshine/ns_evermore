# -*- coding: utf-8 -*-
from __future__ import annotations

from django.urls import path

from ns_backend.iam.views import (
    AccessViewSet,
    AuthViewSet,
    CompanyViewSet,
    DecisionAuditViewSet,
    DepartmentPermissionViewSet,
    DepartmentViewSet,
    InternalIamViewSet,
    OperationAuditViewSet,
    PermissionSyncViewSet,
    PermissionViewSet,
    PolicyRuleViewSet,
    PolicyViewSet,
    ResourceAclViewSet,
    ResourceActionViewSet,
    ResourceRelationViewSet,
    ResourceSyncViewSet,
    ResourceViewSet,
    RolePermissionViewSet,
    RoleViewSet,
    SessionViewSet,
    SubsidiaryPermissionViewSet,
    SubsidiaryViewSet,
    UserPermissionViewSet,
    UserRoleViewSet,
    UserViewSet
)

urlpatterns = [
    path("auth/login/", AuthViewSet.as_view({"post": "login"})),
    path("auth/refresh/", AuthViewSet.as_view({"post": "refresh"})),
    path("auth/logout/", AuthViewSet.as_view({"post": "logout"})),
    path("auth/profile/", AuthViewSet.as_view({"post": "profile"})),
    path("auth/current_user/", AuthViewSet.as_view({"post": "current_user"})),
    path("auth/permissions/", AuthViewSet.as_view({"post": "permissions"})),
    path("auth/menus/", AuthViewSet.as_view({"post": "menus"})),
    path("auth/data_scopes/", AuthViewSet.as_view({"post": "data_scopes"})),

    path("session/list/", SessionViewSet.as_view({"post": "list"})),
    path("session/revoke/", SessionViewSet.as_view({"post": "revoke"})),

    path("access/check/", AccessViewSet.as_view({"post": "check"})),
    path("access/batch_check/", AccessViewSet.as_view({"post": "batch_check"})),

    path("audit/decision/list/", DecisionAuditViewSet.as_view({"post": "list"})),
    path("audit/operation/list/", OperationAuditViewSet.as_view({"post": "list"})),

    path("company/list/", CompanyViewSet.as_view({"post": "list"})),
    path("company/detail/", CompanyViewSet.as_view({"post": "get_detail"})),
    path("company/create/", CompanyViewSet.as_view({"post": "create"})),
    path("company/update/", CompanyViewSet.as_view({"post": "update"})),
    path("company/delete/", CompanyViewSet.as_view({"post": "delete"})),
    path("company/tree/", CompanyViewSet.as_view({"post": "tree"})),
    path("company/org_tree/", CompanyViewSet.as_view({"post": "org_tree"})),

    path("subsidiary/list/", SubsidiaryViewSet.as_view({"post": "list"})),
    path("subsidiary/detail/", SubsidiaryViewSet.as_view({"post": "get_detail"})),
    path("subsidiary/create/", SubsidiaryViewSet.as_view({"post": "create"})),
    path("subsidiary/update/", SubsidiaryViewSet.as_view({"post": "update"})),
    path("subsidiary/delete/", SubsidiaryViewSet.as_view({"post": "delete"})),
    path("subsidiary/tree/", SubsidiaryViewSet.as_view({"post": "tree"})),

    path("department/list/", DepartmentViewSet.as_view({"post": "list"})),
    path("department/detail/", DepartmentViewSet.as_view({"post": "get_detail"})),
    path("department/create/", DepartmentViewSet.as_view({"post": "create"})),
    path("department/update/", DepartmentViewSet.as_view({"post": "update"})),
    path("department/delete/", DepartmentViewSet.as_view({"post": "delete"})),
    path("department/tree/", DepartmentViewSet.as_view({"post": "tree"})),

    path("permission/list/", PermissionViewSet.as_view({"post": "list"})),
    path("permission/detail/", PermissionViewSet.as_view({"post": "get_detail"})),
    path("permission/create/", PermissionViewSet.as_view({"post": "create"})),
    path("permission/update/", PermissionViewSet.as_view({"post": "update"})),
    path("permission/delete/", PermissionViewSet.as_view({"post": "delete"})),
    path("permission/tree/", PermissionViewSet.as_view({"post": "tree"})),
    path("permission/menu_tree/", PermissionViewSet.as_view({"post": "menu_tree"})),
    path("permission/action_list/", PermissionViewSet.as_view({"post": "action_list"})),
    path("permission/data_list/", PermissionViewSet.as_view({"post": "data_list"})),

    path("policy/list/", PolicyViewSet.as_view({"post": "list"})),
    path("policy/detail/", PolicyViewSet.as_view({"post": "get_detail"})),
    path("policy/create/", PolicyViewSet.as_view({"post": "create"})),
    path("policy/update/", PolicyViewSet.as_view({"post": "update"})),
    path("policy/delete/", PolicyViewSet.as_view({"post": "delete"})),
    path("policy/publish/", PolicyViewSet.as_view({"post": "publish"})),
    path("policy/disable/", PolicyViewSet.as_view({"post": "disable"})),

    path("policy_rule/list/", PolicyRuleViewSet.as_view({"post": "list"})),
    path("policy_rule/detail/", PolicyRuleViewSet.as_view({"post": "get_detail"})),
    path("policy_rule/create/", PolicyRuleViewSet.as_view({"post": "create"})),
    path("policy_rule/update/", PolicyRuleViewSet.as_view({"post": "update"})),
    path("policy_rule/delete/", PolicyRuleViewSet.as_view({"post": "delete"})),

    path("internal/introspect_token/", InternalIamViewSet.as_view({"post": "introspect_token"})),
    path("internal/access_check/", InternalIamViewSet.as_view({"post": "access_check"})),
    path("internal/batch_access_check/", InternalIamViewSet.as_view({"post": "batch_access_check"})),

    path("resource/list/", ResourceViewSet.as_view({"post": "list"})),
    path("resource/detail/", ResourceViewSet.as_view({"post": "get_detail"})),
    path("resource/create/", ResourceViewSet.as_view({"post": "create"})),
    path("resource/update/", ResourceViewSet.as_view({"post": "update"})),
    path("resource/delete/", ResourceViewSet.as_view({"post": "delete"})),

    path("resource_action/list/", ResourceActionViewSet.as_view({"post": "list"})),
    path("resource_action/detail/", ResourceActionViewSet.as_view({"post": "get_detail"})),
    path("resource_action/create/", ResourceActionViewSet.as_view({"post": "create"})),
    path("resource_action/update/", ResourceActionViewSet.as_view({"post": "update"})),
    path("resource_action/delete/", ResourceActionViewSet.as_view({"post": "delete"})),

    path("resource_acl/list/", ResourceAclViewSet.as_view({"post": "list"})),
    path("resource_acl/create/", ResourceAclViewSet.as_view({"post": "create"})),
    path("resource_acl/delete/", ResourceAclViewSet.as_view({"post": "delete"})),

    path("resource_relation/list/", ResourceRelationViewSet.as_view({"post": "list"})),
    path("resource_relation/create/", ResourceRelationViewSet.as_view({"post": "create"})),
    path("resource_relation/delete/", ResourceRelationViewSet.as_view({"post": "delete"})),

    path("role/list/", RoleViewSet.as_view({"post": "list"})),
    path("role/detail/", RoleViewSet.as_view({"post": "get_detail"})),
    path("role/create/", RoleViewSet.as_view({"post": "create"})),
    path("role/update/", RoleViewSet.as_view({"post": "update"})),
    path("role/delete/", RoleViewSet.as_view({"post": "delete"})),

    path("user/list/", UserViewSet.as_view({"post": "list"})),
    path("user/detail/", UserViewSet.as_view({"post": "get_detail"})),
    path("user/create/", UserViewSet.as_view({"post": "create"})),
    path("user/update/", UserViewSet.as_view({"post": "update"})),
    path("user/delete/", UserViewSet.as_view({"post": "delete"})),
    path("user/reset_password/", UserViewSet.as_view({"post": "reset_password"})),

    path("user_role/list/", UserRoleViewSet.as_view({"post": "list"})),
    path("user_role/create/", UserRoleViewSet.as_view({"post": "create"})),
    path("user_role/delete/", UserRoleViewSet.as_view({"post": "delete"})),

    path("role_permission/list/", RolePermissionViewSet.as_view({"post": "list"})),
    path("role_permission/create/", RolePermissionViewSet.as_view({"post": "create"})),
    path("role_permission/delete/", RolePermissionViewSet.as_view({"post": "delete"})),

    path("user_permission/list/", UserPermissionViewSet.as_view({"post": "list"})),
    path("user_permission/create/", UserPermissionViewSet.as_view({"post": "create"})),
    path("user_permission/delete/", UserPermissionViewSet.as_view({"post": "delete"})),

    path("department_permission/list/", DepartmentPermissionViewSet.as_view({"post": "list"})),
    path("department_permission/create/", DepartmentPermissionViewSet.as_view({"post": "create"})),
    path("department_permission/delete/", DepartmentPermissionViewSet.as_view({"post": "delete"})),

    path("subsidiary_permission/list/", SubsidiaryPermissionViewSet.as_view({"post": "list"})),
    path("subsidiary_permission/create/", SubsidiaryPermissionViewSet.as_view({"post": "create"})),
    path("subsidiary_permission/delete/", SubsidiaryPermissionViewSet.as_view({"post": "delete"})),

    path("permission/sync/", PermissionSyncViewSet.as_view({"post": "sync"})),
    path("permission/batch_sync/", PermissionSyncViewSet.as_view({"post": "batch_sync"})),

    path("resource/sync/", ResourceSyncViewSet.as_view({"post": "sync"})),
    path("resource/batch_sync/", ResourceSyncViewSet.as_view({"post": "batch_sync"})),
]
