# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.repositories.admin import AdminRepository
from ns_backend.iam.repositories.audit import AuditRepository
from ns_backend.iam.repositories.auth import AuthUserRepository, LoginFailureRepository
from ns_backend.iam.repositories.base import IamBaseRepository
from ns_backend.iam.repositories.data_scope import DataScopeRepository
from ns_backend.iam.repositories.data_scope_filter import DataScopeQuerySetHelper
from ns_backend.iam.repositories.device import UserDeviceRepository
from ns_backend.iam.repositories.grant import (
    DepartmentPermissionGrantRepository,
    GrantPermissionRepository,
    RolePermissionGrantRepository,
    SubsidiaryPermissionGrantRepository,
    UserPermissionGrantRepository,
    UserRoleGrantRepository
)
from ns_backend.iam.repositories.organization import OrganizationRepository
from ns_backend.iam.repositories.permission import PermissionRepository
from ns_backend.iam.repositories.permission_sync import PermissionSyncRepository
from ns_backend.iam.repositories.role import RoleRepository
from ns_backend.iam.repositories.session import UserSessionRepository
from ns_backend.iam.repositories.token import UserTokenRepository, UserTokenRotationRepository
from ns_backend.iam.repositories.user import UserRepository
from ns_backend.iam.schemas import TokenRotationResult

if TYPE_CHECKING:
    pass

__all__ = [
    "AdminRepository",
    "AuditRepository",
    "AuthUserRepository",
    "DataScopeQuerySetHelper",
    "DataScopeRepository",
    "DepartmentPermissionGrantRepository",
    "GrantPermissionRepository",
    "IamBaseRepository",
    "LoginFailureRepository",
    "OrganizationRepository",
    "PermissionRepository",
    "PermissionSyncRepository",
    "RoleRepository",
    "RolePermissionGrantRepository",
    "SubsidiaryPermissionGrantRepository",
    "TokenRotationResult",
    "UserDeviceRepository",
    "UserPermissionGrantRepository",
    "UserRepository",
    "UserRoleGrantRepository",
    "UserSessionRepository",
    "UserTokenRepository",
    "UserTokenRotationRepository",
]
