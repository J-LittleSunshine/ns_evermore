# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from django.db import IntegrityError
from django.utils import timezone

from ns_common.error_codes import NsErrorCode
from ..db.routers import AppDatabaseRouter
from ..exceptions import BusinessError, ValidateError

if TYPE_CHECKING:
    pass


class CrudRepository:
    """Common async CRUD repository for Django models."""

    @staticmethod
    def ensure_model_class(model_class: Any) -> None:
        if model_class is None:
            raise BusinessError("model_class is not configured", NsErrorCode.MODEL_CLASS_NOT_CONFIGURED)

    @classmethod
    def resolve_db_alias(cls, model_class: Any, db_alias: str | None = None) -> str:
        if db_alias:
            return db_alias

        cls.ensure_model_class(model_class)

        # noinspection PyProtectedMember
        app_label = str(model_class._meta.app_label)
        target_db = AppDatabaseRouter.get_target_db(app_label)
        if target_db:
            return target_db

        return AppDatabaseRouter.INFRA_DEFAULT_DB_ALIAS

    @classmethod
    def build_queryset(cls, model_class: Any, *, db_alias: str | None = None, order_by: tuple[str, ...] = ("-id",)) -> Any:
        cls.ensure_model_class(model_class)
        resolved_db_alias = cls.resolve_db_alias(model_class=model_class, db_alias=db_alias)
        queryset = model_class.objects.using(resolved_db_alias).all()
        if order_by:
            queryset = queryset.order_by(*order_by)
        return queryset

    @classmethod
    async def list_items(cls, model_class: Any, fields: tuple[str, ...], page: int | str | None, page_size: int | str | None, tenant_filter: dict[str, Any] | None = None, *, db_alias: str | None = None, order_by: tuple[str, ...] = ("-id",)) -> dict[str, Any]:
        cls.ensure_model_class(model_class)
        normalized_page, normalized_page_size = cls.normalize_page(page, page_size)
        queryset = cls.build_queryset(model_class=model_class, db_alias=db_alias, order_by=order_by)

        if tenant_filter:
            queryset = queryset.filter(**tenant_filter)

        offset: int = (normalized_page - 1) * normalized_page_size
        total: int = await queryset.acount()

        rows: list[dict[str, Any]] = []
        async for item in queryset[offset: offset + normalized_page_size].aiterator():
            rows.append(cls.serialize(item, fields))

        return {"items": rows, "pagination": {"page": normalized_page, "page_size": normalized_page_size, "total": total, "total_pages": (total + normalized_page_size - 1) // normalized_page_size}}

    @classmethod
    async def get_by_id(cls, model_class: Any, item_id: int, *, db_alias: str | None = None) -> Any | None:
        resolved_db_alias = cls.resolve_db_alias(model_class=model_class, db_alias=db_alias)
        return await model_class.objects.using(resolved_db_alias).filter(id=item_id).afirst()

    @classmethod
    def normalize_item_id(cls, item_id: Any) -> int:
        if item_id is None or item_id == "":
            raise BusinessError("id cannot be empty", NsErrorCode.ID_EMPTY)

        try:
            normalized_item_id = int(item_id)
        except (TypeError, ValueError) as exc:
            raise BusinessError("id has invalid format", NsErrorCode.INVALID_VALUE) from exc

        if normalized_item_id <= 0:
            raise BusinessError("id must be positive", NsErrorCode.INVALID_VALUE)

        return normalized_item_id

    @classmethod
    async def get_required_by_id(cls, model_class: Any, item_id: int | str | None, tenant_filter: dict[str, Any] | None = None, *, db_alias: str | None = None) -> Any:
        cls.ensure_model_class(model_class)
        normalized_item_id = cls.normalize_item_id(item_id)
        resolved_db_alias = cls.resolve_db_alias(model_class=model_class, db_alias=db_alias)

        queryset = model_class.objects.using(resolved_db_alias).filter(id=normalized_item_id)

        if tenant_filter:
            queryset = queryset.filter(**tenant_filter)

        item = await queryset.afirst()
        if not item:
            raise BusinessError("Data not found", NsErrorCode.DATA_NOT_FOUND)

        return item

    @classmethod
    async def detail_item(cls, model_class: Any, item_id: int | str | None, fields: tuple[str, ...], tenant_filter: dict[str, Any] | None = None, *, db_alias: str | None = None) -> dict[str, Any]:
        item = await cls.get_required_by_id(model_class=model_class, item_id=item_id, tenant_filter=tenant_filter, db_alias=db_alias)
        return cls.serialize(item, fields)

    @classmethod
    async def create_item(cls, model_class: Any, data: dict[str, Any], *, db_alias: str | None = None) -> Any:
        resolved_db_alias = cls.resolve_db_alias(model_class=model_class, db_alias=db_alias)
        try:
            return await model_class.objects.using(resolved_db_alias).acreate(**data)
        except IntegrityError as exc:
            raise BusinessError(f"Data creation failed: {exc}", NsErrorCode.DATA_CREATION_FAILED) from exc

    @classmethod
    async def create_item_with_audit(cls, model_class: Any, data: dict[str, Any], operator_id: int | None = None, tenant_create_values: dict[str, Any] | None = None, *, db_alias: str | None = None) -> dict[str, Any]:
        cls.ensure_model_class(model_class)

        final_data = data
        if tenant_create_values:
            final_data = {**data, **tenant_create_values}

        create_data = cls.fill_create_audit_fields(model_class=model_class, data=final_data, operator_id=operator_id)
        item = await cls.create_item(model_class=model_class, data=create_data, db_alias=db_alias)
        return {"id": item.id}

    @classmethod
    async def update_item(cls, instance: Any, data: dict[str, Any], *, db_alias: str | None = None) -> None:
        if not data:
            return

        for field, value in data.items():
            setattr(instance, field, value)

        # noinspection PyProtectedMember
        resolved_db_alias = db_alias or instance._state.db or cls.resolve_db_alias(model_class=instance.__class__)

        try:
            await instance.asave(using=resolved_db_alias, update_fields=list(data.keys()))
        except IntegrityError as exc:
            raise BusinessError(f"Data update failed: {exc}", NsErrorCode.DATA_UPDATE_FAILED) from exc

    @classmethod
    async def update_item_with_audit(cls, model_class: Any, item_id: int | str | None, data: dict[str, Any], operator_id: int | None = None, tenant_filter: dict[str, Any] | None = None, *, db_alias: str | None = None) -> None:
        item = await cls.get_required_by_id(model_class=model_class, item_id=item_id, tenant_filter=tenant_filter, db_alias=db_alias)
        update_data = cls.fill_update_audit_fields(model_class=model_class, data=data, operator_id=operator_id)
        await cls.update_item(instance=item, data=update_data, db_alias=db_alias)

    @classmethod
    async def delete_item(cls, instance: Any, *, db_alias: str | None = None) -> None:
        # noinspection PyProtectedMember
        resolved_db_alias = db_alias or instance._state.db or cls.resolve_db_alias(model_class=instance.__class__)
        await instance.adelete(using=resolved_db_alias)

    @classmethod
    async def delete_item_by_id(cls, model_class: Any, item_id: int | str | None, tenant_filter: dict[str, Any] | None = None, *, db_alias: str | None = None) -> None:
        item = await cls.get_required_by_id(model_class=model_class, item_id=item_id, tenant_filter=tenant_filter, db_alias=db_alias)
        await cls.delete_item(item, db_alias=db_alias)

    @staticmethod
    def normalize_page(page: int | str | None, page_size: int | str | None) -> tuple[int, int]:
        try:
            normalized_page = max(int(page or 1), 1)
            normalized_page_size = min(max(int(page_size or 20), 1), 100)
        except (TypeError, ValueError) as exc:
            raise ValidateError("Invalid pagination parameters", NsErrorCode.INVALID_PAGINATION_PARAMETERS) from exc

        return normalized_page, normalized_page_size

    @classmethod
    def fill_create_audit_fields(cls, model_class: Any, data: dict[str, Any], operator_id: int | None = None) -> dict[str, Any]:
        result = data.copy()
        now = timezone.now()
        field_names = cls.get_model_field_names(model_class)

        if "created_by" in field_names:
            result.setdefault("created_by", operator_id)

        if "updated_by" in field_names:
            result.setdefault("updated_by", operator_id)

        if "created_at" in field_names:
            result.setdefault("created_at", now)

        if "updated_at" in field_names:
            result.setdefault("updated_at", now)

        return result

    @classmethod
    def fill_update_audit_fields(cls, model_class: Any, data: dict[str, Any], operator_id: int | None = None) -> dict[str, Any]:
        result = data.copy()
        field_names = cls.get_model_field_names(model_class)

        if "updated_by" in field_names:
            result["updated_by"] = operator_id

        if "updated_at" in field_names:
            result["updated_at"] = timezone.now()

        return result

    @staticmethod
    def serialize(instance: Any, fields: tuple[str, ...]) -> dict[str, Any]:
        result: dict[str, Any] = {}

        for field in fields:
            value = getattr(instance, field)
            if isinstance(value, (datetime, date)):
                value = value.isoformat()
            result[field] = value

        return result

    @staticmethod
    def get_model_field_names(model_class: Any) -> set[str]:
        # noinspection PyProtectedMember
        return {field.name for field in model_class._meta.fields}
