# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.services.access_decision import AccessDecisionService
from ns_backend.iam.services.auth import AuthService
from ns_backend.iam.services.auth_context import AuthContextService
from ns_backend.iam.services.data_scope import DataScopeService
from ns_backend.iam.services.decision_audit import DecisionAuditService
from ns_backend.iam.services.internal import InternalIamService
from ns_backend.iam.services.management import (
    CompanyManagementService,
    DepartmentManagementService,
    DepartmentPermissionManagementService,
    DirectPermissionGrantManagementService,
    IamManagementService,
    PermissionManagementService,
    PolicyManagementService,
    PolicyRuleManagementService,
    ResourceAclManagementService,
    ResourceActionManagementService,
    ResourceManagementService,
    ResourceRelationManagementService,
    RoleManagementService,
    RolePermissionManagementService,
    SubsidiaryManagementService,
    SubsidiaryPermissionManagementService,
    UserManagementService,
    UserPermissionManagementService,
    UserRoleManagementService
)
from ns_backend.iam.services.permission import PermissionService

if TYPE_CHECKING:
    pass

__all__ = [
    "AuthService",
    "AuthContextService",
    "AccessDecisionService",
    "CompanyManagementService",
    "DataScopeService",
    "DepartmentManagementService",
    "DecisionAuditService",
    "DepartmentPermissionManagementService",
    "DirectPermissionGrantManagementService",
    "IamManagementService",
    "PermissionManagementService",
    "PermissionService",
    "ResourceAclManagementService",
    "ResourceActionManagementService",
    "ResourceManagementService",
    "ResourceRelationManagementService",
    "RoleManagementService",
    "RolePermissionManagementService",
    "InternalIamService",
    "SubsidiaryManagementService",
    "SubsidiaryPermissionManagementService",
    "UserManagementService",
    "UserPermissionManagementService",
    "UserRoleManagementService",
    "PolicyManagementService",
    "PolicyRuleManagementService",
]
