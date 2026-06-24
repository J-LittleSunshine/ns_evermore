# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.views.auth_views import AuthViewSet
from ns_backend.iam.views.management_views import (
    CompanyViewSet,
    DepartmentViewSet,
    IamManagementViewSet,
    PermissionViewSet,
    RoleViewSet,
    SubsidiaryViewSet,
    UserViewSet,
)

if TYPE_CHECKING:
    pass

__all__ = [
    "AuthViewSet",
    "CompanyViewSet",
    "DepartmentViewSet",
    "IamManagementViewSet",
    "PermissionViewSet",
    "RoleViewSet",
    "SubsidiaryViewSet",
    "UserViewSet",
]
