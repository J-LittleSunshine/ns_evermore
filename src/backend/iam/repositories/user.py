# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from asgiref.sync import sync_to_async
from django.db import IntegrityError, transaction
from django.utils import timezone

from iam.constants import IAM_DB_ALIAS
from ns_common.error_codes import NsErrorCode
from iam.models import IamUser, IamUserSession, IamUserToken
from ns_backend.exceptions import BusinessError


class UserRepository:
    """用户数据访问层。"""

    @staticmethod
    async def get_active_by_username(username: str) -> IamUser | None:
        return await IamUser.objects.using(IAM_DB_ALIAS).filter(
            username=username,
            is_active=1,
        ).afirst()

    @staticmethod
    async def get_active_by_id(user_id: int) -> IamUser | None:
        return await IamUser.objects.using(IAM_DB_ALIAS).filter(
            id=user_id,
            is_active=1,
        ).afirst()

    @staticmethod
    async def get_by_id(user_id: int) -> IamUser | None:
        return await IamUser.objects.using(IAM_DB_ALIAS).filter(id=user_id).afirst()

    @staticmethod
    async def get_by_id_for_company(user_id: int, company_id: int) -> IamUser | None:
        return await IamUser.objects.using(IAM_DB_ALIAS).filter(
            id=user_id,
            company_id=company_id,
        ).afirst()

    @staticmethod
    async def get_by_id_for_self(user_id: int, operator_user_id: int) -> IamUser | None:
        return await IamUser.objects.using(IAM_DB_ALIAS).filter(id=user_id).filter(id=operator_user_id).afirst()

    @staticmethod
    def build_list_queryset(
        include_staff: bool = False,
        include_superuser: bool = False,
        tenant_filter: dict[str, Any] | None = None,
    ):
        queryset = IamUser.objects.using(IAM_DB_ALIAS).all().order_by("-id")

        if tenant_filter:
            queryset = queryset.filter(**tenant_filter)

        if not include_staff:
            queryset = queryset.filter(is_staff=0, is_superuser=0)
        elif not include_superuser:
            queryset = queryset.filter(is_superuser=0)

        return queryset

    @classmethod
    async def list_users(
        cls,
        page: int,
        page_size: int,
        include_staff: bool = False,
        include_superuser: bool = False,
        tenant_filter: dict[str, Any] | None = None,
    ) -> tuple[list[IamUser], int]:
        queryset = cls.build_list_queryset(
            include_staff=include_staff,
            include_superuser=include_superuser,
            tenant_filter=tenant_filter,
        )
        offset = (page - 1) * page_size
        total = await queryset.acount()

        rows = []
        async for item in queryset[offset: offset + page_size].aiterator():
            rows.append(item)

        return rows, total

    @staticmethod
    async def create_user(data: dict[str, Any]) -> IamUser:
        try:
            return await IamUser.objects.using(IAM_DB_ALIAS).acreate(**data)
        except IntegrityError as exc:
            raise BusinessError(f"User creation failed: {exc}", NsErrorCode.USER_CREATION_FAILED)

    @staticmethod
    async def update_user(user: IamUser, data: dict[str, Any]) -> None:
        for field, value in data.items():
            setattr(user, field, value)

        try:
            await user.asave(
                using=IAM_DB_ALIAS,
                update_fields=list(data.keys()),
            )
        except IntegrityError as exc:
            raise BusinessError(f"User update failed: {exc}", NsErrorCode.USER_UPDATE_FAILED)

    @classmethod
    async def update_user_and_revoke_sessions_tokens(
        cls,
        *,
        user_id: int,
        data: dict[str, Any],
        company_id: int | None = None,
    ) -> None:
        """原子化更新用户并吊销其全部会话与令牌。"""
        await sync_to_async(
            cls._update_user_and_revoke_sessions_tokens_sync,
            thread_sensitive=True,
        )(
            user_id=user_id,
            data=data,
            company_id=company_id,
        )

    @staticmethod
    def _update_user_and_revoke_sessions_tokens_sync(
        *,
        user_id: int,
        data: dict[str, Any],
        company_id: int | None = None,
    ) -> None:
        now = timezone.now()

        with transaction.atomic(using=IAM_DB_ALIAS):
            user_queryset = IamUser.objects.using(IAM_DB_ALIAS).select_for_update().filter(id=user_id)

            if company_id is not None:
                user_queryset = user_queryset.filter(company_id=company_id)

            user = user_queryset.first()

            if not user:
                raise BusinessError("User does not exist", NsErrorCode.USER_NOT_FOUND_LEGACY)

            for field, value in data.items():
                setattr(user, field, value)

            try:
                user.save(
                    using=IAM_DB_ALIAS,
                    update_fields=list(data.keys()),
                )
            except IntegrityError as exc:
                raise BusinessError(f"User update failed: {exc}", NsErrorCode.USER_UPDATE_FAILED)

            IamUserSession.objects.using(IAM_DB_ALIAS).filter(
                user_id=user_id,
                revoked_at__isnull=True,
            ).update(revoked_at=now)

            IamUserToken.objects.using(IAM_DB_ALIAS).filter(
                user_id=user_id,
                revoked_at__isnull=True,
            ).update(revoked_at=now)

    @staticmethod
    async def delete_user(user: IamUser) -> None:
        await user.adelete(using=IAM_DB_ALIAS)

    @classmethod
    async def revoke_and_delete_user(cls, user_id: int, company_id: int | None = None) -> None:
        """原子化吊销用户全部会话/令牌并删除用户。"""
        await sync_to_async(
            cls._revoke_and_delete_user_sync,
            thread_sensitive=True,
        )(
            user_id=user_id,
            company_id=company_id,
        )

    @staticmethod
    def _revoke_and_delete_user_sync(user_id: int, company_id: int | None = None) -> None:
        now = timezone.now()

        with transaction.atomic(using=IAM_DB_ALIAS):
            user_queryset = IamUser.objects.using(IAM_DB_ALIAS).select_for_update().filter(id=user_id)

            if company_id is not None:
                user_queryset = user_queryset.filter(company_id=company_id)

            user = user_queryset.first()

            if not user:
                raise BusinessError("User does not exist", NsErrorCode.USER_NOT_FOUND_LEGACY)

            IamUserSession.objects.using(IAM_DB_ALIAS).filter(
                user_id=user_id,
                revoked_at__isnull=True,
            ).update(revoked_at=now)

            IamUserToken.objects.using(IAM_DB_ALIAS).filter(
                user_id=user_id,
                revoked_at__isnull=True,
            ).update(revoked_at=now)

            user.delete(using=IAM_DB_ALIAS)

    @staticmethod
    async def mark_login_success(user: IamUser) -> None:
        now = timezone.now()
        user.last_login = now
        user.updated_at = now
        await user.asave(
            using=IAM_DB_ALIAS,
            update_fields=["last_login", "updated_at"],
        )
