# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from iam.services.crud import CompanyCrudService
from iam.validators import CompanyValidator
from iam.views.base import BaseIamViewSet


if TYPE_CHECKING:
    pass

class CompanyViewSet(BaseIamViewSet):
    service_class = CompanyCrudService
    validator_class = CompanyValidator
    list_fields = detail_fields = ("id", "company_code", "company_name", "legal_name", "status")
    create_fields = ("company_code", "company_name", "legal_name", "status")
    update_fields = ("company_name", "legal_name", "status")
