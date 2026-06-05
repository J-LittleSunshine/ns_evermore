# -*- coding: utf-8 -*-
from __future__ import annotations

from threading import RLock
from typing import Any

from ns_common.runtime.constants import RUNTIME_NODE_ROLE_SUB
from ns_runtime.connection import NsRuntimeConnection


class NsRuntimeConnectionRegistry:
    """In-process runtime connection registry.

    P7 only tracks backend connector connections and direct sub-node
    connections. Frontend, presence and multi-level runtime topology are
    intentionally deferred.
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._lock = RLock()
        self._connections: dict[str, NsRuntimeConnection] = {}
        self._backend_connections: dict[str, NsRuntimeConnection] = {}
        self._sub_node_connections: dict[str, NsRuntimeConnection] = {}

    def add_unknown(self, connection: NsRuntimeConnection) -> None:
        """Add newly accepted unregistered connection."""
        with self._lock:
            self._connections[connection.connection_id] = connection

    def remove(self, connection_id: str, exc: BaseException | None = None) -> None:
        """Remove connection from all registry indexes."""
        with self._lock:
            connection = self._connections.pop(connection_id, None)
            self._backend_connections.pop(connection_id, None)
            self._sub_node_connections.pop(connection_id, None)

        if connection is not None:
            connection.status = "closed"
            if exc is not None:
                connection.reject_pending_acks(exc)

    def get(self, connection_id: str) -> NsRuntimeConnection | None:
        """Get one connection by id."""
        with self._lock:
            return self._connections.get(connection_id)

    def register_backend(self, connection_id: str, *, payload: dict[str, Any], remote_address: str = "") -> NsRuntimeConnection:
        """Register one backend connector connection."""
        with self._lock:
            connection = self._connections[connection_id]
            instance_id: str = str(payload.get("instance_id") or "").strip() or connection_id

            connection.connection_type = "backend"
            connection.instance_id = instance_id
            connection.service_name = str(payload.get("service_name") or "ns_backend").strip() or "ns_backend"
            connection.version = str(payload.get("version") or "").strip()
            connection.environment = str(payload.get("environment") or "").strip()
            connection.remote_address = remote_address
            connection.mark_seen()

            self._backend_connections[connection_id] = connection
            return connection

    def register_sub_node(self, connection_id: str, *, payload: dict[str, Any], remote_address: str = "") -> NsRuntimeConnection:
        """Register one direct sub runtime node connection."""
        with self._lock:
            connection = self._connections[connection_id]
            node_id: str = str(payload.get("node_id") or "").strip() or connection_id
            node_role: str = str(payload.get("node_role") or "").strip()

            if node_role != RUNTIME_NODE_ROLE_SUB:
                raise ValueError(f"runtime sub connection node_role is invalid: {node_role}")

            connection.connection_type = "runtime_sub"
            connection.node_id = node_id
            connection.node_role = node_role
            connection.remote_address = remote_address
            connection.mark_seen()

            self._sub_node_connections[connection_id] = connection
            return connection

    def refresh_backend(self, connection_id: str, *, health: dict[str, Any] | None = None) -> NsRuntimeConnection | None:
        """Refresh backend connection heartbeat."""
        with self._lock:
            connection = self._backend_connections.get(connection_id)
            if connection is not None:
                connection.mark_seen(health=health)
            return connection

    def refresh_sub_node(self, connection_id: str, *, health: dict[str, Any] | None = None) -> NsRuntimeConnection | None:
        """Refresh sub node heartbeat."""
        with self._lock:
            connection = self._sub_node_connections.get(connection_id)
            if connection is not None:
                connection.mark_seen(health=health)
            return connection

    def list_healthy_sub_nodes(self) -> list[NsRuntimeConnection]:
        """Return currently healthy direct sub-node connections."""
        with self._lock:
            return [
                connection
                for connection in self._sub_node_connections.values()
                if connection.status == "healthy"
            ]

    def count_active(self) -> int:
        """Return active connection count."""
        with self._lock:
            return len(self._connections)

    def count_backend(self) -> int:
        """Return registered backend connection count."""
        with self._lock:
            return len(self._backend_connections)

    def count_sub_nodes(self) -> int:
        """Return registered sub node count."""
        with self._lock:
            return len(self._sub_node_connections)
