# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.constants import (
    DATA_SCOPE_ALL,
    DATA_SCOPE_COMPANY,
    DATA_SCOPE_DEPARTMENT,
    DATA_SCOPE_DEPARTMENT_TREE,
    DATA_SCOPE_LEVELS,
    DATA_SCOPE_SELF,
    DATA_SCOPE_SUBSIDIARY,
)
from iam.repositories.grant import GrantRepository
from iam.schemas import DataScopeFieldMap, DataScopeFilterPlan, DataScopeResult
from ns_backend.exceptions import BusinessError
from ns_backend.policies import BasePolicy


class DataScopePolicy(BasePolicy):
    PERMISSION_TYPE_DATA = "DATA"
    EFFECT_ALLOW = "ALLOW"
    EFFECT_DENY = "DENY"

    @classmethod
    def denied_result(cls) -> DataScopeResult:
        return DataScopeResult(allowed=False)

    @classmethod
    def platform_all_result(cls) -> DataScopeResult:
        return DataScopeResult(
            allowed=True,
            scope=DATA_SCOPE_ALL,
            is_platform_scope=True,
        )

    @classmethod
    def select_max_scope(cls, scopes: list[str]) -> str | None:
        if not scopes:
            return None

        valid_scopes = [scope for scope in scopes if scope in DATA_SCOPE_LEVELS]
        if not valid_scopes:
            return None

        return max(valid_scopes, key=lambda item: DATA_SCOPE_LEVELS[item])

    @classmethod
    def normalize_personal_scope(cls, scopes: list[str]) -> str | None:
        # PERSONAL users are always bounded to self once any ALLOW data-scope exists.
        return DATA_SCOPE_SELF if scopes else None

    @classmethod
    def build_result_for_user(
        cls,
        *,
        user,
        scope: str | None,
        department_ids: list[int] | None = None,
    ) -> DataScopeResult:
        if not scope:
            return cls.denied_result()

        base_kwargs = {
            "allowed": True,
            "scope": scope,
            "company_id": user.company_id,
            "subsidiary_id": user.subsidiary_id,
            "department_id": user.department_id,
            "user_id": user.id,
            "is_platform_scope": False,
        }

        if scope == DATA_SCOPE_SELF:
            return DataScopeResult(**base_kwargs, department_ids=[])

        if scope == DATA_SCOPE_DEPARTMENT:
            if not user.department_id:
                return cls.denied_result()
            return DataScopeResult(**base_kwargs, department_ids=[user.department_id])

        if scope == DATA_SCOPE_DEPARTMENT_TREE:
            if not user.department_id:
                return cls.denied_result()
            if not department_ids:
                return cls.denied_result()
            return DataScopeResult(**base_kwargs, department_ids=department_ids)

        if scope == DATA_SCOPE_SUBSIDIARY:
            if not user.subsidiary_id:
                return cls.denied_result()
            return DataScopeResult(**base_kwargs, department_ids=[])

        if scope == DATA_SCOPE_COMPANY:
            if not user.company_id:
                return cls.denied_result()
            return DataScopeResult(**base_kwargs, department_ids=[])

        if scope == DATA_SCOPE_ALL:
            if not user.company_id:
                return cls.denied_result()
            return DataScopeResult(**base_kwargs, department_ids=[])

        return cls.denied_result()

    @classmethod
    def build_filter_plan(
        cls,
        *,
        scope: DataScopeResult,
        field_map: DataScopeFieldMap,
    ) -> DataScopeFilterPlan:
        if not scope.allowed:
            return DataScopeFilterPlan(
                allowed=False,
                reason="DATA_SCOPE_DENIED",
            )

        if scope.is_platform_scope:
            return DataScopeFilterPlan(
                allowed=True,
                filters={},
                is_platform_scope=True,
            )

        if scope.scope == DATA_SCOPE_SELF:
            if not field_map.self_field:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_SELF_FIELD")
            if scope.user_id is None:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_USER_ID")
            return DataScopeFilterPlan(
                allowed=True,
                filters={field_map.self_field: scope.user_id},
            )

        if scope.scope == DATA_SCOPE_DEPARTMENT:
            if not field_map.department_field:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_DEPARTMENT_FIELD")
            if scope.department_id is None:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_DEPARTMENT_ID")
            return DataScopeFilterPlan(
                allowed=True,
                filters={field_map.department_field: scope.department_id},
            )

        if scope.scope == DATA_SCOPE_DEPARTMENT_TREE:
            if not field_map.department_field:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_DEPARTMENT_FIELD")
            if not scope.department_ids:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_DEPARTMENT_IDS")
            return DataScopeFilterPlan(
                allowed=True,
                filters={f"{field_map.department_field}__in": scope.department_ids},
            )

        if scope.scope == DATA_SCOPE_SUBSIDIARY:
            if not field_map.subsidiary_field:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_SUBSIDIARY_FIELD")
            if scope.subsidiary_id is None:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_SUBSIDIARY_ID")
            return DataScopeFilterPlan(
                allowed=True,
                filters={field_map.subsidiary_field: scope.subsidiary_id},
            )

        if scope.scope == DATA_SCOPE_COMPANY:
            if not field_map.company_field:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_COMPANY_FIELD")
            if scope.company_id is None:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_COMPANY_ID")
            return DataScopeFilterPlan(
                allowed=True,
                filters={field_map.company_field: scope.company_id},
            )

        if scope.scope == DATA_SCOPE_ALL:
            if not field_map.company_field:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_COMPANY_FIELD")
            if scope.company_id is None:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_COMPANY_ID")
            return DataScopeFilterPlan(
                allowed=True,
                filters={field_map.company_field: scope.company_id},
            )

        return DataScopeFilterPlan(
            allowed=False,
            reason="UNKNOWN_DATA_SCOPE",
        )

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
            raise BusinessError("Permission does not exist", 10002)

        if permission_type != cls.PERMISSION_TYPE_DATA:
            if data_scope:
                raise BusinessError("Data scope cannot be set for non-data permissions", 15001)
            return

        if role_permission:
            if not data_scope:
                raise BusinessError("Data permissions must set data scope", 15002)
            return

        if effect == cls.EFFECT_DENY:
            if data_scope:
                raise BusinessError("DENY permissions cannot set data scope", 15003)
            return

        if effect == cls.EFFECT_ALLOW and not data_scope:
            raise BusinessError("Data permissions must set data scope", 15002)


__all__ = ["DataScopePolicy"]

