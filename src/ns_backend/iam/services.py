# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ns_common.error_codes import NsErrorCode

from ns_backend.backend.common import CrudRepository
from ns_backend.backend.exceptions import BusinessError

from .constants import USER_TYPE_ENTERPRISE
from .policies import TenantPolicy
from .schemas import TenantContext

if TYPE_CHECKING:
    pass


class TenantService:
    @classmethod
    def from_user(cls, user: Any) -> TenantContext:
        return TenantContext(
            user_id=user.id,
            user_type=getattr(user, "user_type", ""),
            company_id=getattr(user, "company_id", None),
            subsidiary_id=getattr(user, "subsidiary_id", None),
            department_id=getattr(user, "department_id", None),
            is_staff=bool(getattr(user, "is_staff", False)),
            is_superuser=bool(getattr(user, "is_superuser", False)),
        )


class IamCrudService:
    model_class: Any = None
    validator_class: Any = None

    list_fields: tuple[str, ...] = ()
    detail_fields: tuple[str, ...] = ()
    update_fields: tuple[str, ...] = ()

    tenant_scope_field: str | None = None
    tenant_create_field: str | None = None
    enterprise_resource_required: bool = False

    @classmethod
    async def list_items(
        cls,
        *,
        page: int | str | None = 1,
        page_size: int | str | None = 20,
        tenant_context: TenantContext | None = None,
    ) -> dict[str, Any]:
        tenant_filter = cls.get_tenant_filter(tenant_context=tenant_context)
        return await CrudRepository.list_items(
            model_class=cls.model_class,
            fields=cls.list_fields,
            page=page,
            page_size=page_size,
            tenant_filter=tenant_filter,
        )

    @classmethod
    async def detail_item(
        cls,
        *,
        item_id: int | str | None,
        tenant_context: TenantContext | None = None,
    ) -> dict[str, Any]:
        tenant_filter = cls.get_tenant_filter(tenant_context=tenant_context)
        return await CrudRepository.detail_item(
            model_class=cls.model_class,
            item_id=item_id,
            fields=cls.detail_fields,
            tenant_filter=tenant_filter,
        )

    @classmethod
    async def create_item(
        cls,
        *,
        data: dict[str, Any],
        operator_id: int | None = None,
        tenant_context: TenantContext | None = None,
    ) -> dict[str, Any]:
        validated_data = cls.validate_create_data(data)
        tenant_create_values = cls.get_tenant_create_values(tenant_context=tenant_context)
        return await CrudRepository.create_item_with_audit(
            model_class=cls.model_class,
            data=validated_data,
            operator_id=operator_id,
            tenant_create_values=tenant_create_values,
        )

    @classmethod
    async def update_item(
        cls,
        *,
        item_id: int | str | None,
        data: dict[str, Any],
        operator_id: int | None = None,
        tenant_context: TenantContext | None = None,
    ) -> None:
        validated_data = cls.validate_update_data(data)
        tenant_filter = cls.get_tenant_filter(tenant_context=tenant_context)
        await CrudRepository.update_item_with_audit(
            model_class=cls.model_class,
            item_id=item_id,
            data=validated_data,
            operator_id=operator_id,
            tenant_filter=tenant_filter,
        )

    @classmethod
    async def delete_item(
        cls,
        *,
        item_id: int | str | None,
        tenant_context: TenantContext | None = None,
    ) -> None:
        tenant_filter = cls.get_tenant_filter(tenant_context=tenant_context)
        await CrudRepository.delete_item_by_id(
            model_class=cls.model_class,
            item_id=item_id,
            tenant_filter=tenant_filter,
        )

    @classmethod
    def validate_create_data(cls, data: dict[str, Any]) -> dict[str, Any]:
        if cls.validator_class:
            return cls.validator_class.validate_create(data)
        return data

    @classmethod
    def validate_update_data(cls, data: dict[str, Any]) -> dict[str, Any]:
        allowed_update_fields = set(cls.update_fields)
        for field in data.keys():
            if field == "id":
                continue
            if allowed_update_fields and field not in allowed_update_fields:
                raise BusinessError(f"Updating field is not allowed: {field}", NsErrorCode.UPDATE_FIELD_NOT_ALLOWED)

        if cls.validator_class:
            return cls.validator_class.validate_update(data)

        return {
            field: data[field]
            for field in cls.update_fields
            if field in data
        }

    @classmethod
    def get_tenant_filter(cls, *, tenant_context: TenantContext | None) -> dict[str, Any] | None:
        if cls.tenant_scope_field is None or tenant_context is None:
            return None

        if TenantPolicy.is_platform_admin(tenant_context):
            return None

        if cls.enterprise_resource_required:
            TenantPolicy.ensure_enterprise_context(tenant_context)

        if tenant_context.user_type == USER_TYPE_ENTERPRISE:
            company_id = tenant_context.company_id
            if company_id is None:
                raise BusinessError("Enterprise user is not bound to a company", NsErrorCode.ENTERPRISE_USER_COMPANY_NOT_BOUND)
            return {cls.tenant_scope_field: company_id}

        raise BusinessError(
            "Personal users cannot access enterprise organization resources",
            NsErrorCode.ENTERPRISE_ORG_FORBIDDEN_PERSONAL,
        )

    @classmethod
    def get_tenant_create_values(cls, *, tenant_context: TenantContext | None) -> dict[str, Any] | None:
        if cls.tenant_create_field is None or tenant_context is None:
            return None

        if TenantPolicy.is_platform_admin(tenant_context):
            return None

        if cls.enterprise_resource_required:
            TenantPolicy.ensure_enterprise_context(tenant_context)

        if tenant_context.user_type == USER_TYPE_ENTERPRISE:
            company_id = tenant_context.company_id
            if company_id is None:
                raise BusinessError("Enterprise user is not bound to a company", NsErrorCode.ENTERPRISE_USER_COMPANY_NOT_BOUND)
            return {cls.tenant_create_field: company_id}

        raise BusinessError(
            "Personal users cannot access enterprise organization resources",
            NsErrorCode.ENTERPRISE_ORG_FORBIDDEN_PERSONAL,
        )


__all__ = [
    "TenantService",
    "IamCrudService",
]
