# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    TYPE_CHECKING,
)

from ns_backend.iam.constants import (
    DATA_SCOPE_ALL,
    DATA_SCOPE_DEPARTMENT,
    DATA_SCOPE_DEPARTMENT_AND_CHILDREN,
    DATA_SCOPE_LEVELS,
    DATA_SCOPE_ORGANIZATION,
    DATA_SCOPE_SELF,
    DATA_SCOPE_SUBSIDIARY,
    normalize_data_scope,
)
from ns_backend.iam.schemas import (
    DataScopeFieldMap,
    DataScopeFilterPlan,
    DataScopeResult,
)

if TYPE_CHECKING:
    pass


class DataScopePolicy:
    @classmethod
    def denied_result(cls) -> DataScopeResult:
        return DataScopeResult(
            allowed=False,
            department_ids=[],
        )

    @classmethod
    def platform_all_result(cls) -> DataScopeResult:
        return DataScopeResult(
            allowed=True,
            scope=DATA_SCOPE_ALL,
            is_platform_scope=True,
            department_ids=[],
        )

    @classmethod
    def select_max_scope(cls, scopes: list[str]) -> str | None:
        if not scopes:
            return None

        normalized_scopes = [
            normalize_data_scope(scope)
            for scope in scopes
        ]
        valid_scopes = [
            scope
            for scope in normalized_scopes
            if scope in DATA_SCOPE_LEVELS
        ]

        if not valid_scopes:
            return None

        return max(valid_scopes, key=lambda item: DATA_SCOPE_LEVELS[item])

    @classmethod
    def normalize_personal_scope(cls, scopes: list[str]) -> str | None:
        return DATA_SCOPE_SELF if scopes else None

    @classmethod
    def build_result_for_user(cls, *, user: Any, scope: str | None, department_ids: list[int] | None = None) -> DataScopeResult:
        normalized_scope = normalize_data_scope(scope)
        if not normalized_scope:
            return cls.denied_result()

        base_kwargs = {
            "allowed": True,
            "scope": normalized_scope,
            "company_id": getattr(user, "company_id", None),
            "subsidiary_id": getattr(user, "subsidiary_id", None),
            "department_id": getattr(user, "department_id", None),
            "user_id": getattr(user, "id", None),
            "is_platform_scope": False,
        }

        if normalized_scope == DATA_SCOPE_SELF:
            return DataScopeResult(
                **base_kwargs,
                department_ids=[],
            )

        if normalized_scope == DATA_SCOPE_DEPARTMENT:
            if not getattr(user, "department_id", None):
                return cls.denied_result()

            return DataScopeResult(
                **base_kwargs,
                department_ids=[
                    user.department_id,
                ],
            )

        if normalized_scope == DATA_SCOPE_DEPARTMENT_AND_CHILDREN:
            if not getattr(user, "department_id", None) or not department_ids:
                return cls.denied_result()

            return DataScopeResult(
                **base_kwargs,
                department_ids=department_ids,
            )

        if normalized_scope == DATA_SCOPE_SUBSIDIARY:
            if not getattr(user, "subsidiary_id", None):
                return cls.denied_result()

            return DataScopeResult(
                **base_kwargs,
                department_ids=[],
            )

        if normalized_scope == DATA_SCOPE_ORGANIZATION:
            if not getattr(user, "company_id", None):
                return cls.denied_result()

            return DataScopeResult(
                **base_kwargs,
                department_ids=[],
            )

        if normalized_scope == DATA_SCOPE_ALL:
            if not getattr(user, "company_id", None):
                return cls.denied_result()

            return DataScopeResult(
                **base_kwargs,
                department_ids=[],
            )

        return cls.denied_result()

    @classmethod
    def build_filter_plan(cls, *, scope: DataScopeResult, field_map: DataScopeFieldMap) -> DataScopeFilterPlan:
        if not scope.allowed:
            return DataScopeFilterPlan(
                allowed=False,
                reason="DATA_SCOPE_DENIED",
                filters={},
            )

        if scope.is_platform_scope:
            return DataScopeFilterPlan(
                allowed=True,
                filters={},
                is_platform_scope=True,
            )

        normalized_scope = normalize_data_scope(scope.scope)

        if normalized_scope == DATA_SCOPE_SELF:
            if not field_map.self_field:
                return DataScopeFilterPlan(
                    allowed=False,
                    reason="MISSING_SELF_FIELD",
                    filters={},
                )

            if scope.user_id is None:
                return DataScopeFilterPlan(
                    allowed=False,
                    reason="MISSING_USER_ID",
                    filters={},
                )

            return DataScopeFilterPlan(
                allowed=True,
                filters={
                    field_map.self_field: scope.user_id,
                },
            )

        if normalized_scope == DATA_SCOPE_DEPARTMENT:
            if not field_map.department_field:
                return DataScopeFilterPlan(
                    allowed=False,
                    reason="MISSING_DEPARTMENT_FIELD",
                    filters={},
                )

            if scope.department_id is None:
                return DataScopeFilterPlan(
                    allowed=False,
                    reason="MISSING_DEPARTMENT_ID",
                    filters={},
                )

            return DataScopeFilterPlan(
                allowed=True,
                filters={
                    field_map.department_field: scope.department_id,
                },
            )

        if normalized_scope == DATA_SCOPE_DEPARTMENT_AND_CHILDREN:
            if not field_map.department_field:
                return DataScopeFilterPlan(
                    allowed=False,
                    reason="MISSING_DEPARTMENT_FIELD",
                    filters={},
                )

            if not scope.department_ids:
                return DataScopeFilterPlan(
                    allowed=False,
                    reason="MISSING_DEPARTMENT_IDS",
                    filters={},
                )

            return DataScopeFilterPlan(
                allowed=True,
                filters={
                    f"{field_map.department_field}__in": scope.department_ids,
                },
            )

        if normalized_scope == DATA_SCOPE_SUBSIDIARY:
            if not field_map.subsidiary_field:
                return DataScopeFilterPlan(
                    allowed=False,
                    reason="MISSING_SUBSIDIARY_FIELD",
                    filters={},
                )

            if scope.subsidiary_id is None:
                return DataScopeFilterPlan(
                    allowed=False,
                    reason="MISSING_SUBSIDIARY_ID",
                    filters={},
                )

            return DataScopeFilterPlan(
                allowed=True,
                filters={
                    field_map.subsidiary_field: scope.subsidiary_id,
                },
            )

        if normalized_scope in {
            DATA_SCOPE_ORGANIZATION,
            DATA_SCOPE_ALL,
        }:
            if not field_map.company_field:
                return DataScopeFilterPlan(
                    allowed=False,
                    reason="MISSING_COMPANY_FIELD",
                    filters={},
                )

            if scope.company_id is None:
                return DataScopeFilterPlan(
                    allowed=False,
                    reason="MISSING_COMPANY_ID",
                    filters={},
                )

            return DataScopeFilterPlan(
                allowed=True,
                filters={
                    field_map.company_field: scope.company_id,
                },
            )

        return DataScopeFilterPlan(
            allowed=False,
            reason="UNKNOWN_DATA_SCOPE",
            filters={},
        )
