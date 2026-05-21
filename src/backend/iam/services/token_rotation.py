# -*- coding: utf-8 -*-
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from django.db import transaction
from django.utils import timezone

from iam.constants import IAM_DB_ALIAS
from iam.models import IamUserToken
from ns_backend.exceptions import BusinessError


class TokenRotationService:
    """Refresh Token Rotation 服务。"""

    @classmethod
    def rotate_refresh_token(
        cls,
        refresh_token_hash: str,
        create_token_callback: Callable[[IamUserToken], dict[str, Any]],
    ) -> dict[str, Any]:
        """
        执行 refresh token rotation。

        当前实现基于现有 iam_user_token 表字段：
        - refresh_token：refresh token hash
        - refresh_jti：refresh token 唯一标识
        - revoked_at：吊销时间
        - expired_at：过期时间

        注意：
        当前模型还没有 session_id / device_id / token_family_id / parent_token_id，
        因此这里先保证单 token 级别的一次性使用和并发安全，不盲目增加表字段。
        """
        if not refresh_token_hash:
            raise BusinessError("refresh_token 不能为空", 14000)

        with transaction.atomic(using=IAM_DB_ALIAS):
            token_obj = (
                IamUserToken.objects.using(IAM_DB_ALIAS)
                .select_for_update()
                .filter(refresh_token=refresh_token_hash)
                .first()
            )

            if not token_obj:
                raise BusinessError("refresh_token 不存在", 14001)

            if token_obj.revoked_at:
                raise BusinessError("refresh_token 已失效", 14002)

            if token_obj.expired_at <= timezone.now():
                raise BusinessError("refresh_token 已过期", 14003)

            token_obj.revoked_at = timezone.now()
            token_obj.save(update_fields=["revoked_at"])

            new_token_payload = create_token_callback(token_obj)

        return new_token_payload

    @classmethod
    def revoke_user_tokens(cls, user_id: int) -> int:
        """吊销用户全部未失效 refresh token。"""
        if not user_id:
            raise BusinessError("user_id 不能为空", 14004)

        updated_count = (
            IamUserToken.objects.using(IAM_DB_ALIAS)
            .filter(user_id=user_id, revoked_at__isnull=True)
            .update(revoked_at=timezone.now())
        )

        return updated_count
