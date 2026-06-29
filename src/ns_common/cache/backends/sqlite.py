# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import sqlite3
import time
from pathlib import Path
from threading import RLock
from typing import (
    Any,
    Callable,
    TYPE_CHECKING
)

from ns_common.cache.backends.base import BaseCacheBackend
from ns_common.config import NsCacheConfig
from ns_common.exceptions import (
    NsRuntimeError,
    NsStateError,
)

if TYPE_CHECKING:
    pass


class SQLiteCacheBackend(BaseCacheBackend):
    TABLE_NAME = "ns_cache_entry"

    def __init__(self, config: NsCacheConfig, sqlite_path: Path) -> None:
        self._config = config
        self._sqlite_path = sqlite_path
        self._lock = RLock()
        self._last_cleanup_monotonic = 0.0

    def initialize(self) -> None:
        self._sqlite_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=NORMAL")
            connection.execute(f"PRAGMA busy_timeout={int(self._config.sqlite_busy_timeout_ms)}")
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.TABLE_NAME}
                (
                    cache_key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at REAL NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )
            connection.execute(
                f"""
                CREATE INDEX IF NOT EXISTS idx_{self.TABLE_NAME}_expires_at
                ON {self.TABLE_NAME}(expires_at)
                """
            )

    def close(self) -> None:
        return None

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self._sqlite_path,
            timeout=max(self._config.sqlite_busy_timeout_ms, 1) / 1000,
            isolation_level=None,
        )
        connection.execute(f"PRAGMA busy_timeout={int(self._config.sqlite_busy_timeout_ms)}")
        return connection

    @staticmethod
    def _now() -> float:
        return time.time()

    @staticmethod
    def _expires_at(ttl: int | None) -> float | None:
        if ttl is None:
            return None

        return SQLiteCacheBackend._now() + max(int(ttl), 0)

    @staticmethod
    def _is_expired(expires_at: float | None) -> bool:
        return expires_at is not None and expires_at <= SQLiteCacheBackend._now()

    @staticmethod
    def _is_lock_error(exc: sqlite3.OperationalError) -> bool:
        text = str(exc).lower()
        return "locked" in text or "busy" in text

    def _execute_write_with_retry(self, operation: Callable[[], Any]) -> Any:
        max_retries = max(int(self._config.sqlite_write_max_retries), 0)
        base_delay_ms = max(int(self._config.sqlite_write_retry_base_delay_ms), 0)
        max_delay_ms = max(int(self._config.sqlite_write_retry_max_delay_ms), base_delay_ms)

        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                return operation()
            except sqlite3.OperationalError as exc:
                if not self._is_lock_error(exc):
                    raise NsRuntimeError(
                        "sqlite cache write operation failed.",
                        details={
                            "sqlite_path": str(self._sqlite_path),
                            "exception_class": exc.__class__.__name__,
                        },
                    ) from exc

                last_error = exc

                if attempt >= max_retries:
                    break

                delay_ms = min(base_delay_ms * (2 ** attempt), max_delay_ms)
                if delay_ms > 0:
                    time.sleep(delay_ms / 1000)

        raise NsRuntimeError(
            "sqlite cache write operation failed after retries.",
            details={
                "sqlite_path": str(self._sqlite_path),
                "max_retries": max_retries,
                "exception_class": last_error.__class__.__name__ if last_error else None,
            },
        ) from last_error

    def _maybe_cleanup_expired(self) -> None:
        interval = max(int(self._config.cleanup_interval_seconds), 1)
        now = time.monotonic()

        with self._lock:
            if now - self._last_cleanup_monotonic < interval:
                return

            self._last_cleanup_monotonic = now

        self.cleanup_expired()

    def get(self, key: str) -> str | None:
        self._maybe_cleanup_expired()

        with self._connect() as connection:
            row = connection.execute(
                f"""
                SELECT value, expires_at
                FROM {self.TABLE_NAME}
                WHERE cache_key = ?
                """,
                (key,),
            ).fetchone()

        if row is None:
            return None

        value, expires_at = row
        if self._is_expired(expires_at):
            self.delete(key)
            return None

        return str(value)

    def get_many(self, keys: list[str]) -> dict[str, str]:
        if not keys:
            return {}

        self._maybe_cleanup_expired()

        placeholders = ",".join("?" for _ in keys)
        now = self._now()

        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT cache_key, value
                FROM {self.TABLE_NAME}
                WHERE cache_key IN ({placeholders})
                  AND (expires_at IS NULL OR expires_at > ?)
                """,
                (*keys, now),
            ).fetchall()

        return {
            str(cache_key): str(value)
            for cache_key, value in rows
        }

    def set(self, key: str, value: str, ttl: int | None) -> bool:
        if ttl == 0:
            self.delete(key)
            return False

        self._maybe_cleanup_expired()

        def operation() -> None:
            now = self._now()
            expires_at = self._expires_at(ttl)

            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    f"""
                    INSERT INTO {self.TABLE_NAME}
                    (
                        cache_key,
                        value,
                        expires_at,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(cache_key)
                    DO UPDATE SET
                        value = excluded.value,
                        expires_at = excluded.expires_at,
                        updated_at = excluded.updated_at
                    """,
                    (
                        key,
                        value,
                        expires_at,
                        now,
                        now,
                    ),
                )
                connection.execute("COMMIT")

        self._execute_write_with_retry(operation)
        return True

    def set_many(self, mapping: dict[str, str], ttl: int | None) -> bool:
        if not mapping:
            return True

        if ttl == 0:
            self.delete_many(list(mapping.keys()))
            return False

        self._maybe_cleanup_expired()

        def operation() -> None:
            now = self._now()
            expires_at = self._expires_at(ttl)

            rows = [
                (
                    key,
                    value,
                    expires_at,
                    now,
                    now,
                )
                for key, value in mapping.items()
            ]

            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.executemany(
                    f"""
                    INSERT INTO {self.TABLE_NAME}
                    (
                        cache_key,
                        value,
                        expires_at,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(cache_key)
                    DO UPDATE SET
                        value = excluded.value,
                        expires_at = excluded.expires_at,
                        updated_at = excluded.updated_at
                    """,
                    rows,
                )
                connection.execute("COMMIT")

        self._execute_write_with_retry(operation)
        return True

    def add(self, key: str, value: str, ttl: int | None) -> bool:
        if ttl == 0:
            return False

        self._maybe_cleanup_expired()

        def operation() -> bool:
            now = self._now()
            expires_at = self._expires_at(ttl)

            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")

                existing = connection.execute(
                    f"""
                    SELECT expires_at
                    FROM {self.TABLE_NAME}
                    WHERE cache_key = ?
                    """,
                    (key,),
                ).fetchone()

                if existing is not None and not self._is_expired(existing[0]):
                    connection.execute("COMMIT")
                    return False

                connection.execute(
                    f"DELETE FROM {self.TABLE_NAME} WHERE cache_key = ?",
                    (key,),
                )
                connection.execute(
                    f"""
                    INSERT INTO {self.TABLE_NAME}
                    (
                        cache_key,
                        value,
                        expires_at,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        key,
                        value,
                        expires_at,
                        now,
                        now,
                    ),
                )
                connection.execute("COMMIT")
                return True

        return bool(self._execute_write_with_retry(operation))

    def touch(self, key: str, ttl: int | None) -> bool:
        if ttl == 0:
            return self.delete(key)

        def operation() -> bool:
            expires_at = self._expires_at(ttl)
            now = self._now()

            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                cursor = connection.execute(
                    f"""
                    UPDATE {self.TABLE_NAME}
                    SET expires_at = ?,
                        updated_at = ?
                    WHERE cache_key = ?
                      AND (expires_at IS NULL OR expires_at > ?)
                    """,
                    (
                        expires_at,
                        now,
                        key,
                        now,
                    ),
                )
                connection.execute("COMMIT")

            return cursor.rowcount > 0

        return bool(self._execute_write_with_retry(operation))

    def delete(self, key: str) -> bool:
        def operation() -> bool:
            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                cursor = connection.execute(
                    f"DELETE FROM {self.TABLE_NAME} WHERE cache_key = ?",
                    (key,),
                )
                connection.execute("COMMIT")

            return cursor.rowcount > 0

        return bool(self._execute_write_with_retry(operation))

    def delete_many(self, keys: list[str]) -> int:
        if not keys:
            return 0

        def operation() -> int:
            placeholders = ",".join("?" for _ in keys)

            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                cursor = connection.execute(
                    f"DELETE FROM {self.TABLE_NAME} WHERE cache_key IN ({placeholders})",
                    tuple(keys),
                )
                connection.execute("COMMIT")

            return int(cursor.rowcount)

        return int(self._execute_write_with_retry(operation))

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    def clear(self, namespace_prefix: str) -> bool:
        def operation() -> None:
            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    f"DELETE FROM {self.TABLE_NAME} WHERE cache_key LIKE ?",
                    (f"{namespace_prefix}%",),
                )
                connection.execute("COMMIT")

        self._execute_write_with_retry(operation)
        return True

    def incr(self, key: str, delta: int = 1) -> int:
        def operation() -> int:
            now = self._now()

            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")

                row = connection.execute(
                    f"""
                    SELECT value, expires_at
                    FROM {self.TABLE_NAME}
                    WHERE cache_key = ?
                    """,
                    (key,),
                ).fetchone()

                if row is None:
                    connection.execute("COMMIT")
                    raise NsStateError(
                        "cache key does not exist.",
                        details={
                            "key": key,
                        },
                    )

                raw_value, expires_at = row
                if self._is_expired(expires_at):
                    connection.execute(
                        f"DELETE FROM {self.TABLE_NAME} WHERE cache_key = ?",
                        (key,),
                    )
                    connection.execute("COMMIT")
                    raise NsStateError(
                        "cache key has expired.",
                        details={
                            "key": key,
                        },
                    )

                parsed_value = json.loads(raw_value)
                if isinstance(parsed_value, bool) or not isinstance(parsed_value, int):
                    connection.execute("COMMIT")
                    raise NsStateError(
                        "cache value is not an integer.",
                        details={
                            "key": key,
                            "actual_type": type(parsed_value).__name__,
                        },
                    )

                new_value = parsed_value + int(delta)
                connection.execute(
                    f"""
                    UPDATE {self.TABLE_NAME}
                    SET value = ?,
                        updated_at = ?
                    WHERE cache_key = ?
                    """,
                    (
                        json.dumps(new_value, separators=(",", ":")),
                        now,
                        key,
                    ),
                )
                connection.execute("COMMIT")

            return new_value

        return int(self._execute_write_with_retry(operation))

    def cleanup_expired(self) -> int:
        batch_size = max(int(self._config.cleanup_batch_size), 1)

        def operation() -> int:
            now = self._now()

            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                cursor = connection.execute(
                    f"""
                    DELETE FROM {self.TABLE_NAME}
                    WHERE rowid IN (
                        SELECT rowid
                        FROM {self.TABLE_NAME}
                        WHERE expires_at IS NOT NULL
                          AND expires_at <= ?
                        LIMIT ?
                    )
                    """,
                    (
                        now,
                        batch_size,
                    ),
                )
                connection.execute("COMMIT")

            return int(cursor.rowcount)

        return int(self._execute_write_with_retry(operation))

    async def aget(self, key: str) -> str | None:
        return await asyncio.to_thread(self.get, key)

    async def aget_many(self, keys: list[str]) -> dict[str, str]:
        return await asyncio.to_thread(self.get_many, keys)

    async def aset(self, key: str, value: str, ttl: int | None) -> bool:
        return await asyncio.to_thread(self.set, key, value, ttl)

    async def aset_many(self, mapping: dict[str, str], ttl: int | None) -> bool:
        return await asyncio.to_thread(self.set_many, mapping, ttl)

    async def aadd(self, key: str, value: str, ttl: int | None) -> bool:
        return await asyncio.to_thread(self.add, key, value, ttl)

    async def atouch(self, key: str, ttl: int | None) -> bool:
        return await asyncio.to_thread(self.touch, key, ttl)

    async def adelete(self, key: str) -> bool:
        return await asyncio.to_thread(self.delete, key)

    async def adelete_many(self, keys: list[str]) -> int:
        return await asyncio.to_thread(self.delete_many, keys)

    async def aexists(self, key: str) -> bool:
        return await asyncio.to_thread(self.exists, key)

    async def aclear(self, namespace_prefix: str) -> bool:
        return await asyncio.to_thread(self.clear, namespace_prefix)

    async def aincr(self, key: str, delta: int = 1) -> int:
        return await asyncio.to_thread(self.incr, key, delta)

    async def acleanup_expired(self) -> int:
        return await asyncio.to_thread(self.cleanup_expired)
