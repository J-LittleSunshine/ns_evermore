# -*- coding: utf-8 -*-
from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any

from django.db import transaction
from django.utils import timezone

from iam.constants import IAM_DB_ALIAS
from iam.models import IamUserSession, IamUserToken
from ns_backend.exceptions import BusinessError


class SessionService:
    """企业级 Session 生命周期服务。"""

    DEFAULT_EXPIRED_MINUTES = 43200

    @classmethod
    async def create_session(
        cls,
        user_id: int,
        device_id: int,
        login_ip: str | None = None,
        user_agent: str | None = None,
        expired_minutes: int = DEFAULT_EXPIRED_MINUTES,
        risk_level: int = 0,
    ) -> IamUserSession:
        """创建登录会话。"""
        now = timezone.now()

        return await IamUserSession.objects.using(IAM_DB_ALIAS).acreate(
            user_id=user_id,
            device_id=device_id,
            session_id=uuid.uuid4().hex,
            login_ip=login_ip,
            user_agent=user_agent,
            risk_level=risk_level,
            last_active_at=now,
            expired_at=now + timedelta(minutes=expired_minutes),
            created_at=now,
        )

    @classmethod
    async def get_session(cls, session_id: str) -> IamUserSession:
        """获取会话。"""
        if not session_id:
            raise BusinessError("session_id 不能为空", 15001)

        session = await IamUserSession.objects.using(IAM_DB_ALIAS).filter(
            session_id=session_id,
        ).afirst()

        if not session:
            raise BusinessError("会话不存在", 15002)

        return session

    @classmethod
    async def ensure_session_available(cls, session_id: str) -> IamUserSession:
        """校验会话是否有效。"""
        session = await cls.get_session(session_id)

        if session.revoked_at:
            raise BusinessError("会话已失效", 15003)

        if session.expired_at <= timezone.now():
            raise BusinessError("会话已过期", 15004)

        return session

    @classmethod
    async def revoke_session(cls, session_id: str) -> bool:
        """撤销单个会话及其关联 token。"""
        session = await cls.get_session(session_id)
        now = timezone.now()

        async with transaction.async_atomic(using=IAM_DB_ALIAS):
            updated_count = await IamUserSession.objects.using(IAM_DB_ALIAS).filter(
                id=session.id,
                revoked_at__isnull=True,
            ).aupdate(revoked_at=now)

            await IamUserToken.objects.using(IAM_DB_ALIAS).filter(
                session_id=session.id,
                revoked_at__isnull=True,
            ).aupdate(revoked_at=now)

        return updated_count > 0

    @classmethod
    async def revoke_user_sessions(cls, user_id: int) -> int:
        """撤销用户全部会话。"""
        if not user_id:
            raise BusinessError("user_id 不能为空", 15005)

        now = timezone.now()

        session_ids = [
            item.id
            async for item in IamUserSession.objects.using(IAM_DB_ALIAS).filter(
                user_id=user_id,
                revoked_at__isnull=True,
            ).only("id")
        ]

        updated_count = await IamUserSession.objects.using(IAM_DB_ALIAS).filter(
            id__in=session_ids,
            revoked_at__isnull=True,
        ).aupdate(revoked_at=now)

        if session_ids:
            await IamUserToken.objects.using(IAM_DB_ALIAS).filter(
                session_id__in=session_ids,
                revoked_at__isnull=True,
            ).aupdate(revoked_at=now)

        return updated_count

    @classmethod
    async def revoke_device_sessions(cls, device_id: int) -> int:
        """撤销设备全部会话。"""
        if not device_id:
            raise BusinessError("device_id 不能为空", 15006)

        now = timezone.now()

        session_ids = [
            item.id
            async for item in IamUserSession.objects.using(IAM_DB_ALIAS).filter(
                device_id=device_id,
                revoked_at__isnull=True,
            ).only("id")
        ]

        updated_count = await IamUserSession.objects.using(IAM_DB_ALIAS).filter(
            id__in=session_ids,
            revoked_at__isnull=True,
        ).aupdate(revoked_at=now)

        if session_ids:
            await IamUserToken.objects.using(IAM_DB_ALIAS).filter(
                session_id__in=session_ids,
                revoked_at__isnull=True,
            ).aupdate(revoked_at=now)

        return updated_count

    @classmethod
    async def touch_session_activity(
        cls,
        session_id: str,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """刷新会话活跃时间。"""
        update_data: dict[str, Any] = {
            "last_active_at": timezone.now(),
        }

        if client_ip:
            update_data["login_ip"] = client_ip

        if user_agent:
            update_data["user_agent"] = user_agent

        await IamUserSession.objects.using(IAM_DB_ALIAS).filter(
            session_id=session_id,
            revoked_at__isnull=True,
            expired_at__gt=timezone.now(),
        ).aupdate(**update_data)

    @classmethod
    async def detect_session_risk(
        cls,
        session_id: str,
        current_ip: str | None = None,
        current_user_agent: str | None = None,
    ) -> int:
        """简单会话风险检测。"""
        session = await cls.get_session(session_id)

        risk_level = session.risk_level or 0

        if current_ip and session.login_ip and current_ip != session.login_ip:
            risk_level += 1

        if (
            current_user_agent
            and session.user_agent
            and current_user_agent != session.user_agent
        ):
            risk_level += 1

        if risk_level != session.risk_level:
            await IamUserSession.objects.using(IAM_DB_ALIAS).filter(
                id=session.id,
            ).aupdate(risk_level=risk_level)

        return risk_level

    @classmethod
    async def list_user_sessions(cls, user_id: int) -> list[dict[str, Any]]:
        """获取用户会话列表。"""
        rows = []

        queryset = IamUserSession.objects.using(IAM_DB_ALIAS).filter(
            user_id=user_id,
        ).order_by("-last_active_at")

        async for item in queryset.aiterator():
            rows.append(
                {
                    "session_id": item.session_id,
                    "device_id": item.device_id,
                    "login_ip": item.login_ip,
                    "risk_level": item.risk_level,
                    "last_active_at": item.last_active_at.isoformat(),
                    "expired_at": item.expired_at.isoformat(),
                    "revoked_at": item.revoked_at.isoformat() if item.revoked_at else None,
                }
            )

        return rows
