# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.db import IntegrityError
from django.db.models import Case, DateTimeField, F, Value, When
from django.utils import timezone

from iam.constants import IAM_DB_ALIAS
from iam.models import IamUser, IamUserToken, IamLoginFailureLock
from iam.services.jwt import JwtService
from ns_backend.exceptions import BusinessError


class AuthService:
    LOGIN_MAX_FAILED_COUNT = settings.LOGIN_MAX_FAILED_COUNT
    LOGIN_LOCK_MINUTES = settings.LOGIN_LOCK_MINUTES

    @classmethod
    async def login(
            cls,
            username: str,
            password: str,
            client_ip: str | None = None,
            user_agent: str | None = None,
    ) -> dict:
        username = username.strip()

        await cls.check_login_locked(username=username)

        user = await IamUser.objects.using(IAM_DB_ALIAS).filter(
            username=username,
            is_active=1,
        ).afirst()

        if not user:
            await cls.record_login_failed(
                username=username,
                user=None,
                client_ip=client_ip,
                user_agent=user_agent,
            )
            raise BusinessError("Username or password is incorrect.")

        if not check_password(password, user.password):
            await cls.record_login_failed(
                username=username,
                user=user,
                client_ip=client_ip,
                user_agent=user_agent,
            )
            raise BusinessError("Username or password is incorrect.")

        await cls.clear_login_failed(username=username)

        access_token, access_jti = JwtService.create_access_token(
            user_id=user.id,
            user_type=user.user_type,
        )

        now = timezone.now()
        refresh_token, refresh_token_hash, refresh_jti, refresh_expired_at = (
            JwtService.create_refresh_token(user_id=user.id)
        )

        await IamUserToken.objects.using(IAM_DB_ALIAS).acreate(
            user_id=user.id,
            refresh_token=refresh_token_hash,
            access_jti=access_jti,
            refresh_jti=refresh_jti,
            client_ip=client_ip,
            user_agent=user_agent,
            expired_at=refresh_expired_at,
            created_at=now,
        )

        user.last_login = now
        user.updated_at = now
        await user.asave(
            using=IAM_DB_ALIAS,
            update_fields=["last_login", "updated_at"],
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": JwtService.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    @classmethod
    async def check_login_locked(cls, username: str) -> None:
        record = await IamLoginFailureLock.objects.using(IAM_DB_ALIAS).filter(
            username=username,
        ).afirst()

        if not record or not record.locked_until:
            return

        now = timezone.now()

        if record.locked_until > now:
            raise BusinessError(
                msg="账号因连续登录失败已被锁定，请稍后再试",
                code=11011,
                data={"locked_until": record.locked_until.isoformat()},
            )

        record.failed_count = 0
        record.locked_until = None
        record.updated_at = now
        await record.asave(
            using=IAM_DB_ALIAS,
            update_fields=["failed_count", "locked_until", "updated_at"],
        )

    @classmethod
    async def record_login_failed(
            cls,
            username: str,
            user: IamUser | None,
            client_ip: str | None = None,
            user_agent: str | None = None,
    ) -> None:
        now = timezone.now()
        locked_until = now + timedelta(minutes=cls.LOGIN_LOCK_MINUTES)

        update_fields = {
            "failed_count": F("failed_count") + 1,
            "locked_until": Case(
                When(
                    failed_count__gte=cls.LOGIN_MAX_FAILED_COUNT - 1,
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

        if user:
            update_fields["user_id"] = user.id

        affected_rows = await IamLoginFailureLock.objects.using(IAM_DB_ALIAS).filter(
            username=username,
        ).aupdate(**update_fields)

        if affected_rows:
            return

        try:
            await IamLoginFailureLock.objects.using(IAM_DB_ALIAS).acreate(
                username=username,
                user_id=user.id if user else None,
                failed_count=1,
                locked_until=(
                    locked_until if cls.LOGIN_MAX_FAILED_COUNT <= 1 else None
                ),
                last_failed_at=now,
                last_client_ip=client_ip,
                last_user_agent=user_agent,
                created_at=now,
                updated_at=now,
            )
        except IntegrityError:
            await IamLoginFailureLock.objects.using(IAM_DB_ALIAS).filter(
                username=username,
            ).aupdate(**update_fields)

    @classmethod
    async def clear_login_failed(cls, username: str) -> None:
        await IamLoginFailureLock.objects.using(IAM_DB_ALIAS).filter(
            username=username,
        ).aupdate(
            failed_count=0,
            locked_until=None,
            updated_at=timezone.now(),
        )

    @classmethod
    async def get_user_by_access_token(cls, access_token: str) -> IamUser | None:
        payload = JwtService.decode_access_token(access_token)

        if not payload:
            return None

        user_id = payload.get("uid")
        access_jti = payload.get("jti")

        if not user_id or not access_jti:
            return None

        token_exists = await IamUserToken.objects.using(IAM_DB_ALIAS).filter(
            user_id=user_id,
            access_jti=access_jti,
            revoked_at__isnull=True,
            expired_at__gt=timezone.now(),
        ).aexists()

        if not token_exists:
            return None

        return await IamUser.objects.using(IAM_DB_ALIAS).filter(
            id=user_id,
            is_active=1,
        ).afirst()

    @classmethod
    async def refresh_access_token(cls, refresh_token: str) -> dict:
        payload = JwtService.decode_refresh_token(refresh_token)

        if not payload:
            raise BusinessError("Refresh Token 无效或已过期", 11005)

        refresh_jti = payload.get("jti")
        user_id = payload.get("uid")

        if not refresh_jti or not user_id:
            raise BusinessError("Refresh Token 无效", 11005)

        refresh_token_hash = JwtService.hash_token(refresh_token)

        revoked_token_exists = await IamUserToken.objects.using(IAM_DB_ALIAS).filter(
            user_id=user_id,
            refresh_jti=refresh_jti,
            refresh_token=refresh_token_hash,
            revoked_at__isnull=False,
        ).aexists()

        if revoked_token_exists:
            await cls.revoke_all_user_tokens(user_id=user_id)
            raise BusinessError("检测到 Refresh Token 重放攻击，当前账号已强制下线", 11013)

        token_record = await IamUserToken.objects.using(IAM_DB_ALIAS).filter(
            user_id=user_id,
            refresh_jti=refresh_jti,
            refresh_token=refresh_token_hash,
            revoked_at__isnull=True,
            expired_at__gt=timezone.now(),
        ).afirst()

        if not token_record:
            raise BusinessError("Refresh Token 已失效", 11005)

        user = await IamUser.objects.using(IAM_DB_ALIAS).filter(
            id=user_id,
            is_active=1,
        ).afirst()

        if not user:
            raise BusinessError("用户不存在或已禁用", 11010)

        access_token, access_jti = JwtService.create_access_token(
            user_id=user.id,
            user_type=user.user_type,
        )

        new_refresh_token, new_refresh_token_hash, new_refresh_jti, new_refresh_expired_at = (
            JwtService.create_refresh_token(user_id=user.id)
        )

        now = timezone.now()

        token_record.revoked_at = now
        await token_record.asave(
            using=IAM_DB_ALIAS,
            update_fields=["revoked_at"],
        )

        await IamUserToken.objects.using(IAM_DB_ALIAS).acreate(
            user_id=user.id,
            refresh_token=new_refresh_token_hash,
            access_jti=access_jti,
            refresh_jti=new_refresh_jti,
            client_ip=token_record.client_ip,
            user_agent=token_record.user_agent,
            expired_at=new_refresh_expired_at,
            created_at=now,
        )

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "Bearer",
            "expires_in": JwtService.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    @classmethod
    async def logout(cls, refresh_token: str) -> bool:
        payload = JwtService.decode_refresh_token(refresh_token)

        if not payload:
            return False

        refresh_jti = payload.get("jti")
        user_id = payload.get("uid")

        if not refresh_jti or not user_id:
            return False

        refresh_token_hash = JwtService.hash_token(refresh_token)

        updated_count = await IamUserToken.objects.using(IAM_DB_ALIAS).filter(
            user_id=user_id,
            refresh_jti=refresh_jti,
            refresh_token=refresh_token_hash,
            revoked_at__isnull=True,
        ).aupdate(revoked_at=timezone.now())

        return updated_count > 0

    @staticmethod
    def get_bearer_token_from_request(request) -> str | None:
        authorization = request.headers.get("Authorization", "")

        if not authorization.startswith("Bearer "):
            return None

        token = authorization.removeprefix("Bearer ").strip()
        return token or None

    @classmethod
    async def revoke_access_token(cls, access_token: str) -> bool:
        payload = JwtService.decode_access_token(access_token)

        if not payload:
            return False

        user_id = payload.get("uid")
        access_jti = payload.get("jti")

        if not user_id or not access_jti:
            return False

        updated_count = await IamUserToken.objects.using(IAM_DB_ALIAS).filter(
            user_id=user_id,
            access_jti=access_jti,
            revoked_at__isnull=True,
            expired_at__gt=timezone.now(),
        ).aupdate(revoked_at=timezone.now())

        return updated_count > 0

    @classmethod
    async def revoke_all_user_tokens(cls, user_id: int) -> None:
        await IamUserToken.objects.using(IAM_DB_ALIAS).filter(
            user_id=user_id,
            revoked_at__isnull=True,
        ).aupdate(revoked_at=timezone.now())
