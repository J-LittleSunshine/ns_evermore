# -*- coding: utf-8 -*-
from __future__ import annotations

from django.db import IntegrityError

from iam.constants import IAM_DB_ALIAS
from ns_common.error_codes import NsErrorCode
from iam.models import IamPermission
from ns_backend.exceptions import BusinessError


class PermissionSyncRepository:
    @staticmethod
    async def get_permissions_by_codes(codes: list[str]) -> dict[str, IamPermission]:
        if not codes:
            return {}

        result: dict[str, IamPermission] = {}
        queryset = IamPermission.objects.using(IAM_DB_ALIAS).filter(
            permission_code__in=codes,
        )
        async for item in queryset:
            result[item.permission_code] = item
        return result

    @classmethod
    async def bulk_get_parent_ids(cls, parent_codes: list[str]) -> dict[str, int]:
        permissions = await cls.get_permissions_by_codes(parent_codes)
        return {
            code: permission.id
            for code, permission in permissions.items()
        }

    @staticmethod
    async def create_permission(data: dict) -> IamPermission:
        try:
            return await IamPermission.objects.using(IAM_DB_ALIAS).acreate(**data)
        except IntegrityError as exc:
            raise BusinessError(f"Failed to create permission: {exc}", NsErrorCode.PERMISSION_CREATE_FAILED)

    @staticmethod
    async def update_permission(permission: IamPermission, data: dict) -> None:
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
            await permission.asave(
                using=IAM_DB_ALIAS,
                update_fields=update_fields,
            )
        except IntegrityError as exc:
            raise BusinessError(f"Failed to update permission: {exc}", NsErrorCode.PERMISSION_UPDATE_FAILED)

    @staticmethod
    async def get_permission_by_code(code: str) -> IamPermission | None:
        return await IamPermission.objects.using(IAM_DB_ALIAS).filter(
            permission_code=code,
        ).afirst()


__all__ = ["PermissionSyncRepository"]

