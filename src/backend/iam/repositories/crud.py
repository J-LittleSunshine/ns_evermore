# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from django.db import IntegrityError

from iam.constants import IAM_DB_ALIAS
from ns_backend.exceptions import BusinessError


class CrudRepository:
    """通用 CRUD 数据访问层。"""

    @staticmethod
    def build_queryset(model_class):
        """构建基础查询集。"""
        return model_class.objects.using(IAM_DB_ALIAS).all().order_by("-id")

    @classmethod
    async def list_items(
        cls,
        model_class,
        page: int,
        page_size: int,
    ) -> tuple[list[Any], int]:
        """分页查询数据。"""
        queryset = cls.build_queryset(model_class)
        offset = (page - 1) * page_size
        total = await queryset.acount()

        rows = []
        async for item in queryset[offset: offset + page_size].aiterator():
            rows.append(item)

        return rows, total

    @staticmethod
    async def get_by_id(model_class, item_id: int):
        """按主键查询数据。"""
        return await model_class.objects.using(IAM_DB_ALIAS).filter(id=item_id).afirst()

    @staticmethod
    async def create_item(model_class, data: dict[str, Any]):
        """创建数据。"""
        try:
            return await model_class.objects.using(IAM_DB_ALIAS).acreate(**data)
        except IntegrityError as exc:
            raise BusinessError(f"数据创建失败：{exc}", 10003)

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
            raise BusinessError(f"数据更新失败：{exc}", 10005)

    @staticmethod
    async def delete_item(instance) -> None:
        """删除数据。"""
        await instance.adelete(using=IAM_DB_ALIAS)
