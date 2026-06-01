# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from asgiref.sync import sync_to_async
from django.db import IntegrityError, transaction
from django.utils import timezone

from ns_backend.backend.common import BaseRepository
from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.models import IamUser, IamUserSession, IamUserToken
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


class UserRepository:
    """Repository for IAM user write operations requiring transactional consistency."""

    @classmethod
    async def update_user_and_revoke_sessions_tokens(cls, *, item_id: int | str | None, data: dict[str, Any], operator_id: int | None = None, tenant_filter: dict[str, Any] | None = None) -> None:
        """Update user and revoke all active sessions/tokens in one transaction."""
        await sync_to_async(cls._update_user_and_revoke_sessions_tokens_sync, thread_sensitive=True)(
            item_id=item_id,
            data=data,
            operator_id=operator_id,
            tenant_filter=tenant_filter,
        )

    @classmethod
    async def revoke_and_delete_user(cls, *, item_id: int | str | None, tenant_filter: dict[str, Any] | None = None) -> None:
        """Revoke all active sessions/tokens and delete user in one transaction."""
        await sync_to_async(cls._revoke_and_delete_user_sync, thread_sensitive=True)(
            item_id=item_id,
            tenant_filter=tenant_filter,
        )

    @classmethod
    def _update_user_and_revoke_sessions_tokens_sync(cls, *, item_id: int | str | None, data: dict[str, Any], operator_id: int | None = None, tenant_filter: dict[str, Any] | None = None) -> None:
        """Synchronous transactional implementation for user update and revocation."""
        db_alias = BaseRepository.resolve_db_alias(model_class=IamUser)
        normalized_item_id = BaseRepository.normalize_item_id(item_id)
        now = timezone.now()

        with transaction.atomic(using=db_alias):
            user = cls._get_locked_user(item_id=normalized_item_id, tenant_filter=tenant_filter, db_alias=db_alias)
            update_data = BaseRepository.fill_update_audit_fields(model_class=IamUser, data=data, operator_id=operator_id)

            if update_data:
                for field, value in update_data.items():
                    setattr(user, field, value)

                try:
                    user.save(using=db_alias, update_fields=list(update_data.keys()))
                except IntegrityError as exc:
                    raise BusinessError(f"User update failed: {exc}", NsErrorCode.USER_UPDATE_FAILED) from exc

            cls._revoke_sessions_tokens(user_id=user.id, revoked_at=now, db_alias=db_alias)

    @classmethod
    def _revoke_and_delete_user_sync(cls, *, item_id: int | str | None, tenant_filter: dict[str, Any] | None = None) -> None:
        """Synchronous transactional implementation for user revocation and deletion."""
        db_alias = BaseRepository.resolve_db_alias(model_class=IamUser)
        normalized_item_id = BaseRepository.normalize_item_id(item_id)
        now = timezone.now()

        with transaction.atomic(using=db_alias):
            user = cls._get_locked_user(item_id=normalized_item_id, tenant_filter=tenant_filter, db_alias=db_alias)
            cls._revoke_sessions_tokens(user_id=user.id, revoked_at=now, db_alias=db_alias)
            user.delete(using=db_alias)

    @staticmethod
    def _get_locked_user(*, item_id: int, tenant_filter: dict[str, Any] | None, db_alias: str) -> IamUser:
        """Load user row with row-level lock."""
        queryset = IamUser.objects.using(db_alias).select_for_update().filter(id=item_id)

        if tenant_filter:
            queryset = queryset.filter(**tenant_filter)

        user = queryset.first()
        if user is None:
            raise BusinessError("User does not exist", NsErrorCode.USER_NOT_FOUND)

        return user

    @staticmethod
    def _revoke_sessions_tokens(*, user_id: int, revoked_at, db_alias: str) -> None:
        """Revoke all active sessions and tokens of one user."""
        IamUserSession.objects.using(db_alias).filter(user_id=user_id, revoked_at__isnull=True).update(revoked_at=revoked_at)
        IamUserToken.objects.using(db_alias).filter(user_id=user_id, revoked_at__isnull=True).update(revoked_at=revoked_at)
