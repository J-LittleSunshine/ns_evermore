# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from iam.services.crud import DepartmentCrudService
from iam.validators import DepartmentValidator
from iam.views.base import BaseIamViewSet

if TYPE_CHECKING:
    pass

class DepartmentViewSet(BaseIamViewSet):
    service_class = DepartmentCrudService
    validator_class = DepartmentValidator
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
