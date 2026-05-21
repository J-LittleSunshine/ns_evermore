# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import timedelta

from django.db import IntegrityError
from django.db.models import Case, DateTimeField, F, Value, When
from django.utils import timezone

from iam.constants import IAM_DB_ALIAS
from iam.models import IamLoginFailureLock, IamUser


class LoginFailureRepository:
    """登录失败锁定数据访问层。"""

    @staticmethod
    async def get_by_username(username: str) -> IamLoginFailureLock | None:
        return await IamLoginFailureLock.objects.using(IAM_DB_ALIAS).filter(
            username=username,
        ).afirst()

    @staticmethod
    async def reset_record(record: IamLoginFailureLock) -> None:
        record.failed_count = 0
        record.locked_until = None
        record.updated_at = timezone.now()
        await record.asave(
            using=IAM_DB_ALIAS,
            update_fields=["failed_count", "locked_until", "updated_at"],
        )

    @staticmethod
    async def clear_by_username(username: str) -> None:
        await IamLoginFailureLock.objects.using(IAM_DB_ALIAS).filter(
            username=username,
        ).aupdate(
            failed_count=0,
            locked_until=None,
            updated_at=timezone.now(),
        )

    @staticmethod
    async def record_failed(
        username: str,
        user: IamUser | None,
        max_failed_count: int,
        lock_minutes: int,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        now = timezone.now()
        locked_until = now + timedelta(minutes=lock_minutes)

        update_fields = {
            "failed_count": F("failed_count") + 1,
            "locked_until": Case(
                When(
                    failed_count__gte=max_failed_count - 1,
                    then=Value(locked_until),
                ),
                default=F("locked_until"),
                output_field=DateTimeField(),
            ),
            "last_failed_at": now,
            "last_client_ip": client_ip,
            "last_user_agent": user_agent,
            "updated_at": now,
        }

        if user:
            update_fields["user_id"] = user.id

        affected_rows = await IamLoginFailureLock.objects.using(IAM_DB_ALIAS).filter(
            username=username,
        ).aupdate(**update_fields)

        if affected_rows:
            return

        try:
            await IamLoginFailureLock.objects.using(IAM_DB_ALIAS).acreate(
                username=username,
                user_id=user.id if user else None,
                failed_count=1,
                locked_until=locked_until if max_failed_count <= 1 else None,
                last_failed_at=now,
                last_client_ip=client_ip,
                last_user_agent=user_agent,
                created_at=now,
                updated_at=now,
            )
        except IntegrityError:
            await IamLoginFailureLock.objects.using(IAM_DB_ALIAS).filter(
                username=username,
            ).aupdate(**update_fields)
