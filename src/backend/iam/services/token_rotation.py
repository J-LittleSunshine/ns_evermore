# -*- coding: utf-8 -*-
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from iam.constants import IAM_DB_ALIAS
from ns_backend.exceptions import BusinessError


class TokenRotationService:
    """Refresh Token Rotation 服务。"""

    @classmethod
    def rotate_refresh_token(
        cls,
        token_model,
        token_value: str,
        create_token_callback,
        revoke_family_callback=None,
    ) -> dict:
        """
        执行 refresh token rotation。

        要求：
        - refresh token 只能使用一次
        - 并发刷新时只能有一个请求成功
        - 发现 replay attack 时可撤销整个 token family

        参数：
            token_model:
                refresh token ORM model。

            token_value:
                当前 refresh token hash/value。

            create_token_callback:
                新 token 创建回调。

            revoke_family_callback:
                replay attack 时的 token family 撤销回调。
        """

        with transaction.atomic(using=IAM_DB_ALIAS):
            token_obj = (
                token_model.objects
                .using(IAM_DB_ALIAS)
                .select_for_update()
                .filter(token=token_value)
                .first()
            )

            if not token_obj:
                raise BusinessError("refresh_token 不存在", 14001)

            if getattr(token_obj, "revoked_at", None):
                if revoke_family_callback:
                    revoke_family_callback(token_obj)

                raise BusinessError("refresh_token 已失效", 14002)

            expired_at = getattr(token_obj, "expired_at", None)

            if expired_at and expired_at <= timezone.now():
                raise BusinessError("refresh_token 已过期", 14003)

            token_obj.revoked_at = timezone.now()

            if hasattr(token_obj, "revoked_reason"):
                token_obj.revoked_reason = "ROTATED"

            update_fields = ["revoked_at"]

            if hasattr(token_obj, "revoked_reason"):
                update_fields.append("revoked_reason")

            token_obj.save(update_fields=update_fields)

            new_token_payload = create_token_callback(token_obj)

        return new_token_payload
