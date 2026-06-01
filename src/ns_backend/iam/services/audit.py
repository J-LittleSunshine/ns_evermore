# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.utils import timezone

from ns_backend.iam.policies import AuditPolicy
from ns_backend.iam.repositories import AuditRepository
from ns_backend.iam.schemas import AuditEvent

if TYPE_CHECKING:
    pass


class AuditService:
    """Audit domain service.

    Service responsibilities:
    1. Normalize and mask audit event payloads through AuditPolicy.
    2. Build persistence payloads.
    3. Build AuditEvent from request context.
    4. Delegate persistence to AuditRepository.
    """

    @classmethod
    async def record_event(cls, event: AuditEvent) -> dict[str, int]:
        """Normalize and persist one audit event."""
        normalized_event = AuditPolicy.normalize_event(event)
        data = cls.build_create_data(normalized_event)
        item = await AuditRepository.create_event(data)
        return {"id": item.id}

    @staticmethod
    def build_create_data(event: AuditEvent) -> dict[str, Any]:
        """Build database create payload from an audit event."""
        now = timezone.now()
        return {
            "operator_id": event.operator_id,
            "company_id": event.company_id,
            "operation_type": event.operation_type,
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "request_method": event.request_method,
            "request_path": event.request_path,
            "client_ip": event.client_ip,
            "user_agent": event.user_agent,
            "request_data": event.request_data,
            "before_data": event.before_data,
            "after_data": event.after_data,
            "extra_data": event.extra_data,
            "status": event.status,
            "error_code": event.error_code,
            "error_message": event.error_message,
            "trace_id": event.trace_id,
            "created_at": now,
        }

    @classmethod
    def build_event_from_request(
            cls,
            *,
            request,
            operation_type: str,
            resource_type: str,
            resource_id: int | None = None,
            request_data: dict[str, Any] | None = None,
            before_data: dict[str, Any] | None = None,
            after_data: dict[str, Any] | None = None,
            extra_data: dict[str, Any] | None = None,
            status: str = "SUCCESS",
            error_code: int | None = None,
            error_message: str | None = None
    ) -> AuditEvent:
        """Build audit event from request and explicit audit metadata."""
        operator = getattr(request, "current_user", None)
        operator_id = getattr(operator, "id", None)
        company_id = getattr(operator, "company_id", None)

        request_meta = getattr(request, "META", {}) or {}
        headers = getattr(request, "headers", {}) or {}

        client_ip = cls.get_client_ip(request_meta=request_meta, headers=headers)
        trace_id = cls.get_trace_id(headers=headers)
        user_agent = request_meta.get("HTTP_USER_AGENT") or headers.get("User-Agent")

        return AuditEvent(
            operation_type=operation_type,
            resource_type=resource_type,
            operator_id=operator_id,
            company_id=company_id,
            resource_id=resource_id,
            request_method=getattr(request, "method", None),
            request_path=getattr(request, "path", None),
            client_ip=client_ip,
            user_agent=user_agent,
            request_data=request_data,
            before_data=before_data,
            after_data=after_data,
            extra_data=extra_data,
            status=status,
            error_code=error_code,
            error_message=error_message,
            trace_id=trace_id,
        )

    @staticmethod
    def get_client_ip(*, request_meta: dict[str, Any], headers: Any) -> str | None:
        """Resolve client IP for audit context."""
        client_ip = None

        if bool(getattr(settings, "TRUST_X_FORWARDED_FOR", False)):
            x_forwarded_for = headers.get("X-Forwarded-For") or request_meta.get("HTTP_X_FORWARDED_FOR")
            if x_forwarded_for:
                client_ip = str(x_forwarded_for).split(",")[0].strip() or None

        if client_ip is None:
            client_ip = request_meta.get("REMOTE_ADDR")

        return None if client_ip is None else str(client_ip)

    @staticmethod
    def get_trace_id(*, headers: Any) -> str | None:
        """Resolve trace id from request headers."""
        if not headers:
            return None

        trace_id = headers.get("X-Trace-Id") or headers.get("X-Request-Id")
        return None if trace_id is None else str(trace_id)
