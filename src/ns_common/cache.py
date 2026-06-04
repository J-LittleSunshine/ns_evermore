# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import pickle
import re
import sqlite3
import time
from importlib import import_module
from pathlib import Path
from threading import RLock
from typing import Any, ClassVar, Protocol, TYPE_CHECKING

from ns_common import DATA_DIR
from ns_common.config import NsCacheConfig

if TYPE_CHECKING:
    pass


class _DefaultCacheTimeout:
    """Sentinel for using configured default timeout."""




NS_CACHE_DEFAULT_TIMEOUT = _DefaultCacheTimeout()

_MISSING = object()


class NsCacheError(Exception):
    """Base exception for ns_common cache."""


class NsCacheConfigurationError(NsCacheError):
    """Raised when cache configuration is invalid."""


class NsCacheConnectionError(NsCacheError):
    """Raised when cache backend operation fails."""


class NsCacheSerializationError(NsCacheError):
    """Raised when cache serialization or deserialization fails."""


class _CacheSerializer(Protocol):
    """Cache serializer protocol."""

    def dumps(self, value: object) -> bytes:
        """Serialize Python value to bytes."""

    def loads(self, payload: bytes) -> object:
        """Deserialize bytes to Python value."""


class _PickleCacheSerializer:
    """Pickle cache serializer."""

    @staticmethod
    def dumps(value: object) -> bytes:
        """Serialize object by pickle."""
        try:
            return pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as _error:
            raise NsCacheSerializationError("pickle cache serialization failed") from _error

    @staticmethod
    def loads(payload: bytes) -> object:
        """Deserialize object by pickle."""
        try:
            return pickle.loads(payload)
        except Exception as _error:
            raise NsCacheSerializationError("pickle cache deserialization failed") from _error


class _JsonCacheSerializer:
    """JSON cache serializer."""

    @staticmethod
    def dumps(value: object) -> bytes:
        """Serialize JSON-compatible value."""
        try:
            return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        except Exception as _error:
            raise NsCacheSerializationError("json cache serialization failed") from _error

    @staticmethod
    def loads(payload: bytes) -> object:
        """Deserialize JSON-compatible value."""
        try:
            return json.loads(payload.decode("utf-8"))
        except Exception as _error:
            raise NsCacheSerializationError("json cache deserialization failed") from _error


class _RawCacheSerializer:
    """Raw cache serializer."""

    @staticmethod
    def dumps(value: object) -> bytes:
        """Serialize primitive value to bytes."""
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return value.encode("utf-8")
        if isinstance(value, (int, float, bool)):
            return str(value).encode("utf-8")
        if value is None:
            return b""
        raise NsCacheSerializationError("raw cache serializer only supports bytes, str, int, float, bool, or None")

    @staticmethod
    def loads(payload: bytes) -> object:
        """Return raw bytes."""
        return payload


def _build_serializer(name: str) -> _CacheSerializer:
    """Build cache serializer by name."""
    serializer_name = str(name or "pickle").strip().lower()
    if serializer_name == "pickle":
        return _PickleCacheSerializer()
    if serializer_name == "json":
        return _JsonCacheSerializer()
    if serializer_name == "raw":
        return _RawCacheSerializer()
    raise NsCacheConfigurationError(f"unsupported cache serializer: {name}")


