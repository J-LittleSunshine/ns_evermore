# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from typing import (
    Any,
    TYPE_CHECKING,
)

from django.db.utils import DatabaseError
from django.utils import timezone

from ns_backend.iam.constants import (
    PERMISSION_EFFECT_ALLOW,
    PERMISSION_EFFECT_DENY,
    RESOURCE_ACCESS_MODE_ACL_REQUIRED,
    RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW,
)
from ns_backend.iam.errors import IamRuntimeRequestInvalidError
from ns_backend.iam.repositories import AccessDecisionRepository
from ns_backend.iam.schemas import DataScopeFieldMap
from ns_backend.iam.services.backoff import (
    get_backoff_enabled,
    retry_with_backoff,
)
from ns_backend.iam.services.data_scope import DataScopeService
from ns_backend.iam.services.decision_audit import DecisionAuditService
from ns_backend.iam.services.permission import PermissionService
from ns_backend.iam.services.policy_engine import PolicyEngineService
from ns_common import get_ns_logger

if TYPE_CHECKING:
    pass

logger = get_ns_logger("ns_backend.iam.access_decision", True)

class AccessDecisionService:
    EFFECT_ALLOW = "allow"
    EFFECT_DENY = "deny"

    MATCHED_SOURCE_ACL = "acl"
    MATCHED_SOURCE_RBAC = "rbac"
    MATCHED_SOURCE_SUPERUSER = "superuser"
    MATCHED_SOURCE_NONE = "none"
    MATCHED_SOURCE_POLICY = "policy"

    ACTION_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")

    RETRYABLE_EXCEPTIONS = (
        DatabaseError,
        ConnectionError,
        TimeoutError,
        OSError,
        RuntimeError,
    )

    @classmethod
    async def check_with_audit(cls, *, user: Any, data: dict[str, Any], trace_id: str | None = None) -> dict[str, Any]:
        decision = await cls.check(
            user=user,
            data=data,
            trace_id=trace_id,
        )

        await DecisionAuditService.record_from_decision_safe(
            user=user,
            decision=decision,
            trace_id=trace_id,
        )

        return decision

    @classmethod
    async def batch_check_with_audit(cls, *, user: Any, data: dict[str, Any], trace_id: str | None = None) -> dict[str, Any]:
        request_data = cls.ensure_dict(data)
        items = request_data.get("items")

        if not isinstance(items, list) or not items:
            raise IamRuntimeRequestInvalidError(
                "items must be a non-empty list.",
            )

        decisions = []

        for item in items:
            if not isinstance(item, dict):
                raise IamRuntimeRequestInvalidError(
                    "items must contain object elements.",
                )

            decisions.append(
                await cls.check_with_audit(
                    user=user,
                    data=item,
                    trace_id=trace_id,
                )
            )

        return {
            "items": decisions,
            "total": len(decisions),
        }

    @classmethod
    async def check(cls, *, user: Any, data: dict[str, Any], trace_id: str | None = None) -> dict[str, Any]:
        request_data = cls.ensure_dict(data)

        resource_type = cls.normalize_resource_type(request_data.get("resource_type"))
        resource_id = cls.normalize_required_text(request_data.get("resource_id"), "resource_id")
        action_code = cls.normalize_action_code(request_data.get("action_code"))
        permission_code = cls.resolve_permission_code(
            request_data=request_data,
            resource_type=resource_type,
            action_code=action_code,
        )

        attempt_count = 0

        async def operation() -> dict[str, Any]:
            nonlocal attempt_count
            attempt_count += 1

            return await cls.check_once(
                user=user,
                data=request_data,
                trace_id=trace_id,
            )

        try:
            if get_backoff_enabled():
                return await retry_with_backoff(
                    operation,
                    retryable_exceptions=cls.RETRYABLE_EXCEPTIONS,
                    operation_name="iam_access_decision_check",
                )

            return await operation()

        except IamRuntimeRequestInvalidError:
            raise

        except Exception as exc:  # noqa
            retry_count = max(attempt_count - 1, 0)

            logger.error(
                "authorization check failed",
                exc_info=True,
                extra={
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "action_code": action_code,
                    "permission_code": permission_code,
                    "user_id": getattr(user, "id", None),
                    "retry_count": retry_count,
                    "exception_class": exc.__class__.__name__,
                },
            )

            return cls.build_authorization_failed_decision(
                resource_type=resource_type,
                resource_id=resource_id,
                action_code=action_code,
                permission_code=permission_code,
                retry_count=retry_count,
                error=exc,
                trace_id=trace_id,
            )

    @classmethod
    async def check_once(cls, *, user: Any, data: dict[str, Any], trace_id: str | None = None) -> dict[str, Any]:
        request_data = cls.ensure_dict(data)

        resource_type = cls.normalize_resource_type(request_data.get("resource_type"))
        resource_id = cls.normalize_required_text(request_data.get("resource_id"), "resource_id")
        action_code = cls.normalize_action_code(request_data.get("action_code"))
        permission_code = cls.resolve_permission_code(
            request_data=request_data,
            resource_type=resource_type,
            action_code=action_code,
        )

        decision_chain: list[dict[str, Any]] = []
        hit_details: dict[str, Any] = {
            "resource": {
                "matched": False,
                "access_mode": None,
            },
            "acl": {
                "matched": False,
            },
            "policy": {
                "matched": False,
            },
            "rbac": {
                "matched": False,
            },
        }

        if user is None or not bool(getattr(user, "is_active", False)):
            cls.append_chain(
                decision_chain,
                source=cls.MATCHED_SOURCE_NONE,
                effect=cls.EFFECT_DENY,
                reason="USER_INACTIVE",
            )

            return cls.build_decision(
                allowed=False,
                reason="USER_INACTIVE",
                matched_source=cls.MATCHED_SOURCE_NONE,
                resource_type=resource_type,
                resource_id=resource_id,
                action_code=action_code,
                permission_code=permission_code,
                hit_details=hit_details,
                decision_chain=decision_chain,
                trace_id=trace_id,
            )

        resource = await AccessDecisionRepository.get_resource_by_type(
            resource_type=resource_type,
        )

        if resource is None:
            cls.append_chain(
                decision_chain,
                source=cls.MATCHED_SOURCE_NONE,
                effect=cls.EFFECT_DENY,
                reason="RESOURCE_TYPE_NOT_REGISTERED",
            )

            return cls.build_decision(
                allowed=False,
                reason="RESOURCE_TYPE_NOT_REGISTERED",
                matched_source=cls.MATCHED_SOURCE_NONE,
                resource_type=resource_type,
                resource_id=resource_id,
                action_code=action_code,
                permission_code=permission_code,
                hit_details=hit_details,
                decision_chain=decision_chain,
                trace_id=trace_id,
            )

        action_registered = await AccessDecisionRepository.has_action_for_resource_type(
            resource_type=resource_type,
            action_code=action_code,
        )

        if not action_registered:
            cls.append_chain(
                decision_chain,
                source=cls.MATCHED_SOURCE_NONE,
                effect=cls.EFFECT_DENY,
                reason="RESOURCE_ACTION_NOT_REGISTERED",
            )

            return cls.build_decision(
                allowed=False,
                reason="RESOURCE_ACTION_NOT_REGISTERED",
                matched_source=cls.MATCHED_SOURCE_NONE,
                resource_type=resource_type,
                resource_id=resource_id,
                action_code=action_code,
                permission_code=permission_code,
                hit_details=hit_details,
                decision_chain=decision_chain,
                trace_id=trace_id,
            )

        access_mode = cls.normalize_access_mode(
            getattr(resource, "access_mode", None)
        )

        hit_details["resource"] = {
            "matched": True,
            "access_mode": access_mode,
        }

        if bool(getattr(user, "is_superuser", False)):
            cls.append_chain(
                decision_chain,
                source=cls.MATCHED_SOURCE_SUPERUSER,
                effect=cls.EFFECT_ALLOW,
                reason="SUPERUSER_BYPASS",
            )

            return cls.build_decision(
                allowed=True,
                reason="SUPERUSER_BYPASS",
                matched_source=cls.MATCHED_SOURCE_SUPERUSER,
                resource_type=resource_type,
                resource_id=resource_id,
                action_code=action_code,
                permission_code=permission_code,
                access_mode=access_mode,
                hit_details=hit_details,
                decision_chain=decision_chain,
                trace_id=trace_id,
            )

        subject_bindings = await cls.build_subject_bindings(user=user)

        acl_result = await cls.resolve_acl_effect(
            subject_bindings=subject_bindings,
            resource_type=resource_type,
            resource_id=resource_id,
            action_code=action_code,
        )

        policy_result = await PolicyEngineService.evaluate(
            subject_bindings=subject_bindings,
            resource_type=resource_type,
            resource_id=resource_id,
            action_code=action_code,
            context=cls.build_policy_context(
                request_data=request_data,
                user=user,
                resource_type=resource_type,
                resource_id=resource_id,
                action_code=action_code,
                permission_code=permission_code,
                access_mode=access_mode,
            ),
        )

        if acl_result is None:
            cls.append_chain(
                decision_chain,
                source=cls.MATCHED_SOURCE_ACL,
                effect="none",
                reason="ACL_NOT_MATCHED",
            )

        if acl_result is not None and acl_result.get("effect") == PERMISSION_EFFECT_DENY:
            hit_details["acl"] = {
                "matched": True,
                "effect": PERMISSION_EFFECT_DENY,
                "matched_acl_id": acl_result.get("matched_acl_id"),
                "matched_acl_depth": acl_result.get("matched_acl_depth"),
                "matched_resource_type": acl_result.get("matched_resource_type"),
                "matched_resource_id": acl_result.get("matched_resource_id"),
            }

            cls.append_chain(
                decision_chain,
                source=cls.MATCHED_SOURCE_ACL,
                effect=cls.EFFECT_DENY,
                reason="ACL_DENY",
                matched_acl_id=acl_result.get("matched_acl_id"),
                matched_acl_depth=acl_result.get("matched_acl_depth"),
            )

            return cls.build_decision(
                allowed=False,
                reason="ACL_DENY",
                matched_source=cls.MATCHED_SOURCE_ACL,
                resource_type=resource_type,
                resource_id=resource_id,
                action_code=action_code,
                permission_code=permission_code,
                access_mode=access_mode,
                matched_acl_id=acl_result.get("matched_acl_id"),
                hit_details=hit_details,
                decision_chain=decision_chain,
                trace_id=trace_id,
            )

        if policy_result is None:
            cls.append_chain(
                decision_chain,
                source=cls.MATCHED_SOURCE_POLICY,
                effect="none",
                reason="POLICY_NOT_MATCHED",
            )

        if policy_result is not None and policy_result.get("effect") == PERMISSION_EFFECT_DENY:
            hit_details["policy"] = {
                "matched": True,
                "effect": PERMISSION_EFFECT_DENY,
                "matched_policy_id": policy_result.get("matched_policy_id"),
                "matched_rule_id": policy_result.get("matched_rule_id"),
                "data_scope": policy_result.get("data_scope"),
            }

            cls.append_chain(
                decision_chain,
                source=cls.MATCHED_SOURCE_POLICY,
                effect=cls.EFFECT_DENY,
                reason="POLICY_DENY",
                matched_policy_id=policy_result.get("matched_policy_id"),
                matched_rule_id=policy_result.get("matched_rule_id"),
            )

            return cls.build_decision(
                allowed=False,
                reason="POLICY_DENY",
                matched_source=cls.MATCHED_SOURCE_POLICY,
                resource_type=resource_type,
                resource_id=resource_id,
                action_code=action_code,
                permission_code=permission_code,
                access_mode=access_mode,
                matched_policy_id=policy_result.get("matched_policy_id"),
                matched_rule_id=policy_result.get("matched_rule_id"),
                hit_details=hit_details,
                decision_chain=decision_chain,
                trace_id=trace_id,
            )

        if acl_result is not None and acl_result.get("effect") == PERMISSION_EFFECT_ALLOW:
            hit_details["acl"] = {
                "matched": True,
                "effect": PERMISSION_EFFECT_ALLOW,
                "matched_acl_id": acl_result.get("matched_acl_id"),
                "matched_acl_depth": acl_result.get("matched_acl_depth"),
                "matched_resource_type": acl_result.get("matched_resource_type"),
                "matched_resource_id": acl_result.get("matched_resource_id"),
                "data_scope": acl_result.get("data_scope"),
            }

            filters = await cls.resolve_data_filters(
                user=user,
                permission_code=permission_code,
                field_map_data=request_data.get("field_map"),
            )

            if acl_result.get("data_scope"):
                filters.setdefault("acl_data_scope", acl_result.get("data_scope"))

            cls.append_chain(
                decision_chain,
                source=cls.MATCHED_SOURCE_ACL,
                effect=cls.EFFECT_ALLOW,
                reason="ACL_ALLOW",
                matched_acl_id=acl_result.get("matched_acl_id"),
                matched_acl_depth=acl_result.get("matched_acl_depth"),
            )

            return cls.build_decision(
                allowed=True,
                reason="ACL_ALLOW",
                matched_source=cls.MATCHED_SOURCE_ACL,
                resource_type=resource_type,
                resource_id=resource_id,
                action_code=action_code,
                permission_code=permission_code,
                access_mode=access_mode,
                filters=filters,
                matched_acl_id=acl_result.get("matched_acl_id"),
                hit_details=hit_details,
                decision_chain=decision_chain,
                trace_id=trace_id,
            )

        if policy_result is not None and policy_result.get("effect") == PERMISSION_EFFECT_ALLOW:
            hit_details["policy"] = {
                "matched": True,
                "effect": PERMISSION_EFFECT_ALLOW,
                "matched_policy_id": policy_result.get("matched_policy_id"),
                "matched_rule_id": policy_result.get("matched_rule_id"),
                "data_scope": policy_result.get("data_scope"),
            }

            filters = await cls.resolve_data_filters(
                user=user,
                permission_code=permission_code,
                field_map_data=request_data.get("field_map"),
            )

            if policy_result.get("data_scope"):
                filters.setdefault("policy_data_scope", policy_result.get("data_scope"))

            cls.append_chain(
                decision_chain,
                source=cls.MATCHED_SOURCE_POLICY,
                effect=cls.EFFECT_ALLOW,
                reason="POLICY_ALLOW",
                matched_policy_id=policy_result.get("matched_policy_id"),
                matched_rule_id=policy_result.get("matched_rule_id"),
            )

            return cls.build_decision(
                allowed=True,
                reason="POLICY_ALLOW",
                matched_source=cls.MATCHED_SOURCE_POLICY,
                resource_type=resource_type,
                resource_id=resource_id,
                action_code=action_code,
                permission_code=permission_code,
                access_mode=access_mode,
                filters=filters,
                matched_policy_id=policy_result.get("matched_policy_id"),
                matched_rule_id=policy_result.get("matched_rule_id"),
                hit_details=hit_details,
                decision_chain=decision_chain,
                trace_id=trace_id,
            )

        if access_mode == RESOURCE_ACCESS_MODE_ACL_REQUIRED:
            cls.append_chain(
                decision_chain,
                source=cls.MATCHED_SOURCE_ACL,
                effect=cls.EFFECT_DENY,
                reason="ACL_REQUIRED_NO_RESOURCE_ALLOW",
            )

            return cls.build_decision(
                allowed=False,
                reason="ACL_REQUIRED_NO_RESOURCE_ALLOW",
                matched_source=cls.MATCHED_SOURCE_ACL,
                resource_type=resource_type,
                resource_id=resource_id,
                action_code=action_code,
                permission_code=permission_code,
                access_mode=access_mode,
                hit_details=hit_details,
                decision_chain=decision_chain,
                trace_id=trace_id,
            )

        if permission_code:
            has_rbac_permission = await PermissionService.has_permission(
                user,
                permission_code,
            )

            if has_rbac_permission:
                hit_details["rbac"] = {
                    "matched": True,
                    "effect": cls.EFFECT_ALLOW,
                    "permission_code": permission_code,
                    "access_mode": access_mode,
                }

                filters = await cls.resolve_data_filters(
                    user=user,
                    permission_code=permission_code,
                    field_map_data=request_data.get("field_map"),
                )

                cls.append_chain(
                    decision_chain,
                    source=cls.MATCHED_SOURCE_RBAC,
                    effect=cls.EFFECT_ALLOW,
                    reason="RBAC_ALLOW",
                    permission_code=permission_code,
                )

                return cls.build_decision(
                    allowed=True,
                    reason="RBAC_ALLOW",
                    matched_source=cls.MATCHED_SOURCE_RBAC,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action_code=action_code,
                    permission_code=permission_code,
                    access_mode=access_mode,
                    filters=filters,
                    matched_rbac_permission_code=permission_code,
                    hit_details=hit_details,
                    decision_chain=decision_chain,
                    trace_id=trace_id,
                )

            cls.append_chain(
                decision_chain,
                source=cls.MATCHED_SOURCE_RBAC,
                effect=cls.EFFECT_DENY,
                reason="RBAC_NOT_GRANTED",
                permission_code=permission_code,
            )
        else:
            cls.append_chain(
                decision_chain,
                source=cls.MATCHED_SOURCE_RBAC,
                effect="none",
                reason="PERMISSION_CODE_NOT_RESOLVED",
            )

        return cls.build_decision(
            allowed=False,
            reason="NO_MATCHED_RULE",
            matched_source=cls.MATCHED_SOURCE_NONE,
            resource_type=resource_type,
            resource_id=resource_id,
            action_code=action_code,
            permission_code=permission_code,
            access_mode=access_mode,
            hit_details=hit_details,
            decision_chain=decision_chain,
            trace_id=trace_id,
        )

    @classmethod
    async def batch_check(cls, *, user: Any, data: dict[str, Any], trace_id: str | None = None) -> dict[str, Any]:
        request_data = cls.ensure_dict(data)
        items = request_data.get("items")

        if not isinstance(items, list) or not items:
            raise IamRuntimeRequestInvalidError(
                "items must be a non-empty list.",
            )

        decisions = []

        for item in items:
            if not isinstance(item, dict):
                raise IamRuntimeRequestInvalidError(
                    "items must contain object elements.",
                )

            decisions.append(
                await cls.check(
                    user=user,
                    data=item,
                    trace_id=trace_id,
                )
            )

        return {
            "items": decisions,
            "total": len(decisions),
        }

    @classmethod
    async def build_subject_bindings(cls, *, user: Any) -> list[tuple[str, int]]:
        user_id = int(getattr(user, "id"))

        subject_bindings: list[tuple[str, int]] = [
            (
                "USER",
                user_id,
            )
        ]

        role_ids = await AccessDecisionRepository.list_active_role_ids_for_user(
            user_id=user_id,
        )

        subject_bindings.extend(
            (
                "ROLE",
                role_id,
            )
            for role_id in role_ids
        )

        department_id = getattr(user, "department_id", None)
        if department_id:
            subject_bindings.append(
                (
                    "DEPARTMENT",
                    int(department_id),
                )
            )

        company_id = getattr(user, "company_id", None)
        if company_id:
            subject_bindings.append(
                (
                    "ORGANIZATION",
                    int(company_id),
                )
            )

        subsidiary_id = getattr(user, "subsidiary_id", None)
        if subsidiary_id:
            subject_bindings.append(
                (
                    "SUBSIDIARY",
                    int(subsidiary_id),
                )
            )

        return subject_bindings

    @staticmethod
    def build_field_map(field_map_data: Any) -> DataScopeFieldMap:
        if not isinstance(field_map_data, dict):
            return DataScopeFieldMap(
                self_field=None,
                company_field="company_id",
                subsidiary_field="subsidiary_id",
                department_field="department_id",
            )

        return DataScopeFieldMap(
            self_field=field_map_data.get("self_field"),
            company_field=field_map_data.get("company_field", "company_id"),
            subsidiary_field=field_map_data.get("subsidiary_field", "subsidiary_id"),
            department_field=field_map_data.get("department_field", "department_id"),
        )

    @classmethod
    async def resolve_data_filters(cls,*,user: Any,permission_code: str | None,field_map_data: Any) -> dict[str, Any]:
        if permission_code is None:
            return {}

        filter_plan = await DataScopeService.resolve_filter_plan(
            user=user,
            permission_code=permission_code,
            field_map=cls.build_field_map(field_map_data),
        )

        if not filter_plan.allowed:
            return {
                "_denied_reason": filter_plan.reason,
            }

        return dict(filter_plan.filters or {})

    @classmethod
    def build_policy_context(cls,*,request_data: dict[str, Any],user: Any,resource_type: str,resource_id: str,action_code: str,permission_code: str | None,access_mode: str) -> dict[str, Any]:
        raw_context = request_data.get("context")

        if isinstance(raw_context, dict):
            context = dict(raw_context)
        else:
            context = {}

        context.setdefault("user_id", getattr(user, "id", None))
        context.setdefault("username", getattr(user, "username", None))
        context.setdefault("user_type", getattr(user, "user_type", None))
        context.setdefault("company_id", getattr(user, "company_id", None))
        context.setdefault("subsidiary_id", getattr(user, "subsidiary_id", None))
        context.setdefault("department_id", getattr(user, "department_id", None))
        context.setdefault("is_staff", bool(getattr(user, "is_staff", False)))
        context.setdefault("is_superuser", bool(getattr(user, "is_superuser", False)))

        context.setdefault("resource_type", resource_type)
        context.setdefault("resource_id", resource_id)
        context.setdefault("action_code", action_code)
        context.setdefault("permission_code", permission_code)
        context.setdefault("access_mode", access_mode)

        return context

    @classmethod
    async def resolve_acl_effect(cls, *, subject_bindings: list[tuple[str, int]], resource_type: str, resource_id: str, action_code: str) -> dict[str, Any] | None:
        now = timezone.now()

        resource_chain = await AccessDecisionRepository.list_resource_ancestor_chain(
            resource_type=resource_type,
            resource_id=resource_id,
        )

        resource_pairs = [
            (
                str(item.get("resource_type") or "").strip().lower(),
                str(item.get("resource_id") or "").strip(),
            )
            for item in resource_chain
            if str(item.get("resource_type") or "").strip()
               and str(item.get("resource_id") or "").strip()
        ]

        if not resource_pairs:
            resource_pairs = [
                (
                    resource_type,
                    resource_id,
                )
            ]

        depth_map = {
            (
                str(item.get("resource_type") or "").strip().lower(),
                str(item.get("resource_id") or "").strip(),
            ): int(item.get("depth") or 0)
            for item in resource_chain
        }

        effect_rows = await AccessDecisionRepository.list_active_acl_effects_for_resources(
            subject_bindings=subject_bindings,
            resource_pairs=resource_pairs,
            action_code=action_code,
            now=now,
        )

        if not effect_rows:
            return None

        def sort_key(row: dict[str, Any]) -> tuple[int, int]:
            pair = (
                str(row.get("resource_type") or "").strip().lower(),
                str(row.get("resource_id") or "").strip(),
            )
            return (
                depth_map.get(pair, 99),
                int(row.get("id") or 0),
            )

        sorted_rows = sorted(effect_rows, key=sort_key)

        deny_rows = [
            row
            for row in sorted_rows
            if str(row.get("effect") or "").upper() == PERMISSION_EFFECT_DENY
        ]

        if deny_rows:
            item = deny_rows[0]
            pair = (
                str(item.get("resource_type") or "").strip().lower(),
                str(item.get("resource_id") or "").strip(),
            )
            depth = depth_map.get(pair, 0)

            return {
                "effect": PERMISSION_EFFECT_DENY,
                "matched_acl_id": item.get("id"),
                "matched_acl_depth": depth,
                "matched_resource_type": pair[0],
                "matched_resource_id": pair[1],
                "data_scope": item.get("data_scope"),
            }

        allow_rows = [
            row
            for row in sorted_rows
            if str(row.get("effect") or "").upper() == PERMISSION_EFFECT_ALLOW
        ]

        if allow_rows:
            item = allow_rows[0]
            pair = (
                str(item.get("resource_type") or "").strip().lower(),
                str(item.get("resource_id") or "").strip(),
            )
            depth = depth_map.get(pair, 0)

            return {
                "effect": PERMISSION_EFFECT_ALLOW,
                "matched_acl_id": item.get("id"),
                "matched_acl_depth": depth,
                "matched_resource_type": pair[0],
                "matched_resource_id": pair[1],
                "data_scope": item.get("data_scope"),
            }

        return None

    @classmethod
    def resolve_permission_code(cls, *, request_data: dict[str, Any], resource_type: str, action_code: str) -> str | None:
        explicit_permission_code = str(request_data.get("permission_code") or "").strip()

        if explicit_permission_code:
            return explicit_permission_code

        normalized_resource = resource_type.replace(".", ":")
        if ":" not in normalized_resource:
            return None

        return f"{normalized_resource}:{action_code}"

    @classmethod
    def normalize_access_mode(cls, value: Any) -> str:
        access_mode = str(value or RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW).strip().upper()

        if access_mode in (
                "",
                RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW,
        ):
            return RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW

        if access_mode == RESOURCE_ACCESS_MODE_ACL_REQUIRED:
            return RESOURCE_ACCESS_MODE_ACL_REQUIRED

        raise IamRuntimeRequestInvalidError(
            "resource access_mode is invalid.",
            details={
                "access_mode": value,
            },
        )

    @classmethod
    def normalize_resource_type(cls, value: Any) -> str:
        resource_type = cls.normalize_required_text(value, "resource_type").lower()

        if " " in resource_type:
            raise IamRuntimeRequestInvalidError(
                "resource_type is invalid.",
                details={
                    "resource_type": resource_type,
                },
            )

        return resource_type

    @classmethod
    def normalize_action_code(cls, value: Any) -> str:
        action_code = cls.normalize_required_text(value, "action_code").lower()

        if cls.ACTION_CODE_PATTERN.fullmatch(action_code) is None:
            raise IamRuntimeRequestInvalidError(
                "action_code is invalid.",
                details={
                    "action_code": action_code,
                    "pattern": cls.ACTION_CODE_PATTERN.pattern,
                },
            )

        return action_code

    @staticmethod
    def normalize_required_text(value: Any, field_name: str) -> str:
        text = str(value or "").strip()

        if not text:
            raise IamRuntimeRequestInvalidError(
                f"{field_name} is required.",
                details={
                    "field": field_name,
                },
            )

        return text

    @staticmethod
    def ensure_dict(data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise IamRuntimeRequestInvalidError(
                "Request payload must be an object.",
            )

        return dict(data)

    @classmethod
    def build_authorization_failed_decision(
            cls,
            *,
            resource_type: str,
            resource_id: str,
            action_code: str,
            permission_code: str | None,
            retry_count: int,
            error: Exception,
            trace_id: str | None,
    ) -> dict[str, Any]:
        decision_chain: list[dict[str, Any]] = []

        cls.append_chain(
            decision_chain,
            source="system",
            effect=cls.EFFECT_DENY,
            reason="AUTHORIZATION_CHECK_FAILED",
            retry_count=max(retry_count, 0),
        )

        return cls.build_decision(
            allowed=False,
            reason="AUTHORIZATION_CHECK_FAILED",
            matched_source=cls.MATCHED_SOURCE_NONE,
            resource_type=resource_type,
            resource_id=resource_id,
            action_code=action_code,
            permission_code=permission_code,
            access_mode=None,
            filters={},
            matched_rbac_permission_code=permission_code,
            hit_details={
                "error": error.__class__.__name__,
                "retry_count": max(retry_count, 0),
                "resource": {
                    "access_mode": None,
                },
            },
            decision_chain=decision_chain,
            trace_id=trace_id,
        )

    @classmethod
    def build_decision(
            cls,
            *,
            allowed: bool,
            reason: str,
            matched_source: str,
            resource_type: str,
            resource_id: str,
            action_code: str,
            permission_code: str | None,
            access_mode: str | None = None,
            filters: dict[str, Any] | None = None,
            matched_acl_id: int | None = None,
            matched_policy_id: int | None = None,
            matched_rule_id: int | None = None,
            matched_rbac_permission_code: str | None = None,
            hit_details: dict[str, Any] | None = None,
            decision_chain: list[dict[str, Any]] | None = None,
            trace_id: str | None = None,
    ) -> dict[str, Any]:
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
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action_code": action_code,
            "permission_code": permission_code,
            "filters": filters or {},
            "hit_details": hit_details or {},
            "decision_chain": decision_chain or [],
            "trace_id": trace_id,
        }

    @staticmethod
    def append_chain(chain: list[dict[str, Any]], *, source: str, effect: str, reason: str, **extra: Any) -> None:
        item = {
            "source": source,
            "effect": effect,
            "reason": reason,
        }

        for key, value in extra.items():
            if value in (
                    None,
                    "",
                    [],
                    {},
            ):
                continue

            item[key] = value

        chain.append(item)
