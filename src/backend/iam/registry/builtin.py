# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.registry.module import PermissionModuleRegistry
from iam.registry.permission import PermissionRegistry
from iam.schemas import PermissionSpec

IAM_BUILTIN_PERMISSIONS: tuple[PermissionSpec, ...] = (
    PermissionSpec(code="iam:company", name="IAM Company", permission_type="MENU"),
    PermissionSpec(code="iam:company:list", name="List companies", permission_type="ACTION", parent_code="iam:company"),
    PermissionSpec(code="iam:company:detail", name="Company detail", permission_type="ACTION", parent_code="iam:company"),
    PermissionSpec(code="iam:company:create", name="Create company", permission_type="ACTION", parent_code="iam:company"),
    PermissionSpec(code="iam:company:update", name="Update company", permission_type="ACTION", parent_code="iam:company"),
    PermissionSpec(code="iam:company:delete", name="Delete company", permission_type="ACTION", parent_code="iam:company"),
    PermissionSpec(code="iam:subsidiary", name="IAM Subsidiary", permission_type="MENU"),
    PermissionSpec(code="iam:subsidiary:list", name="List subsidiaries", permission_type="ACTION", parent_code="iam:subsidiary"),
    PermissionSpec(code="iam:subsidiary:detail", name="Subsidiary detail", permission_type="ACTION", parent_code="iam:subsidiary"),
    PermissionSpec(code="iam:subsidiary:create", name="Create subsidiary", permission_type="ACTION", parent_code="iam:subsidiary"),
    PermissionSpec(code="iam:subsidiary:update", name="Update subsidiary", permission_type="ACTION", parent_code="iam:subsidiary"),
    PermissionSpec(code="iam:subsidiary:delete", name="Delete subsidiary", permission_type="ACTION", parent_code="iam:subsidiary"),
    PermissionSpec(code="iam:department", name="IAM Department", permission_type="MENU"),
    PermissionSpec(code="iam:department:list", name="List departments", permission_type="ACTION", parent_code="iam:department"),
    PermissionSpec(code="iam:department:detail", name="Department detail", permission_type="ACTION", parent_code="iam:department"),
    PermissionSpec(code="iam:department:create", name="Create department", permission_type="ACTION", parent_code="iam:department"),
    PermissionSpec(code="iam:department:update", name="Update department", permission_type="ACTION", parent_code="iam:department"),
    PermissionSpec(code="iam:department:delete", name="Delete department", permission_type="ACTION", parent_code="iam:department"),
    PermissionSpec(code="iam:permission", name="IAM Permission", permission_type="MENU"),
    PermissionSpec(code="iam:permission:list", name="List permissions", permission_type="ACTION", parent_code="iam:permission"),
    PermissionSpec(code="iam:permission:detail", name="Permission detail", permission_type="ACTION", parent_code="iam:permission"),
    PermissionSpec(code="iam:permission:create", name="Create permission", permission_type="ACTION", parent_code="iam:permission"),
    PermissionSpec(code="iam:permission:update", name="Update permission", permission_type="ACTION", parent_code="iam:permission"),
    PermissionSpec(code="iam:permission:delete", name="Delete permission", permission_type="ACTION", parent_code="iam:permission"),
    PermissionSpec(code="iam:role", name="IAM Role", permission_type="MENU"),
    PermissionSpec(code="iam:role:list", name="List roles", permission_type="ACTION", parent_code="iam:role"),
    PermissionSpec(code="iam:role:detail", name="Role detail", permission_type="ACTION", parent_code="iam:role"),
    PermissionSpec(code="iam:role:create", name="Create role", permission_type="ACTION", parent_code="iam:role"),
    PermissionSpec(code="iam:role:update", name="Update role", permission_type="ACTION", parent_code="iam:role"),
    PermissionSpec(code="iam:role:delete", name="Delete role", permission_type="ACTION", parent_code="iam:role"),
    PermissionSpec(code="iam:user", name="IAM User", permission_type="MENU"),
    PermissionSpec(code="iam:user:list", name="List users", permission_type="ACTION", parent_code="iam:user"),
    PermissionSpec(code="iam:user:detail", name="User detail", permission_type="ACTION", parent_code="iam:user"),
    PermissionSpec(code="iam:user:create", name="Create user", permission_type="ACTION", parent_code="iam:user"),
    PermissionSpec(code="iam:user:update", name="Update user", permission_type="ACTION", parent_code="iam:user"),
    PermissionSpec(code="iam:user:delete", name="Delete user", permission_type="ACTION", parent_code="iam:user"),
    PermissionSpec(code="iam:user:reset_password", name="Reset user password", permission_type="ACTION", parent_code="iam:user"),
    PermissionSpec(code="iam:grant", name="IAM Grant", permission_type="MENU"),
    PermissionSpec(code="iam:grant:user_role:bind", name="Bind user role", permission_type="ACTION", parent_code="iam:grant"),
    PermissionSpec(code="iam:grant:user_role:unbind", name="Unbind user role", permission_type="ACTION", parent_code="iam:grant"),
    PermissionSpec(code="iam:grant:role_permission:grant", name="Grant role permission", permission_type="ACTION", parent_code="iam:grant"),
    PermissionSpec(code="iam:grant:role_permission:revoke", name="Revoke role permission", permission_type="ACTION", parent_code="iam:grant"),
    PermissionSpec(code="iam:grant:user_permission:grant", name="Grant user permission", permission_type="ACTION", parent_code="iam:grant"),
    PermissionSpec(code="iam:grant:user_permission:revoke", name="Revoke user permission", permission_type="ACTION", parent_code="iam:grant"),
    PermissionSpec(code="iam:grant:department_permission:grant", name="Grant department permission", permission_type="ACTION", parent_code="iam:grant"),
    PermissionSpec(code="iam:grant:department_permission:revoke", name="Revoke department permission", permission_type="ACTION", parent_code="iam:grant"),
    PermissionSpec(code="iam:grant:subsidiary_permission:grant", name="Grant subsidiary permission", permission_type="ACTION", parent_code="iam:grant"),
    PermissionSpec(code="iam:grant:subsidiary_permission:revoke", name="Revoke subsidiary permission", permission_type="ACTION", parent_code="iam:grant"),
    PermissionSpec(code="iam:auth", name="IAM Auth", permission_type="MENU"),
    PermissionSpec(code="iam:auth:current_user", name="Get current user", permission_type="ACTION", parent_code="iam:auth"),
    PermissionSpec(code="iam:auth:profile", name="Get auth profile", permission_type="ACTION", parent_code="iam:auth"),
    PermissionSpec(code="iam:auth:permissions", name="Get auth permissions", permission_type="ACTION", parent_code="iam:auth"),
    PermissionSpec(code="iam:auth:menus", name="Get auth menus", permission_type="ACTION", parent_code="iam:auth"),
)


def register_builtin_permissions() -> None:
    PermissionRegistry.register_many(IAM_BUILTIN_PERMISSIONS)


class IamPermissionProvider:
    app_label = "iam"

    def list_permissions(self) -> tuple[PermissionSpec, ...]:
        return IAM_BUILTIN_PERMISSIONS


def register_builtin_permission_providers() -> None:
    PermissionModuleRegistry.register_provider(IamPermissionProvider())


__all__ = [
    "IAM_BUILTIN_PERMISSIONS",
    "IamPermissionProvider",
    "register_builtin_permissions",
    "register_builtin_permission_providers",
]

