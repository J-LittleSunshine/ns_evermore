# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import timedelta
from typing import (
    Any,
    TYPE_CHECKING
)

from asgiref.sync import sync_to_async
from django.db import (
    IntegrityError,
    transaction,
)
from django.db.models import (
    Case,
    DateTimeField,
    F,
    Value,
    When,
)
from django.utils import timezone

from backend.common import BaseRepository
from ns_backend.iam.errors import (
    IamLoginFailureUpdateFailedError,
    IamUserDisabledOrNotFoundError,
)
from ns_backend.iam.models import (
    IamLoginFailureLock,
    IamUser,
    IamUserDevice,
    IamUserSession,
    IamUserToken,
)

if TYPE_CHECKING:
    pass


class AuthUserRepository:
    @staticmethod
    async def get_active_user_by_username(username: str) -> IamUser | None:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamUser)
        return await IamUser.objects.using(db_alias).filter(username=username, is_active=1).afirst()

    @staticmethod
    async def get_user_by_id(user_id: int) -> IamUser | None:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamUser)
        return await IamUser.objects.using(db_alias).filter(id=user_id).afirst()

    @staticmethod
    async def update_last_login(user: IamUser, last_login) -> None:
        user.last_login = last_login
        db_alias = user._state.db or BaseRepository.resolve_db_alias(model_class=IamUser)  # noqa
        await user.asave(using=db_alias, update_fields=[
            "last_login",
        ]
        )


class LoginFailureRepository:
    @staticmethod
    async def get_by_username(username: str) -> IamLoginFailureLock | None:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamLoginFailureLock)
        return await IamLoginFailureLock.objects.using(db_alias).filter(username=username).afirst()

    @staticmethod
    async def reset_record(record: IamLoginFailureLock) -> None:
        record.failed_count = 0
        record.locked_until = None
        record.updated_at = timezone.now()

        db_alias = record._state.db or BaseRepository.resolve_db_alias(model_class=IamLoginFailureLock)  # noqa
        await record.asave(using=db_alias, update_fields=[
            "failed_count",
            "locked_until",
            "updated_at",
        ]
        )

    @staticmethod
    async def clear_by_username(username: str) -> None:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamLoginFailureLock)
        await IamLoginFailureLock.objects.using(db_alias).filter(username=username, ).aupdate(failed_count=0, locked_until=None, updated_at=timezone.now())

    @classmethod
    async def record_failed(cls, *, username: str, user: Any | None, max_failed_count: int, lock_minutes: int, client_ip: str | None = None, user_agent: str | None = None) -> None:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamLoginFailureLock)
        now = timezone.now()
        locked_until = now + timedelta(minutes=lock_minutes)

        update_fields: dict[str, Any] = {
            "failed_count": F("failed_count") + 1,
            "locked_until": Case(
                When(
                    failed_count__gte=max_failed_count - 1,
                    then=Value(locked_until),
                ),
                default=F("locked_until"),
                output_field=DateTimeField(),
            ),
            "last_failed_at": now,
            "last_client_ip": client_ip,
            "last_user_agent": user_agent,
            "updated_at": now,
        }

        if user is not None:
            update_fields["user_id"] = getattr(user, "id", None)

        affected_rows = await IamLoginFailureLock.objects.using(db_alias).filter(username=username).aupdate(**update_fields)

        if affected_rows:
            return

        try:
            await IamLoginFailureLock.objects.using(db_alias).acreate(
                username=username,
                user_id=getattr(user, "id", None) if user is not None else None,
                failed_count=1,
                locked_until=locked_until if max_failed_count <= 1 else None,
                last_failed_at=now,
                last_client_ip=client_ip,
                last_user_agent=user_agent,
                created_at=now,
                updated_at=now,
            )
            return
        except IntegrityError:
            retry_rows = await IamLoginFailureLock.objects.using(db_alias).filter(username=username).aupdate(**update_fields)

            if retry_rows:
                return

        raise IamLoginFailureUpdateFailedError()


