# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from adrf.viewsets import ViewSet
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from ns_common.logging.logger import get_ns_logger
from ...backend.exceptions import BusinessError

if TYPE_CHECKING:
    pass

_REQUEST_LOGGER = get_ns_logger("backend", False)

class BaseRequestViewSet(ViewSet):
    @classmethod
    def as_view(cls, actions: dict[str, str] | None = None, **initkwargs: Any) -> APIView[GenericAPIView]:
        if not actions:
            raise NotImplementedError(f"{cls.__name__} must declare as_view(actions)")
        return super().as_view(actions=actions, **initkwargs)

    async def dispatch(self, request, *args, **kwargs) -> JsonResponse | Any:
        try:
            return await super().dispatch(request, *args, **kwargs)  # noqa
        except BusinessError as exc:
            return self.failed_response(msg=exc.msg, code=exc.code, data=exc.data)
        except Exception as exc:  # noqa
            trace_id = getattr(request, "trace_id", None)
            request_id = None
            if hasattr(request, "headers"):
                if not isinstance(trace_id, str):
                    trace_id = request.headers.get("X-Trace-Id")
                request_id = request.headers.get("X-Request-Id")

            current_user = getattr(request, "current_user", None)
            user_id = getattr(current_user, "id", None)

            _REQUEST_LOGGER.error(
                "unhandled request exception | view=%s method=%s path=%s user_id=%s trace_id=%s request_id=%s exception=%s",
                self.__class__.__name__,
                getattr(request, "method", None),
                getattr(request, "path", None),
                user_id,
                trace_id,
                request_id,
                exc.__class__.__name__,
                exc_info=True,
            )
            return self.failed_response(msg="System error", code=50000)

    @staticmethod
    def success_response(data: Any = None, msg: str = "success", code: int = 0) -> JsonResponse:
        payload = {
            "code": code,
            "msg": msg
        }
        if data is not None:
            payload["data"] = data
        return JsonResponse(payload)

    @staticmethod
    def failed_response(msg: str, code: int, data: Any = None) -> JsonResponse:
        payload = {
            "code": code,
            "msg": msg
        }
        if data is not None:
            payload["data"] = data
        return JsonResponse(payload)
