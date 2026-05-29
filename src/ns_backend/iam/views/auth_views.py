# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from django.contrib.auth.hashers import check_password
from django.utils import timezone

from ns_common.error_codes import NsErrorCode
from ..models import IamUser, IamUserDevice, IamUserSession, IamUserToken
from ..services import AuthContextService
from ..utils import sha256_text, get_bearer_token_from_request
from ...backend.common.validators import AuthRequestValidator
from ...backend.common.viewset import BaseRequestViewSet
from ...backend.exceptions import BusinessError

if TYPE_CHECKING:
    pass


class AuthViewSet(BaseRequestViewSet):
    SESSION_EXPIRE_MINUTES = 43200

    @staticmethod
    def _is_truthy(value: Any) -> bool:
        return value in (True, 1, "1", "true", "True", "yes", "YES", "on", "ON")

    @classmethod
    async def resolve_user_from_request(cls, request) -> tuple[IamUser, IamUserToken]:
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
        token_record = await IamUserToken.objects.select_related("user", "session").filter(user_id=user_id, access_jti=access_jti, revoked_at__isnull=True, expired_at__gt=now).afirst()
        if token_record is None:
            raise BusinessError("User is not logged in or session has expired", NsErrorCode.USER_NOT_LOGGED_IN_OR_SESSION_EXPIRED)

        session = getattr(token_record, "session", None)
        if session is not None:
            if session.revoked_at is not None or session.expired_at <= now:
                raise BusinessError("User is not logged in or session has expired", NsErrorCode.USER_NOT_LOGGED_IN_OR_SESSION_EXPIRED)

        user = getattr(token_record, "user", None)
        if user is None:
            user = await IamUser.objects.filter(id=user_id).afirst()

        if user is None or not bool(getattr(user, "is_active", False)):
            raise BusinessError("User disabled or not found", NsErrorCode.USER_DISABLED_OR_NOT_FOUND)

        return user, token_record

    @classmethod
    async def ensure_login_not_locked(cls, username: str) -> None:
        record = await IamLoginFailureLock.objects.filter(username=username).afirst()
        if record is None or record.locked_until is None:
            return

        now = timezone.now()
        if record.locked_until > now:
            raise BusinessError(
                "Account is locked due to consecutive login failures, please try again later",
                NsErrorCode.ACCOUNT_LOCKED,
                data={"locked_until": record.locked_until.isoformat()},
            )

        record.failed_count = 0
        record.locked_until = None
        record.updated_at = now
        await record.asave(update_fields=["failed_count", "locked_until", "updated_at"])

    @classmethod
    async def record_login_failed(cls, *, username: str, user: IamUser | None, client_ip: str | None, user_agent: str | None) -> None:
        now = timezone.now()
        max_failed_count = int(getattr(settings, "LOGIN_MAX_FAILED_COUNT", 5))
        lock_minutes = int(getattr(settings, "LOGIN_LOCK_MINUTES", 15))

        record = await IamLoginFailureLock.objects.filter(username=username).afirst()
        if record is None:
            failed_count = 1
            locked_until = now + timedelta(minutes=lock_minutes) if failed_count >= max_failed_count else None
            await IamLoginFailureLock.objects.acreate(
                username=username,
                user_id=getattr(user, "id", None),
                failed_count=failed_count,
                locked_until=locked_until,
                last_failed_at=now,
                last_client_ip=client_ip,
                last_user_agent=user_agent,
                created_at=now,
                updated_at=now,
            )
            return

        failed_count = int(record.failed_count or 0) + 1
        record.user_id = getattr(user, "id", None)
        record.failed_count = failed_count
        record.locked_until = now + timedelta(minutes=lock_minutes) if failed_count >= max_failed_count else None
        record.last_failed_at = now
        record.last_client_ip = client_ip
        record.last_user_agent = user_agent
        record.updated_at = now
        await record.asave(update_fields=["user_id", "failed_count", "locked_until", "last_failed_at", "last_client_ip", "last_user_agent", "updated_at"])

    @staticmethod
    async def clear_login_failure(username: str) -> None:
        await IamLoginFailureLock.objects.filter(username=username).adelete()

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
    def get_device_payload(request) -> dict[str, str]:
        data = request.data if isinstance(request.data, dict) else {}

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

    async def login(self, request, *args, **kwargs):
        username = str(request.data.get("username", "")).strip()
        password_payload = str(request.data.get("password", "")).strip()

        if not username:
            raise BusinessError("username cannot be empty", NsErrorCode.USERNAME_EMPTY)
        if not password_payload:
            raise BusinessError("password cannot be empty", NsErrorCode.PASSWORD_EMPTY)

        client_ip = self.get_client_ip(request)
        user_agent = self.get_user_agent(request)

        PasswordTransportService.validate_payload_basic(password_payload)
        await self.ensure_login_not_locked(username=username)

        raw_password = PasswordTransportService.resolve(password_payload)
        user = await IamUser.objects.filter(username=username, is_active=1).afirst()

        if not user:
            await self.record_login_failed(username=username, user=None, client_ip=client_ip, user_agent=user_agent)
            raise BusinessError("username or password incorrect", NsErrorCode.USERNAME_OR_PASSWORD_INCORRECT)

        password_ok = False
        if isinstance(user.password, str):
            try:
                password_ok = check_password(raw_password, user.password)
            except Exception:  # noqa
                password_ok = False

        if not password_ok:
            await self.record_login_failed(username=username, user=user, client_ip=client_ip, user_agent=user_agent)
            raise BusinessError("username or password incorrect", NsErrorCode.USERNAME_OR_PASSWORD_INCORRECT)

        now = timezone.now()
        device_payload = self.get_device_payload(request)
        fingerprint_hash = sha256_text(device_payload["fingerprint"])

        device = await IamUserDevice.objects.filter(user_id=user.id, fingerprint_hash=fingerprint_hash).afirst()
        if not device:
            device = await IamUserDevice.objects.acreate(
                user_id=user.id,
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
        else:
            device.device_name = device_payload["device_name"]
            device.device_type = device_payload["device_type"]
            device.os_name = device_payload["os_name"] or None
            device.browser_name = device_payload["browser_name"] or None
            device.last_active_at = now
            device.last_client_ip = client_ip
            device.updated_at = now
            await device.asave(update_fields=["device_name", "device_type", "os_name", "browser_name", "last_active_at", "last_client_ip", "updated_at"])

        access_token, access_jti = JwtService.create_access_token(user_id=user.id, user_type=user.user_type)
        refresh_token, refresh_token_hash, refresh_jti, refresh_expired_at = JwtService.create_refresh_token(user_id=user.id)

        session_public_id = uuid.uuid4().hex
        session = await IamUserSession.objects.acreate(
            user_id=user.id,
            device_id=device.id,
            session_id=session_public_id,
            login_ip=client_ip,
            user_agent=user_agent,
            risk_level=0,
            last_active_at=now,
            expired_at=now + timedelta(minutes=self.SESSION_EXPIRE_MINUTES),
            revoked_at=None,
            created_at=now,
        )

        await IamUserToken.objects.acreate(
            user_id=user.id,
            session_id=session.id,
            refresh_token_hash=refresh_token_hash,
            access_jti=access_jti,
            refresh_jti=refresh_jti,
            client_ip=client_ip,
            user_agent=user_agent,
            expired_at=refresh_expired_at,
            revoked_at=None,
            created_at=now,
        )

        user.last_login = now
        await user.asave(update_fields=["last_login"])
        await self.clear_login_failure(username=username)

        return self.success_response(
            {
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
            }
        )

    async def refresh(self, request, *args, **kwargs):
        refresh_token = str(request.data.get("refresh_token", "")).strip()
        if not refresh_token:
            raise BusinessError("refresh token cannot be empty", NsErrorCode.REFRESH_TOKEN_EMPTY)

        payload = JwtService.decode_refresh_token(refresh_token)
        if not payload:
            raise BusinessError("refresh token invalid or expired", NsErrorCode.REFRESH_TOKEN_INVALID_OR_EXPIRED)

        user_id = payload.get("uid")
        refresh_jti = payload.get("jti")
        if not isinstance(user_id, int) or not isinstance(refresh_jti, str):
            raise BusinessError("refresh token invalid or expired", NsErrorCode.REFRESH_TOKEN_INVALID_OR_EXPIRED)

        now = timezone.now()
        refresh_token_hash = JwtService.hash_token(refresh_token)

        old_token = await IamUserToken.objects.select_related("user", "session").filter(user_id=user_id, refresh_jti=refresh_jti, refresh_token_hash=refresh_token_hash, revoked_at__isnull=True, expired_at__gt=now).afirst()
        if not old_token:
            raise BusinessError("refresh token invalid or expired", NsErrorCode.REFRESH_TOKEN_INVALID_OR_EXPIRED)

        user = getattr(old_token, "user", None)
        if user is None or not bool(getattr(user, "is_active", False)):
            raise BusinessError("User disabled or not found", NsErrorCode.USER_DISABLED_OR_NOT_FOUND)

        session = getattr(old_token, "session", None)
        if session is not None:
            if session.revoked_at is not None or session.expired_at <= now:
                raise BusinessError("refresh token invalid or expired", NsErrorCode.REFRESH_TOKEN_INVALID_OR_EXPIRED)
            session.last_active_at = now
            session.login_ip = old_token.client_ip
            session.user_agent = old_token.user_agent
            await session.asave(update_fields=["last_active_at", "login_ip", "user_agent"])

        old_token.revoked_at = now
        await old_token.asave(update_fields=["revoked_at"])

        new_access_token, new_access_jti = JwtService.create_access_token(user_id=user.id, user_type=user.user_type)
        new_refresh_token, new_refresh_token_hash, new_refresh_jti, new_refresh_expired_at = JwtService.create_refresh_token(user_id=user.id)

        await IamUserToken.objects.acreate(
            user_id=user.id,
            session_id=old_token.session_id,
            refresh_token_hash=new_refresh_token_hash,
            access_jti=new_access_jti,
            refresh_jti=new_refresh_jti,
            client_ip=old_token.client_ip,
            user_agent=old_token.user_agent,
            expired_at=new_refresh_expired_at,
            revoked_at=None,
            created_at=now,
        )

        return self.success_response(
            {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "Bearer",
                "expires_in": int(getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 30)) * 60,
                "session_id": getattr(session, "session_id", None),
            }
        )

    async def refresh_token(self, request, *args, **kwargs):
        return await self.refresh(request, *args, **kwargs)

    async def logout(self, request, *args, **kwargs):
        logout_all = self._is_truthy(request.data.get("logout_all"))
        user, token_record = await self.resolve_user_from_request(request)
        now = timezone.now()

        if logout_all:
            await IamUserToken.objects.filter(user_id=user.id, revoked_at__isnull=True).aupdate(revoked_at=now)
            await IamUserSession.objects.filter(user_id=user.id, revoked_at__isnull=True).aupdate(revoked_at=now)
            return self.success_response({"success": True, "logout_all": True})

        refresh_revoked = False
        refresh_token = str(request.data.get("refresh_token", "") or "").strip()
        if refresh_token:
            payload = JwtService.decode_refresh_token(refresh_token)
            if payload:
                refresh_user_id = payload.get("uid")
                refresh_jti = payload.get("jti")
                if refresh_user_id != user.id:
                    raise BusinessError("Refresh token does not match the current user", NsErrorCode.REFRESH_TOKEN_USER_MISMATCH)
                refresh_token_hash = JwtService.hash_token(refresh_token)
                updated_count = await IamUserToken.objects.filter(user_id=user.id, refresh_jti=refresh_jti, refresh_token_hash=refresh_token_hash, revoked_at__isnull=True).aupdate(revoked_at=now)
                refresh_revoked = updated_count > 0

        access_revoked = await self.revoke_token_session(token_record=token_record, now=now)

        return self.success_response(
            {
                "success": access_revoked or refresh_revoked,
                "access_revoked": access_revoked,
                "refresh_revoked": refresh_revoked,
            }
        )

    @staticmethod
    async def revoke_token_session(*, token_record: IamUserToken, now) -> bool:
        if token_record.session_id:
            await IamUserSession.objects.filter(id=token_record.session_id, revoked_at__isnull=True).aupdate(revoked_at=now)
            updated_count = await IamUserToken.objects.filter(session_id=token_record.session_id, revoked_at__isnull=True).aupdate(revoked_at=now)
            return updated_count > 0

        if token_record.revoked_at is None:
            token_record.revoked_at = now
            await token_record.asave(update_fields=["revoked_at"])
            return True

        return False

    async def profile(self, request, *args, **kwargs):
        user, _ = await self.resolve_user_from_request(request)
        data = AuthContextService.build_profile(user)
        return self.success_response(data)

    async def current_user(self, request, *args, **kwargs):
        user, _ = await self.resolve_user_from_request(request)
        return self.success_response(
            {
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
        )

    async def permissions(self, request, *args, **kwargs):
        user, _ = await self.resolve_user_from_request(request)
        permission_codes = await AuthContextService.list_permission_codes(user)
        return self.success_response({"permissions": permission_codes})

    async def menus(self, request, *args, **kwargs):
        user, _ = await self.resolve_user_from_request(request)
        menus = await AuthContextService.list_menu_tree(user)
        return self.success_response({"menus": menus})

    async def data_scopes(self, request, *args, **kwargs):
        user, _ = await self.resolve_user_from_request(request)
        clean_codes = AuthRequestValidator.validate_data_scope_codes(request.data)
        items = await AuthContextService.list_data_scopes(user=user, permission_codes=clean_codes)
        return self.success_response({"items": items})
