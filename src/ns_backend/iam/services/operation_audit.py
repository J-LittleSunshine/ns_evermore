# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    TYPE_CHECKING,
)

from django.conf import settings

from ns_backend.iam.errors import IamManagementRequestInvalidError
from ns_backend.iam.repositories import OperationAuditRepository
from ns_common import get_ns_logger

if TYPE_CHECKING:
    from rest_framework.request import Request

logger = get_ns_logger("ns_backend.iam.operation_audit", True)


class OperationAuditService:
    STATUS_SUCCESS = "SUCCESS"
    STATUS_FAILED = "FAILED"

    SENSITIVE_KEYWORDS = (
        "password",
        "token",
        "secret",
        "private_key",
        "passphrase",
    )

    allowed_filter_fields = {
        "id",
        "operator_id",
        "operation_type",
        "resource_type",
        "company_id",
        "resource_id",
        "request_method",
        "request_path",
        "client_ip",
        "status",
        "error_code",
        "trace_id",
    }

    @classmethod
    def is_enabled(cls) -> bool:
        return bool(getattr(settings, "IAM_OPERATION_AUDIT_ENABLED", True))

    @classmethod
    def is_strict_mode_enabled(cls) -> bool:
        return bool(getattr(settings, "IAM_OPERATION_AUDIT_STRICT_MODE", False))

    @classmethod
    async def record_safe(
            cls,
            *,
            operator: Any | None,
            operation_type: str,
            resource_type: str,
            request: "Request",
            request_data: dict[str, Any] | None = None,
            before_data: dict[str, Any] | None = None,
            after_data: dict[str, Any] | None = None,
            status: str = STATUS_SUCCESS,
            error: BaseException | None = None,
            resource_id: int | None = None,
            company_id: int | None = None,
            extra_data: dict[str, Any] | None = None,
    ) -> None:
        if not cls.is_enabled():
            return

        try:
            await cls.record(
                operator=operator,
                operation_type=operation_type,
                resource_type=resource_type,
                request=request,
                request_data=request_data,
                before_data=before_data,
                after_data=after_data,
                status=status,
                error=error,
                resource_id=resource_id,
                company_id=company_id,
                extra_data=extra_data,
            )
        except Exception as exc:  # noqa
            logger.error(
                "operation audit write failed",
                exc_info=True,
                extra={
                    "operator_id": getattr(operator, "id", None),
                    "operation_type": operation_type,
                    "resource_type": resource_type,
                    "exception_class": exc.__class__.__name__,
                },
            )

            if cls.is_strict_mode_enabled():
                raise

    @classmethod
    async def record(
            cls,
            *,
            operator: Any | None,
            operation_type: str,
            resource_type: str,
            request: "Request",
            request_data: dict[str, Any] | None = None,
            before_data: dict[str, Any] | None = None,
            after_data: dict[str, Any] | None = None,
            status: str = STATUS_SUCCESS,
            error: BaseException | None = None,
            resource_id: int | None = None,
            company_id: int | None = None,
            extra_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized_status = cls.normalize_status(status)

        error_code = None
        error_message = None

        if error is not None:
            error_code = cls.normalize_optional_int(getattr(error, "numeric_code", None))
            error_message = str(getattr(error, "default_message", "") or str(error) or error.__class__.__name__)[:512]

        data = {
            "operator_id": cls.normalize_optional_int(getattr(operator, "id", None)),
            "operation_type": str(operation_type or "").strip().lower()[:64],
            "resource_type": str(resource_type or "").strip().lower()[:64],
            "company_id": company_id if company_id is not None else cls.normalize_optional_int(getattr(operator, "company_id", None)),
            "resource_id": resource_id,
            "request_method": str(getattr(request, "method", "") or "").strip().upper()[:16],
            "request_path": str(getattr(request, "path", "") or "").strip()[:255],
            "client_ip": cls.get_client_ip(request),
            "user_agent": str(request.headers.get("User-Agent", "") or "").strip()[:512],
            "request_data": cls.sanitize_payload(request_data),
            "before_data": cls.sanitize_payload(before_data),
            "after_data": cls.sanitize_payload(after_data),
            "extra_data": cls.sanitize_payload(extra_data),
            "status": normalized_status,
            "error_code": error_code,
            "error_message": error_message,
            "trace_id": cls.get_trace_id(request),
        }

        return await OperationAuditRepository.create_log(
            data=data,
        )

    @classmethod
    async def list_items(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        request_data = cls.ensure_dict(data)

        page = cls.normalize_page(request_data.get("page", 1))
        page_size = cls.normalize_page_size(request_data.get("page_size", 20))
        filters = cls.build_filters(request_data)

        return await OperationAuditRepository.list_logs(
            page=page,
            page_size=page_size,
            filters=filters,
        )

    @classmethod
    def build_filters(cls, data: dict[str, Any]) -> dict[str, Any]:
        filters: dict[str, Any] = {}

        raw_filters = data.get("filters")
        if isinstance(raw_filters, dict):
            for field, value in raw_filters.items():
                if field not in cls.allowed_filter_fields:
                    continue

                if value in (None, ""):
                    continue

                filters[field] = cls.normalize_filter_value(
                    field=field,
                    value=value,
                )

        direct_fields = (
            "operator_id",
            "operation_type",
            "resource_type",
            "company_id",
            "resource_id",
            "status",
            "trace_id",
        )

        for field in direct_fields:
            value = data.get(field)
            if value in (None, ""):
                continue

            filters[field] = cls.normalize_filter_value(
                field=field,
                value=value,
            )

        return filters

    @classmethod
    def normalize_filter_value(cls, *, field: str, value: Any) -> Any:
        if field in (
                "id",
                "operator_id",
                "company_id",
                "resource_id",
                "error_code",
        ):
            return cls.normalize_positive_int(value, field)

        if field == "status":
            return cls.normalize_status(value)

        if field in (
                "operation_type",
                "resource_type",
        ):
            return str(value or "").strip().lower()

        return str(value or "").strip()

    @staticmethod
    def normalize_status(value: Any) -> str:
        status = str(value or "").strip().upper()

        if status not in (
                OperationAuditService.STATUS_SUCCESS,
                OperationAuditService.STATUS_FAILED,
        ):
            raise IamManagementRequestInvalidError(
                "operation audit status is invalid.",
                details={
                    "status": value,
                    "allowed_values": [
                        OperationAuditService.STATUS_SUCCESS,
                        OperationAuditService.STATUS_FAILED,
                    ],
                },
            )

        return status

    @staticmethod
    def normalize_positive_int(value: Any, field_name: str) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise IamManagementRequestInvalidError(
                f"{field_name} is invalid.",
                details={
                    "field": field_name,
                    "value": value,
                },
            ) from exc

        if parsed <= 0:
            raise IamManagementRequestInvalidError(
                f"{field_name} is invalid.",
                details={
                    "field": field_name,
                    "value": value,
                },
            )

        return parsed

    @staticmethod
    def normalize_optional_int(value: Any) -> int | None:
        if value in (None, ""):
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def extract_resource_id(*, request_data: dict[str, Any] | None = None, result_data: dict[str, Any] | None = None) -> int | None:
        candidates = []

        if isinstance(result_data, dict):
            candidates.extend(
                [
                    result_data.get("id"),
                    result_data.get("resource_id"),
                ]
            )

        if isinstance(request_data, dict):
            candidates.extend(
                [
                    request_data.get("id"),
                    request_data.get("resource_id"),
                ]
            )

        for candidate in candidates:
            try:
                parsed = int(candidate)
            except (TypeError, ValueError):
                continue

            if parsed > 0:
                return parsed

        return None

    @classmethod
    def sanitize_payload(cls, value: Any) -> Any:
        if value is None:
            return None

        if isinstance(value, dict):
            result: dict[str, Any] = {}
            for key, item in value.items():
                key_text = str(key)
                if cls.is_sensitive_key(key_text):
                    result[key_text] = "***"
                    continue

                result[key_text] = cls.sanitize_payload(item)

            return result

        if isinstance(value, list):
            return [
                cls.sanitize_payload(item)
                for item in value
            ]

        if isinstance(value, tuple):
            return [
                cls.sanitize_payload(item)
                for item in value
            ]

        if hasattr(value, "isoformat"):
            return value.isoformat()

        return value

    @classmethod
    def is_sensitive_key(cls, key: str) -> bool:
        normalized_key = str(key or "").strip().lower()

        return any(
            keyword in normalized_key
            for keyword in cls.SENSITIVE_KEYWORDS
        )

    @staticmethod
    def get_client_ip(request: "Request") -> str | None:
        forwarded_for = str(request.headers.get("X-Forwarded-For", "") or "").strip()
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()[:64] or None

        meta = getattr(request, "META", {}) or {}
        remote_addr = str(meta.get("REMOTE_ADDR", "") or "").strip()

        return remote_addr[:64] or None

    @staticmethod
    def get_trace_id(request: "Request") -> str | None:
        trace_id = str(
            request.headers.get("X-Trace-Id")
            or request.headers.get("X-Request-Id")
            or ""
        ).strip()

        return trace_id[:64] or None

    @staticmethod
    def normalize_page(value: Any) -> int:
        try:
            page = int(value)
        except (TypeError, ValueError):
            page = 1

        return max(page, 1)

    @staticmethod
    def normalize_page_size(value: Any) -> int:
        try:
            page_size = int(value)
        except (TypeError, ValueError):
            page_size = 20

        if page_size <= 0:
            return 20

        return min(page_size, 200)

    @staticmethod
    def ensure_dict(data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise IamManagementRequestInvalidError(
                "Request payload must be an object.",
            )

        return dict(data)
