# -*- coding: utf-8 -*-
from __future__ import annotations

import uuid
from datetime import timedelta
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.utils import timezone

from ns_common.error_codes import NsErrorCode
from iam.repositories.login_failure import LoginFailureRepository
from iam.repositories.session import SessionRepository
from iam.repositories.token import TokenRepository
from iam.repositories.user import UserRepository
from iam.services.session import SessionService
from ns_backend.exceptions import BusinessError
from ns_backend.logging import emit_log_event, short_identifier
from ns_backend.security import PasswordTransportService
from ns_backend.utils.jwt import JwtService
from ns_common.logging import NsLogEvent

if TYPE_CHECKING:
    from iam.models import IamUser


class LoginFailureService:
    """登录失败锁定服务。"""

    LOGIN_MAX_FAILED_COUNT = settings.LOGIN_MAX_FAILED_COUNT
    LOGIN_LOCK_MINUTES = settings.LOGIN_LOCK_MINUTES

    @classmethod
    async def ensure_not_locked(cls, username: str) -> None:
        record = await LoginFailureRepository.get_by_username(username)

        if not record or not record.locked_until:
            return

        now = timezone.now()

        if record.locked_until > now:
            raise BusinessError(
                msg="Account is locked due to consecutive login failures, please try again later",
                code=NsErrorCode.ACCOUNT_LOCKED,
                data={"locked_until": record.locked_until.isoformat()},
            )

        await LoginFailureRepository.reset_record(record)

    @classmethod
    async def record_failed(
            cls,
            username: str,
            user: IamUser | None,
            client_ip: str | None = None,
            user_agent: str | None = None,
    ) -> None:
        await LoginFailureRepository.record_failed(
            username=username,
            user=user,
            max_failed_count=cls.LOGIN_MAX_FAILED_COUNT,
            lock_minutes=cls.LOGIN_LOCK_MINUTES,
            client_ip=client_ip,
            user_agent=user_agent,
        )

    @classmethod
    async def clear(cls, username: str) -> None:
        await LoginFailureRepository.clear_by_username(username)


class LoginService:
    """登录服务。"""

    @classmethod
    async def execute(
            cls,
            username: str,
            password: str,
            client_ip: str | None = None,
            user_agent: str | None = None,
            device_name: str | None = None,
            device_type: str | None = None,
            fingerprint_raw: str | None = None,
            os_name: str | None = None,
            browser_name: str | None = None,
    ) -> dict:
        if not isinstance(username, str):
            raise BusinessError("username cannot be empty", NsErrorCode.USERNAME_EMPTY)

        if not isinstance(password, str):
            raise BusinessError("password cannot be empty", NsErrorCode.PASSWORD_EMPTY)

        username = username.strip()

        if not username:
            raise BusinessError("username cannot be empty", NsErrorCode.USERNAME_EMPTY)

        PasswordTransportService.validate_payload_basic(password)

        await LoginFailureService.ensure_not_locked(username=username)

        raw_password = PasswordTransportService.resolve(password)

        user = await UserRepository.get_active_by_username(username)

        if not user:
            await LoginFailureService.record_failed(
                username=username,
                user=None,
                client_ip=client_ip,
                user_agent=user_agent,
            )
            raise BusinessError("Username or password is incorrect.", NsErrorCode.USERNAME_OR_PASSWORD_INCORRECT)

        if not check_password(raw_password, user.password):
            await LoginFailureService.record_failed(
                username=username,
                user=user,
                client_ip=client_ip,
                user_agent=user_agent,
            )
            raise BusinessError("Username or password is incorrect.", NsErrorCode.USERNAME_OR_PASSWORD_INCORRECT)

        fingerprint_raw = fingerprint_raw or cls.build_fallback_fingerprint(
            username=username,
            client_ip=client_ip,
            user_agent=user_agent,
        )

        access_token, access_jti = JwtService.create_access_token(
            user_id=user.id,
            user_type=user.user_type,
        )

        refresh_token, refresh_token_hash, refresh_jti, refresh_expired_at = (
            JwtService.create_refresh_token(user_id=user.id)
        )

        session_id = uuid.uuid4().hex
        session_now = timezone.now()
        session, device = await SessionRepository.create_login_bundle_with_device(
            user_id=user.id,
            device_name=device_name or "Unknown Device",
            device_type=device_type or "WEB",
            fingerprint_raw=fingerprint_raw,
            user_agent=user_agent,
            client_ip=client_ip,
            os_name=os_name,
            browser_name=browser_name,
            session_id=session_id,
            risk_level=0,
            last_active_at=session_now,
            session_expired_at=session_now + timedelta(minutes=SessionService.DEFAULT_EXPIRED_MINUTES),
            refresh_token_hash=refresh_token_hash,
            access_jti=access_jti,
            refresh_jti=refresh_jti,
            token_expired_at=refresh_expired_at,
        )

        try:
            await LoginFailureService.clear(username=username)
        except Exception as exc:  # noqa
            emit_log_event(
                event=NsLogEvent.SYSTEM_EXCEPTION,
                message="login failure clear failed",
                level="WARNING",
                user_id=user.id,
                context={
                    "stage": "login_failure_clear",
                    "exception_type": exc.__class__.__name__,
                },
                exc_info=True,
            )
            pass

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": JwtService.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "session_id": session.session_id,
            "device_id": device.device_id,
        }

    @staticmethod
    def build_fallback_fingerprint(
            username: str,
            client_ip: str | None = None,
            user_agent: str | None = None,
    ) -> str:
        return "|".join(
            [
                username,
                client_ip or "",
                user_agent or "",
            ]
        )


