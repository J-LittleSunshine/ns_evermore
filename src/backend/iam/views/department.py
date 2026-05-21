# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from iam.models import IamDepartment
from iam.validators import DepartmentValidator
from iam.views.base import BaseIamViewSet

if TYPE_CHECKING:
    pass


class DepartmentViewSet(BaseIamViewSet):
    model_class = IamDepartment
    validator_class = DepartmentValidator
    tenant_scope_field = "company_id"
    tenant_create_field = "company_id"
    enterprise_resource_required = True
    list_fields = detail_fields = (
        "id", "company_id", "subsidiary_id", "parent_id",
        "department_code", "department_name", "status",
    )
    create_fields = (
        "company_id", "subsidiary_id", "parent_id",
        "department_code", "department_name", "status",
    )
    update_fields = (
        "company_id", "subsidiary_id", "parent_id",
        "department_name", "status",
    )
