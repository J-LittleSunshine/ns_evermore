# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from adrf.viewsets import ViewSet
from django.http import JsonResponse

from ns_backend.exceptions import BusinessError
from ns_backend.logger import get_logger

if TYPE_CHECKING:
    pass
_logger = get_logger("ns_backend")


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

        except Exception as exc:
            _logger.exception(exc)
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
