# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from ns_runtime.packets.enums import RuntimeEndpointStatus, RuntimeEndpointType


@dataclass(frozen=True)
class RuntimeEndpoint:
    endpoint_id: str
    endpoint_type: RuntimeEndpointType
    capabilities: tuple[str, ...]
    metadata: dict[str, Any]
    status: RuntimeEndpointStatus
    registered_at: datetime
    last_seen_at: datetime

    @classmethod
    def create(
        cls,
        *,
        endpoint_id: str,
        endpoint_type: RuntimeEndpointType,
        capabilities: Iterable[str] = (),
        metadata: Mapping[str, Any] | None = None,
    ) -> RuntimeEndpoint:
        now = datetime.now(timezone.utc)
        unique_capabilities = _normalize_capabilities(capabilities)
        return cls(
            endpoint_id=str(endpoint_id).strip(),
            endpoint_type=endpoint_type,
            capabilities=unique_capabilities,
            metadata=dict(metadata or {}),
            status=RuntimeEndpointStatus.ONLINE,
            registered_at=now,
            last_seen_at=now,
        )

    def heartbeat(self) -> RuntimeEndpoint:
        return replace(
            self,
            last_seen_at=datetime.now(timezone.utc),
            status=RuntimeEndpointStatus.ONLINE,
        )

    def mark_offline(self) -> RuntimeEndpoint:
        return replace(self, status=RuntimeEndpointStatus.OFFLINE)


def _normalize_capabilities(values: Iterable[str]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return tuple(result)

