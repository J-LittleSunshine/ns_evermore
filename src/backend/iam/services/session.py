# -*- coding: utf-8 -*-
from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any

from django.utils import timezone

from iam.repositories.session import SessionRepository
from ns_backend.exceptions import BusinessError


class SessionService:
	"""会话服务。"""

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
		session = await SessionRepository.get_by_public_session_id(session_id)
		return cls.ensure_session_state_available(session)

	@classmethod
	async def ensure_available_by_pk(cls, session_pk: int):
		session = await SessionRepository.get_by_pk(session_pk)
		return cls.ensure_session_state_available(session)

	@staticmethod
	def ensure_session_state_available(session):
		if not session:
			raise BusinessError("Session does not exist", 15002)

		if session.revoked_at:
			raise BusinessError("Session has been revoked", 15003)

		if session.expired_at <= timezone.now():
			raise BusinessError("Session has expired", 15004)

		return session

	@classmethod
	async def revoke_session(cls, session_id: str) -> bool:
		session = await SessionRepository.get_by_public_session_id(session_id)

		if not session:
			raise BusinessError("Session does not exist", 15002)

		return await cls.revoke_session_by_pk(session.id)

	@classmethod
	async def revoke_session_by_pk(cls, session_pk: int) -> bool:
		if not session_pk:
			raise BusinessError("session_id cannot be empty", 15001)

		updated_count = await SessionRepository.revoke_session_and_tokens_by_pk(session_pk)

		return updated_count > 0

	@classmethod
	async def revoke_user_sessions(cls, user_id: int) -> int:
		if not user_id:
			raise BusinessError("user_id cannot be empty", 15005)

		return await SessionRepository.revoke_user_sessions_and_tokens(user_id)

	@classmethod
	async def revoke_device_sessions(cls, device_id: int) -> int:
		if not device_id:
			raise BusinessError("device_id cannot be empty", 15006)

		return await SessionRepository.revoke_device_sessions_and_tokens(device_id)

	@classmethod
	async def touch_activity(
		cls,
		session_id: str,
		client_ip: str | None = None,
		user_agent: str | None = None,
	) -> None:
		update_data = cls.build_touch_update_data(
			client_ip=client_ip,
			user_agent=user_agent,
		)

		await SessionRepository.touch_session_by_public_id(session_id, update_data)

	@classmethod
	async def touch_activity_by_pk(
		cls,
		session_pk: int,
		client_ip: str | None = None,
		user_agent: str | None = None,
	) -> None:
		update_data = cls.build_touch_update_data(
			client_ip=client_ip,
			user_agent=user_agent,
		)

		await SessionRepository.touch_session_by_pk(session_pk, update_data)

	@staticmethod
	def build_touch_update_data(
		client_ip: str | None = None,
		user_agent: str | None = None,
	) -> dict[str, Any]:
		update_data: dict[str, Any] = {
			"last_active_at": timezone.now(),
		}

		if client_ip:
			update_data["login_ip"] = client_ip

		if user_agent:
			update_data["user_agent"] = user_agent

		return update_data


__all__ = ["SessionService"]

