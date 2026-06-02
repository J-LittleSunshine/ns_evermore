# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.repositories.admin import AdminRepository
from ns_backend.iam.repositories.audit import AuditRepository
from ns_backend.iam.repositories.authorize import AuthorizeRepository
from ns_backend.iam.repositories.auth import AuthLoginBundleRepository, AuthUserRepository, LoginFailureRepository
from ns_backend.iam.repositories.base import IamBaseRepository
from ns_backend.iam.repositories.data_scope import DataScopeRepository
from ns_backend.iam.repositories.data_scope_filter import DataScopeQuerySetHelper
from ns_backend.iam.repositories.decision_audit import DecisionAuditRepository
from ns_backend.iam.repositories.grant import (
    DepartmentPermissionGrantRepository,
    GrantBoundaryRepository,
    GrantPermissionRepository,
    RolePermissionGrantRepository,
    SubsidiaryPermissionGrantRepository,
    UserPermissionGrantRepository,
    UserRoleGrantRepository
)
from ns_backend.iam.repositories.organization import OrganizationRepository
from ns_backend.iam.repositories.permission import PermissionRepository
from ns_backend.iam.repositories.permission_sync import PermissionSyncRepository
from ns_backend.iam.repositories.policy import PolicyRepository
from ns_backend.iam.repositories.resource import ResourceRepository
from ns_backend.iam.repositories.resource_acl import ResourceAclRepository
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
    "AuthorizeRepository",
    "AuthLoginBundleRepository",
    "AuthUserRepository",
    "DataScopeQuerySetHelper",
    "DataScopeRepository",
    "DecisionAuditRepository",
    "DepartmentPermissionGrantRepository",
    "GrantPermissionRepository",
    "GrantBoundaryRepository",
    "IamBaseRepository",
    "LoginFailureRepository",
    "OrganizationRepository",
    "PermissionRepository",
    "PermissionSyncRepository",
    "PolicyRepository",
    "ResourceAclRepository",
    "ResourceRepository",
    "RoleRepository",
    "RolePermissionGrantRepository",
    "SubsidiaryPermissionGrantRepository",
    "TokenRotationResult",
    "UserPermissionGrantRepository",
    "UserRepository",
    "UserRoleGrantRepository",
    "UserSessionRepository",
    "UserTokenRepository",
    "UserTokenRotationRepository",
]
