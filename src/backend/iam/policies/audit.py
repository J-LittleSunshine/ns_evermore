# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import replace
from typing import Any

from iam.schemas import AuditEvent
from ns_backend.exceptions import BusinessError
from ns_backend.policies import BasePolicy


class AuditPolicy(BasePolicy):
    STATUS_SUCCESS = "SUCCESS"
    STATUS_FAILED = "FAILED"

    SENSITIVE_KEYS = {
        "password",
        "old_password",
        "new_password",
        "confirm_password",
        "refresh_token",
        "access_token",
        "token",
        "authorization",
        "secret",
        "client_secret",
    }

    @classmethod
    def mask_sensitive_data(cls, data):
        if data is None:
            return None

        if isinstance(data, dict):
            masked: dict[str, Any] = {}
            for key, value in data.items():
                if str(key).lower() in cls.SENSITIVE_KEYS:
                    masked[key] = "***"
                    continue
                masked[key] = cls.mask_sensitive_data(value)
            return masked

        if isinstance(data, list):
            return [cls.mask_sensitive_data(item) for item in data]

        return data

    @classmethod
    def normalize_status(cls, status: str | None) -> str:
        if status == cls.STATUS_FAILED:
            return cls.STATUS_FAILED
        return cls.STATUS_SUCCESS

    @classmethod
    def normalize_event(cls, event: AuditEvent) -> AuditEvent:
        if not event.operation_type:
            raise BusinessError("operation_type is required", 16001)

        if not event.resource_type:
            raise BusinessError("resource_type is required", 16002)

        return replace(
            event,
            request_data=cls.mask_sensitive_data(event.request_data),
            before_data=cls.mask_sensitive_data(event.before_data),
            after_data=cls.mask_sensitive_data(event.after_data),
            status=cls.normalize_status(event.status),
            error_message=(event.error_message or None)[:512] if event.error_message else None,
            request_path=(event.request_path or None)[:255] if event.request_path else None,
            user_agent=(event.user_agent or None)[:512] if event.user_agent else None,
            trace_id=(event.trace_id or None)[:64] if event.trace_id else None,
        )


__all__ = ["AuditPolicy"]

