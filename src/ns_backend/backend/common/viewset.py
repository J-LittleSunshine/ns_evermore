# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any, NoReturn
from asgiref.sync import async_to_sync
from adrf.viewsets import ViewSet
from django.http import JsonResponse

from ns_backend.backend.common.logger import iam_logger, logger
from ns_backend.backend.exceptions import BusinessError
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


class BaseRequestViewSet(ViewSet):
    @classmethod
    def as_view(cls, actions: dict[str, str] | None = None, **initkwargs: Any):
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

            logger.error(
                "unhandled request exception",
                exc_info=True,
                extra={
                    "view": self.__class__.__name__,
                    "method": getattr(request, "method", None),
                    "path": getattr(request, "path", None),
                    "user_id": user_id,
                    "trace_id": trace_id,
                    "request_id": request_id,
                    "exception_class": exc.__class__.__name__,
                },
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


class AuthenticatedRequestViewSet(BaseRequestViewSet):
    """Authenticate request user and evaluate route permissions via authorize service."""

    authentication_required = True
    required_permissions: tuple[str, ...] = ()
    authorize_resource_type = "iam.endpoint"
    verify_service = None
    permission_service = None
    authorize_service = None

    authentication_classes = ()
    permission_classes = ()
    throttle_classes = ()

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
    def _raise_permission_denied(permission_code: str) -> NoReturn:
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

    def initial(self, request, *args, **kwargs) -> None:
        """Run authentication and authorization checks before action dispatch.

        ADRF calls initial() through sync_to_async(), so this method must remain
        synchronous. Async IAM services are invoked through async_to_sync().
        """
        super().initial(request, *args, **kwargs)
        self._iam_decision_context = None

        if not self.authentication_required:
            self.set_decision_context(
                allowed=True,
                decision_reason="AUTHENTICATION_NOT_REQUIRED",
                decision_source=self.DECISION_SOURCE_ANONYMOUS,
            )
            return

        user = async_to_sync(self.get_current_user)(request)
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
                decision = async_to_sync(self.check_permission_by_authorize_service)(
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
                iam_logger.error(
                    "authorize service check failed",
                    exc_info=True,
                    extra={
                        "view": self.__class__.__name__,
                        "path": getattr(request, "path", None),
                        "user_id": getattr(user, "id", None),
                        "permission_code": permission_code,
                        "trace_id": self._resolve_trace_id(request),
                        "exception_class": exc.__class__.__name__,
                    },
                )
                self._raise_permission_denied(permission_code)
            else:
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

    @classmethod
    def get_authorize_resource_type(cls, request, permission_code: str) -> str:
        """Resolve resource type used for route-level authorize checks."""
        _ = (request, permission_code)
        resource_type = str(getattr(cls, "authorize_resource_type", "") or "").strip().lower()
        return resource_type or "iam.endpoint"

    @staticmethod
    def get_authorize_resource_id(request, permission_code: str) -> str:
        """Resolve resource id used for route-level authorize checks."""
        _ = permission_code
        return str(getattr(request, "path", "") or "")

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
        """Check one permission through the unified authorize service."""
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
                "resource_type": self.get_authorize_resource_type(request, permission_code),
                "resource_id": self.get_authorize_resource_id(request, permission_code),
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

    def perform_authentication(self, request) -> None:
        """Disable DRF default authentication.

        ns_backend uses IAM token verification instead of django.contrib.auth.
        DRF's default unauthenticated-user path imports django.contrib.auth
        models, which are intentionally not installed in this project.
        """
        _ = request

    def check_permissions(self, request) -> None:
        """Disable DRF permission classes; IAM handles permission decisions."""
        _ = request

    def check_throttles(self, request) -> None:
        """Disable DRF throttle classes by default."""
        _ = request
