# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib.auth.hashers import make_password
from django.utils import timezone

from ns_backend.backend.exceptions import BusinessError
from ns_backend.backend.utils.password_transport import PasswordTransportService
from ns_backend.iam.constants import USER_TYPE_ENTERPRISE
from ns_backend.iam.models import IamCompany, IamDepartment, IamPermission, IamRole, IamSubsidiary, IamUser
from ns_backend.iam.policies import OrganizationPolicy, TenantPolicy, UserPolicy
from ns_backend.iam.repositories import IamBaseRepository, UserSessionRepository, UserTokenRepository
from ns_backend.iam.schemas import TenantContext
from ns_backend.iam.validators import CompanyValidator, DepartmentValidator, PermissionValidator, RoleValidator, SubsidiaryValidator, UserValidator
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


class IamBaseService:
    """Base IAM resource operation service.

    Service responsibilities:
    1. Resolve tenant filters and tenant create values.
    2. Validate create/update payloads.
    3. Run resource-specific business rule hooks.
    4. Delegate all persistence operations to repositories.
    """

    model_class: Any = None
    validator_class: Any = None

    list_fields: tuple[str, ...] = ()
    detail_fields: tuple[str, ...] = ()
    update_fields: tuple[str, ...] = ()

    tenant_scope_field: str | None = None
    tenant_create_field: str | None = None
    enterprise_resource_required: bool = False

    @staticmethod
    def is_truthy(value: Any) -> bool:
        """Return whether value is treated as true in request payload."""
        return value in (True, 1, "1", "true", "True", "yes", "YES", "on", "ON")

    @classmethod
    async def list_items(cls, *, page: int | str | None = 1, page_size: int | str | None = 20, tenant_context: TenantContext | None = None) -> dict[str, Any]:
        """List IAM resources."""
        tenant_filter = cls.get_tenant_filter(tenant_context=tenant_context)
        return await IamBaseRepository.list_items(model_class=cls.model_class, fields=cls.list_fields, page=page, page_size=page_size, tenant_filter=tenant_filter)

    @classmethod
    async def detail_item(cls, *, item_id: int | str | None, tenant_context: TenantContext | None = None) -> dict[str, Any]:
        """Get IAM resource detail."""
        tenant_filter = cls.get_tenant_filter(tenant_context=tenant_context)
        return await IamBaseRepository.detail_item(model_class=cls.model_class, item_id=item_id, fields=cls.detail_fields, tenant_filter=tenant_filter)

    @classmethod
    async def create_item(cls, *, data: dict[str, Any], operator_id: int | None = None, tenant_context: TenantContext | None = None) -> dict[str, Any]:
        """Create IAM resource."""
        validated_data = cls.validate_create_data(data)
        await cls.validate_create_business_rules(data=validated_data, tenant_context=tenant_context)

        tenant_create_values = cls.get_tenant_create_values(tenant_context=tenant_context)
        return await IamBaseRepository.create_item_with_audit(model_class=cls.model_class, data=validated_data, operator_id=operator_id, tenant_create_values=tenant_create_values)

    @classmethod
    async def update_item(cls, *, item_id: int | str | None, data: dict[str, Any], operator_id: int | None = None, tenant_context: TenantContext | None = None) -> None:
        """Update IAM resource."""
        validated_data = cls.validate_update_data(data)
        tenant_filter = cls.get_tenant_filter(tenant_context=tenant_context)
        item = await IamBaseRepository.get_required_by_id(model_class=cls.model_class, item_id=item_id, tenant_filter=tenant_filter)

        await cls.validate_update_business_rules(item=item, data=validated_data, tenant_context=tenant_context)
        await IamBaseRepository.update_item_with_audit(model_class=cls.model_class, item_id=item_id, data=validated_data, operator_id=operator_id, tenant_filter=tenant_filter)

    @classmethod
    async def delete_item(cls, *, item_id: int | str | None, tenant_context: TenantContext | None = None) -> None:
        """Delete IAM resource."""
        tenant_filter = cls.get_tenant_filter(tenant_context=tenant_context)
        await IamBaseRepository.delete_item_by_id(model_class=cls.model_class, item_id=item_id, tenant_filter=tenant_filter)

    @classmethod
    async def validate_create_business_rules(cls, *, data: dict[str, Any], tenant_context: TenantContext | None = None) -> None:
        """Validate resource-specific create business rules."""
        return None

    @classmethod
    async def validate_update_business_rules(cls, *, item: Any, data: dict[str, Any], tenant_context: TenantContext | None = None) -> None:
        """Validate resource-specific update business rules."""
        return None

    @classmethod
    def validate_create_data(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Validate create payload."""
        if cls.validator_class:
            return cls.validator_class.validate_create(data)
        return data

    @classmethod
    def validate_update_data(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Validate update payload and reject fields outside update_fields."""
        allowed_update_fields = set(cls.update_fields)
        for field in data.keys():
            if field == "id":
                continue
            if allowed_update_fields and field not in allowed_update_fields:
                raise BusinessError(f"Updating field is not allowed: {field}", NsErrorCode.UPDATE_FIELD_NOT_ALLOWED)

        if cls.validator_class:
            return cls.validator_class.validate_update(data)

        return {field: data[field] for field in cls.update_fields if field in data}

    @classmethod
    def get_tenant_filter(cls, *, tenant_context: TenantContext | None) -> dict[str, Any] | None:
        """Resolve tenant filter for list/detail/update/delete."""
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

        raise BusinessError("Personal users cannot access enterprise organization resources", NsErrorCode.ENTERPRISE_ORG_FORBIDDEN_PERSONAL)

    @classmethod
    def get_tenant_create_values(cls, *, tenant_context: TenantContext | None) -> dict[str, Any] | None:
        """Resolve tenant create values for create operation."""
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

        raise BusinessError("Personal users cannot access enterprise organization resources", NsErrorCode.ENTERPRISE_ORG_FORBIDDEN_PERSONAL)

    @classmethod
    def resolve_company_id_for_payload(cls, *, data: dict[str, Any], tenant_context: TenantContext | None = None) -> int | None:
        """Resolve effective company id for a create/update payload."""
        if tenant_context is not None and not TenantPolicy.is_platform_admin(tenant_context):
            TenantPolicy.ensure_enterprise_context(tenant_context)
            return tenant_context.company_id

        company_id = data.get("company_id")
        return None if company_id in (None, "") else int(company_id)


class CompanyService(IamBaseService):
    """Company resource operation service."""

    model_class = IamCompany
    validator_class = CompanyValidator
    tenant_scope_field = "id"
    tenant_create_field = None
    enterprise_resource_required = True

    list_fields = detail_fields = ("id", "company_code", "company_name", "legal_name", "status")
    update_fields = ("company_name", "legal_name", "status")

    @classmethod
    async def create_item(cls, *, data: dict[str, Any], operator_id: int | None = None, tenant_context: TenantContext | None = None) -> dict[str, Any]:
        """Create company. Only platform administrators can create companies."""
        if tenant_context is not None:
            OrganizationPolicy.ensure_can_create_company(tenant_context)
        return await super().create_item(data=data, operator_id=operator_id, tenant_context=tenant_context)

    @classmethod
    async def delete_item(cls, *, item_id: int | str | None, tenant_context: TenantContext | None = None) -> None:
        """Delete company. Only platform administrators can delete companies."""
        if tenant_context is not None:
            OrganizationPolicy.ensure_can_delete_company(tenant_context)
        await super().delete_item(item_id=item_id, tenant_context=tenant_context)


class DepartmentService(IamBaseService):
    """Department resource operation service."""

    model_class = IamDepartment
    validator_class = DepartmentValidator
    tenant_scope_field = "company_id"
    tenant_create_field = "company_id"
    enterprise_resource_required = True

    list_fields = detail_fields = ("id", "company_id", "subsidiary_id", "parent_id", "department_code", "department_name", "status")
    update_fields = ("department_name", "status")

    @classmethod
    async def validate_create_business_rules(cls, *, data: dict[str, Any], tenant_context: TenantContext | None = None) -> None:
        """Validate organization boundary before creating department."""
        company_id = cls.resolve_company_id_for_payload(data=data, tenant_context=tenant_context)
        if company_id is None:
            return

        await OrganizationPolicy.ensure_subsidiary_belongs_to_company(subsidiary_id=data.get("subsidiary_id"), company_id=company_id)
        await OrganizationPolicy.ensure_parent_department_belongs_to_company(parent_id=data.get("parent_id"), company_id=company_id)


class PermissionBaseService(IamBaseService):
    """Permission resource operation service."""

    model_class = IamPermission
    validator_class = PermissionValidator

    list_fields = detail_fields = ("id", "permission_code", "permission_name", "permission_type", "parent_id", "status")
    update_fields = ("permission_name", "permission_type", "parent_id", "status")


class RoleService(IamBaseService):
    """Role resource operation service."""

    model_class = IamRole
    validator_class = RoleValidator
    tenant_scope_field = "company_id"
    tenant_create_field = "company_id"
    enterprise_resource_required = False

    list_fields = detail_fields = ("id", "company_id", "role_code", "role_name", "role_scope", "status")
    update_fields = ("role_name", "status")


class SubsidiaryService(IamBaseService):
    """Subsidiary resource operation service."""

    model_class = IamSubsidiary
    validator_class = SubsidiaryValidator
    tenant_scope_field = "company_id"
    tenant_create_field = "company_id"
    enterprise_resource_required = True

    list_fields = detail_fields = ("id", "company_id", "subsidiary_code", "subsidiary_name", "status")
    update_fields = ("subsidiary_name", "status")


class UserService(IamBaseService):
    """User resource operation service."""

    model_class = IamUser
    validator_class = UserValidator
    tenant_scope_field = "company_id"
    tenant_create_field = "company_id"
    enterprise_resource_required = False

    list_fields = detail_fields = (
        "id",
        "username",
        "email",
        "phone",
        "display_name",
        "user_type",
        "company_id",
        "subsidiary_id",
        "department_id",
        "is_active",
        "is_staff",
        "is_superuser",
        "last_login",
        "created_at",
        "updated_at"
    )
    update_fields = ("email", "phone", "display_name", "company_id", "subsidiary_id", "department_id", "is_active", "is_staff", "is_superuser")

    @classmethod
    async def create_item(cls, *, data: dict[str, Any], operator_id: int | None = None, tenant_context: TenantContext | None = None) -> dict[str, Any]:
        """Create user and hash password before persistence."""
        create_payload = cls.build_user_create_payload(data=data, tenant_context=tenant_context)
        validated_data = cls.validate_create_data(create_payload)

        raw_password_payload = validated_data.get("password")
        if raw_password_payload is None or raw_password_payload == "":
            raise BusinessError("password cannot be empty", NsErrorCode.USER_PASSWORD_EMPTY)

        raw_password = PasswordTransportService.resolve(raw_password_payload)

        create_data = dict(validated_data)
        create_data["password"] = make_password(raw_password)

        await cls.validate_user_organization_assignment(data=create_data)
        return await IamBaseRepository.create_item_with_audit(model_class=cls.model_class, data=create_data, operator_id=operator_id, tenant_create_values=None)

    @classmethod
    async def update_item(cls, *, item_id: int | str | None, data: dict[str, Any], operator_id: int | None = None, tenant_context: TenantContext | None = None) -> None:
        """Update user and revoke sessions/tokens when user is disabled."""
        tenant_filter = cls.get_tenant_filter(tenant_context=tenant_context)
        item = await IamBaseRepository.get_required_by_id(model_class=cls.model_class, item_id=item_id, tenant_filter=tenant_filter)
        prev_is_active = bool(getattr(item, "is_active", False))

        validated_data = cls.validate_update_data(data)
        await cls.validate_update_business_rules(item=item, data=validated_data, tenant_context=tenant_context)

        await IamBaseRepository.update_item_with_audit(model_class=cls.model_class, item_id=item_id, data=validated_data, operator_id=operator_id, tenant_filter=tenant_filter)

        next_is_active = validated_data.get("is_active")
        should_revoke = prev_is_active and str(next_is_active) == "0"
        if should_revoke:
            now = timezone.now()
            await cls.revoke_user_sessions_and_tokens(user_id=item.id, revoked_at=now)

    @classmethod
    async def delete_item(cls, *, item_id: int | str | None, tenant_context: TenantContext | None = None) -> None:
        """Delete user and revoke all active sessions/tokens first."""
        tenant_filter = cls.get_tenant_filter(tenant_context=tenant_context)
        item = await IamBaseRepository.get_required_by_id(model_class=cls.model_class, item_id=item_id, tenant_filter=tenant_filter)

        if tenant_context is not None and not tenant_context.is_superuser and bool(getattr(item, "is_superuser", False)):
            raise BusinessError("Staff administrators cannot operate on superusers", NsErrorCode.STAFF_CANNOT_OPERATE_SUPERUSER)

        now = timezone.now()
        await cls.revoke_user_sessions_and_tokens(user_id=item.id, revoked_at=now)
        await IamBaseRepository.delete_item(item)

    @classmethod
    async def reset_password(cls, *, item_id: int | str | None, password: str | None, operator_id: int | None = None, tenant_context: TenantContext | None = None) -> None:
        """Reset user password and revoke all active sessions/tokens."""
        if not isinstance(password, str) or not password:
            raise BusinessError("password cannot be empty", NsErrorCode.USER_PASSWORD_EMPTY)

        tenant_filter = cls.get_tenant_filter(tenant_context=tenant_context)
        item = await IamBaseRepository.get_required_by_id(model_class=cls.model_class, item_id=item_id, tenant_filter=tenant_filter)

        if tenant_context is not None and not tenant_context.is_superuser and bool(getattr(item, "is_superuser", False)):
            raise BusinessError("Staff administrators cannot operate on superusers", NsErrorCode.STAFF_CANNOT_OPERATE_SUPERUSER)

        now = timezone.now()
        raw_password = PasswordTransportService.resolve(password)
        await IamBaseRepository.update_item(
            instance=item,
            data={
                "password": make_password(raw_password),
                "updated_by": operator_id,
                "updated_at": now,
            },
        )
        await cls.revoke_user_sessions_and_tokens(user_id=item.id, revoked_at=now)

    @classmethod
    def build_user_create_payload(cls, *, data: dict[str, Any], tenant_context: TenantContext | None = None) -> dict[str, Any]:
        """Build tenant-safe user create payload."""
        create_data = dict(data)

        if tenant_context is None:
            return create_data

        if TenantPolicy.is_platform_admin(tenant_context):
            return create_data

        TenantPolicy.ensure_enterprise_context(tenant_context)

        if cls.is_truthy(create_data.get("is_superuser")):
            raise BusinessError("Staff administrators cannot operate on superusers", NsErrorCode.STAFF_CANNOT_OPERATE_SUPERUSER)

        create_data["company_id"] = tenant_context.company_id
        create_data["user_type"] = USER_TYPE_ENTERPRISE
        create_data["is_superuser"] = 0
        return create_data

    @classmethod
    async def validate_update_business_rules(cls, *, item: Any, data: dict[str, Any], tenant_context: TenantContext | None = None) -> None:
        """Validate user update business rules."""
        if tenant_context is not None and not tenant_context.is_superuser and bool(getattr(item, "is_superuser", False)):
            raise BusinessError("Staff administrators cannot operate on superusers", NsErrorCode.STAFF_CANNOT_OPERATE_SUPERUSER)

        if tenant_context is not None and not TenantPolicy.is_platform_admin(tenant_context):
            if "company_id" in data:
                raise BusinessError("Updating field is not allowed: company_id", NsErrorCode.UPDATE_FIELD_NOT_ALLOWED)

            if cls.is_truthy(data.get("is_superuser")):
                raise BusinessError("Staff administrators cannot operate on superusers", NsErrorCode.STAFF_CANNOT_OPERATE_SUPERUSER)

            if cls.is_truthy(data.get("is_staff")):
                raise BusinessError(f"Permission denied: {UserPolicy.ADMIN_USER_PERMISSION}", NsErrorCode.PERMISSION_DENIED)

        company_id = data.get("company_id", getattr(item, "company_id", None))
        if company_id in (None, ""):
            return

        organization_data = {
            "company_id": company_id,
            "subsidiary_id": data.get("subsidiary_id", getattr(item, "subsidiary_id", None)),
            "department_id": data.get("department_id", getattr(item, "department_id", None)),
        }
        await cls.validate_user_organization_assignment(data=organization_data)

    @staticmethod
    async def validate_user_organization_assignment(*, data: dict[str, Any]) -> None:
        """Validate user subsidiary and department assignment under company."""
        company_id = data.get("company_id")
        if company_id in (None, ""):
            return

        normalized_company_id = int(company_id)
        await OrganizationPolicy.ensure_subsidiary_belongs_to_company(subsidiary_id=data.get("subsidiary_id"), company_id=normalized_company_id)
        await OrganizationPolicy.ensure_department_belongs_to_company(department_id=data.get("department_id"), company_id=normalized_company_id)

    @staticmethod
    async def revoke_user_sessions_and_tokens(*, user_id: int, revoked_at) -> None:
        """Revoke all active sessions and tokens of one user."""
        await UserSessionRepository.revoke_by_user_id(user_id=user_id, revoked_at=revoked_at)
        await UserTokenRepository.revoke_by_user_id(user_id=user_id, revoked_at=revoked_at)
