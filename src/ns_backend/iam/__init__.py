# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from django.http import JsonResponse

from ns_backend.backend.common.viewset import BaseRequestViewSet
from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.services import AuditService
from ns_common.error_codes import NsErrorCode
from ns_common.logging.logger import get_ns_logger

if TYPE_CHECKING:
    pass
IAM_LOGGER = get_ns_logger("iam", True)


class AuthenticatedRequestViewSet(BaseRequestViewSet):
    authentication_required = True
    required_permissions: tuple[str, ...] = ()
    verify_service = None
    permission_service = None

    async def initial(self, request, *args, **kwargs):
        await super().initial(request, *args, **kwargs)  # noqa

        if not self.authentication_required:
            return

        user = await self.get_current_user(request)
        if not user:
            raise BusinessError("User is not logged in or session has expired", NsErrorCode.USER_NOT_LOGGED_IN_OR_SESSION_EXPIRED)

        if not bool(getattr(user, "is_active", False)):
            raise BusinessError("User is disabled", NsErrorCode.USER_DISABLED)

        request.current_user = user

        for permission_code in self.required_permissions:
            has_permission = await self.has_permission(user=user, permission_code=permission_code)
            if not has_permission:
                raise BusinessError(f"Permission denied: {permission_code}", NsErrorCode.PERMISSION_DENIED)

    @classmethod
    async def get_current_user(cls, request):
        token = cls.get_bearer_token_from_request(request)
        if not token:
            return None

        verify_service = cls.get_verify_service()
        if verify_service is None:
            return None

        return await verify_service.get_user_by_access_token(token)

    @classmethod
    def get_verify_service(cls):
        return cls.verify_service

    @classmethod
    def get_permission_service(cls):
        return cls.permission_service

    @classmethod
    async def has_permission(cls, user, permission_code: str) -> bool:
        permission_service = cls.get_permission_service()
        if permission_service is None:
            return False
        return await permission_service.has_permission(user=user, permission_code=permission_code)

    @staticmethod
    def get_bearer_token_from_request(request) -> str | None:
        headers = getattr(request, "headers", None)
        if headers is None:
            return None

        authorization = str(headers.get("Authorization", "")).strip()
        if not authorization.startswith("Bearer "):
            return None

        token = authorization.removeprefix("Bearer ").strip()
        return token or None


