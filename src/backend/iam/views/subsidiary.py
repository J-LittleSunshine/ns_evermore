# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from iam.services.crud import SubsidiaryCrudService
from iam.validators import SubsidiaryValidator
from iam.views.base import BaseIamViewSet

if TYPE_CHECKING:
    pass


class SubsidiaryViewSet(BaseIamViewSet):
    service_class = SubsidiaryCrudService
    validator_class = SubsidiaryValidator
    list_fields = detail_fields = ("id", "company_id", "subsidiary_code", "subsidiary_name", "status")
    create_fields = ("company_id", "subsidiary_code", "subsidiary_name", "status")
    update_fields = ("company_id", "subsidiary_name", "status")
