# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from django.http import JsonResponse

from ns_backend.backend.common.logger import IAM_LOGGER
from ns_backend.backend.common.viewset import AuthenticatedRequestViewSet
from ns_backend.iam.services import TenantService, VerifyService, PermissionService
from ns_backend.iam.services.authorize import AuthorizeService
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


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

    DECISION_ERROR_REASON_MAP = {
        NsErrorCode.USER_NOT_LOGGED_IN_OR_SESSION_EXPIRED: ("AUTHENTICATION_REQUIRED", "authentication"),
        NsErrorCode.USER_DISABLED: ("USER_DISABLED", "authentication"),
        NsErrorCode.USER_DISABLED_OR_NOT_FOUND: ("USER_DISABLED_OR_NOT_FOUND", "authentication"),
        NsErrorCode.PERMISSION_DENIED: ("PERMISSION_DENIED", "rbac"),
    }

    async def dispatch(self, request, *args, **kwargs):
        """Dispatch request and record operation audit when enabled."""
        response = await super().dispatch(request, *args, **kwargs)  # noqa
        if self.audit_enabled:
            await self.record_operation_audit(request=request, response=response)
        return response

    def get_audit_action_name(self, request) -> str:
        """Resolve audit action name from view action, url name, or path."""
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
        """Resolve audit resource type from view or service model metadata."""
        if self.audit_resource_type:
            return self.audit_resource_type

        model_class = getattr(self, "model_class", None)
        if model_class is not None:
            # noinspection PyProtectedMember
            return str(model_class._meta.db_table)

        service_class = getattr(self, "service_class", None)
        service_model_class = getattr(service_class, "model_class", None)
        if service_model_class is not None:
            # noinspection PyProtectedMember
            return str(service_model_class._meta.db_table)

        return self.__class__.__name__

    def get_audit_operation_type(self, request) -> str:
        """Build audit operation type identifier."""
        resource_type = self.get_audit_resource_type()
        action = self.get_audit_action_name(request)
        return f"{resource_type}:{action}"

    @staticmethod
    def parse_response_payload(response) -> dict[str, Any]:
        """Parse standard JSON response payload for audit extraction."""
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
        """Extract normalized response code and message from payload."""
        raw_code = response_payload.get("code", 0)
        msg = response_payload.get("msg")

        try:
            code = int(raw_code)
        except (TypeError, ValueError):
            code = 50000

        return code, None if msg is None else str(msg)

    def get_audit_resource_id(self, request, response_payload: dict[str, Any]) -> int | None:
        """Resolve audited resource id from response data or request body."""
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
        """Return request payload as dict when possible."""
        try:
            data = request.data
        except Exception:  # noqa
            return None

        if not isinstance(data, dict):
            return None

        return data

    def get_audit_request_data(self, request) -> dict[str, Any] | None:
        """Build request summary payload for operation audit."""
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
        """Build response summary payload for operation audit."""
        code, msg = self.get_response_code_and_msg(response_payload)
        after_data: dict[str, Any] = {
            "code": code,
            "msg": msg,
        }

        if self.audit_include_response_data:
            after_data["data"] = response_payload.get("data")

        return after_data

    def resolve_decision_audit_fields(self, request, *, response_code: int, response_msg: str | None) -> dict[str, Any]:
        """Resolve decision fields for audit extra_data from request context and response."""
        decision_context = getattr(self, "_iam_decision_context", None)
        has_decision_context = isinstance(decision_context, dict)

        decision_reason: str | None = None
        matched_permission_code: str | None = None
        decision_source = "none"
        decision_allowed = response_code == 0

        if has_decision_context:
            decision_reason_value = decision_context.get("decision_reason")
            if decision_reason_value:
                decision_reason = str(decision_reason_value)

            matched_permission_code_value = decision_context.get("matched_permission_code")
            if matched_permission_code_value:
                matched_permission_code = str(matched_permission_code_value)

            decision_source_value = decision_context.get("decision_source")
            if decision_source_value:
                decision_source = str(decision_source_value)

            allowed_value = decision_context.get("allowed")
            if isinstance(allowed_value, bool):
                decision_allowed = allowed_value and response_code == 0

        if not matched_permission_code:
            required_permissions = list(getattr(self, "required_permissions", ()) or ())
            if required_permissions:
                matched_permission_code = required_permissions[0]

        mapped_reason, mapped_source = self.DECISION_ERROR_REASON_MAP.get(response_code, (None, None))
        if response_code != 0:
            decision_allowed = False
            if not decision_reason and mapped_reason:
                decision_reason = mapped_reason
            if not has_decision_context and decision_source == "none" and mapped_source:
                decision_source = mapped_source

        if response_code == 0 and not decision_reason:
            decision_reason = "REQUEST_ALLOWED"

        if response_code != 0 and not decision_reason:
            if response_msg:
                decision_reason = f"REQUEST_FAILED: {response_msg}"
            else:
                decision_reason = f"REQUEST_FAILED_CODE_{response_code}"

        return {
            "decision_allowed": decision_allowed,
            "decision_reason": decision_reason,
            "matched_permission_code": matched_permission_code,
            "decision_source": decision_source,
        }

    def get_audit_extra_data(self, request, response_payload: dict[str, Any]) -> dict[str, Any]:
        """Build operation-audit extra data including decision context fields."""
        action = self.get_audit_action_name(request)
        code, msg = self.get_response_code_and_msg(response_payload)
        decision_fields = self.resolve_decision_audit_fields(request, response_code=code, response_msg=msg)

        return {
            "view": self.__class__.__name__,
            "action": action,
            "required_permissions": list(getattr(self, "required_permissions", ()) or ()),
            "response_code": code,
            "response_msg": msg,
            "decision_reason": decision_fields["decision_reason"],
            "matched_permission_code": decision_fields["matched_permission_code"],
            "decision_source": decision_fields["decision_source"],
            "decision_allowed": decision_fields["decision_allowed"],
        }

    async def record_operation_audit(self, request, response) -> None:
        """Record operation audit and log errors without breaking request flow."""
        response_code: int | None = None
        try:
            from ns_backend.iam.services import AuditService

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
            trace_id = AuthenticatedRequestViewSet._resolve_trace_id(request)
            request_id = None
            if hasattr(request, "headers"):
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


