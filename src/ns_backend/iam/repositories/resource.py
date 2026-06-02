# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ns_backend.backend.common import BaseRepository
from ns_backend.iam.models import IamResource, IamResourceAction

if TYPE_CHECKING:
    pass


class ResourceRepository:
    """Repository for IAM resource and resource-action registration tables."""

    RESOURCE_FIELDS: tuple[str, ...] = (
        "id",
        "resource_type",
        "resource_name",
        "module_code",
        "status",
        "created_at",
        "updated_at",
    )

    RESOURCE_ACTION_FIELDS: tuple[str, ...] = (
        "id",
        "resource_id",
        "action_code",
        "action_name",
        "status",
        "created_at",
        "updated_at",
    )

    @staticmethod
    async def get_resource_by_type(resource_type: str) -> IamResource | None:
        """Load one resource row by resource_type."""
        db_alias: str = BaseRepository.resolve_db_alias(model_class=IamResource)
        return await IamResource.objects.using(db_alias).filter(resource_type=resource_type).afirst()

    @staticmethod
    async def create_resource(*, resource_type: str, resource_name: str, module_code: str, status: int, operator_id: int | None) -> dict[str, Any]:
        """Create one resource registration row."""
        return await BaseRepository.create_item_with_audit(
            model_class=IamResource,
            data={
                "resource_type": resource_type,
                "resource_name": resource_name,
                "module_code": module_code,
                "status": status,
            },
            operator_id=operator_id,
        )

    @staticmethod
    async def update_resource(*, item: IamResource, resource_name: str, module_code: str, status: int, operator_id: int | None) -> None:
        """Update one resource registration row."""
        update_data: dict[str, Any] = BaseRepository.fill_update_audit_fields(
            model_class=IamResource,
            data={
                "resource_name": resource_name,
                "module_code": module_code,
                "status": status,
            },
            operator_id=operator_id,
        )
        await BaseRepository.update_item(instance=item, data=update_data)

    @classmethod
    async def list_resources(cls, *, page: int | str | None, page_size: int | str | None, filters: dict[str, Any] | None) -> dict[str, Any]:
        """List resource registration rows."""
        return await BaseRepository.list_items(
            model_class=IamResource,
            fields=cls.RESOURCE_FIELDS,
            page=page,
            page_size=page_size,
            filters=filters,
            order_by=("module_code", "resource_type", "id"),
        )

    @staticmethod
    async def get_resource_action(*, resource_id: int, action_code: str) -> IamResourceAction | None:
        """Load one resource action row by unique key."""
        db_alias: str = BaseRepository.resolve_db_alias(model_class=IamResourceAction)
        return await IamResourceAction.objects.using(db_alias).filter(resource_id=resource_id, action_code=action_code).afirst()

    @staticmethod
    async def create_resource_action(*, resource_id: int, action_code: str, action_name: str, status: int, operator_id: int | None) -> dict[str, Any]:
        """Create one resource action row."""
        return await BaseRepository.create_item_with_audit(
            model_class=IamResourceAction,
            data={
                "resource_id": resource_id,
                "action_code": action_code,
                "action_name": action_name,
                "status": status,
            },
            operator_id=operator_id,
        )

    @staticmethod
    async def update_resource_action(*, item: IamResourceAction, action_name: str, status: int, operator_id: int | None) -> None:
        """Update one resource action row."""
        update_data: dict[str, Any] = BaseRepository.fill_update_audit_fields(
            model_class=IamResourceAction,
            data={
                "action_name": action_name,
                "status": status,
            },
            operator_id=operator_id,
        )
        await BaseRepository.update_item(instance=item, data=update_data)

    @staticmethod
    async def list_actions_by_resource_ids(resource_ids: list[int]) -> list[dict[str, Any]]:
        """List resource actions grouped by resource ids."""
        if not resource_ids:
            return []

        db_alias: str = BaseRepository.resolve_db_alias(model_class=IamResourceAction)
        queryset = IamResourceAction.objects.using(db_alias).filter(resource_id__in=resource_ids).order_by("resource_id", "action_code").values(
            "id",
            "resource_id",
            "action_code",
            "action_name",
            "status",
        )
        return [item async for item in queryset]

