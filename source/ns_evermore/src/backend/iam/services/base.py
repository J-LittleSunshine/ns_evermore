# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, date
from typing import Any

from django.db import IntegrityError
from django.utils import timezone

from iam.constants import IAM_DB_ALIAS
from ns_backend.exceptions import BusinessError


class BaseIamService:
    model = None

    @classmethod
    async def list_items(
        cls,
        fields: tuple[str, ...],
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        try:
            page = max(int(page or 1), 1)
            page_size = min(max(int(page_size or 20), 1), 100)
        except (TypeError, ValueError):
            raise BusinessError("分页参数非法", 12006)

        offset = (page - 1) * page_size
        queryset = cls.model.objects.using(IAM_DB_ALIAS).all().order_by("-id")
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

    @classmethod
    async def detail_item(cls, item_id: int, fields: tuple[str, ...]) -> dict[str, Any]:
        item = await cls.model.objects.using(IAM_DB_ALIAS).filter(id=item_id).afirst()

        if not item:
            raise BusinessError("数据不存在", 10002)

        return cls.serialize(item, fields)

    @classmethod
    async def create_item(
        cls,
        data: dict[str, Any],
        operator_id: int | None = None,
    ) -> dict[str, Any]:
        now = timezone.now()

        if hasattr(cls.model, "created_by"):
            data.setdefault("created_by", operator_id)

        if hasattr(cls.model, "updated_by"):
            data.setdefault("updated_by", operator_id)

        if hasattr(cls.model, "created_at"):
            data.setdefault("created_at", now)

        if hasattr(cls.model, "updated_at"):
            data.setdefault("updated_at", now)

        try:
            item = await cls.model.objects.using(IAM_DB_ALIAS).acreate(**data)
        except IntegrityError as exc:
            raise BusinessError(f"数据创建失败：{exc}", 10003)

        return {"id": item.id}

    @classmethod
    async def update_item(
        cls,
        item_id: int,
        data: dict[str, Any],
        operator_id: int | None = None,
    ) -> None:
        item = await cls.model.objects.using(IAM_DB_ALIAS).filter(id=item_id).afirst()

        if not item:
            raise BusinessError("数据不存在", 10002)

        if hasattr(cls.model, "updated_by"):
            data["updated_by"] = operator_id

        if hasattr(cls.model, "updated_at"):
            data["updated_at"] = timezone.now()

        for field, value in data.items():
            setattr(item, field, value)

        try:
            await item.asave(
                using=IAM_DB_ALIAS,
                update_fields=list(data.keys()),
            )
        except IntegrityError as exc:
            raise BusinessError(f"数据更新失败：{exc}", 10005)

    @classmethod
    async def delete_item(cls, item_id: int) -> None:
        item = await cls.model.objects.using(IAM_DB_ALIAS).filter(id=item_id).afirst()

        if not item:
            raise BusinessError("数据不存在", 10002)

        await item.adelete(using=IAM_DB_ALIAS)

    @staticmethod
    def serialize(instance, fields: tuple[str, ...]) -> dict[str, Any]:
        result = {}

        for field in fields:
            value = getattr(instance, field)

            if isinstance(value, (datetime, date)):
                value = value.isoformat()

            result[field] = value

        return result
