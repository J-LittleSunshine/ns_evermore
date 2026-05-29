# -*- coding: utf-8 -*-
from __future__ import annotations

from threading import RLock

from ns_runtime.endpoints.endpoint import RuntimeEndpoint


class EndpointRegistry:
    def __init__(self) -> None:
        self._lock = RLock()
        self._endpoints: dict[str, RuntimeEndpoint] = {}

    def register(self, endpoint: RuntimeEndpoint) -> RuntimeEndpoint:
        with self._lock:
            self._endpoints[endpoint.endpoint_id] = endpoint
            return endpoint

    def unregister(self, endpoint_id: str) -> None:
        with self._lock:
            self._endpoints.pop(endpoint_id, None)

    def get(self, endpoint_id: str) -> RuntimeEndpoint | None:
        with self._lock:
            return self._endpoints.get(endpoint_id)

    def list_all(self) -> tuple[RuntimeEndpoint, ...]:
        with self._lock:
            return tuple(self._endpoints.values())

    def heartbeat(self, endpoint_id: str) -> RuntimeEndpoint:
        with self._lock:
            endpoint = self._endpoints.get(endpoint_id)
            if endpoint is None:
                raise KeyError(f"endpoint not found: {endpoint_id}")
            updated = endpoint.heartbeat()
            self._endpoints[endpoint_id] = updated
            return updated

    def mark_offline(self, endpoint_id: str) -> RuntimeEndpoint:
        with self._lock:
            endpoint = self._endpoints.get(endpoint_id)
            if endpoint is None:
                raise KeyError(f"endpoint not found: {endpoint_id}")
            updated = endpoint.mark_offline()
            self._endpoints[endpoint_id] = updated
            return updated

    def find_by_capability(self, capability: str) -> tuple[RuntimeEndpoint, ...]:
        lookup = capability.strip()
        if not lookup:
            return ()

        with self._lock:
            matched = [
                endpoint
                for endpoint in self._endpoints.values()
                if lookup in endpoint.capabilities
            ]
            return tuple(matched)

