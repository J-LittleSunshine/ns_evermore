# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    TYPE_CHECKING,
)

from asgiref.sync import sync_to_async
from django.db import (
    IntegrityError,
    transaction,
)
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.utils import timezone

from backend.common import BaseRepository
from ns_backend.iam.errors import (
    IamManagementPersistenceError,
    IamResourceInUseError,
)

if TYPE_CHECKING:
    pass


class IamManagementRepository(BaseRepository):
    @classmethod
    async def list_items(cls, *, model_class: Any, fields: tuple[str, ...], page: int, page_size: int, filters: dict[str, Any] | None = None, keyword_conditions: list[dict[str, Any]] | None = None, order_by: tuple[str, ...] = ("-id",)) -> dict[str, Any]:
        db_alias = cls.resolve_db_alias(model_class=model_class)

        return await sync_to_async(cls._list_items_sync, thread_sensitive=True)(
            model_class=model_class,
            fields=fields,
            page=page,
            page_size=page_size,
            filters=filters or {},
            keyword_conditions=keyword_conditions or [],
            order_by=order_by,
            db_alias=db_alias,
        )

    @classmethod
    def _list_items_sync(cls, *, model_class: Any, fields: tuple[str, ...], page: int, page_size: int, filters: dict[str, Any], keyword_conditions: list[dict[str, Any]], order_by: tuple[str, ...], db_alias: str) -> dict[str, Any]:
        queryset = model_class.objects.using(db_alias).all()

        if filters:
            queryset = queryset.filter(**filters)

        keyword_query = cls.build_keyword_query(keyword_conditions)
        if keyword_query is not None:
            queryset = queryset.filter(keyword_query)

        total = queryset.count()
        offset = (page - 1) * page_size
        rows = list(queryset.order_by(*order_by)[offset: offset + page_size])

        return {
            "items": [
                cls.serialize_instance(instance=row, fields=fields)
                for row in rows
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    @classmethod
    async def get_by_id(cls, *, model_class: Any, item_id: int) -> Any | None:
        db_alias = cls.resolve_db_alias(model_class=model_class)

        return await sync_to_async(cls._get_by_id_sync, thread_sensitive=True)(
            model_class=model_class,
            item_id=item_id,
            db_alias=db_alias,
        )

    @staticmethod
    def _get_by_id_sync(*, model_class: Any, item_id: int, db_alias: str) -> Any | None:
        return model_class.objects.using(db_alias).filter(id=item_id).first()

    @classmethod
    async def detail_item(cls, *, model_class: Any, item_id: int, fields: tuple[str, ...]) -> dict[str, Any] | None:
        db_alias = cls.resolve_db_alias(model_class=model_class)

        return await sync_to_async(cls._detail_item_sync, thread_sensitive=True)(
            model_class=model_class,
            item_id=item_id,
            fields=fields,
            db_alias=db_alias,
        )

    @classmethod
    def _detail_item_sync(cls, *, model_class: Any, item_id: int, fields: tuple[str, ...], db_alias: str) -> dict[str, Any] | None:
        instance = model_class.objects.using(db_alias).filter(id=item_id).first()

        if instance is None:
            return None

        return cls.serialize_instance(instance=instance, fields=fields)

    @classmethod
    async def exists_by_filters(cls, *, model_class: Any, filters: dict[str, Any], exclude_id: int | None = None) -> bool:
        db_alias = cls.resolve_db_alias(model_class=model_class)

        return await sync_to_async(cls._exists_by_filters_sync, thread_sensitive=True)(
            model_class=model_class,
            filters=filters,
            exclude_id=exclude_id,
            db_alias=db_alias,
        )

    @staticmethod
    def _exists_by_filters_sync(*, model_class: Any, filters: dict[str, Any], exclude_id: int | None, db_alias: str) -> bool:
        queryset = model_class.objects.using(db_alias).filter(**filters)

        if exclude_id is not None:
            queryset = queryset.exclude(id=exclude_id)

        return queryset.exists()

    @classmethod
    async def create_item(cls, *, model_class: Any, data: dict[str, Any], fields: tuple[str, ...], operator_id: int | None = None) -> dict[str, Any]:
        db_alias = cls.resolve_db_alias(model_class=model_class)

        return await sync_to_async(cls._create_item_sync, thread_sensitive=True)(
            model_class=model_class,
            data=data,
            fields=fields,
            operator_id=operator_id,
            db_alias=db_alias,
        )

    @classmethod
    def _create_item_sync(cls, *, model_class: Any, data: dict[str, Any], fields: tuple[str, ...], operator_id: int | None, db_alias: str) -> dict[str, Any]:
        now = timezone.now()
        create_data = dict(data)
        create_data["created_by"] = operator_id
        create_data["updated_by"] = operator_id
        create_data["created_at"] = now
        create_data["updated_at"] = now

        try:
            with transaction.atomic(using=db_alias):
                instance = model_class.objects.using(db_alias).create(**create_data)
        except IntegrityError as exc:
            raise IamManagementPersistenceError("Failed to create IAM resource.",
                details={
                    "model": model_class.__name__,
                },
            ) from exc

        return cls.serialize_instance(instance=instance, fields=fields)

    @classmethod
    async def update_item(cls, *, model_class: Any, item_id: int, data: dict[str, Any], fields: tuple[str, ...], operator_id: int | None = None) -> dict[str, Any] | None:
        db_alias = cls.resolve_db_alias(model_class=model_class)

        return await sync_to_async(cls._update_item_sync, thread_sensitive=True)(
            model_class=model_class,
            item_id=item_id,
            data=data,
            fields=fields,
            operator_id=operator_id,
            db_alias=db_alias,
        )

    @classmethod
    def _update_item_sync(cls, *, model_class: Any, item_id: int, data: dict[str, Any], fields: tuple[str, ...], operator_id: int | None, db_alias: str) -> dict[str, Any] | None:
        now = timezone.now()

        try:
            with transaction.atomic(using=db_alias):
                instance = model_class.objects.using(db_alias).select_for_update().filter(id=item_id).first()

                if instance is None:
                    return None

                update_fields: list[str] = []

                for field, value in data.items():
                    setattr(instance, field, value)
                    update_fields.append(field)

                instance.updated_by = operator_id
                instance.updated_at = now
                update_fields.extend([
                    "updated_by",
                    "updated_at",
                ]
                )

                instance.save(
                    using=db_alias,
                    update_fields=update_fields,
                )
        except IntegrityError as exc:
            raise IamManagementPersistenceError("Failed to update IAM resource.",
                details={
                    "model": model_class.__name__,
                    "id": item_id,
                },
            ) from exc

        return cls.serialize_instance(instance=instance, fields=fields)

    @classmethod
    async def delete_item(cls, *, model_class: Any, item_id: int) -> bool:
        db_alias = cls.resolve_db_alias(model_class=model_class)

        return await sync_to_async(cls._delete_item_sync, thread_sensitive=True)(
            model_class=model_class,
            item_id=item_id,
            db_alias=db_alias,
        )

    @staticmethod
    def _delete_item_sync(*, model_class: Any, item_id: int, db_alias: str) -> bool:
        try:
            with transaction.atomic(using=db_alias):
                instance = model_class.objects.using(db_alias).select_for_update().filter(id=item_id).first()

                if instance is None:
                    return False

                instance.delete(using=db_alias)
        except (ProtectedError, IntegrityError) as exc:
            raise IamResourceInUseError(
                details={
                    "model": model_class.__name__,
                    "id": item_id,
                },
            ) from exc

        return True

    @staticmethod
    def build_keyword_query(keyword_conditions: list[dict[str, Any]]) -> Q | None:
        if not keyword_conditions:
            return None

        query = Q()

        for condition in keyword_conditions:
            query |= Q(**condition)

        return query

    @staticmethod
    def serialize_instance(*, instance: Any, fields: tuple[str, ...]) -> dict[str, Any]:
        data: dict[str, Any] = {}

        for field in fields:
            value = getattr(instance, field, None)

            if hasattr(value, "isoformat"):
                value = value.isoformat()

            data[field] = value

        return data
