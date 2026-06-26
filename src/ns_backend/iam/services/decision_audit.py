# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    TYPE_CHECKING,
)

from django.conf import settings

from ns_backend.iam.errors import IamManagementRequestInvalidError
from ns_backend.iam.repositories import DecisionAuditRepository
from ns_common import get_ns_logger

if TYPE_CHECKING:
    pass

logger = get_ns_logger("ns_backend.iam.decision_audit")


class DecisionAuditService:
    RESULT_ALLOW = "ALLOW"
    RESULT_DENY = "DENY"

    SUBJECT_USER = "USER"

    allowed_filter_fields = {
        "id",
        "operator_id",
        "subject_type",
        "subject_id",
        "resource_type",
        "resource_id",
        "action_code",
        "result",
        "matched_acl_id",
        "matched_policy_id",
        "matched_rule_id",
        "matched_source",
        "trace_id",
    }

    @classmethod
    def is_enabled(cls) -> bool:
        return bool(getattr(settings, "IAM_DECISION_AUDIT_ENABLED", True))

    @classmethod
    def is_strict_mode_enabled(cls) -> bool:
        return bool(getattr(settings, "IAM_DECISION_AUDIT_STRICT_MODE", False))

    @classmethod
    async def record_from_decision_safe(cls, *, user: Any, decision: dict[str, Any], trace_id: str | None = None) -> None:
        if not cls.is_enabled():
            return

        try:
            await cls.record_from_decision(
                user=user,
                decision=decision,
                trace_id=trace_id,
            )
        except Exception as exc:  # noqa
            logger.error(
                "decision audit write failed",
                exc_info=True,
                extra={
                    "user_id": getattr(user, "id", None),
                    "resource_type": decision.get("resource_type"),
                    "resource_id": decision.get("resource_id"),
                    "action_code": decision.get("action_code"),
                    "exception_class": exc.__class__.__name__,
                },
            )

            if cls.is_strict_mode_enabled():
                raise

    @classmethod
    async def record_from_decision(cls, *, user: Any, decision: dict[str, Any], trace_id: str | None = None) -> dict[str, Any]:
        user_id = cls.normalize_positive_int(
            getattr(user, "id", None),
            "user.id",
        )

        result = cls.RESULT_ALLOW if bool(decision.get("allowed")) else cls.RESULT_DENY

        data = {
            "operator_id": user_id,
            "subject_type": cls.SUBJECT_USER,
            "subject_id": user_id,
            "resource_type": str(decision.get("resource_type") or "").strip()[:128],
            "resource_id": str(decision.get("resource_id") or "").strip()[:128],
            "action_code": str(decision.get("action_code") or "").strip()[:64],
            "result": result,
            "reason": cls.build_reason_with_chain(
                reason=str(decision.get("reason") or ""),
                decision_chain=decision.get("decision_chain"),
            ),
            "matched_acl_id": cls.normalize_optional_int(decision.get("matched_acl_id")),
            "matched_policy_id": cls.normalize_optional_int(decision.get("matched_policy_id")),
            "matched_rule_id": cls.normalize_optional_int(decision.get("matched_rule_id")),
            "matched_source": cls.normalize_optional_source(decision.get("matched_source")),
            "trace_id": cls.normalize_trace_id(trace_id or decision.get("trace_id")),
        }

        return await DecisionAuditRepository.create_log(
            data=data,
        )

    @classmethod
    async def list_items(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        """
        管理端查询 decision audit。

        注意：
        - 审计日志是平台级敏感数据。
        - 访问控制由 DecisionAuditViewSet.required_permissions 控制。
        - 不做 company 级租户过滤，因为 iam_audit_log 当前没有 company_id 字段。
        """
        request_data = cls.ensure_dict(data)

        page = cls.normalize_page(request_data.get("page", 1))
        page_size = cls.normalize_page_size(request_data.get("page_size", 20))
        filters = cls.build_filters(request_data)

        return await DecisionAuditRepository.list_logs(
            page=page,
            page_size=page_size,
            filters=filters,
        )

    @classmethod
    def build_filters(cls, data: dict[str, Any]) -> dict[str, Any]:
        filters: dict[str, Any] = {}

        raw_filters = data.get("filters")
        if isinstance(raw_filters, dict):
            for field, value in raw_filters.items():
                if field not in cls.allowed_filter_fields:
                    continue

                if value in (None, ""):
                    continue

                filters[field] = cls.normalize_filter_value(
                    field=field,
                    value=value,
                )

        direct_fields = (
            "subject_type",
            "subject_id",
            "resource_type",
            "resource_id",
            "action_code",
            "result",
            "matched_source",
            "trace_id",
        )

        for field in direct_fields:
            value = data.get(field)
            if value in (None, ""):
                continue

            filters[field] = cls.normalize_filter_value(
                field=field,
                value=value,
            )

        return filters

    @classmethod
    def normalize_filter_value(cls, *, field: str, value: Any) -> Any:
        if field in (
                "id",
                "operator_id",
                "subject_id",
                "matched_acl_id",
                "matched_policy_id",
                "matched_rule_id",
        ):
            return cls.normalize_positive_int(value, field)

        if field == "subject_type":
            return str(value or "").strip().upper()

        if field in (
                "resource_type",
                "action_code",
                "matched_source",
        ):
            return str(value or "").strip().lower()

        if field == "result":
            return cls.normalize_result(value)

        return str(value or "").strip()

    @staticmethod
    def normalize_result(value: Any) -> str:
        result = str(value or "").strip().upper()

        if result not in (
                DecisionAuditService.RESULT_ALLOW,
                DecisionAuditService.RESULT_DENY,
        ):
            raise IamManagementRequestInvalidError(
                "result is invalid.",
                details={
                    "result": value,
                    "allowed_values": [
                        DecisionAuditService.RESULT_ALLOW,
                        DecisionAuditService.RESULT_DENY,
                    ],
                },
            )

        return result

    @staticmethod
    def normalize_positive_int(value: Any, field_name: str) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise IamManagementRequestInvalidError(
                f"{field_name} is invalid.",
                details={
                    "field": field_name,
                    "value": value,
                },
            ) from exc

        if parsed <= 0:
            raise IamManagementRequestInvalidError(
                f"{field_name} is invalid.",
                details={
                    "field": field_name,
                    "value": value,
                },
            )

        return parsed

    @staticmethod
    def normalize_optional_int(value: Any) -> int | None:
        if value in (None, ""):
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def normalize_optional_source(value: Any) -> str | None:
        if value in (None, ""):
            return None

        return str(value).strip().lower()[:32] or None

    @staticmethod
    def normalize_trace_id(value: Any) -> str | None:
        if value in (None, ""):
            return None

        return str(value).strip()[:64] or None

    @staticmethod
    def build_reason_with_chain(*, reason: str, decision_chain: Any) -> str:
        base_reason = str(reason or "").strip()

        if not isinstance(decision_chain, list) or not decision_chain:
            return base_reason[:512]

        chain_parts: list[str] = []

        for item in decision_chain:
            if not isinstance(item, dict):
                continue

            source = str(item.get("source") or "none").strip().lower()
            effect = str(item.get("effect") or "none").strip().lower()
            item_reason = str(item.get("reason") or "").strip().upper()

            if item_reason:
                chain_parts.append(f"{source}:{effect}:{item_reason}")
            else:
                chain_parts.append(f"{source}:{effect}")

        if not chain_parts:
            return base_reason[:512]

        chain_text = " > ".join(chain_parts)
        merged = f"{base_reason} | chain={chain_text}" if base_reason else f"chain={chain_text}"

        return merged[:512]

    @staticmethod
    def normalize_page(value: Any) -> int:
        try:
            page = int(value)
        except (TypeError, ValueError):
            page = 1

        return max(page, 1)

    @staticmethod
    def normalize_page_size(value: Any) -> int:
        try:
            page_size = int(value)
        except (TypeError, ValueError):
            page_size = 20

        if page_size <= 0:
            return 20

        return min(page_size, 200)

    @staticmethod
    def ensure_dict(data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise IamManagementRequestInvalidError(
                "Request payload must be an object.",
            )

        return dict(data)
