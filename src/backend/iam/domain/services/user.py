# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from django.contrib.auth.hashers import make_password
from django.utils import timezone

from iam.repositories.user import UserRepository
from ns_backend.exceptions import BusinessError


class UserDomainService:
    """用户领域服务。"""

    @staticmethod
    def normalize_page(page: int | str | None, page_size: int | str | None) -> tuple[int, int]:
        """规范化分页参数。"""
        try:
            normalized_page = max(int(page or 1), 1)
            normalized_page_size = min(max(int(page_size or 20), 1), 100)
        except (TypeError, ValueError):
            raise BusinessError("分页参数非法", 12006)

        return normalized_page, normalized_page_size

    @classmethod
    async def get_user(cls, user_id: int):
        """获取用户。"""
        if not user_id:
            raise BusinessError("id 不能为空", 10001)

        user = await UserRepository.get_by_id(user_id)

        if not user:
            raise BusinessError("用户不存在", 10103)

        return user

    @staticmethod
    def build_create_data(data: dict[str, Any], operator_id: int | None = None) -> dict[str, Any]:
        """构建用户创建数据。"""
        create_data = data.copy()
        raw_password = create_data.pop("password", None)

        if not raw_password:
            raise BusinessError("password 不能为空", 10101)

        now = timezone.now()
        create_data["password"] = make_password(raw_password)
        create_data.setdefault("created_by", operator_id)
        create_data.setdefault("updated_by", operator_id)
        create_data.setdefault("created_at", now)
        create_data.setdefault("updated_at", now)
        return create_data

    @staticmethod
    def build_update_data(data: dict[str, Any], operator_id: int | None = None) -> dict[str, Any]:
        """构建用户更新数据。"""
        update_data = data.copy()
        update_data["updated_by"] = operator_id
        update_data["updated_at"] = timezone.now()
        return update_data

    @staticmethod
    def build_reset_password_data(
        raw_password: str,
        operator_id: int | None = None,
    ) -> dict[str, Any]:
        """构建重置密码数据。"""
        if not raw_password:
            raise BusinessError("password 不能为空", 10101)

        return {
            "password": make_password(raw_password),
            "updated_by": operator_id,
            "updated_at": timezone.now(),
        }

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
