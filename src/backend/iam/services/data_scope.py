# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils import timezone

from iam.constants import DATA_SCOPE_DEPARTMENT_TREE
from iam.policies.data_scope import DataScopePolicy
from iam.repositories.data_scope import DataScopeRepository
from iam.repositories.permission import PermissionRepository
from iam.schemas import DataScopeResult

if TYPE_CHECKING:
    from iam.models import IamUser


class DataScopeService:
    USER_TYPE_PERSONAL = "PERSONAL"
    USER_TYPE_ENTERPRISE = "ENTERPRISE"

    @classmethod
    async def resolve_scope(cls, user: IamUser, permission_code: str) -> DataScopeResult:
        if not user or not user.is_active:
            return DataScopePolicy.denied_result()

        if not permission_code:
            return DataScopePolicy.denied_result()

        if user.is_superuser:
            return DataScopePolicy.platform_all_result()

        permission_ids = await PermissionRepository.get_active_permission_ids_with_ancestors(
            permission_code,
        )
        if not permission_ids:
            return DataScopePolicy.denied_result()

        now = timezone.now()

        if user.user_type == cls.USER_TYPE_PERSONAL:
            return await cls.resolve_personal_scope(
                user=user,
                permission_ids=permission_ids,
                now=now,
            )

        if user.user_type == cls.USER_TYPE_ENTERPRISE:
            return await cls.resolve_enterprise_scope(
                user=user,
                permission_ids=permission_ids,
                now=now,
            )

        return DataScopePolicy.denied_result()

    @classmethod
    async def resolve_personal_scope(
        cls,
        *,
        user: IamUser,
        permission_ids: list[int],
        now,
    ) -> DataScopeResult:
        if await DataScopeRepository.has_user_deny(user.id, permission_ids, now):
            return DataScopePolicy.denied_result()

        scopes: list[str] = []
        scopes.extend(
            await DataScopeRepository.get_user_allow_scopes(
                user.id,
                permission_ids,
                now,
            ),
        )
        scopes.extend(
            await DataScopeRepository.get_role_allow_scopes(
                user.id,
                permission_ids,
                now,
                role_scope=cls.USER_TYPE_PERSONAL,
                company_id=None,
            ),
        )

        if not scopes:
            return DataScopePolicy.denied_result()

        scope = DataScopePolicy.normalize_personal_scope(scopes)
        return DataScopePolicy.build_result_for_user(user=user, scope=scope)

    @classmethod
    async def resolve_enterprise_scope(
        cls,
        *,
        user: IamUser,
        permission_ids: list[int],
        now,
    ) -> DataScopeResult:
        if not user.company_id:
            return DataScopePolicy.denied_result()

        if await DataScopeRepository.has_user_deny(user.id, permission_ids, now):
            return DataScopePolicy.denied_result()

        if user.department_id and await DataScopeRepository.has_department_deny(
            user.department_id,
            permission_ids,
            now,
        ):
            return DataScopePolicy.denied_result()

        if user.subsidiary_id and await DataScopeRepository.has_subsidiary_deny(
            user.subsidiary_id,
            permission_ids,
            now,
        ):
            return DataScopePolicy.denied_result()

        scopes: list[str] = []
        scopes.extend(
            await DataScopeRepository.get_user_allow_scopes(
                user.id,
                permission_ids,
                now,
            ),
        )
        scopes.extend(
            await DataScopeRepository.get_role_allow_scopes(
                user.id,
                permission_ids,
                now,
                role_scope=cls.USER_TYPE_ENTERPRISE,
                company_id=user.company_id,
            ),
        )

        if user.department_id:
            scopes.extend(
                await DataScopeRepository.get_department_allow_scopes(
                    user.department_id,
                    permission_ids,
                    now,
                ),
            )

        if user.subsidiary_id:
            scopes.extend(
                await DataScopeRepository.get_subsidiary_allow_scopes(
                    user.subsidiary_id,
                    permission_ids,
                    now,
                ),
            )

        scope = DataScopePolicy.select_max_scope(scopes)
        if not scope:
            return DataScopePolicy.denied_result()

        if scope == DATA_SCOPE_DEPARTMENT_TREE:
            department_ids = await DataScopeRepository.get_descendant_department_ids(
                company_id=user.company_id,
                department_id=user.department_id,
            )
            return DataScopePolicy.build_result_for_user(
                user=user,
                scope=scope,
                department_ids=department_ids,
            )

        return DataScopePolicy.build_result_for_user(user=user, scope=scope)


__all__ = ["DataScopeService"]

