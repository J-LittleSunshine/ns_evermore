# -*- coding: utf-8 -*-
"""Standard runtime.error Envelope construction from ERR-1 metadata."""

from __future__ import annotations

from dataclasses import dataclass

from ns_common.exceptions import (
    NsRuntimeError,
    get_error_definition,
)
from ns_common.security import Sanitizer

from .models import (
    Envelope,
    MessageGroup,
    PayloadGroup,
    ProtocolGroup,
    SourceGroup,
    TargetGroup,
    TraceGroup,
)


@dataclass(frozen=True, slots=True)
class ErrorEnvelopeContext:
    protocol: ProtocolGroup
    source: SourceGroup
    error_message_id: str
    created_at: str
    target: TargetGroup | None = None
    trace: TraceGroup | None = None
    referenced_message_id: str | None = None
    referenced_delivery_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.protocol, ProtocolGroup):
            raise TypeError("protocol must be ProtocolGroup")
        if not isinstance(self.source, SourceGroup):
            raise TypeError("source must be SourceGroup")
        for name in ("error_message_id", "created_at"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{name} must be a non-empty string")
        if self.target is not None and not isinstance(self.target, TargetGroup):
            raise TypeError("target must be TargetGroup or None")
        if self.trace is not None and not isinstance(self.trace, TraceGroup):
            raise TypeError("trace must be TraceGroup or None")
        for name in ("referenced_message_id", "referenced_delivery_id"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or not value):
                raise ValueError(f"{name} must be a non-empty string or None")


class ErrorEnvelopeBuilder:
    """Build a safe error response without reading exception content."""

    def __init__(self, *, sanitizer: Sanitizer) -> None:
        if not isinstance(sanitizer, Sanitizer):
            raise TypeError("sanitizer must be Sanitizer")
        self._sanitizer = sanitizer

    def build(
        self,
        error: BaseException,
        *,
        context: ErrorEnvelopeContext,
    ) -> Envelope:
        if isinstance(error, (KeyboardInterrupt, SystemExit)):
            raise error
        if not isinstance(error, BaseException):
            raise TypeError("error must be BaseException")
        if not isinstance(context, ErrorEnvelopeContext):
            raise TypeError("context must be ErrorEnvelopeContext")

        definition = get_error_definition(type(error))
        if definition is None:
            definition = get_error_definition(NsRuntimeError)
        if definition is None:  # ERR-1 registry corruption must fail closed.
            raise RuntimeError("ERR-1 generic runtime definition is unavailable")

        detail = self._sanitizer.sanitize(
            {"action": definition.action},
            field_name="error_detail",
        )
        if not isinstance(detail, dict):
            detail = {"action": "report_runtime_error"}

        payload: dict[str, object] = {
            "error_code": definition.code,
            "numeric_code": definition.numeric_code,
            "message": definition.error_type.default_message,
            "severity": definition.severity.value,
            "category": definition.category.value,
            "retryable": definition.retryable,
            "disconnect_required": definition.disconnect_required,
            "audit_required": definition.audit_required,
            "action": definition.action,
            "detail": detail,
        }
        if context.referenced_message_id is not None:
            payload["message_id"] = self._safe_reference(
                context.referenced_message_id,
                "message_id",
            )
        if context.referenced_delivery_id is not None:
            payload["delivery_id"] = self._safe_reference(
                context.referenced_delivery_id,
                "delivery_id",
            )

        return Envelope(
            protocol=context.protocol,
            message=MessageGroup(
                message_id=context.error_message_id,
                type="runtime.error",
                category="error",
                priority=0,
                created_at=context.created_at,
                reliability="best_effort",
            ),
            source=context.source,
            target=context.target,
            payload=PayloadGroup(mode="inline", inline=payload),
            trace=context.trace,
        )

    def _safe_reference(self, value: str, field_name: str) -> str:
        sanitized = self._sanitizer.sanitize(value, field_name=field_name)
        if not isinstance(sanitized, str) or not sanitized:
            return "[REDACTED]"
        return sanitized


__all__ = ("ErrorEnvelopeBuilder", "ErrorEnvelopeContext")
