# -*- coding: utf-8 -*-
from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any

from django.utils import timezone

from iam.repositories.session import SessionRepository
from ns_backend.exceptions import BusinessError


class SessionDomainService:
    """会话领域服务。"""

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
    ):
        """创建会话。"""
        now = timezone.now()

        return await SessionRepository.create_session(
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
    async def ensure_available(cls, session_id: str):
        """按业务 session_id 确保会话有效。"""
        session = await SessionRepository.get_by_session_id(session_id)
        return cls.ensure_session_state_available(session)

    @classmethod
    async def ensure_available_by_pk(cls, session_pk: int):
        """按数据库主键确保会话有效。"""
        session = await SessionRepository.get_by_id(session_pk)
        return cls.ensure_session_state_available(session)

    @staticmethod
    def ensure_session_state_available(session):
        """校验会话状态。"""
        if not session:
            raise BusinessError("会话不存在", 15002)

        if session.revoked_at:
            raise BusinessError("会话已失效", 15003)

        if session.expired_at <= timezone.now():
            raise BusinessError("会话已过期", 15004)

        return session

    @classmethod
    async def revoke_session(cls, session_id: str) -> bool:
        """按业务 session_id 撤销会话及其全部 Token。"""
        session = await SessionRepository.get_by_session_id(session_id)

        if not session:
            raise BusinessError("会话不存在", 15002)

        return await cls.revoke_session_by_pk(session.id)

    @classmethod
    async def revoke_session_by_pk(cls, session_pk: int) -> bool:
        """按数据库主键撤销会话及其全部 Token。"""
        if not session_pk:
            raise BusinessError("session_id 不能为空", 15001)

        updated_count = await SessionRepository.revoke_by_id(session_pk)

        await SessionRepository.revoke_token_by_session_id(session_pk)

        return updated_count > 0

    @classmethod
    async def revoke_user_sessions(cls, user_id: int) -> int:
        """撤销用户全部会话。"""
        session_ids = await SessionRepository.list_active_ids_by_user_id(user_id)

        updated_count = await SessionRepository.revoke_by_ids(session_ids)

        await SessionRepository.revoke_tokens_by_session_ids(session_ids)

        return updated_count

    @classmethod
    async def revoke_device_sessions(cls, device_id: int) -> int:
        """撤销设备全部会话。"""
        session_ids = await SessionRepository.list_active_ids_by_device_id(device_id)

        updated_count = await SessionRepository.revoke_by_ids(session_ids)

        await SessionRepository.revoke_tokens_by_session_ids(session_ids)

        return updated_count

    @classmethod
    async def touch_activity(
        cls,
        session_id: str,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """按业务 session_id 刷新会话活跃状态。"""
        update_data = cls.build_touch_update_data(
            client_ip=client_ip,
            user_agent=user_agent,
        )

        await SessionRepository.touch_session(session_id, update_data)

    @classmethod
    async def touch_activity_by_pk(
        cls,
        session_pk: int,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """按数据库主键刷新会话活跃状态。"""
        update_data = cls.build_touch_update_data(
            client_ip=client_ip,
            user_agent=user_agent,
        )

        await SessionRepository.touch_session_by_id(session_pk, update_data)

    @staticmethod
    def build_touch_update_data(
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> dict[str, Any]:
        """构建会话活跃字段更新数据。"""
        update_data: dict[str, Any] = {
            "last_active_at": timezone.now(),
        }

        if client_ip:
            update_data["login_ip"] = client_ip

        if user_agent:
            update_data["user_agent"] = user_agent

        return update_data
