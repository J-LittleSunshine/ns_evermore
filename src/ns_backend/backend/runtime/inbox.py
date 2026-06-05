# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any

from ns_common import DATA_DIR
from ns_common.config import ns_config
from ns_common.runtime.config import NsRuntimeConfig
from ns_common.runtime.errors import NsRuntimeError
from ns_common.runtime.messages import NsRuntimeMessage


class NsBackendRuntimeInboxError(NsRuntimeError):
    """Raised when backend runtime inbound inbox operation fails."""


@dataclass(slots=True, frozen=True, kw_only=True)
class NsBackendRuntimeInboundMessage:
    """Inbound runtime message delivered to backend connector."""

    message_id: str
    topic: str
    event: str
    payload: dict[str, Any]
    target_type: str
    producer_type: str
    headers: dict[str, str]
    created_at_epoch_ms: int
    received_at_epoch_ms: int

    correlation_id: str | None = None
    reply_to_message_id: str | None = None
    target_id: str | None = None
    producer_id: str | None = None
    trace_id: str | None = None

    def to_runtime_message(self) -> NsRuntimeMessage:
        """Convert inbound record back to NsRuntimeMessage."""
        return NsRuntimeMessage(
            topic=self.topic,
            event=self.event,
            payload=dict(self.payload),
            target_type=self.target_type,  # type: ignore[arg-type]
            target_id=self.target_id,
            producer_type=self.producer_type,  # type: ignore[arg-type]
            producer_id=self.producer_id,
            message_id=self.message_id,
            trace_id=self.trace_id,
            idempotency_key=None,
            ttl_seconds=None,
            require_ack=True,
            created_at_epoch_ms=self.created_at_epoch_ms,
            headers=dict(self.headers),
        ).normalized()


