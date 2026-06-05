# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import sqlite3
import time
from pathlib import Path
from threading import RLock
from typing import Any, TYPE_CHECKING

from ns_common import DATA_DIR
from ns_common.runtime.config import NsRuntimeConfig
from ns_common.runtime.constants import (
    RUNTIME_BACKEND_SQL_WAL,
    RUNTIME_MESSAGE_STATUS_ACKED,
    RUNTIME_MESSAGE_STATUS_DEAD,
    RUNTIME_MESSAGE_STATUS_PENDING,
    RUNTIME_MESSAGE_STATUS_RETRY,
    RUNTIME_MESSAGE_STATUS_SENDING,
)
from ns_common.runtime.errors import NsRuntimeConfigurationError, NsRuntimeOutboxError
from ns_common.runtime.messages import NsRuntimeAck, NsRuntimeMessage

if TYPE_CHECKING:
    pass


class SqlWalRuntimeOutbox:
    """SQLite WAL runtime outbox.

    This outbox is intended to provide local durable delivery between
    ns_backend workers and the backend runtime connector without requiring
    Redis, ValKey, or MQ.
    """

    _TABLE_NAME = "ns_runtime_outbox"

    def __init__(self, config: NsRuntimeConfig) -> None:
        """Initialize SQLite WAL runtime outbox."""
        if config.resolved_backend_outbox_backend() != RUNTIME_BACKEND_SQL_WAL:
            raise NsRuntimeConfigurationError("SqlWalRuntimeOutbox requires backend_outbox_backend=sql_wal")

        self._config: NsRuntimeConfig = config
        self._lock: RLock = RLock()
        self._db_path: Path = self._resolve_db_path(config.backend_outbox_location)
        self._connection: sqlite3.Connection = self._open_connection()
        self._ensure_schema()

    def enqueue(self, message: NsRuntimeMessage) -> str:
        """Persist one runtime message and return message id."""
        normalized_message: NsRuntimeMessage = message.normalized()
        now: float = self._now()
        message_id: str = str(normalized_message.message_id or "").strip()

        payload_json: str = self._json_dumps(normalized_message.payload)
        headers_json: str = self._json_dumps(normalized_message.headers)

        with self._lock:
            try:
                self._connection.execute(
                    f"""
                    INSERT INTO {self._TABLE_NAME} (
                        message_id,
                        idempotency_key,
                        topic,
                        event,
                        target_type,
                        target_id,
                        producer_type,
                        producer_id,
                        payload_json,
                        headers_json,
                        status,
                        priority,
                        attempt_count,
                        max_attempts,
                        next_retry_at,
                        locked_by,
                        locked_until,
                        ack_status,
                        acked_at,
                        dead_reason,
                        trace_id,
                        ttl_seconds,
                        require_ack,
                        created_at_epoch_ms,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(message_id) DO NOTHING
                    """,
                    (
                        message_id,
                        normalized_message.idempotency_key,
                        normalized_message.topic,
                        normalized_message.event,
                        normalized_message.target_type,
                        normalized_message.target_id,
                        normalized_message.producer_type,
                        normalized_message.producer_id,
                        payload_json,
                        headers_json,
                        RUNTIME_MESSAGE_STATUS_PENDING,
                        self._resolve_priority(normalized_message),
                        0,
                        self._config.max_attempts,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        normalized_message.trace_id,
                        normalized_message.ttl_seconds,
                        1 if normalized_message.require_ack else 0,
                        normalized_message.created_at_epoch_ms,
                        now,
                        now,
                    ),
                )
                self._connection.commit()
            except sqlite3.Error as exc:
                self._connection.rollback()
                raise NsRuntimeOutboxError("failed to enqueue runtime message") from exc

        return message_id

    def claim_batch(self, *, consumer_id: str, limit: int) -> list[NsRuntimeMessage]:
        """Claim pending messages for one connector consumer atomically."""
        normalized_consumer_id: str = self._normalize_consumer_id(consumer_id)
        normalized_limit: int = self._normalize_limit(limit)
        now: float = self._now()
        locked_until: float = now + self._claim_lease_seconds()

        with self._lock:
            try:
                # 使用 BEGIN IMMEDIATE 获取写锁，确保 SELECT + UPDATE 是一个原子 claim。
                # 这可以避免多 connector 误启动时重复领取同一批消息。
                self._connection.execute("BEGIN IMMEDIATE")

                rows = self._connection.execute(
                    f"""
                    SELECT *
                    FROM {self._TABLE_NAME}
                    WHERE
                        (
                            status IN (?, ?)
                            AND (next_retry_at IS NULL OR next_retry_at <= ?)
                        )
                        OR (
                            status = ?
                            AND locked_until IS NOT NULL
                            AND locked_until <= ?
                        )
                    ORDER BY priority ASC, id ASC
                    LIMIT ?
                    """,
                    (
                        RUNTIME_MESSAGE_STATUS_PENDING,
                        RUNTIME_MESSAGE_STATUS_RETRY,
                        now,
                        RUNTIME_MESSAGE_STATUS_SENDING,
                        now,
                        normalized_limit,
                    ),
                ).fetchall()

                if not rows:
                    self._connection.commit()
                    return []

                messages: list[NsRuntimeMessage] = []
                for row in rows:
                    message_id = str(row["message_id"])
                    self._connection.execute(
                        f"""
                        UPDATE {self._TABLE_NAME}
                        SET
                            status = ?,
                            attempt_count = attempt_count + 1,
                            locked_by = ?,
                            locked_until = ?,
                            updated_at = ?
                        WHERE message_id = ?
                        """,
                        (
                            RUNTIME_MESSAGE_STATUS_SENDING,
                            normalized_consumer_id,
                            locked_until,
                            now,
                            message_id,
                        ),
                    )
                    messages.append(self._row_to_message(row))

                self._connection.commit()
                return messages
            except sqlite3.Error as exc:
                self._connection.rollback()
                raise NsRuntimeOutboxError("failed to claim runtime outbox messages") from exc

    def mark_acked(self, *, message_id: str, ack: NsRuntimeAck | None = None) -> None:
        """Mark one message as acknowledged by runtime master."""
        normalized_message_id: str = self._normalize_message_id(message_id)
        normalized_ack: NsRuntimeAck | None = ack.normalized() if ack is not None else None
        now: float = self._now()

        with self._lock:
            try:
                self._connection.execute(
                    f"""
                    UPDATE {self._TABLE_NAME}
                    SET
                        status = ?,
                        ack_status = ?,
                        acked_at = ?,
                        locked_by = NULL,
                        locked_until = NULL,
                        updated_at = ?
                    WHERE message_id = ?
                    """,
                    (
                        RUNTIME_MESSAGE_STATUS_ACKED,
                        None if normalized_ack is None else normalized_ack.status,
                        now,
                        now,
                        normalized_message_id,
                    ),
                )
                self._connection.commit()
            except sqlite3.Error as exc:
                self._connection.rollback()
                raise NsRuntimeOutboxError("failed to mark runtime message acked") from exc

    def mark_retry(self, *, message_id: str, reason: str) -> None:
        """Release one message for retry, or mark dead after max attempts."""
        normalized_message_id: str = self._normalize_message_id(message_id)
        normalized_reason: str = self._normalize_reason(reason)
        now: float = self._now()

        with self._lock:
            try:
                row = self._connection.execute(
                    f"""
                    SELECT attempt_count, max_attempts
                    FROM {self._TABLE_NAME}
                    WHERE message_id = ?
                    """,
                    (normalized_message_id,),
                ).fetchone()

                if row is None:
                    self._connection.commit()
                    return

                attempt_count: int = int(row["attempt_count"] or 0)
                max_attempts: int = int(row["max_attempts"] or self._config.max_attempts)

                if attempt_count >= max_attempts:
                    self._connection.execute(
                        f"""
                        UPDATE {self._TABLE_NAME}
                        SET
                            status = ?,
                            dead_reason = ?,
                            locked_by = NULL,
                            locked_until = NULL,
                            updated_at = ?
                        WHERE message_id = ?
                        """,
                        (
                            RUNTIME_MESSAGE_STATUS_DEAD,
                            normalized_reason,
                            now,
                            normalized_message_id,
                        ),
                    )
                else:
                    retry_delay: float = self._calculate_retry_delay(attempt_count)
                    self._connection.execute(
                        f"""
                        UPDATE {self._TABLE_NAME}
                        SET
                            status = ?,
                            next_retry_at = ?,
                            dead_reason = NULL,
                            locked_by = NULL,
                            locked_until = NULL,
                            updated_at = ?
                        WHERE message_id = ?
                        """,
                        (
                            RUNTIME_MESSAGE_STATUS_RETRY,
                            now + retry_delay,
                            now,
                            normalized_message_id,
                        ),
                    )

                self._connection.commit()
            except sqlite3.Error as exc:
                self._connection.rollback()
                raise NsRuntimeOutboxError("failed to mark runtime message retry") from exc

    def mark_dead(self, *, message_id: str, reason: str) -> None:
        """Mark one message as permanently failed."""
        normalized_message_id: str = self._normalize_message_id(message_id)
        normalized_reason: str = self._normalize_reason(reason)
        now: float = self._now()

        with self._lock:
            try:
                self._connection.execute(
                    f"""
                    UPDATE {self._TABLE_NAME}
                    SET
                        status = ?,
                        dead_reason = ?,
                        locked_by = NULL,
                        locked_until = NULL,
                        updated_at = ?
                    WHERE message_id = ?
                    """,
                    (
                        RUNTIME_MESSAGE_STATUS_DEAD,
                        normalized_reason,
                        now,
                        normalized_message_id,
                    ),
                )
                self._connection.commit()
            except sqlite3.Error as exc:
                self._connection.rollback()
                raise NsRuntimeOutboxError("failed to mark runtime message dead") from exc

    def count_by_status(self, status: str) -> int:
        """Return message count by status."""
        normalized_status: str = str(status or "").strip().upper()
        if not normalized_status:
            raise NsRuntimeOutboxError("runtime outbox status is required")

        with self._lock:
            row = self._connection.execute(
                f"SELECT COUNT(*) AS total FROM {self._TABLE_NAME} WHERE status = ?",
                (normalized_status,),
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
        """Create runtime outbox schema."""
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                self._connection.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self._TABLE_NAME} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        message_id TEXT NOT NULL UNIQUE,
                        idempotency_key TEXT,
                        topic TEXT NOT NULL,
                        event TEXT NOT NULL,
                        target_type TEXT NOT NULL,
                        target_id TEXT,
                        producer_type TEXT NOT NULL,
                        producer_id TEXT,
                        payload_json TEXT NOT NULL,
                        headers_json TEXT NOT NULL,
                        status TEXT NOT NULL,
                        priority INTEGER NOT NULL DEFAULT 100,
                        attempt_count INTEGER NOT NULL DEFAULT 0,
                        max_attempts INTEGER NOT NULL,
                        next_retry_at REAL,
                        locked_by TEXT,
                        locked_until REAL,
                        ack_status TEXT,
                        acked_at REAL,
                        dead_reason TEXT,
                        trace_id TEXT,
                        ttl_seconds INTEGER,
                        require_ack INTEGER NOT NULL DEFAULT 1,
                        created_at_epoch_ms INTEGER NOT NULL,
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL
                    )
                    """
                )
                self._connection.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS idx_{self._TABLE_NAME}_claim
                    ON {self._TABLE_NAME}(status, next_retry_at, priority, id)
                    """
                )
                self._connection.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS idx_{self._TABLE_NAME}_locked_until
                    ON {self._TABLE_NAME}(status, locked_until)
                    """
                )
                self._connection.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS idx_{self._TABLE_NAME}_idempotency
                    ON {self._TABLE_NAME}(idempotency_key)
                    """
                )
                self._connection.commit()
            except sqlite3.Error:
                self._connection.rollback()
                raise

    def _row_to_message(self, row: sqlite3.Row) -> NsRuntimeMessage:
        """Convert one SQLite row to runtime message."""
        payload = self._json_loads(str(row["payload_json"] or "{}"))
        headers = self._json_loads(str(row["headers_json"] or "{}"))

        if not isinstance(payload, dict):
            raise NsRuntimeOutboxError("runtime outbox payload_json must decode to object")
        if not isinstance(headers, dict):
            raise NsRuntimeOutboxError("runtime outbox headers_json must decode to object")

        return NsRuntimeMessage(
            topic=str(row["topic"]),
            event=str(row["event"]),
            payload=dict(payload),
            target_type=str(row["target_type"]),  # type: ignore[arg-type]
            target_id=row["target_id"],
            producer_type=str(row["producer_type"]),  # type: ignore[arg-type]
            producer_id=row["producer_id"],
            message_id=str(row["message_id"]),
            trace_id=row["trace_id"],
            idempotency_key=row["idempotency_key"],
            ttl_seconds=row["ttl_seconds"],
            require_ack=bool(int(row["require_ack"] or 0)),
            created_at_epoch_ms=int(row["created_at_epoch_ms"]),
            headers={str(key): str(value) for key, value in headers.items()},
        ).normalized()

    def _resolve_db_path(self, location: str) -> Path:
        """Resolve SQLite database path."""
        location_text: str = str(location or "").strip()
        if not location_text:
            return DATA_DIR / "runtime" / "backend_outbox.sqlite3"

        db_path = Path(location_text)
        if db_path.is_absolute():
            return db_path
        return DATA_DIR / db_path

    def _calculate_retry_delay(self, attempt_count: int) -> float:
        """Calculate bounded exponential retry delay."""
        base_delay: float = max(float(self._config.retry_base_delay_seconds), 0.0)
        max_delay: float = max(float(self._config.retry_max_delay_seconds), 0.001)
        exponent: int = max(attempt_count - 1, 0)
        delay: float = base_delay * (2 ** exponent)
        if delay <= 0:
            return 0.0
        return min(delay, max_delay)

    def _claim_lease_seconds(self) -> float:
        """Return claim lease seconds."""
        return max(float(self._config.ack_timeout_seconds) * 2, 10.0)

    @staticmethod
    def _resolve_priority(message: NsRuntimeMessage) -> int:
        """Resolve message priority from headers."""
        raw_priority = message.headers.get("priority")
        if raw_priority is None:
            return 100

        try:
            priority = int(str(raw_priority).strip())
        except ValueError:
            return 100

        return max(priority, 0)

    @staticmethod
    def _normalize_consumer_id(value: str) -> str:
        """Normalize consumer id."""
        normalized_value = str(value or "").strip()
        if not normalized_value:
            raise NsRuntimeOutboxError("runtime outbox consumer_id is required")
        return normalized_value

    @staticmethod
    def _normalize_message_id(value: str) -> str:
        """Normalize message id."""
        normalized_value = str(value or "").strip()
        if not normalized_value:
            raise NsRuntimeOutboxError("runtime outbox message_id is required")
        return normalized_value

    @staticmethod
    def _normalize_limit(value: int) -> int:
        """Normalize claim limit."""
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise NsRuntimeOutboxError("runtime outbox claim limit must be a positive int")
        return value

    @staticmethod
    def _normalize_reason(value: str) -> str:
        """Normalize failure reason."""
        normalized_value = str(value or "").strip()
        return normalized_value or "UNKNOWN_RUNTIME_OUTBOX_REASON"

    @staticmethod
    def _json_dumps(value: Any) -> str:
        """Serialize JSON payload."""
        try:
            return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        except (TypeError, ValueError) as exc:
            raise NsRuntimeOutboxError("runtime outbox payload must be JSON serializable") from exc

    @staticmethod
    def _json_loads(value: str) -> Any:
        """Deserialize JSON payload."""
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise NsRuntimeOutboxError("runtime outbox payload is invalid JSON") from exc

    @staticmethod
    def _now() -> float:
        """Return current unix timestamp."""
        return time.time()


