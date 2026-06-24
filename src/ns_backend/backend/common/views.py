# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass
from typing import (
    Any,
    ClassVar,
    TYPE_CHECKING,
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


@dataclass(slots=True, kw_only=True)
class NsRequestContext:
    request_id: str
    method: str
    path: str
    action: str | None
    started_at: float
    client_ip: str | None = None
    user_agent: str | None = None
    current_user: Any | None = None


class NsAPIView(ViewSet):
    logger_name: str = "ns_backend.api"
    wrap_response: bool = True
    request_id_header_name: str = "X-Request-ID"
    enable_access_log: bool = True

    success_status_by_action: ClassVar[dict[str, int]] = {}
    error_status_by_code: ClassVar[dict[str, int]] = {}

    def initial(self, request: "Request", *args: Any, **kwargs: Any) -> None:
        self.request_id = self._get_or_create_request_id(request)  # noqa
        self.request_started_at = time.monotonic()  # noqa
        self.logger = get_ns_logger(self.logger_name)  # noqa
        self.api_context = self.build_request_context(request)  # noqa

        super().initial(request, *args, **kwargs)

        self.pre_action(request, *args, **kwargs)
        self.check_action_access(request, *args, **kwargs)

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
                    "view": self.__class__.__name__,
                    "action": getattr(self, "action", None),
                }
            )
            return error_response(exc, status=self.get_error_status(exc), request_id=request_id)

        if isinstance(exc, APIException):
            error = NsRuntimeError(str(exc.detail), code="NS_API_ERROR", numeric_code=100300,
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
                    "view": self.__class__.__name__,
                    "action": getattr(self, "action", None),
                },
            )
            return error_response(error, status=getattr(exc, "status_code", 400), request_id=request_id, )

        logger.error("api unexpected error", exc_info=True,
            extra={
                "request_id": request_id,
                "view": self.__class__.__name__,
                "action": getattr(self, "action", None),
            },
        )
        return internal_error_response(request_id=request_id)

    def finalize_response(self, request: "Request", response: Any, *args: Any, **kwargs: Any) -> Response:
        request_id = getattr(self, "request_id", None)

        if self.wrap_response and not isinstance(response, Response):
            response = success_response(
                data=response,
                status=self.get_success_status(),
                request_id=request_id,
            )

        response = super().finalize_response(request, response, *args, **kwargs)

        if request_id:
            response[self.request_id_header_name] = request_id

        response = self.safe_post_action(
            request=request,
            response=response,
            args=args,
            kwargs=kwargs,
        )

        self._log_response(response)

        return response

    def build_request_context(self, request: "Request") -> NsRequestContext:
        return NsRequestContext(
            request_id=getattr(self, "request_id", self._get_or_create_request_id(request)),
            method=str(getattr(request, "method", "") or "").upper(),
            path=str(getattr(request, "path", "") or ""),
            action=getattr(self, "action", None),
            started_at=getattr(self, "request_started_at", time.monotonic()),
            client_ip=self.get_client_ip(request),
            user_agent=self.get_user_agent(request),
        )

    def pre_action(self, request: "Request", *args: Any, **kwargs: Any) -> None:
        return None

    def check_action_access(self, request: "Request", *args: Any, **kwargs: Any) -> None:
        return None

    def post_action(self, request: "Request", response: Response, *args: Any, **kwargs: Any) -> Response | None:
        return None

    def safe_post_action(self, *, request: "Request", response: Response, args: tuple[Any, ...], kwargs: dict[str, Any]) -> Response:
        logger = getattr(self, "logger", get_ns_logger(self.logger_name))

        try:
            next_response = self.post_action(
                request,
                response,
                *args,
                **kwargs,
            )
        except Exception:  # noqa
            logger.error("api post_action failed", exc_info=True,
                extra={
                    "request_id": getattr(self, "request_id", None),
                    "view": self.__class__.__name__,
                    "action": getattr(self, "action", None),
                },
            )
            return response

        return next_response if isinstance(next_response, Response) else response

    def get_success_status(self) -> int:
        action_name = getattr(self, "action", None)

        if not action_name:
            return 200

        return self.success_status_by_action.get(action_name, 200)

    def get_error_status(self, error: NsEvermoreError) -> int:
        return self.error_status_by_code.get(error.code, 400)

    @classmethod
    def get_action_success_status(cls, action_name: str) -> int:
        return cls.success_status_by_action.get(action_name, 200)

    @staticmethod
    def get_request_data(request: "Request") -> dict[str, Any]:
        data = getattr(request, "data", None)

        if isinstance(data, dict):
            return dict(data)

        return {}

    @staticmethod
    def get_client_ip(request: "Request") -> str | None:
        remote_addr = getattr(request, "META", {}).get("REMOTE_ADDR")

        if not remote_addr:
            return None

        return str(remote_addr)[:64]

    @staticmethod
    def get_user_agent(request: "Request") -> str | None:
        user_agent = str(request.headers.get("User-Agent", "") or "").strip()
        return user_agent[:512] or None

    def set_current_user(self, user: Any | None) -> None:
        context = getattr(self, "api_context", None)
        if context is not None:
            context.current_user = user

    @staticmethod
    def _get_or_create_request_id(request: "Request") -> str:
        request_id = request.headers.get("X-Request-ID")

        if request_id:
            return str(request_id)[:128]

        return uuid.uuid4().hex

    def _log_response(self, response: Response) -> None:
        if not self.enable_access_log:
            return

        logger = getattr(self, "logger", get_ns_logger(self.logger_name))
        context = getattr(self, "api_context", None)
        started_at = getattr(self, "request_started_at", None)

        duration_ms: float | None = None
        if started_at is not None:
            duration_ms = round((time.monotonic() - started_at) * 1000, 2)

        logger.info("api response",
            extra={
                "request_id": getattr(context, "request_id", getattr(self, "request_id", None)),
                "method": getattr(context, "method", None),
                "path": getattr(context, "path", None),
                "client_ip": getattr(context, "client_ip", None),
                "action": getattr(context, "action", getattr(self, "action", None)),
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )


class NsViewSet(NsAPIView):
    allowed_actions: ClassVar[set[str] | None] = None

    @classmethod
    def as_view(cls, actions: dict[str, str] | None = None, **initkwargs: Any) -> "Callable[..., Any]":
        if not actions:
            raise NsValidationError("ViewSet actions must be declared.",
                details={
                    "view_set": cls.__name__,
                },
            )

        normalized_actions: dict[str, str] = {}

        for method_name, action_name in actions.items():
            normalized_method_name = cls.validate_http_method_name(method_name)
            normalized_action_name = cls.validate_action_definition(action_name)
            normalized_actions[normalized_method_name] = normalized_action_name

        return super().as_view(actions=normalized_actions, **initkwargs)

    @classmethod
    def validate_action_definition(cls, action_name: str) -> str:
        normalized_action_name = cls.validate_action_name(action_name)

        if cls.allowed_actions is not None and normalized_action_name not in cls.allowed_actions:
            raise NsValidationError("Action is not allowed.",
                details={
                    "action": normalized_action_name,
                    "allowed_actions": sorted(cls.allowed_actions),
                    "view_set": cls.__name__,
                },
            )

        handler = getattr(cls, normalized_action_name, None)
        if handler is None or not callable(handler):
            raise NsValidationError("Action handler does not exist.",
                details={
                    "action": normalized_action_name,
                    "view_set": cls.__name__,
                },
            )

        return normalized_action_name

    @staticmethod
    def validate_action_name(action_name: str) -> str:
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

        return normalized

    @staticmethod
    def validate_http_method_name(method_name: str) -> str:
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

        return normalized
