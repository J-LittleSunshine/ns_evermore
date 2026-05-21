# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from iam.policies.tenant import TenantPolicy
from iam.repositories.base import CrudRepository
from iam.services.auth import VerifyService
from iam.services.permission import PermissionService
from iam.services.tenant import TenantContext, TenantService
from ns_backend.auth import AuthenticatedRequestViewSet
from ns_backend.exceptions import BusinessError
from ns_backend.exceptions import ValidateError

if TYPE_CHECKING:
    pass


class IamRequestViewSet(AuthenticatedRequestViewSet):
    verify_service = VerifyService
    permission_service = PermissionService


class BaseIamViewSet(IamRequestViewSet):
    model_class = None
    validator_class = None
    tenant_scope_field: str | None = None
    tenant_create_field: str | None = None
    enterprise_resource_required: bool = False

    list_fields: tuple[str, ...] = ()
    detail_fields: tuple[str, ...] = ()
    update_fields: tuple[str, ...] = ()

    async def list_item(self, request, *args, **kwargs):
        page = request.data.get("page", 1)
        page_size = request.data.get("page_size", 20)
        tenant_filter = self.get_tenant_filter(request)

        data = await CrudRepository.list_items(
            model_class=self.model_class,
            fields=self.list_fields,
            page=page,
            page_size=page_size,
            tenant_filter=tenant_filter,
        )

        return self.success_response(data)

    async def detail_item(self, request, *args, **kwargs):
        item_id = request.data.get("id")
        tenant_filter = self.get_tenant_filter(request)

        data = await CrudRepository.detail_item(
            model_class=self.model_class,
            item_id=item_id,
            fields=self.detail_fields,
            tenant_filter=tenant_filter,
        )

        return self.success_response(data)

    async def create_item(self, request, *args, **kwargs):
        data = self.validate_create_data(request.data)
        operator_id = self.get_operator_id(request)
        tenant_create_values = self.get_tenant_create_values(request)

        result = await CrudRepository.create_item_with_audit(
            model_class=self.model_class,
            data=data,
            operator_id=operator_id,
            tenant_create_values=tenant_create_values,
        )

        return self.success_response(result)

    async def update_item(self, request, *args, **kwargs):
        item_id = request.data.get("id")
        data = self.validate_update_data(request.data)
        operator_id = self.get_operator_id(request)
        tenant_filter = self.get_tenant_filter(request)

        await CrudRepository.update_item_with_audit(
            model_class=self.model_class,
            item_id=item_id,
            data=data,
            operator_id=operator_id,
            tenant_filter=tenant_filter,
        )

        return self.success_response()

    async def delete_item(self, request, *args, **kwargs):
        item_id = request.data.get("id")
        tenant_filter = self.get_tenant_filter(request)

        await CrudRepository.delete_item_by_id(
            model_class=self.model_class,
            item_id=item_id,
            tenant_filter=tenant_filter,
        )

        return self.success_response()

    def validate_create_data(self, data: dict[str, Any]) -> dict[str, Any]:
        if self.validator_class:
            return self.validator_class.validate_create(data)

        return data

    def validate_update_data(self, data: dict[str, Any]) -> dict[str, Any]:
        for field in data.keys():
            if field == "id":
                continue

            if field not in self.update_fields:
                raise ValidateError(f"不允许更新字段：{field}", 12005)

        if self.validator_class:
            return self.validator_class.validate_update(data)

        return {
            field: data[field]
            for field in self.update_fields
            if field in data
        }

    @staticmethod
    def get_operator_id(request) -> int | None:
        current_user = getattr(request, "current_user", None)
        return getattr(current_user, "id", None)

    def get_tenant_context(self, request) -> TenantContext | None:
        current_user = getattr(request, "current_user", None)

        if not current_user:
            return None

        return TenantService.from_user(current_user)

    def get_tenant_filter(self, request) -> dict[str, Any] | None:
        if self.tenant_scope_field is None:
            return None

        context = self.get_tenant_context(request)

        if context is None:
            return None

        if TenantPolicy.is_platform_admin(context):
            return None

        if self.enterprise_resource_required:
            TenantPolicy.ensure_enterprise_context(context)

        if TenantPolicy.is_enterprise_user(context):
            company_id = context.company_id

            if company_id is None:
                raise BusinessError("企业用户未绑定公司", 14001)

            return {self.tenant_scope_field: company_id}

        raise BusinessError("个人用户不能访问企业组织资源", 14002)

    def get_tenant_create_values(self, request) -> dict[str, Any] | None:
        if self.tenant_create_field is None:
            return None

        context = self.get_tenant_context(request)

        if context is None:
            return None

        if TenantPolicy.is_platform_admin(context):
            return None

        if self.enterprise_resource_required:
            TenantPolicy.ensure_enterprise_context(context)

        if TenantPolicy.is_enterprise_user(context):
            company_id = context.company_id

            if company_id is None:
                raise BusinessError("企业用户未绑定公司", 14001)

            return {self.tenant_create_field: company_id}

        raise BusinessError("个人用户不能访问企业组织资源", 14002)


