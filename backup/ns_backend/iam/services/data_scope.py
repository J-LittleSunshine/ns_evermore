# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.utils import timezone

from ns_backend.iam.constants import (
    USER_TYPE_ENTERPRISE,
    USER_TYPE_PERSONAL,
    DATA_SCOPE_DEPARTMENT_AND_CHILDREN,
    PERMISSION_EFFECT_DENY,
    ROLE_SCOPE_PERSONAL,
    ROLE_SCOPE_ENTERPRISE,
    normalize_data_scope,
)
from ns_backend.iam.policies import DataScopePolicy
from ns_backend.iam.repositories import DataScopeRepository
from ns_backend.iam.schemas import DataScopeFieldMap, DataScopeFilterPlan, DataScopeResult
from ns_backend.iam.services.permission import PermissionService

if TYPE_CHECKING:
    pass


class DataScopeService:
    """Data-scope domain service.

    Service responsibilities:
    1. Resolve data permission chain.
    2. Apply DENY precedence.
    3. Select the maximum effective data scope.
    4. Delegate all database reads to DataScopeRepository.
    """

    SUBJECT_USER = "user"
    SUBJECT_DEPARTMENT = "department"
    SUBJECT_SUBSIDIARY = "subsidiary"

    @classmethod
    async def resolve_filter_plan(cls, *, user: Any, permission_code: str, field_map: DataScopeFieldMap) -> DataScopeFilterPlan:
        """Resolve data-scope filter plan for repository/query usage."""
        scope = await cls.resolve_scope(user=user, permission_code=permission_code)
        return DataScopePolicy.build_filter_plan(scope=scope, field_map=field_map)

    @classmethod
    async def resolve_scope(cls, *, user: Any, permission_code: str) -> DataScopeResult:
        """Resolve effective data scope for one user and permission code."""
        if not user or not bool(getattr(user, "is_active", False)):
            return DataScopePolicy.denied_result()

        if not permission_code:
            return DataScopePolicy.denied_result()

        if bool(getattr(user, "is_superuser", False)):
            return DataScopePolicy.platform_all_result()

        permission_ids = await PermissionService.get_active_permission_ids_with_ancestors(permission_code)
        if not permission_ids:
            return DataScopePolicy.denied_result()

        now = timezone.now()
        user_type = getattr(user, "user_type", None)

        if user_type == USER_TYPE_PERSONAL:
            return await cls._resolve_personal_scope(user=user, permission_ids=permission_ids, now=now)

        if user_type == USER_TYPE_ENTERPRISE:
            return await cls._resolve_enterprise_scope(user=user, permission_ids=permission_ids, now=now)

        return DataScopePolicy.denied_result()

    @classmethod
    async def _resolve_personal_scope(cls, *, user: Any, permission_ids: list[int], now) -> DataScopeResult:
        """Resolve personal-user data scope."""
        user_id = int(getattr(user, "id"))

        if await cls._has_direct_effect(subject_type=cls.SUBJECT_USER, subject_id=user_id, permission_ids=permission_ids, effect=PERMISSION_EFFECT_DENY, now=now):
            return DataScopePolicy.denied_result()

        scopes: list[str] = []
        scopes.extend(await cls._list_user_scopes(user_id, permission_ids, now))
        scopes.extend(await cls._list_role_scopes(user_id, permission_ids, now, role_scope=ROLE_SCOPE_PERSONAL, company_id=None))

        if not scopes:
            return DataScopePolicy.denied_result()

        scope = DataScopePolicy.normalize_personal_scope(scopes)
        return DataScopePolicy.build_result_for_user(user=user, scope=scope)

    @classmethod
    async def _resolve_enterprise_scope(cls, *, user: Any, permission_ids: list[int], now) -> DataScopeResult:
        """Resolve enterprise-user data scope."""
        company_id = getattr(user, "company_id", None)
        if not company_id:
            return DataScopePolicy.denied_result()

        user_id = int(getattr(user, "id"))
        department_id = getattr(user, "department_id", None)
        subsidiary_id = getattr(user, "subsidiary_id", None)

        if await cls._has_direct_effect(subject_type=cls.SUBJECT_USER, subject_id=user_id, permission_ids=permission_ids, effect=PERMISSION_EFFECT_DENY, now=now):
            return DataScopePolicy.denied_result()

        if department_id and await cls._has_direct_effect(subject_type=cls.SUBJECT_DEPARTMENT, subject_id=department_id, permission_ids=permission_ids, effect=PERMISSION_EFFECT_DENY, now=now):
            return DataScopePolicy.denied_result()

        if subsidiary_id and await cls._has_direct_effect(subject_type=cls.SUBJECT_SUBSIDIARY, subject_id=subsidiary_id, permission_ids=permission_ids, effect=PERMISSION_EFFECT_DENY, now=now):
            return DataScopePolicy.denied_result()

        scopes: list[str] = []
        scopes.extend(await cls._list_user_scopes(user_id, permission_ids, now))
        scopes.extend(await cls._list_role_scopes(user_id, permission_ids, now, role_scope=ROLE_SCOPE_ENTERPRISE, company_id=company_id))

        if department_id:
            scopes.extend(await cls._list_department_scopes(department_id, permission_ids, now))

        if subsidiary_id:
            scopes.extend(await cls._list_subsidiary_scopes(subsidiary_id, permission_ids, now))

        scope = DataScopePolicy.select_max_scope(scopes)
        if not scope:
            return DataScopePolicy.denied_result()

        if normalize_data_scope(scope) == DATA_SCOPE_DEPARTMENT_AND_CHILDREN:
            department_ids = await cls._get_descendant_department_ids(company_id=company_id, department_id=department_id)
            return DataScopePolicy.build_result_for_user(user=user, scope=scope, department_ids=department_ids)

        return DataScopePolicy.build_result_for_user(user=user, scope=scope)

    @classmethod
    async def _has_direct_effect(cls, *, subject_type: str, subject_id: int, permission_ids: list[int], effect: str, now) -> bool:
        """Check direct permission effect by subject type."""
        if subject_type == cls.SUBJECT_USER:
            return await DataScopeRepository.has_user_effect(user_id=subject_id, permission_ids=permission_ids, effect=effect, now=now)

        if subject_type == cls.SUBJECT_DEPARTMENT:
            return await DataScopeRepository.has_department_effect(department_id=subject_id, permission_ids=permission_ids, effect=effect, now=now)

        if subject_type == cls.SUBJECT_SUBSIDIARY:
            return await DataScopeRepository.has_subsidiary_effect(subsidiary_id=subject_id, permission_ids=permission_ids, effect=effect, now=now)

        return False

    @staticmethod
    async def _list_user_scopes(user_id: int, permission_ids: list[int], now) -> list[str]:
        """List user allow data scopes."""
        return await DataScopeRepository.list_user_scopes(user_id=user_id, permission_ids=permission_ids, now=now)

    @staticmethod
    async def _list_department_scopes(department_id: int, permission_ids: list[int], now) -> list[str]:
        """List department allow data scopes."""
        return await DataScopeRepository.list_department_scopes(department_id=department_id, permission_ids=permission_ids, now=now)

    @staticmethod
    async def _list_subsidiary_scopes(subsidiary_id: int, permission_ids: list[int], now) -> list[str]:
        """List subsidiary allow data scopes."""
        return await DataScopeRepository.list_subsidiary_scopes(subsidiary_id=subsidiary_id, permission_ids=permission_ids, now=now)

    @staticmethod
    async def _list_role_scopes(user_id: int, permission_ids: list[int], now, *, role_scope: str, company_id: int | None) -> list[str]:
        """List role allow data scopes."""
        return await DataScopeRepository.list_role_scopes(user_id=user_id, permission_ids=permission_ids, now=now, role_scope=role_scope, company_id=company_id)

    @staticmethod
    async def _get_descendant_department_ids(*, company_id: int | None, department_id: int | None) -> list[int]:
        """List department and descendant department ids."""
        return await DataScopeRepository.list_descendant_department_ids(company_id=company_id, department_id=department_id)