class IamRequestViewSet(AuditRequestMixin, AuthenticatedRequestViewSet):
    authorize_resource_type = "iam.endpoint"
    verify_service = VerifyService
    permission_service = PermissionService
    authorize_service = AuthorizeService
    authentication_required = True


class BaseIamViewSet(IamRequestViewSet):
    service_class = None

    @property
    def service(self):
        """Return configured service class for current IAM view."""
        if self.service_class is None:
            raise RuntimeError("service_class is not configured")
        return self.service_class

    @staticmethod
    def _current_user(request):
        """Return current authenticated user bound to request."""
        return getattr(request, "current_user", None)

    @classmethod
    def _tenant_context(cls, request):
        """Build tenant context from request user."""
        user = getattr(request, "current_user", None)
        if user is None:
            return None
        return TenantService.from_user(user)

    async def list_item(self, request, *args, **kwargs):
        """List IAM domain entities by paging and filter conditions."""
        user = self._current_user(request)
        data = await self.service.list_items(
            page=request.data.get("page", 1),
            page_size=request.data.get("page_size", 20),
            filters=request.data.get("filters"),
            keyword=request.data.get("keyword"),
            order_by=request.data.get("order_by"),
            include_staff=request.data.get("include_staff"),
            include_superuser=request.data.get("include_superuser"),
            operator=user,
            tenant_context=self._tenant_context(request),
        )
        return self.success_response(data)

    async def detail_item(self, request, *args, **kwargs):
        """Query one IAM domain entity by identifier."""
        user = self._current_user(request)
        data = await self.service.detail_item(
            item_id=request.data.get("id"),
            operator=user,
            tenant_context=self._tenant_context(request),
        )
        return self.success_response(data)

    async def create_item(self, request, *args, **kwargs):
        """Create one IAM domain entity."""
        user = self._current_user(request)
        result = await self.service.create_item(
            data=request.data,
            operator=user,
            operator_id=getattr(user, "id", None),
            tenant_context=self._tenant_context(request),
        )
        return self.success_response(result)

    async def update_item(self, request, *args, **kwargs):
        """Update one IAM domain entity."""
        user = self._current_user(request)
        await self.service.update_item(
            item_id=request.data.get("id"),
            data=request.data,
            operator=user,
            operator_id=getattr(user, "id", None),
            tenant_context=self._tenant_context(request),
        )
        return self.success_response()

    async def delete_item(self, request, *args, **kwargs):
        """Delete one IAM domain entity."""
        user = self._current_user(request)
        await self.service.delete_item(
            item_id=request.data.get("id"),
            operator=user,
            tenant_context=self._tenant_context(request),
        )
        return self.success_response()
