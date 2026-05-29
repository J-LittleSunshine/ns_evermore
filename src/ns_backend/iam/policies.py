# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ns_common.error_codes import NsErrorCode
from .constants import (
    USER_TYPE_ENTERPRISE,
    USER_TYPE_PERSONAL,
    DATA_SCOPE_ALL,
    DATA_SCOPE_LEVELS,
    DATA_SCOPE_SELF,
    DATA_SCOPE_DEPARTMENT,
    DATA_SCOPE_DEPARTMENT_TREE,
    DATA_SCOPE_SUBSIDIARY,
    DATA_SCOPE_COMPANY,
    PERMISSION_TYPE_DATA,
    PERMISSION_EFFECT_DENY,
    PERMISSION_EFFECT_ALLOW
)
from .errors import IamDomainError
from .schemas import TenantContext, DataScopeResult, DataScopeFilterPlan, DataScopeFieldMap

if TYPE_CHECKING:
    pass


class BasePolicy:
    @staticmethod
    def deny(message: str, code: int) -> None:
        raise IamDomainError(message=message, code=code)

    @classmethod
    def ensure(cls, condition: bool, message: str, code: int) -> None:
        if not condition:
            cls.deny(message, code)

    @staticmethod
    def is_truthy(value: object) -> bool:
        return value in (True, 1, "1", "true", "True")

    @staticmethod
    def is_falsy(value: object) -> bool:
        return value in (False, 0, "0", "false", "False")


class TenantPolicy(BasePolicy):
    @classmethod
    def is_platform_admin(cls, context: TenantContext) -> bool:
        return bool(context.is_superuser)

    @classmethod
    def is_enterprise_user(cls, context: TenantContext) -> bool:
        return context.user_type == USER_TYPE_ENTERPRISE

    @classmethod
    def is_personal_user(cls, context: TenantContext) -> bool:
        return context.user_type == USER_TYPE_PERSONAL

    @classmethod
    def ensure_enterprise_context(cls, context: TenantContext) -> None:
        if cls.is_platform_admin(context):
            return

        if cls.is_personal_user(context):
            cls.deny("Personal users cannot access enterprise organization resources", NsErrorCode.ENTERPRISE_ORG_FORBIDDEN_PERSONAL)

        if cls.is_enterprise_user(context) and not context.company_id:
            cls.deny("Enterprise user is not bound to a company", NsErrorCode.ENTERPRISE_USER_COMPANY_NOT_BOUND)

    @classmethod
    def ensure_platform_admin(cls, context: TenantContext, message: str, code: int) -> None:
        if not cls.is_platform_admin(context):
            cls.deny(message, code)

    @classmethod
    def ensure_same_company(cls, left_company_id: int | None, right_company_id: int | None, message: str, code: int) -> None:
        if left_company_id != right_company_id:
            cls.deny(message, code)

    @classmethod
    def get_company_scope(cls, context: TenantContext) -> int | None:
        if cls.is_platform_admin(context):
            return None

        if cls.is_enterprise_user(context):
            cls.ensure_enterprise_context(context)
            return context.company_id

        return None


class DataScopePolicy(BasePolicy):
    @classmethod
    def denied_result(cls) -> DataScopeResult:
        return DataScopeResult(allowed=False)

    @classmethod
    def platform_all_result(cls) -> DataScopeResult:
        return DataScopeResult(allowed=True, scope=DATA_SCOPE_ALL, is_platform_scope=True)

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
        return DATA_SCOPE_SELF if scopes else None

    @classmethod
    def build_result_for_user(cls, *, user: Any, scope: str | None, department_ids: list[int] | None = None) -> DataScopeResult:
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
            if not user.department_id or not department_ids:
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
    def build_filter_plan(cls, *, scope: DataScopeResult, field_map: DataScopeFieldMap) -> DataScopeFilterPlan:
        if not scope.allowed:
            return DataScopeFilterPlan(allowed=False, reason="DATA_SCOPE_DENIED")

        if scope.is_platform_scope:
            return DataScopeFilterPlan(allowed=True, filters={}, is_platform_scope=True)

        if scope.scope == DATA_SCOPE_SELF:
            if not field_map.self_field:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_SELF_FIELD")
            if scope.user_id is None:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_USER_ID")
            return DataScopeFilterPlan(allowed=True, filters={field_map.self_field: scope.user_id})

        if scope.scope == DATA_SCOPE_DEPARTMENT:
            if not field_map.department_field:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_DEPARTMENT_FIELD")
            if scope.department_id is None:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_DEPARTMENT_ID")
            return DataScopeFilterPlan(allowed=True, filters={field_map.department_field: scope.department_id})

        if scope.scope == DATA_SCOPE_DEPARTMENT_TREE:
            if not field_map.department_field:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_DEPARTMENT_FIELD")
            if not scope.department_ids:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_DEPARTMENT_IDS")
            return DataScopeFilterPlan(allowed=True, filters={f"{field_map.department_field}__in": scope.department_ids})

        if scope.scope == DATA_SCOPE_SUBSIDIARY:
            if not field_map.subsidiary_field:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_SUBSIDIARY_FIELD")
            if scope.subsidiary_id is None:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_SUBSIDIARY_ID")
            return DataScopeFilterPlan(allowed=True, filters={field_map.subsidiary_field: scope.subsidiary_id})

        if scope.scope in {DATA_SCOPE_COMPANY, DATA_SCOPE_ALL}:
            if not field_map.company_field:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_COMPANY_FIELD")
            if scope.company_id is None:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_COMPANY_ID")
            return DataScopeFilterPlan(allowed=True, filters={field_map.company_field: scope.company_id})

        return DataScopeFilterPlan(allowed=False, reason="UNKNOWN_DATA_SCOPE")

    @classmethod
    def ensure_grant_data_scope_by_permission_type(cls, *, permission_type: str | None, data_scope: str | None, effect: str | None = None, role_permission: bool = False) -> None:
        if permission_type is None:
            cls.deny("Permission does not exist", NsErrorCode.DATA_NOT_FOUND)

        if permission_type != PERMISSION_TYPE_DATA:
            if data_scope:
                cls.deny("Data scope cannot be set for non-data permissions", NsErrorCode.DATA_SCOPE_NOT_ALLOWED_FOR_NON_DATA)
            return

        if role_permission:
            if not data_scope:
                cls.deny("Data permissions must set data scope", NsErrorCode.DATA_SCOPE_REQUIRED)
            return

        if effect == PERMISSION_EFFECT_DENY:
            if data_scope:
                cls.deny("DENY permissions cannot set data scope", NsErrorCode.DATA_SCOPE_FORBIDDEN_FOR_DENY)
            return

        if effect == PERMISSION_EFFECT_ALLOW and not data_scope:
            cls.deny("Data permissions must set data scope", NsErrorCode.DATA_SCOPE_REQUIRED)
