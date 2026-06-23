# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    TYPE_CHECKING
)

from backend.common import NsViewSet

if TYPE_CHECKING:
    from rest_framework.request import Request


class IamViewSet(NsViewSet):
    logger_name = "ns_backend.iam.api"

    allowed_actions = {
        "health_check",
    }

    @staticmethod
    async def health_check(request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {
            "module": "iam",
            "healthy": True,
        }
