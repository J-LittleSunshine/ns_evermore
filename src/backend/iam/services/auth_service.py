# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.hashers import check_password
from django.utils import timezone

from iam import IAM_DB_ALIAS
from iam.models import IamUser, IamUserToken
from iam.services.jwt_service import JwtService

if TYPE_CHECKING:
    pass


class AuthService:
    @classmethod
    async def login(cls, username: str, password: str, client_ip: str | None = None, user_agent: str | None = None) -> dict:
        user = await IamUser.objects.filter(username=username, is_active=1).afirst()

        if not user:
            raise ValueError("Username or password is incorrect.")

        if not check_password(password, user.password):
            raise ValueError("Username or password is incorrect.")

        access_token, access_jti = JwtService.create_access_token(user_id=user.id, user_type=user.user_type)

        refresh_token, refresh_jti, refresh_expired_at = JwtService.create_refresh_token(user_id=user.id)
        user_token_data = {
            "user_id": user.id,
            "refresh_token": refresh_token,
            "access_jti": access_jti,
            "refresh_jti": refresh_jti,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "expired_at": refresh_expired_at
        }
        await IamUserToken.objects.using(IAM_DB_ALIAS).acreate(**user_token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": JwtService.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    @classmethod
    async def get_user_by_access_token(cls, access_token: str) -> IamUser | None:
        payload = JwtService.decode_access_token(access_token)

        if not payload:
            return None

        user_id = payload.get("uid")

        if not user_id:
            return None

        return await IamUser.objects.using(IAM_DB_ALIAS).filter(id=user_id, is_active=1).afirst()

    @classmethod
    async def refresh_access_token(cls, refresh_token: str) -> dict:
        payload = JwtService.decode_refresh_token(refresh_token)

        if not payload:
            raise ValueError("Refresh Token invalid or expired.")

        refresh_jti = payload.get("jti")
        user_id = payload.get("uid")

        if not refresh_jti or not user_id:
            raise ValueError("Refresh Token invalid.")

        token_record = await IamUserToken.objects.using(IAM_DB_ALIAS).filter(
            refresh_jti=refresh_jti,
            user_id=user_id,
            revoked_at__isnull=True,
            expired_at__gt=timezone.now(),
        ).afirst()

        if not token_record:
            raise ValueError("Refresh Token 已失效")

        user = await IamUser.objects.using(IAM_DB_ALIAS).filter(id=user_id, is_active=1).afirst()

        if not user:
            raise ValueError("User not found or inactive.")

        access_token, access_jti = JwtService.create_access_token(user_id=user.id, user_type=user.user_type)

        token_record.access_jti = access_jti
        await token_record.asave(update_fields=["access_jti"])

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": JwtService.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    @classmethod
    async def logout(cls, refresh_token: str) -> bool:
        payload = JwtService.decode_refresh_token(refresh_token)

        if not payload:
            return False

        refresh_jti = payload.get("jti")

        if not refresh_jti:
            return False

        updated_count = await IamUserToken.objects.using(IAM_DB_ALIAS).filter(refresh_jti=refresh_jti, revoked_at__isnull=True, ).aupdate(revoked_at=timezone.now())

        return updated_count > 0

    @staticmethod
    def get_bearer_token_from_request(request) -> str | None:
        authorization = request.headers.get("Authorization", "")

        if not authorization.startswith("Bearer "):
            return None

        token = authorization.removeprefix("Bearer ").strip()

        return token or None
