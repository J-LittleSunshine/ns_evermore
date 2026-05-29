# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ns_common.protocol import RuntimeEndpointType


@dataclass(frozen=True)
class ExecutorClientConfig:
    endpoint_id: str
    gateway_url: str
    endpoint_type: RuntimeEndpointType = RuntimeEndpointType.EXECUTOR
    capabilities: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    heartbeat_interval_seconds: float = 5.0
    outbound_poll_interval_seconds: float = 0.1
    reconnect_interval_seconds: float = 3.0
    stop_message_type: str = "stop"

    def __post_init__(self) -> None:
        endpoint_id = str(self.endpoint_id).strip()
        gateway_url = str(self.gateway_url).strip()
        stop_message_type = str(self.stop_message_type).strip() or "stop"

        if not endpoint_id:
            raise ValueError("endpoint_id must be non-empty")
        if not gateway_url:
            raise ValueError("gateway_url must be non-empty")
        if not (gateway_url.startswith("ws://") or gateway_url.startswith("wss://")):
            raise ValueError("gateway_url must start with ws:// or wss://")
        if self.heartbeat_interval_seconds <= 0:
            raise ValueError("heartbeat_interval_seconds must be > 0")
        if self.outbound_poll_interval_seconds <= 0:
            raise ValueError("outbound_poll_interval_seconds must be > 0")
        if self.reconnect_interval_seconds <= 0:
            raise ValueError("reconnect_interval_seconds must be > 0")

        normalized_capabilities = _normalize_capabilities(self.capabilities)

        # 该配置属于 executor client 的独立配置，不依赖 Django settings。
        object.__setattr__(self, "endpoint_id", endpoint_id)
        object.__setattr__(self, "gateway_url", gateway_url)
        object.__setattr__(self, "capabilities", normalized_capabilities)
        object.__setattr__(self, "metadata", dict(self.metadata))
        object.__setattr__(self, "stop_message_type", stop_message_type)


def _normalize_capabilities(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return tuple(result)

