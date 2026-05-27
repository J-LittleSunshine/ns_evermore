# -*- coding: utf-8 -*-
from __future__ import annotations

from enum import Enum


class RuntimeTaskStatus(str, Enum):
    # 本阶段仅使用 CREATED/QUEUED，其他状态为后续 dispatcher、executor、retry、dlq 能力预留。
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    DISPATCHING = "DISPATCHING"
    ACCEPTED = "ACCEPTED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"
    DEAD_LETTER = "DEAD_LETTER"

