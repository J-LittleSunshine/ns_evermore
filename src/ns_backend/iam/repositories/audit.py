# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db import IntegrityError

from ns_backend.backend.common import BaseRepository
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
        db_alias = BaseRepository.resolve_db_alias(model_class=IamOperationAudit)
        try:
            return await IamOperationAudit.objects.using(db_alias).acreate(**data)
        except IntegrityError as exc:
            raise BusinessError(f"Failed to create audit event: {exc}", NsErrorCode.AUDIT_CREATE_FAILED) from exc
