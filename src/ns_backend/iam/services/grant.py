# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.constants import to_storage_data_scope
from ns_backend.iam.errors import IamDomainError
from ns_backend.iam.policies import DataScopePolicy, GrantPolicy
from ns_backend.iam.repositories import (
    DepartmentPermissionGrantRepository,
    GrantPermissionRepository,
    RolePermissionGrantRepository,
    SubsidiaryPermissionGrantRepository,
    UserPermissionGrantRepository,
    UserRoleGrantRepository,
)
from ns_backend.iam.validators import (
    DepartmentPermissionValidator,
    RolePermissionValidator,
    SubsidiaryPermissionValidator,
    UserPermissionValidator,
    UserRoleValidator,
)
from ns_backend.iam.services.authorization_context import AuthorizationContextService
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


def _to_positive_int(value: Any, field_name: str) -> int:
    """Convert value to positive int."""
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise BusinessError(f"{field_name} is invalid", NsErrorCode.INVALID_VALUE) from exc

    if parsed <= 0:
        raise BusinessError(f"{field_name} is invalid", NsErrorCode.INVALID_VALUE)

    return parsed


def _raise_business_from_domain_error(exc: IamDomainError) -> None:
    """Convert IAM domain error to BusinessError."""
    raise BusinessError(exc.message, exc.code, exc.data) from exc


def _normalize_data_scope_for_storage(data_scope: str | None) -> str | None:
    """Convert canonical data-scope values to storage-compatible aliases."""
    return to_storage_data_scope(data_scope)


class UserRoleGrantService:
    """User-role grant service."""

    @classmethod
    async def bind_user_role(cls, *, data: dict[str, Any], operator: Any = None, operator_id: int | None) -> dict[str, Any]:
        """Bind role to user idempotently."""
        if not data.get("user_id") or not data.get("role_id"):
            raise BusinessError("user_id and role_id cannot be empty", 13011)

        validated_data = UserRoleValidator.validate_create(data)
        user_id = _to_positive_int(validated_data.get("user_id"), "user_id")
        role_id = _to_positive_int(validated_data.get("role_id"), "role_id")

        if operator is not None:
            await GrantPolicy.ensure_can_bind_user_role(user_id=user_id, role_id=role_id, operator=operator)

        existed = await UserRoleGrantRepository.get_existing(user_id=user_id, role_id=role_id)
        if existed:
            return {"id": existed.id}

        created = await UserRoleGrantRepository.create(user_id=user_id, role_id=role_id, operator_id=operator_id)
        AuthorizationContextService.invalidate_user(user_id)
        return created

    @classmethod
    async def unbind_user_role(cls, *, data: dict[str, Any], operator: Any = None) -> None:
        """Unbind role from user idempotently."""
        if not data.get("user_id") or not data.get("role_id"):
            raise BusinessError("user_id and role_id cannot be empty", 13011)

        user_id = _to_positive_int(data.get("user_id"), "user_id")
        role_id = _to_positive_int(data.get("role_id"), "role_id")

        if operator is not None:
            await GrantPolicy.ensure_can_bind_user_role(user_id=user_id, role_id=role_id, operator=operator)

        item = await UserRoleGrantRepository.get_existing(user_id=user_id, role_id=role_id)
        if item:
            await UserRoleGrantRepository.delete(item)
            AuthorizationContextService.invalidate_user(user_id)


