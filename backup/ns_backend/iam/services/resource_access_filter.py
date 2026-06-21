# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.utils import timezone

from ns_backend.backend.common.logger import iam_logger
from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.constants import (
    RESOURCE_ACCESS_MODE_ACL_REQUIRED,
    RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW,
)
from ns_backend.iam.repositories import AuthorizeRepository, ResourceAclRepository, ResourceRelationRepository, ResourceRepository
from ns_backend.iam.schemas import DataScopeFieldMap
from ns_backend.iam.services.backoff import retry_with_backoff
from ns_backend.iam.services.data_scope import DataScopeService
from ns_backend.iam.services.permission import PermissionService
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


class ResourceAccessFilterService:
    """Resolve retrieval-stage access filters from ACL/RBAC/DataScope signals."""

    DEFAULT_RESOURCE_ID_FIELD = "resource_id"
    DEFAULT_AUTH_BACKOFF_ENABLED = True
    DEFAULT_AUTH_BACKOFF_MAX_RETRIES = 3
    DEFAULT_AUTH_BACKOFF_BASE_DELAY_MS = 50
    DEFAULT_AUTH_BACKOFF_MAX_DELAY_MS = 1000
    DEFAULT_AUTH_BACKOFF_JITTER_RATIO = 0.5

    @staticmethod
    def _coerce_non_negative_int(value: Any, default: int) -> int:
        try:
            parsed = int(value)
        except (
                TypeError,
                ValueError
        ):
            return default
        return max(parsed, 0)

    @staticmethod
    def _coerce_float(value: Any, default: float, *, min_value: float, max_value: float) -> float:
        try:
            parsed = float(value)
        except (
                TypeError,
                ValueError
        ):
            return default
        if parsed < min_value:
            return min_value
        if parsed > max_value:
            return max_value
        return parsed

    @classmethod
    def _backoff_enabled(cls) -> bool:
        return bool(getattr(settings, "IAM_AUTH_BACKOFF_ENABLED", cls.DEFAULT_AUTH_BACKOFF_ENABLED))

    @classmethod
    def _backoff_max_retries(cls) -> int:
        return cls._coerce_non_negative_int(
            getattr(settings, "IAM_AUTH_BACKOFF_MAX_RETRIES", cls.DEFAULT_AUTH_BACKOFF_MAX_RETRIES),
            cls.DEFAULT_AUTH_BACKOFF_MAX_RETRIES,
        )

    @classmethod
    def _backoff_base_delay_ms(cls) -> int:
        return cls._coerce_non_negative_int(
            getattr(settings, "IAM_AUTH_BACKOFF_BASE_DELAY_MS", cls.DEFAULT_AUTH_BACKOFF_BASE_DELAY_MS),
            cls.DEFAULT_AUTH_BACKOFF_BASE_DELAY_MS,
        )

    @classmethod
    def _backoff_max_delay_ms(cls) -> int:
        return cls._coerce_non_negative_int(
            getattr(settings, "IAM_AUTH_BACKOFF_MAX_DELAY_MS", cls.DEFAULT_AUTH_BACKOFF_MAX_DELAY_MS),
            cls.DEFAULT_AUTH_BACKOFF_MAX_DELAY_MS,
        )

    @classmethod
    def _backoff_jitter_ratio(cls) -> float:
        return cls._coerce_float(
            getattr(settings, "IAM_AUTH_BACKOFF_JITTER_RATIO", cls.DEFAULT_AUTH_BACKOFF_JITTER_RATIO),
            cls.DEFAULT_AUTH_BACKOFF_JITTER_RATIO,
            min_value=0.0,
            max_value=1.0,
        )

    @staticmethod
    def _normalize_required_text(value: Any, field_name: str) -> str:
        text_value = str(value or "").strip()
        if not text_value:
            raise BusinessError(f"{field_name} is required", NsErrorCode.INVALID_VALUE)
        return text_value

    @classmethod
    def _normalize_resource_type(cls, value: Any) -> str:
        return cls._normalize_required_text(value, "resource_type").lower()

    @classmethod
    def _normalize_action_code(cls, value: Any) -> str:
        return cls._normalize_required_text(value, "action_code").lower()

    @classmethod
    def _normalize_access_mode(cls, value: Any) -> str:
        access_mode = str(value or RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW).strip().upper()
        if access_mode in (
                "",
                RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW
        ):
            return RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW
        if access_mode == RESOURCE_ACCESS_MODE_ACL_REQUIRED:
            return RESOURCE_ACCESS_MODE_ACL_REQUIRED
        raise BusinessError("access_mode is invalid", NsErrorCode.INVALID_VALUE)

    @classmethod
    def _build_deny_all_filter(cls, *, reason: str, access_mode: str | None = None, retry_count: int = 0) -> dict[str, Any]:
        return {
            "access_mode": access_mode,
            "allowed_resource_ids": [],
            "denied_resource_ids": [],
            "retry_count": max(int(retry_count), 0),
            "filters": {
                "deny_all": True,
                "allow_all": False,
                "default_allow": False,
                "access_mode": access_mode,
                "reason": reason,
                "orm": {
                    "include": {
                        f"{cls.DEFAULT_RESOURCE_ID_FIELD}__in": []
                    },
                    "exclude": {},
                },
                "vector": {
                    "must": {
                        "terms": {
                            cls.DEFAULT_RESOURCE_ID_FIELD: []
                        }
                    },
                    "must_not": {},
                },
                "data_scope": {},
            },
        }

    @classmethod
    def _derive_permission_code(cls, *, resource_type: str, action_code: str) -> str | None:
        normalized_resource = resource_type.replace(".", ":")
        if ":" not in normalized_resource:
            return None
        return f"{normalized_resource}:{action_code}"

    @classmethod
    async def _build_subject_bindings(cls, *, user: Any) -> list[tuple[str, int]]:
        user_id = int(getattr(user, "id"))
        subject_bindings: list[tuple[str, int]] = [
            (
                "USER",
                user_id
            )
        ]

        role_ids = await AuthorizeRepository.list_active_role_ids_for_user(user_id=user_id)
        subject_bindings.extend(
            (
                "ROLE",
                role_id
            ) for role_id in role_ids
        )

        department_id = getattr(user, "department_id", None)
        if department_id:
            subject_bindings.append(
                (
                    "DEPARTMENT",
                    int(department_id)
                )
            )

        company_id = getattr(user, "company_id", None)
        if company_id:
            subject_bindings.append(
                (
                    "ORGANIZATION",
                    int(company_id)
                )
            )

        subsidiary_id = getattr(user, "subsidiary_id", None)
        if subsidiary_id:
            subject_bindings.append(
                (
                    "SUBSIDIARY",
                    int(subsidiary_id)
                )
            )

        return subject_bindings

    @staticmethod
    def _build_field_map(field_map_data: Any) -> DataScopeFieldMap:
        if not isinstance(field_map_data, dict):
            return DataScopeFieldMap()

        return DataScopeFieldMap(
            self_field=field_map_data.get("self_field"),
            company_field=field_map_data.get("company_field", "company_id"),
            subsidiary_field=field_map_data.get("subsidiary_field", "subsidiary_id"),
            department_field=field_map_data.get("department_field", "department_id"),
        )

    @staticmethod
    def _apply_acl_effects(*, rows: list[dict[str, Any]], allow_ids: set[str], deny_ids: set[str]) -> None:
        for row in rows:
            resource_id = str(row.get("resource_id") or "").strip()
            if not resource_id:
                continue

            effect = str(row.get("effect") or "").strip().upper()
            if effect == "DENY":
                deny_ids.add(resource_id)
                continue

            if effect == "ALLOW":
                allow_ids.add(resource_id)

    @classmethod
    async def _collect_direct_acl_ids(
            cls,
            *,
            subject_bindings: list[tuple[str, int]],
            resource_type: str,
            action_code: str,
            now,
            allow_ids: set[str],
            deny_ids: set[str],
    ) -> None:
        rows = await ResourceAclRepository.list_active_effects_for_resource_type_action(
            subject_bindings=subject_bindings,
            resource_type=resource_type,
            action_code=action_code,
            now=now,
        )
        cls._apply_acl_effects(rows=rows, allow_ids=allow_ids, deny_ids=deny_ids)

    @classmethod
    async def _collect_inherited_acl_ids(
            cls,
            *,
            subject_bindings: list[tuple[str, int]],
            resource_type: str,
            action_code: str,
            now,
            allow_ids: set[str],
            deny_ids: set[str],
    ) -> None:
        ancestor_types = await ResourceRelationRepository.list_ancestor_resource_types(resource_type=resource_type)
        if not ancestor_types:
            return

        for ancestor_type in ancestor_types:
            ancestor_rows = await ResourceAclRepository.list_active_effects_for_resource_type_action(
                subject_bindings=subject_bindings,
                resource_type=ancestor_type,
                action_code=action_code,
                now=now,
            )
            if not ancestor_rows:
                continue

            for row in ancestor_rows:
                parent_resource_id = str(row.get("resource_id") or "").strip()
                if not parent_resource_id:
                    continue

                descendant_ids = await ResourceRelationRepository.list_descendant_resource_ids(
                    parent_resource_type=ancestor_type,
                    parent_resource_id=parent_resource_id,
                    target_resource_type=resource_type,
                )
                if not descendant_ids:
                    continue

                effect = str(row.get("effect") or "").strip().upper()
                if effect == "DENY":
                    deny_ids.update(descendant_ids)
                    continue

                if effect == "ALLOW":
                    allow_ids.update(descendant_ids)

    @classmethod
    async def _resolve_retrieval_filter_once(
            cls,
            *,
            user: Any,
            normalized_resource_type: str,
            normalized_action_code: str,
            permission_code: str | None,
            field_map: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if user is None or not bool(getattr(user, "is_active", False)):
            return cls._build_deny_all_filter(reason="USER_INACTIVE")

        resource_item = await ResourceRepository.get_resource_by_type(normalized_resource_type)
        if resource_item is None:
            return cls._build_deny_all_filter(reason="RESOURCE_TYPE_NOT_FOUND")

        raw_access_mode = getattr(resource_item, "access_mode", RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW)
        try:
            access_mode = cls._normalize_access_mode(raw_access_mode)
        except BusinessError:
            return cls._build_deny_all_filter(
                reason="INVALID_ACCESS_MODE",
                access_mode=None if raw_access_mode in (
                    None,
                    ""
                ) else str(raw_access_mode),
            )

        if bool(getattr(user, "is_superuser", False)):
            return {
                "access_mode": access_mode,
                "allowed_resource_ids": [],
                "denied_resource_ids": [],
                "filters": {
                    "deny_all": False,
                    "allow_all": True,
                    "default_allow": True,
                    "access_mode": access_mode,
                    "reason": "SUPERUSER_BYPASS",
                    "orm": {},
                    "vector": {},
                    "data_scope": {},
                },
            }

        subject_bindings = await cls._build_subject_bindings(user=user)
        now = timezone.now()

        allow_ids: set[str] = set()
        deny_ids: set[str] = set()
        await cls._collect_direct_acl_ids(
            subject_bindings=subject_bindings,
            resource_type=normalized_resource_type,
            action_code=normalized_action_code,
            now=now,
            allow_ids=allow_ids,
            deny_ids=deny_ids,
        )
        await cls._collect_inherited_acl_ids(
            subject_bindings=subject_bindings,
            resource_type=normalized_resource_type,
            action_code=normalized_action_code,
            now=now,
            allow_ids=allow_ids,
            deny_ids=deny_ids,
        )

        # Deny always overrides allow.
        allow_ids.difference_update(deny_ids)

        resolved_permission_code = permission_code or cls._derive_permission_code(
            resource_type=normalized_resource_type,
            action_code=normalized_action_code,
        )
        has_rbac_allow = False
        if resolved_permission_code:
            has_rbac_allow = await PermissionService.has_permission(user=user, permission_code=resolved_permission_code)

        data_scope_filters: dict[str, Any] = {}
        data_scope_reason: str | None = None
        if resolved_permission_code:
            filter_plan = await DataScopeService.resolve_filter_plan(
                user=user,
                permission_code=resolved_permission_code,
                field_map=cls._build_field_map(field_map),
            )
            if filter_plan.allowed:
                data_scope_filters = dict(filter_plan.filters)
            else:
                data_scope_reason = str(filter_plan.reason or "DATA_SCOPE_DENIED")

        orm_filters: dict[str, Any] = dict(data_scope_filters)
        orm_include: dict[str, Any] = {}
        orm_exclude: dict[str, Any] = {}
        vector_must: dict[str, Any] = {}
        vector_must_not: dict[str, Any] = {}

        resolved_allow_ids = sorted(allow_ids)
        resolved_deny_ids = sorted(deny_ids)

        default_allow = False
        deny_all = False
        reason = "NO_MATCHED_RULE"

        if access_mode == RESOURCE_ACCESS_MODE_ACL_REQUIRED:
            default_allow = False
            if resolved_allow_ids:
                deny_all = False
                reason = "ACL_REQUIRED_ALLOW"
                orm_include[f"{cls.DEFAULT_RESOURCE_ID_FIELD}__in"] = resolved_allow_ids
                vector_must["terms"] = {
                    cls.DEFAULT_RESOURCE_ID_FIELD: resolved_allow_ids
                }
            else:
                deny_all = True
                reason = data_scope_reason or "ACL_REQUIRED_NO_RESOURCE_ALLOW"
                orm_include[f"{cls.DEFAULT_RESOURCE_ID_FIELD}__in"] = []
                vector_must["terms"] = {
                    cls.DEFAULT_RESOURCE_ID_FIELD: []
                }
        else:
            if has_rbac_allow and not data_scope_reason:
                default_allow = True
                deny_all = False
                reason = "RBAC_DEFAULT_ALLOW"
            elif has_rbac_allow and data_scope_reason:
                default_allow = False
                if resolved_allow_ids:
                    deny_all = False
                    reason = "DATA_SCOPE_DENIED_ACL_FALLBACK"
                    orm_include[f"{cls.DEFAULT_RESOURCE_ID_FIELD}__in"] = resolved_allow_ids
                    vector_must["terms"] = {
                        cls.DEFAULT_RESOURCE_ID_FIELD: resolved_allow_ids
                    }
                else:
                    deny_all = True
                    reason = data_scope_reason
                    orm_include[f"{cls.DEFAULT_RESOURCE_ID_FIELD}__in"] = []
                    vector_must["terms"] = {
                        cls.DEFAULT_RESOURCE_ID_FIELD: []
                    }
            elif resolved_allow_ids:
                default_allow = False
                deny_all = False
                reason = "ACL_ALLOW_ONLY"
                orm_include[f"{cls.DEFAULT_RESOURCE_ID_FIELD}__in"] = resolved_allow_ids
                vector_must["terms"] = {
                    cls.DEFAULT_RESOURCE_ID_FIELD: resolved_allow_ids
                }
            else:
                default_allow = False
                deny_all = True
                reason = data_scope_reason or "RBAC_NOT_GRANTED_AND_NO_ACL_ALLOW"
                orm_include[f"{cls.DEFAULT_RESOURCE_ID_FIELD}__in"] = []
                vector_must["terms"] = {
                    cls.DEFAULT_RESOURCE_ID_FIELD: []
                }

        if resolved_deny_ids:
            orm_exclude[f"{cls.DEFAULT_RESOURCE_ID_FIELD}__in"] = resolved_deny_ids
            vector_must_not["terms"] = {
                cls.DEFAULT_RESOURCE_ID_FIELD: resolved_deny_ids
            }

        result_filters: dict[str, Any] = {
            "deny_all": deny_all,
            "allow_all": False,
            "default_allow": default_allow,
            "access_mode": access_mode,
            "reason": reason,
            "orm": {
                "include": {**orm_filters, **orm_include},
                "exclude": orm_exclude,
            },
            "vector": {
                "must": vector_must,
                "must_not": vector_must_not,
            },
            "data_scope": data_scope_filters,
        }
        if data_scope_reason:
            result_filters["data_scope_reason"] = data_scope_reason

        return {
            "access_mode": access_mode,
            "allowed_resource_ids": resolved_allow_ids,
            "denied_resource_ids": resolved_deny_ids,
            "filters": result_filters,
        }

    @classmethod
    async def resolve_retrieval_filter(
            cls,
            user: Any,
            resource_type: str,
            action_code: str,
            *,
            permission_code: str | None = None,
            field_map: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Resolve resource-level allow/deny ids and query-level filters for retrievers."""
        normalized_resource_type = cls._normalize_resource_type(resource_type)
        normalized_action_code = cls._normalize_action_code(action_code)

        attempt_count = 0

        async def _operation() -> dict[str, Any]:
            nonlocal attempt_count
            attempt_count += 1
            return await cls._resolve_retrieval_filter_once(
                user=user,
                normalized_resource_type=normalized_resource_type,
                normalized_action_code=normalized_action_code,
                permission_code=permission_code,
                field_map=field_map,
            )

        try:
            if cls._backoff_enabled():
                result = await retry_with_backoff(
                    _operation,
                    max_retries=cls._backoff_max_retries(),
                    base_delay_ms=cls._backoff_base_delay_ms(),
                    max_delay_ms=cls._backoff_max_delay_ms(),
                    jitter_ratio=cls._backoff_jitter_ratio(),
                    retryable_exceptions=(
                        Exception,
                    ),
                    operation_name="resource_access_filter_resolve",
                )
            else:
                result = await _operation()

            retry_count = max(attempt_count - 1, 0)
            if not isinstance(result, dict):
                result = cls._build_deny_all_filter(reason="AUTH_FILTER_BUILD_FAILED", retry_count=retry_count)
            result["retry_count"] = retry_count
            return result
        except Exception as exc:  # noqa
            retry_count = max(attempt_count - 1, 0)
            iam_logger.error(
                "resource access filter build failed",
                exc_info=True,
                extra={
                    "resource_type": normalized_resource_type,
                    "action_code": normalized_action_code,
                    "user_id": getattr(user, "id", None),
                    "retry_count": retry_count,
                    "exception_class": exc.__class__.__name__,
                },
            )
            return cls._build_deny_all_filter(
                reason="AUTH_FILTER_BUILD_FAILED",
                retry_count=retry_count,
            )
