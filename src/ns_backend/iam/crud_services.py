# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from .models import (
    IamCompany,
    IamDepartment,
    IamDepartmentPermission,
    IamPermission,
    IamRole,
    IamRolePermission,
    IamSubsidiary,
    IamSubsidiaryPermission,
    IamUser,
    IamUserPermission,
    IamUserRole,
)
from .services import IamCrudService
from .validators import (
    CompanyValidator,
    DepartmentPermissionValidator,
    DepartmentValidator,
    PermissionValidator,
    RolePermissionValidator,
    RoleValidator,
    SubsidiaryPermissionValidator,
    SubsidiaryValidator,
    UserPermissionValidator,
    UserRoleValidator,
    UserValidator,
)

if TYPE_CHECKING:
    pass


class CompanyCrudService(IamCrudService):
    model_class = IamCompany
    validator_class = CompanyValidator
    tenant_scope_field = "id"
    tenant_create_field = None
    enterprise_resource_required = True

    list_fields = detail_fields = ("id", "company_code", "company_name", "legal_name", "status")
    update_fields = ("company_name", "legal_name", "status")


class SubsidiaryCrudService(IamCrudService):
    model_class = IamSubsidiary
    validator_class = SubsidiaryValidator
    tenant_scope_field = "company_id"
    tenant_create_field = "company_id"
    enterprise_resource_required = True

    list_fields = detail_fields = ("id", "company_id", "subsidiary_code", "subsidiary_name", "status")
    update_fields = ("subsidiary_name", "status")


class DepartmentCrudService(IamCrudService):
    model_class = IamDepartment
    validator_class = DepartmentValidator
    tenant_scope_field = "company_id"
    tenant_create_field = "company_id"
    enterprise_resource_required = True

    list_fields = detail_fields = (
        "id",
        "company_id",
        "subsidiary_id",
        "parent_id",
        "department_code",
        "department_name",
        "status",
    )
    update_fields = ("department_name", "status")


class PermissionCrudService(IamCrudService):
    model_class = IamPermission
    validator_class = PermissionValidator
    list_fields = detail_fields = (
        "id",
        "permission_code",
        "permission_name",
        "permission_type",
        "parent_id",
        "status",
    )
    update_fields = ("permission_name", "permission_type", "parent_id", "status")


class RoleCrudService(IamCrudService):
    model_class = IamRole
    validator_class = RoleValidator
    tenant_scope_field = "company_id"
    tenant_create_field = "company_id"
    enterprise_resource_required = False

    list_fields = detail_fields = ("id", "company_id", "role_code", "role_name", "role_scope", "status")
    update_fields = ("role_name", "status")


class UserCrudService(IamCrudService):
    model_class = IamUser
    validator_class = UserValidator
    tenant_scope_field = "company_id"
    tenant_create_field = "company_id"
    enterprise_resource_required = False

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
        "last_login",
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


class UserRoleCrudService(IamCrudService):
    model_class = IamUserRole
    validator_class = UserRoleValidator
    list_fields = detail_fields = ("id", "user_id", "role_id")
    update_fields = ("user_id", "role_id")


class RolePermissionCrudService(IamCrudService):
    model_class = IamRolePermission
    validator_class = RolePermissionValidator
    list_fields = detail_fields = (
        "id",
        "role_id",
        "permission_id",
        "data_scope",
        "granted_by_id",
        "expired_at",
    )
    update_fields = (
        "role_id",
        "permission_id",
        "data_scope",
        "granted_by_id",
        "expired_at",
    )


class UserPermissionCrudService(IamCrudService):
    model_class = IamUserPermission
    validator_class = UserPermissionValidator
    list_fields = detail_fields = (
        "id",
        "user_id",
        "permission_id",
        "effect",
        "data_scope",
        "granted_by_id",
        "expired_at",
    )
    update_fields = (
        "user_id",
        "permission_id",
        "effect",
        "data_scope",
        "granted_by_id",
        "expired_at",
    )


class DepartmentPermissionCrudService(IamCrudService):
    model_class = IamDepartmentPermission
    validator_class = DepartmentPermissionValidator
    list_fields = detail_fields = (
        "id",
        "department_id",
        "permission_id",
        "effect",
        "data_scope",
        "granted_by_id",
        "expired_at",
    )
    update_fields = (
        "department_id",
        "permission_id",
        "effect",
        "data_scope",
        "granted_by_id",
        "expired_at",
    )


class SubsidiaryPermissionCrudService(IamCrudService):
    model_class = IamSubsidiaryPermission
    validator_class = SubsidiaryPermissionValidator
    list_fields = detail_fields = (
        "id",
        "subsidiary_id",
        "permission_id",
        "effect",
        "data_scope",
        "granted_by_id",
        "expired_at",
    )
    update_fields = (
        "subsidiary_id",
        "permission_id",
        "effect",
        "data_scope",
        "granted_by_id",
        "expired_at",
    )


__all__ = [
    "CompanyCrudService",
    "SubsidiaryCrudService",
    "DepartmentCrudService",
    "PermissionCrudService",
    "RoleCrudService",
    "UserCrudService",
    "UserRoleCrudService",
    "RolePermissionCrudService",
    "UserPermissionCrudService",
    "DepartmentPermissionCrudService",
    "SubsidiaryPermissionCrudService",
]
