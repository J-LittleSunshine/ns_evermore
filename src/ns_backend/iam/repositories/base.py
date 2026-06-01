# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ns_backend.backend.common import BaseRepository

if TYPE_CHECKING:
    pass


class IamBaseRepository:
    """Repository facade for IAM base resource operations.

    This repository owns all calls to backend BaseRepository so IAM services do
    not call persistence helpers directly.
    """

    @staticmethod
    async def list_items(
            *,
            model_class: Any,
            fields: tuple[str, ...],
            page: int | str | None,
            page_size: int | str | None,
            tenant_filter: dict[str, Any] | None = None,
            filters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """List IAM model rows with pagination."""
        return await BaseRepository.list_items(
            model_class=model_class,
            fields=fields,
            page=page,
            page_size=page_size,
            tenant_filter=tenant_filter,
            filters=filters,
        )

    @staticmethod
    async def detail_item(*, model_class: Any, item_id: int | str | None, fields: tuple[str, ...], tenant_filter: dict[str, Any] | None = None) -> dict[str, Any]:
        """Load one IAM model row detail."""
        return await BaseRepository.detail_item(model_class=model_class, item_id=item_id, fields=fields, tenant_filter=tenant_filter)

    @staticmethod
    async def create_item_with_audit(*, model_class: Any, data: dict[str, Any], operator_id: int | None = None, tenant_create_values: dict[str, Any] | None = None) -> dict[str, Any]:
        """Create one IAM model row with audit fields."""
        return await BaseRepository.create_item_with_audit(model_class=model_class, data=data, operator_id=operator_id, tenant_create_values=tenant_create_values)

    @staticmethod
    async def update_item_with_audit(*, model_class: Any, item_id: int | str | None, data: dict[str, Any], operator_id: int | None = None, tenant_filter: dict[str, Any] | None = None) -> None:
        """Update one IAM model row with audit fields."""
        await BaseRepository.update_item_with_audit(model_class=model_class, item_id=item_id, data=data, operator_id=operator_id, tenant_filter=tenant_filter)

    @staticmethod
    async def delete_item_by_id(*, model_class: Any, item_id: int | str | None, tenant_filter: dict[str, Any] | None = None) -> None:
        """Delete one IAM model row by id."""
        await BaseRepository.delete_item_by_id(model_class=model_class, item_id=item_id, tenant_filter=tenant_filter)

    @staticmethod
    async def get_required_by_id(*, model_class: Any, item_id: int | str | None, tenant_filter: dict[str, Any] | None = None) -> Any:
        """Load one required IAM model row by id."""
        return await BaseRepository.get_required_by_id(model_class=model_class, item_id=item_id, tenant_filter=tenant_filter)

    @staticmethod
    async def update_item(*, instance: Any, data: dict[str, Any]) -> None:
        """Update one existing IAM model instance."""
        await BaseRepository.update_item(instance=instance, data=data)

    @staticmethod
    async def delete_item(instance: Any) -> None:
        """Delete one existing IAM model instance."""
        await BaseRepository.delete_item(instance)
