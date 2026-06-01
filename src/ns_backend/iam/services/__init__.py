# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.services.auth import AuthLoginResult, AuthService
from ns_backend.iam.services.legacy import (
    AuditService,
    AuthContextService,
    CompanyCrudService,
    DataScopeService,
    DepartmentCrudService,
    DepartmentPermissionCrudService,
    IamCrudService,
    PermissionCrudService,
    PermissionService,
    PermissionSyncService,
    RoleCrudService,
    RolePermissionCrudService,
    SubsidiaryCrudService,
    SubsidiaryPermissionCrudService,
    TenantService,
    UserCrudService,
    UserPermissionCrudService,
    UserRoleCrudService,
)
from ns_backend.iam.services.verify import VerifyService

if TYPE_CHECKING:
    pass

__all__ = [
    "AuditService",
    "AuthContextService",
    "AuthLoginResult",
    "AuthService",
    "CompanyCrudService",
    "DataScopeService",
    "DepartmentCrudService",
    "DepartmentPermissionCrudService",
    "IamCrudService",
    "PermissionCrudService",
    "PermissionService",
    "PermissionSyncService",
    "RoleCrudService",
    "RolePermissionCrudService",
    "SubsidiaryCrudService",
    "SubsidiaryPermissionCrudService",
    "TenantService",
    "UserCrudService",
    "UserPermissionCrudService",
    "UserRoleCrudService",
    "VerifyService",
]
