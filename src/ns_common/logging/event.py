# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class NsLogEventData:
    event: str
    message: str
    trace_id: str | None = None
    user_id: int | None = None
    error_code: int | None = None
    context: dict[str, Any] = field(default_factory=dict)


__all__ = ["NsLogEventData"]

