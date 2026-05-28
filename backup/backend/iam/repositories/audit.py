# -*- coding: utf-8 -*-
from __future__ import annotations

from django.db import IntegrityError

from iam.constants import IAM_DB_ALIAS
from ns_common.error_codes import NsErrorCode
from iam.models import IamOperationAudit
from ns_backend.exceptions import BusinessError


class AuditRepository:
    @staticmethod
    async def create_event(data: dict) -> IamOperationAudit:
        try:
            return await IamOperationAudit.objects.using(IAM_DB_ALIAS).acreate(**data)
        except IntegrityError as exc:
            raise BusinessError(f"Failed to create audit event: {exc}", NsErrorCode.AUDIT_CREATE_FAILED)


__all__ = ["AuditRepository"]

