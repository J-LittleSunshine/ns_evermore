# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ns_backend.backend.common import BaseRepository
from ns_backend.iam.models import IamAuditLog

if TYPE_CHECKING:
    pass


class DecisionAuditRepository:
    """Repository for IAM authorization decision audit records."""

    AUDIT_FIELDS: tuple[str, ...] = (
        "id",
        "operator_id",
        "subject_type",
        "subject_id",
        "resource_type",
        "resource_id",
        "action_code",
        "result",
        "reason",
        "matched_acl_id",
        "matched_policy_id",
        "matched_rule_id",
        "matched_source",
        "trace_id",
        "created_at",
    )

    @staticmethod
    async def create_log(*, data: dict[str, Any]) -> dict[str, Any]:
        """Create one decision audit row."""
        return await BaseRepository.create_item_with_audit(
            model_class=IamAuditLog,
            data=data,
            operator_id=data.get("operator_id"),
        )

    @classmethod
    async def list_logs(cls, *, page: int | str | None, page_size: int | str | None, filters: dict[str, Any] | None) -> dict[str, Any]:
        """List decision audit rows."""
        return await BaseRepository.list_items(
            model_class=IamAuditLog,
            fields=cls.AUDIT_FIELDS,
            page=page,
            page_size=page_size,
            filters=filters,
            order_by=(
                "-id",
            ),
        )
