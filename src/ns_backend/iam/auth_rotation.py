# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.db import transaction
from django.utils import timezone

from ns_backend.backend.exceptions import BusinessError
from ns_backend.backend.utils.jwt import JwtService
from ns_backend.iam.models import IamUserSession, IamUserToken
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


@dataclass(frozen=True, slots=True)
class RefreshTokenRotationResult:
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    session_id: str | None


class RefreshTokenRotationService:
    @classmethod
    def rotate(cls, *, user_id: int, refresh_jti: str, refresh_token_hash: str) -> RefreshTokenRotationResult:
        with transaction.atomic():
            now = timezone.now()

            token_record = IamUserToken.objects.select_for_update().select_related("user", "session").filter(
                user_id=user_id,
                refresh_jti=refresh_jti,
                refresh_token_hash=refresh_token_hash,
            ).first()

            if token_record is None:
                raise BusinessError("refresh token invalid or expired", NsErrorCode.REFRESH_TOKEN_INVALID_OR_EXPIRED)

            session = getattr(token_record, "session", None)
            user = getattr(token_record, "user", None)

            if token_record.revoked_at is not None:
                cls._revoke_session_and_tokens(session_id=token_record.session_id, user_id=user_id, now=now)
                raise BusinessError("Refresh token replay detected, current session has been forcibly logged out", NsErrorCode.REFRESH_TOKEN_REPLAY_DETECTED)

            if token_record.expired_at <= now:
                raise BusinessError("refresh token invalid or expired", NsErrorCode.REFRESH_TOKEN_INVALID_OR_EXPIRED)

            if user is None or not bool(getattr(user, "is_active", False)):
                cls._revoke_session_and_tokens(session_id=token_record.session_id, user_id=user_id, now=now)
                raise BusinessError("User disabled or not found", NsErrorCode.USER_DISABLED_OR_NOT_FOUND)

            if session is not None:
                if session.revoked_at is not None or session.expired_at <= now:
                    raise BusinessError("refresh token invalid or expired", NsErrorCode.REFRESH_TOKEN_INVALID_OR_EXPIRED)

                session.last_active_at = now
                session.login_ip = token_record.client_ip
                session.user_agent = token_record.user_agent
                session.save(update_fields=["last_active_at", "login_ip", "user_agent"])

            token_record.revoked_at = now
            token_record.save(update_fields=["revoked_at"])

            new_access_token, new_access_jti = JwtService.create_access_token(user_id=user.id, user_type=user.user_type)
            new_refresh_token, new_refresh_token_hash, new_refresh_jti, new_refresh_expired_at = JwtService.create_refresh_token(user_id=user.id)

            IamUserToken.objects.create(
                user_id=user.id,
                session_id=token_record.session_id,
                refresh_token_hash=new_refresh_token_hash,
                access_jti=new_access_jti,
                refresh_jti=new_refresh_jti,
                client_ip=token_record.client_ip,
                user_agent=token_record.user_agent,
                expired_at=new_refresh_expired_at,
                revoked_at=None,
                created_at=now,
            )

            return RefreshTokenRotationResult(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                token_type="Bearer",
                expires_in=JwtService._access_token_expire_minutes() * 60,  # noqa
                session_id=getattr(session, "session_id", None),
            )

    @staticmethod
    def _revoke_session_and_tokens(*, session_id: int | None, user_id: int, now) -> None:
        if session_id:
            IamUserSession.objects.filter(id=session_id, revoked_at__isnull=True).update(revoked_at=now)
            IamUserToken.objects.filter(session_id=session_id, revoked_at__isnull=True).update(revoked_at=now)
            return

        IamUserToken.objects.filter(user_id=user_id, revoked_at__isnull=True).update(revoked_at=now)
