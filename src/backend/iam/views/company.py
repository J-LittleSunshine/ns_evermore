# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from iam.models import IamCompany
from iam.policies.organization import OrganizationPolicy
from iam.services.tenant import TenantService
from iam.validators import CompanyValidator
from iam.views.base import BaseIamViewSet

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
        context = TenantService.from_user(request.current_user)
        OrganizationPolicy.ensure_can_create_company(context)

        return await super().create_item(request, *args, **kwargs)

    async def delete_item(self, request, *args, **kwargs):
        context = TenantService.from_user(request.current_user)
        OrganizationPolicy.ensure_can_delete_company(context)

        return await super().delete_item(request, *args, **kwargs)

