# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.utils import timezone

from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.repositories import UserSessionRepository, UserTokenRepository
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


class SessionService:
    """Session management service.

    业务规则：
    1. 用户只能查看自己的 session。
    2. 用户只能吊销自己的 session。
    3. 吊销 session 时必须联动吊销该 session 下的 token。
    """

    @classmethod
    async def list_current_user_sessions(cls, *, user_id: int) -> dict[str, list[dict[str, Any]]]:
        """List current user's sessions."""
        sessions = await UserSessionRepository.list_by_user_id(user_id=user_id)
        return {
            "items": [
                cls.serialize_session(session)
                for session in sessions
            ]
        }

    @classmethod
    async def revoke_current_user_session(cls, *, user_id: int, session_id: str) -> None:
        """Revoke current user's session and all tokens under this session."""
        clean_session_id = str(session_id or "").strip()
        if not clean_session_id:
            raise BusinessError("session_id cannot be empty", NsErrorCode.SESSION_ID_EMPTY)

        session = await UserSessionRepository.get_by_user_and_public_id(user_id=user_id, session_id=clean_session_id)
        if session is None:
            raise BusinessError("session not found", NsErrorCode.SESSION_NOT_FOUND)

        now = timezone.now()
        await UserSessionRepository.revoke_by_id(session_pk=session.id, revoked_at=now)
        await UserTokenRepository.revoke_by_session_id(session_pk=session.id, revoked_at=now)

    @staticmethod
    def serialize_session(session) -> dict[str, Any]:
        """Serialize session model to API payload."""
        return {
            "session_id": session.session_id,
            "device_id": session.device_id,
            "login_ip": session.login_ip,
            "user_agent": session.user_agent,
            "last_active_at": session.last_active_at.isoformat() if session.last_active_at else None,
            "expired_at": session.expired_at.isoformat() if session.expired_at else None,
            "revoked_at": session.revoked_at.isoformat() if session.revoked_at else None,
        }
