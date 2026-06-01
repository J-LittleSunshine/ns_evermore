# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db import transaction
from django.utils import timezone

from ns_backend.backend.exceptions import BusinessError
from ns_backend.backend.utils.jwt import JwtService
from ns_backend.iam.models import IamUserSession, IamUserToken
from ns_backend.iam.schemas import TokenRotationResult, TokenRotationOutcome
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


class UserTokenRepository:
    """Repository for IAM user token records."""

    @staticmethod
    async def create_token(data: dict[str, Any]) -> IamUserToken:
        return await IamUserToken.objects.acreate(**data)

    @staticmethod
    async def get_active_access_token_record(*, user_id: int, access_jti: str, now) -> IamUserToken | None:
        return await IamUserToken.objects.select_related("user", "session").filter(
            user_id=user_id,
            access_jti=access_jti,
            revoked_at__isnull=True,
            expired_at__gt=now,
        ).afirst()

    @staticmethod
    async def revoke_by_user_id(*, user_id: int, revoked_at) -> int:
        return await IamUserToken.objects.filter(user_id=user_id, revoked_at__isnull=True).aupdate(revoked_at=revoked_at)

    @staticmethod
    async def revoke_by_session_id(*, session_pk: int, revoked_at) -> int:
        return await IamUserToken.objects.filter(session_id=session_pk, revoked_at__isnull=True).aupdate(revoked_at=revoked_at)

    @staticmethod
    async def revoke_refresh_token(*, user_id: int, refresh_jti: str, refresh_token_hash: str, revoked_at) -> int:
        return await IamUserToken.objects.filter(
            user_id=user_id,
            refresh_jti=refresh_jti,
            refresh_token_hash=refresh_token_hash,
            revoked_at__isnull=True,
        ).aupdate(revoked_at=revoked_at)

    @staticmethod
    async def revoke_token_record(token_record: IamUserToken, revoked_at) -> bool:
        if token_record.revoked_at is not None:
            return False

        token_record.revoked_at = revoked_at
        await token_record.asave(update_fields=["revoked_at"])
        return True

    @classmethod
    async def revoke_token_session(cls, *, token_record: IamUserToken, revoked_at) -> bool:
        if token_record.session_id:
            await IamUserSession.objects.filter(id=token_record.session_id, revoked_at__isnull=True).aupdate(revoked_at=revoked_at)
            updated_count = await cls.revoke_by_session_id(session_pk=token_record.session_id, revoked_at=revoked_at)
            return updated_count > 0

        return await cls.revoke_token_record(token_record=token_record, revoked_at=revoked_at)


class UserTokenRotationRepository:
    """Synchronous repository for refresh token rotation guarded by transaction locks."""

    @classmethod
    def rotate(cls, *, user_id: int, refresh_jti: str, refresh_token_hash: str) -> TokenRotationResult:
        outcome = cls._rotate_in_transaction(
            user_id=user_id,
            refresh_jti=refresh_jti,
            refresh_token_hash=refresh_token_hash,
        )

        if outcome.status == "rotated" and outcome.result is not None:
            return outcome.result

        if outcome.status == "replayed":
            raise BusinessError("Refresh token replay detected, current session has been forcibly logged out", NsErrorCode.REFRESH_TOKEN_REPLAY_DETECTED)

        if outcome.status == "user_inactive":
            raise BusinessError("User disabled or not found", NsErrorCode.USER_DISABLED_OR_NOT_FOUND)

        raise BusinessError("refresh token invalid or expired", NsErrorCode.REFRESH_TOKEN_INVALID_OR_EXPIRED)

    @classmethod
    def _rotate_in_transaction(cls, *, user_id: int, refresh_jti: str, refresh_token_hash: str) -> TokenRotationOutcome:
        with transaction.atomic():
            now = timezone.now()

            token_record = IamUserToken.objects.select_for_update().select_related("user", "session").filter(
                user_id=user_id,
                refresh_jti=refresh_jti,
                refresh_token_hash=refresh_token_hash,
            ).first()

            if token_record is None:
                return TokenRotationOutcome(status="invalid")

            session = getattr(token_record, "session", None)
            user = getattr(token_record, "user", None)

            if token_record.revoked_at is not None:
                cls._revoke_session_and_tokens(session_id=token_record.session_id, user_id=user_id, now=now)
                return TokenRotationOutcome(status="replayed")

            if token_record.expired_at <= now:
                return TokenRotationOutcome(status="expired")

            if user is None or not bool(getattr(user, "is_active", False)):
                cls._revoke_session_and_tokens(session_id=token_record.session_id, user_id=user_id, now=now)
                return TokenRotationOutcome(status="user_inactive")

            if session is not None:
                if session.revoked_at is not None or session.expired_at <= now:
                    return TokenRotationOutcome(status="session_unavailable")

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

            result = TokenRotationResult(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                token_type="Bearer",
                expires_in=JwtService._access_token_expire_minutes() * 60,  # noqa
                session_id=getattr(session, "session_id", None),
            )

            return TokenRotationOutcome(status="rotated", result=result)

    @staticmethod
    def _revoke_session_and_tokens(*, session_id: int | None, user_id: int, now) -> None:
        if session_id:
            IamUserSession.objects.filter(id=session_id, revoked_at__isnull=True).update(revoked_at=now)
            IamUserToken.objects.filter(session_id=session_id, revoked_at__isnull=True).update(revoked_at=now)
            return

        IamUserToken.objects.filter(user_id=user_id, revoked_at__isnull=True).update(revoked_at=now)
