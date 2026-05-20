# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from django.contrib.auth.hashers import make_password
from django.utils import timezone

from iam.constants import IAM_DB_ALIAS
from iam.models import IamUser
from iam.services.base import BaseIamService
from ns_backend.exceptions import BusinessError


class UserService(BaseIamService):
    model = IamUser

    @classmethod
    async def list_users(
        cls,
        fields: tuple[str, ...],
        page: int = 1,
        page_size: int = 20,
        include_staff: bool = False,
        include_superuser: bool = False,
    ) -> dict[str, Any]:
        try:
            page = max(int(page or 1), 1)
            page_size = min(max(int(page_size or 20), 1), 100)
        except (TypeError, ValueError):
            raise BusinessError("分页参数非法", 12006)

        queryset = IamUser.objects.using(IAM_DB_ALIAS).all().order_by("-id")

        if not include_staff:
            queryset = queryset.filter(is_staff=0, is_superuser=0)
        elif not include_superuser:
            queryset = queryset.filter(is_superuser=0)

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

    @classmethod
    async def get_user(cls, user_id: int) -> IamUser:
        if not user_id:
            raise BusinessError("id 不能为空", 10001)

        user = await IamUser.objects.using(IAM_DB_ALIAS).filter(id=user_id).afirst()

        if not user:
            raise BusinessError("用户不存在", 10103)

        return user

    @classmethod
    async def create_user(
        cls,
        data: dict,
        operator_id: int | None = None,
    ) -> dict:
        raw_password = data.pop("password", None)

        if not raw_password:
            raise BusinessError("password 不能为空", 10101)

        data["password"] = make_password(raw_password)

        return await cls.create_item(
            data=data,
            operator_id=operator_id,
        )

    @classmethod
    async def reset_password(
        cls,
        user_id: int,
        raw_password: str,
        operator_id: int | None = None,
    ) -> None:
        if not raw_password:
            raise BusinessError("password 不能为空", 10101)

        user = await cls.get_user(user_id)
        user.password = make_password(raw_password)
        user.updated_by = operator_id
        user.updated_at = timezone.now()

        await user.asave(
            using=IAM_DB_ALIAS,
            update_fields=["password", "updated_by", "updated_at"],
        )

    @staticmethod
    def serialize(instance, fields: tuple[str, ...]) -> dict[str, Any]:
        result = {}

        for field in fields:
            value = getattr(instance, field)

            if isinstance(value, (datetime, date)):
                value = value.isoformat()

            result[field] = value

        return result
