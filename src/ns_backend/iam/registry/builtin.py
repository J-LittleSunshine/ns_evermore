# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.constants import (
    PERMISSION_TYPE_ACTION,
    PERMISSION_TYPE_MENU,
)
from ns_backend.iam.registry.module import PermissionModuleRegistry
from ns_backend.iam.schemas import PermissionSpec

if TYPE_CHECKING:
    pass

IAM_BUILTIN_PERMISSION_SPECS: tuple[PermissionSpec, ...] = (
    PermissionSpec(permission_code="iam:auth", permission_name="IAM Auth", permission_type=PERMISSION_TYPE_MENU),
    PermissionSpec(permission_code="iam:auth:profile", permission_name="Get auth profile", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:auth"),
    PermissionSpec(permission_code="iam:auth:current_user", permission_name="Get current user", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:auth"),
    PermissionSpec(permission_code="iam:auth:permissions", permission_name="Get auth permissions", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:auth"),
    PermissionSpec(permission_code="iam:auth:menus", permission_name="Get auth menus", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:auth"),
    PermissionSpec(permission_code="iam:auth:data_scopes", permission_name="Get auth data scopes", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:auth"),
    PermissionSpec(permission_code="iam:auth:logout", permission_name="Logout current user", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:auth"),

    PermissionSpec(permission_code="iam:access", permission_name="IAM Access", permission_type=PERMISSION_TYPE_MENU),
    PermissionSpec(permission_code="iam:access:check", permission_name="Access check", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:access"),
    PermissionSpec(permission_code="iam:access:batch_check", permission_name="Batch access check", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:access"),

    PermissionSpec(permission_code="iam:internal", permission_name="IAM Internal", permission_type=PERMISSION_TYPE_MENU),
    PermissionSpec(permission_code="iam:internal:introspect_token", permission_name="Internal introspect token", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:internal"),
    PermissionSpec(permission_code="iam:internal:access_check", permission_name="Internal access check", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:internal"),
    PermissionSpec(permission_code="iam:internal:batch_access_check", permission_name="Internal batch access check", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:internal"),
    PermissionSpec(permission_code="iam:internal:resolve_resource_filter", permission_name="Internal resolve resource filter", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:internal"),

    PermissionSpec(permission_code="iam:session", permission_name="IAM Session", permission_type=PERMISSION_TYPE_MENU),
    PermissionSpec(permission_code="iam:session:read", permission_name="Read sessions", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:session"),
    PermissionSpec(permission_code="iam:session:revoke", permission_name="Revoke session", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:session"),

    PermissionSpec(permission_code="iam:company", permission_name="IAM Company", permission_type=PERMISSION_TYPE_MENU),
    PermissionSpec(permission_code="iam:company:read", permission_name="Read companies", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:company"),
    PermissionSpec(permission_code="iam:company:create", permission_name="Create company", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:company"),
    PermissionSpec(permission_code="iam:company:update", permission_name="Update company", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:company"),
    PermissionSpec(permission_code="iam:company:delete", permission_name="Delete company", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:company"),

    PermissionSpec(permission_code="iam:subsidiary", permission_name="IAM Subsidiary", permission_type=PERMISSION_TYPE_MENU),
    PermissionSpec(permission_code="iam:subsidiary:read", permission_name="Read subsidiaries", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:subsidiary"),
    PermissionSpec(permission_code="iam:subsidiary:create", permission_name="Create subsidiary", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:subsidiary"),
    PermissionSpec(permission_code="iam:subsidiary:update", permission_name="Update subsidiary", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:subsidiary"),
    PermissionSpec(permission_code="iam:subsidiary:delete", permission_name="Delete subsidiary", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:subsidiary"),

    PermissionSpec(permission_code="iam:department", permission_name="IAM Department", permission_type=PERMISSION_TYPE_MENU),
    PermissionSpec(permission_code="iam:department:read", permission_name="Read departments", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:department"),
    PermissionSpec(permission_code="iam:department:create", permission_name="Create department", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:department"),
    PermissionSpec(permission_code="iam:department:update", permission_name="Update department", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:department"),
    PermissionSpec(permission_code="iam:department:delete", permission_name="Delete department", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:department"),

    PermissionSpec(permission_code="iam:permission", permission_name="IAM Permission", permission_type=PERMISSION_TYPE_MENU),
    PermissionSpec(permission_code="iam:permission:read", permission_name="Read permissions", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:permission"),
    PermissionSpec(permission_code="iam:permission:create", permission_name="Create permission", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:permission"),
    PermissionSpec(permission_code="iam:permission:update", permission_name="Update permission", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:permission"),
    PermissionSpec(permission_code="iam:permission:delete", permission_name="Delete permission", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:permission"),
    PermissionSpec(permission_code="iam:permission:sync", permission_name="Sync permissions", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:permission"),

    PermissionSpec(permission_code="iam:resource", permission_name="IAM Resource", permission_type=PERMISSION_TYPE_MENU),
    PermissionSpec(permission_code="iam:resource:read", permission_name="Read resources", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:resource"),
    PermissionSpec(permission_code="iam:resource:create", permission_name="Create resource", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:resource"),
    PermissionSpec(permission_code="iam:resource:update", permission_name="Update resource", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:resource"),
    PermissionSpec(permission_code="iam:resource:delete", permission_name="Delete resource", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:resource"),
    PermissionSpec(permission_code="iam:resource:sync", permission_name="Sync resources", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:resource"),

    PermissionSpec(permission_code="iam:resource_action", permission_name="IAM Resource Action", permission_type=PERMISSION_TYPE_MENU),
    PermissionSpec(permission_code="iam:resource_action:read", permission_name="Read resource actions", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:resource_action"),
    PermissionSpec(permission_code="iam:resource_action:create", permission_name="Create resource action", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:resource_action"),
    PermissionSpec(permission_code="iam:resource_action:update", permission_name="Update resource action", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:resource_action"),
    PermissionSpec(permission_code="iam:resource_action:delete", permission_name="Delete resource action", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:resource_action"),

    PermissionSpec(permission_code="iam:resource_relation", permission_name="IAM Resource Relation", permission_type=PERMISSION_TYPE_MENU),
    PermissionSpec(permission_code="iam:resource_relation:read", permission_name="Read resource relations", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:resource_relation"),
    PermissionSpec(permission_code="iam:resource_relation:create", permission_name="Create resource relation", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:resource_relation"),
    PermissionSpec(permission_code="iam:resource_relation:delete", permission_name="Delete resource relation", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:resource_relation"),

    PermissionSpec(permission_code="iam:resource_acl", permission_name="IAM Resource ACL", permission_type=PERMISSION_TYPE_MENU),
    PermissionSpec(permission_code="iam:resource_acl:read", permission_name="Read resource ACLs", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:resource_acl"),
    PermissionSpec(permission_code="iam:resource_acl:create", permission_name="Create resource ACL", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:resource_acl"),
    PermissionSpec(permission_code="iam:resource_acl:delete", permission_name="Delete resource ACL", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:resource_acl"),

    PermissionSpec(permission_code="iam:role", permission_name="IAM Role", permission_type=PERMISSION_TYPE_MENU),
    PermissionSpec(permission_code="iam:role:read", permission_name="Read roles", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:role"),
    PermissionSpec(permission_code="iam:role:create", permission_name="Create role", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:role"),
    PermissionSpec(permission_code="iam:role:update", permission_name="Update role", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:role"),
    PermissionSpec(permission_code="iam:role:delete", permission_name="Delete role", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:role"),

    PermissionSpec(permission_code="iam:user", permission_name="IAM User", permission_type=PERMISSION_TYPE_MENU),
    PermissionSpec(permission_code="iam:user:read", permission_name="Read users", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:user"),
    PermissionSpec(permission_code="iam:user:create", permission_name="Create user", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:user"),
    PermissionSpec(permission_code="iam:user:update", permission_name="Update user", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:user"),
    PermissionSpec(permission_code="iam:user:delete", permission_name="Delete user", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:user"),
    PermissionSpec(permission_code="iam:user:reset_password", permission_name="Reset user password", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:user"),

    PermissionSpec(permission_code="iam:grant", permission_name="IAM Grant", permission_type=PERMISSION_TYPE_MENU),
    PermissionSpec(permission_code="iam:user_role:read", permission_name="Read user role grants", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:grant"),
    PermissionSpec(permission_code="iam:user_role:create", permission_name="Create user role grant", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:grant"),
    PermissionSpec(permission_code="iam:user_role:delete", permission_name="Delete user role grant", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:grant"),
    PermissionSpec(permission_code="iam:role_permission:read", permission_name="Read role permission grants", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:grant"),
    PermissionSpec(permission_code="iam:role_permission:create", permission_name="Create role permission grant", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:grant"),
    PermissionSpec(permission_code="iam:role_permission:delete", permission_name="Delete role permission grant", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:grant"),
    PermissionSpec(permission_code="iam:user_permission:read", permission_name="Read user permission grants", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:grant"),
    PermissionSpec(permission_code="iam:user_permission:create", permission_name="Create user permission grant", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:grant"),
    PermissionSpec(permission_code="iam:user_permission:delete", permission_name="Delete user permission grant", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:grant"),
    PermissionSpec(permission_code="iam:department_permission:read", permission_name="Read department permission grants", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:grant"),
    PermissionSpec(permission_code="iam:department_permission:create", permission_name="Create department permission grant", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:grant"),
    PermissionSpec(permission_code="iam:department_permission:delete", permission_name="Delete department permission grant", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:grant"),
    PermissionSpec(permission_code="iam:subsidiary_permission:read", permission_name="Read subsidiary permission grants", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:grant"),
    PermissionSpec(permission_code="iam:subsidiary_permission:create", permission_name="Create subsidiary permission grant", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:grant"),
    PermissionSpec(permission_code="iam:subsidiary_permission:delete", permission_name="Delete subsidiary permission grant", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:grant"),

    PermissionSpec(permission_code="iam:policy", permission_name="IAM Policy", permission_type=PERMISSION_TYPE_MENU),
    PermissionSpec(permission_code="iam:policy:read", permission_name="Read policies", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:policy"),
    PermissionSpec(permission_code="iam:policy:create", permission_name="Create policy", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:policy"),
    PermissionSpec(permission_code="iam:policy:update", permission_name="Update policy", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:policy"),
    PermissionSpec(permission_code="iam:policy:delete", permission_name="Delete policy", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:policy"),
    PermissionSpec(permission_code="iam:policy:publish", permission_name="Publish policy", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:policy"),
    PermissionSpec(permission_code="iam:policy:disable", permission_name="Disable policy", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:policy"),

    PermissionSpec(permission_code="iam:policy_rule", permission_name="IAM Policy Rule", permission_type=PERMISSION_TYPE_MENU),
    PermissionSpec(permission_code="iam:policy_rule:read", permission_name="Read policy rules", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:policy_rule"),
    PermissionSpec(permission_code="iam:policy_rule:create", permission_name="Create policy rule", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:policy_rule"),
    PermissionSpec(permission_code="iam:policy_rule:update", permission_name="Update policy rule", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:policy_rule"),
    PermissionSpec(permission_code="iam:policy_rule:delete", permission_name="Delete policy rule", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:policy_rule"),

    PermissionSpec(permission_code="iam:audit", permission_name="IAM Audit", permission_type=PERMISSION_TYPE_MENU),
    PermissionSpec(permission_code="iam:audit:decision:read", permission_name="Read decision audit logs", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:audit"),
    PermissionSpec(permission_code="iam:audit:operation:read", permission_name="Read operation audit logs", permission_type=PERMISSION_TYPE_ACTION, parent_code="iam:audit"),
)


class IamBuiltinPermissionProvider:
    app_label = "iam"

    def list_permissions(self) -> tuple[PermissionSpec, ...]:
        return IAM_BUILTIN_PERMISSION_SPECS


def register_builtin_permission_providers() -> None:
    if PermissionModuleRegistry.has_provider(IamBuiltinPermissionProvider.app_label):
        return

    PermissionModuleRegistry.register_provider(IamBuiltinPermissionProvider())
