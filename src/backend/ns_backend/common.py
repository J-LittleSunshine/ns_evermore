# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from adrf.viewsets import ViewSet
from django.http import JsonResponse

from iam.application.auth.verify import VerifyApplicationService
from iam.domain.services.permission import PermissionDomainService
from ns_backend.exceptions import BusinessError
from ns_backend.logger import get_logger

if TYPE_CHECKING:
    pass
_logger = get_logger("ns_backend")


class BaseRequestViewSet(ViewSet):
    authentication_required = True
    required_permissions: tuple[str, ...] = ()

    @classmethod
    def as_view(cls, actions: dict[str, str] | None = None, **initkwargs: Any):
        if not actions:
            raise NotImplementedError(
                f"{cls.__name__} 必须显式声明 as_view(actions)"
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
                msg="系统异常",
                code=50000,
            )

    async def initial(self, request, *args, **kwargs):
        await super().initial(request, *args, **kwargs)  # noqa

        if not self.authentication_required:
            return

        user = await self.get_current_user(request)

        if not user:
            raise BusinessError("用户未登录或登录状态已失效", 11007)

        if not user.is_active:
            raise BusinessError("用户已被禁用", 11008)

        request.current_user = user

        for permission_code in self.required_permissions:
            has_permission = await PermissionDomainService.has_permission(
                user=user,
                permission_code=permission_code,
            )

            if not has_permission:
                raise BusinessError(f"权限不足：{permission_code}", 11009)

    @classmethod
    async def get_current_user(cls, request):
        token = cls.get_bearer_token_from_request(request)

        if not token:
            return None

        return await VerifyApplicationService.get_user_by_access_token(token)

    @staticmethod
    def get_bearer_token_from_request(request) -> str | None:
        authorization = request.headers.get("Authorization", "")

        if not authorization.startswith("Bearer "):
            return None

        token = authorization.removeprefix("Bearer ").strip()
        return token or None

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
