# -*- coding: utf-8 -*-
from __future__ import annotations

import time
from dataclasses import dataclass, replace
from threading import RLock
from typing import Any, Protocol

from ns_common.runtime.config import NsRuntimeConfig
from ns_common.runtime.constants import RUNTIME_BACKEND_MEMORY
from ns_common.runtime.errors import NsRuntimeConfigurationError
from ns_runtime.connection import NsRuntimeConnection

RUNTIME_PRESENCE_STATUS_ONLINE = "online"
RUNTIME_PRESENCE_STATUS_OFFLINE = "offline"


@dataclass(slots=True, frozen=True, kw_only=True)
class NsRuntimePresenceRecord:
    """Runtime connection presence snapshot.

    P12-A keeps presence local to one runtime process. It is intentionally a
    connection-level record so future Redis/ValKey presence can reuse the same
    contract without coupling to Django or backend IAM ORM models.
    """

    node_id: str
    connection_id: str
    connection_type: str
    status: str

    principal_type: str | None = None
    principal_id: str | None = None

    user_id: str | None = None
    client_id: str | None = None
    session_id: str | None = None
    backend_id: str | None = None
    service_id: str | None = None
    runtime_node_id: str | None = None

    rooms: tuple[str, ...] = ()

    remote_address: str = ""
    connected_at_epoch_ms: int = 0
    last_seen_epoch_ms: int = 0

    health: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize presence record to a JSON-compatible dict."""
        return {
            "node_id": self.node_id,
            "connection_id": self.connection_id,
            "connection_type": self.connection_type,
            "status": self.status,
            "principal_type": self.principal_type,
            "principal_id": self.principal_id,
            "user_id": self.user_id,
            "client_id": self.client_id,
            "session_id": self.session_id,
            "backend_id": self.backend_id,
            "service_id": self.service_id,
            "runtime_node_id": self.runtime_node_id,
            "rooms": list(self.rooms),
            "remote_address": self.remote_address,
            "connected_at_epoch_ms": int(self.connected_at_epoch_ms),
            "last_seen_epoch_ms": int(self.last_seen_epoch_ms),
            "health": dict(self.health or {}),
            "metadata": dict(self.metadata or {}),
        }


class NsRuntimePresenceStore(Protocol):
    """Runtime presence store protocol.

    P12-A implements only memory presence. Redis/ValKey backends will implement
    this protocol later without changing ns_runtime.core lifecycle hooks.
    """

    def upsert_connection(self, connection: NsRuntimeConnection, *, node_id: str) -> NsRuntimePresenceRecord:
        """Insert or update one online connection presence record."""

    def refresh_connection(self, connection_id: str, *, last_seen_epoch_ms: int | None = None, health: dict[str, Any] | None = None) -> NsRuntimePresenceRecord | None:
        """Refresh last_seen / health for one online connection."""

    def remove_connection(self, connection_id: str) -> NsRuntimePresenceRecord | None:
        """Remove one connection from online presence indexes."""

    def get_connection(self, connection_id: str) -> NsRuntimePresenceRecord | None:
        """Return one online presence record by connection id."""

    def list_online_frontends(self) -> list[NsRuntimePresenceRecord]:
        """Return online frontend presence records."""

    def list_online_backends(self) -> list[NsRuntimePresenceRecord]:
        """Return online backend presence records."""

    def list_online_runtime_sub_nodes(self) -> list[NsRuntimePresenceRecord]:
        """Return online runtime sub-node presence records."""

    def list_online_by_user(self, user_id: str) -> list[NsRuntimePresenceRecord]:
        """Return online frontend presence records for one user."""

    def list_online_by_session(self, session_id: str) -> list[NsRuntimePresenceRecord]:
        """Return online frontend presence records for one session."""

    def list_online_by_client(self, client_id: str) -> list[NsRuntimePresenceRecord]:
        """Return online frontend presence records for one client."""

    def list_online_by_room(self, room_id: str) -> list[NsRuntimePresenceRecord]:
        """Return online frontend presence records for one room."""

    def count_online(self) -> int:
        """Return online connection count."""

    def snapshot_counts(self) -> dict[str, int]:
        """Return online presence counters."""


class MemoryRuntimePresenceStore:
    """In-process memory runtime presence store.

    Scope:
    - local runtime process only
    - no cross-node consistency
    - no persistence
    - no Redis/ValKey dependency

    This is the default development and standalone runtime presence backend.
    """

    def __init__(self) -> None:
        """Initialize empty local presence store."""
        self._lock = RLock()
        self._records: dict[str, NsRuntimePresenceRecord] = {}

        self._frontend_connections: set[str] = set()
        self._backend_connections: set[str] = set()
        self._runtime_sub_connections: set[str] = set()

        self._frontend_by_user_id: dict[str, set[str]] = {}
        self._frontend_by_session_id: dict[str, set[str]] = {}
        self._frontend_by_client_id: dict[str, set[str]] = {}
        self._frontend_by_room_id: dict[str, set[str]] = {}

    def upsert_connection(self, connection: NsRuntimeConnection, *, node_id: str) -> NsRuntimePresenceRecord:
        """Insert or update one online connection presence record."""
        normalized_node_id = str(node_id or "").strip()
        if not normalized_node_id:
            raise ValueError("runtime presence node_id is required")

        with self._lock:
            old_record = self._records.get(connection.connection_id)
            if old_record is not None:
                self._remove_indexes(old_record)

            record = self._record_from_connection(
                connection,
                node_id=normalized_node_id,
                connected_at_epoch_ms=old_record.connected_at_epoch_ms if old_record is not None else connection.registered_at_epoch_ms,
            )
            self._records[record.connection_id] = record
            self._add_indexes(record)
            return record

    def refresh_connection(self, connection_id: str, *, last_seen_epoch_ms: int | None = None, health: dict[str, Any] | None = None) -> NsRuntimePresenceRecord | None:
        """Refresh last_seen / health for one online connection."""
        normalized_connection_id = str(connection_id or "").strip()
        if not normalized_connection_id:
            return None

        with self._lock:
            record = self._records.get(normalized_connection_id)
            if record is None:
                return None

            refreshed_record = replace(
                record,
                last_seen_epoch_ms=int(last_seen_epoch_ms or int(time.time() * 1000)),
                health=dict(health or record.health or {}),
            )
            self._records[normalized_connection_id] = refreshed_record
            return refreshed_record

    def remove_connection(self, connection_id: str) -> NsRuntimePresenceRecord | None:
        """Remove one connection from online presence indexes."""
        normalized_connection_id = str(connection_id or "").strip()
        if not normalized_connection_id:
            return None

        with self._lock:
            record = self._records.pop(normalized_connection_id, None)
            if record is None:
                return None

            self._remove_indexes(record)
            return replace(
                record,
                status=RUNTIME_PRESENCE_STATUS_OFFLINE,
                last_seen_epoch_ms=int(time.time() * 1000),
            )

    def get_connection(self, connection_id: str) -> NsRuntimePresenceRecord | None:
        """Return one online presence record by connection id."""
        normalized_connection_id = str(connection_id or "").strip()
        if not normalized_connection_id:
            return None

        with self._lock:
            return self._records.get(normalized_connection_id)

    def list_online_frontends(self) -> list[NsRuntimePresenceRecord]:
        """Return online frontend presence records."""
        with self._lock:
            return self._records_by_connection_ids(self._frontend_connections)

    def list_online_backends(self) -> list[NsRuntimePresenceRecord]:
        """Return online backend presence records."""
        with self._lock:
            return self._records_by_connection_ids(self._backend_connections)

    def list_online_runtime_sub_nodes(self) -> list[NsRuntimePresenceRecord]:
        """Return online runtime sub-node presence records."""
        with self._lock:
            return self._records_by_connection_ids(self._runtime_sub_connections)

    def list_online_by_user(self, user_id: str) -> list[NsRuntimePresenceRecord]:
        """Return online frontend presence records for one user."""
        normalized_user_id = self._normalize_optional(user_id)
        if normalized_user_id is None:
            return []

        with self._lock:
            return self._records_by_connection_ids(self._frontend_by_user_id.get(normalized_user_id, set()))

    def list_online_by_session(self, session_id: str) -> list[NsRuntimePresenceRecord]:
        """Return online frontend presence records for one session."""
        normalized_session_id = self._normalize_optional(session_id)
        if normalized_session_id is None:
            return []

        with self._lock:
            return self._records_by_connection_ids(self._frontend_by_session_id.get(normalized_session_id, set()))

    def list_online_by_client(self, client_id: str) -> list[NsRuntimePresenceRecord]:
        """Return online frontend presence records for one client."""
        normalized_client_id = self._normalize_optional(client_id)
        if normalized_client_id is None:
            return []

        with self._lock:
            return self._records_by_connection_ids(self._frontend_by_client_id.get(normalized_client_id, set()))

    def list_online_by_room(self, room_id: str) -> list[NsRuntimePresenceRecord]:
        """Return online frontend presence records for one room."""
        normalized_room_id = self._normalize_optional(room_id)
        if normalized_room_id is None:
            return []

        with self._lock:
            return self._records_by_connection_ids(self._frontend_by_room_id.get(normalized_room_id, set()))

    def count_online(self) -> int:
        """Return online connection count."""
        with self._lock:
            return len(self._records)

    def snapshot_counts(self) -> dict[str, int]:
        """Return online presence counters."""
        with self._lock:
            online_user_ids = {
                record.user_id
                for record in self._records_by_connection_ids(self._frontend_connections)
                if record.user_id is not None
            }
            return {
                "online_connections": len(self._records),
                "online_frontends": len(self._frontend_connections),
                "online_backends": len(self._backend_connections),
                "online_runtime_sub_nodes": len(self._runtime_sub_connections),
                "online_users": len(online_user_ids),
            }

    def _add_indexes(self, record: NsRuntimePresenceRecord) -> None:
        """Add record to connection-type and frontend secondary indexes."""
        if record.connection_type == "frontend":
            self._frontend_connections.add(record.connection_id)

            if record.user_id is not None:
                self._add_index(self._frontend_by_user_id, record.user_id, record.connection_id)

            if record.session_id is not None:
                self._add_index(self._frontend_by_session_id, record.session_id, record.connection_id)

            if record.client_id is not None:
                self._add_index(self._frontend_by_client_id, record.client_id, record.connection_id)

            for room_id in record.rooms:
                self._add_index(self._frontend_by_room_id, room_id, record.connection_id)

            return

        if record.connection_type == "backend":
            self._backend_connections.add(record.connection_id)
            return

        if record.connection_type == "runtime_sub":
            self._runtime_sub_connections.add(record.connection_id)

    def _remove_indexes(self, record: NsRuntimePresenceRecord) -> None:
        """Remove record from all presence indexes."""
        self._frontend_connections.discard(record.connection_id)
        self._backend_connections.discard(record.connection_id)
        self._runtime_sub_connections.discard(record.connection_id)

        if record.user_id is not None:
            self._remove_index(self._frontend_by_user_id, record.user_id, record.connection_id)

        if record.session_id is not None:
            self._remove_index(self._frontend_by_session_id, record.session_id, record.connection_id)

        if record.client_id is not None:
            self._remove_index(self._frontend_by_client_id, record.client_id, record.connection_id)

        for room_id in record.rooms:
            self._remove_index(self._frontend_by_room_id, room_id, record.connection_id)

    def _records_by_connection_ids(self, connection_ids: set[str]) -> list[NsRuntimePresenceRecord]:
        """Return online records by connection ids."""
        result: list[NsRuntimePresenceRecord] = []
        for connection_id in list(connection_ids):
            record = self._records.get(connection_id)
            if record is not None and record.status == RUNTIME_PRESENCE_STATUS_ONLINE:
                result.append(record)
        return result

    @classmethod
    def _record_from_connection(cls, connection: NsRuntimeConnection, *, node_id: str, connected_at_epoch_ms: int) -> NsRuntimePresenceRecord:
        """Build presence record from runtime connection state."""
        principal = connection.principal

        return NsRuntimePresenceRecord(
            node_id=node_id,
            connection_id=connection.connection_id,
            connection_type=connection.connection_type,
            status=RUNTIME_PRESENCE_STATUS_ONLINE,
            principal_type=principal.principal_type if principal is not None else None,
            principal_id=principal.principal_id if principal is not None else None,
            user_id=cls._normalize_optional(connection.user_id) or (cls._normalize_optional(principal.user_id) if principal is not None else None),
            client_id=cls._normalize_optional(connection.client_id) or (cls._normalize_optional(principal.client_id) if principal is not None else None),
            session_id=cls._normalize_optional(connection.session_id) or (cls._normalize_optional(principal.session_id) if principal is not None else None),
            backend_id=cls._normalize_optional(connection.instance_id) or (cls._normalize_optional(principal.backend_id) if principal is not None else None),
            service_id=cls._normalize_optional(connection.service_name) or (cls._normalize_optional(principal.service_id) if principal is not None else None),
            runtime_node_id=cls._normalize_optional(connection.node_id) or (cls._normalize_optional(principal.node_id) if principal is not None else None),
            rooms=tuple(sorted(str(room).strip() for room in set(connection.rooms or set()) if str(room).strip())),
            remote_address=str(connection.remote_address or ""),
            connected_at_epoch_ms=int(connected_at_epoch_ms or int(time.time() * 1000)),
            last_seen_epoch_ms=int(connection.last_seen_epoch_ms or int(time.time() * 1000)),
            health=dict(connection.health or {}),
            metadata={
                "node_role": connection.node_role,
                "version": connection.version,
                "environment": connection.environment,
                "device": connection.device,
            },
        )

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
        """Normalize optional text identifier."""
        if value is None:
            return None

        normalized = str(value).strip()
        return normalized or None


def build_runtime_presence_store(config: NsRuntimeConfig | None = None) -> NsRuntimePresenceStore:
    """Build runtime presence store from runtime config.

    P12-D keeps presence backend extensibility explicit:
    - memory is implemented now
    - redis / valkey / sql_wal are reserved extension points
    - unimplemented backends fail fast with a configuration error
    """
    if config is None:
        from ns_common.config import ns_config

        config = ns_config.runtime_config

    backend = str(config.resolved_runtime_presence_backend() or RUNTIME_BACKEND_MEMORY).strip().lower()

    # Keep implementation availability centralized in NsRuntimeConfig so direct
    # config.validate() and runtime factory startup have the same semantics.
    config.ensure_runtime_presence_backend_implemented()

    if backend == RUNTIME_BACKEND_MEMORY:
        return MemoryRuntimePresenceStore()

    raise NsRuntimeConfigurationError(f"runtime presence backend is not implemented yet: {backend}")
