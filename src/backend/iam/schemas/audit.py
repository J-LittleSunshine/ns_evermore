# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AuditEvent:
    operation_type: str
    resource_type: str
    operator_id: int | None = None
    company_id: int | None = None
    resource_id: int | None = None
    request_method: str | None = None
    request_path: str | None = None
    client_ip: str | None = None
    user_agent: str | None = None
    request_data: dict[str, Any] | None = None
    before_data: dict[str, Any] | None = None
    after_data: dict[str, Any] | None = None
    status: str = "SUCCESS"
    error_code: int | None = None
    error_message: str | None = None
    trace_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


__all__ = ["AuditEvent"]

