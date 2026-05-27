# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass

from ns_runtime.endpoints import RuntimeEndpoint
from ns_runtime.packets import RuntimePacket
from ns_runtime.tasks import RuntimeTask


@dataclass(frozen=True)
class RuntimeTaskDispatchResult:
    # Phase 6A 仅负责任务下发，不处理 executor accept_ack。
    task: RuntimeTask
    packet: RuntimePacket
    selected_endpoint: RuntimeEndpoint | None
    dispatched: bool
    reason: str | None = None


