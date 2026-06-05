# -*- coding: utf-8 -*-
from __future__ import annotations

from threading import RLock
from typing import Any

from ns_common.runtime.constants import (
    RUNTIME_NODE_ROLE_SUB,
    RUNTIME_TARGET_BROADCAST,
    RUNTIME_TARGET_CONNECTION,
    RUNTIME_TARGET_ROOM,
    RUNTIME_TARGET_SESSION,
    RUNTIME_TARGET_USER,
)
from ns_common.runtime.messages import NsRuntimeMessage
from ns_runtime.connection import NsRuntimeConnection


class NsRuntimeConnectionRegistry:
    """In-process runtime connection registry.

    P8 tracks backend connector connections, direct sub-node connections and
    local frontend connections. Presence, distributed routing and auth are
    intentionally deferred.
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._lock = RLock()
        self._connections: dict[str, NsRuntimeConnection] = {}
        self._backend_connections: dict[str, NsRuntimeConnection] = {}
        self._backend_by_instance_id: dict[str, str] = {}
        self._sub_node_connections: dict[str, NsRuntimeConnection] = {}

        self._frontend_connections: dict[str, NsRuntimeConnection] = {}
        self._frontend_by_client_id: dict[str, set[str]] = {}
        self._frontend_by_session_id: dict[str, set[str]] = {}
        self._frontend_by_user_id: dict[str, set[str]] = {}
        self._frontend_by_room: dict[str, set[str]] = {}

    def add_unknown(self, connection: NsRuntimeConnection) -> None:
        """Add newly accepted unregistered connection."""
        with self._lock:
            self._connections[connection.connection_id] = connection

    def remove(self, connection_id: str, exc: BaseException | None = None) -> None:
        """Remove connection from all registry indexes."""
        with self._lock:
            connection = self._connections.pop(connection_id, None)
            backend = self._backend_connections.pop(connection_id, None)
            if backend is not None and backend.instance_id:
                self._backend_by_instance_id.pop(backend.instance_id, None)
            self._sub_node_connections.pop(connection_id, None)

            if connection is not None:
                self._remove_frontend_indexes(connection)

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
            self._backend_by_instance_id[instance_id] = connection_id
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

    def register_frontend(self, connection_id: str, *, payload: dict[str, Any], remote_address: str = "") -> NsRuntimeConnection:
        """Register one frontend WebSocket connection."""
        with self._lock:
            connection = self._connections[connection_id]

            self._remove_frontend_indexes(connection)

            client_id = self._normalize_optional(payload.get("client_id")) or connection_id
            session_id = self._normalize_optional(payload.get("session_id"))
            user_id = self._normalize_optional(payload.get("user_id"))
            rooms = self._normalize_rooms(payload.get("rooms"))

            connection.connection_type = "frontend"
            connection.client_id = client_id
            connection.session_id = session_id
            connection.user_id = user_id
            connection.rooms = rooms
            connection.device = self._normalize_optional(payload.get("device")) or ""
            connection.version = self._normalize_optional(payload.get("version")) or ""
            connection.remote_address = remote_address
            connection.mark_seen()

            self._frontend_connections[connection_id] = connection
            self._add_index(self._frontend_by_client_id, client_id, connection_id)

            if session_id is not None:
                self._add_index(self._frontend_by_session_id, session_id, connection_id)

            if user_id is not None:
                self._add_index(self._frontend_by_user_id, user_id, connection_id)

            for room in rooms:
                self._add_index(self._frontend_by_room, room, connection_id)

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

    def refresh_frontend(self, connection_id: str, *, health: dict[str, Any] | None = None) -> NsRuntimeConnection | None:
        """Refresh frontend connection heartbeat."""
        with self._lock:
            connection = self._frontend_connections.get(connection_id)
            if connection is not None:
                connection.mark_seen(health=health)
            return connection

    def join_frontend_rooms(self, connection_id: str, rooms: set[str] | list[str] | tuple[str, ...]) -> NsRuntimeConnection | None:
        """Add rooms to one registered frontend connection."""
        with self._lock:
            connection = self._frontend_connections.get(connection_id)
            if connection is None:
                return None

            normalized_rooms = self._normalize_rooms(rooms)
            for room in normalized_rooms:
                if room in connection.rooms:
                    continue

                connection.rooms.add(room)
                self._add_index(self._frontend_by_room, room, connection_id)

            connection.mark_seen()
            return connection

    def leave_frontend_rooms(self, connection_id: str, rooms: set[str] | list[str] | tuple[str, ...]) -> NsRuntimeConnection | None:
        """Remove rooms from one registered frontend connection."""
        with self._lock:
            connection = self._frontend_connections.get(connection_id)
            if connection is None:
                return None

            normalized_rooms = self._normalize_rooms(rooms)
            for room in normalized_rooms:
                if room not in connection.rooms:
                    continue

                connection.rooms.discard(room)
                self._remove_index(self._frontend_by_room, room, connection_id)

            connection.mark_seen()
            return connection

    def select_backend_for_reply(self, target_backend_id: str | None = None) -> NsRuntimeConnection | None:
        """Select backend connection for backend.reply delivery."""
        with self._lock:
            if target_backend_id:
                connection_id = self._backend_by_instance_id.get(str(target_backend_id).strip())
                if connection_id:
                    connection = self._backend_connections.get(connection_id)
                    if connection is not None and connection.status == "healthy":
                        return connection
                return None

            for connection in self._backend_connections.values():
                if connection.status == "healthy":
                    return connection

            return None

    def list_healthy_sub_nodes(self) -> list[NsRuntimeConnection]:
        """Return currently healthy direct sub-node connections."""
        with self._lock:
            return [
                connection
                for connection in self._sub_node_connections.values()
                if connection.status == "healthy"
            ]

    def list_frontend_targets(self, message: NsRuntimeMessage) -> list[NsRuntimeConnection]:
        """Return local frontend connections matched by message target."""
        normalized_message = message.normalized()
        target_type = str(normalized_message.target_type or "").strip()
        target_id = self._normalize_optional(normalized_message.target_id)

        with self._lock:
            if target_type == RUNTIME_TARGET_BROADCAST:
                return self._healthy_frontend_connections(list(self._frontend_connections.keys()))

            if target_id is None:
                return []

            connection_ids: set[str] = set()

            if target_type == RUNTIME_TARGET_CONNECTION:
                if target_id in self._frontend_connections:
                    connection_ids.add(target_id)
                connection_ids.update(self._frontend_by_client_id.get(target_id, set()))

            elif target_type == RUNTIME_TARGET_SESSION:
                connection_ids.update(self._frontend_by_session_id.get(target_id, set()))

            elif target_type == RUNTIME_TARGET_USER:
                connection_ids.update(self._frontend_by_user_id.get(target_id, set()))

            elif target_type == RUNTIME_TARGET_ROOM:
                connection_ids.update(self._frontend_by_room.get(target_id, set()))

            else:
                # resource 等目标类型 P8 暂不映射到本地 frontend 连接。
                return []

            return self._healthy_frontend_connections(list(connection_ids))

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

    def count_frontend(self) -> int:
        """Return registered frontend connection count."""
        with self._lock:
            return len(self._frontend_connections)

    def _healthy_frontend_connections(self, connection_ids: list[str]) -> list[NsRuntimeConnection]:
        """Return unique healthy frontend connections by connection ids."""
        result: list[NsRuntimeConnection] = []
        seen: set[str] = set()

        for connection_id in connection_ids:
            if connection_id in seen:
                continue

            seen.add(connection_id)
            connection = self._frontend_connections.get(connection_id)
            if connection is not None and connection.status == "healthy":
                result.append(connection)

        return result

    def _remove_frontend_indexes(self, connection: NsRuntimeConnection) -> None:
        """Remove one frontend connection from all frontend indexes."""
        connection_id = connection.connection_id
        self._frontend_connections.pop(connection_id, None)

        if connection.client_id:
            self._remove_index(self._frontend_by_client_id, connection.client_id, connection_id)

        if connection.session_id:
            self._remove_index(self._frontend_by_session_id, connection.session_id, connection_id)

        if connection.user_id:
            self._remove_index(self._frontend_by_user_id, connection.user_id, connection_id)

        for room in set(connection.rooms or set()):
            self._remove_index(self._frontend_by_room, room, connection_id)

    @staticmethod
    def _add_index(index: dict[str, set[str]], key: str, connection_id: str) -> None:
        """Add connection id to one secondary index."""
        normalized_key = str(key or "").strip()
        if not normalized_key:
            return

        index.setdefault(normalized_key, set()).add(connection_id)

    @staticmethod
    def _remove_index(index: dict[str, set[str]], key: str, connection_id: str) -> None:
        """Remove connection id from one secondary index."""
        normalized_key = str(key or "").strip()
        if not normalized_key:
            return

        connection_ids = index.get(normalized_key)
        if connection_ids is None:
            return

        connection_ids.discard(connection_id)
        if not connection_ids:
            index.pop(normalized_key, None)

    @staticmethod
    def _normalize_optional(value: Any) -> str | None:
        """Normalize optional string identifier."""
        if value is None:
            return None

        normalized = str(value).strip()
        return normalized or None

    @classmethod
    def _normalize_rooms(cls, value: Any) -> set[str]:
        """Normalize frontend room list."""
        if value is None:
            return set()

        if isinstance(value, str):
            normalized = cls._normalize_optional(value)
            return {normalized} if normalized else set()

        if isinstance(value, list | tuple | set):
            rooms: set[str] = set()
            for item in value:
                normalized = cls._normalize_optional(item)
                if normalized:
                    rooms.add(normalized)
            return rooms

        return set()
