# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import uuid
from typing import Any

from asgiref.sync import sync_to_async
from django.db import IntegrityError, transaction
from django.utils import timezone

from iam.constants import IAM_DB_ALIAS
from iam.models import IamUser, IamUserDevice, IamUserSession, IamUserToken
from ns_backend.exceptions import BusinessError


class SessionRepository:
    """会话数据访问层。"""

    @staticmethod
    async def create_session(**kwargs) -> IamUserSession:
        return await IamUserSession.objects.using(IAM_DB_ALIAS).acreate(**kwargs)

    @classmethod
    async def create_login_bundle(
        cls,
        *,
        user_id: int,
        device_id: int,
        session_id: str,
        login_ip: str | None,
        user_agent: str | None,
        risk_level: int,
        last_active_at,
        session_expired_at,
        refresh_token_hash: str,
        access_jti: str,
        refresh_jti: str,
        token_expired_at,
    ) -> IamUserSession:
        """兼容保留：禁止调用旧登录写路径。"""
        raise BusinessError("create_login_bundle 已废弃，请改用 create_login_bundle_with_device", 15007)

    @staticmethod
    def _create_login_bundle_sync(
        *,
        user_id: int,
        device_id: int,
        session_id: str,
        login_ip: str | None,
        user_agent: str | None,
        risk_level: int,
        last_active_at,
        session_expired_at,
        refresh_token_hash: str,
        access_jti: str,
        refresh_jti: str,
        token_expired_at,
    ) -> IamUserSession:
        raise BusinessError("_create_login_bundle_sync 已废弃", 15007)

    @classmethod
    async def create_login_bundle_with_device(
        cls,
        *,
        user_id: int,
        device_name: str,
        device_type: str,
        fingerprint_raw: str,
        client_ip: str | None,
        os_name: str | None,
        browser_name: str | None,
        session_id: str,
        user_agent: str | None,
        risk_level: int,
        last_active_at,
        session_expired_at,
        refresh_token_hash: str,
        access_jti: str,
        refresh_jti: str,
        token_expired_at,
    ) -> tuple[IamUserSession, IamUserDevice]:
        """原子化处理设备、会话、Token 与最近登录时间。"""
        return await sync_to_async(
            cls._create_login_bundle_with_device_sync,
            thread_sensitive=True,
        )(
            user_id=user_id,
            device_name=device_name,
            device_type=device_type,
            fingerprint_raw=fingerprint_raw,
            client_ip=client_ip,
            os_name=os_name,
            browser_name=browser_name,
            session_id=session_id,
            user_agent=user_agent,
            risk_level=risk_level,
            last_active_at=last_active_at,
            session_expired_at=session_expired_at,
            refresh_token_hash=refresh_token_hash,
            access_jti=access_jti,
            refresh_jti=refresh_jti,
            token_expired_at=token_expired_at,
        )

    @staticmethod
    def _create_login_bundle_with_device_sync(
        *,
        user_id: int,
        device_name: str,
        device_type: str,
        fingerprint_raw: str,
        client_ip: str | None,
        os_name: str | None,
        browser_name: str | None,
        session_id: str,
        user_agent: str | None,
        risk_level: int,
        last_active_at,
        session_expired_at,
        refresh_token_hash: str,
        access_jti: str,
        refresh_jti: str,
        token_expired_at,
    ) -> tuple[IamUserSession, IamUserDevice]:
        now = timezone.now()
        fingerprint_hash = hashlib.sha256(fingerprint_raw.encode("utf-8")).hexdigest()

        with transaction.atomic(using=IAM_DB_ALIAS):
            user = (
                IamUser.objects.using(IAM_DB_ALIAS)
                .select_for_update()
                .filter(id=user_id)
                .first()
            )

            if not user or not user.is_active:
                raise BusinessError("Username or password is incorrect.", 11003)

            device = (
                IamUserDevice.objects.using(IAM_DB_ALIAS)
                .select_for_update()
                .filter(
                    user_id=user_id,
                    fingerprint_hash=fingerprint_hash,
                )
                .first()
            )

            if device:
                device.last_active_at = last_active_at
                device.last_client_ip = client_ip
                if device.status != 1:
                    device.status = 1
                device.updated_at = now
                device.save(
                    using=IAM_DB_ALIAS,
                    update_fields=["last_active_at", "last_client_ip", "status", "updated_at"],
                )
            else:
                try:
                    device = IamUserDevice.objects.using(IAM_DB_ALIAS).create(
                        user_id=user_id,
                        device_id=uuid.uuid4().hex,
                        device_name=device_name,
                        device_type=device_type,
                        os_name=os_name,
                        browser_name=browser_name,
                        fingerprint_hash=fingerprint_hash,
                        trusted=0,
                        status=1,
                        first_login_at=now,
                        last_active_at=last_active_at,
                        last_client_ip=client_ip,
                        created_at=now,
                        updated_at=now,
                    )
                except IntegrityError:
                    # Another concurrent login created the same fingerprint row; lock and reuse it.
                    device = (
                        IamUserDevice.objects.using(IAM_DB_ALIAS)
                        .select_for_update()
                        .filter(
                            user_id=user_id,
                            fingerprint_hash=fingerprint_hash,
                        )
                        .first()
                    )

                    if not device:
                        raise

                    device.last_active_at = last_active_at
                    device.last_client_ip = client_ip
                    if device.status != 1:
                        device.status = 1
                    device.updated_at = now
                    device.save(
                        using=IAM_DB_ALIAS,
                        update_fields=["last_active_at", "last_client_ip", "status", "updated_at"],
                    )

            session = IamUserSession.objects.using(IAM_DB_ALIAS).create(
                user_id=user_id,
                device_id=device.id,
                session_id=session_id,
                login_ip=client_ip,
                user_agent=user_agent,
                risk_level=risk_level,
                last_active_at=last_active_at,
                expired_at=session_expired_at,
                created_at=now,
            )

            IamUserToken.objects.using(IAM_DB_ALIAS).create(
                user_id=user_id,
                session_id=session.id,
                refresh_token=refresh_token_hash,
                access_jti=access_jti,
                refresh_jti=refresh_jti,
                client_ip=client_ip,
                user_agent=user_agent,
                expired_at=token_expired_at,
                created_at=now,
            )

            IamUser.objects.using(IAM_DB_ALIAS).filter(id=user_id).update(
                last_login=now,
                updated_at=now,
            )

            return session, device

    @staticmethod
    async def get_by_id(session_pk: int) -> IamUserSession | None:
        return await IamUserSession.objects.using(IAM_DB_ALIAS).filter(
            id=session_pk,
        ).afirst()

    @staticmethod
    async def get_by_session_id(session_id: str) -> IamUserSession | None:
        return await IamUserSession.objects.using(IAM_DB_ALIAS).filter(
            session_id=session_id,
        ).afirst()

    @staticmethod
    async def get_available_by_id(session_id: int) -> IamUserSession | None:
        return await IamUserSession.objects.using(IAM_DB_ALIAS).filter(
            id=session_id,
            revoked_at__isnull=True,
            expired_at__gt=timezone.now(),
        ).afirst()

    @staticmethod
    async def revoke_by_id(session_id: int) -> int:
        return await IamUserSession.objects.using(IAM_DB_ALIAS).filter(
            id=session_id,
            revoked_at__isnull=True,
        ).aupdate(revoked_at=timezone.now())

    @staticmethod
    async def revoke_token_by_session_id(session_id: int) -> int:
        return await IamUserToken.objects.using(IAM_DB_ALIAS).filter(
            session_id=session_id,
            revoked_at__isnull=True,
        ).aupdate(revoked_at=timezone.now())

    @classmethod
    async def revoke_session_and_tokens_by_id(cls, session_id: int) -> int:
        """原子化撤销单个会话及其全部 Token。"""
        return await sync_to_async(
            cls._revoke_session_and_tokens_by_id_sync,
            thread_sensitive=True,
        )(session_id=session_id)

    @staticmethod
    def _revoke_session_and_tokens_by_id_sync(session_id: int) -> int:
        now = timezone.now()

        with transaction.atomic(using=IAM_DB_ALIAS):
            locked_sessions = (
                IamUserSession.objects.using(IAM_DB_ALIAS)
                .select_for_update()
                .filter(id=session_id)
            )
            session_ids = list(locked_sessions.values_list("id", flat=True))

            if not session_ids:
                return 0

            updated_count = IamUserSession.objects.using(IAM_DB_ALIAS).filter(
                id__in=session_ids,
                revoked_at__isnull=True,
            ).update(revoked_at=now)

            IamUserToken.objects.using(IAM_DB_ALIAS).filter(
                session_id__in=session_ids,
                revoked_at__isnull=True,
            ).update(revoked_at=now)

            return updated_count

    @classmethod
    async def revoke_user_sessions_and_tokens(cls, user_id: int) -> int:
        """原子化撤销用户全部会话及全部 Token。"""
        return await sync_to_async(
            cls._revoke_user_sessions_and_tokens_sync,
            thread_sensitive=True,
        )(user_id=user_id)

    @staticmethod
    def _revoke_user_sessions_and_tokens_sync(user_id: int) -> int:
        now = timezone.now()

        with transaction.atomic(using=IAM_DB_ALIAS):
            locked_sessions = (
                IamUserSession.objects.using(IAM_DB_ALIAS)
                .select_for_update()
                .filter(user_id=user_id)
            )
            session_ids = list(locked_sessions.values_list("id", flat=True))

            updated_count = IamUserSession.objects.using(IAM_DB_ALIAS).filter(
                id__in=session_ids,
                revoked_at__isnull=True,
            ).update(revoked_at=now)

            IamUserToken.objects.using(IAM_DB_ALIAS).filter(
                user_id=user_id,
                revoked_at__isnull=True,
            ).update(revoked_at=now)

            return updated_count

    @classmethod
    async def revoke_device_sessions_and_tokens(cls, device_id: int) -> int:
        """原子化撤销设备全部会话及其全部 Token。"""
        return await sync_to_async(
            cls._revoke_device_sessions_and_tokens_sync,
            thread_sensitive=True,
        )(device_id=device_id)

    @staticmethod
    def _revoke_device_sessions_and_tokens_sync(device_id: int) -> int:
        now = timezone.now()

        with transaction.atomic(using=IAM_DB_ALIAS):
            locked_sessions = (
                IamUserSession.objects.using(IAM_DB_ALIAS)
                .select_for_update()
                .filter(device_id=device_id)
            )
            session_ids = list(locked_sessions.values_list("id", flat=True))

            if not session_ids:
                return 0

            updated_count = IamUserSession.objects.using(IAM_DB_ALIAS).filter(
                id__in=session_ids,
                revoked_at__isnull=True,
            ).update(revoked_at=now)

            IamUserToken.objects.using(IAM_DB_ALIAS).filter(
                session_id__in=session_ids,
                revoked_at__isnull=True,
            ).update(revoked_at=now)

            return updated_count

    @staticmethod
    async def list_active_ids_by_user_id(user_id: int) -> list[int]:
        return [
            item.id
            async for item in IamUserSession.objects.using(IAM_DB_ALIAS).filter(
                user_id=user_id,
                revoked_at__isnull=True,
            ).only("id")
        ]

    @staticmethod
    async def list_active_ids_by_device_id(device_id: int) -> list[int]:
        return [
            item.id
            async for item in IamUserSession.objects.using(IAM_DB_ALIAS).filter(
                device_id=device_id,
                revoked_at__isnull=True,
            ).only("id")
        ]

    @staticmethod
    async def revoke_by_ids(session_ids: list[int]) -> int:
        if not session_ids:
            return 0

        return await IamUserSession.objects.using(IAM_DB_ALIAS).filter(
            id__in=session_ids,
            revoked_at__isnull=True,
        ).aupdate(revoked_at=timezone.now())

    @staticmethod
    async def revoke_tokens_by_session_ids(session_ids: list[int]) -> int:
        if not session_ids:
            return 0

        return await IamUserToken.objects.using(IAM_DB_ALIAS).filter(
            session_id__in=session_ids,
            revoked_at__isnull=True,
        ).aupdate(revoked_at=timezone.now())

    @staticmethod
    async def touch_session(session_id: str, update_data: dict[str, Any]) -> int:
        return await IamUserSession.objects.using(IAM_DB_ALIAS).filter(
            session_id=session_id,
            revoked_at__isnull=True,
            expired_at__gt=timezone.now(),
        ).aupdate(**update_data)

    @staticmethod
    async def touch_session_by_id(session_id: int, update_data: dict[str, Any]) -> int:
        return await IamUserSession.objects.using(IAM_DB_ALIAS).filter(
            id=session_id,
            revoked_at__isnull=True,
            expired_at__gt=timezone.now(),
        ).aupdate(**update_data)

    @staticmethod
    async def update_risk_level(session_id: int, risk_level: int) -> int:
        return await IamUserSession.objects.using(IAM_DB_ALIAS).filter(
            id=session_id,
        ).aupdate(risk_level=risk_level)

    @staticmethod
    async def list_by_user_id(user_id: int):
        return IamUserSession.objects.using(IAM_DB_ALIAS).filter(
            user_id=user_id,
        ).order_by("-last_active_at")