class RolePermissionGrantService:
    """Role-permission grant service."""

    @classmethod
    async def grant_role_permission(cls, *, data: dict[str, Any], operator: Any = None, operator_id: int | None) -> dict[str, Any]:
        """Grant permission to role idempotently."""
        if not data.get("role_id") or not data.get("permission_id"):
            raise BusinessError("role_id and permission_id cannot be empty", 13012)

        validated_data = RolePermissionValidator.validate_create(data)
        role_id = _to_positive_int(validated_data.get("role_id"), "role_id")
        permission_id = _to_positive_int(validated_data.get("permission_id"), "permission_id")
        data_scope = _normalize_data_scope_for_storage(validated_data.get("data_scope"))

        if operator is not None:
            await GrantPolicy.ensure_can_operate_role(role_id=role_id, operator=operator)

        existed = await RolePermissionGrantRepository.get_existing(role_id=role_id, permission_id=permission_id)
        if existed:
            return {"id": existed.id}

        permission = await GrantPermissionRepository.get_permission_by_id(permission_id)
        try:
            DataScopePolicy.ensure_grant_data_scope_by_permission_type(
                permission_type=getattr(permission, "permission_type", None),
                data_scope=data_scope,
                role_permission=True,
            )
        except IamDomainError as exc:
            _raise_business_from_domain_error(exc)

        created = await RolePermissionGrantRepository.create(
            role_id=role_id,
            permission_id=permission_id,
            data_scope=data_scope,
            expired_at=validated_data.get("expired_at"),
            operator_id=operator_id,
        )
        AuthorizationContextService.invalidate_all()
        return created

    @classmethod
    async def revoke_role_permission(cls, *, data: dict[str, Any], operator: Any = None) -> None:
        """Revoke permission from role idempotently."""
        if not data.get("role_id") or not data.get("permission_id"):
            raise BusinessError("role_id and permission_id cannot be empty", 13012)

        role_id = _to_positive_int(data.get("role_id"), "role_id")
        permission_id = _to_positive_int(data.get("permission_id"), "permission_id")

        if operator is not None:
            await GrantPolicy.ensure_can_operate_role(role_id=role_id, operator=operator)

        item = await RolePermissionGrantRepository.get_existing(role_id=role_id, permission_id=permission_id)
        if item:
            await RolePermissionGrantRepository.delete(item)
            AuthorizationContextService.invalidate_all()


class UserPermissionGrantService:
    """User-permission grant service."""

    @classmethod
    async def grant_user_permission(cls, *, data: dict[str, Any], operator: Any = None, operator_id: int | None) -> dict[str, Any]:
        """Grant permission to user idempotently."""
        if not data.get("user_id") or not data.get("permission_id"):
            raise BusinessError("user_id and permission_id cannot be empty", 13013)

        validated_data = UserPermissionValidator.validate_create(data)
        user_id = _to_positive_int(validated_data.get("user_id"), "user_id")
        permission_id = _to_positive_int(validated_data.get("permission_id"), "permission_id")
        effect = validated_data.get("effect")
        data_scope = _normalize_data_scope_for_storage(validated_data.get("data_scope"))

        if operator is not None:
            await GrantPolicy.ensure_can_operate_user(user_id=user_id, operator=operator)

        existed = await UserPermissionGrantRepository.get_existing(user_id=user_id, permission_id=permission_id)
        if existed:
            return {"id": existed.id}

        permission = await GrantPermissionRepository.get_permission_by_id(permission_id)
        try:
            DataScopePolicy.ensure_grant_data_scope_by_permission_type(
                permission_type=getattr(permission, "permission_type", None),
                data_scope=data_scope,
                effect=effect,
                role_permission=False,
            )
        except IamDomainError as exc:
            _raise_business_from_domain_error(exc)

        created = await UserPermissionGrantRepository.create(
            user_id=user_id,
            permission_id=permission_id,
            effect=effect,
            data_scope=data_scope,
            expired_at=validated_data.get("expired_at"),
            operator_id=operator_id,
        )
        AuthorizationContextService.invalidate_user(user_id)
        return created

    @classmethod
    async def revoke_user_permission(cls, *, data: dict[str, Any], operator: Any = None) -> None:
        """Revoke permission from user idempotently."""
        if not data.get("user_id") or not data.get("permission_id"):
            raise BusinessError("user_id and permission_id cannot be empty", 13013)

        user_id = _to_positive_int(data.get("user_id"), "user_id")
        permission_id = _to_positive_int(data.get("permission_id"), "permission_id")

        if operator is not None:
            await GrantPolicy.ensure_can_operate_user(user_id=user_id, operator=operator)

        item = await UserPermissionGrantRepository.get_existing(user_id=user_id, permission_id=permission_id)
        if item:
            await UserPermissionGrantRepository.delete(item)
            AuthorizationContextService.invalidate_user(user_id)


