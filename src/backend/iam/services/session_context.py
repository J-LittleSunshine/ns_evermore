# -*- coding: utf-8 -*-
from __future__ import annotations

from django.utils import timezone

from iam.repositories.session import SessionRepository
from iam.repositories.token import TokenRepository
from ns_backend.exceptions import BusinessError
from ns_backend.utils.jwt import JwtService


class SessionContextService:
    @classmethod
    async def list_sessions(
        cls,
        *,
        user,
        access_token: str | None = None,
    ) -> list[dict]:
        if not user or not user.is_active:
            return []

        current_session_pk = await cls.get_current_session_pk(
            user=user,
            access_token=access_token,
        )
        rows = await SessionRepository.list_user_sessions(user.id)
        valid_token_session_ids = await SessionRepository.list_valid_token_session_ids(user.id)
        now = timezone.now()

        return [
            cls.serialize_session(
                item=item,
                current_session_pk=current_session_pk,
                now=now,
                valid_token_session_ids=valid_token_session_ids,
            )
            for item in rows
        ]

    @classmethod
    async def revoke_session(
        cls,
        *,
        user,
        session_id: str,
    ) -> dict:
        if not user or not user.is_active:
            raise BusinessError("User is not logged in or session has expired", 11007)

        if not isinstance(session_id, str) or not session_id.strip():
            raise BusinessError("session_id cannot be empty", 15001)

        public_session_id = session_id.strip()
        session = await SessionRepository.get_user_session_by_public_id(
            user_id=user.id,
            session_id=public_session_id,
        )
        if not session:
            raise BusinessError("Session does not exist", 15002)

        if session.revoked_at:
            return {
                "success": False,
                "revoked": False,
                "session_id": session.session_id,
            }

        updated_count = await SessionRepository.revoke_session_and_tokens_by_id(session.id)
        revoked = updated_count > 0
        return {
            "success": revoked,
            "revoked": revoked,
            "session_id": session.session_id,
        }

    @classmethod
    async def get_current_session_pk(
        cls,
        *,
        user,
        access_token: str | None,
    ) -> int | None:
        if not user or not access_token:
            return None

        payload = JwtService.decode_access_token(access_token)
        if not payload:
            return None

        payload_uid = payload.get("uid")
        access_jti = payload.get("jti")

        if payload_uid != user.id:
            return None

        if not isinstance(access_jti, str) or not access_jti:
            return None

        token_record = await TokenRepository.get_valid_access_token(
            user_id=user.id,
            access_jti=access_jti,
        )
        if not token_record:
            return None

        return token_record.session_id

    @staticmethod
    def serialize_session(
        *,
        item: dict,
        current_session_pk: int | None,
        now,
        valid_token_session_ids: set[int],
    ) -> dict:
        internal_id = item.get("id")
        expired_at = item.get("expired_at")
        revoked_at = item.get("revoked_at")
        session_available = bool(
            revoked_at is None
            and expired_at is not None
            and expired_at > now
        )
        has_valid_token = internal_id in valid_token_session_ids
        is_active = session_available and has_valid_token

        return {
            "session_id": item.get("session_id"),
            "login_ip": item.get("login_ip"),
            "user_agent": item.get("user_agent"),
            "risk_level": item.get("risk_level"),
            "last_active_at": SessionContextService.format_datetime(item.get("last_active_at")),
            "expired_at": SessionContextService.format_datetime(expired_at),
            "revoked_at": SessionContextService.format_datetime(revoked_at),
            "created_at": SessionContextService.format_datetime(item.get("created_at")),
            "is_current": internal_id == current_session_pk,
            "session_available": session_available,
            "has_valid_token": has_valid_token,
            "is_active": is_active,
            "device": item.get("device"),
        }

    @staticmethod
    def format_datetime(value):
        if value is None:
            return None

        if hasattr(value, "isoformat"):
            return value.isoformat()

        return value


__all__ = ["SessionContextService"]

