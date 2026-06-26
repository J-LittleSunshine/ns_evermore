# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    TYPE_CHECKING,
)

from django.utils import timezone

from backend.utils.jwt import JwtService
from ns_backend.iam.errors import (
    IamRuntimeRequestInvalidError,
    IamUserNotLoggedInOrSessionExpiredError,
)
from ns_backend.iam.repositories import (
    UserSessionRepository,
    UserTokenRepository,
)

if TYPE_CHECKING:
    pass


class SessionService:
    @classmethod
    async def list_current_user_sessions(cls, *, user: Any, access_token: str | None = None) -> dict[str, Any]:
        if user is None or not bool(getattr(user, "is_active", False)):
            return {
                "items": [],
                "total": 0,
            }

        user_id = int(getattr(user, "id"))
        now = timezone.now()

        current_session_pk = await cls.get_current_session_pk(
            user=user,
            access_token=access_token,
            now=now,
        )

        valid_token_session_ids = await UserSessionRepository.list_valid_token_session_ids(
            user_id=user_id,
            now=now,
        )

        sessions = await UserSessionRepository.list_by_user_id(
            user_id=user_id,
        )

        items = [
            cls.serialize_session(
                session=session,
                current_session_pk=current_session_pk,
                valid_token_session_ids=valid_token_session_ids,
                now=now,
            )
            for session in sessions
        ]

        return {
            "items": items,
            "total": len(items),
        }

    @classmethod
    async def revoke_current_user_session(cls, *, user: Any, session_id: str) -> dict[str, Any]:
        if user is None or not bool(getattr(user, "is_active", False)):
            raise IamUserNotLoggedInOrSessionExpiredError()

        clean_session_id = str(session_id or "").strip()

        if not clean_session_id:
            raise IamRuntimeRequestInvalidError(
                "session_id is required.",
                details={
                    "field": "session_id",
                },
            )

        session = await UserSessionRepository.get_by_user_and_public_id(
            user_id=int(getattr(user, "id")),
            session_id=clean_session_id,
        )

        if session is None:
            return {
                "revoked": False,
                "session_id": clean_session_id,
                "reason": "SESSION_NOT_FOUND",
            }

        if session.revoked_at is not None:
            return {
                "revoked": False,
                "session_id": session.session_id,
                "reason": "SESSION_ALREADY_REVOKED",
            }

        updated_count = await UserSessionRepository.revoke_session_and_tokens_by_id(
            session_pk=session.id,
            revoked_at=timezone.now(),
        )

        revoked = updated_count > 0

        return {
            "revoked": revoked,
            "session_id": session.session_id,
        }

    @classmethod
    async def get_current_session_pk(cls, *, user: Any, access_token: str | None, now) -> int | None:
        if not user or not access_token:
            return None

        payload = JwtService.decode_access_token(access_token)

        if not payload:
            return None

        payload_user_id = payload.get("uid")
        access_jti = payload.get("jti")

        if payload_user_id != getattr(user, "id", None):
            return None

        if not isinstance(access_jti, str) or not access_jti:
            return None

        token_record = await UserTokenRepository.get_active_access_token_record(
            user_id=int(getattr(user, "id")),
            access_jti=access_jti,
            now=now,
        )

        if token_record is None:
            return None

        return token_record.session_id

    @staticmethod
    def serialize_session(*, session, current_session_pk: int | None, valid_token_session_ids: set[int], now) -> dict[str, Any]:
        expired_at = session.expired_at
        revoked_at = session.revoked_at

        session_available = bool(
            revoked_at is None
            and expired_at is not None
            and expired_at > now
        )

        has_valid_token = session.id in valid_token_session_ids

        device = getattr(session, "device", None)
        device_data = None

        if device is not None:
            device_data = {
                "device_id": device.device_id,
                "device_name": device.device_name,
                "device_type": device.device_type,
                "os_name": device.os_name,
                "browser_name": device.browser_name,
                "trusted": device.trusted,
                "status": device.status,
                "last_client_ip": device.last_client_ip,
            }

        return {
            "session_id": session.session_id,
            "login_ip": session.login_ip,
            "user_agent": session.user_agent,
            "risk_level": session.risk_level,
            "last_active_at": session.last_active_at.isoformat() if session.last_active_at else None,
            "expired_at": expired_at.isoformat() if expired_at else None,
            "revoked_at": revoked_at.isoformat() if revoked_at else None,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "is_current": session.id == current_session_pk,
            "session_available": session_available,
            "has_valid_token": has_valid_token,
            "is_active": session_available and has_valid_token,
            "device": device_data,
        }
