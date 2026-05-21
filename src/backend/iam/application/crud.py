# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from django.utils import timezone

from iam.repositories.crud import CrudRepository
from ns_backend.exceptions import BusinessError


class CrudApplicationService:
    """通用 CRUD 应用服务。"""

    @classmethod
    async def list_items(
        cls,
        model_class,
        fields: tuple[str, ...],
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """分页查询通用数据。"""
        page, page_size = cls.normalize_page(page, page_size)
        items, total = await CrudRepository.list_items(
            model_class=model_class,
            page=page,
            page_size=page_size,
        )

        return {
            "items": [cls.serialize(item, fields) for item in items],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
        }

    @classmethod
    async def detail_item(cls, model_class, item_id: int, fields: tuple[str, ...]) -> dict[str, Any]:
        """查询通用数据详情。"""
        item = await cls.get_item(model_class=model_class, item_id=item_id)
        return cls.serialize(item, fields)

    @classmethod
    async def create_item(
        cls,
        model_class,
        data: dict[str, Any],
        operator_id: int | None = None,
    ) -> dict[str, Any]:
        """创建通用数据。"""
        data = cls.fill_create_audit_fields(
            model_class=model_class,
            data=data,
            operator_id=operator_id,
        )
        item = await CrudRepository.create_item(model_class=model_class, data=data)
        return {"id": item.id}

    @classmethod
    async def update_item(
        cls,
        model_class,
        item_id: int,
        data: dict[str, Any],
        operator_id: int | None = None,
    ) -> None:
        """更新通用数据。"""
        item = await cls.get_item(model_class=model_class, item_id=item_id)
        data = cls.fill_update_audit_fields(
            model_class=model_class,
            data=data,
            operator_id=operator_id,
        )
        await CrudRepository.update_item(instance=item, data=data)

    @classmethod
    async def delete_item(cls, model_class, item_id: int) -> None:
        """删除通用数据。"""
        item = await cls.get_item(model_class=model_class, item_id=item_id)
        await CrudRepository.delete_item(item)

    @staticmethod
    async def get_item(model_class, item_id: int):
        """获取通用数据。"""
        if not item_id:
            raise BusinessError("id 不能为空", 10001)

        item = await CrudRepository.get_by_id(model_class=model_class, item_id=item_id)

        if not item:
            raise BusinessError("数据不存在", 10002)

        return item

    @staticmethod
    def normalize_page(page: int | str | None, page_size: int | str | None) -> tuple[int, int]:
        """规范化分页参数。"""
        try:
            normalized_page = max(int(page or 1), 1)
            normalized_page_size = min(max(int(page_size or 20), 1), 100)
        except (TypeError, ValueError):
            raise BusinessError("分页参数非法", 12006)

        return normalized_page, normalized_page_size

    @staticmethod
    def fill_create_audit_fields(
        model_class,
        data: dict[str, Any],
        operator_id: int | None = None,
    ) -> dict[str, Any]:
        """填充创建审计字段。"""
        result = data.copy()
        now = timezone.now()

        if hasattr(model_class, "created_by"):
            result.setdefault("created_by", operator_id)

        if hasattr(model_class, "updated_by"):
            result.setdefault("updated_by", operator_id)

        if hasattr(model_class, "created_at"):
            result.setdefault("created_at", now)

        if hasattr(model_class, "updated_at"):
            result.setdefault("updated_at", now)

        return result

    @staticmethod
    def fill_update_audit_fields(
        model_class,
        data: dict[str, Any],
        operator_id: int | None = None,
    ) -> dict[str, Any]:
        """填充更新审计字段。"""
        result = data.copy()

        if hasattr(model_class, "updated_by"):
            result["updated_by"] = operator_id

        if hasattr(model_class, "updated_at"):
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
