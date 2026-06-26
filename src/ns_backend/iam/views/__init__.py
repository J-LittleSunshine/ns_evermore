# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.views.auth_views import AuthViewSet
from ns_backend.iam.views.access_views import AccessViewSet
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
from ns_backend.iam.views.internal_views import InternalIamViewSet

if TYPE_CHECKING:
    pass

__all__ = [
    "AuthViewSet",
    "AccessViewSet",
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
    "InternalIamViewSet",
    "SubsidiaryPermissionViewSet",
    "SubsidiaryViewSet",
    "UserPermissionViewSet",
    "UserRoleViewSet",
    "UserViewSet",
]
