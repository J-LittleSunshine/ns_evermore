# -*- coding: utf-8 -*-
from __future__ import annotations

from django.conf import settings
from django.utils import timezone

from iam.models import IamUser
from iam.repositories.login_failure import LoginFailureRepository
from ns_backend.exceptions import BusinessError


class LoginFailureDomainService:
    """登录失败锁定领域服务。"""

    LOGIN_MAX_FAILED_COUNT = settings.LOGIN_MAX_FAILED_COUNT
    LOGIN_LOCK_MINUTES = settings.LOGIN_LOCK_MINUTES

    @classmethod
    async def ensure_not_locked(cls, username: str) -> None:
        """校验账号是否处于登录锁定状态。"""
        record = await LoginFailureRepository.get_by_username(username)

        if not record or not record.locked_until:
            return

        now = timezone.now()

        if record.locked_until > now:
            raise BusinessError(
                msg="账号因连续登录失败已被锁定，请稍后再试",
                code=11011,
                data={"locked_until": record.locked_until.isoformat()},
            )

        await LoginFailureRepository.reset_record(record)

    @classmethod
    async def record_failed(
        cls,
        username: str,
        user: IamUser | None,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """记录登录失败。"""
        await LoginFailureRepository.record_failed(
            username=username,
            user=user,
            max_failed_count=cls.LOGIN_MAX_FAILED_COUNT,
            lock_minutes=cls.LOGIN_LOCK_MINUTES,
            client_ip=client_ip,
            user_agent=user_agent,
        )

    @classmethod
    async def clear(cls, username: str) -> None:
        """清除登录失败记录。"""
        await LoginFailureRepository.clear_by_username(username)
