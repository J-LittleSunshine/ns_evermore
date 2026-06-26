# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.views.auth_views import AuthViewSet
from ns_backend.iam.views.authorize_views import AuthorizeViewSet
from ns_backend.iam.views.management_views import (
    CompanyViewSet,
    DepartmentPermissionViewSet,
    DepartmentViewSet,
    IamManagementViewSet,
    PermissionViewSet,
    ResourceAclViewSet,
    ResourceActionViewSet,
    ResourceRelationViewSet,
    ResourceViewSet,
    RolePermissionViewSet,
    RoleViewSet,
    SubsidiaryPermissionViewSet,
    SubsidiaryViewSet,
    UserPermissionViewSet,
    UserRoleViewSet,
    UserViewSet
)
from ns_backend.iam.views.runtime_auth_views import RuntimeIamInternalViewSet

if TYPE_CHECKING:
    pass

__all__ = [
    "AuthViewSet",
    "AuthorizeViewSet",
    "CompanyViewSet",
    "DepartmentPermissionViewSet",
    "DepartmentViewSet",
    "IamManagementViewSet",
    "PermissionViewSet",
    "ResourceAclViewSet",
    "ResourceActionViewSet",
    "ResourceRelationViewSet",
    "ResourceViewSet",
    "RolePermissionViewSet",
    "RoleViewSet",
    "RuntimeIamInternalViewSet",
    "SubsidiaryPermissionViewSet",
    "SubsidiaryViewSet",
    "UserPermissionViewSet",
    "UserRoleViewSet",
    "UserViewSet",
]
