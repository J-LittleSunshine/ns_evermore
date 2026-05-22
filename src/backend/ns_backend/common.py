# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from adrf.viewsets import ViewSet
from django.http import JsonResponse

from ns_backend.exceptions import BusinessError
from ns_backend.logging import safe_emit_log_event
from ns_common.logging import NsLogEvent

if TYPE_CHECKING:
    pass


class BaseRequestViewSet(ViewSet):
    @classmethod
    def as_view(cls, actions: dict[str, str] | None = None, **initkwargs: Any):
        if not actions:
            raise NotImplementedError(
                f"{cls.__name__} must explicitly declare as_view(actions)"
            )

        return super().as_view(actions=actions, **initkwargs)

    async def dispatch(self, request, *args, **kwargs):
        try:
            return await super().dispatch(request, *args, **kwargs)  # noqa

        except BusinessError as exc:
            return self.failed_response(
                msg=exc.msg,
                code=exc.code,
                data=exc.data,
            )

        except Exception as exc:  # noqa
            trace_id = getattr(request, "trace_id", None)
            request_id = None
            if hasattr(request, "headers"):
                if not isinstance(trace_id, str):
                    trace_id = request.headers.get("X-Trace-Id")
                request_id = request.headers.get("X-Request-Id")

            safe_emit_log_event(
                event=NsLogEvent.DJANGO_REQUEST_EXCEPTION,
                message="unhandled request exception",
                level="ERROR",
                trace_id=trace_id if isinstance(trace_id, str) else None,
                request_id=request_id,
                context={
                    "view": self.__class__.__name__,
                    "method": getattr(request, "method", None),
                    "path": getattr(request, "path", None),
                    "exception_type": exc.__class__.__name__,
                },
                exc_info=True,
            )
            return self.failed_response(
                msg="System error",
                code=50000,
            )


    @staticmethod
    def success_response(data: Any = None, msg: str = "success", code: int = 0):
        response_data = {
            "code": code,
            "msg": msg,
        }

        if data is not None:
            response_data["data"] = data

        return JsonResponse(response_data)

    @staticmethod
    def failed_response(msg: str, code: int, data: Any = None):
        response_data = {
            "code": code,
            "msg": msg,
        }

        if data is not None:
            response_data["data"] = data

        return JsonResponse(response_data)
