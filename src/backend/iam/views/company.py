# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from iam.models import IamCompany
from iam.validators import CompanyValidator
from iam.views.base import BaseIamViewSet
from ns_backend.exceptions import BusinessError

if TYPE_CHECKING:
    pass


class CompanyViewSet(BaseIamViewSet):
    model_class = IamCompany
    validator_class = CompanyValidator
    tenant_scope_field = "id"
    tenant_create_field = None
    enterprise_resource_required = True
    list_fields = detail_fields = ("id", "company_code", "company_name", "legal_name", "status")
    create_fields = ("company_code", "company_name", "legal_name", "status")
    update_fields = ("company_name", "legal_name", "status")

    async def create_item(self, request, *args, **kwargs):
        current_user = getattr(request, "current_user", None)

        if not bool(getattr(current_user, "is_superuser", False)):
            raise BusinessError("只有平台管理员可以创建公司", 14003)

        return await super().create_item(request, *args, **kwargs)

