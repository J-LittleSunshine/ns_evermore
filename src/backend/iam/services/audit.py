# -*- coding: utf-8 -*-
from __future__ import annotations

from django.utils import timezone

from iam.policies.audit import AuditPolicy
from iam.repositories.audit import AuditRepository
from iam.schemas import AuditEvent


class AuditService:
    @classmethod
    async def record_event(cls, event: AuditEvent) -> dict:
        normalized_event = AuditPolicy.normalize_event(event)
        data = cls.build_create_data(normalized_event)
        item = await AuditRepository.create_event(data)
        return {"id": item.id}

    @staticmethod
    def build_create_data(event: AuditEvent) -> dict:
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
        request_data: dict | None = None,
        before_data: dict | None = None,
        after_data: dict | None = None,
        status: str = "SUCCESS",
        error_code: int | None = None,
        error_message: str | None = None,
    ) -> AuditEvent:
        operator = getattr(request, "current_user", None)
        operator_id = getattr(operator, "id", None)
        company_id = getattr(operator, "company_id", None)

        request_meta = getattr(request, "META", {}) or {}
        x_forwarded_for = request_meta.get("HTTP_X_FORWARDED_FOR")
        client_ip = None
        if x_forwarded_for:
            client_ip = x_forwarded_for.split(",")[0].strip() or None
        if client_ip is None:
            client_ip = request_meta.get("REMOTE_ADDR")

        headers = getattr(request, "headers", {})
        trace_id = None
        if headers:
            trace_id = headers.get("X-Trace-Id") or headers.get("X-Request-Id")

        return AuditEvent(
            operation_type=operation_type,
            resource_type=resource_type,
            operator_id=operator_id,
            company_id=company_id,
            resource_id=resource_id,
            request_method=getattr(request, "method", None),
            request_path=getattr(request, "path", None),
            client_ip=client_ip,
            user_agent=request_meta.get("HTTP_USER_AGENT"),
            request_data=request_data,
            before_data=before_data,
            after_data=after_data,
            status=status,
            error_code=error_code,
            error_message=error_message,
            trace_id=trace_id,
        )


__all__ = ["AuditService"]

