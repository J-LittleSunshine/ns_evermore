# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.repositories.grant import GrantRepository
from ns_backend.exceptions import BusinessError
from ns_backend.policies import BasePolicy


class DataScopePolicy(BasePolicy):
    PERMISSION_TYPE_DATA = "DATA"
    EFFECT_ALLOW = "ALLOW"
    EFFECT_DENY = "DENY"

    @classmethod
    async def ensure_grant_data_scope(
        cls,
        *,
        permission_id: int,
        data_scope: str | None,
        effect: str | None = None,
        role_permission: bool = False,
    ) -> None:
        permission_type = await GrantRepository.get_permission_type(permission_id)

        if permission_type is None:
            raise BusinessError("权限不存在", 10002)

        if permission_type != cls.PERMISSION_TYPE_DATA:
            if data_scope:
                raise BusinessError("非数据权限不能设置数据范围", 15001)
            return

        if role_permission:
            if not data_scope:
                raise BusinessError("数据权限必须设置数据范围", 15002)
            return

        if effect == cls.EFFECT_DENY:
            if data_scope:
                raise BusinessError("拒绝权限不能设置数据范围", 15003)
            return

        if effect == cls.EFFECT_ALLOW and not data_scope:
            raise BusinessError("数据权限必须设置数据范围", 15002)


__all__ = ["DataScopePolicy"]