class LogoutService:
    """登出服务。"""

    @classmethod
    async def execute(cls, refresh_token: str, current_user_id: int | None = None) -> bool:
        if not isinstance(refresh_token, str) or not refresh_token:
            return False

        try:
            payload = JwtService.decode_refresh_token(refresh_token)
        except Exception:  # noqa
            return False

        if not payload:
            return False

        refresh_jti = payload.get("jti")
        user_id = payload.get("uid")

        if not refresh_jti or not user_id:
            return False

        if current_user_id is not None and user_id != current_user_id:
            raise BusinessError("Refresh token does not match the current user", NsErrorCode.REFRESH_TOKEN_USER_MISMATCH)

        refresh_token_hash = JwtService.hash_token(refresh_token)

        token_record = await TokenRepository.get_refresh_token(
            user_id=user_id,
            refresh_jti=refresh_jti,
            refresh_token_hash=refresh_token_hash,
        )

        if not token_record or token_record.revoked_at:
            return False

        if token_record.session_id:
            return await SessionService.revoke_session_by_pk(token_record.session_id)

        updated_count = await TokenRepository.revoke_token(token_record.id)

        return updated_count > 0


class RefreshService:
    """刷新令牌服务。"""

    @classmethod
    async def execute(cls, refresh_token: str) -> dict:
        payload = JwtService.decode_refresh_token(refresh_token)

        if not payload:
            raise BusinessError("Refresh token is invalid or expired", NsErrorCode.REFRESH_TOKEN_INVALID_OR_EXPIRED)

        refresh_jti = payload.get("jti")
        user_id = payload.get("uid")

        if not refresh_jti or not user_id:
            raise BusinessError("Refresh token is invalid", NsErrorCode.REFRESH_TOKEN_INVALID_OR_EXPIRED)

        refresh_token_hash = JwtService.hash_token(refresh_token)

        access_jti = JwtService.create_access_jti()

        new_refresh_token, new_refresh_token_hash, new_refresh_jti, new_refresh_expired_at = (
            JwtService.create_refresh_token(user_id=user_id)
        )

        try:
            rotate_status, rotated_token, session_pk, session_public_id, locked_user_type = await TokenRepository.rotate_refresh_token_with_guard(
                user_id=user_id,
                refresh_jti=refresh_jti,
                refresh_token_hash=refresh_token_hash,
                new_token_data={
                    "refresh_token_hash": new_refresh_token_hash,
                    "access_jti": access_jti,
                    "refresh_jti": new_refresh_jti,
                    "expired_at": new_refresh_expired_at,
                    "created_at": timezone.now(),
                },
            )
        except BusinessError as exc:
            if exc.code in NsErrorCode.TOKEN_ROTATION_REJECT_CODES:
                emit_log_event(
                    event=NsLogEvent.IAM_REFRESH_REJECTED,
                    message="refresh token rotation rejected",
                    level="WARNING",
                    user_id=user_id,
                    error_code=exc.code,
                    context={
                        "refresh_jti": short_identifier(refresh_jti),
                        "exception_type": exc.__class__.__name__,
                    },
                    exc_info=True,
                )
                raise BusinessError("Refresh token has been revoked", NsErrorCode.REFRESH_TOKEN_INVALID_OR_EXPIRED)
            raise

        if rotate_status == "replayed":
            emit_log_event(
                event=NsLogEvent.IAM_REFRESH_REPLAY_DETECTED,
                message="refresh token replay detected",
                level="WARNING",
                user_id=user_id,
                error_code=NsErrorCode.REFRESH_TOKEN_REPLAY_DETECTED,
                context={
                    "refresh_jti": short_identifier(refresh_jti),
                    "session_pk": session_pk,
                },
            )
            if session_pk:
                await SessionService.revoke_session_by_pk(session_pk)
            else:
                await TokenRepository.revoke_user_tokens(user_id=user_id)
            raise BusinessError(
                "Refresh token replay detected, current session has been forcibly logged out",
                NsErrorCode.REFRESH_TOKEN_REPLAY_DETECTED,
            )

        if rotate_status == "user_inactive":
            if session_pk:
                await SessionService.revoke_session_by_pk(session_pk)
            else:
                await TokenRepository.revoke_user_tokens(user_id=user_id)
            raise BusinessError("User does not exist or is disabled", NsErrorCode.USER_DISABLED_OR_NOT_FOUND)

        if rotate_status == "session_unavailable":
            raise BusinessError("Refresh token has been revoked", NsErrorCode.REFRESH_TOKEN_INVALID_OR_EXPIRED)

        if rotate_status != "rotated":
            raise BusinessError("Refresh token has been revoked", NsErrorCode.REFRESH_TOKEN_INVALID_OR_EXPIRED)

        if not locked_user_type:
            raise BusinessError("User does not exist or is disabled", NsErrorCode.USER_DISABLED_OR_NOT_FOUND)

        access_token, _ = JwtService.create_access_token(
            user_id=user_id,
            user_type=locked_user_type,
            access_jti=access_jti,
        )

        if session_pk:
            await SessionService.touch_activity_by_pk(
                session_pk=session_pk,
                client_ip=rotated_token.client_ip if rotated_token else None,
                user_agent=rotated_token.user_agent if rotated_token else None,
            )

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "Bearer",
            "expires_in": JwtService.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "session_id": session_public_id,
        }


