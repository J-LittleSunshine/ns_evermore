# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from iam.models import (
    IamCompany,
    IamDepartment,
    IamDepartmentPermission,
    IamPermission,
    IamRole,
    IamRolePermission,
    IamSubsidiary,
    IamSubsidiaryPermission,
    IamUserPermission,
    IamUserRole,
)
from iam.services.base import BaseIamService


class CompanyCrudService(BaseIamService):
    model = IamCompany


class SubsidiaryCrudService(BaseIamService):
    model = IamSubsidiary


class DepartmentCrudService(BaseIamService):
    model = IamDepartment


class PermissionCrudService(BaseIamService):
    model = IamPermission


class RoleCrudService(BaseIamService):
    model = IamRole


class UserRoleCrudService(BaseIamService):
    model = IamUserRole


class RolePermissionCrudService(BaseIamService):
    model = IamRolePermission


class UserPermissionCrudService(BaseIamService):
    model = IamUserPermission


class DepartmentPermissionCrudService(BaseIamService):
    model = IamDepartmentPermission


class SubsidiaryPermissionCrudService(BaseIamService):
    model = IamSubsidiaryPermission
