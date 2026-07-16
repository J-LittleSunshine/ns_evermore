# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from .base import NsEvermoreError


_ERROR_ACTION_PATTERN = re.compile(r"[a-z][a-z0-9_]{0,63}")


class NsErrorSeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NsErrorCategory(str, Enum):
    COMMON = "common"
    CONFIGURATION = "configuration"
    VALIDATION = "validation"
    DEPENDENCY = "dependency"
    STATE = "state"
    HTTP = "http"
    RUNTIME = "runtime"
    PROTOCOL = "protocol"
    SECURITY = "security"
    PAYLOAD_REF = "payload_ref"
    DELIVERY = "delivery"
    BACKPRESSURE = "backpressure"
    CLUSTER = "cluster"


@dataclass(frozen=True, slots=True)
class NsErrorDefinition:
    """Default policy hints for one exact exception type.

    Policy flags and ``action`` are not inherited through the Python class
    hierarchy and are not unconditional execution instructions. Callers must
    query with the concrete ``type(error)`` and combine any returned hints
    with the current context, configured policy, and runtime phase. A missing
    exact definition must be handled conservatively.
    """

    error_type: type[NsEvermoreError]
    code: str
    numeric_code: int
    severity: NsErrorSeverity
    category: NsErrorCategory
    retryable: bool
    disconnect_required: bool
    audit_required: bool
    safe_detail: bool
    action: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.error_type, type)
            or not issubclass(self.error_type, NsEvermoreError)
        ):
            raise TypeError("error_type must be an NsEvermoreError class")
        if not isinstance(self.code, str) or not self.code.strip():
            raise ValueError("code must be a non-empty string")
        if self.code != self.error_type.code:
            raise ValueError("definition code must match error_type.code")
        if isinstance(self.numeric_code, bool) or not isinstance(self.numeric_code, int):
            raise TypeError("numeric_code must be a positive integer")
        if self.numeric_code <= 0:
            raise ValueError("numeric_code must be a positive integer")
        if self.numeric_code != self.error_type.numeric_code:
            raise ValueError(
                "definition numeric_code must match error_type.numeric_code"
            )
        if not isinstance(self.severity, NsErrorSeverity):
            raise TypeError("severity must be NsErrorSeverity")
        if not isinstance(self.category, NsErrorCategory):
            raise TypeError("category must be NsErrorCategory")
        for field_name in (
            "retryable",
            "disconnect_required",
            "audit_required",
            "safe_detail",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise TypeError(f"{field_name} must be a boolean")
        if (
            not isinstance(self.action, str)
            or _ERROR_ACTION_PATTERN.fullmatch(self.action) is None
        ):
            raise ValueError(
                "action must be a non-empty lowercase machine-readable value"
            )

    @classmethod
    def for_error_type(
        cls,
        error_type: type[NsEvermoreError],
        *,
        severity: NsErrorSeverity,
        category: NsErrorCategory,
        retryable: bool = False,
        disconnect_required: bool = False,
        audit_required: bool = False,
        safe_detail: bool = False,
        action: str,
    ) -> "NsErrorDefinition":
        if (
            not isinstance(error_type, type)
            or not issubclass(error_type, NsEvermoreError)
        ):
            raise TypeError("error_type must be an NsEvermoreError class")
        return cls(
            error_type=error_type,
            code=error_type.code,
            numeric_code=error_type.numeric_code,
            severity=severity,
            category=category,
            retryable=retryable,
            disconnect_required=disconnect_required,
            audit_required=audit_required,
            safe_detail=safe_detail,
            action=action,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "error_type": self.error_type.__name__,
            "code": self.code,
            "numeric_code": self.numeric_code,
            "severity": self.severity.value,
            "category": self.category.value,
            "retryable": self.retryable,
            "disconnect_required": self.disconnect_required,
            "audit_required": self.audit_required,
            "safe_detail": self.safe_detail,
            "action": self.action,
        }
