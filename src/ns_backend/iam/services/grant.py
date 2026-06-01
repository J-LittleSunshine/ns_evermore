# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ns_backend.backend.exceptions import BusinessError
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


class UserRoleGrantService:
    """User-role grant service."""

    @classmethod
    async def bind_user_role(cls, *, data: dict[str, Any], operator: Any = None, operator_id: int | None) -> dict[str, Any]:
        """Bind role to user idempotently."""
        validated_data = UserRoleValidator.validate_create(data)
        user_id = _to_positive_int(validated_data.get("user_id"), "user_id")
        role_id = _to_positive_int(validated_data.get("role_id"), "role_id")

        if operator is not None:
            await GrantPolicy.ensure_can_bind_user_role(user_id=user_id, role_id=role_id, operator=operator)

        existed = await UserRoleGrantRepository.get_existing(user_id=user_id, role_id=role_id)
        if existed:
            return {"id": existed.id}

        return await UserRoleGrantRepository.create(user_id=user_id, role_id=role_id, operator_id=operator_id)

    @classmethod
    async def unbind_user_role(cls, *, data: dict[str, Any], operator: Any = None) -> None:
        """Unbind role from user idempotently."""
        user_id = _to_positive_int(data.get("user_id"), "user_id")
        role_id = _to_positive_int(data.get("role_id"), "role_id")

        if operator is not None:
            await GrantPolicy.ensure_can_bind_user_role(user_id=user_id, role_id=role_id, operator=operator)

        item = await UserRoleGrantRepository.get_existing(user_id=user_id, role_id=role_id)
        if item:
            await UserRoleGrantRepository.delete(item)


class RolePermissionGrantService:
    """Role-permission grant service."""

    @classmethod
    async def grant_role_permission(cls, *, data: dict[str, Any], operator: Any = None, operator_id: int | None) -> dict[str, Any]:
        """Grant permission to role idempotently."""
        validated_data = RolePermissionValidator.validate_create(data)
        role_id = _to_positive_int(validated_data.get("role_id"), "role_id")
        permission_id = _to_positive_int(validated_data.get("permission_id"), "permission_id")
        data_scope = validated_data.get("data_scope")

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

        return await RolePermissionGrantRepository.create(
            role_id=role_id,
            permission_id=permission_id,
            data_scope=data_scope,
            expired_at=validated_data.get("expired_at"),
            operator_id=operator_id,
        )

    @classmethod
    async def revoke_role_permission(cls, *, data: dict[str, Any], operator: Any = None) -> None:
        """Revoke permission from role idempotently."""
        role_id = _to_positive_int(data.get("role_id"), "role_id")
        permission_id = _to_positive_int(data.get("permission_id"), "permission_id")

        if operator is not None:
            await GrantPolicy.ensure_can_operate_role(role_id=role_id, operator=operator)

        item = await RolePermissionGrantRepository.get_existing(role_id=role_id, permission_id=permission_id)
        if item:
            await RolePermissionGrantRepository.delete(item)


class UserPermissionGrantService:
    """User-permission grant service."""

    @classmethod
    async def grant_user_permission(cls, *, data: dict[str, Any], operator: Any = None, operator_id: int | None) -> dict[str, Any]:
        """Grant permission to user idempotently."""
        validated_data = UserPermissionValidator.validate_create(data)
        user_id = _to_positive_int(validated_data.get("user_id"), "user_id")
        permission_id = _to_positive_int(validated_data.get("permission_id"), "permission_id")
        effect = validated_data.get("effect")
        data_scope = validated_data.get("data_scope")

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

        return await UserPermissionGrantRepository.create(
            user_id=user_id,
            permission_id=permission_id,
            effect=effect,
            data_scope=data_scope,
            expired_at=validated_data.get("expired_at"),
            operator_id=operator_id,
        )

    @classmethod
    async def revoke_user_permission(cls, *, data: dict[str, Any], operator: Any = None) -> None:
        """Revoke permission from user idempotently."""
        user_id = _to_positive_int(data.get("user_id"), "user_id")
        permission_id = _to_positive_int(data.get("permission_id"), "permission_id")

        if operator is not None:
            await GrantPolicy.ensure_can_operate_user(user_id=user_id, operator=operator)

        item = await UserPermissionGrantRepository.get_existing(user_id=user_id, permission_id=permission_id)
        if item:
            await UserPermissionGrantRepository.delete(item)


class DepartmentPermissionGrantService:
    """Department-permission grant service."""

    @classmethod
    async def grant_department_permission(cls, *, data: dict[str, Any], operator: Any = None, operator_id: int | None) -> dict[str, Any]:
        """Grant permission to department idempotently."""
        validated_data = DepartmentPermissionValidator.validate_create(data)
        department_id = _to_positive_int(validated_data.get("department_id"), "department_id")
        permission_id = _to_positive_int(validated_data.get("permission_id"), "permission_id")
        effect = validated_data.get("effect")
        data_scope = validated_data.get("data_scope")

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

        return await DepartmentPermissionGrantRepository.create(
            department_id=department_id,
            permission_id=permission_id,
            effect=effect,
            data_scope=data_scope,
            expired_at=validated_data.get("expired_at"),
            operator_id=operator_id,
        )

    @classmethod
    async def revoke_department_permission(cls, *, data: dict[str, Any], operator: Any = None) -> None:
        """Revoke permission from department idempotently."""
        department_id = _to_positive_int(data.get("department_id"), "department_id")
        permission_id = _to_positive_int(data.get("permission_id"), "permission_id")

        if operator is not None:
            await GrantPolicy.ensure_can_operate_department(department_id=department_id, operator=operator)

        item = await DepartmentPermissionGrantRepository.get_existing(department_id=department_id, permission_id=permission_id)
        if item:
            await DepartmentPermissionGrantRepository.delete(item)


class SubsidiaryPermissionGrantService:
    """Subsidiary-permission grant service."""

    @classmethod
    async def grant_subsidiary_permission(cls, *, data: dict[str, Any], operator: Any = None, operator_id: int | None) -> dict[str, Any]:
        """Grant permission to subsidiary idempotently."""
        validated_data = SubsidiaryPermissionValidator.validate_create(data)
        subsidiary_id = _to_positive_int(validated_data.get("subsidiary_id"), "subsidiary_id")
        permission_id = _to_positive_int(validated_data.get("permission_id"), "permission_id")
        effect = validated_data.get("effect")
        data_scope = validated_data.get("data_scope")

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

        return await SubsidiaryPermissionGrantRepository.create(
            subsidiary_id=subsidiary_id,
            permission_id=permission_id,
            effect=effect,
            data_scope=data_scope,
            expired_at=validated_data.get("expired_at"),
            operator_id=operator_id,
        )

    @classmethod
    async def revoke_subsidiary_permission(cls, *, data: dict[str, Any], operator: Any = None) -> None:
        """Revoke permission from subsidiary idempotently."""
        subsidiary_id = _to_positive_int(data.get("subsidiary_id"), "subsidiary_id")
        permission_id = _to_positive_int(data.get("permission_id"), "permission_id")

        if operator is not None:
            await GrantPolicy.ensure_can_operate_subsidiary(subsidiary_id=subsidiary_id, operator=operator)

        item = await SubsidiaryPermissionGrantRepository.get_existing(subsidiary_id=subsidiary_id, permission_id=permission_id)
        if item:
            await SubsidiaryPermissionGrantRepository.delete(item)
