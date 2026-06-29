# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import asdict
from typing import (
    Any,
    TYPE_CHECKING,
)

from django.utils import timezone

from ns_backend.iam.constants import (
    DATA_SCOPE_DEPARTMENT_AND_CHILDREN,
    PERMISSION_EFFECT_DENY,
    ROLE_SCOPE_ENTERPRISE,
    ROLE_SCOPE_PERSONAL,
    USER_TYPE_ENTERPRISE,
    USER_TYPE_PERSONAL,
    normalize_data_scope,
)
from ns_backend.iam.policies import DataScopePolicy
from ns_backend.iam.repositories import DataScopeRepository
from ns_backend.iam.schemas import (
    DataScopeFieldMap,
    DataScopeFilterPlan,
    DataScopeResult,
)
from ns_backend.iam.services.cache import IamCacheService
from ns_backend.iam.services.permission import PermissionService

if TYPE_CHECKING:
    pass


class DataScopeService:
    SUBJECT_USER = "user"
    SUBJECT_DEPARTMENT = "department"
    SUBJECT_SUBSIDIARY = "subsidiary"

    @classmethod
    async def resolve_filter_plan(cls, *, user: Any, permission_code: str, field_map: DataScopeFieldMap) -> DataScopeFilterPlan:
        scope = await cls.resolve_scope(user=user, permission_code=permission_code)
        return DataScopePolicy.build_filter_plan(scope=scope, field_map=field_map)

    @classmethod
    async def resolve_scope(cls, *, user: Any, permission_code: str) -> DataScopeResult:
        if not user or not bool(getattr(user, "is_active", False)):
            return DataScopePolicy.denied_result()

        if not permission_code:
            return DataScopePolicy.denied_result()

        cache_key = {
            "kind": "user_data_scope",
            "user": IamCacheService.build_user_fingerprint(user),
            "permission_code": permission_code,
        }

        cached_payload = await IamCacheService.aget(
            cache_key,
            default=None,
        )
        cached_result = cls._data_scope_result_from_cache_payload(cached_payload)
        if cached_result is not None:
            return cached_result

        result = await cls._resolve_scope_from_db(
            user=user,
            permission_code=permission_code,
        )

        await IamCacheService.aset(
            cache_key,
            cls._data_scope_result_to_cache_payload(result),
            ttl=IamCacheService.user_cache_ttl_seconds(),
        )
        return result

    @classmethod
    async def _resolve_scope_from_db(cls, *, user: Any, permission_code: str) -> DataScopeResult:
        if bool(getattr(user, "is_superuser", False)):
            return DataScopePolicy.platform_all_result()

        permission_ids = await PermissionService.get_active_permission_ids_with_ancestors(permission_code)
        if not permission_ids:
            return DataScopePolicy.denied_result()

        now = timezone.now()
        user_type = getattr(user, "user_type", None)

        if user_type == USER_TYPE_PERSONAL:
            return await cls._resolve_personal_scope(
                user=user,
                permission_ids=permission_ids,
                now=now,
            )

        if user_type == USER_TYPE_ENTERPRISE:
            return await cls._resolve_enterprise_scope(
                user=user,
                permission_ids=permission_ids,
                now=now,
            )

        return DataScopePolicy.denied_result()

    @staticmethod
    def _data_scope_result_to_cache_payload(result: DataScopeResult) -> dict[str, Any]:
        return asdict(result)

    @classmethod
    def _data_scope_result_from_cache_payload(cls, payload: Any) -> DataScopeResult | None:
        if not isinstance(payload, dict):
            return None

        allowed = payload.get("allowed")
        if not isinstance(allowed, bool):
            return None

        department_ids = cls._cached_int_list_or_none(payload.get("department_ids"))
        if department_ids is None:
            department_ids = []

        return DataScopeResult(
            allowed=allowed,
            scope=cls._optional_str(payload.get("scope")),
            company_id=cls._optional_int(payload.get("company_id")),
            subsidiary_id=cls._optional_int(payload.get("subsidiary_id")),
            department_id=cls._optional_int(payload.get("department_id")),
            department_ids=department_ids,
            user_id=cls._optional_int(payload.get("user_id")),
            is_platform_scope=bool(payload.get("is_platform_scope", False)),
        )

    @staticmethod
    def _optional_str(value: Any) -> str | None:
        if value is None:
            return None

        text = str(value).strip()
        return text or None

    @staticmethod
    def _optional_int(value: Any) -> int | None:
        if value is None or value == "":
            return None

        if isinstance(value, bool):
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _cached_int_list_or_none(value: Any) -> list[int] | None:
        if value is None:
            return []

        if not isinstance(value, list):
            return None

        result: list[int] = []
        for item in value:
            if isinstance(item, bool):
                return None

            try:
                result.append(int(item))
            except (TypeError, ValueError):
                return None

        return result

    @classmethod
    async def _resolve_personal_scope(cls, *, user: Any, permission_ids: list[int], now) -> DataScopeResult:
        user_id = int(getattr(user, "id"))

        if await cls._has_direct_effect(subject_type=cls.SUBJECT_USER, subject_id=user_id, permission_ids=permission_ids, effect=PERMISSION_EFFECT_DENY, now=now):
            return DataScopePolicy.denied_result()

        scopes: list[str] = []
        scopes.extend(
            await cls._list_user_scopes(
                user_id,
                permission_ids,
                now,
            )
        )
        scopes.extend(
            await cls._list_role_scopes(
                user_id,
                permission_ids,
                now,
                role_scope=ROLE_SCOPE_PERSONAL,
                company_id=None,
            )
        )

        if not scopes:
            return DataScopePolicy.denied_result()

        scope = DataScopePolicy.normalize_personal_scope(scopes)
        return DataScopePolicy.build_result_for_user(user=user, scope=scope)

    @classmethod
    async def _resolve_enterprise_scope(cls, *, user: Any, permission_ids: list[int], now) -> DataScopeResult:
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
        scopes.extend(
            await cls._list_user_scopes(
                user_id,
                permission_ids,
                now,
            )
        )
        scopes.extend(
            await cls._list_role_scopes(
                user_id,
                permission_ids,
                now,
                role_scope=ROLE_SCOPE_ENTERPRISE,
                company_id=company_id,
            )
        )

        if department_id:
            scopes.extend(
                await cls._list_department_scopes(
                    department_id,
                    permission_ids,
                    now,
                )
            )

        if subsidiary_id:
            scopes.extend(
                await cls._list_subsidiary_scopes(
                    subsidiary_id,
                    permission_ids,
                    now,
                )
            )

        scope = DataScopePolicy.select_max_scope(scopes)
        if not scope:
            return DataScopePolicy.denied_result()

        if normalize_data_scope(scope) == DATA_SCOPE_DEPARTMENT_AND_CHILDREN:
            department_ids = await cls._get_descendant_department_ids(
                company_id=company_id,
                department_id=department_id,
            )
            return DataScopePolicy.build_result_for_user(
                user=user,
                scope=scope,
                department_ids=department_ids,
            )

        return DataScopePolicy.build_result_for_user(user=user, scope=scope)

    @classmethod
    async def _has_direct_effect(cls, *, subject_type: str, subject_id: int, permission_ids: list[int], effect: str, now) -> bool:
        if subject_type == cls.SUBJECT_USER:
            return await DataScopeRepository.has_user_effect(
                user_id=subject_id,
                permission_ids=permission_ids,
                effect=effect,
                now=now,
            )

        if subject_type == cls.SUBJECT_DEPARTMENT:
            return await DataScopeRepository.has_department_effect(
                department_id=subject_id,
                permission_ids=permission_ids,
                effect=effect,
                now=now,
            )

        if subject_type == cls.SUBJECT_SUBSIDIARY:
            return await DataScopeRepository.has_subsidiary_effect(
                subsidiary_id=subject_id,
                permission_ids=permission_ids,
                effect=effect,
                now=now,
            )

        return False

    @staticmethod
    async def _list_user_scopes(user_id: int, permission_ids: list[int], now) -> list[str]:
        return await DataScopeRepository.list_user_scopes(
            user_id=user_id,
            permission_ids=permission_ids,
            now=now,
        )

    @staticmethod
    async def _list_department_scopes(department_id: int, permission_ids: list[int], now) -> list[str]:
        return await DataScopeRepository.list_department_scopes(
            department_id=department_id,
            permission_ids=permission_ids,
            now=now,
        )

    @staticmethod
    async def _list_subsidiary_scopes(subsidiary_id: int, permission_ids: list[int], now) -> list[str]:
        return await DataScopeRepository.list_subsidiary_scopes(
            subsidiary_id=subsidiary_id,
            permission_ids=permission_ids,
            now=now,
        )

    @staticmethod
    async def _list_role_scopes(user_id: int, permission_ids: list[int], now, *, role_scope: str, company_id: int | None) -> list[str]:
        return await DataScopeRepository.list_role_scopes(
            user_id=user_id,
            permission_ids=permission_ids,
            now=now,
            role_scope=role_scope,
            company_id=company_id,
        )

    @classmethod
    async def _get_descendant_department_ids(cls, *, company_id: int | None, department_id: int | None) -> list[int]:
        if not company_id or not department_id:
            return []

        cache_key = {
            "kind": "descendant_department_ids",
            "company_id": company_id,
            "department_id": department_id,
        }

        cached_ids = await IamCacheService.aget(
            cache_key,
            default=None,
        )
        normalized_ids = cls._cached_int_list_or_none(cached_ids)
        if normalized_ids is not None:
            return normalized_ids

        department_ids = await DataScopeRepository.list_descendant_department_ids(
            company_id=company_id,
            department_id=department_id,
        )

        await IamCacheService.aset(
            cache_key,
            department_ids,
            ttl=IamCacheService.cache_ttl_seconds(),
        )
        return department_ids