class AsyncSqlWalRuntimeOutbox:
    """Async wrapper for SQLite WAL runtime outbox."""

    def __init__(self, config: NsRuntimeConfig) -> None:
        """Initialize async SQLite WAL runtime outbox."""
        self._outbox = SqlWalRuntimeOutbox(config)

    async def enqueue(self, message: NsRuntimeMessage) -> str:
        """Persist one runtime message and return message id."""
        return await asyncio.to_thread(self._outbox.enqueue, message)

    async def claim_batch(self, *, consumer_id: str, limit: int) -> list[NsRuntimeMessage]:
        """Claim pending messages for one connector consumer."""
        return await asyncio.to_thread(self._outbox.claim_batch, consumer_id=consumer_id, limit=limit)

    async def mark_acked(self, *, message_id: str, ack: NsRuntimeAck | None = None) -> None:
        """Mark one message as acknowledged by runtime master."""
        await asyncio.to_thread(self._outbox.mark_acked, message_id=message_id, ack=ack)

    async def mark_retry(self, *, message_id: str, reason: str) -> None:
        """Release one message for retry."""
        await asyncio.to_thread(self._outbox.mark_retry, message_id=message_id, reason=reason)

    async def mark_dead(self, *, message_id: str, reason: str) -> None:
        """Mark one message as permanently failed."""
        await asyncio.to_thread(self._outbox.mark_dead, message_id=message_id, reason=reason)

    async def close(self) -> None:
        """Close SQLite connection."""
        await asyncio.to_thread(self._outbox.close)


def build_runtime_outbox(config: NsRuntimeConfig) -> SqlWalRuntimeOutbox:
    """Build sync runtime outbox by explicit configuration."""
    backend = config.resolved_backend_outbox_backend()
    if backend == RUNTIME_BACKEND_SQL_WAL:
        return SqlWalRuntimeOutbox(config)

    raise NsRuntimeConfigurationError(f"unsupported or unimplemented runtime outbox backend: {backend}")


def build_async_runtime_outbox(config: NsRuntimeConfig) -> AsyncSqlWalRuntimeOutbox:
    """Build async runtime outbox by explicit configuration."""
    backend = config.resolved_backend_outbox_backend()
    if backend == RUNTIME_BACKEND_SQL_WAL:
        return AsyncSqlWalRuntimeOutbox(config)

    raise NsRuntimeConfigurationError(f"unsupported or unimplemented async runtime outbox backend: {backend}")