class DepartmentPermissionGrantService:
    """Department-permission grant service."""

    @classmethod
    async def grant_department_permission(cls, *, data: dict[str, Any], operator: Any = None, operator_id: int | None) -> dict[str, Any]:
        """Grant permission to department idempotently."""
        if not data.get("department_id") or not data.get("permission_id"):
            raise BusinessError("department_id and permission_id cannot be empty", 13014)

        validated_data = DepartmentPermissionValidator.validate_create(data)
        department_id = _to_positive_int(validated_data.get("department_id"), "department_id")
        permission_id = _to_positive_int(validated_data.get("permission_id"), "permission_id")
        effect = validated_data.get("effect")
        data_scope = _normalize_data_scope_for_storage(validated_data.get("data_scope"))

        if operator is not None:
            await GrantPolicy.ensure_can_operate_department(department_id=department_id, operator=operator)

        existed = await DepartmentPermissionGrantRepository.get_existing(department_id=department_id, permission_id=permission_id)
        if existed:
            return {"id": existed.id}

        permission = await GrantPermissionRepository.get_permission_by_id(permission_id)
        try:
            DataScopePolicy.ensure_grant_data_scope_by_permission_type(
                permission_type=getattr(permission, "permission_type", None),
                data_scope=data_scope,
                effect=effect,
                role_permission=False,
            )
        except IamDomainError as exc:
            _raise_business_from_domain_error(exc)

        created = await DepartmentPermissionGrantRepository.create(
            department_id=department_id,
            permission_id=permission_id,
            effect=effect,
            data_scope=data_scope,
            expired_at=validated_data.get("expired_at"),
            operator_id=operator_id,
        )
        AuthorizationContextService.invalidate_all()
        return created

    @classmethod
    async def revoke_department_permission(cls, *, data: dict[str, Any], operator: Any = None) -> None:
        """Revoke permission from department idempotently."""
        if not data.get("department_id") or not data.get("permission_id"):
            raise BusinessError("department_id and permission_id cannot be empty", 13014)

        department_id = _to_positive_int(data.get("department_id"), "department_id")
        permission_id = _to_positive_int(data.get("permission_id"), "permission_id")

        if operator is not None:
            await GrantPolicy.ensure_can_operate_department(department_id=department_id, operator=operator)

        item = await DepartmentPermissionGrantRepository.get_existing(department_id=department_id, permission_id=permission_id)
        if item:
            await DepartmentPermissionGrantRepository.delete(item)
            AuthorizationContextService.invalidate_all()


class SubsidiaryPermissionGrantService:
    """Subsidiary-permission grant service."""

    @classmethod
    async def grant_subsidiary_permission(cls, *, data: dict[str, Any], operator: Any = None, operator_id: int | None) -> dict[str, Any]:
        """Grant permission to subsidiary idempotently."""
        if not data.get("subsidiary_id") or not data.get("permission_id"):
            raise BusinessError("subsidiary_id and permission_id cannot be empty", 13015)

        validated_data = SubsidiaryPermissionValidator.validate_create(data)
        subsidiary_id = _to_positive_int(validated_data.get("subsidiary_id"), "subsidiary_id")
        permission_id = _to_positive_int(validated_data.get("permission_id"), "permission_id")
        effect = validated_data.get("effect")
        data_scope = _normalize_data_scope_for_storage(validated_data.get("data_scope"))

        if operator is not None:
            await GrantPolicy.ensure_can_operate_subsidiary(subsidiary_id=subsidiary_id, operator=operator)

        existed = await SubsidiaryPermissionGrantRepository.get_existing(subsidiary_id=subsidiary_id, permission_id=permission_id)
        if existed:
            return {"id": existed.id}

        permission = await GrantPermissionRepository.get_permission_by_id(permission_id)
        try:
            DataScopePolicy.ensure_grant_data_scope_by_permission_type(
                permission_type=getattr(permission, "permission_type", None),
                data_scope=data_scope,
                effect=effect,
                role_permission=False,
            )
        except IamDomainError as exc:
            _raise_business_from_domain_error(exc)

        created = await SubsidiaryPermissionGrantRepository.create(
            subsidiary_id=subsidiary_id,
            permission_id=permission_id,
            effect=effect,
            data_scope=data_scope,
            expired_at=validated_data.get("expired_at"),
            operator_id=operator_id,
        )
        AuthorizationContextService.invalidate_all()
        return created

    @classmethod
    async def revoke_subsidiary_permission(cls, *, data: dict[str, Any], operator: Any = None) -> None:
        """Revoke permission from subsidiary idempotently."""
        if not data.get("subsidiary_id") or not data.get("permission_id"):
            raise BusinessError("subsidiary_id and permission_id cannot be empty", 13015)

        subsidiary_id = _to_positive_int(data.get("subsidiary_id"), "subsidiary_id")
        permission_id = _to_positive_int(data.get("permission_id"), "permission_id")

        if operator is not None:
            await GrantPolicy.ensure_can_operate_subsidiary(subsidiary_id=subsidiary_id, operator=operator)

        item = await SubsidiaryPermissionGrantRepository.get_existing(subsidiary_id=subsidiary_id, permission_id=permission_id)
        if item:
            await SubsidiaryPermissionGrantRepository.delete(item)
            AuthorizationContextService.invalidate_all()
