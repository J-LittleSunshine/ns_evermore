# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.services import DecisionAuditService
from ns_backend.iam.views.management_views import IamManagementViewSet

if TYPE_CHECKING:
    pass


class DecisionAuditViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.decision_audit.api"
    service_class = DecisionAuditService

    allowed_actions = {
        "list",
    }

    required_permissions = {
        "list": ("iam:audit:decision:read",),
    }
