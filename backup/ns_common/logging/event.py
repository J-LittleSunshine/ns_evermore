# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class NsLogEventData:
    event: str
    message: str
    component: str | None = None
    log_name: str | None = None
    trace_id: str | None = None
    request_id: str | None = None
    connection_id: str | None = None
    user_id: int | str | None = None
    session_id: str | None = None
    error_code: int | None = None
    level: str = "INFO"
    pid: int | None = None
    context: dict[str, Any] = field(default_factory=dict)


def get_current_pid() -> int:
    return os.getpid()


__all__ = ["NsLogEventData", "get_current_pid"]

