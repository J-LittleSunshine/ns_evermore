# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.services.audit import AuditService
from ns_backend.iam.services.auth import AuthLoginResult, AuthService
from ns_backend.iam.services.auth_context import AuthContextService
from ns_backend.iam.services.data_scope import DataScopeService
from ns_backend.iam.services.grant import (
    DepartmentPermissionGrantService,
    RolePermissionGrantService,
    SubsidiaryPermissionGrantService,
    UserPermissionGrantService,
    UserRoleGrantService
)
from ns_backend.iam.services.legacy import (
    CompanyCrudService,
    DepartmentCrudService,
    DepartmentPermissionCrudService,
    IamCrudService,
    PermissionCrudService,
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
from ns_backend.iam.services.permission import PermissionService
from ns_backend.iam.services.session import SessionService
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
    "DepartmentPermissionGrantService",
    "IamCrudService",
    "PermissionCrudService",
    "PermissionService",
    "PermissionSyncService",
    "RoleCrudService",
    "RolePermissionCrudService",
    "RolePermissionGrantService",
    "SessionService",
    "SubsidiaryCrudService",
    "SubsidiaryPermissionCrudService",
    "SubsidiaryPermissionGrantService",
    "TenantService",
    "UserCrudService",
    "UserPermissionCrudService",
    "UserPermissionGrantService",
    "UserRoleCrudService",
    "UserRoleGrantService",
    "VerifyService",
]