class AuditRequestMixin:
    audit_enabled = True
    audit_resource_type: str | None = None
    audit_include_response_data = False
    audit_request_body_enabled = False

    audit_resource_id_fields = (
        "id",
        "user_id",
        "role_id",
        "permission_id",
        "company_id",
        "subsidiary_id",
        "department_id",
    )

    audit_request_summary_fields = (
        "id",
        "user_id",
        "role_id",
        "permission_id",
        "company_id",
        "subsidiary_id",
        "department_id",
        "session_id",
        "device_id",
        "permission_code",
        "role_code",
        "username",
    )

    async def dispatch(self, request, *args, **kwargs):
        response = await super().dispatch(request, *args, **kwargs)  # noqa
        if self.audit_enabled:
            await self.record_operation_audit(request=request, response=response)
        return response

    def get_audit_action_name(self, request) -> str:
        action = getattr(self, "action", None)
        if action:
            return str(action)

        resolver_match = getattr(request, "resolver_match", None)
        url_name = getattr(resolver_match, "url_name", None)
        if url_name:
            return str(url_name)

        path = getattr(request, "path", None)
        if path:
            normalized_path = str(path).strip("/")
            if normalized_path:
                return normalized_path.replace("/", ":")

        return str(getattr(request, "method", "unknown")).lower()

    def get_audit_resource_type(self) -> str:
        if self.audit_resource_type:
            return self.audit_resource_type

        model_class = getattr(self, "model_class", None)
        if model_class is not None:
            # noinspection PyProtectedMember
            return str(model_class._meta.db_table)

        crud_service_class = getattr(self, "crud_service_class", None)
        service_model_class = getattr(crud_service_class, "model_class", None)
        if service_model_class is not None:
            # noinspection PyProtectedMember
            return str(service_model_class._meta.db_table)

        return self.__class__.__name__

    def get_audit_operation_type(self, request) -> str:
        resource_type = self.get_audit_resource_type()
        action = self.get_audit_action_name(request)
        return f"{resource_type}:{action}"

    @staticmethod
    def parse_response_payload(response) -> dict[str, Any]:
        if not isinstance(response, JsonResponse):
            return {}

        try:
            content = getattr(response, "content", b"")
            if not content:
                return {}
            parsed = json.loads(content.decode("utf-8"))
            return parsed if isinstance(parsed, dict) else {}
        except Exception:  # noqa
            return {}

    @staticmethod
    def get_response_code_and_msg(response_payload: dict[str, Any]) -> tuple[int, str | None]:
        raw_code = response_payload.get("code", 0)
        msg = response_payload.get("msg")

        try:
            code = int(raw_code)
        except (TypeError, ValueError):
            code = 50000

        return code, None if msg is None else str(msg)

    def get_audit_resource_id(self, request, response_payload: dict[str, Any]) -> int | None:
        response_data = response_payload.get("data")
        if isinstance(response_data, dict):
            value = response_data.get("id")
            try:
                return int(value)
            except (TypeError, ValueError):
                pass

        request_data = self.get_request_dict(request)
        if request_data is None:
            return None

        for field in self.audit_resource_id_fields:
            value = request_data.get(field)
            try:
                return int(value)
            except (TypeError, ValueError):
                continue

        return None

    @staticmethod
    def get_request_dict(request) -> dict[str, Any] | None:
        try:
            data = request.data
        except Exception:  # noqa
            return None

        if not isinstance(data, dict):
            return None

        return data

    def get_audit_request_data(self, request) -> dict[str, Any] | None:
        request_dict = self.get_request_dict(request)

        if self.audit_request_body_enabled and request_dict is not None:
            return dict(request_dict)

        content_type = getattr(request, "content_type", None)

        if request_dict is not None:
            selected_fields = {field: request_dict[field] for field in self.audit_request_summary_fields if field in request_dict}
            return {
                "method": getattr(request, "method", None),
                "path": getattr(request, "path", None),
                "content_type": content_type,
                "body_type": "dict",
                "body_size_hint": len(request_dict),
                "selected_fields": selected_fields,
            }

        try:
            data = request.data
        except Exception:  # noqa
            return None

        return {
            "method": getattr(request, "method", None),
            "path": getattr(request, "path", None),
            "content_type": content_type,
            "body_type": type(data).__name__,
        }

    def get_audit_after_data(self, response_payload: dict[str, Any]) -> dict[str, Any]:
        code, msg = self.get_response_code_and_msg(response_payload)
        after_data: dict[str, Any] = {
            "code": code,
            "msg": msg,
        }

        if self.audit_include_response_data:
            after_data["data"] = response_payload.get("data")

        return after_data

    def get_audit_extra_data(self, request, response_payload: dict[str, Any]) -> dict[str, Any]:
        action = self.get_audit_action_name(request)
        code, msg = self.get_response_code_and_msg(response_payload)

        return {
            "view": self.__class__.__name__,
            "action": action,
            "required_permissions": list(getattr(self, "required_permissions", ()) or ()),
            "response_code": code,
            "response_msg": msg,
        }

    async def record_operation_audit(self, request, response) -> None:
        response_code: int | None = None
        try:
            response_payload = self.parse_response_payload(response)
            code, msg = self.get_response_code_and_msg(response_payload)
            response_code = code
            status = "SUCCESS" if code == 0 else "FAILED"

            event = AuditService.build_event_from_request(
                request=request,
                operation_type=self.get_audit_operation_type(request),
                resource_type=self.get_audit_resource_type(),
                resource_id=self.get_audit_resource_id(request, response_payload),
                request_data=self.get_audit_request_data(request),
                after_data=self.get_audit_after_data(response_payload),
                extra_data=self.get_audit_extra_data(request, response_payload),
                status=status,
                error_code=None if code == 0 else code,
                error_message=None if code == 0 else msg,
            )
            await AuditService.record_event(event)
        except Exception as exc:  # noqa
            trace_id = getattr(request, "trace_id", None)
            request_id = None
            if hasattr(request, "headers"):
                if not isinstance(trace_id, str):
                    trace_id = request.headers.get("X-Trace-Id")
                request_id = request.headers.get("X-Request-Id")

            current_user = getattr(request, "current_user", None)
            user_id = getattr(current_user, "id", None)

            IAM_LOGGER.error(
                "audit record failed | view=%s method=%s path=%s user_id=%s trace_id=%s request_id=%s response_code=%s exception=%s",
                self.__class__.__name__,
                getattr(request, "method", None),
                getattr(request, "path", None),
                user_id,
                trace_id,
                request_id,
                response_code,
                exc.__class__.__name__,
                exc_info=True,
            )
