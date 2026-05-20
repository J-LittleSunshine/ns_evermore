# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from .company import CompanyViewSet
from .department import DepartmentViewSet
from .grant import (
    DepartmentPermissionViewSet,
    RolePermissionViewSet,
    SubsidiaryPermissionViewSet,
    UserPermissionViewSet,
    UserRoleViewSet,
)
from .permission import PermissionViewSet
from .role import RoleViewSet
from .subsidiary import SubsidiaryViewSet
from .user import UserViewSet

if TYPE_CHECKING:
    pass

__all__ = [
    "CompanyViewSet",
    "SubsidiaryViewSet",
    "DepartmentViewSet",
    "PermissionViewSet",
    "RoleViewSet",
    "UserViewSet",
    "UserRoleViewSet",
    "RolePermissionViewSet",
    "UserPermissionViewSet",
    "DepartmentPermissionViewSet",
    "SubsidiaryPermissionViewSet",
]