class SqliteBackendRuntimeInbox:
    """SQLite-backed backend inbound inbox.

    The backend connector and Django/ADRF workers are separate processes.
    Therefore P9 cannot use an in-memory queue as the canonical inbound channel.
    This inbox uses the same SQLite database file as the local runtime outbox by
    default, making connector-written replies visible to backend views/workers.
    """

    _TABLE_NAME = "ns_runtime_inbox"

    def __init__(self, config: NsRuntimeConfig | None = None) -> None:
        """Initialize backend runtime inbox."""
        self._config: NsRuntimeConfig = config or ns_config.runtime_config
        self._lock = RLock()
        self._db_path = self._resolve_db_path(self._config.backend_outbox_location)
        self._connection = self._open_connection()
        self._ensure_schema()

    def put(
            self,
            message: NsRuntimeMessage,
            *,
            correlation_id: str | None = None,
            reply_to_message_id: str | None = None,
    ) -> str:
        """Persist one inbound runtime message and return message id."""
        normalized_message = message.normalized()
        now_epoch_ms = int(time.time() * 1000)
        normalized_correlation_id = self._normalize_optional(
            correlation_id
            or normalized_message.headers.get("correlation_id")
            or normalized_message.trace_id
        )
        normalized_reply_to_message_id = self._normalize_optional(
            reply_to_message_id
            or normalized_message.headers.get("reply_to_message_id")
        )

        with self._lock:
            try:
                self._connection.execute(
                    f"""
                    INSERT INTO {self._TABLE_NAME} (
                        message_id,
                        correlation_id,
                        reply_to_message_id,
                        topic,
                        event,
                        payload_json,
                        target_type,
                        target_id,
                        producer_type,
                        producer_id,
                        trace_id,
                        headers_json,
                        created_at_epoch_ms,
                        received_at_epoch_ms
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(message_id) DO UPDATE SET
                        correlation_id = excluded.correlation_id,
                        reply_to_message_id = excluded.reply_to_message_id,
                        topic = excluded.topic,
                        event = excluded.event,
                        payload_json = excluded.payload_json,
                        target_type = excluded.target_type,
                        target_id = excluded.target_id,
                        producer_type = excluded.producer_type,
                        producer_id = excluded.producer_id,
                        trace_id = excluded.trace_id,
                        headers_json = excluded.headers_json,
                        created_at_epoch_ms = excluded.created_at_epoch_ms,
                        received_at_epoch_ms = excluded.received_at_epoch_ms
                    """,
                    (
                        normalized_message.message_id,
                        normalized_correlation_id,
                        normalized_reply_to_message_id,
                        normalized_message.topic,
                        normalized_message.event,
                        self._json_dumps(normalized_message.payload),
                        normalized_message.target_type,
                        normalized_message.target_id,
                        normalized_message.producer_type,
                        normalized_message.producer_id,
                        normalized_message.trace_id,
                        self._json_dumps(normalized_message.headers),
                        normalized_message.created_at_epoch_ms,
                        now_epoch_ms,
                    ),
                )
                self._connection.commit()
            except sqlite3.Error as exc:
                self._connection.rollback()
                raise NsBackendRuntimeInboxError("failed to put backend runtime inbound message") from exc

        return str(normalized_message.message_id)

    def get_by_correlation_id(self, correlation_id: str) -> NsBackendRuntimeInboundMessage | None:
        """Return the latest inbound message for one correlation id."""
        normalized_correlation_id = self._normalize_required(correlation_id, "correlation_id")

        with self._lock:
            row = self._connection.execute(
                f"""
                SELECT *
                FROM {self._TABLE_NAME}
                WHERE correlation_id = ?
                ORDER BY received_at_epoch_ms DESC, id DESC
                LIMIT 1
                """,
                (normalized_correlation_id,),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_inbound_message(row)

    def get_by_message_id(self, message_id: str) -> NsBackendRuntimeInboundMessage | None:
        """Return one inbound message by message id."""
        normalized_message_id = self._normalize_required(message_id, "message_id")

        with self._lock:
            row = self._connection.execute(
                f"""
                SELECT *
                FROM {self._TABLE_NAME}
                WHERE message_id = ?
                LIMIT 1
                """,
                (normalized_message_id,),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_inbound_message(row)

    def wait_for_correlation_id(
            self,
            correlation_id: str,
            *,
            timeout_seconds: float = 5.0,
            poll_interval_seconds: float = 0.05,
    ) -> NsBackendRuntimeInboundMessage | None:
        """Poll inbox for one correlation id within timeout.

        This is only a low-level building block for later request/reply APIs.
        It should be used with short timeouts in HTTP views.
        """
        normalized_timeout = max(float(timeout_seconds), 0.0)
        normalized_poll_interval = max(float(poll_interval_seconds), 0.01)
        deadline = time.monotonic() + normalized_timeout

        while True:
            message = self.get_by_correlation_id(correlation_id)
            if message is not None:
                return message

            if time.monotonic() >= deadline:
                return None

            time.sleep(normalized_poll_interval)

    def count(self) -> int:
        """Return inbound inbox message count."""
        with self._lock:
            row = self._connection.execute(
                f"SELECT COUNT(*) AS total FROM {self._TABLE_NAME}"
            ).fetchone()

        return int(row["total"] if row is not None else 0)

    def close(self) -> None:
        """Close SQLite connection."""
        with self._lock:
            self._connection.close()

    def _open_connection(self) -> sqlite3.Connection:
        """Open SQLite WAL connection."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(
            str(self._db_path),
            timeout=max(float(self._config.ack_timeout_seconds), 5.0),
            isolation_level=None,
            check_same_thread=False,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        connection.execute("PRAGMA busy_timeout=5000")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _ensure_schema(self) -> None:
        """Create backend runtime inbox schema."""
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                self._connection.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self._TABLE_NAME} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        message_id TEXT NOT NULL UNIQUE,
                        correlation_id TEXT,
                        reply_to_message_id TEXT,
                        topic TEXT NOT NULL,
                        event TEXT NOT NULL,
                        payload_json TEXT NOT NULL,
                        target_type TEXT NOT NULL,
                        target_id TEXT,
                        producer_type TEXT NOT NULL,
                        producer_id TEXT,
                        trace_id TEXT,
                        headers_json TEXT NOT NULL,
                        created_at_epoch_ms INTEGER NOT NULL,
                        received_at_epoch_ms INTEGER NOT NULL
                    )
                    """
                )
                self._connection.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS idx_{self._TABLE_NAME}_correlation
                    ON {self._TABLE_NAME}(correlation_id, received_at_epoch_ms DESC)
                    """
                )
                self._connection.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS idx_{self._TABLE_NAME}_reply_to
                    ON {self._TABLE_NAME}(reply_to_message_id)
                    """
                )
                self._connection.commit()
            except sqlite3.Error:
                self._connection.rollback()
                raise

    def _row_to_inbound_message(self, row: sqlite3.Row) -> NsBackendRuntimeInboundMessage:
        """Convert SQLite row to inbound message."""
        payload = self._json_loads(str(row["payload_json"] or "{}"))
        headers = self._json_loads(str(row["headers_json"] or "{}"))

        if not isinstance(payload, dict):
            raise NsBackendRuntimeInboxError("backend runtime inbox payload_json must decode to object")

        if not isinstance(headers, dict):
            raise NsBackendRuntimeInboxError("backend runtime inbox headers_json must decode to object")

        return NsBackendRuntimeInboundMessage(
            message_id=str(row["message_id"]),
            correlation_id=row["correlation_id"],
            reply_to_message_id=row["reply_to_message_id"],
            topic=str(row["topic"]),
            event=str(row["event"]),
            payload=dict(payload),
            target_type=str(row["target_type"]),
            target_id=row["target_id"],
            producer_type=str(row["producer_type"]),
            producer_id=row["producer_id"],
            trace_id=row["trace_id"],
            headers={str(key): str(value) for key, value in headers.items()},
            created_at_epoch_ms=int(row["created_at_epoch_ms"]),
            received_at_epoch_ms=int(row["received_at_epoch_ms"]),
        )

    def _resolve_db_path(self, location: str) -> Path:
        """Resolve SQLite database path.

        Reuse backend_outbox_location so outbox and inbox are visible across
        backend worker and backend connector processes.
        """
        location_text = str(location or "").strip()
        if not location_text:
            return DATA_DIR / "runtime" / "backend_outbox.sqlite3"

        db_path = Path(location_text)
        if db_path.is_absolute():
            return db_path

        return DATA_DIR / db_path

    @staticmethod
    def _normalize_optional(value: Any) -> str | None:
        """Normalize optional identifier."""
        if value is None:
            return None

        normalized = str(value).strip()
        return normalized or None

    @classmethod
    def _normalize_required(cls, value: Any, field_name: str) -> str:
        """Normalize required identifier."""
        normalized = cls._normalize_optional(value)
        if normalized is None:
            raise NsBackendRuntimeInboxError(f"{field_name} is required")
        return normalized

    @staticmethod
    def _json_dumps(value: dict[str, Any]) -> str:
        """Dump JSON object."""
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def _json_loads(value: str) -> Any:
        """Load JSON payload."""
        return json.loads(value or "{}")


def build_backend_runtime_inbox(config: NsRuntimeConfig | None = None) -> SqliteBackendRuntimeInbox:
    """Build default backend runtime inbound inbox."""
    return SqliteBackendRuntimeInbox(config or ns_config.runtime_config)
