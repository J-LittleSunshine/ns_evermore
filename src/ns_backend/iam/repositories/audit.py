# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.models import IamOperationAudit
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


class AuditRepository:
    """Repository for IAM operation audit persistence."""

    @staticmethod
    async def create_event(data: dict[str, Any]) -> IamOperationAudit:
        """Create one operation audit event."""
        try:
            return await IamOperationAudit.objects.acreate(**data)
        except Exception as exc:
            raise BusinessError(f"Failed to create audit event: {exc}", NsErrorCode.AUDIT_CREATE_FAILED) from exc

