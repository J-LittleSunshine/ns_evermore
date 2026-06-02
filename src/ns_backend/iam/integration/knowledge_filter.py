# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.services.authorize import AuthorizeService
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


class KnowledgeAuthorizationFilter:
    """Filter Knowledge candidates through IAM before retriever execution."""

    DEFAULT_RESOURCE_TYPE = "knowledge.chunk"
    DEFAULT_ACTION_CODE = "read"

    @staticmethod
    def _normalize_candidates(candidates: Any) -> list[dict[str, Any]]:
        """Validate and normalize candidate payload list."""
        if not isinstance(candidates, list):
            raise BusinessError("candidates must be a list", NsErrorCode.INVALID_VALUE)

        normalized_candidates: list[dict[str, Any]] = []
        for item in candidates:
            if not isinstance(item, dict):
                raise BusinessError("candidate item must be an object", NsErrorCode.INVALID_VALUE)
            normalized_candidates.append(item)

        return normalized_candidates

    @classmethod
    def _read_candidate_field(cls, *, candidate: dict[str, Any], field_name: str) -> tuple[bool, Any]:
        """Read a candidate field from top-level payload or metadata."""
        if field_name in candidate:
            return True, candidate.get(field_name)

        metadata = candidate.get("metadata")
        if isinstance(metadata, dict) and field_name in metadata:
            return True, metadata.get(field_name)

        return False, None

    @classmethod
    def _matches_decision_filters(cls, *, candidate: dict[str, Any], decision_filters: Any) -> tuple[bool, str | None]:
        """Check whether one candidate satisfies IAM decision filters."""
        if decision_filters in (None, {}):
            return True, None

        if not isinstance(decision_filters, dict):
            return False, "INVALID_FILTERS"

        denied_reason = decision_filters.get("_denied_reason")
        if denied_reason:
            return False, str(denied_reason)

        for filter_key, expected_value in decision_filters.items():
            if str(filter_key).startswith("_"):
                return False, f"UNSUPPORTED_FILTER_KEY:{filter_key}"

            if str(filter_key) == "policy_data_scope":
                continue

            if str(filter_key).endswith("__in"):
                field_name = str(filter_key)[:-4]
                field_exists, candidate_value = cls._read_candidate_field(candidate=candidate, field_name=field_name)
                if not field_exists:
                    return False, f"MISSING_FILTER_FIELD:{field_name}"

                if not isinstance(expected_value, (list, tuple, set)):
                    return False, f"INVALID_FILTER_EXPECTED:{filter_key}"

                if candidate_value not in expected_value:
                    return False, f"FILTER_NOT_MATCHED:{filter_key}"
                continue

            field_exists, candidate_value = cls._read_candidate_field(candidate=candidate, field_name=str(filter_key))
            if not field_exists:
                return False, f"MISSING_FILTER_FIELD:{filter_key}"

            if candidate_value != expected_value:
                return False, f"FILTER_NOT_MATCHED:{filter_key}"

        return True, None

    @classmethod
    def _build_authorize_items(
        cls,
        *,
        candidates: list[dict[str, Any]],
        resource_type: str,
        action_code: str,
        resource_id_field: str,
        permission_code: str | None,
    ) -> list[dict[str, Any]]:
        """Build authorize batch items from candidate payloads."""
        items: list[dict[str, Any]] = []
        for candidate in candidates:
            field_exists, resource_id = cls._read_candidate_field(candidate=candidate, field_name=resource_id_field)
            if not field_exists or resource_id in (None, ""):
                raise BusinessError(f"candidate missing field: {resource_id_field}", NsErrorCode.INVALID_VALUE)

            items.append(
                {
                    "resource_type": resource_type,
                    "resource_id": str(resource_id),
                    "action_code": action_code,
                    "permission_code": permission_code,
                }
            )

        return items

    @staticmethod
    def _validate_decision_items(*, decision_items: list[Any], candidate_count: int) -> None:
        """Validate authorize batch decisions against candidate count and shape."""
        if len(decision_items) != candidate_count:
            raise BusinessError("authorize decision count mismatch", NsErrorCode.PERMISSION_DENIED)

        for decision_item in decision_items:
            if not isinstance(decision_item, dict):
                raise BusinessError("authorize decision item is invalid", NsErrorCode.PERMISSION_DENIED)

    @classmethod
    def _split_candidates_by_decision(
        cls,
        *,
        candidates: list[dict[str, Any]],
        decision_items: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Split candidates into allowed and denied lists from decision results."""
        allowed_items: list[dict[str, Any]] = []
        denied_items: list[dict[str, Any]] = []

        for candidate, decision in zip(candidates, decision_items):
            decision_allowed = bool(decision.get("allowed", False))
            matches_filters, filter_reason = cls._matches_decision_filters(
                candidate=candidate,
                decision_filters=decision.get("filters"),
            )

            if decision_allowed and matches_filters:
                allowed_items.append(candidate)
                continue

            denied_reason = filter_reason
            if denied_reason is None and not decision_allowed:
                denied_reason = str(decision.get("reason") or "PERMISSION_DENIED")

            denied_items.append(
                {
                    "candidate": candidate,
                    "decision": decision,
                    "denied_reason": denied_reason,
                }
            )

        return allowed_items, denied_items

    @classmethod
    async def filter_candidates(
        cls,
        *,
        user: Any,
        candidates: list[dict[str, Any]],
        resource_type: str = DEFAULT_RESOURCE_TYPE,
        action_code: str = DEFAULT_ACTION_CODE,
        resource_id_field: str = "resource_id",
        permission_code: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Filter candidate chunks/documents using IAM batch authorization results."""
        normalized_candidates = cls._normalize_candidates(candidates)
        if not normalized_candidates:
            return {
                "allowed_items": [],
                "denied_items": [],
                "decision_items": [],
            }

        items = cls._build_authorize_items(
            candidates=normalized_candidates,
            resource_type=resource_type,
            action_code=action_code,
            resource_id_field=resource_id_field,
            permission_code=permission_code,
        )

        batch_result = await AuthorizeService.batch_check(
            user=user,
            data={"items": items},
            trace_id=trace_id,
        )
        decision_items: list[dict[str, Any]] = list(batch_result.get("items", []))
        cls._validate_decision_items(decision_items=decision_items, candidate_count=len(normalized_candidates))
        allowed_items, denied_items = cls._split_candidates_by_decision(
            candidates=normalized_candidates,
            decision_items=decision_items,
        )

        return {
            "allowed_items": allowed_items,
            "denied_items": denied_items,
            "decision_items": decision_items,
        }

