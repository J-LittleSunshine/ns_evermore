# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from django.db import IntegrityError
from django.utils import timezone

from iam.constants import IAM_DB_ALIAS
from iam.models import IamUser
from ns_backend.exceptions import BusinessError


class UserRepository:
    """用户数据访问层。"""

    @staticmethod
    async def get_active_by_username(username: str) -> IamUser | None:
        return await IamUser.objects.using(IAM_DB_ALIAS).filter(
            username=username,
            is_active=1,
        ).afirst()

    @staticmethod
    async def get_active_by_id(user_id: int) -> IamUser | None:
        return await IamUser.objects.using(IAM_DB_ALIAS).filter(
            id=user_id,
            is_active=1,
        ).afirst()

    @staticmethod
    async def get_by_id(user_id: int) -> IamUser | None:
        return await IamUser.objects.using(IAM_DB_ALIAS).filter(id=user_id).afirst()

    @staticmethod
    def build_list_queryset(include_staff: bool = False, include_superuser: bool = False):
        queryset = IamUser.objects.using(IAM_DB_ALIAS).all().order_by("-id")

        if not include_staff:
            queryset = queryset.filter(is_staff=0, is_superuser=0)
        elif not include_superuser:
            queryset = queryset.filter(is_superuser=0)

        return queryset

    @classmethod
    async def list_users(
        cls,
        page: int,
        page_size: int,
        include_staff: bool = False,
        include_superuser: bool = False,
    ) -> tuple[list[IamUser], int]:
        queryset = cls.build_list_queryset(
            include_staff=include_staff,
            include_superuser=include_superuser,
        )
        offset = (page - 1) * page_size
        total = await queryset.acount()

        rows = []
        async for item in queryset[offset: offset + page_size].aiterator():
            rows.append(item)

        return rows, total

    @staticmethod
    async def create_user(data: dict[str, Any]) -> IamUser:
        try:
            return await IamUser.objects.using(IAM_DB_ALIAS).acreate(**data)
        except IntegrityError as exc:
            raise BusinessError(f"用户创建失败：{exc}", 12001)

    @staticmethod
    async def update_user(user: IamUser, data: dict[str, Any]) -> None:
        for field, value in data.items():
            setattr(user, field, value)

        try:
            await user.asave(
                using=IAM_DB_ALIAS,
                update_fields=list(data.keys()),
            )
        except IntegrityError as exc:
            raise BusinessError(f"用户更新失败：{exc}", 12002)

    @staticmethod
    async def delete_user(user: IamUser) -> None:
        await user.adelete(using=IAM_DB_ALIAS)

    @staticmethod
    async def mark_login_success(user: IamUser) -> None:
        now = timezone.now()
        user.last_login = now
        user.updated_at = now
        await user.asave(
            using=IAM_DB_ALIAS,
            update_fields=["last_login", "updated_at"],
        )
