# -*- coding: utf-8 -*-
from __future__ import annotations

import ipaddress
import uuid
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.utils import timezone

from ns_backend.backend.exceptions import BusinessError
from ns_backend.backend.utils.jwt import JwtService
from ns_backend.backend.utils.password_transport import PasswordTransportService
from ns_backend.iam import IAM_LOGGER
from ns_backend.iam.repositories import (
    AuthLoginBundleRepository,
    AuthUserRepository,
    LoginFailureRepository,
    UserSessionRepository,
    UserTokenRepository,
    UserTokenRotationRepository,
)
from ns_backend.iam.schemas import AuthLoginResult, TokenRotationResult
from ns_backend.iam.utils import get_bearer_token_from_request, sha256_text
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


class RefreshTokenRotationService:
    """Refresh token rotation service facade."""

    @classmethod
    def rotate(cls, *, user_id: int, refresh_jti: str, refresh_token_hash: str) -> TokenRotationResult:
        return UserTokenRotationRepository.rotate(user_id=user_id, refresh_jti=refresh_jti, refresh_token_hash=refresh_token_hash)


class AuthService:
    """Authentication orchestration service."""

    SESSION_EXPIRE_MINUTES = 43200

    @staticmethod
    def is_truthy(value: Any) -> bool:
        return value in (True, 1, "1", "true", "True", "yes", "YES", "on", "ON")

    @classmethod
    async def resolve_user_from_request(cls, request):
        bearer_token = get_bearer_token_from_request(request)
        if not bearer_token:
            raise BusinessError("User is not logged in or session has expired", NsErrorCode.USER_NOT_LOGGED_IN_OR_SESSION_EXPIRED)

        payload = JwtService.decode_access_token(bearer_token)
        if not payload:
            raise BusinessError("User is not logged in or session has expired", NsErrorCode.USER_NOT_LOGGED_IN_OR_SESSION_EXPIRED)

        user_id = payload.get("uid")
        access_jti = payload.get("jti")
        if not isinstance(user_id, int) or not isinstance(access_jti, str):
            raise BusinessError("User is not logged in or session has expired", NsErrorCode.USER_NOT_LOGGED_IN_OR_SESSION_EXPIRED)

        now = timezone.now()
        token_record = await UserTokenRepository.get_active_access_token_record(user_id=user_id, access_jti=access_jti, now=now)
        if token_record is None:
            raise BusinessError("User is not logged in or session has expired", NsErrorCode.USER_NOT_LOGGED_IN_OR_SESSION_EXPIRED)

        session = getattr(token_record, "session", None)
        if session is not None:
            if session.revoked_at is not None or session.expired_at <= now:
                raise BusinessError("User is not logged in or session has expired", NsErrorCode.USER_NOT_LOGGED_IN_OR_SESSION_EXPIRED)

        user = getattr(token_record, "user", None)
        if user is None:
            user = await AuthUserRepository.get_user_by_id(user_id)

        if user is None or not bool(getattr(user, "is_active", False)):
            raise BusinessError("User disabled or not found", NsErrorCode.USER_DISABLED_OR_NOT_FOUND)

        request.current_user = user
        return user, token_record

    @classmethod
    async def ensure_login_not_locked(cls, username: str) -> None:
        record = await LoginFailureRepository.get_by_username(username)
        if record is None or record.locked_until is None:
            return

        now = timezone.now()
        if record.locked_until > now:
            raise BusinessError(
                "Account is locked due to consecutive login failures, please try again later",
                NsErrorCode.ACCOUNT_LOCKED,
                data={"locked_until": record.locked_until.isoformat()},
            )

        await LoginFailureRepository.update_failed_record(
            record,
            {
                "failed_count": 0,
                "locked_until": None,
                "updated_at": now,
            },
        )

    @classmethod
    async def record_login_failed(cls, *, username: str, user: Any | None, client_ip: str | None, user_agent: str | None) -> None:
        now = timezone.now()
        max_failed_count = int(getattr(settings, "LOGIN_MAX_FAILED_COUNT", 5))
        lock_minutes = int(getattr(settings, "LOGIN_LOCK_MINUTES", 15))

        record = await LoginFailureRepository.get_by_username(username)
        if record is None:
            failed_count = 1
            locked_until = now + timedelta(minutes=lock_minutes) if failed_count >= max_failed_count else None
            await LoginFailureRepository.create_failed_record(
                {
                    "username": username,
                    "user_id": getattr(user, "id", None),
                    "failed_count": failed_count,
                    "locked_until": locked_until,
                    "last_failed_at": now,
                    "last_client_ip": client_ip,
                    "last_user_agent": user_agent,
                    "created_at": now,
                    "updated_at": now,
                }
            )
            return

        failed_count = int(record.failed_count or 0) + 1
        await LoginFailureRepository.update_failed_record(
            record,
            {
                "user_id": getattr(user, "id", None),
                "failed_count": failed_count,
                "locked_until": now + timedelta(minutes=lock_minutes) if failed_count >= max_failed_count else None,
                "last_failed_at": now,
                "last_client_ip": client_ip,
                "last_user_agent": user_agent,
                "updated_at": now,
            },
        )

    @staticmethod
    async def clear_login_failure(username: str, user_id: int) -> None:
        try:
            await LoginFailureRepository.clear_by_username(username)
        except Exception as exc:
            IAM_LOGGER.warning(
                f"login failure clear failed | username={username} user_id={user_id} exception={exc.__class__.__name__}", exc_info=True,
            )

    @staticmethod
    def get_client_ip(request) -> str | None:
        trust_xff = bool(getattr(settings, "TRUST_X_FORWARDED_FOR", False))

        if trust_xff:
            x_forwarded_for = request.headers.get("X-Forwarded-For")
            if x_forwarded_for:
                candidate = x_forwarded_for.split(",")[0].strip()
                try:
                    ipaddress.ip_address(candidate)
                    return candidate[:64]
                except ValueError:
                    pass

        remote_addr = request.META.get("REMOTE_ADDR")
        if not remote_addr:
            return None

        try:
            ipaddress.ip_address(remote_addr)
            return str(remote_addr)[:64]
        except ValueError:
            return None

    @staticmethod
    def get_user_agent(request) -> str | None:
        user_agent = str(request.headers.get("User-Agent", "") or "").strip()
        return user_agent[:512] or None

    @staticmethod
    def get_device_payload(data: dict[str, Any]) -> dict[str, str]:
        device_id = str(data.get("device_id", "") or "").strip() or uuid.uuid4().hex
        device_name = str(data.get("device_name", "") or "").strip() or "Unknown Device"
        device_type = str(data.get("device_type", "") or "").strip() or "WEB"
        os_name = str(data.get("os_name", "") or "").strip()
        browser_name = str(data.get("browser_name", "") or "").strip()
        fingerprint = str(data.get("fingerprint", "") or "").strip() or device_id

        return {
            "device_id": device_id[:128],
            "device_name": device_name[:128],
            "device_type": device_type[:32],
            "os_name": os_name[:64],
            "browser_name": browser_name[:64],
            "fingerprint": fingerprint,
        }

    @classmethod
    async def login(cls, *, data: dict[str, Any], request) -> AuthLoginResult:
        username = str(data.get("username", "")).strip()
        password_payload = str(data.get("password", "")).strip()

        if not username:
            raise BusinessError("username cannot be empty", NsErrorCode.USERNAME_EMPTY)
        if not password_payload:
            raise BusinessError("password cannot be empty", NsErrorCode.PASSWORD_EMPTY)

        client_ip = cls.get_client_ip(request)
        user_agent = cls.get_user_agent(request)

        PasswordTransportService.validate_payload_basic(password_payload)
        await cls.ensure_login_not_locked(username=username)

        raw_password = PasswordTransportService.resolve(password_payload)
        user = await AuthUserRepository.get_active_user_by_username(username)

        if not user:
            await cls.record_login_failed(username=username, user=None, client_ip=client_ip, user_agent=user_agent)
            raise BusinessError("username or password incorrect", NsErrorCode.USERNAME_OR_PASSWORD_INCORRECT)

        password_ok = False
        if isinstance(user.password, str):
            try:
                password_ok = check_password(raw_password, user.password)
            except Exception:  # noqa
                password_ok = False

        if not password_ok:
            await cls.record_login_failed(username=username, user=user, client_ip=client_ip, user_agent=user_agent)
            raise BusinessError("username or password incorrect", NsErrorCode.USERNAME_OR_PASSWORD_INCORRECT)

        now = timezone.now()
        device_payload = cls.get_device_payload(data)
        fingerprint_hash = sha256_text(device_payload["fingerprint"])

        access_token, access_jti = JwtService.create_access_token(user_id=user.id, user_type=user.user_type)
        refresh_token, refresh_token_hash, refresh_jti, refresh_expired_at = JwtService.create_refresh_token(user_id=user.id)

        session_public_id = uuid.uuid4().hex
        session, device = await AuthLoginBundleRepository.create_login_bundle_with_device(
            user_id=user.id,
            device_payload=device_payload,
            fingerprint_hash=fingerprint_hash,
            client_ip=client_ip,
            user_agent=user_agent,
            session_public_id=session_public_id,
            session_expired_at=now + timedelta(minutes=cls.SESSION_EXPIRE_MINUTES),
            refresh_token_hash=refresh_token_hash,
            access_jti=access_jti,
            refresh_jti=refresh_jti,
            token_expired_at=refresh_expired_at,
            now=now,
        )

        await cls.clear_login_failure(username=username, user_id=user.id)

        return AuthLoginResult(
            user=user,
            data={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "session_id": session_public_id,
                "device_id": device.device_id,
                "expires_in": int(getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 30)) * 60,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "display_name": user.display_name,
                    "user_type": user.user_type,
                },
            },
        )

    @classmethod
    async def refresh(cls, *, data: dict[str, Any]) -> dict[str, Any]:
        refresh_token = str(data.get("refresh_token", "")).strip()
        if not refresh_token:
            raise BusinessError("refresh token cannot be empty", NsErrorCode.REFRESH_TOKEN_EMPTY)

        payload = JwtService.decode_refresh_token(refresh_token)
        if not payload:
            raise BusinessError("refresh token invalid or expired", NsErrorCode.REFRESH_TOKEN_INVALID_OR_EXPIRED)

        user_id = payload.get("uid")
        refresh_jti = payload.get("jti")
        if not isinstance(user_id, int) or not isinstance(refresh_jti, str):
            raise BusinessError("refresh token invalid or expired", NsErrorCode.REFRESH_TOKEN_INVALID_OR_EXPIRED)

        refresh_token_hash = JwtService.hash_token(refresh_token)
        result = await sync_to_async(RefreshTokenRotationService.rotate, thread_sensitive=True)(
            user_id=user_id,
            refresh_jti=refresh_jti,
            refresh_token_hash=refresh_token_hash,
        )

        return {
            "access_token": result.access_token,
            "refresh_token": result.refresh_token,
            "token_type": result.token_type,
            "expires_in": result.expires_in,
            "session_id": result.session_id,
        }

    @classmethod
    async def logout(cls, *, data: dict[str, Any], request) -> dict[str, Any]:
        logout_all = cls.is_truthy(data.get("logout_all"))
        user, token_record = await cls.resolve_user_from_request(request)
        now = timezone.now()

        if logout_all:
            await UserSessionRepository.revoke_user_sessions_and_tokens(user_id=user.id, revoked_at=now)
            return {"success": True, "logout_all": True}

        refresh_revoked = False
        refresh_token = str(data.get("refresh_token", "") or "").strip()
        if refresh_token:
            payload = JwtService.decode_refresh_token(refresh_token)
            if payload:
                refresh_user_id = payload.get("uid")
                refresh_jti = payload.get("jti")
                if refresh_user_id != user.id:
                    raise BusinessError("Refresh token does not match the current user", NsErrorCode.REFRESH_TOKEN_USER_MISMATCH)
                refresh_token_hash = JwtService.hash_token(refresh_token)
                updated_count = await UserTokenRepository.revoke_refresh_token(user_id=user.id, refresh_jti=refresh_jti, refresh_token_hash=refresh_token_hash, revoked_at=now)
                refresh_revoked = updated_count > 0

        access_revoked = await UserTokenRepository.revoke_token_session(token_record=token_record, revoked_at=now)

        return {
            "success": access_revoked or refresh_revoked,
            "access_revoked": access_revoked,
            "refresh_revoked": refresh_revoked,
        }

    @staticmethod
    def build_current_user_payload(user) -> dict[str, Any]:
        return {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "email": user.email,
            "phone": user.phone,
            "user_type": user.user_type,
            "company_id": user.company_id,
            "subsidiary_id": user.subsidiary_id,
            "department_id": user.department_id,
            "is_active": user.is_active,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        }
