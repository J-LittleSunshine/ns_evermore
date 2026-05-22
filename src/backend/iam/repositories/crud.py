# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from django.db import IntegrityError
from django.utils import timezone

from iam.constants import IAM_DB_ALIAS
from iam.error_codes import IamErrorCode
from ns_backend.exceptions import BusinessError


class CrudRepository:
    """通用 CRUD 数据访问层。"""

    @staticmethod
    def ensure_model_class(model_class) -> None:
        """确保 View 已配置模型类。"""
        if model_class is None:
            raise BusinessError("model_class is not configured", IamErrorCode.MODEL_CLASS_NOT_CONFIGURED)

    @staticmethod
    def build_queryset(model_class):
        """构建基础查询集。"""
        return model_class.objects.using(IAM_DB_ALIAS).all().order_by("-id")

    @classmethod
    async def list_items(
        cls,
        model_class,
        fields: tuple[str, ...],
        page: int | str | None,
        page_size: int | str | None,
        tenant_filter: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """分页查询数据。"""
        cls.ensure_model_class(model_class)
        page, page_size = cls.normalize_page(page, page_size)
        queryset = cls.build_queryset(model_class)

        if tenant_filter:
            queryset = queryset.filter(**tenant_filter)

        offset = (page - 1) * page_size
        total = await queryset.acount()

        rows = []
        async for item in queryset[offset: offset + page_size].aiterator():
            rows.append(cls.serialize(item, fields))

        return {
            "items": rows,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
        }

    @staticmethod
    async def get_by_id(model_class, item_id: int):
        """按主键查询数据。"""
        return await model_class.objects.using(IAM_DB_ALIAS).filter(id=item_id).afirst()

    @classmethod
    async def get_required_by_id(
        cls,
        model_class,
        item_id: int,
        tenant_filter: dict[str, Any] | None = None,
    ):
        """按主键获取必需数据。"""
        cls.ensure_model_class(model_class)

        if not item_id:
            raise BusinessError("id cannot be empty", IamErrorCode.ID_EMPTY)

        queryset = model_class.objects.using(IAM_DB_ALIAS).filter(id=item_id)

        if tenant_filter:
            queryset = queryset.filter(**tenant_filter)

        item = await queryset.afirst()

        if not item:
            raise BusinessError("Data not found", IamErrorCode.DATA_NOT_FOUND)

        return item

    @classmethod
    async def detail_item(
        cls,
        model_class,
        item_id: int,
        fields: tuple[str, ...],
        tenant_filter: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """查询通用数据详情。"""
        item = await cls.get_required_by_id(
            model_class=model_class,
            item_id=item_id,
            tenant_filter=tenant_filter,
        )
        return cls.serialize(item, fields)

    @staticmethod
    async def create_item(model_class, data: dict[str, Any]):
        """创建数据。"""
        try:
            return await model_class.objects.using(IAM_DB_ALIAS).acreate(**data)
        except IntegrityError as exc:
            raise BusinessError(f"Data creation failed: {exc}", IamErrorCode.DATA_CREATION_FAILED)

    @classmethod
    async def create_item_with_audit(
        cls,
        model_class,
        data: dict[str, Any],
        operator_id: int | None = None,
        tenant_create_values: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """创建通用数据并填充审计字段。"""
        cls.ensure_model_class(model_class)
        final_data = data

        if tenant_create_values:
            final_data = {**data, **tenant_create_values}

        create_data = cls.fill_create_audit_fields(
            model_class=model_class,
            data=final_data,
            operator_id=operator_id,
        )
        item = await cls.create_item(model_class=model_class, data=create_data)
        return {"id": item.id}

    @staticmethod
    async def update_item(instance, data: dict[str, Any]) -> None:
        """更新数据。"""
        for field, value in data.items():
            setattr(instance, field, value)

        try:
            await instance.asave(
                using=IAM_DB_ALIAS,
                update_fields=list(data.keys()),
            )
        except IntegrityError as exc:
            raise BusinessError(f"Data update failed: {exc}", IamErrorCode.DATA_UPDATE_FAILED)

    @classmethod
    async def update_item_with_audit(
        cls,
        model_class,
        item_id: int,
        data: dict[str, Any],
        operator_id: int | None = None,
        tenant_filter: dict[str, Any] | None = None,
    ) -> None:
        """更新通用数据并填充审计字段。"""
        item = await cls.get_required_by_id(
            model_class=model_class,
            item_id=item_id,
            tenant_filter=tenant_filter,
        )
        update_data = cls.fill_update_audit_fields(
            model_class=model_class,
            data=data,
            operator_id=operator_id,
        )
        await cls.update_item(instance=item, data=update_data)

    @staticmethod
    async def delete_item(instance) -> None:
        """删除数据。"""
        await instance.adelete(using=IAM_DB_ALIAS)

    @classmethod
    async def delete_item_by_id(
        cls,
        model_class,
        item_id: int,
        tenant_filter: dict[str, Any] | None = None,
    ) -> None:
        """按主键删除通用数据。"""
        item = await cls.get_required_by_id(
            model_class=model_class,
            item_id=item_id,
            tenant_filter=tenant_filter,
        )
        await cls.delete_item(item)

    @staticmethod
    def normalize_page(page: int | str | None, page_size: int | str | None) -> tuple[int, int]:
        """规范化分页参数。"""
        try:
            normalized_page = max(int(page or 1), 1)
            normalized_page_size = min(max(int(page_size or 20), 1), 100)
        except (TypeError, ValueError):
            raise BusinessError("Invalid pagination parameters", IamErrorCode.INVALID_PAGINATION_PARAMETERS)

        return normalized_page, normalized_page_size

    @classmethod
    def fill_create_audit_fields(
        cls,
        model_class,
        data: dict[str, Any],
        operator_id: int | None = None,
    ) -> dict[str, Any]:
        """填充创建审计字段。"""
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
    def fill_update_audit_fields(
        cls,
        model_class,
        data: dict[str, Any],
        operator_id: int | None = None,
    ) -> dict[str, Any]:
        """填充更新审计字段。"""
        result = data.copy()
        field_names = cls.get_model_field_names(model_class)

        if "updated_by" in field_names:
            result["updated_by"] = operator_id

        if "updated_at" in field_names:
            result["updated_at"] = timezone.now()

        return result

    @staticmethod
    def serialize(instance, fields: tuple[str, ...]) -> dict[str, Any]:
        """序列化模型字段。"""
        result = {}

        for field in fields:
            value = getattr(instance, field)

            if isinstance(value, (datetime, date)):
                value = value.isoformat()

            result[field] = value

        return result

    @staticmethod
    def get_model_field_names(model_class) -> set[str]:
        """获取 Django 模型字段名集合。"""
        return {field.name for field in model_class._meta.fields}

