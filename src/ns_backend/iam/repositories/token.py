# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import transaction
from django.utils import timezone

from backend.common import BaseRepository
from backend.utils.jwt import JwtService
from ns_backend.iam.errors import (
    IamRefreshTokenInvalidOrExpiredError,
    IamRefreshTokenReplayDetectedError,
    IamUserDisabledOrNotFoundError,
)
from ns_backend.iam.models import (
    IamUserSession,
    IamUserToken,
)
from ns_backend.iam.schemas import (
    TokenRotationOutcome,
    TokenRotationResult,
)

if TYPE_CHECKING:
    pass


class UserTokenRepository:
    @staticmethod
    async def get_active_access_token_record(*, user_id: int, access_jti: str, now) -> IamUserToken | None:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamUserToken)
        return await IamUserToken.objects.using(db_alias).select_related("user", "session", ).filter(
            user_id=user_id,
            access_jti=access_jti,
            revoked_at__isnull=True,
            expired_at__gt=now
        ).afirst()

    @staticmethod
    async def revoke_by_user_id(*, user_id: int, revoked_at) -> int:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamUserToken)
        return await IamUserToken.objects.using(db_alias).filter(user_id=user_id, revoked_at__isnull=True, ).aupdate(revoked_at=revoked_at)

    @staticmethod
    async def revoke_refresh_token(*, user_id: int, refresh_jti: str, refresh_token_hash: str, revoked_at) -> int:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamUserToken)
        return await IamUserToken.objects.using(db_alias).filter(
            user_id=user_id,
            refresh_jti=refresh_jti,
            refresh_token_hash=refresh_token_hash,
            revoked_at__isnull=True,
        ).aupdate(
            revoked_at=revoked_at,
        )

    @classmethod
    async def revoke_token_session(cls, *, token_record: IamUserToken, revoked_at) -> bool:
        db_alias = token_record._state.db or BaseRepository.resolve_db_alias(model_class=IamUserToken)  # noqa
        return cls._revoke_token_session_sync(
            token_id=token_record.id,
            session_id=token_record.session_id,
            revoked_at=revoked_at,
            db_alias=db_alias,
        )

    @staticmethod
    def _revoke_token_session_sync(*, token_id: int, session_id: int | None, revoked_at, db_alias: str) -> bool:
        with transaction.atomic(using=db_alias):
            if session_id:
                session_updated = IamUserSession.objects.using(db_alias).filter(id=session_id, revoked_at__isnull=True).update(revoked_at=revoked_at)
                token_updated = IamUserToken.objects.using(db_alias).filter(session_id=session_id, revoked_at__isnull=True).update(revoked_at=revoked_at)
                return session_updated > 0 or token_updated > 0

            token_updated = IamUserToken.objects.using(db_alias).filter(id=token_id, revoked_at__isnull=True).update(revoked_at=revoked_at)
            return token_updated > 0


class UserSessionRepository:
    @staticmethod
    async def revoke_user_sessions_and_tokens(*, user_id: int, revoked_at) -> None:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamUserSession)

        await IamUserSession.objects.using(db_alias).filter(user_id=user_id, revoked_at__isnull=True, ).aupdate(revoked_at=revoked_at)

        await IamUserToken.objects.using(db_alias).filter(user_id=user_id, revoked_at__isnull=True).aupdate(revoked_at=revoked_at)


class UserTokenRotationRepository:
    @classmethod
    def rotate(cls, *, user_id: int, refresh_jti: str, refresh_token_hash: str) -> TokenRotationResult:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamUserToken)
        outcome = cls._rotate_in_transaction(
            user_id=user_id,
            refresh_jti=refresh_jti,
            refresh_token_hash=refresh_token_hash,
            db_alias=db_alias,
        )

        if outcome.status == "rotated" and outcome.result is not None:
            return outcome.result

        if outcome.status == "replayed":
            raise IamRefreshTokenReplayDetectedError()

        if outcome.status == "user_inactive":
            raise IamUserDisabledOrNotFoundError()

        raise IamRefreshTokenInvalidOrExpiredError()

    @classmethod
    def _rotate_in_transaction(cls, *, user_id: int, refresh_jti: str, refresh_token_hash: str, db_alias: str) -> TokenRotationOutcome:
        with transaction.atomic(using=db_alias):
            now = timezone.now()

            token_record = IamUserToken.objects.using(db_alias).select_for_update().select_related("user", "session", ).filter(
                user_id=user_id,
                refresh_jti=refresh_jti,
                refresh_token_hash=refresh_token_hash,
            ).first()

            if token_record is None:
                return TokenRotationOutcome(status="invalid")

            session = getattr(token_record, "session", None)
            user = getattr(token_record, "user", None)

            if token_record.revoked_at is not None:
                cls._revoke_session_and_tokens(
                    session_id=token_record.session_id,
                    user_id=user_id,
                    now=now,
                    db_alias=db_alias,
                )
                return TokenRotationOutcome(status="replayed")

            if token_record.expired_at <= now:
                return TokenRotationOutcome(status="expired")

            if user is None or not bool(getattr(user, "is_active", False)):
                cls._revoke_session_and_tokens(
                    session_id=token_record.session_id,
                    user_id=user_id,
                    now=now,
                    db_alias=db_alias,
                )
                return TokenRotationOutcome(status="user_inactive")

            if session is not None:
                if session.revoked_at is not None or session.expired_at <= now:
                    return TokenRotationOutcome(status="session_unavailable")

                session.last_active_at = now
                session.login_ip = token_record.client_ip
                session.user_agent = token_record.user_agent
                session.save(using=db_alias, update_fields=[
                    "last_active_at",
                    "login_ip",
                    "user_agent",
                ]
                )

            token_record.revoked_at = now
            token_record.save(using=db_alias, update_fields=[
                "revoked_at",
            ]
            )

            new_access_token, new_access_jti = JwtService.create_access_token(user_id=user.id, user_type=user.user_type)
            new_refresh_token, new_refresh_token_hash, new_refresh_jti, new_refresh_expired_at, = JwtService.create_refresh_token(user_id=user.id)

            IamUserToken.objects.using(db_alias).create(
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
    def _revoke_session_and_tokens(*, session_id: int | None, user_id: int, now, db_alias: str) -> None:
        if session_id:
            IamUserSession.objects.using(db_alias).filter(id=session_id, revoked_at__isnull=True).update(revoked_at=now)
            IamUserToken.objects.using(db_alias).filter(session_id=session_id, revoked_at__isnull=True).update(revoked_at=now)
            return

        IamUserToken.objects.using(db_alias).filter(user_id=user_id, revoked_at__isnull=True).update(revoked_at=now)