class _CacheBackend(Protocol):
    """Internal cache backend protocol."""

    def get(self, key: str, default: object | None = None) -> object | None:
        """Get cache value."""

    def set(self, key: str, value: object, timeout: int | None | _DefaultCacheTimeout = NS_CACHE_DEFAULT_TIMEOUT) -> bool:
        """Set cache value."""

    def add(self, key: str, value: object, timeout: int | None | _DefaultCacheTimeout = NS_CACHE_DEFAULT_TIMEOUT) -> bool:
        """Add cache value if key does not exist."""

    def delete(self, key: str) -> bool:
        """Delete cache key."""

    def exists(self, key: str) -> bool:
        """Check whether key exists."""

    def expire(self, key: str, timeout: int) -> bool:
        """Update key expiration."""

    def persist(self, key: str) -> bool:
        """Remove key expiration."""

    def ttl(self, key: str) -> int:
        """Return Redis-compatible TTL."""

    def clear(self) -> bool:
        """Clear cache keys."""

    def get_many(self, keys: list[str]) -> dict[str, object]:
        """Batch get cache values."""

    def set_many(self, data: dict[str, object], timeout: int | None | _DefaultCacheTimeout = NS_CACHE_DEFAULT_TIMEOUT) -> list[str]:
        """Batch set cache values."""

    def delete_many(self, keys: list[str]) -> int:
        """Batch delete cache keys."""

    def close(self) -> None:
        """Close backend resources."""


class _BaseCacheBackend:
    """Base cache backend."""

    def __init__(self, config: NsCacheConfig) -> None:
        """Initialize base backend."""
        self._config: NsCacheConfig = config
        self._key_prefix: str = config.key_prefix
        self._serializer: _CacheSerializer = _build_serializer(config.serializer)

    def _make_key(self, key: str) -> str:
        """Build storage key with namespace prefix."""
        if not isinstance(key, str) or not key.strip():
            raise NsCacheConfigurationError("cache key must be a non-empty str")

        normalized_key = key.strip()
        if not self._key_prefix:
            return normalized_key

        if normalized_key == self._key_prefix or normalized_key.startswith(f"{self._key_prefix}:"):
            return normalized_key

        return f"{self._key_prefix}:{normalized_key}"

    def _resolve_timeout(self, timeout: int | None | _DefaultCacheTimeout = NS_CACHE_DEFAULT_TIMEOUT) -> int | None:
        """Resolve timeout value."""
        selected_timeout: int | None
        if isinstance(timeout, _DefaultCacheTimeout):
            selected_timeout = self._config.default_timeout_seconds
        else:
            selected_timeout = timeout

        if selected_timeout is None:
            return None

        if isinstance(selected_timeout, bool) or not isinstance(selected_timeout, int):
            raise NsCacheConfigurationError("cache timeout must be int, None, or NS_CACHE_DEFAULT_TIMEOUT")

        return selected_timeout

    @staticmethod
    def _now() -> float:
        """Return current unix timestamp."""
        return time.time()


