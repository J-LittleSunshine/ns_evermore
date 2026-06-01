# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ns_backend.backend.common import BaseRepository
from ns_backend.iam.models import (
    IamDepartment,
    IamDepartmentPermission,
    IamPermission,
    IamRole,
    IamRolePermission,
    IamSubsidiary,
    IamSubsidiaryPermission,
    IamUser,
    IamUserPermission,
    IamUserRole,
)
if TYPE_CHECKING:
    pass


class GrantPermissionRepository:
    """Repository for permission lookup used by grant services."""

    @staticmethod
    async def get_permission_by_id(permission_id: int) -> IamPermission | None:
        """Load permission by primary key."""
        return await IamPermission.objects.filter(id=permission_id).afirst()

class GrantBoundaryRepository:
    """Repository for IAM grant boundary lookup."""

    @staticmethod
    async def user_exists(user_id: int) -> bool:
        """Check whether user exists."""
        return await IamUser.objects.filter(id=user_id).aexists()

    @staticmethod
    async def get_user_company_id(user_id: int) -> int | None:
        """Load user company id."""
        item = await IamUser.objects.filter(id=user_id).values("company_id").afirst()
        return None if item is None else item.get("company_id")

    @staticmethod
    async def get_role_scope_and_company_id(role_id: int) -> tuple[str, int | None] | None:
        """Load role scope and company id."""
        item = await IamRole.objects.filter(id=role_id).values("role_scope", "company_id").afirst()
        if item is None:
            return None

        return item.get("role_scope"), item.get("company_id")

    @staticmethod
    async def get_department_company_id(department_id: int) -> int | None:
        """Load department company id."""
        item = await IamDepartment.objects.filter(id=department_id).values("company_id").afirst()
        return None if item is None else item.get("company_id")

    @staticmethod
    async def get_subsidiary_company_id(subsidiary_id: int) -> int | None:
        """Load subsidiary company id."""
        item = await IamSubsidiary.objects.filter(id=subsidiary_id).values("company_id").afirst()
        return None if item is None else item.get("company_id")

class UserRoleGrantRepository:
    """Repository for user-role grant records."""

    @staticmethod
    async def get_existing(*, user_id: int, role_id: int) -> IamUserRole | None:
        """Load existing user-role binding."""
        return await IamUserRole.objects.filter(user_id=user_id, role_id=role_id).afirst()

    @staticmethod
    async def create(*, user_id: int, role_id: int, operator_id: int | None) -> dict[str, Any]:
        """Create user-role binding."""
        return await BaseRepository.create_item_with_audit(
            model_class=IamUserRole,
            data={
                "user_id": user_id,
                "role_id": role_id,
            },
            operator_id=operator_id,
        )

    @staticmethod
    async def delete(item: IamUserRole) -> None:
        """Delete user-role binding."""
        await BaseRepository.delete_item(item)


class RolePermissionGrantRepository:
    """Repository for role-permission grant records."""

    @staticmethod
    async def get_existing(*, role_id: int, permission_id: int) -> IamRolePermission | None:
        """Load existing role-permission binding."""
        return await IamRolePermission.objects.filter(role_id=role_id, permission_id=permission_id).afirst()

    @staticmethod
    async def create(*, role_id: int, permission_id: int, data_scope: str | None, expired_at, operator_id: int | None) -> dict[str, Any]:
        """Create role-permission binding."""
        return await BaseRepository.create_item_with_audit(
            model_class=IamRolePermission,
            data={
                "role_id": role_id,
                "permission_id": permission_id,
                "data_scope": data_scope,
                "granted_by_id": operator_id,
                "expired_at": expired_at,
            },
            operator_id=operator_id,
        )

    @staticmethod
    async def delete(item: IamRolePermission) -> None:
        """Delete role-permission binding."""
        await BaseRepository.delete_item(item)


class UserPermissionGrantRepository:
    """Repository for user-permission grant records."""

    @staticmethod
    async def get_existing(*, user_id: int, permission_id: int) -> IamUserPermission | None:
        """Load existing user-permission binding."""
        return await IamUserPermission.objects.filter(user_id=user_id, permission_id=permission_id).afirst()

    @staticmethod
    async def create(*, user_id: int, permission_id: int, effect: str, data_scope: str | None, expired_at, operator_id: int | None) -> dict[str, Any]:
        """Create user-permission binding."""
        return await BaseRepository.create_item_with_audit(
            model_class=IamUserPermission,
            data={
                "user_id": user_id,
                "permission_id": permission_id,
                "effect": effect,
                "data_scope": data_scope,
                "granted_by_id": operator_id,
                "expired_at": expired_at,
            },
            operator_id=operator_id,
        )

    @staticmethod
    async def delete(item: IamUserPermission) -> None:
        """Delete user-permission binding."""
        await BaseRepository.delete_item(item)


class DepartmentPermissionGrantRepository:
    """Repository for department-permission grant records."""

    @staticmethod
    async def get_existing(*, department_id: int, permission_id: int) -> IamDepartmentPermission | None:
        """Load existing department-permission binding."""
        return await IamDepartmentPermission.objects.filter(department_id=department_id, permission_id=permission_id).afirst()

    @staticmethod
    async def create(*, department_id: int, permission_id: int, effect: str, data_scope: str | None, expired_at, operator_id: int | None) -> dict[str, Any]:
        """Create department-permission binding."""
        return await BaseRepository.create_item_with_audit(
            model_class=IamDepartmentPermission,
            data={
                "department_id": department_id,
                "permission_id": permission_id,
                "effect": effect,
                "data_scope": data_scope,
                "granted_by_id": operator_id,
                "expired_at": expired_at,
            },
            operator_id=operator_id,
        )

    @staticmethod
    async def delete(item: IamDepartmentPermission) -> None:
        """Delete department-permission binding."""
        await BaseRepository.delete_item(item)


class SubsidiaryPermissionGrantRepository:
    """Repository for subsidiary-permission grant records."""

    @staticmethod
    async def get_existing(*, subsidiary_id: int, permission_id: int) -> IamSubsidiaryPermission | None:
        """Load existing subsidiary-permission binding."""
        return await IamSubsidiaryPermission.objects.filter(subsidiary_id=subsidiary_id, permission_id=permission_id).afirst()

    @staticmethod
    async def create(*, subsidiary_id: int, permission_id: int, effect: str, data_scope: str | None, expired_at, operator_id: int | None) -> dict[str, Any]:
        """Create subsidiary-permission binding."""
        return await BaseRepository.create_item_with_audit(
            model_class=IamSubsidiaryPermission,
            data={
                "subsidiary_id": subsidiary_id,
                "permission_id": permission_id,
                "effect": effect,
                "data_scope": data_scope,
                "granted_by_id": operator_id,
                "expired_at": expired_at,
            },
            operator_id=operator_id,
        )

    @staticmethod
    async def delete(item: IamSubsidiaryPermission) -> None:
        """Delete subsidiary-permission binding."""
        await BaseRepository.delete_item(item)
