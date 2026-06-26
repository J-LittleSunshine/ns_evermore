# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    TYPE_CHECKING,
)

from ns_backend.iam.errors import IamRuntimeRequestInvalidError
from ns_backend.iam.services.resource_access_filter import ResourceAccessFilterService

if TYPE_CHECKING:
    pass


class KnowledgeAuthorizationFilter:
    DEFAULT_RESOURCE_TYPE = "knowledge.chunk"
    DEFAULT_ACTION_CODE = "read"
    DEFAULT_RESOURCE_ID_FIELD = "resource_id"

    @staticmethod
    def normalize_candidates(candidates: Any) -> list[dict[str, Any]]:
        if not isinstance(candidates, list):
            raise IamRuntimeRequestInvalidError(
                "candidates must be a list.",
                details={
                    "field": "candidates",
                },
            )

        normalized_candidates: list[dict[str, Any]] = []
        for index, item in enumerate(candidates):
            if not isinstance(item, dict):
                raise IamRuntimeRequestInvalidError(
                    "candidate item must be an object.",
                    details={
                        "field": "candidates",
                        "index": index,
                        "actual_type": type(item).__name__,
                    },
                )

            normalized_candidates.append(dict(item))

        return normalized_candidates

    @classmethod
    def read_candidate_field(cls, *, candidate: dict[str, Any], field_name: str) -> tuple[bool, Any]:
        if field_name in candidate:
            return True, candidate.get(field_name)

        metadata = candidate.get("metadata")
        if isinstance(metadata, dict) and field_name in metadata:
            return True, metadata.get(field_name)

        return False, None

    @classmethod
    def matches_data_scope_filters(cls, *, candidate: dict[str, Any], data_scope_filters: Any) -> tuple[bool, str | None]:
        if data_scope_filters in (
                None,
                {},
        ):
            return True, None

        if not isinstance(data_scope_filters, dict):
            return False, "INVALID_DATA_SCOPE_FILTERS"

        denied_reason = data_scope_filters.get("_denied_reason")
        if denied_reason:
            return False, str(denied_reason)

        for filter_key, expected_value in data_scope_filters.items():
            filter_key_text = str(filter_key or "").strip()

            if not filter_key_text:
                return False, "INVALID_FILTER_KEY"

            if filter_key_text.startswith("_"):
                return False, f"UNSUPPORTED_FILTER_KEY:{filter_key_text}"

            if filter_key_text == "policy_data_scope":
                continue

            if filter_key_text.endswith("__in"):
                field_name = filter_key_text[:-4]
                field_exists, candidate_value = cls.read_candidate_field(
                    candidate=candidate,
                    field_name=field_name,
                )

                if not field_exists:
                    return False, f"MISSING_FILTER_FIELD:{field_name}"

                if not isinstance(expected_value, (list, tuple, set)):
                    return False, f"INVALID_FILTER_EXPECTED:{filter_key_text}"

                if candidate_value not in expected_value:
                    return False, f"FILTER_NOT_MATCHED:{filter_key_text}"

                continue

            field_exists, candidate_value = cls.read_candidate_field(
                candidate=candidate,
                field_name=filter_key_text,
            )

            if not field_exists:
                return False, f"MISSING_FILTER_FIELD:{filter_key_text}"

            if candidate_value != expected_value:
                return False, f"FILTER_NOT_MATCHED:{filter_key_text}"

        return True, None

    @classmethod
    def build_decision_items_from_retrieval_filter(cls, *, candidates: list[dict[str, Any]], retrieval_filter: dict[str, Any], resource_id_field: str) -> list[dict[str, Any]]:
        allowed_ids = {
            str(item)
            for item in retrieval_filter.get("allowed_resource_ids", [])
            if str(item).strip()
        }
        denied_ids = {
            str(item)
            for item in retrieval_filter.get("denied_resource_ids", [])
            if str(item).strip()
        }

        filters = retrieval_filter.get("filters")
        if not isinstance(filters, dict):
            filters = {}

        deny_all = bool(filters.get("deny_all", False))
        allow_all = bool(filters.get("allow_all", False))
        default_allow = bool(filters.get("default_allow", False))

        data_scope_filters = filters.get("data_scope")
        if not isinstance(data_scope_filters, dict):
            data_scope_filters = {}

        decision_items: list[dict[str, Any]] = []

        for index, candidate in enumerate(candidates):
            exists, resource_id_value = cls.read_candidate_field(
                candidate=candidate,
                field_name=resource_id_field,
            )

            if not exists or resource_id_value in (
                    None,
                    "",
            ):
                raise IamRuntimeRequestInvalidError(
                    "candidate missing resource id field.",
                    details={
                        "index": index,
                        "resource_id_field": resource_id_field,
                    },
                )

            resource_id = str(resource_id_value)
            allowed = False
            reason = "NO_MATCHED_RULE"

            if resource_id in denied_ids:
                allowed = False
                reason = "ACL_DENY"
            elif allow_all:
                allowed = True
                reason = "ALLOW_ALL"
            elif resource_id in allowed_ids:
                allowed = True
                reason = "ACL_ALLOW"
            elif deny_all:
                allowed = False
                reason = "RETRIEVAL_FILTER_DENY"
            elif default_allow:
                allowed = True
                reason = "RBAC_ALLOW"

            if allowed:
                matches_scope, scope_reason = cls.matches_data_scope_filters(
                    candidate=candidate,
                    data_scope_filters=data_scope_filters,
                )

                if not matches_scope:
                    allowed = False
                    reason = scope_reason or "DATA_SCOPE_FILTER_DENY"

            decision_items.append(
                {
                    "allowed": allowed,
                    "effect": "allow" if allowed else "deny",
                    "reason": reason,
                    "matched_source": "retrieval_filter",
                    "resource_id": resource_id,
                    "resource_id_field": resource_id_field,
                    "filters": data_scope_filters if allowed else {},
                    "decision_chain": [
                        {
                            "source": "retrieval_filter",
                            "effect": "allow" if allowed else "deny",
                            "reason": reason,
                        }
                    ],
                }
            )

        return decision_items

    @classmethod
    def split_candidates_by_decision(cls, *, candidates: list[dict[str, Any]], decision_items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        allowed_items: list[dict[str, Any]] = []
        denied_items: list[dict[str, Any]] = []

        for candidate, decision in zip(candidates, decision_items):
            if bool(decision.get("allowed", False)):
                allowed_items.append(candidate)
                continue

            denied_items.append(
                {
                    "candidate": candidate,
                    "decision": decision,
                    "denied_reason": str(decision.get("reason") or "PERMISSION_DENIED"),
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
            resource_id_field: str = DEFAULT_RESOURCE_ID_FIELD,
            permission_code: str | None = None,
            field_map: dict[str, Any] | None = None,
            trace_id: str | None = None,
    ) -> dict[str, Any]:
        normalized_candidates = cls.normalize_candidates(candidates)

        if not normalized_candidates:
            return {
                "allowed_items": [],
                "denied_items": [],
                "decision_items": [],
                "retrieval_filter": None,
                "trace_id": trace_id,
            }

        retrieval_filter = await ResourceAccessFilterService.resolve_retrieval_filter(
            user=user,
            resource_type=resource_type,
            action_code=action_code,
            permission_code=permission_code,
            field_map=field_map,
        )

        decision_items = cls.build_decision_items_from_retrieval_filter(
            candidates=normalized_candidates,
            retrieval_filter=retrieval_filter,
            resource_id_field=str(resource_id_field or cls.DEFAULT_RESOURCE_ID_FIELD).strip() or cls.DEFAULT_RESOURCE_ID_FIELD,
        )

        allowed_items, denied_items = cls.split_candidates_by_decision(
            candidates=normalized_candidates,
            decision_items=decision_items,
        )

        return {
            "allowed_items": allowed_items,
            "denied_items": denied_items,
            "decision_items": decision_items,
            "retrieval_filter": retrieval_filter,
            "trace_id": trace_id,
        }