class AuthLoginBundleRepository:
    @classmethod
    async def create_login_bundle_with_device(cls, *, user_id: int, device_payload: dict[str, Any], fingerprint_hash: str, client_ip: str | None, user_agent: str | None, session_public_id: str, session_expired_at, refresh_token_hash: str, access_jti: str, refresh_jti: str, token_expired_at, now) -> \
            tuple[IamUserSession, IamUserDevice]:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamUser)
        return await sync_to_async(cls._create_login_bundle_with_device_sync, thread_sensitive=True)(
            user_id=user_id,
            device_payload=device_payload,
            fingerprint_hash=fingerprint_hash,
            client_ip=client_ip,
            user_agent=user_agent,
            session_public_id=session_public_id,
            session_expired_at=session_expired_at,
            refresh_token_hash=refresh_token_hash,
            access_jti=access_jti,
            refresh_jti=refresh_jti,
            token_expired_at=token_expired_at,
            now=now,
            db_alias=db_alias,
        )

    @classmethod
    def _create_login_bundle_with_device_sync(
            cls,
            *,
            user_id: int,
            device_payload: dict[str, Any],
            fingerprint_hash: str,
            client_ip: str | None,
            user_agent: str | None,
            session_public_id: str,
            session_expired_at,
            refresh_token_hash: str,
            access_jti: str,
            refresh_jti: str,
            token_expired_at,
            now,
            db_alias: str
    ) -> tuple[IamUserSession, IamUserDevice]:
        with transaction.atomic(using=db_alias):
            user = IamUser.objects.using(db_alias).select_for_update().filter(id=user_id).first()

            if user is None or not bool(getattr(user, "is_active", False)):
                raise IamUserDisabledOrNotFoundError()

            device = cls._get_or_create_locked_device(
                user_id=user_id,
                device_payload=device_payload,
                fingerprint_hash=fingerprint_hash,
                client_ip=client_ip,
                now=now,
                db_alias=db_alias,
            )

            session = IamUserSession.objects.using(db_alias).create(
                user_id=user_id,
                device_id=device.id,
                session_id=session_public_id,
                login_ip=client_ip,
                user_agent=user_agent,
                risk_level=0,
                last_active_at=now,
                expired_at=session_expired_at,
                revoked_at=None,
                created_at=now,
            )

            IamUserToken.objects.using(db_alias).create(
                user_id=user_id,
                session_id=session.id,
                refresh_token_hash=refresh_token_hash,
                access_jti=access_jti,
                refresh_jti=refresh_jti,
                client_ip=client_ip,
                user_agent=user_agent,
                expired_at=token_expired_at,
                revoked_at=None,
                created_at=now,
            )

            IamUser.objects.using(db_alias).filter(id=user_id).update(
                last_login=now,
            )

            return session, device

    @classmethod
    def _get_or_create_locked_device(cls, *, user_id: int, device_payload: dict[str, Any], fingerprint_hash: str, client_ip: str | None, now, db_alias: str) -> IamUserDevice:
        device = IamUserDevice.objects.using(db_alias).select_for_update().filter(user_id=user_id, fingerprint_hash=fingerprint_hash).first()

        if device is not None:
            cls._update_device(
                device=device,
                device_payload=device_payload,
                client_ip=client_ip,
                now=now,
                db_alias=db_alias,
            )
            return device

        try:
            return IamUserDevice.objects.using(db_alias).create(
                user_id=user_id,
                device_id=device_payload["device_id"],
                device_name=device_payload["device_name"],
                device_type=device_payload["device_type"],
                os_name=device_payload["os_name"] or None,
                browser_name=device_payload["browser_name"] or None,
                fingerprint_hash=fingerprint_hash,
                trusted=0,
                status=1,
                first_login_at=now,
                last_active_at=now,
                last_client_ip=client_ip,
                created_at=now,
                updated_at=now,
            )
        except IntegrityError:
            device = IamUserDevice.objects.using(db_alias).select_for_update().filter(user_id=user_id, fingerprint_hash=fingerprint_hash).first()

            if device is None:
                raise

            cls._update_device(
                device=device,
                device_payload=device_payload,
                client_ip=client_ip,
                now=now,
                db_alias=db_alias,
            )
            return device

    @staticmethod
    def _update_device(*, device: IamUserDevice, device_payload: dict[str, Any], client_ip: str | None, now, db_alias: str) -> None:
        device.device_name = device_payload["device_name"]
        device.device_type = device_payload["device_type"]
        device.os_name = device_payload["os_name"] or None
        device.browser_name = device_payload["browser_name"] or None
        device.last_active_at = now
        device.last_client_ip = client_ip
        device.status = 1
        device.updated_at = now

        device.save(using=db_alias, update_fields=[
            "device_name",
            "device_type",
            "os_name",
            "browser_name",
            "last_active_at",
            "last_client_ip",
            "status",
            "updated_at",
        ]
        )
