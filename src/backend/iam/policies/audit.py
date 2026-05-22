# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

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
    def to_json_safe(cls, value):
        if value is None or isinstance(value, (str, int, float, bool)):
            return value

        if isinstance(value, (datetime, date)):
            return value.isoformat()

        if isinstance(value, (Decimal, UUID)):
            return str(value)

        if isinstance(value, bytes):
            try:
                return value.decode("utf-8", errors="replace")
            except Exception:
                return str(value)

        if isinstance(value, dict):
            result: dict[str, Any] = {}
            for key, item in value.items():
                result[str(key)] = cls.to_json_safe(item)
            return result

        if isinstance(value, (list, tuple, set)):
            return [cls.to_json_safe(item) for item in value]

        return str(value)

    @classmethod
    def mask_sensitive_data(cls, data):
        if data is None:
            return None

        if isinstance(data, dict):
            masked: dict[str, Any] = {}
            for key, value in data.items():
                normalized_key = str(key)
                if normalized_key.lower() in cls.SENSITIVE_KEYS:
                    masked[normalized_key] = "***"
                    continue
                masked[normalized_key] = cls.mask_sensitive_data(value)
            return masked

        if isinstance(data, (list, tuple, set)):
            return [cls.mask_sensitive_data(item) for item in data]

        return cls.to_json_safe(data)

    @classmethod
    def normalize_status(cls, status: str | None) -> str:
        if status == cls.STATUS_FAILED:
            return cls.STATUS_FAILED
        return cls.STATUS_SUCCESS

    @staticmethod
    def truncate(value: str | None, max_length: int) -> str | None:
        if value is None:
            return None
        return str(value)[:max_length]

    @classmethod
    def normalize_event(cls, event: AuditEvent) -> AuditEvent:
        if not event.operation_type:
            raise BusinessError("operation_type is required", 16001)

        if not event.resource_type:
            raise BusinessError("resource_type is required", 16002)

        return replace(
            event,
            operation_type=cls.truncate(event.operation_type, 64),
            resource_type=cls.truncate(event.resource_type, 64),
            request_method=cls.truncate(event.request_method, 16),
            request_path=cls.truncate(event.request_path, 255),
            client_ip=cls.truncate(event.client_ip, 64),
            user_agent=cls.truncate(event.user_agent, 512),
            request_data=cls.mask_sensitive_data(event.request_data),
            before_data=cls.mask_sensitive_data(event.before_data),
            after_data=cls.mask_sensitive_data(event.after_data),
            extra_data=cls.mask_sensitive_data(event.extra_data),
            status=cls.normalize_status(event.status),
            error_message=cls.truncate(event.error_message, 512),
            trace_id=cls.truncate(event.trace_id, 64),
        )


__all__ = ["AuditPolicy"]

