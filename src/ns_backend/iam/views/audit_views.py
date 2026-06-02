# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.services import DecisionAuditService
from ns_backend.iam.views import IamRequestViewSet

if TYPE_CHECKING:
    pass


class DecisionAuditViewSet(IamRequestViewSet):
    """IAM authorization decision audit query API viewset."""

    audit_resource_type = "iam_audit_log"

    async def list_decision_audits(self, request, *args, **kwargs):
        result = await DecisionAuditService.list_logs(data=request.data)
        return self.success_response(result)

