# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.db.utils import DatabaseError

from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.constants import (
    RESOURCE_ACCESS_MODE_ACL_REQUIRED,
    RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW,
)
from ns_backend.iam.repositories import AuthorizeRepository, ResourceRepository
from ns_backend.iam.schemas import DataScopeFieldMap, DataScopeFilterPlan
from ns_backend.iam.services.backoff import retry_with_backoff
from ns_backend.iam.services.data_scope import DataScopeService
from ns_backend.iam.services.decision_audit import DecisionAuditService
from ns_backend.iam.services.permission import PermissionService
from ns_backend.iam.services.policy_engine import PolicyEngineService
from ns_backend.iam.services.resource_acl import ResourceAclService
from ns_common.error_codes import NsErrorCode
from ns_common.logging.logger import get_ns_logger

if TYPE_CHECKING:
    pass

IAM_LOGGER = get_ns_logger("iam", True)
_RETRY_WITH_BACKOFF = retry_with_backoff
_RETRYABLE_DB_ERROR = DatabaseError


class AuthorizeService:
    """Evaluate unified IAM authorization decisions for one or many actions."""

    MATCHED_SOURCE_ACL = "acl"
    MATCHED_SOURCE_POLICY = "policy"
    MATCHED_SOURCE_RBAC = "rbac"
    MATCHED_SOURCE_SUPERUSER = "superuser"
    MATCHED_SOURCE_NONE = "none"

    EFFECT_ALLOW = "allow"
    EFFECT_DENY = "deny"
    ACTION_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
    DEFAULT_AUTH_BACKOFF_ENABLED = True
    DEFAULT_AUTH_BACKOFF_MAX_RETRIES = 3
    DEFAULT_AUTH_BACKOFF_BASE_DELAY_MS = 50
    DEFAULT_AUTH_BACKOFF_MAX_DELAY_MS = 1000
    DEFAULT_AUTH_BACKOFF_JITTER_RATIO = 0.5

    @staticmethod
    def _coerce_non_negative_int(value: Any, default: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        return max(parsed, 0)

    @staticmethod
    def _coerce_float(value: Any, default: float, *, min_value: float, max_value: float) -> float:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
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
    def _ensure_request_data(data: dict[str, Any] | None) -> dict[str, Any]:
        """Validate the request payload object."""
        if not isinstance(data, dict):
            raise BusinessError("request data must be an object", NsErrorCode.INVALID_VALUE)
        return data

    @staticmethod
    def _normalize_required_text(value: Any, field_name: str) -> str:
        """Normalize one required text field."""
        text_value: str = str(value or "").strip()
        if not text_value:
            raise BusinessError(f"{field_name} is required", NsErrorCode.INVALID_VALUE)
        return text_value

    @classmethod
    def _normalize_resource_type(cls, value: Any) -> str:
        """Normalize and validate the resource type."""
        resource_type: str = cls._normalize_required_text(value, "resource_type").lower()
        if " " in resource_type:
            raise BusinessError("resource_type is invalid", NsErrorCode.INVALID_VALUE)
        return resource_type

    @classmethod
    def _normalize_resource_id(cls, value: Any) -> str:
        """Normalize and validate the resource identifier."""
        return cls._normalize_required_text(value, "resource_id")

    @classmethod
    def _normalize_action_code(cls, value: Any) -> str:
        """Normalize and validate the action code."""
        action_code: str = cls._normalize_required_text(value, "action_code").lower()
        if cls.ACTION_CODE_PATTERN.fullmatch(action_code) is None:
            raise BusinessError("action_code is invalid", NsErrorCode.PERMISSION_ACTION_INVALID)
        return action_code

    @staticmethod
    async def _ensure_resource_action_registered(*, resource_type: str, action_code: str) -> None:
        """Ensure resource/action tuple is registered in IAM resource-action table."""
        exists = await ResourceRepository.has_action_for_resource_type(
            resource_type=resource_type,
            action_code=action_code,
        )
        if not exists:
            raise BusinessError("resource_type/action_code is not registered", NsErrorCode.DATA_NOT_FOUND)

    @staticmethod
    def _normalize_permission_code(value: Any) -> str | None:
        """Normalize an optional permission code."""
        if value in (None, ""):
            return None

        permission_code: str = str(value).strip().lower()
        if not permission_code:
            return None

        return permission_code

    @classmethod
    def _derive_permission_code(cls, *, resource_type: str, action_code: str) -> str | None:
        """Derive permission code from resource/action when explicit code is absent."""
        normalized_resource: str = resource_type.replace(".", ":")
        if ":" not in normalized_resource:
            return None
        return f"{normalized_resource}:{action_code}"

    @classmethod
    def _resolve_permission_code(cls, *, request_data: dict[str, Any], resource_type: str, action_code: str) -> str | None:
        """Resolve explicit or derived permission code for one decision."""
        explicit_permission_code: str | None = cls._normalize_permission_code(request_data.get("permission_code"))
        if explicit_permission_code is not None:
            return explicit_permission_code
        return cls._derive_permission_code(resource_type=resource_type, action_code=action_code)

    @classmethod
    def _normalize_access_mode(cls, value: Any) -> str:
        access_mode = str(value or RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW).strip().upper()
        if access_mode in ("", RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW):
            return RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW
        if access_mode == RESOURCE_ACCESS_MODE_ACL_REQUIRED:
            return RESOURCE_ACCESS_MODE_ACL_REQUIRED
        raise BusinessError("resource access_mode is invalid", NsErrorCode.INVALID_VALUE)

    @classmethod
    async def _resolve_resource_access_mode(cls, *, resource_type: str) -> str:
        value = await ResourceRepository.get_resource_access_mode(resource_type=resource_type)
        return cls._normalize_access_mode(value)

    @staticmethod
    def _build_field_map(field_map_data: Any) -> DataScopeFieldMap:
        """Build DataScope field map from request payload."""
        if not isinstance(field_map_data, dict):
            return DataScopeFieldMap()

        return DataScopeFieldMap(
            self_field=field_map_data.get("self_field"),
            company_field=field_map_data.get("company_field", "company_id"),
            subsidiary_field=field_map_data.get("subsidiary_field", "subsidiary_id"),
            department_field=field_map_data.get("department_field", "department_id"),
        )

    @classmethod
    async def _resolve_data_filters(cls, *, user: Any, permission_code: str | None, field_map_data: Any) -> dict[str, Any]:
        """Resolve data-scope filters for the current permission decision."""
        if permission_code is None:
            return {}

        filter_plan: DataScopeFilterPlan = await DataScopeService.resolve_filter_plan(
            user=user,
            permission_code=permission_code,
            field_map=cls._build_field_map(field_map_data),
        )
        if not filter_plan.allowed:
            return {
                "_denied_reason": filter_plan.reason,
            }

        return dict(filter_plan.filters)

    @staticmethod
    def _normalize_context(value: Any) -> dict[str, Any] | None:
        """Normalize optional decision context payload."""
        if not isinstance(value, dict):
            return None
        return dict(value)

    @classmethod
    def _build_decision(
        cls,
        *,
        allowed: bool,
        reason: str,
        matched_source: str,
        access_mode: str | None = None,
        filters: dict[str, Any] | None = None,
        matched_acl_id: int | None = None,
        matched_policy_id: int | None = None,
        matched_rule_id: int | None = None,
        matched_rbac_permission_code: str | None = None,
        hit_details: dict[str, Any] | None = None,
        decision_chain: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Build one normalized authorization decision payload."""
        return {
            "allowed": bool(allowed),
            "effect": cls.EFFECT_ALLOW if allowed else cls.EFFECT_DENY,
            "reason": reason,
            "matched_source": matched_source,
            "access_mode": access_mode,
            "matched_acl_id": matched_acl_id,
            "matched_policy_id": matched_policy_id,
            "matched_rule_id": matched_rule_id,
            "matched_rbac_permission_code": matched_rbac_permission_code,
            "filters": {} if filters is None else filters,
            "hit_details": {} if hit_details is None else hit_details,
            "decision_chain": [] if decision_chain is None else decision_chain,
        }

    @staticmethod
    def _append_chain(chain: list[dict[str, Any]], *, source: str, effect: str, reason: str, **extra: Any) -> None:
        """Append one normalized chain step for authorization tracing."""
        item: dict[str, Any] = {
            "source": source,
            "effect": effect,
            "reason": reason,
        }
        for key, value in extra.items():
            if value in (None, "", [], {}):
                continue
            item[key] = value
        chain.append(item)

    @classmethod
    def _build_authorization_failed_decision(
        cls,
        *,
        permission_code: str | None,
        retry_count: int,
        error: Exception,
        access_mode: str | None,
    ) -> dict[str, Any]:
        decision_chain: list[dict[str, Any]] = []
        cls._append_chain(
            decision_chain,
            source="system",
            effect=cls.EFFECT_DENY,
            reason="AUTHORIZATION_CHECK_FAILED",
            retry_count=max(retry_count, 0),
        )
        return cls._build_decision(
            allowed=False,
            reason="AUTHORIZATION_CHECK_FAILED",
            matched_source=cls.MATCHED_SOURCE_NONE,
            access_mode=access_mode,
            filters={},
            matched_rbac_permission_code=permission_code,
            hit_details={
                "error": error.__class__.__name__,
                "retry_count": max(retry_count, 0),
                "resource": {
                    "access_mode": access_mode,
                },
            },
            decision_chain=decision_chain,
        )

    @classmethod
    async def _run_with_backoff(
        cls,
        *,
        operation,
        operation_name: str,
        user_id: int | None,
        resource_type: str,
        action_code: str,
    ) -> Any:
        attempt_count = 0
        retryable_exceptions: tuple[type[Exception], ...] = (
            _RETRYABLE_DB_ERROR,
            ConnectionError,
            TimeoutError,
            OSError,
            RuntimeError,
        )

        async def _operation_wrapper() -> Any:
            nonlocal attempt_count
            attempt_count += 1
            return await operation()

        try:
            if cls._backoff_enabled():
                return await _RETRY_WITH_BACKOFF(
                    _operation_wrapper,
                    max_retries=cls._backoff_max_retries(),
                    base_delay_ms=cls._backoff_base_delay_ms(),
                    max_delay_ms=cls._backoff_max_delay_ms(),
                    jitter_ratio=cls._backoff_jitter_ratio(),
                    retryable_exceptions=retryable_exceptions,
                    logger_name="iam",
                    operation_name=operation_name,
                )
            return await _operation_wrapper()
        except retryable_exceptions as exc:
            setattr(exc, "_iam_retry_count", max(attempt_count - 1, 0))
            IAM_LOGGER.error(
                "authorization operation failed after retries | operation_name=%s resource_type=%s action_code=%s user_id=%s retry_count=%s exception_class=%s",
                operation_name,
                resource_type,
                action_code,
                user_id,
                max(attempt_count - 1, 0),
                exc.__class__.__name__,
            )
            raise

    @classmethod
    async def _build_subject_bindings(cls, *, user: Any) -> list[tuple[str, int]]:
        """Build all subject bindings participating in authorization evaluation."""
        user_id: int = int(getattr(user, "id"))
        subject_bindings: list[tuple[str, int]] = [("USER", user_id)]

        role_ids: list[int] = await AuthorizeRepository.list_active_role_ids_for_user(user_id=user_id)
        subject_bindings.extend(("ROLE", role_id) for role_id in role_ids)

        department_id = getattr(user, "department_id", None)
        if department_id:
            subject_bindings.append(("DEPARTMENT", int(department_id)))

        company_id = getattr(user, "company_id", None)
        if company_id:
            subject_bindings.append(("ORGANIZATION", int(company_id)))

        subsidiary_id = getattr(user, "subsidiary_id", None)
        if subsidiary_id:
            subject_bindings.append(("SUBSIDIARY", int(subsidiary_id)))

        return subject_bindings

    @classmethod
    async def _record_decision_audit(
        cls,
        *,
        user: Any,
        resource_type: str,
        resource_id: str,
        action_code: str,
        decision: dict[str, Any],
        trace_id: str | None,
    ) -> None:
        """Persist one decision audit row without affecting authorization response."""
        user_id = getattr(user, "id", None)
        if user_id is None:
            return

        try:
            subject_id = int(user_id)
        except (TypeError, ValueError):
            return

        await DecisionAuditService.record_decision_safe(
            operator_id=subject_id,
            subject_type="USER",
            subject_id=subject_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action_code=action_code,
            result="ALLOW" if bool(decision.get("allowed")) else "DENY",
            reason=str(decision.get("reason") or ""),
            matched_acl_id=decision.get("matched_acl_id"),
            matched_policy_id=decision.get("matched_policy_id"),
            matched_rule_id=decision.get("matched_rule_id"),
            matched_source=decision.get("matched_source"),
            decision_chain=decision.get("decision_chain"),
            trace_id=trace_id,
        )

    @classmethod
    async def _finalize_decision(
        cls,
        *,
        user: Any,
        resource_type: str,
        resource_id: str,
        action_code: str,
        decision: dict[str, Any],
        trace_id: str | None,
    ) -> dict[str, Any]:
        """Record decision audit and return the final decision payload."""
        await cls._record_decision_audit(
            user=user,
            resource_type=resource_type,
            resource_id=resource_id,
            action_code=action_code,
            decision=decision,
            trace_id=trace_id,
        )
        return decision

    @classmethod
    async def check(cls, *, user: Any, data: dict[str, Any], trace_id: str | None = None) -> dict[str, Any]:
        """Authorize one resource action for the current user."""
        request_data: dict[str, Any] = cls._ensure_request_data(data)

        resource_type: str = cls._normalize_resource_type(request_data.get("resource_type"))
        resource_id: str = cls._normalize_resource_id(request_data.get("resource_id"))
        action_code: str = cls._normalize_action_code(request_data.get("action_code"))
        user_id = getattr(user, "id", None)
        permission_code: str | None = None
        access_mode: str | None = None

        decision_chain: list[dict[str, Any]] = []
        hit_details: dict[str, Any] = {
            "resource": {"access_mode": None},
            "acl": {"matched": False},
            "policy": {"matched": False},
            "rbac": {"matched": False},
        }

        if user is None or not bool(getattr(user, "is_active", False)):
            cls._append_chain(
                decision_chain,
                source=cls.MATCHED_SOURCE_NONE,
                effect=cls.EFFECT_DENY,
                reason="USER_INACTIVE",
            )
            decision = cls._build_decision(
                allowed=False,
                reason="USER_INACTIVE",
                matched_source=cls.MATCHED_SOURCE_NONE,
                access_mode=access_mode,
                hit_details=hit_details,
                decision_chain=decision_chain,
            )
            return await cls._finalize_decision(
                user=user,
                resource_type=resource_type,
                resource_id=resource_id,
                action_code=action_code,
                decision=decision,
                trace_id=trace_id,
            )

        try:
            await cls._run_with_backoff(
                operation=lambda: cls._ensure_resource_action_registered(resource_type=resource_type, action_code=action_code),
                operation_name="authorize_ensure_resource_action_registered",
                user_id=None if user_id is None else int(user_id),
                resource_type=resource_type,
                action_code=action_code,
            )

            permission_code = cls._resolve_permission_code(
                request_data=request_data,
                resource_type=resource_type,
                action_code=action_code,
            )

            try:
                access_mode = await cls._run_with_backoff(
                    operation=lambda: cls._resolve_resource_access_mode(resource_type=resource_type),
                    operation_name="authorize_resolve_resource_access_mode",
                    user_id=None if user_id is None else int(user_id),
                    resource_type=resource_type,
                    action_code=action_code,
                )
            except BusinessError as exc:
                if str(getattr(exc, "msg", "")) == "resource access_mode is invalid":
                    cls._append_chain(
                        decision_chain,
                        source=cls.MATCHED_SOURCE_NONE,
                        effect=cls.EFFECT_DENY,
                        reason="INVALID_ACCESS_MODE",
                    )
                    decision = cls._build_decision(
                        allowed=False,
                        reason="INVALID_ACCESS_MODE",
                        matched_source=cls.MATCHED_SOURCE_NONE,
                        access_mode=None,
                        hit_details=hit_details,
                        decision_chain=decision_chain,
                    )
                    return await cls._finalize_decision(
                        user=user,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        action_code=action_code,
                        decision=decision,
                        trace_id=trace_id,
                    )
                raise

            hit_details["resource"] = {"access_mode": access_mode}

            if bool(getattr(user, "is_superuser", False)):
                cls._append_chain(
                    decision_chain,
                    source=cls.MATCHED_SOURCE_SUPERUSER,
                    effect=cls.EFFECT_ALLOW,
                    reason="SUPERUSER_BYPASS",
                )
                decision = cls._build_decision(
                    allowed=True,
                    reason="SUPERUSER_BYPASS",
                    matched_source=cls.MATCHED_SOURCE_SUPERUSER,
                    access_mode=access_mode,
                    filters={},
                    hit_details=hit_details,
                    decision_chain=decision_chain,
                )
                return await cls._finalize_decision(
                    user=user,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action_code=action_code,
                    decision=decision,
                    trace_id=trace_id,
                )

            subject_bindings: list[tuple[str, int]] = await cls._run_with_backoff(
                operation=lambda: cls._build_subject_bindings(user=user),
                operation_name="authorize_build_subject_bindings",
                user_id=None if user_id is None else int(user_id),
                resource_type=resource_type,
                action_code=action_code,
            )

            acl_result: dict[str, Any] | None = await cls._run_with_backoff(
                operation=lambda: ResourceAclService.resolve_acl_effect(
                    subject_bindings=subject_bindings,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action_code=action_code,
                ),
                operation_name="authorize_resolve_acl_effect",
                user_id=None if user_id is None else int(user_id),
                resource_type=resource_type,
                action_code=action_code,
            )

            if acl_result is None:
                cls._append_chain(
                    decision_chain,
                    source=cls.MATCHED_SOURCE_ACL,
                    effect="none",
                    reason="ACL_NOT_MATCHED",
                )

            if acl_result is not None and acl_result.get("effect") == ResourceAclService.EFFECT_DENY:
                hit_details["acl"] = {
                    "matched": True,
                    "effect": ResourceAclService.EFFECT_DENY,
                    "matched_acl_id": acl_result.get("matched_acl_id"),
                    "matched_source": acl_result.get("matched_source"),
                }
                cls._append_chain(
                    decision_chain,
                    source=cls.MATCHED_SOURCE_ACL,
                    effect=cls.EFFECT_DENY,
                    reason=str(acl_result.get("reason", "ACL_DENY")),
                    matched_acl_id=acl_result.get("matched_acl_id"),
                    matched_source=acl_result.get("matched_source"),
                )
                decision = cls._build_decision(
                    allowed=False,
                    reason=str(acl_result.get("reason", "ACL_DENY")),
                    matched_source=cls.MATCHED_SOURCE_ACL,
                    access_mode=access_mode,
                    matched_acl_id=acl_result.get("matched_acl_id"),
                    hit_details=hit_details,
                    decision_chain=decision_chain,
                )
                return await cls._finalize_decision(
                    user=user,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action_code=action_code,
                    decision=decision,
                    trace_id=trace_id,
                )

            policy_result: dict[str, Any] | None = await cls._run_with_backoff(
                operation=lambda: PolicyEngineService.evaluate(
                    subject_bindings=subject_bindings,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action_code=action_code,
                    context=cls._normalize_context(request_data.get("context")),
                ),
                operation_name="authorize_policy_evaluate",
                user_id=None if user_id is None else int(user_id),
                resource_type=resource_type,
                action_code=action_code,
            )
            if policy_result is not None and str(policy_result.get("effect", "")).upper() == PolicyEngineService.EFFECT_DENY:
                hit_details["policy"] = {
                    "matched": True,
                    "effect": PolicyEngineService.EFFECT_DENY,
                    "matched_policy_id": policy_result.get("matched_policy_id"),
                    "matched_rule_id": policy_result.get("matched_rule_id"),
                }
                cls._append_chain(
                    decision_chain,
                    source=cls.MATCHED_SOURCE_POLICY,
                    effect=cls.EFFECT_DENY,
                    reason=str(policy_result.get("reason") or "POLICY_DENY"),
                    matched_policy_id=policy_result.get("matched_policy_id"),
                    matched_rule_id=policy_result.get("matched_rule_id"),
                )
                decision = cls._build_decision(
                    allowed=False,
                    reason=str(policy_result.get("reason") or "POLICY_DENY"),
                    matched_source=cls.MATCHED_SOURCE_POLICY,
                    access_mode=access_mode,
                    matched_policy_id=policy_result.get("matched_policy_id"),
                    matched_rule_id=policy_result.get("matched_rule_id"),
                    hit_details=hit_details,
                    decision_chain=decision_chain,
                )
                return await cls._finalize_decision(
                    user=user,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action_code=action_code,
                    decision=decision,
                    trace_id=trace_id,
                )

            if acl_result is not None and acl_result.get("effect") == ResourceAclService.EFFECT_ALLOW:
                hit_details["acl"] = {
                    "matched": True,
                    "effect": ResourceAclService.EFFECT_ALLOW,
                    "matched_acl_id": acl_result.get("matched_acl_id"),
                    "matched_source": acl_result.get("matched_source"),
                    "matched_acl_depth": acl_result.get("matched_acl_depth"),
                }
                acl_filters: dict[str, Any] = await cls._run_with_backoff(
                    operation=lambda: cls._resolve_data_filters(
                        user=user,
                        permission_code=permission_code,
                        field_map_data=request_data.get("field_map"),
                    ),
                    operation_name="authorize_acl_data_scope_filters",
                    user_id=None if user_id is None else int(user_id),
                    resource_type=resource_type,
                    action_code=action_code,
                )
                if acl_result.get("data_scope"):
                    acl_filters.setdefault("acl_data_scope", acl_result.get("data_scope"))

                cls._append_chain(
                    decision_chain,
                    source=cls.MATCHED_SOURCE_ACL,
                    effect=cls.EFFECT_ALLOW,
                    reason=str(acl_result.get("reason", "ACL_ALLOW")),
                    matched_acl_id=acl_result.get("matched_acl_id"),
                    matched_source=acl_result.get("matched_source"),
                    matched_acl_depth=acl_result.get("matched_acl_depth"),
                )
                decision = cls._build_decision(
                    allowed=True,
                    reason=str(acl_result.get("reason", "ACL_ALLOW")),
                    matched_source=cls.MATCHED_SOURCE_ACL,
                    access_mode=access_mode,
                    filters=acl_filters,
                    matched_acl_id=acl_result.get("matched_acl_id"),
                    hit_details=hit_details,
                    decision_chain=decision_chain,
                )
                return await cls._finalize_decision(
                    user=user,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action_code=action_code,
                    decision=decision,
                    trace_id=trace_id,
                )

            if policy_result is not None and str(policy_result.get("effect", "")).upper() == PolicyEngineService.EFFECT_ALLOW:
                hit_details["policy"] = {
                    "matched": True,
                    "effect": PolicyEngineService.EFFECT_ALLOW,
                    "matched_policy_id": policy_result.get("matched_policy_id"),
                    "matched_rule_id": policy_result.get("matched_rule_id"),
                }
                policy_filters: dict[str, Any] = await cls._run_with_backoff(
                    operation=lambda: cls._resolve_data_filters(
                        user=user,
                        permission_code=permission_code,
                        field_map_data=request_data.get("field_map"),
                    ),
                    operation_name="authorize_policy_data_scope_filters",
                    user_id=None if user_id is None else int(user_id),
                    resource_type=resource_type,
                    action_code=action_code,
                )
                data_scope = policy_result.get("data_scope")
                if data_scope:
                    policy_filters.setdefault("policy_data_scope", data_scope)

                cls._append_chain(
                    decision_chain,
                    source=cls.MATCHED_SOURCE_POLICY,
                    effect=cls.EFFECT_ALLOW,
                    reason=str(policy_result.get("reason") or "POLICY_ALLOW"),
                    matched_policy_id=policy_result.get("matched_policy_id"),
                    matched_rule_id=policy_result.get("matched_rule_id"),
                )

                decision = cls._build_decision(
                    allowed=True,
                    reason=str(policy_result.get("reason") or "POLICY_ALLOW"),
                    matched_source=cls.MATCHED_SOURCE_POLICY,
                    access_mode=access_mode,
                    filters=policy_filters,
                    matched_policy_id=policy_result.get("matched_policy_id"),
                    matched_rule_id=policy_result.get("matched_rule_id"),
                    hit_details=hit_details,
                    decision_chain=decision_chain,
                )
                return await cls._finalize_decision(
                    user=user,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action_code=action_code,
                    decision=decision,
                    trace_id=trace_id,
                )

            if permission_code is not None:
                has_rbac_permission: bool = await cls._run_with_backoff(
                    operation=lambda: PermissionService.has_permission(user=user, permission_code=permission_code),
                    operation_name="authorize_rbac_has_permission",
                    user_id=None if user_id is None else int(user_id),
                    resource_type=resource_type,
                    action_code=action_code,
                )
                if has_rbac_permission:
                    if access_mode == RESOURCE_ACCESS_MODE_ACL_REQUIRED:
                        hit_details["rbac"] = {
                            "matched": True,
                            "effect": cls.EFFECT_DENY,
                            "permission_code": permission_code,
                            "access_mode": access_mode,
                        }
                        cls._append_chain(
                            decision_chain,
                            source=cls.MATCHED_SOURCE_RBAC,
                            effect=cls.EFFECT_DENY,
                            reason="RBAC_ALLOW_BLOCKED_BY_ACL_REQUIRED",
                            permission_code=permission_code,
                            access_mode=access_mode,
                        )
                        decision = cls._build_decision(
                            allowed=False,
                            reason="ACL_REQUIRED_NO_RESOURCE_ALLOW",
                            matched_source=cls.MATCHED_SOURCE_RBAC,
                            access_mode=access_mode,
                            matched_rbac_permission_code=permission_code,
                            hit_details=hit_details,
                            decision_chain=decision_chain,
                        )
                        return await cls._finalize_decision(
                            user=user,
                            resource_type=resource_type,
                            resource_id=resource_id,
                            action_code=action_code,
                            decision=decision,
                            trace_id=trace_id,
                        )

                    hit_details["rbac"] = {
                        "matched": True,
                        "effect": cls.EFFECT_ALLOW,
                        "permission_code": permission_code,
                        "access_mode": access_mode,
                    }
                    rbac_filters: dict[str, Any] = await cls._run_with_backoff(
                        operation=lambda: cls._resolve_data_filters(
                            user=user,
                            permission_code=permission_code,
                            field_map_data=request_data.get("field_map"),
                        ),
                        operation_name="authorize_rbac_data_scope_filters",
                        user_id=None if user_id is None else int(user_id),
                        resource_type=resource_type,
                        action_code=action_code,
                    )
                    cls._append_chain(
                        decision_chain,
                        source=cls.MATCHED_SOURCE_RBAC,
                        effect=cls.EFFECT_ALLOW,
                        reason="RBAC_ALLOW",
                        permission_code=permission_code,
                    )
                    decision = cls._build_decision(
                        allowed=True,
                        reason="RBAC_ALLOW",
                        matched_source=cls.MATCHED_SOURCE_RBAC,
                        access_mode=access_mode,
                        filters=rbac_filters,
                        matched_rbac_permission_code=permission_code,
                        hit_details=hit_details,
                        decision_chain=decision_chain,
                    )
                    return await cls._finalize_decision(
                        user=user,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        action_code=action_code,
                        decision=decision,
                        trace_id=trace_id,
                    )

                cls._append_chain(
                    decision_chain,
                    source=cls.MATCHED_SOURCE_RBAC,
                    effect=cls.EFFECT_DENY,
                    reason="RBAC_NOT_GRANTED",
                    permission_code=permission_code,
                )

            if policy_result is None:
                cls._append_chain(
                    decision_chain,
                    source=cls.MATCHED_SOURCE_POLICY,
                    effect="none",
                    reason="POLICY_NOT_MATCHED",
                )

            decision = cls._build_decision(
                allowed=False,
                reason="NO_MATCHED_RULE",
                matched_source=cls.MATCHED_SOURCE_NONE,
                access_mode=access_mode,
                hit_details=hit_details,
                decision_chain=decision_chain,
            )
            return await cls._finalize_decision(
                user=user,
                resource_type=resource_type,
                resource_id=resource_id,
                action_code=action_code,
                decision=decision,
                trace_id=trace_id,
            )
        except BusinessError:
            raise
        except Exception as exc:  # noqa
            retry_count = int(getattr(exc, "_iam_retry_count", 0) or 0)
            IAM_LOGGER.error(
                "authorization check failed | resource_type=%s resource_id=%s action_code=%s user_id=%s retry_count=%s exception_class=%s",
                resource_type,
                resource_id,
                action_code,
                user_id,
                retry_count,
                exc.__class__.__name__,
                exc_info=True,
            )
            decision = cls._build_authorization_failed_decision(
                permission_code=permission_code,
                retry_count=retry_count,
                error=exc,
                access_mode=access_mode,
            )
            return await cls._finalize_decision(
                user=user,
                resource_type=resource_type,
                resource_id=resource_id,
                action_code=action_code,
                decision=decision,
                trace_id=trace_id,
            )

    @classmethod
    async def batch_check(cls, *, user: Any, data: dict[str, Any], trace_id: str | None = None) -> dict[str, Any]:
        """Authorize multiple resource actions in one request."""
        request_data: dict[str, Any] = cls._ensure_request_data(data)
        items: Any = request_data.get("items")

        if not isinstance(items, list) or not items:
            raise BusinessError("items must be a non-empty list", NsErrorCode.INVALID_VALUE)

        decisions: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                raise BusinessError("items must contain object elements", NsErrorCode.INVALID_VALUE)
            decision: dict[str, Any] = await cls.check(user=user, data=item, trace_id=trace_id)
            decisions.append(decision)

        return {
            "items": decisions,
            "total": len(decisions),
        }

