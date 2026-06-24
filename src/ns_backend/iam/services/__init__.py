# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.services.auth import AuthService
from ns_backend.iam.services.auth_context import AuthContextService
from ns_backend.iam.services.data_scope import DataScopeService
from ns_backend.iam.services.management import (
    CompanyManagementService,
    DepartmentManagementService,
    DepartmentPermissionManagementService,
    DirectPermissionGrantManagementService,
    IamManagementService,
    PermissionManagementService,
    RoleManagementService,
    RolePermissionManagementService,
    SubsidiaryManagementService,
    SubsidiaryPermissionManagementService,
    UserManagementService,
    UserPermissionManagementService,
    UserRoleManagementService,
)
from ns_backend.iam.services.permission import PermissionService

if TYPE_CHECKING:
    pass

__all__ = [
    "AuthContextService",
    "AuthService",
    "CompanyManagementService",
    "DataScopeService",
    "DepartmentManagementService",
    "DepartmentPermissionManagementService",
    "DirectPermissionGrantManagementService",
    "IamManagementService",
    "PermissionManagementService",
    "PermissionService",
    "RoleManagementService",
    "RolePermissionManagementService",
    "SubsidiaryManagementService",
    "SubsidiaryPermissionManagementService",
    "UserManagementService",
    "UserPermissionManagementService",
    "UserRoleManagementService",
]