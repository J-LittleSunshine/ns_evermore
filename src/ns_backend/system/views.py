# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    TYPE_CHECKING
)

from backend.common import NsViewSet
from ns_common import NsValidationError

if TYPE_CHECKING:
    from rest_framework.request import Request


class SystemViewSet(NsViewSet):
    logger_name = "ns_backend.system.api"

    allowed_actions = {
        "health_check",
        "raise_validation_error",
    }

    @staticmethod
    async def health_check(request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {
            "pong": True,
        }

    async def raise_validation_error(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        raise NsValidationError(
            "Validation error test.",
            details={
                "source": "system.raise_validation_error",
            },
        )
