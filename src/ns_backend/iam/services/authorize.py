# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.repositories import AuthorizeRepository
from ns_backend.iam.schemas import DataScopeFieldMap, DataScopeFilterPlan
from ns_backend.iam.services.data_scope import DataScopeService
from ns_backend.iam.services.decision_audit import DecisionAuditService
from ns_backend.iam.services.permission import PermissionService
from ns_backend.iam.services.policy_engine import PolicyEngineService
from ns_backend.iam.services.resource_acl import ResourceAclService
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


class AuthorizeService:
    """Evaluate unified IAM authorization decisions for one or many actions."""

    MATCHED_SOURCE_ACL = "acl"
    MATCHED_SOURCE_POLICY = "policy"
    MATCHED_SOURCE_RBAC = "rbac"
    MATCHED_SOURCE_SUPERUSER = "superuser"
    MATCHED_SOURCE_NONE = "none"

    EFFECT_ALLOW = "allow"
    EFFECT_DENY = "deny"

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
        if action_code not in ResourceAclService.ALLOWED_ACTION_CODES:
            raise BusinessError("action_code is invalid", NsErrorCode.PERMISSION_ACTION_INVALID)
        return action_code

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
        filters: dict[str, Any] | None = None,
        matched_policy_id: int | None = None,
        matched_rule_id: int | None = None,
    ) -> dict[str, Any]:
        """Build one normalized authorization decision payload."""
        return {
            "allowed": bool(allowed),
            "effect": cls.EFFECT_ALLOW if allowed else cls.EFFECT_DENY,
            "reason": reason,
            "matched_source": matched_source,
            "matched_policy_id": matched_policy_id,
            "matched_rule_id": matched_rule_id,
            "filters": {} if filters is None else filters,
        }

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
            matched_policy_id=decision.get("matched_policy_id"),
            matched_rule_id=decision.get("matched_rule_id"),
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

        if user is None or not bool(getattr(user, "is_active", False)):
            decision = cls._build_decision(
                allowed=False,
                reason="USER_INACTIVE",
                matched_source=cls.MATCHED_SOURCE_NONE,
            )
            return await cls._finalize_decision(
                user=user,
                resource_type=resource_type,
                resource_id=resource_id,
                action_code=action_code,
                decision=decision,
                trace_id=trace_id,
            )

        permission_code: str | None = cls._resolve_permission_code(
            request_data=request_data,
            resource_type=resource_type,
            action_code=action_code,
        )

        if bool(getattr(user, "is_superuser", False)):
            decision = cls._build_decision(
                allowed=True,
                reason="SUPERUSER_BYPASS",
                matched_source=cls.MATCHED_SOURCE_SUPERUSER,
                filters={},
            )
            return await cls._finalize_decision(
                user=user,
                resource_type=resource_type,
                resource_id=resource_id,
                action_code=action_code,
                decision=decision,
                trace_id=trace_id,
            )

        subject_bindings: list[tuple[str, int]] = await cls._build_subject_bindings(user=user)
        acl_result: dict[str, Any] | None = await ResourceAclService.resolve_acl_effect(
            subject_bindings=subject_bindings,
            resource_type=resource_type,
            resource_id=resource_id,
            action_code=action_code,
        )

        if acl_result is not None and acl_result.get("effect") == ResourceAclService.EFFECT_DENY:
            decision = cls._build_decision(
                allowed=False,
                reason=str(acl_result.get("reason", "ACL_DENY")),
                matched_source=cls.MATCHED_SOURCE_ACL,
            )
            return await cls._finalize_decision(
                user=user,
                resource_type=resource_type,
                resource_id=resource_id,
                action_code=action_code,
                decision=decision,
                trace_id=trace_id,
            )

        policy_result: dict[str, Any] | None = await PolicyEngineService.evaluate(
            subject_bindings=subject_bindings,
            resource_type=resource_type,
            resource_id=resource_id,
            action_code=action_code,
            context=cls._normalize_context(request_data.get("context")),
        )
        if policy_result is not None and str(policy_result.get("effect", "")).upper() == PolicyEngineService.EFFECT_DENY:
            decision = cls._build_decision(
                allowed=False,
                reason=str(policy_result.get("reason") or "POLICY_DENY"),
                matched_source=cls.MATCHED_SOURCE_POLICY,
                matched_policy_id=policy_result.get("matched_policy_id"),
                matched_rule_id=policy_result.get("matched_rule_id"),
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
            acl_filters: dict[str, Any] = await cls._resolve_data_filters(
                user=user,
                permission_code=permission_code,
                field_map_data=request_data.get("field_map"),
            )
            decision = cls._build_decision(
                allowed=True,
                reason=str(acl_result.get("reason", "ACL_ALLOW")),
                matched_source=cls.MATCHED_SOURCE_ACL,
                filters=acl_filters,
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
            policy_filters: dict[str, Any] = await cls._resolve_data_filters(
                user=user,
                permission_code=permission_code,
                field_map_data=request_data.get("field_map"),
            )
            data_scope = policy_result.get("data_scope")
            if data_scope:
                policy_filters.setdefault("policy_data_scope", data_scope)

            decision = cls._build_decision(
                allowed=True,
                reason=str(policy_result.get("reason") or "POLICY_ALLOW"),
                matched_source=cls.MATCHED_SOURCE_POLICY,
                filters=policy_filters,
                matched_policy_id=policy_result.get("matched_policy_id"),
                matched_rule_id=policy_result.get("matched_rule_id"),
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
            has_rbac_permission: bool = await PermissionService.has_permission(user=user, permission_code=permission_code)
            if has_rbac_permission:
                rbac_filters: dict[str, Any] = await cls._resolve_data_filters(
                    user=user,
                    permission_code=permission_code,
                    field_map_data=request_data.get("field_map"),
                )
                decision = cls._build_decision(
                    allowed=True,
                    reason="RBAC_ALLOW",
                    matched_source=cls.MATCHED_SOURCE_RBAC,
                    filters=rbac_filters,
                )
                return await cls._finalize_decision(
                    user=user,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action_code=action_code,
                    decision=decision,
                    trace_id=trace_id,
                )

        decision = cls._build_decision(
            allowed=False,
            reason="NO_MATCHED_RULE",
            matched_source=cls.MATCHED_SOURCE_NONE,
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

