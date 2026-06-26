# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.services.admin import AdminService
from ns_backend.iam.services.audit import AuditService
from ns_backend.iam.services.access_decision import AccessDecisionService
from ns_backend.iam.services.authorization_context import AuthorizationContextService
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
from ns_backend.iam.services.decision_audit import DecisionAuditService
from ns_backend.iam.services.grant import (
    DepartmentPermissionGrantService,
    RolePermissionGrantService,
    SubsidiaryPermissionGrantService,
    UserPermissionGrantService,
    UserRoleGrantService
)
from ns_backend.iam.services.module_hook import ModuleRegistrationHookService
from ns_backend.iam.services.permission import PermissionService
from ns_backend.iam.services.permission_sync import PermissionSyncService
from ns_backend.iam.services.policy import PolicyService
from ns_backend.iam.services.policy_engine import PolicyEngineService
from ns_backend.iam.services.resource_acl import ResourceAclService
from ns_backend.iam.services.resource_access_filter import ResourceAccessFilterService
from ns_backend.iam.services.resource_registry import ResourceRegistryService
from ns_backend.iam.services.session import SessionService
from ns_backend.iam.services.tenant import TenantService
from ns_backend.iam.services.verify import VerifyService

if TYPE_CHECKING:
    pass

__all__ = [
    "AdminService",
    "AuditService",
    "AccessDecisionService",
    "AuthorizationContextService",
    "AuthContextService",
    "AuthLoginResult",
    "AuthService",
    "CompanyService",
    "DataScopeService",
    "DecisionAuditService",
    "DepartmentPermissionGrantService",
    "DepartmentService",
    "IamBaseService",
    "ModuleRegistrationHookService",
    "PermissionBaseService",
    "PermissionService",
    "PermissionSyncService",
    "PolicyEngineService",
    "PolicyService",
    "ResourceAclService",
    "ResourceAccessFilterService",
    "ResourceRegistryService",
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
