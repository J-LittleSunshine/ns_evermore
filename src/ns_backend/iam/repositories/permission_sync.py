# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db import IntegrityError

from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.models import IamPermission
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


class PermissionSyncRepository:
    """Repository for iam_permission synchronization."""

    @staticmethod
    async def get_permissions_by_codes(codes: list[str]) -> dict[str, IamPermission]:
        """Load permissions by permission_code."""
        if not codes:
            return {}

        result: dict[str, IamPermission] = {}
        queryset = IamPermission.objects.filter(permission_code__in=codes)

        async for item in queryset:
            result[item.permission_code] = item

        return result

    @classmethod
    async def bulk_get_parent_ids(cls, parent_codes: list[str]) -> dict[str, int]:
        """Load parent permission ids by parent codes."""
        permissions = await cls.get_permissions_by_codes(parent_codes)
        return {code: permission.id for code, permission in permissions.items()}

    @staticmethod
    async def create_permission(data: dict[str, Any]) -> IamPermission:
        """Create one permission."""
        try:
            return await IamPermission.objects.acreate(**data)
        except IntegrityError as exc:
            raise BusinessError(f"Failed to create permission: {exc}", NsErrorCode.PERMISSION_CREATE_FAILED) from exc

    @staticmethod
    async def update_permission(permission: IamPermission, data: dict[str, Any]) -> None:
        """Update one permission if fields changed."""
        update_fields: list[str] = []

        for field in (
            "permission_name",
            "permission_type",
            "parent_id",
            "status",
            "updated_by",
            "updated_at",
        ):
            if field not in data:
                continue

            value = data[field]
            if getattr(permission, field) == value:
                continue

            setattr(permission, field, value)
            update_fields.append(field)

        if not update_fields:
            return

        try:
            await permission.asave(update_fields=update_fields)
        except IntegrityError as exc:
            raise BusinessError(f"Failed to update permission: {exc}", NsErrorCode.PERMISSION_UPDATE_FAILED) from exc

    @staticmethod
    async def get_permission_by_code(code: str) -> IamPermission | None:
        """Load one permission by code."""
        return await IamPermission.objects.filter(permission_code=code).afirst()


__all__ = ["PermissionSyncRepository"]
