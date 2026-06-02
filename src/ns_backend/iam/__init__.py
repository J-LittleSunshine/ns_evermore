# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from django.http import JsonResponse

from ns_backend.backend.common.viewset import BaseRequestViewSet
from ns_backend.backend.exceptions import BusinessError
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
    authorize_service = None

    DECISION_SOURCE_ANONYMOUS = "anonymous"
    DECISION_SOURCE_AUTHENTICATION = "authentication"
    DECISION_SOURCE_RBAC = "rbac"
    DECISION_SOURCE_ACL = "acl"
    DECISION_SOURCE_POLICY = "policy"
    DECISION_SOURCE_SUPERUSER = "superuser"
    DECISION_SOURCE_NONE = "none"

    @classmethod
    def build_decision_context(
        cls,
        *,
        allowed: bool,
        decision_reason: str,
        decision_source: str,
        matched_permission_code: str | None = None,
    ) -> dict[str, Any]:
        """Build one normalized authorization decision context payload."""
        return {
            "allowed": bool(allowed),
            "decision_reason": str(decision_reason).strip() if decision_reason else "UNKNOWN_DECISION_REASON",
            "decision_source": str(decision_source).strip() if decision_source else cls.DECISION_SOURCE_NONE,
            "matched_permission_code": None if not matched_permission_code else str(matched_permission_code).strip(),
        }

    @staticmethod
    def _resolve_trace_id(request) -> str | None:
        """Resolve trace id from request attribute or inbound headers."""
        trace_id = getattr(request, "trace_id", None)
        if not isinstance(trace_id, str) and hasattr(request, "headers"):
            trace_id = request.headers.get("X-Trace-Id")

        if isinstance(trace_id, str):
            normalized = trace_id.strip()
            return normalized or None

        return None

    @staticmethod
    def _raise_permission_denied(permission_code: str) -> None:
        """Raise a normalized permission denied error for one permission code."""
        raise BusinessError(f"Permission denied: {permission_code}", NsErrorCode.PERMISSION_DENIED)

    def set_decision_context(
        self,
        *,
        allowed: bool,
        decision_reason: str,
        decision_source: str,
        matched_permission_code: str | None = None,
    ) -> None:
        """Store authorization decision context on view instance for audit usage."""
        decision_context = self.build_decision_context(
            allowed=allowed,
            decision_reason=decision_reason,
            decision_source=decision_source,
            matched_permission_code=matched_permission_code,
        )
        self._iam_decision_context = decision_context

    async def initial(self, request, *args, **kwargs):
        """Run authentication and IAM authorization before action dispatch."""
        await super().initial(request, *args, **kwargs)  # noqa
        self._iam_decision_context = None

        if not self.authentication_required:
            self.set_decision_context(
                allowed=True,
                decision_reason="AUTHENTICATION_NOT_REQUIRED",
                decision_source=self.DECISION_SOURCE_ANONYMOUS,
            )
            return

        user = await self.get_current_user(request)
        if not user:
            self.set_decision_context(
                allowed=False,
                decision_reason="AUTHENTICATION_REQUIRED",
                decision_source=self.DECISION_SOURCE_AUTHENTICATION,
            )
            raise BusinessError("User is not logged in or session has expired", NsErrorCode.USER_NOT_LOGGED_IN_OR_SESSION_EXPIRED)

        if not bool(getattr(user, "is_active", False)):
            self.set_decision_context(
                allowed=False,
                decision_reason="USER_DISABLED",
                decision_source=self.DECISION_SOURCE_AUTHENTICATION,
            )
            raise BusinessError("User is disabled", NsErrorCode.USER_DISABLED)

        request.current_user = user

        if not self.required_permissions:
            self.set_decision_context(
                allowed=True,
                decision_reason="NO_REQUIRED_PERMISSIONS",
                decision_source=self.DECISION_SOURCE_AUTHENTICATION,
            )
            return

        last_allowed_reason = "PERMISSION_GRANTED"
        last_allowed_source = self.DECISION_SOURCE_NONE
        last_permission_code: str | None = None

        for permission_code in self.required_permissions:
            try:
                decision = await self.check_permission_by_authorize_service(
                    request=request,
                    user=user,
                    permission_code=permission_code,
                )
            except Exception as exc:  # noqa
                self.set_decision_context(
                    allowed=False,
                    decision_reason="AUTHORIZE_SERVICE_UNAVAILABLE",
                    decision_source=self.DECISION_SOURCE_NONE,
                    matched_permission_code=permission_code,
                )
                IAM_LOGGER.error(
                    "authorize service check failed | view=%s path=%s user_id=%s permission_code=%s exception=%s",
                    self.__class__.__name__,
                    getattr(request, "path", None),
                    getattr(user, "id", None),
                    permission_code,
                    exc.__class__.__name__,
                    exc_info=True,
                )
                self._raise_permission_denied(permission_code)

            decision_allowed = bool(decision.get("allowed", False))
            decision_reason = str(decision.get("reason") or "PERMISSION_DENIED")
            decision_source = str(decision.get("matched_source") or self.DECISION_SOURCE_NONE)

            if not decision_allowed:
                self.set_decision_context(
                    allowed=False,
                    decision_reason=decision_reason,
                    decision_source=decision_source,
                    matched_permission_code=permission_code,
                )
                self._raise_permission_denied(permission_code)

            last_allowed_reason = str(decision.get("reason") or "PERMISSION_GRANTED")
            last_allowed_source = decision_source
            last_permission_code = permission_code

        self.set_decision_context(
            allowed=True,
            decision_reason=last_allowed_reason,
            decision_source=last_allowed_source,
            matched_permission_code=last_permission_code,
        )

    @classmethod
    async def get_current_user(cls, request):
        """Resolve current user from bearer token."""
        token = cls.get_bearer_token_from_request(request)
        if not token:
            return None

        verify_service = cls.get_verify_service()
        if verify_service is None:
            return None

        return await verify_service.get_user_by_access_token(token)

    @classmethod
    def get_verify_service(cls):
        """Return configured token verify service."""
        return cls.verify_service

    @classmethod
    def get_permission_service(cls):
        """Return configured permission service."""
        return cls.permission_service

    @classmethod
    def get_authorize_service(cls):
        """Return configured unified authorize service."""
        return cls.authorize_service

    @staticmethod
    def parse_action_from_permission_code(permission_code: str) -> str | None:
        """Extract action segment from one permission code."""
        segments = [segment.strip() for segment in str(permission_code).split(":")]
        if len(segments) < 3:
            return None
        if any(not segment for segment in segments):
            return None
        return segments[-1].lower()

    async def check_permission_by_authorize_service(self, *, request, user, permission_code: str) -> dict[str, Any]:
        """Check one permission through the unified AuthorizeService."""
        authorize_service = self.get_authorize_service()
        if authorize_service is None:
            raise BusinessError("authorize_service is not configured", NsErrorCode.PERMISSION_DENIED)

        action_code = self.parse_action_from_permission_code(permission_code)
        if action_code is None:
            raise BusinessError(f"permission_code is invalid: {permission_code}", NsErrorCode.PERMISSION_DENIED)

        trace_id = self._resolve_trace_id(request)

        decision = await authorize_service.check(
            user=user,
            data={
                "resource_type": "iam.endpoint",
                "resource_id": str(getattr(request, "path", "") or ""),
                "action_code": action_code,
                "permission_code": permission_code,
            },
            trace_id=trace_id,
        )

        if not isinstance(decision, dict):
            raise BusinessError("authorize_service decision is invalid", NsErrorCode.PERMISSION_DENIED)

        return decision

    @classmethod
    async def has_permission(cls, user, permission_code: str) -> bool:
        """Check one permission by legacy permission service (compatibility path)."""
        permission_service = cls.get_permission_service()
        if permission_service is None:
            return False
        return await permission_service.has_permission(user=user, permission_code=permission_code)

    @staticmethod
    def get_bearer_token_from_request(request) -> str | None:
        """Extract bearer token from request Authorization header."""
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
