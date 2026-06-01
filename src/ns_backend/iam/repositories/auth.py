# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ns_backend.iam.models import IamLoginFailureLock, IamUser

if TYPE_CHECKING:
    pass


class AuthUserRepository:
    """Repository for IAM authentication user queries."""

    @staticmethod
    async def get_active_user_by_username(username: str) -> IamUser | None:
        return await IamUser.objects.filter(username=username, is_active=1).afirst()

    @staticmethod
    async def get_user_by_id(user_id: int) -> IamUser | None:
        return await IamUser.objects.filter(id=user_id).afirst()

    @staticmethod
    async def update_last_login(user: IamUser, last_login) -> None:
        user.last_login = last_login
        await user.asave(update_fields=["last_login"])


class LoginFailureRepository:
    """Repository for login failure lock records."""

    @staticmethod
    async def get_by_username(username: str) -> IamLoginFailureLock | None:
        return await IamLoginFailureLock.objects.filter(username=username).afirst()

    @staticmethod
    async def create_failed_record(data: dict[str, Any]) -> IamLoginFailureLock:
        return await IamLoginFailureLock.objects.acreate(**data)

    @staticmethod
    async def update_failed_record(record: IamLoginFailureLock, data: dict[str, Any]) -> None:
        for field, value in data.items():
            setattr(record, field, value)
        await record.asave(update_fields=list(data.keys()))

    @staticmethod
    async def clear_by_username(username: str) -> None:
        await IamLoginFailureLock.objects.filter(username=username).adelete()
