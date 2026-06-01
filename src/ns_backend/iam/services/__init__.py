# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.services.audit import AuditService
from ns_backend.iam.services.auth import AuthLoginResult, AuthService
from ns_backend.iam.services.auth_context import AuthContextService
from ns_backend.iam.services.base import (
    CompanyService,
    DepartmentService,
    IamBaseService,
    PermissionBaseService,
    RoleService,
    SubsidiaryService,
    UserService
)
from ns_backend.iam.services.data_scope import DataScopeService
from ns_backend.iam.services.grant import (
    DepartmentPermissionGrantService,
    RolePermissionGrantService,
    SubsidiaryPermissionGrantService,
    UserPermissionGrantService,
    UserRoleGrantService
)
from ns_backend.iam.services.permission import PermissionService
from ns_backend.iam.services.permission_sync import PermissionSyncService
from ns_backend.iam.services.session import SessionService
from ns_backend.iam.services.tenant import TenantService
from ns_backend.iam.services.verify import VerifyService

if TYPE_CHECKING:
    pass

__all__ = [
    "AuditService",
    "AuthContextService",
    "AuthLoginResult",
    "AuthService",
    "CompanyService",
    "DataScopeService",
    "DepartmentPermissionGrantService",
    "DepartmentService",
    "IamBaseService",
    "PermissionBaseService",
    "PermissionService",
    "PermissionSyncService",
    "RolePermissionGrantService",
    "RoleService",
    "SessionService",
    "SubsidiaryPermissionGrantService",
    "SubsidiaryService",
    "TenantService",
    "UserPermissionGrantService",
    "UserRoleGrantService",
    "UserService",
    "VerifyService",
]
