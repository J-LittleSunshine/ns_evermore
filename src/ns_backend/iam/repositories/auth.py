# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from asgiref.sync import sync_to_async
from django.db import IntegrityError, transaction

from ns_backend.backend.common import BaseRepository
from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.models import IamLoginFailureLock, IamUser, IamUserDevice, IamUserSession, IamUserToken
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


class AuthUserRepository:
    """Repository for IAM authentication user queries."""

    @staticmethod
    async def get_active_user_by_username(username: str) -> IamUser | None:
        """Get active user by username."""
        db_alias = BaseRepository.resolve_db_alias(model_class=IamUser)
        return await IamUser.objects.using(db_alias).filter(username=username, is_active=1).afirst()

    @staticmethod
    async def get_user_by_id(user_id: int) -> IamUser | None:
        """Get user by id."""
        db_alias = BaseRepository.resolve_db_alias(model_class=IamUser)
        return await IamUser.objects.using(db_alias).filter(id=user_id).afirst()

    @staticmethod
    async def update_last_login(user: IamUser, last_login) -> None:
        """Update user's last login time."""
        user.last_login = last_login
        db_alias = user._state.db or BaseRepository.resolve_db_alias(model_class=IamUser)  # noqa
        await user.asave(using=db_alias, update_fields=["last_login"])


class LoginFailureRepository:
    """Repository for login failure lock records."""

    @staticmethod
    async def get_by_username(username: str) -> IamLoginFailureLock | None:
        """Get login failure lock by username."""
        db_alias = BaseRepository.resolve_db_alias(model_class=IamLoginFailureLock)
        return await IamLoginFailureLock.objects.using(db_alias).filter(username=username).afirst()

    @staticmethod
    async def create_failed_record(data: dict[str, Any]) -> IamLoginFailureLock:
        """Create login failure lock record."""
        db_alias = BaseRepository.resolve_db_alias(model_class=IamLoginFailureLock)
        return await IamLoginFailureLock.objects.using(db_alias).acreate(**data)

    @staticmethod
    async def update_failed_record(record: IamLoginFailureLock, data: dict[str, Any]) -> None:
        """Update login failure lock record."""
        for field, value in data.items():
            setattr(record, field, value)

        db_alias = record._state.db or BaseRepository.resolve_db_alias(model_class=IamLoginFailureLock)  # noqa
        await record.asave(using=db_alias, update_fields=list(data.keys()))

    @staticmethod
    async def clear_by_username(username: str) -> None:
        """Clear login failure lock by username."""
        db_alias = BaseRepository.resolve_db_alias(model_class=IamLoginFailureLock)
        await IamLoginFailureLock.objects.using(db_alias).filter(username=username).adelete()


class AuthLoginBundleRepository:
    """Repository for atomic login device, session, token and last-login writes."""

    @classmethod
    async def create_login_bundle_with_device(
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
            now
    ) -> tuple[IamUserSession, IamUserDevice]:
        """Create or update device, create session/token, and update last_login in one transaction."""
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
        """Synchronous transaction implementation for login bundle creation."""
        with transaction.atomic(using=db_alias):
            user = (
                IamUser.objects.using(db_alias)
                .select_for_update()
                .filter(id=user_id)
                .first()
            )
            if user is None or not bool(getattr(user, "is_active", False)):
                raise BusinessError("User disabled or not found", NsErrorCode.USER_DISABLED_OR_NOT_FOUND)

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

            IamUser.objects.using(db_alias).filter(id=user_id).update(last_login=now)
            return session, device

    @classmethod
    def _get_or_create_locked_device(
            cls,
            *,
            user_id: int,
            device_payload: dict[str, Any],
            fingerprint_hash: str,
            client_ip: str | None,
            now,
            db_alias: str
    ) -> IamUserDevice:
        """Get, create, or recover device row under the current transaction."""
        device = (
            IamUserDevice.objects.using(db_alias)
            .select_for_update()
            .filter(user_id=user_id, fingerprint_hash=fingerprint_hash)
            .first()
        )

        if device is not None:
            cls._update_device(device=device, device_payload=device_payload, client_ip=client_ip, now=now, db_alias=db_alias)
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
            device = (
                IamUserDevice.objects.using(db_alias)
                .select_for_update()
                .filter(user_id=user_id, fingerprint_hash=fingerprint_hash)
                .first()
            )
            if device is None:
                raise

            cls._update_device(device=device, device_payload=device_payload, client_ip=client_ip, now=now, db_alias=db_alias)
            return device

    @staticmethod
    def _update_device(*, device: IamUserDevice, device_payload: dict[str, Any], client_ip: str | None, now, db_alias: str) -> None:
        """Update device metadata for a successful login."""
        device.device_name = device_payload["device_name"]
        device.device_type = device_payload["device_type"]
        device.os_name = device_payload["os_name"] or None
        device.browser_name = device_payload["browser_name"] or None
        device.last_active_at = now
        device.last_client_ip = client_ip
        device.status = 1
        device.updated_at = now
        device.save(
            using=db_alias,
            update_fields=[
                "device_name",
                "device_type",
                "os_name",
                "browser_name",
                "last_active_at",
                "last_client_ip",
                "status",
                "updated_at",
            ],
        )
