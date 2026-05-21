# -*- coding: utf-8 -*-
from __future__ import annotations

from django.utils import timezone

from iam.constants import IAM_DB_ALIAS
from iam.models import IamUser


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
    async def mark_login_success(user: IamUser) -> None:
        now = timezone.now()
        user.last_login = now
        user.updated_at = now
        await user.asave(
            using=IAM_DB_ALIAS,
            update_fields=["last_login", "updated_at"],
        )
