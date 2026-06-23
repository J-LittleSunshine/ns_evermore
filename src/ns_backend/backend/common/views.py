# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import time
import uuid
from typing import (
    Any,
    ClassVar,
    TYPE_CHECKING
)

from adrf.viewsets import ViewSet
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from backend.common.responses import (
    error_response,
    internal_error_response,
    success_response,
)
from ns_common import (
    NsEvermoreError,
    NsRuntimeError,
    NsValidationError,
    get_ns_logger,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from rest_framework.request import Request

_ACTION_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class NsAPIView(ViewSet):
    logger_name: str = "ns_backend.api"
    wrap_response: bool = True

    def initial(self, request: "Request", *args: Any, **kwargs: Any) -> None:
        self.request_id = self._get_or_create_request_id(request)  # noqa
        self.request_started_at = time.monotonic()  # noqa
        self.logger = get_ns_logger(self.logger_name)  # noqa

        super().initial(request, *args, **kwargs)

    async def dispatch(self, request: "Request", *args: Any, **kwargs: Any) -> Response:
        try:
            return await super().dispatch(request, *args, **kwargs)  # noqa
        except Exception as exc:  # noqa
            response = self.handle_exception(exc)

            return self.finalize_response(request, response, *args, **kwargs)

    def handle_exception(self, exc: Exception) -> Response:
        request_id = getattr(self, "request_id", None)
        logger = getattr(self, "logger", get_ns_logger(self.logger_name))

        if isinstance(exc, NsEvermoreError):
            logger.warning("api known error",
                extra={
                    "request_id": request_id,
                    "error": exc.code,
                    "numeric_code": exc.numeric_code,
                    "details": exc.details,
                },
            )
            return error_response(exc, status=400, request_id=request_id)

        if isinstance(exc, APIException):
            error = NsRuntimeError(
                str(exc.detail),
                code="NS_API_ERROR",
                numeric_code=100300,
                details={
                    "drf_code": getattr(exc, "default_code", None),
                    "status_code": getattr(exc, "status_code", None),
                },
            )
            logger.warning("api framework error",
                extra={
                    "request_id": request_id,
                    "error": error.code,
                    "numeric_code": error.numeric_code,
                    "details": error.details,
                },
            )
            return error_response(error, status=getattr(exc, "status_code", 400), request_id=request_id)

        logger.error("api unexpected error",
            exc_info=exc,
            extra={
                "request_id": request_id,
                "view": self.__class__.__name__,
            },
        )
        return internal_error_response(request_id=request_id)

    def finalize_response(self, request: "Request", response: Any, *args: Any, **kwargs: Any) -> Response:
        request_id = getattr(self, "request_id", None)

        if self.wrap_response and not isinstance(response, Response):
            response = success_response(data=response, request_id=request_id)

        response = super().finalize_response(request, response, *args, **kwargs)

        self._log_response(response)

        return response

    @staticmethod
    def _get_or_create_request_id(request: "Request") -> str:
        request_id = request.headers.get("X-Request-ID")

        if request_id:
            return request_id

        return uuid.uuid4().hex

    def _log_response(self, response: Response) -> None:
        logger = getattr(self, "logger", get_ns_logger(self.logger_name))
        request_id = getattr(self, "request_id", None)
        started_at = getattr(self, "request_started_at", None)
        action_name = getattr(self, "action", None)

        duration_ms: float | None = None
        if started_at is not None:
            duration_ms = round((time.monotonic() - started_at) * 1000, 2)

        logger.info("api response",
            extra={
                "request_id": request_id,
                "action": action_name,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )


class NsViewSet(NsAPIView):
    allowed_actions: ClassVar[set[str] | None] = None
    http_method_name: ClassVar[str] = "post"

    @classmethod
    def as_view(cls, actions: dict[str, str] | None = None, **initkwargs: Any) -> "Callable[..., Any]":
        if not actions:
            raise NsValidationError("ViewSet actions must be declared.",
                details={
                    "view_set": cls.__name__,
                },
            )

        for method_name, action_name in actions.items():
            cls.validate_http_method_name(method_name)
            cls.validate_action_definition(action_name)

        return super().as_view(actions=actions, **initkwargs)

    @classmethod
    def validate_action_definition(cls, action_name: str) -> None:
        cls.validate_action_name(action_name)

        if cls.allowed_actions is not None and action_name not in cls.allowed_actions:
            raise NsValidationError("Action is not allowed.",
                details={
                    "action": action_name,
                    "allowed_actions": sorted(cls.allowed_actions),
                    "view_set": cls.__name__,
                },
            )

        handler = getattr(cls, action_name, None)
        if handler is None or not callable(handler):
            raise NsValidationError("Action handler does not exist.",
                details={
                    "action": action_name,
                    "view_set": cls.__name__,
                },
            )

    @staticmethod
    def validate_action_name(action_name: str) -> None:
        if not isinstance(action_name, str) or not action_name.strip():
            raise NsValidationError("Action name must not be empty.",
                details={
                    "action": action_name,
                },
            )

        normalized = action_name.strip()

        if not _ACTION_NAME_PATTERN.fullmatch(normalized):
            raise NsValidationError("Invalid action name.",
                details={
                    "action": action_name,
                },
            )

        if "__" in normalized:
            raise NsValidationError("Invalid action name.",
                details={
                    "action": action_name,
                },
            )

    @staticmethod
    def validate_http_method_name(method_name: str) -> None:
        normalized = str(method_name).strip().lower()

        allowed_methods = {
            "get",
            "post",
            "put",
            "patch",
            "delete",
        }
        if normalized not in allowed_methods:
            raise NsValidationError("Invalid HTTP method name.",
                details={
                    "method": method_name,
                },
            )
