# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from iam.error_codes import IamErrorCode
from iam.schemas import AuditEvent
from ns_backend.exceptions import BusinessError
from ns_backend.policies import BasePolicy


class AuditPolicy(BasePolicy):
    STATUS_SUCCESS = "SUCCESS"
    STATUS_FAILED = "FAILED"
    MAX_AUDIT_STRING_LENGTH = 2048
    MAX_AUDIT_JSON_LENGTH = 32768

    SENSITIVE_KEYS = {
        "password",
        "old_password",
        "new_password",
        "confirm_password",
        "oldpassword",
        "newpassword",
        "confirmpassword",
        "refresh_token",
        "access_token",
        "refreshtoken",
        "accesstoken",
        "token",
        "authtoken",
        "auth_token",
        "sessiontoken",
        "session_token",
        "authorization",
        "bearer",
        "jwt",
        "jwt_token",
        "secret",
        "client_secret",
        "clientsecret",
        "api_key",
        "apikey",
        "secret_key",
        "secretkey",
        "private_key",
        "privatekey",
        "csrf",
        "csrf_token",
        "csrftoken",
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
    def get_json_length(cls, value) -> int:
        try:
            return len(json.dumps(value, ensure_ascii=False, default=str))
        except Exception:
            return len(str(value))

    @classmethod
    def limit_audit_value(cls, value):
        safe_value = cls.to_json_safe(value)
        if isinstance(safe_value, str) and len(safe_value) > cls.MAX_AUDIT_STRING_LENGTH:
            return {
                "__truncated__": True,
                "type": "string",
                "length": len(safe_value),
                "value": safe_value[: cls.MAX_AUDIT_STRING_LENGTH],
            }
        return safe_value

    @classmethod
    def limit_audit_payload(cls, value):
        if value is None:
            return None

        if isinstance(value, dict):
            limited_obj = {
                str(key): cls.limit_audit_payload(item)
                for key, item in value.items()
            }
            json_length = cls.get_json_length(limited_obj)
            if json_length > cls.MAX_AUDIT_JSON_LENGTH:
                return {
                    "__truncated__": True,
                    "type": "object",
                    "length": json_length,
                }
            return limited_obj

        if isinstance(value, (list, tuple, set)):
            limited_arr = [cls.limit_audit_payload(item) for item in value]
            json_length = cls.get_json_length(limited_arr)
            if json_length > cls.MAX_AUDIT_JSON_LENGTH:
                return {
                    "__truncated__": True,
                    "type": "array",
                    "length": json_length,
                }
            return limited_arr

        return cls.limit_audit_value(value)

    @classmethod
    def normalize_payload(cls, value):
        masked = cls.mask_sensitive_data(value)
        return cls.limit_audit_payload(masked)

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
            raise BusinessError("operation_type is required", IamErrorCode.AUDIT_OPERATION_TYPE_REQUIRED)

        if not event.resource_type:
            raise BusinessError("resource_type is required", IamErrorCode.AUDIT_RESOURCE_TYPE_REQUIRED)

        return replace(
            event,
            operation_type=cls.truncate(event.operation_type, 64),
            resource_type=cls.truncate(event.resource_type, 64),
            request_method=cls.truncate(event.request_method, 16),
            request_path=cls.truncate(event.request_path, 255),
            client_ip=cls.truncate(event.client_ip, 64),
            user_agent=cls.truncate(event.user_agent, 512),
            request_data=cls.normalize_payload(event.request_data),
            before_data=cls.normalize_payload(event.before_data),
            after_data=cls.normalize_payload(event.after_data),
            extra_data=cls.normalize_payload(event.extra_data),
            status=cls.normalize_status(event.status),
            error_message=cls.truncate(event.error_message, 512),
            trace_id=cls.truncate(event.trace_id, 64),
        )


__all__ = ["AuditPolicy"]

