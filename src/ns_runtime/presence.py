# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import time
from dataclasses import dataclass, replace
from threading import RLock
from typing import Any, Protocol, Callable

from ns_common.runtime.config import NsRuntimeConfig
from ns_common.runtime.constants import (
    RUNTIME_BACKEND_MEMORY,
    RUNTIME_BACKEND_REDIS,
    RUNTIME_BACKEND_VALKEY,
)
from ns_common.runtime.errors import NsRuntimeConfigurationError, NsRuntimePresenceError
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

    P12-A implements only memory presence. Redis/ValKey backends implement
    this protocol without changing ns_runtime.core lifecycle hooks.
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


class RedisRuntimePresenceStore:
    """Redis/ValKey distributed runtime presence store.

    Scope:
    - cross-process visibility through Redis/ValKey
    - JSON connection records
    - set-based secondary indexes
    - TTL-based connection lease
    - opportunistic stale index cleanup on reads

    P14-C adds a dedicated presence error boundary. It intentionally does not
    implement Lua atomicity or distributed locks.
    """

    DEFAULT_URL = "redis://127.0.0.1:6379/0"
    DEFAULT_KEY_PREFIX = "ns:runtime:presence"

    def __init__(self, *, url: str = "", key_prefix: str = DEFAULT_KEY_PREFIX, record_ttl_seconds: int = 90, socket_timeout: float = 3.0, socket_connect_timeout: float = 3.0, health_check_interval: int = 30) -> None:
        """Initialize Redis/ValKey presence store."""
        normalized_key_prefix = str(key_prefix or "").strip().strip(":")
        self._url: str = str(url or "").strip() or self.DEFAULT_URL
        self._key_prefix: str = normalized_key_prefix or self.DEFAULT_KEY_PREFIX
        self._record_ttl_seconds: int = max(int(record_ttl_seconds), 1)
        self._socket_timeout: float = float(socket_timeout)
        self._socket_connect_timeout: float = float(socket_connect_timeout)
        self._health_check_interval: int = int(health_check_interval)
        self._lock = RLock()
        self._client: Any | None = None

    def upsert_connection(self, connection: NsRuntimeConnection, *, node_id: str) -> NsRuntimePresenceRecord:
        """Insert or update one online connection presence record."""
        normalized_node_id = str(node_id or "").strip()
        if not normalized_node_id:
            raise ValueError("runtime presence node_id is required")

        normalized_connection_id = str(connection.connection_id or "").strip()
        if not normalized_connection_id:
            raise ValueError("runtime presence connection_id is required")

        old_record = self.get_connection(normalized_connection_id)
        record = MemoryRuntimePresenceStore._record_from_connection(
            connection,
            node_id=normalized_node_id,
            connected_at_epoch_ms=old_record.connected_at_epoch_ms if old_record is not None else connection.registered_at_epoch_ms,
        )

        cleanup_keys = self._replace_record_with_pipeline(old_record, record)
        self._delete_empty_index_keys(cleanup_keys)
        return record

    def refresh_connection(self, connection_id: str, *, last_seen_epoch_ms: int | None = None, health: dict[str, Any] | None = None) -> NsRuntimePresenceRecord | None:
        """Refresh last_seen / health for one online connection."""
        normalized_connection_id = str(connection_id or "").strip()
        if not normalized_connection_id:
            return None

        record = self.get_connection(normalized_connection_id)
        if record is None:
            return None

        refreshed_record = replace(
            record,
            last_seen_epoch_ms=int(last_seen_epoch_ms or int(time.time() * 1000)),
            health=dict(health or record.health or {}),
        )
        self._refresh_record_with_pipeline(refreshed_record)
        return refreshed_record

    def remove_connection(self, connection_id: str) -> NsRuntimePresenceRecord | None:
        """Remove one connection from online presence indexes."""
        normalized_connection_id = str(connection_id or "").strip()
        if not normalized_connection_id:
            return None

        record = self.get_connection(normalized_connection_id)
        if record is None:
            return None

        cleanup_keys = self._remove_record_with_pipeline(record)
        self._delete_empty_index_keys(cleanup_keys)
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

        raw = self._run_redis("get connection", lambda _client: _client.get(self._connection_key(normalized_connection_id)))
        if raw is None:
            return None

        record = self._record_from_payload_or_none(raw)
        if record is None or record.status != RUNTIME_PRESENCE_STATUS_ONLINE:
            return None

        return record

    def list_online_frontends(self) -> list[NsRuntimePresenceRecord]:
        """Return online frontend presence records."""
        return self._records_by_set_key(self._role_key("frontend"))

    def list_online_backends(self) -> list[NsRuntimePresenceRecord]:
        """Return online backend presence records."""
        return self._records_by_set_key(self._role_key("backend"))

    def list_online_runtime_sub_nodes(self) -> list[NsRuntimePresenceRecord]:
        """Return online runtime sub-node presence records."""
        return self._records_by_set_key(self._role_key("runtime_sub"))

    def list_online_by_user(self, user_id: str) -> list[NsRuntimePresenceRecord]:
        """Return online frontend presence records for one user."""
        normalized_user_id = MemoryRuntimePresenceStore._normalize_optional(user_id)
        if normalized_user_id is None:
            return []
        return self._records_by_set_key(self._index_key("user", normalized_user_id))

    def list_online_by_session(self, session_id: str) -> list[NsRuntimePresenceRecord]:
        """Return online frontend presence records for one session."""
        normalized_session_id = MemoryRuntimePresenceStore._normalize_optional(session_id)
        if normalized_session_id is None:
            return []
        return self._records_by_set_key(self._index_key("session", normalized_session_id))

    def list_online_by_client(self, client_id: str) -> list[NsRuntimePresenceRecord]:
        """Return online frontend presence records for one client."""
        normalized_client_id = MemoryRuntimePresenceStore._normalize_optional(client_id)
        if normalized_client_id is None:
            return []
        return self._records_by_set_key(self._index_key("client", normalized_client_id))

    def list_online_by_room(self, room_id: str) -> list[NsRuntimePresenceRecord]:
        """Return online frontend presence records for one room."""
        normalized_room_id = MemoryRuntimePresenceStore._normalize_optional(room_id)
        if normalized_room_id is None:
            return []
        return self._records_by_set_key(self._index_key("room", normalized_room_id))

    def count_online(self) -> int:
        """Return online connection count."""
        return (
                len(self.list_online_frontends())
                + len(self.list_online_backends())
                + len(self.list_online_runtime_sub_nodes())
        )

    def snapshot_counts(self) -> dict[str, int]:
        """Return online presence counters."""
        online_frontends = len(self.list_online_frontends())
        online_backends = len(self.list_online_backends())
        online_runtime_sub_nodes = len(self.list_online_runtime_sub_nodes())
        return {
            "online_connections": online_frontends + online_backends + online_runtime_sub_nodes,
            "online_frontends": online_frontends,
            "online_backends": online_backends,
            "online_runtime_sub_nodes": online_runtime_sub_nodes,
            "online_users": self._count_online_index_records("user"),
        }

    def _set_record(self, record: NsRuntimePresenceRecord) -> None:
        """Store one presence record with lease TTL."""
        self._run_redis(
            "set connection",
            lambda _client: _client.set(
                self._connection_key(record.connection_id),
                self._record_to_json(record),
                ex=self._record_ttl_seconds,
            ),
        )

    def _refresh_record_with_pipeline(self, record: NsRuntimePresenceRecord) -> None:
        """Refresh one presence record and reverse index lease through one Redis transaction."""
        index_keys = self._record_index_keys(record)
        reverse_index_key = self._reverse_index_key(record.connection_id)

        def _refresh(_client: Any) -> None:
            _pipeline = _client.pipeline(transaction=True)

            _pipeline.set(
                self._connection_key(record.connection_id),
                self._record_to_json(record),
                ex=self._record_ttl_seconds,
            )

            if index_keys:
                _pipeline.sadd(reverse_index_key, *sorted(index_keys))

            _pipeline.expire(reverse_index_key, self._reverse_index_ttl_seconds())
            _pipeline.execute()

        self._run_redis("refresh connection with reverse index lease", _refresh)

    def _replace_record_with_pipeline(self, old_record: NsRuntimePresenceRecord | None, record: NsRuntimePresenceRecord) -> set[str]:
        """Replace one record and its indexes through one Redis transaction."""
        new_index_keys = self._record_index_keys(record)
        cleanup_keys = set(self._read_reverse_index_keys(record.connection_id))

        if old_record is not None:
            cleanup_keys.update(self._record_index_keys(old_record))

        def _replace(_client: Any) -> None:
            _pipeline = _client.pipeline(transaction=True)

            for key in cleanup_keys:
                _pipeline.srem(key, record.connection_id)

            _pipeline.set(
                self._connection_key(record.connection_id),
                self._record_to_json(record),
                ex=self._record_ttl_seconds,
            )

            for key in new_index_keys:
                _pipeline.sadd(key, record.connection_id)

            reverse_index_key = self._reverse_index_key(record.connection_id)
            _pipeline.delete(reverse_index_key)

            if new_index_keys:
                _pipeline.sadd(reverse_index_key, *sorted(new_index_keys))

            _pipeline.expire(reverse_index_key, self._reverse_index_ttl_seconds())
            _pipeline.execute()

        self._run_redis("replace connection with indexes", _replace)
        cleanup_keys.difference_update(new_index_keys)
        return cleanup_keys

    def _remove_record_with_pipeline(self, record: NsRuntimePresenceRecord) -> set[str]:
        """Remove one record and its indexes through one Redis transaction."""
        cleanup_keys = self._record_index_keys(record)
        cleanup_keys.update(self._read_reverse_index_keys(record.connection_id))

        def _remove(_client: Any) -> None:
            _pipeline = _client.pipeline(transaction=True)
            _pipeline.delete(self._connection_key(record.connection_id))

            for key in cleanup_keys:
                _pipeline.srem(key, record.connection_id)

            _pipeline.delete(self._reverse_index_key(record.connection_id))
            _pipeline.execute()

        self._run_redis("remove connection with indexes", _remove)
        return cleanup_keys

    def _record_index_keys(self, record: NsRuntimePresenceRecord) -> set[str]:
        """Return all index keys for one presence record."""
        keys = {
            self._role_key(record.connection_type),
        }

        if record.connection_type != "frontend":
            return keys

        if record.user_id is not None:
            keys.add(self._index_key("user", record.user_id))

        if record.session_id is not None:
            keys.add(self._index_key("session", record.session_id))

        if record.client_id is not None:
            keys.add(self._index_key("client", record.client_id))

        for room_id in record.rooms:
            keys.add(self._index_key("room", room_id))

        return keys

    def _delete_empty_index_keys(self, keys: set[str]) -> None:
        """Delete empty index keys after write transaction succeeds."""
        for key in sorted(str(item).strip() for item in keys if str(item).strip()):
            self._delete_empty_index_key(key)

    def _read_reverse_index_keys(self, connection_id: str) -> set[str]:
        """Read recorded index keys for one connection id."""
        normalized_connection_id = str(connection_id or "").strip()
        if not normalized_connection_id:
            return set()

        raw_keys = self._run_redis("read reverse index keys", lambda _client: _client.smembers(self._reverse_index_key(normalized_connection_id)))
        return {
            str(key).strip()
            for key in raw_keys
            if str(key).strip()
        }

    def _reverse_index_key(self, connection_id: str) -> str:
        """Build Redis reverse index key for one connection id."""
        return f"{self._key_prefix}:indexes:{str(connection_id or '').strip()}"

    def _reverse_index_ttl_seconds(self) -> int:
        """Return reverse index TTL seconds."""
        return max(self._record_ttl_seconds * 2, self._record_ttl_seconds + 1)

    def _add_indexes(self, record: NsRuntimePresenceRecord) -> None:
        """Add record to role and frontend secondary indexes."""

        def _add(_client: Any) -> None:
            _client.sadd(self._role_key(record.connection_type), record.connection_id)

            if record.connection_type != "frontend":
                return

            if record.user_id is not None:
                _client.sadd(self._index_key("user", record.user_id), record.connection_id)

            if record.session_id is not None:
                _client.sadd(self._index_key("session", record.session_id), record.connection_id)

            if record.client_id is not None:
                _client.sadd(self._index_key("client", record.client_id), record.connection_id)

            for room_id in record.rooms:
                _client.sadd(self._index_key("room", room_id), record.connection_id)

        self._run_redis("add indexes", _add)

    def _remove_indexes(self, record: NsRuntimePresenceRecord) -> None:
        """Remove record from all presence indexes without deleting the record."""
        cleanup_keys = self._record_index_keys(record)

        def _remove(_client: Any) -> None:
            _pipeline = _client.pipeline(transaction=True)

            for key in cleanup_keys:
                _pipeline.srem(key, record.connection_id)

            _pipeline.execute()

        self._run_redis("remove indexes", _remove)
        self._delete_empty_index_keys(cleanup_keys)

    def _records_by_set_key(self, key: str) -> list[NsRuntimePresenceRecord]:
        """Return online records by one Redis set key and cleanup stale members."""
        raw_connection_ids = self._run_redis("read index set", lambda _client: _client.smembers(key))
        connection_ids = {
            str(connection_id).strip()
            for connection_id in raw_connection_ids
            if str(connection_id).strip()
        }
        return self._records_by_connection_ids(connection_ids, source_set_key=key)

    def _records_by_connection_ids(self, connection_ids: set[str], *, source_set_key: str | None = None) -> list[NsRuntimePresenceRecord]:
        """Return online records by connection ids."""
        if not connection_ids:
            if source_set_key is not None:
                self._delete_empty_index_key(source_set_key)
            return []

        normalized_connection_ids = sorted(str(connection_id).strip() for connection_id in connection_ids if str(connection_id).strip())
        if not normalized_connection_ids:
            if source_set_key is not None:
                self._delete_empty_index_key(source_set_key)
            return []

        keys = [self._connection_key(connection_id) for connection_id in normalized_connection_ids]
        raw_records = self._run_redis("read connection records", lambda _client: _client.mget(keys))

        result: list[NsRuntimePresenceRecord] = []
        stale_connection_ids: list[str] = []

        for connection_id, raw_record in zip(normalized_connection_ids, raw_records, strict=False):
            record = self._record_from_payload_or_none(raw_record)
            if record is not None and record.status == RUNTIME_PRESENCE_STATUS_ONLINE:
                result.append(record)
                continue

            stale_connection_ids.append(connection_id)

        if source_set_key is not None and stale_connection_ids:
            self._run_redis("cleanup stale index members", lambda _client: _client.srem(source_set_key, *stale_connection_ids))
            self._delete_empty_index_key(source_set_key)

        return sorted(result, key=lambda item: item.connection_id)

    def _count_online_index_records(self, index_name: str) -> int:
        """Count secondary index keys that still contain at least one live record."""
        count: int = 0
        pattern = self._index_key(index_name, "*")
        keys = self._run_redis("scan index keys", lambda _client: list(_client.scan_iter(match=pattern, count=100)))

        for key in keys:
            normalized_key = str(key)
            if self._records_by_set_key(normalized_key):
                count += 1
                continue

            self._delete_empty_index_key(normalized_key)

        return count

    def _remove_from_index_key(self, key: str, connection_id: str) -> None:
        """Remove one connection id from one index key."""
        self._run_redis("remove index member", lambda _client: _client.srem(key, connection_id))
        self._delete_empty_index_key(key)

    def _delete_empty_index_key(self, key: str) -> None:
        """Delete an index key when it has no remaining members."""

        def _delete(_client: Any) -> None:
            if int(_client.scard(key) or 0) <= 0:
                _client.delete(key)

        self._run_redis("delete empty index key", _delete)

    def _run_redis(self, operation_name: str, callback: Callable[[Any], Any]) -> Any:
        """Run one Redis operation behind the runtime presence error boundary."""
        normalized_operation_name = str(operation_name or "").strip() or "operation"
        try:
            return callback(self._get_client())
        except NsRuntimeConfigurationError:
            raise
        except Exception as exc:
            raise NsRuntimePresenceError(f"runtime redis presence {normalized_operation_name} failed: {exc}") from exc

    def _get_client(self) -> Any:
        """Return initialized sync Redis client."""
        with self._lock:
            if self._client is not None:
                return self._client

            try:
                import redis
            except ImportError as exc:
                raise NsRuntimeConfigurationError("redis package is required for redis/valkey runtime presence") from exc

            self._client = redis.Redis.from_url(
                self._url,
                socket_timeout=self._socket_timeout,
                socket_connect_timeout=self._socket_connect_timeout,
                health_check_interval=self._health_check_interval,
                decode_responses=True,
            )
            return self._client

    def _connection_key(self, connection_id: str) -> str:
        """Build Redis connection record key."""
        return f"{self._key_prefix}:connections:{str(connection_id or '').strip()}"

    def _role_key(self, role: str) -> str:
        """Build Redis role index key."""
        return self._index_key("role", role)

    def _index_key(self, index_name: str, index_value: str) -> str:
        """Build Redis secondary index key."""
        return f"{self._key_prefix}:index:{str(index_name or '').strip()}:{str(index_value or '').strip()}"

    @classmethod
    def _record_to_json(cls, record: NsRuntimePresenceRecord) -> str:
        """Serialize presence record to compact JSON."""
        return json.dumps(record.to_dict(), ensure_ascii=False, separators=(",", ":"))

    @classmethod
    def _record_from_payload_or_none(cls, payload: Any) -> NsRuntimePresenceRecord | None:
        """Deserialize presence record from Redis payload."""
        if payload is None:
            return None

        try:
            return cls._record_from_payload(payload)
        except Exception:
            return None

    @classmethod
    def _record_from_payload(cls, payload: Any) -> NsRuntimePresenceRecord:
        """Deserialize presence record from Redis payload."""
        if isinstance(payload, bytes | bytearray):
            raw_text = bytes(payload).decode("utf-8")
        else:
            raw_text = str(payload)

        data: Any = json.loads(raw_text)
        if not isinstance(data, dict):
            raise ValueError("runtime presence record payload must be a JSON object")

        rooms_raw = data.get("rooms") or ()
        if not isinstance(rooms_raw, list | tuple | set):
            rooms_raw = ()

        health_raw = data.get("health") or {}
        metadata_raw = data.get("metadata") or {}

        return NsRuntimePresenceRecord(
            node_id=str(data.get("node_id") or ""),
            connection_id=str(data.get("connection_id") or ""),
            connection_type=str(data.get("connection_type") or ""),
            status=str(data.get("status") or RUNTIME_PRESENCE_STATUS_ONLINE),
            principal_type=cls._optional_str(data.get("principal_type")),
            principal_id=cls._optional_str(data.get("principal_id")),
            user_id=cls._optional_str(data.get("user_id")),
            client_id=cls._optional_str(data.get("client_id")),
            session_id=cls._optional_str(data.get("session_id")),
            backend_id=cls._optional_str(data.get("backend_id")),
            service_id=cls._optional_str(data.get("service_id")),
            runtime_node_id=cls._optional_str(data.get("runtime_node_id")),
            rooms=tuple(sorted(str(room).strip() for room in rooms_raw if str(room).strip())),
            remote_address=str(data.get("remote_address") or ""),
            connected_at_epoch_ms=int(data.get("connected_at_epoch_ms") or 0),
            last_seen_epoch_ms=int(data.get("last_seen_epoch_ms") or 0),
            health=dict(health_raw) if isinstance(health_raw, dict) else {},
            metadata=dict(metadata_raw) if isinstance(metadata_raw, dict) else {},
        )

    @staticmethod
    def _optional_str(value: Any) -> str | None:
        """Normalize optional string field from Redis payload."""
        if value is None:
            return None

        normalized = str(value).strip()
        return normalized or None


def build_runtime_presence_store(config: NsRuntimeConfig | None = None) -> NsRuntimePresenceStore:
    """Build runtime presence store from runtime config."""
    if config is None:
        from ns_common.config import ns_config

        config = ns_config.runtime_config

    backend = str(config.resolved_runtime_presence_backend() or RUNTIME_BACKEND_MEMORY).strip().lower()

    # Keep implementation availability centralized in NsRuntimeConfig so direct
    # config.validate() and runtime factory startup have the same semantics.
    config.ensure_runtime_presence_backend_implemented()

    if backend == RUNTIME_BACKEND_MEMORY:
        return MemoryRuntimePresenceStore()

    if backend in {RUNTIME_BACKEND_REDIS, RUNTIME_BACKEND_VALKEY}:
        return RedisRuntimePresenceStore(
            url=str(config.runtime_presence_location or "").strip(),
            key_prefix=str(config.runtime_presence_key_prefix or "").strip(),
            record_ttl_seconds=int(config.runtime_presence_record_ttl_seconds),
        )

    raise NsRuntimeConfigurationError(f"runtime presence backend is not implemented yet: {backend}")
