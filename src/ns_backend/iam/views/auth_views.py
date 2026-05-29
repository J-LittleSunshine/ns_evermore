# -*- coding: utf-8 -*-
from __future__ import annotations

import secrets
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from django.contrib.auth.hashers import check_password
from django.utils import timezone

from ns_common.error_codes import NsErrorCode
from ..models import IamUser, IamUserDevice, IamUserSession, IamUserToken
from ..services import AuthContextService
from ..utils import sha256_text, build_access_token, get_bearer_token_from_request, parse_access_token
from ...backend.common.validators import AuthRequestValidator
from ...backend.common.viewset import BaseRequestViewSet
from ...backend.exceptions import BusinessError

if TYPE_CHECKING:
    pass


class AuthViewSet(BaseRequestViewSet):
    @staticmethod
    def _is_truthy(value: Any) -> bool:
        return value in (True, 1, "1", "true", "True", "yes", "YES", "on", "ON")

    @classmethod
    async def resolve_user_from_request(cls, request):
        bearer_token = get_bearer_token_from_request(request)
        if not bearer_token:
            raise BusinessError("User is not logged in or session has expired", NsErrorCode.USER_NOT_LOGGED_IN_OR_SESSION_EXPIRED)

        parsed = parse_access_token(bearer_token)
        if parsed is None:
            raise BusinessError("User is not logged in or session has expired", NsErrorCode.USER_NOT_LOGGED_IN_OR_SESSION_EXPIRED)

        user_id, access_jti = parsed
        now = timezone.now()

        token_record = await IamUserToken.objects.filter(user_id=user_id, access_jti=access_jti, revoked_at__isnull=True, expired_at__gt=now).afirst()
        if token_record is None:
            raise BusinessError("User is not logged in or session has expired", NsErrorCode.USER_NOT_LOGGED_IN_OR_SESSION_EXPIRED)

        user = await IamUser.objects.filter(id=user_id, is_active=1).afirst()
        if user is None:
            raise BusinessError("User disabled or not found", NsErrorCode.USER_DISABLED_OR_NOT_FOUND)

        return user, token_record

    async def login(self, request, *args, **kwargs):
        username = str(request.data.get("username", "")).strip()
        password = str(request.data.get("password", "")).strip()
        if not username:
            raise BusinessError("username cannot be empty", NsErrorCode.USERNAME_EMPTY)
        if not password:
            raise BusinessError("password cannot be empty", NsErrorCode.PASSWORD_EMPTY)

        user = await IamUser.objects.filter(username=username, is_active=1).afirst()
        if not user:
            raise BusinessError("username or password incorrect", NsErrorCode.USERNAME_OR_PASSWORD_INCORRECT)

        password_ok = False
        if isinstance(user.password, str):
            try:
                password_ok = check_password(password, user.password)
            except Exception:  # noqa
                password_ok = False

        if not password_ok:
            password_ok = user.password == password

        if not password_ok:
            raise BusinessError("username or password incorrect", NsErrorCode.USERNAME_OR_PASSWORD_INCORRECT)

        now = timezone.now()
        device_id = str(request.data.get("device_id", "")).strip() or secrets.token_hex(16)
        user_agent = str(request.headers.get("User-Agent", ""))[:512]
        client_ip = str(request.META.get("REMOTE_ADDR", "") or "")[:64]

        device = await IamUserDevice.objects.filter(device_id=device_id, user_id=user.id).afirst()
        if not device:
            device = await IamUserDevice.objects.acreate(
                user_id=user.id,
                device_id=device_id,
                device_name="unknown",
                device_type="unknown",
                fingerprint_hash=sha256_text(device_id),
                trusted=0,
                status=1,
                first_login_at=now,
                last_active_at=now,
                last_client_ip=client_ip or None,
                created_at=now,
                updated_at=now,
            )
        else:
            device.last_active_at = now
            device.last_client_ip = client_ip or None
            device.updated_at = now
            await device.asave(update_fields=["last_active_at", "last_client_ip", "updated_at"])

        session_public_id = secrets.token_hex(16)
        session = await IamUserSession.objects.acreate(
            user_id=user.id,
            device_id=device.id,
            session_id=session_public_id,
            login_ip=client_ip or None,
            user_agent=user_agent or None,
            risk_level=0,
            last_active_at=now,
            expired_at=now + timedelta(days=7),
            revoked_at=None,
            created_at=now,
        )

        access_jti = secrets.token_hex(16)
        refresh_jti = secrets.token_hex(16)
        refresh_token = secrets.token_urlsafe(48)

        await IamUserToken.objects.acreate(
            user_id=user.id,
            session_id=session.id,
            refresh_token_hash=sha256_text(refresh_token),
            access_jti=access_jti,
            refresh_jti=refresh_jti,
            client_ip=client_ip or None,
            user_agent=user_agent or None,
            expired_at=session.expired_at,
            revoked_at=None,
            created_at=now,
        )

        user.last_login = now
        await user.asave(update_fields=["last_login"])

        return self.success_response(
            {
                "access_token": build_access_token(user.id, access_jti),
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "session_id": session_public_id,
                "expires_in": 7 * 24 * 3600,
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

        now = timezone.now()
        old_token = await IamUserToken.objects.filter(refresh_token_hash=sha256_text(refresh_token), revoked_at__isnull=True, expired_at__gt=now).afirst()
        if not old_token:
            raise BusinessError("refresh token invalid or expired", NsErrorCode.REFRESH_TOKEN_INVALID_OR_EXPIRED)

        old_token.revoked_at = now
        await old_token.asave(update_fields=["revoked_at"])

        new_access_jti = secrets.token_hex(16)
        new_refresh_jti = secrets.token_hex(16)
        new_refresh_token = secrets.token_urlsafe(48)

        new_token = await IamUserToken.objects.acreate(
            user_id=old_token.user_id,
            session_id=old_token.session_id,
            refresh_token_hash=sha256_text(new_refresh_token),
            access_jti=new_access_jti,
            refresh_jti=new_refresh_jti,
            client_ip=old_token.client_ip,
            user_agent=old_token.user_agent,
            expired_at=old_token.expired_at,
            revoked_at=None,
            created_at=now,
        )

        expires_in = max(int((new_token.expired_at - now).total_seconds()), 0)
        return self.success_response(
            {
                "access_token": build_access_token(new_token.user_id, new_access_jti),
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": expires_in,
            }
        )

    async def logout(self, request, *args, **kwargs):
        logout_all = self._is_truthy(request.data.get("logout_all"))

        if logout_all:
            user, _ = await self.resolve_user_from_request(request)
            now = timezone.now()
            await IamUserToken.objects.filter(user_id=user.id, revoked_at__isnull=True).aupdate(revoked_at=now)
            return self.success_response()

        refresh_token = str(request.data.get("refresh_token", "")).strip()
        if not refresh_token:
            raise BusinessError("refresh token cannot be empty", NsErrorCode.REFRESH_TOKEN_EMPTY)

        token = await IamUserToken.objects.filter(refresh_token_hash=sha256_text(refresh_token), revoked_at__isnull=True).afirst()
        if token:
            token.revoked_at = timezone.now()
            await token.asave(update_fields=["revoked_at"])

        return self.success_response()

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
