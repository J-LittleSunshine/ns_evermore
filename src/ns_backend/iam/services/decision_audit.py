# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.conf import settings

from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.repositories import DecisionAuditRepository
from ns_common.error_codes import NsErrorCode
from ns_common.logging.logger import get_ns_logger

if TYPE_CHECKING:
    pass

IAM_LOGGER = get_ns_logger("iam", True)


class DecisionAuditService:
    """Write and query IAM authorization decision audit logs."""

    RESULT_ALLOW = "ALLOW"
    RESULT_DENY = "DENY"

    SUBJECT_TYPES = {
        "USER",
        "ROLE",
        "DEPARTMENT",
        "ORGANIZATION",
        "SUBSIDIARY",
    }

    STRICT_MODE_SETTING = "IAM_DECISION_AUDIT_STRICT_MODE"

    @classmethod
    def is_strict_mode_enabled(cls) -> bool:
        """Return whether strict decision-audit mode is enabled."""
        return bool(getattr(settings, cls.STRICT_MODE_SETTING, False))

    @staticmethod
    def _normalize_result(value: Any) -> str:
        """Normalize and validate one decision result value."""
        result = str(value or "").strip().upper()
        if result not in {DecisionAuditService.RESULT_ALLOW, DecisionAuditService.RESULT_DENY}:
            raise BusinessError("result is invalid", NsErrorCode.INVALID_VALUE)
        return result

    @staticmethod
    def _normalize_subject_type(value: Any) -> str:
        """Normalize and validate one decision subject type."""
        subject_type = str(value or "").strip().upper()
        if subject_type not in DecisionAuditService.SUBJECT_TYPES:
            raise BusinessError("subject_type is invalid", NsErrorCode.INVALID_VALUE)
        return subject_type

    @staticmethod
    def _normalize_positive_int(value: Any, field_name: str) -> int:
        """Normalize and validate one positive integer field."""
        try:
            parsed_value = int(value)
        except (TypeError, ValueError) as exc:
            raise BusinessError(f"{field_name} is invalid", NsErrorCode.INVALID_VALUE) from exc

        if parsed_value <= 0:
            raise BusinessError(f"{field_name} is invalid", NsErrorCode.INVALID_VALUE)

        return parsed_value

    @staticmethod
    def _normalize_optional_int(value: Any) -> int | None:
        """Normalize optional integer value."""
        if value in (None, ""):
            return None
        return int(value)

    @staticmethod
    def _normalize_optional_source(value: Any) -> str | None:
        """Normalize optional matched-source marker."""
        if value in (None, ""):
            return None
        return str(value).strip().lower()[:32] or None

    @classmethod
    def _build_reason_with_chain(cls, *, reason: str, decision_chain: Any) -> str:
        """Build reason text with compact decision chain for audit traceability."""
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

    @classmethod
    def _build_record_payload(
        cls,
        *,
        operator_id: int | None,
        subject_type: str,
        subject_id: int,
        resource_type: str,
        resource_id: str,
        action_code: str,
        result: str,
        reason: str,
        matched_acl_id: int | None,
        matched_policy_id: int | None,
        matched_rule_id: int | None,
        matched_source: str | None,
        decision_chain: list[dict[str, Any]] | None,
        trace_id: str | None,
    ) -> dict[str, Any]:
        """Build normalized audit-log payload for repository write."""
        return {
            "operator_id": operator_id,
            "subject_type": cls._normalize_subject_type(subject_type),
            "subject_id": cls._normalize_positive_int(subject_id, "subject_id"),
            "resource_type": str(resource_type or "").strip()[:128],
            "resource_id": str(resource_id or "").strip()[:128],
            "action_code": str(action_code or "").strip()[:64],
            "result": cls._normalize_result(result),
            "reason": cls._build_reason_with_chain(reason=reason, decision_chain=decision_chain),
            "matched_acl_id": cls._normalize_optional_int(matched_acl_id),
            "matched_policy_id": cls._normalize_optional_int(matched_policy_id),
            "matched_rule_id": cls._normalize_optional_int(matched_rule_id),
            "matched_source": cls._normalize_optional_source(matched_source),
            "trace_id": None if not trace_id else str(trace_id)[:64],
        }

    @staticmethod
    def _build_strict_mode_error_data(kwargs: dict[str, Any]) -> dict[str, Any]:
        """Build strict-mode error context payload."""
        return {
            "subject_type": kwargs.get("subject_type"),
            "subject_id": kwargs.get("subject_id"),
            "resource_type": kwargs.get("resource_type"),
            "resource_id": kwargs.get("resource_id"),
            "action_code": kwargs.get("action_code"),
        }

    @classmethod
    async def record_decision(
        cls,
        *,
        operator_id: int | None,
        subject_type: str,
        subject_id: int,
        resource_type: str,
        resource_id: str,
        action_code: str,
        result: str,
        reason: str,
        matched_acl_id: int | None = None,
        matched_policy_id: int | None = None,
        matched_rule_id: int | None = None,
        matched_source: str | None = None,
        decision_chain: list[dict[str, Any]] | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Record one authorization decision audit row."""
        return await DecisionAuditRepository.create_log(
            data=cls._build_record_payload(
                operator_id=operator_id,
                subject_type=subject_type,
                subject_id=subject_id,
                resource_type=resource_type,
                resource_id=resource_id,
                action_code=action_code,
                result=result,
                reason=reason,
                matched_acl_id=matched_acl_id,
                matched_policy_id=matched_policy_id,
                matched_rule_id=matched_rule_id,
                matched_source=matched_source,
                decision_chain=decision_chain,
                trace_id=trace_id,
            )
        )

    @classmethod
    async def record_decision_safe(cls, **kwargs) -> None:
        """Record one decision audit row with optional strict-mode failure."""
        try:
            await cls.record_decision(**kwargs)
        except Exception as exc:  # noqa
            IAM_LOGGER.error(
                "decision audit write failed | subject_type=%s subject_id=%s resource_type=%s resource_id=%s action_code=%s exception=%s",
                kwargs.get("subject_type"),
                kwargs.get("subject_id"),
                kwargs.get("resource_type"),
                kwargs.get("resource_id"),
                kwargs.get("action_code"),
                exc.__class__.__name__,
                exc_info=True,
            )

            if cls.is_strict_mode_enabled():
                raise BusinessError(
                    "authorization decision audit write failed",
                    NsErrorCode.AUDIT_CREATE_FAILED,
                    data=cls._build_strict_mode_error_data(kwargs),
                )

            return

    @classmethod
    async def list_logs(cls, *, data: dict[str, Any]) -> dict[str, Any]:
        """List decision audit rows by paging and optional filters."""
        if not isinstance(data, dict):
            raise BusinessError("request data must be an object", NsErrorCode.INVALID_VALUE)

        page = data.get("page", 1)
        page_size = data.get("page_size", 20)

        filters: dict[str, Any] = {}
        raw_filters = data.get("filters")
        if isinstance(raw_filters, dict):
            filters.update(raw_filters)

        if data.get("subject_type") not in (None, ""):
            filters["subject_type"] = cls._normalize_subject_type(data.get("subject_type"))

        if data.get("subject_id") not in (None, ""):
            filters["subject_id"] = cls._normalize_positive_int(data.get("subject_id"), "subject_id")

        if data.get("resource_type") not in (None, ""):
            filters["resource_type"] = str(data.get("resource_type")).strip().lower()

        if data.get("action_code") not in (None, ""):
            filters["action_code"] = str(data.get("action_code")).strip().lower()

        if data.get("result") not in (None, ""):
            filters["result"] = cls._normalize_result(data.get("result"))

        if data.get("matched_acl_id") not in (None, ""):
            filters["matched_acl_id"] = cls._normalize_positive_int(data.get("matched_acl_id"), "matched_acl_id")

        if data.get("matched_source") not in (None, ""):
            matched_source = cls._normalize_optional_source(data.get("matched_source"))
            if matched_source:
                filters["matched_source"] = matched_source

        return await DecisionAuditRepository.list_logs(page=page, page_size=page_size, filters=filters or None)