class _SqlWalCacheBackend(_BaseCacheBackend):
    """SQLite WAL cache backend with automatic table creation."""

    _TABLE_NAME_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    def __init__(self, config: NsCacheConfig) -> None:
        """Initialize SQLite WAL backend."""
        super().__init__(config)
        self._lock: RLock = RLock()
        self._db_path: Path = self._resolve_db_path(config.location)
        self._table: str = self._validate_table_name(config.sql_table)
        self._connection: sqlite3.Connection = self._open_connection()
        self._ensure_schema()

    def get(self, key: str, default: object | None = None) -> object | None:
        """Get cache value."""
        cache_key = self._make_key(key)
        now = self._now()

        with self._lock:
            row = self._connection.execute(f"SELECT value, expire_at FROM {self._table} WHERE cache_key = ?", (cache_key,)).fetchone()
            if row is None:
                return default

            payload, expire_at = row
            if expire_at is not None and float(expire_at) <= now:
                self._connection.execute(f"DELETE FROM {self._table} WHERE cache_key = ?", (cache_key,))
                self._connection.commit()
                return default

            self._connection.execute(f"UPDATE {self._table} SET accessed_at = ? WHERE cache_key = ?", (now, cache_key))
            self._connection.commit()

        return self._serializer.loads(bytes(payload))

    def set(self, key: str, value: object, timeout: int | None | _DefaultCacheTimeout = NS_CACHE_DEFAULT_TIMEOUT) -> bool:
        """Set cache value."""
        cache_key = self._make_key(key)
        normalized_timeout = self._resolve_timeout(timeout)

        if normalized_timeout == 0:
            self.delete(key)
            return False
        if normalized_timeout is not None and normalized_timeout < 0:
            self.delete(key)
            return False

        now = self._now()
        expire_at = None if normalized_timeout is None else now + normalized_timeout
        payload = sqlite3.Binary(self._serializer.dumps(value))

        with self._lock:
            self._connection.execute(
                f"""
                INSERT INTO {self._table} (cache_key, value, expire_at, created_at, updated_at, accessed_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    value = excluded.value,
                    expire_at = excluded.expire_at,
                    updated_at = excluded.updated_at,
                    accessed_at = excluded.accessed_at
                """,
                (cache_key, payload, expire_at, now, now, now),
            )
            self._cull_if_needed_locked(now)
            self._connection.commit()

        return True

    def add(self, key: str, value: object, timeout: int | None | _DefaultCacheTimeout = NS_CACHE_DEFAULT_TIMEOUT) -> bool:
        """Set value only if key does not exist."""
        cache_key = self._make_key(key)
        normalized_timeout = self._resolve_timeout(timeout)

        if normalized_timeout == 0:
            return False
        if normalized_timeout is not None and normalized_timeout < 0:
            self.delete(key)
            return False

        now = self._now()
        expire_at = None if normalized_timeout is None else now + normalized_timeout
        payload = sqlite3.Binary(self._serializer.dumps(value))

        with self._lock:
            self._delete_expired_key_locked(cache_key, now)

            exists = self._connection.execute(f"SELECT 1 FROM {self._table} WHERE cache_key = ?", (cache_key,)).fetchone()
            if exists is not None:
                self._connection.commit()
                return False

            self._connection.execute(
                f"""
                INSERT INTO {self._table} (cache_key, value, expire_at, created_at, updated_at, accessed_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (cache_key, payload, expire_at, now, now, now),
            )
            self._cull_if_needed_locked(now)
            self._connection.commit()

        return True

    def delete(self, key: str) -> bool:
        """Delete cache key."""
        cache_key = self._make_key(key)

        with self._lock:
            cursor = self._connection.execute(f"DELETE FROM {self._table} WHERE cache_key = ?", (cache_key,))
            self._connection.commit()
            return int(cursor.rowcount or 0) > 0

    def exists(self, key: str) -> bool:
        """Check whether cache key exists."""
        cache_key = self._make_key(key)
        now = self._now()

        with self._lock:
            self._delete_expired_key_locked(cache_key, now)
            row = self._connection.execute(f"SELECT 1 FROM {self._table} WHERE cache_key = ?", (cache_key,)).fetchone()
            self._connection.commit()
            return row is not None

    def expire(self, key: str, timeout: int) -> bool:
        """Update key expiration."""
        if isinstance(timeout, bool) or not isinstance(timeout, int):
            raise NsCacheConfigurationError("cache expire timeout must be int")

        if timeout <= 0:
            return self.delete(key)

        cache_key = self._make_key(key)
        now = self._now()
        expire_at = now + timeout

        with self._lock:
            self._delete_expired_key_locked(cache_key, now)
            cursor = self._connection.execute(f"UPDATE {self._table} SET expire_at = ?, updated_at = ? WHERE cache_key = ?", (expire_at, now, cache_key))
            self._connection.commit()
            return int(cursor.rowcount or 0) > 0

    def persist(self, key: str) -> bool:
        """Remove key expiration."""
        cache_key = self._make_key(key)
        now = self._now()

        with self._lock:
            self._delete_expired_key_locked(cache_key, now)
            cursor = self._connection.execute(f"UPDATE {self._table} SET expire_at = NULL, updated_at = ? WHERE cache_key = ?", (now, cache_key))
            self._connection.commit()
            return int(cursor.rowcount or 0) > 0

    def ttl(self, key: str) -> int:
        """Return Redis-compatible TTL: -2 missing, -1 no expiration, >=0 remaining seconds."""
        cache_key = self._make_key(key)
        now = self._now()

        with self._lock:
            row = self._connection.execute(f"SELECT expire_at FROM {self._table} WHERE cache_key = ?", (cache_key,)).fetchone()
            if row is None:
                return -2

            expire_at = row[0]
            if expire_at is None:
                return -1

            remaining = int(float(expire_at) - now)
            if remaining < 0:
                self._connection.execute(f"DELETE FROM {self._table} WHERE cache_key = ?", (cache_key,))
                self._connection.commit()
                return -2

            return remaining

    def clear(self) -> bool:
        """Clear cache entries under current key prefix."""
        with self._lock:
            if not self._key_prefix:
                self._connection.execute(f"DELETE FROM {self._table}")
            else:
                escaped_prefix = self._escape_sql_like(self._key_prefix)
                self._connection.execute(
                    f"DELETE FROM {self._table} WHERE cache_key = ? OR cache_key LIKE ? ESCAPE '\\'",
                    (self._key_prefix, f"{escaped_prefix}:%"),
                )
            self._connection.commit()

        return True

    def get_many(self, keys: list[str]) -> dict[str, object]:
        """Batch get cache values."""
        if not keys:
            return {}

        result: dict[str, object] = {}
        for key in keys:
            value = self.get(key, _MISSING)
            if value is not _MISSING:
                result[key] = value

        return result

    def set_many(self, data: dict[str, object], timeout: int | None | _DefaultCacheTimeout = NS_CACHE_DEFAULT_TIMEOUT) -> list[str]:
        """Batch set cache values."""
        if not data:
            return []

        failed_keys: list[str] = []
        for key, value in data.items():
            if not self.set(key, value, timeout):
                failed_keys.append(key)

        return failed_keys

    def delete_many(self, keys: list[str]) -> int:
        """Batch delete cache keys."""
        if not keys:
            return 0

        deleted_count = 0
        for key in keys:
            if self.delete(key):
                deleted_count += 1

        return deleted_count

    def close(self) -> None:
        """Close SQLite connection."""
        with self._lock:
            try:
                self._connection.close()
            except Exception:  # noqa
                pass

    def _open_connection(self) -> sqlite3.Connection:
        """Open SQLite connection and enable WAL mode."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(str(self._db_path), timeout=self._config.sql_timeout_seconds, check_same_thread=False)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        connection.execute(f"PRAGMA busy_timeout={int(self._config.sql_timeout_seconds * 1000)}")
        connection.commit()
        return connection

    def _ensure_schema(self) -> None:
        """Create cache table automatically."""
        expire_index = f"idx_{self._table}_expire_at"
        accessed_index = f"idx_{self._table}_accessed_at"

        with self._lock:
            self._connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self._table} (
                    cache_key TEXT PRIMARY KEY,
                    value BLOB NOT NULL,
                    expire_at REAL NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    accessed_at REAL NOT NULL
                )
                """
            )
            self._connection.execute(f"CREATE INDEX IF NOT EXISTS {expire_index} ON {self._table}(expire_at)")
            self._connection.execute(f"CREATE INDEX IF NOT EXISTS {accessed_index} ON {self._table}(accessed_at)")
            self._connection.commit()

    def _delete_expired_key_locked(self, cache_key: str, now: float) -> None:
        """Delete one expired key under caller lock."""
        self._connection.execute(f"DELETE FROM {self._table} WHERE cache_key = ? AND expire_at IS NOT NULL AND expire_at <= ?", (cache_key, now))

    def _delete_expired_locked(self, now: float) -> None:
        """Delete expired keys under caller lock."""
        self._connection.execute(f"DELETE FROM {self._table} WHERE expire_at IS NOT NULL AND expire_at <= ?", (now,))

    def _cull_if_needed_locked(self, now: float) -> None:
        """Cull expired and oldest cache entries."""
        self._delete_expired_locked(now)

        row = self._connection.execute(f"SELECT COUNT(*) FROM {self._table}").fetchone()
        total_count = int(row[0] if row is not None else 0)
        if total_count <= self._config.sql_max_entries:
            return

        overflow = total_count - self._config.sql_max_entries
        delete_limit = max(overflow, total_count // self._config.sql_cull_frequency, 1)
        self._connection.execute(
            f"""
            DELETE FROM {self._table}
            WHERE cache_key IN (
                SELECT cache_key
                FROM {self._table}
                ORDER BY accessed_at ASC
                LIMIT ?
            )
            """,
            (delete_limit,),
        )

    @classmethod
    def _validate_table_name(cls, value: object) -> str:
        """Validate SQLite table name."""
        table_name = str(value or "").strip()
        if not cls._TABLE_NAME_PATTERN.fullmatch(table_name):
            raise NsCacheConfigurationError("cache sql_table must match pattern ^[A-Za-z_][A-Za-z0-9_]*$")
        return table_name

    @staticmethod
    def _resolve_db_path(location: str) -> Path:
        """Resolve SQLite database path."""
        if not location:
            return DATA_DIR / "ns_cache.sqlite3"

        db_path = Path(location)
        if db_path.is_absolute():
            return db_path

        return DATA_DIR / db_path

    @staticmethod
    def _escape_sql_like(value: str) -> str:
        """Escape SQLite LIKE value."""
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class _RedisCompatibleCacheBackend(_BaseCacheBackend):
    """Redis / Valkey cache backend selected by explicit config."""

    def __init__(self, config: NsCacheConfig) -> None:
        """Initialize Redis-compatible backend."""
        super().__init__(config)
        self._backend_name = config.resolved_backend()
        if self._backend_name not in {"redis", "valkey"}:
            raise NsCacheConfigurationError("redis-compatible backend requires redis or valkey")

        self._module: Any = self._import_backend_module()
        self._client: Any = self._build_client()

    def get(self, key: str, default: object | None = None) -> object | None:
        """Get cache value."""
        cache_key = self._make_key(key)

        try:
            payload = self._client.get(cache_key)
        except self._connection_error_types() as _error:
            raise self._build_connection_error(_error) from _error

        if payload is None:
            return default

        return self._serializer.loads(payload)

    def set(self, key: str, value: object, timeout: int | None | _DefaultCacheTimeout = NS_CACHE_DEFAULT_TIMEOUT) -> bool:
        """Set cache value."""
        cache_key = self._make_key(key)
        normalized_timeout = self._resolve_timeout(timeout)

        if normalized_timeout == 0:
            self.delete(key)
            return False
        if normalized_timeout is not None and normalized_timeout < 0:
            self.delete(key)
            return False

        payload = self._serializer.dumps(value)

        try:
            return bool(self._client.set(name=cache_key, value=payload, ex=normalized_timeout))
        except self._connection_error_types() as _error:
            raise self._build_connection_error(_error) from _error

    def add(self, key: str, value: object, timeout: int | None | _DefaultCacheTimeout = NS_CACHE_DEFAULT_TIMEOUT) -> bool:
        """Set cache value only if key does not exist."""
        cache_key = self._make_key(key)
        normalized_timeout = self._resolve_timeout(timeout)

        if normalized_timeout == 0:
            return False
        if normalized_timeout is not None and normalized_timeout < 0:
            self.delete(key)
            return False

        payload = self._serializer.dumps(value)

        try:
            return bool(self._client.set(name=cache_key, value=payload, ex=normalized_timeout, nx=True))
        except self._connection_error_types() as _error:
            raise self._build_connection_error(_error) from _error

    def delete(self, key: str) -> bool:
        """Delete cache key."""
        cache_key = self._make_key(key)

        try:
            return int(self._client.delete(cache_key) or 0) > 0
        except self._connection_error_types() as _error:
            raise self._build_connection_error(_error) from _error

    def exists(self, key: str) -> bool:
        """Check whether key exists."""
        cache_key = self._make_key(key)

        try:
            return int(self._client.exists(cache_key) or 0) > 0
        except self._connection_error_types() as _error:
            raise self._build_connection_error(_error) from _error

    def expire(self, key: str, timeout: int) -> bool:
        """Update key expiration."""
        if isinstance(timeout, bool) or not isinstance(timeout, int):
            raise NsCacheConfigurationError("cache expire timeout must be int")

        if timeout <= 0:
            return self.delete(key)

        cache_key = self._make_key(key)

        try:
            return bool(self._client.expire(cache_key, timeout))
        except self._connection_error_types() as _error:
            raise self._build_connection_error(_error) from _error

    def persist(self, key: str) -> bool:
        """Remove key expiration."""
        cache_key = self._make_key(key)

        try:
            if int(self._client.exists(cache_key) or 0) <= 0:
                return False
            return bool(self._client.persist(cache_key))
        except self._connection_error_types() as _error:
            raise self._build_connection_error(_error) from _error

    def ttl(self, key: str) -> int:
        """Return Redis-compatible TTL."""
        cache_key = self._make_key(key)

        try:
            return int(self._client.ttl(cache_key))
        except self._connection_error_types() as _error:
            raise self._build_connection_error(_error) from _error

    def clear(self) -> bool:
        """Clear cache keys under current key prefix."""
        if not self._key_prefix:
            raise NsCacheConfigurationError("cache key_prefix is required when clearing redis-compatible cache")

        direct_key = self._key_prefix
        pattern = f"{self._key_prefix}:*"
        batch_size = 1000
        batch: list[Any] = []

        try:
            self._client.delete(direct_key)

            for cache_key in self._client.scan_iter(match=pattern, count=batch_size):
                batch.append(cache_key)
                if len(batch) >= batch_size:
                    self._client.delete(*batch)
                    batch.clear()

            if batch:
                self._client.delete(*batch)

            return True
        except self._connection_error_types() as _error:
            raise self._build_connection_error(_error) from _error

    def get_many(self, keys: list[str]) -> dict[str, object]:
        """Batch get cache values."""
        if not keys:
            return {}

        cache_keys = [self._make_key(key) for key in keys]

        try:
            payloads = self._client.mget(cache_keys)
        except self._connection_error_types() as _error:
            raise self._build_connection_error(_error) from _error

        result: dict[str, object] = {}
        for key, payload in zip(keys, payloads):
            if payload is None:
                continue
            result[key] = self._serializer.loads(payload)

        return result

    def set_many(self, data: dict[str, object], timeout: int | None | _DefaultCacheTimeout = NS_CACHE_DEFAULT_TIMEOUT) -> list[str]:
        """Batch set cache values."""
        if not data:
            return []

        normalized_timeout = self._resolve_timeout(timeout)

        if normalized_timeout == 0:
            return list(data.keys())
        if normalized_timeout is not None and normalized_timeout < 0:
            self.delete_many(list(data.keys()))
            return list(data.keys())

        entries: list[tuple[str, str, bytes]] = []
        for key, value in data.items():
            entries.append((key, self._make_key(key), self._serializer.dumps(value)))

        try:
            pipeline = self._client.pipeline(transaction=False)
            for _, cache_key, payload in entries:
                pipeline.set(name=cache_key, value=payload, ex=normalized_timeout)
            results = pipeline.execute()
        except self._connection_error_types() as _error:
            raise self._build_connection_error(_error) from _error

        return [key for (key, _, _), result in zip(entries, results) if not bool(result)]

    def delete_many(self, keys: list[str]) -> int:
        """Batch delete cache keys."""
        if not keys:
            return 0

        cache_keys = [self._make_key(key) for key in keys]

        try:
            return int(self._client.delete(*cache_keys) or 0)
        except self._connection_error_types() as _error:
            raise self._build_connection_error(_error) from _error

    def close(self) -> None:
        """Close Redis / Valkey client resources."""
        try:
            close_method = getattr(self._client, "close", None)
            if callable(close_method):
                close_method()
        except Exception:  # noqa
            pass

        try:
            connection_pool = getattr(self._client, "connection_pool", None)
            disconnect_method = getattr(connection_pool, "disconnect", None)
            if callable(disconnect_method):
                disconnect_method()
        except Exception:  # noqa
            pass

    def _import_backend_module(self) -> Any:
        """Import explicitly configured backend client module."""
        module_name = "redis" if self._backend_name == "redis" else "valkey"

        try:
            return import_module(module_name)
        except ImportError as _error:
            raise NsCacheConfigurationError(f"{module_name} client is not installed") from _error

    def _build_client(self) -> Any:
        """Build Redis / Valkey client without runtime fallback."""
        if not self._config.location:
            raise NsCacheConfigurationError(f"{self._backend_name} cache location is required")

        try:
            return self._module.from_url(
                self._config.location,
                socket_timeout=self._config.socket_timeout,
                socket_connect_timeout=self._config.socket_connect_timeout,
                max_connections=self._config.max_connections,
                health_check_interval=self._config.health_check_interval,
                decode_responses=False,
            )
        except (TypeError, ValueError) as _error:
            raise NsCacheConfigurationError("invalid redis-compatible cache configuration") from _error

    def _connection_error_types(self) -> tuple[type[BaseException], ...]:
        """Return backend-specific connection error types."""
        error_types: list[type[BaseException]] = [OSError, ConnectionError, TimeoutError]

        for attr_name in ("RedisError", "ValkeyError"):
            error_type = getattr(self._module, attr_name, None)
            if isinstance(error_type, type) and issubclass(error_type, BaseException):
                error_types.append(error_type)

        exceptions_module = getattr(self._module, "exceptions", None)
        for attr_name in ("RedisError", "ValkeyError", "ConnectionError", "TimeoutError"):
            error_type = getattr(exceptions_module, attr_name, None)
            if isinstance(error_type, type) and issubclass(error_type, BaseException):
                error_types.append(error_type)

        return tuple(dict.fromkeys(error_types))

    def _build_connection_error(self, _error: BaseException) -> NsCacheConnectionError:
        """Build normalized cache connection error."""
        return NsCacheConnectionError(f"{self._backend_name} cache backend operation failed")


class NsCacheClient:
    """Thread-safe process-local singleton cache client.

    Singleton identity is controlled by client name.
    Different config under the same client name is rejected.
    """

    name: str
    config: NsCacheConfig
    _backend: _CacheBackend

    _lock: ClassVar[RLock] = RLock()
    _instances: ClassVar[dict[str, "NsCacheClient"]] = {}
    _default_config: ClassVar[NsCacheConfig | None] = None

    def __new__(cls, name: str = "default", config: NsCacheConfig | None = None) -> "NsCacheClient":
        """Create or return named singleton instance."""
        normalized_name = cls._normalize_client_name(name)

        with cls._lock:
            existing_client = cls._instances.get(normalized_name)
            if existing_client is not None:
                if config is not None and config != existing_client.config:
                    raise NsCacheConfigurationError(f"cache client already exists with different config: {normalized_name}")
                return existing_client

            selected_config = config or cls._default_config or cls._load_config_from_ns_config()
            instance = super().__new__(cls)
            instance.name = normalized_name
            instance.config = selected_config
            instance._backend = cls._build_backend(selected_config)
            cls._instances[normalized_name] = instance
            return instance

    def __init__(self, name: str = "default", config: NsCacheConfig | None = None) -> None:
        """Keep __init__ idempotent because singleton construction is handled in __new__."""
        _ = (name, config)

    @classmethod
    def configure_default(cls, config: NsCacheConfig) -> None:
        """Configure default cache config for later default client creation."""
        if not isinstance(config, NsCacheConfig):
            raise NsCacheConfigurationError("default cache config must be NsCacheConfig")

        with cls._lock:
            cls._default_config = config

    @classmethod
    def get_default(cls) -> "NsCacheClient":
        """Get default cache client."""
        return cls("default")

    @classmethod
    def get_or_create(cls, name: str = "default", config: NsCacheConfig | None = None) -> "NsCacheClient":
        """Compatibility helper for named singleton access."""
        return cls(name, config)

    @classmethod
    def close_all(cls) -> None:
        """Close all process-local cache clients."""
        with cls._lock:
            clients = list(cls._instances.values())
            cls._instances.clear()

        for client in clients:
            client.close()

    def get(self, key: str, default: object | None = None) -> object | None:
        """Get cache value."""
        return self._backend.get(key, default)

    def set(self, key: str, value: object, timeout: int | None | _DefaultCacheTimeout = NS_CACHE_DEFAULT_TIMEOUT) -> bool:
        """Set cache value."""
        return self._backend.set(key, value, timeout)

    def add(self, key: str, value: object, timeout: int | None | _DefaultCacheTimeout = NS_CACHE_DEFAULT_TIMEOUT) -> bool:
        """Set cache value only when key does not exist."""
        return self._backend.add(key, value, timeout)

    def delete(self, key: str) -> bool:
        """Delete cache key."""
        return self._backend.delete(key)

    def exists(self, key: str) -> bool:
        """Check whether key exists."""
        return self._backend.exists(key)

    def expire(self, key: str, timeout: int) -> bool:
        """Update key expiration."""
        return self._backend.expire(key, timeout)

    def persist(self, key: str) -> bool:
        """Remove key expiration."""
        return self._backend.persist(key)

    def ttl(self, key: str) -> int:
        """Return Redis-compatible TTL."""
        return self._backend.ttl(key)

    def clear(self) -> bool:
        """Clear cache keys under current prefix."""
        return self._backend.clear()

    def get_many(self, keys: list[str]) -> dict[str, object]:
        """Batch get cache values."""
        return self._backend.get_many(keys)

    def set_many(self, data: dict[str, object], timeout: int | None | _DefaultCacheTimeout = NS_CACHE_DEFAULT_TIMEOUT) -> list[str]:
        """Batch set cache values."""
        return self._backend.set_many(data, timeout)

    def delete_many(self, keys: list[str]) -> int:
        """Batch delete cache keys."""
        return self._backend.delete_many(keys)

    def close(self) -> None:
        """Close cache backend resources and remove singleton reference."""
        with self.__class__._lock:
            existing_client: NsCacheClient | None = self.__class__._instances.get(self.name)
            if existing_client is self:
                self.__class__._instances.pop(self.name, None)

        self._backend.close()

    @staticmethod
    def _normalize_client_name(name: str) -> str:
        """Normalize singleton client name."""
        if not isinstance(name, str) or not name.strip():
            raise NsCacheConfigurationError("cache client name must be a non-empty str")
        return name.strip()

    @staticmethod
    def _load_config_from_ns_config() -> NsCacheConfig:
        """Load default cache config from ns_config."""
        from ns_common.config import ns_config

        return ns_config.cache_config

    @staticmethod
    def _build_backend(config: NsCacheConfig) -> _CacheBackend:
        """Build backend by explicit configuration."""
        resolved_backend = config.resolved_backend()
        if resolved_backend == "sql_wal":
            return _SqlWalCacheBackend(config)
        if resolved_backend in {"redis", "valkey"}:
            return _RedisCompatibleCacheBackend(config)
        raise NsCacheConfigurationError(f"unsupported cache backend: {config.backend}")
