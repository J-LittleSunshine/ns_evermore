# -*- coding: utf-8 -*-
from __future__ import annotations

import uuid
from datetime import timedelta

from django.utils import timezone

from iam.constants import IAM_DB_ALIAS
from iam.models.device import IamUserSession


class SessionService:

    @classmethod
    async def create_session(
            cls,
            user_id: int,
            device_id: int,
            login_ip: str | None = None,
            user_agent: str | None = None,
            expired_minutes: int = 43200,
    ) -> IamUserSession:
        now = timezone.now()

        return await IamUserSession.objects.using(IAM_DB_ALIAS).acreate(
            user_id=user_id,
            device_id=device_id,
            session_id=uuid.uuid4().hex,
            login_ip=login_ip,
            user_agent=user_agent,
            risk_level=0,
            last_active_at=now,
            expired_at=now + timedelta(minutes=expired_minutes),
            created_at=now,
        )

    @classmethod
    async def revoke_session(cls, session_id: str) -> bool:
        updated_count = await IamUserSession.objects.using(IAM_DB_ALIAS).filter(
            session_id=session_id,
            revoked_at__isnull=True,
        ).aupdate(revoked_at=timezone.now())

        return updated_count > 0

    @classmethod
    async def touch_session(cls, session_id: str) -> None:
        await IamUserSession.objects.using(IAM_DB_ALIAS).filter(
            session_id=session_id,
            revoked_at__isnull=True,
            expired_at__gt=timezone.now(),
        ).aupdate(last_active_at=timezone.now())
