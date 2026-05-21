# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from iam.models import IamSubsidiary
from iam.validators import SubsidiaryValidator
from iam.views.base import BaseIamViewSet

if TYPE_CHECKING:
    pass


class SubsidiaryViewSet(BaseIamViewSet):
    model_class = IamSubsidiary
    validator_class = SubsidiaryValidator
    tenant_scope_field = "company_id"
    tenant_create_field = "company_id"
    enterprise_resource_required = True
    list_fields = detail_fields = ("id", "company_id", "subsidiary_code", "subsidiary_name", "status")
    create_fields = ("company_id", "subsidiary_code", "subsidiary_name", "status")
    update_fields = ("company_id", "subsidiary_name", "status")