class RevokeService:
    """令牌吊销服务。"""

    @classmethod
    async def revoke_access_token(cls, access_token: str) -> bool:
        payload = JwtService.decode_access_token(access_token)

        if not payload:
            return False

        user_id = payload.get("uid")
        access_jti = payload.get("jti")

        if not user_id or not access_jti:
            return False

        token_record = await TokenRepository.get_valid_access_token(
            user_id=user_id,
            access_jti=access_jti,
        )

        if not token_record:
            return False

        if token_record.session_id:
            return await SessionService.revoke_session_by_pk(token_record.session_id)

        updated_count = await TokenRepository.revoke_token(token_record.id)

        return updated_count > 0

    @classmethod
    async def revoke_user_sessions_and_tokens(cls, user_id: int) -> None:
        await SessionService.revoke_user_sessions(user_id=user_id)

    @classmethod
    async def revoke_user_tokens(cls, user_id: int) -> None:
        await cls.revoke_user_sessions_and_tokens(user_id=user_id)


class VerifyService:
    """访问令牌校验服务。"""

    @classmethod
    async def get_user_by_access_token(cls, access_token: str):
        payload = JwtService.decode_access_token(access_token)

        if not payload:
            return None

        user_id = payload.get("uid")
        access_jti = payload.get("jti")

        if not user_id or not access_jti:
            return None

        token_record = await TokenRepository.get_valid_access_token_with_session(
            user_id=user_id,
            access_jti=access_jti,
        )

        if not token_record:
            return None

        return token_record.user


__all__ = [
    "LoginService",
    "LogoutService",
    "RefreshService",
    "RevokeService",
    "VerifyService",
]
