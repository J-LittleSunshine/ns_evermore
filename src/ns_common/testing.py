# -*- coding: utf-8 -*-
from __future__ import annotations

import inspect
import re
import socket as socket_module
import tempfile
import uuid
from collections.abc import AsyncIterator, Iterator, Mapping
from contextlib import (
    AbstractAsyncContextManager,
    AbstractContextManager,
    asynccontextmanager,
    contextmanager,
)
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any

from ns_common.config import NsConfig
from ns_common.exceptions import NsStateError, NsValidationError
from ns_common.observability import (
    DEFAULT_IN_MEMORY_SINK_CAPACITY,
    InMemoryDiagnosticSnapshotSink,
    InMemoryMetricsSink,
    InMemoryTraceSink,
)
from ns_common.time import ControlledClock, UTC_EPOCH


DEFAULT_REDIS_CLEANUP_BATCH_SIZE = 500
DEFAULT_TEST_REDIS_KEY_PREFIX = "ns_test"

_SAFE_RESOURCE_PART_PATTERN = re.compile(r"[A-Za-z0-9_.-]+\Z")
_SAFE_FILE_PREFIX_PATTERN = re.compile(r"[A-Za-z0-9_.-]+\Z")
_SAFE_REDIS_KEY_SEGMENT_PATTERN = re.compile(r"[A-Za-z0-9_.-]+\Z")


def _validate_resource_part(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise NsValidationError(
            f"{field_name} must be a string.",
            details={
                "field": field_name,
                "actual_type": type(value).__name__,
            },
        )
    if (
        not value
        or value != value.strip()
        or len(value) > 128
        or _SAFE_RESOURCE_PART_PATTERN.fullmatch(value) is None
    ):
        raise NsValidationError(
            f"{field_name} must use the safe test resource format.",
            details={
                "field": field_name,
                "maximum_length": 128,
                "allowed_pattern": _SAFE_RESOURCE_PART_PATTERN.pattern,
            },
        )
    return value


def _validate_cleanup_batch_size(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 10_000:
        raise NsValidationError(
            "batch_size must be an integer from 1 through 10000.",
            details={
                "field": "batch_size",
                "actual_type": type(value).__name__,
                "minimum": 1,
                "maximum": 10_000,
            },
        )
    return value


def _require_client_method(client: object, method_name: str) -> Any:
    method = getattr(client, method_name, None)
    if not callable(method):
        raise NsValidationError(
            f"Redis client must provide callable {method_name}().",
            details={
                "field": "client",
                "required_method": method_name,
                "actual_type": type(client).__name__,
            },
        )
    return method


def _discard_unawaited(value: object) -> None:
    cancel = getattr(value, "cancel", None)
    if callable(cancel):
        cancel()
    close = getattr(value, "close", None)
    if callable(close):
        close()


def _normalize_deleted_count(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if not isinstance(value, int) or value < 0:
        raise NsStateError(
            "Redis client returned an invalid delete count.",
            details={
                "operation": "delete",
                "actual_type": type(value).__name__,
            },
        )
    return value


def _clone_config_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            key: _clone_config_value(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_clone_config_value(item) for item in value]
    if isinstance(value, tuple):
        return [_clone_config_value(item) for item in value]
    return value


def _deep_merge_config(
    base: Mapping[object, object],
    override: Mapping[object, object],
) -> dict[object, object]:
    merged = {
        key: _clone_config_value(value)
        for key, value in base.items()
    }
    for key, value in override.items():
        current = merged.get(key)
        if isinstance(current, Mapping) and isinstance(value, Mapping):
            merged[key] = _deep_merge_config(current, value)
        else:
            merged[key] = _clone_config_value(value)
    return merged


@dataclass(frozen=True, slots=True)
class NsTemporaryDirectories:
    """All filesystem paths owned by one test resource factory."""

    root: Path
    data: Path
    etc: Path
    log: Path
    tmp: Path

    def contains(self, path: str | Path) -> bool:
        try:
            Path(path).resolve().relative_to(self.root)
        except (OSError, RuntimeError, ValueError):
            return False
        return True


@dataclass(frozen=True, slots=True)
class NsRedisNamespace:
    """An isolated Redis/Valkey key prefix with strict scoped cleanup.

    The namespace is client-agnostic. It works with synchronous or asynchronous
    Redis-compatible clients that expose ``scan_iter()`` and ``delete()`` and
    never invokes database-wide commands such as ``FLUSHDB``.
    """

    key_prefix: str
    namespace: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "key_prefix",
            _validate_resource_part(self.key_prefix, field_name="key_prefix"),
        )
        object.__setattr__(
            self,
            "namespace",
            _validate_resource_part(self.namespace, field_name="namespace"),
        )

    @property
    def prefix(self) -> str:
        return f"{self.key_prefix}:{self.namespace}:"

    @property
    def match_pattern(self) -> str:
        return f"{self.prefix}*"

    def key(self, *segments: str) -> str:
        if not segments:
            raise NsValidationError(
                "At least one Redis key segment is required.",
                details={"field": "segments"},
            )
        normalized_segments: list[str] = []
        for index, segment in enumerate(segments):
            if (
                not isinstance(segment, str)
                or not segment
                or segment != segment.strip()
                or len(segment) > 256
                or _SAFE_REDIS_KEY_SEGMENT_PATTERN.fullmatch(segment) is None
            ):
                raise NsValidationError(
                    "Redis key segment must use the safe test key format.",
                    details={
                        "field": f"segments[{index}]",
                        "maximum_length": 256,
                        "allowed_pattern": _SAFE_REDIS_KEY_SEGMENT_PATTERN.pattern,
                    },
                )
            normalized_segments.append(segment)
        return f"{self.prefix}{':'.join(normalized_segments)}"

    def owns(self, key: object) -> bool:
        if isinstance(key, str):
            return key.startswith(self.prefix)
        if isinstance(key, bytes):
            return key.startswith(self.prefix.encode("utf-8"))
        return False

    def cleanup(
        self,
        client: object,
        *,
        batch_size: int = DEFAULT_REDIS_CLEANUP_BATCH_SIZE,
    ) -> int:
        """Delete only keys owned by this namespace using a sync client."""

        normalized_batch_size = _validate_cleanup_batch_size(batch_size)
        scan_iter = _require_client_method(client, "scan_iter")
        delete = _require_client_method(client, "delete")
        iterator = scan_iter(
            match=self.match_pattern,
            count=normalized_batch_size,
        )
        if inspect.isawaitable(iterator) or hasattr(iterator, "__aiter__"):
            _discard_unawaited(iterator)
            raise NsValidationError(
                "cleanup() requires a synchronous Redis client.",
                details={"field": "client", "operation": "cleanup"},
            )
        try:
            keys = iter(iterator)
        except TypeError:
            raise NsValidationError(
                "Redis scan_iter() must return a synchronous iterator.",
                details={"field": "client", "operation": "scan_iter"},
            ) from None

        deleted_count = 0
        batch: list[str | bytes] = []
        for key in keys:
            if not isinstance(key, (str, bytes)) or not self.owns(key):
                raise NsStateError(
                    "Redis namespace scan escaped its owned prefix.",
                    details={
                        "operation": "scan_iter",
                        "namespace": self.namespace,
                    },
                )
            batch.append(key)
            if len(batch) < normalized_batch_size:
                continue
            deleted_count += self._delete_sync_batch(delete, batch)
            batch.clear()

        if batch:
            deleted_count += self._delete_sync_batch(delete, batch)
        return deleted_count

    async def acleanup(
        self,
        client: object,
        *,
        batch_size: int = DEFAULT_REDIS_CLEANUP_BATCH_SIZE,
    ) -> int:
        """Delete only keys owned by this namespace using an async client."""

        normalized_batch_size = _validate_cleanup_batch_size(batch_size)
        scan_iter = _require_client_method(client, "scan_iter")
        delete = _require_client_method(client, "delete")
        iterator = scan_iter(
            match=self.match_pattern,
            count=normalized_batch_size,
        )
        if inspect.isawaitable(iterator):
            iterator = await iterator
        if not hasattr(iterator, "__aiter__"):
            raise NsValidationError(
                "Redis scan_iter() must return an asynchronous iterator.",
                details={"field": "client", "operation": "scan_iter"},
            )

        deleted_count = 0
        batch: list[str | bytes] = []
        async for key in iterator:
            if not isinstance(key, (str, bytes)) or not self.owns(key):
                raise NsStateError(
                    "Redis namespace scan escaped its owned prefix.",
                    details={
                        "operation": "scan_iter",
                        "namespace": self.namespace,
                    },
                )
            batch.append(key)
            if len(batch) < normalized_batch_size:
                continue
            deleted_count += await self._delete_async_batch(delete, batch)
            batch.clear()

        if batch:
            deleted_count += await self._delete_async_batch(delete, batch)
        return deleted_count

    @contextmanager
    def manage(
        self,
        client: object,
        *,
        batch_size: int = DEFAULT_REDIS_CLEANUP_BATCH_SIZE,
    ) -> Iterator["NsRedisNamespace"]:
        """Start clean and strictly clean this namespace again on exit."""

        self.cleanup(client, batch_size=batch_size)
        try:
            yield self
        finally:
            self.cleanup(client, batch_size=batch_size)

    @asynccontextmanager
    async def amanage(
        self,
        client: object,
        *,
        batch_size: int = DEFAULT_REDIS_CLEANUP_BATCH_SIZE,
    ) -> AsyncIterator["NsRedisNamespace"]:
        """Async variant of :meth:`manage`."""

        await self.acleanup(client, batch_size=batch_size)
        try:
            yield self
        finally:
            await self.acleanup(client, batch_size=batch_size)

    @staticmethod
    def _delete_sync_batch(delete: Any, batch: list[str | bytes]) -> int:
        result = delete(*batch)
        if inspect.isawaitable(result):
            _discard_unawaited(result)
            raise NsValidationError(
                "cleanup() requires a synchronous Redis delete().",
                details={"field": "client", "operation": "delete"},
            )
        return _normalize_deleted_count(result)

    @staticmethod
    async def _delete_async_batch(delete: Any, batch: list[str | bytes]) -> int:
        result = delete(*batch)
        if inspect.isawaitable(result):
            result = await result
        return _normalize_deleted_count(result)


@dataclass(frozen=True, slots=True)
class NsTemporaryConfig:
    """An immutable config snapshot and its explicit temporary file."""

    snapshot: NsConfig
    path: Path
    directories: NsTemporaryDirectories
    redis_namespace: NsRedisNamespace
    environment: str

    @property
    def config(self) -> NsConfig:
        return self.snapshot


@dataclass(frozen=True, slots=True)
class NsInMemorySinkBundle:
    """Fresh in-memory observability sinks owned by one test."""

    metrics: InMemoryMetricsSink
    traces: InMemoryTraceSink
    diagnostics: InMemoryDiagnosticSnapshotSink

    def __post_init__(self) -> None:
        expected_types = {
            "metrics": InMemoryMetricsSink,
            "traces": InMemoryTraceSink,
            "diagnostics": InMemoryDiagnosticSnapshotSink,
        }
        for field_name, expected_type in expected_types.items():
            value = getattr(self, field_name)
            if not isinstance(value, expected_type):
                raise NsValidationError(
                    f"{field_name} must be a {expected_type.__name__}.",
                    details={
                        "field": field_name,
                        "actual_type": type(value).__name__,
                    },
                )

    @property
    def metrics_sink(self) -> InMemoryMetricsSink:
        return self.metrics

    @property
    def trace_sink(self) -> InMemoryTraceSink:
        return self.traces

    @property
    def diagnostic_snapshot_sink(self) -> InMemoryDiagnosticSnapshotSink:
        return self.diagnostics

    def clear(self) -> int:
        return (
            self.metrics.clear()
            + self.traces.clear()
            + self.diagnostics.clear()
        )

    async def aclose(self) -> None:
        try:
            await self.diagnostics.aclose()
        finally:
            try:
                await self.traces.aclose()
            finally:
                await self.metrics.aclose()
                self.clear()

    async def __aenter__(self) -> "NsInMemorySinkBundle":
        return self

    async def __aexit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        await self.aclose()


class NsReservedPort:
    """An OS-assigned TCP port kept bound until explicitly released."""

    def __init__(self, reserved_socket: socket_module.socket) -> None:
        if not isinstance(reserved_socket, socket_module.socket):
            raise NsValidationError(
                "reserved_socket must be a socket.",
                details={
                    "field": "reserved_socket",
                    "actual_type": type(reserved_socket).__name__,
                },
            )
        if reserved_socket.family != socket_module.AF_INET:
            raise NsValidationError(
                "reserved_socket must use the IPv4 address family.",
                details={"field": "reserved_socket"},
            )
        if reserved_socket.getsockopt(
            socket_module.SOL_SOCKET,
            socket_module.SO_TYPE,
        ) != socket_module.SOCK_STREAM:
            raise NsValidationError(
                "reserved_socket must be a TCP stream socket.",
                details={"field": "reserved_socket"},
            )
        try:
            address = reserved_socket.getsockname()
        except OSError:
            raise NsValidationError(
                "reserved_socket must already be bound.",
                details={"field": "reserved_socket"},
            ) from None
        if not isinstance(address, tuple) or len(address) < 2 or int(address[1]) <= 0:
            raise NsValidationError(
                "reserved_socket must already be bound to a non-zero port.",
                details={"field": "reserved_socket"},
            )
        self._socket: socket_module.socket | None = reserved_socket
        self._host = str(address[0])
        self._port = int(address[1])
        self._lock = RLock()

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def is_released(self) -> bool:
        with self._lock:
            return self._socket is None

    @property
    def socket(self) -> socket_module.socket:
        with self._lock:
            if self._socket is None:
                raise NsStateError(
                    "Reserved TCP port has already been released.",
                    details={"operation": "get_socket"},
                )
            return self._socket

    def fileno(self) -> int:
        return self.socket.fileno()

    def release(self) -> bool:
        with self._lock:
            reserved_socket = self._socket
            self._socket = None
        if reserved_socket is None:
            return False
        reserved_socket.close()
        return True

    close = release

    def __enter__(self) -> "NsReservedPort":
        if self.is_released:
            raise NsStateError(
                "Released TCP port reservation cannot be re-entered.",
                details={"operation": "enter"},
            )
        return self

    def __exit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        self.release()


class NsTestResourceFactory:
    """Per-test owner for filesystem and socket resources.

    The factory never changes environment variables, repository path globals,
    global config singletons, cache clients, or observability sinks.
    """

    def __init__(
        self,
        *,
        base_directory: str | Path | None = None,
        prefix: str = "ns-test-",
    ) -> None:
        if (
            not isinstance(prefix, str)
            or not prefix
            or len(prefix) > 64
            or _SAFE_FILE_PREFIX_PATTERN.fullmatch(prefix) is None
        ):
            raise NsValidationError(
                "prefix must use the safe temporary directory format.",
                details={
                    "field": "prefix",
                    "maximum_length": 64,
                    "allowed_pattern": _SAFE_FILE_PREFIX_PATTERN.pattern,
                },
            )

        parent: Path | None = None
        if base_directory is not None:
            if not isinstance(base_directory, (str, Path)):
                raise NsValidationError(
                    "base_directory must be an existing directory.",
                    details={
                        "field": "base_directory",
                        "actual_type": type(base_directory).__name__,
                    },
                )
            try:
                parent = Path(base_directory).resolve(strict=True)
            except (OSError, RuntimeError, ValueError):
                raise NsValidationError(
                    "base_directory must be an existing directory.",
                    details={"field": "base_directory"},
                ) from None
            if not parent.is_dir():
                raise NsValidationError(
                    "base_directory must be an existing directory.",
                    details={"field": "base_directory"},
                )

        self._lock = RLock()
        self._closed = False
        self._ports: list[NsReservedPort] = []
        self._temporary_directory = tempfile.TemporaryDirectory(
            prefix=prefix,
            dir=None if parent is None else str(parent),
        )
        root = Path(self._temporary_directory.name).resolve()
        directories = NsTemporaryDirectories(
            root=root,
            data=root / "data",
            etc=root / "etc",
            log=root / "log",
            tmp=root / "tmp",
        )
        for directory in (
            directories.data,
            directories.etc,
            directories.log,
            directories.tmp,
        ):
            directory.mkdir(parents=True, exist_ok=False)
        self._directories = directories

    @property
    def directories(self) -> NsTemporaryDirectories:
        with self._lock:
            self._require_open()
            return self._directories

    @property
    def is_closed(self) -> bool:
        with self._lock:
            return self._closed

    def create_temporary_config(
        self,
        overrides: Mapping[object, object] | None = None,
        *,
        environment: str = "test",
        effective_at: datetime | str | None = None,
        filename: str | None = None,
        redis_namespace: NsRedisNamespace | None = None,
    ) -> NsTemporaryConfig:
        with self._lock:
            self._require_open()
            if overrides is not None and not isinstance(overrides, Mapping):
                raise NsValidationError(
                    "overrides must be a mapping.",
                    details={
                        "field": "overrides",
                        "actual_type": type(overrides).__name__,
                    },
                )
            namespace = (
                self._create_redis_namespace_locked(
                    scope="config",
                    key_prefix=DEFAULT_TEST_REDIS_KEY_PREFIX,
                )
                if redis_namespace is None
                else redis_namespace
            )
            if not isinstance(namespace, NsRedisNamespace):
                raise NsValidationError(
                    "redis_namespace must be an NsRedisNamespace.",
                    details={
                        "field": "redis_namespace",
                        "actual_type": type(namespace).__name__,
                    },
                )
            config_filename = self._resolve_config_filename(filename)
            config_path = self._directories.etc / config_filename
            if config_path.exists():
                raise NsStateError(
                    "Temporary config file already exists.",
                    details={
                        "operation": "create_temporary_config",
                        "filename": config_filename,
                    },
                )
            raw_config = self._build_isolated_config(
                {} if overrides is None else overrides,
                redis_namespace=namespace,
            )
            snapshot = NsConfig.resolve(
                raw_config,
                environment=environment,
                effective_at=(UTC_EPOCH if effective_at is None else effective_at),
            )
            snapshot.save(config_path, environment=environment)
            return NsTemporaryConfig(
                snapshot=snapshot,
                path=config_path,
                directories=self._directories,
                redis_namespace=namespace,
                environment=environment.strip().lower(),
            )

    def create_controlled_clock(
        self,
        *,
        utc_start: datetime = UTC_EPOCH,
        monotonic_start: float = 0.0,
    ) -> ControlledClock:
        with self._lock:
            self._require_open()
            return ControlledClock(
                utc_start=utc_start,
                monotonic_start=monotonic_start,
            )

    def create_in_memory_sinks(
        self,
        *,
        capacity: int = DEFAULT_IN_MEMORY_SINK_CAPACITY,
    ) -> NsInMemorySinkBundle:
        with self._lock:
            self._require_open()
            return NsInMemorySinkBundle(
                metrics=InMemoryMetricsSink(capacity=capacity),
                traces=InMemoryTraceSink(capacity=capacity),
                diagnostics=InMemoryDiagnosticSnapshotSink(capacity=capacity),
            )

    def reserve_tcp_port(self, *, host: str = "127.0.0.1") -> NsReservedPort:
        if not isinstance(host, str) or not host or host != host.strip():
            raise NsValidationError(
                "host must be a non-empty string without surrounding whitespace.",
                details={
                    "field": "host",
                    "actual_type": type(host).__name__,
                },
            )
        with self._lock:
            self._require_open()
            reserved_socket = socket_module.socket(
                socket_module.AF_INET,
                socket_module.SOCK_STREAM,
            )
            try:
                reserved_socket.bind((host, 0))
                reserved_socket.listen(1)
                reservation = NsReservedPort(reserved_socket)
            except BaseException:
                reserved_socket.close()
                raise
            self._ports.append(reservation)
            return reservation

    def create_redis_namespace(
        self,
        *,
        scope: str = "runtime",
        key_prefix: str = DEFAULT_TEST_REDIS_KEY_PREFIX,
    ) -> NsRedisNamespace:
        with self._lock:
            self._require_open()
            return self._create_redis_namespace_locked(
                scope=scope,
                key_prefix=key_prefix,
            )

    def manage_redis_namespace(
        self,
        client: object,
        *,
        scope: str = "runtime",
        key_prefix: str = DEFAULT_TEST_REDIS_KEY_PREFIX,
        batch_size: int = DEFAULT_REDIS_CLEANUP_BATCH_SIZE,
    ) -> AbstractContextManager[NsRedisNamespace]:
        namespace = self.create_redis_namespace(
            scope=scope,
            key_prefix=key_prefix,
        )
        return namespace.manage(client, batch_size=batch_size)

    def amanage_redis_namespace(
        self,
        client: object,
        *,
        scope: str = "runtime",
        key_prefix: str = DEFAULT_TEST_REDIS_KEY_PREFIX,
        batch_size: int = DEFAULT_REDIS_CLEANUP_BATCH_SIZE,
    ) -> AbstractAsyncContextManager[NsRedisNamespace]:
        namespace = self.create_redis_namespace(
            scope=scope,
            key_prefix=key_prefix,
        )
        return namespace.amanage(client, batch_size=batch_size)

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            reservations = tuple(reversed(self._ports))
            self._ports.clear()
        first_error: Exception | None = None
        try:
            for reservation in reservations:
                try:
                    reservation.release()
                except Exception as error:
                    if first_error is None:
                        first_error = error
        finally:
            try:
                self._temporary_directory.cleanup()
            except Exception as error:
                if first_error is None:
                    first_error = error
        if first_error is not None:
            raise first_error

    def __enter__(self) -> "NsTestResourceFactory":
        with self._lock:
            self._require_open()
        return self

    def __exit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        self.close()

    def _require_open(self) -> None:
        if self._closed:
            raise NsStateError(
                "Test resource factory is closed.",
                details={"operation": "create_test_resource"},
            )

    def _create_redis_namespace_locked(
        self,
        *,
        scope: str,
        key_prefix: str,
    ) -> NsRedisNamespace:
        normalized_scope = _validate_resource_part(scope, field_name="scope")
        if len(normalized_scope) > 64:
            raise NsValidationError(
                "scope exceeds the safe test namespace length.",
                details={
                    "field": "scope",
                    "maximum_length": 64,
                },
            )
        normalized_prefix = _validate_resource_part(
            key_prefix,
            field_name="key_prefix",
        )
        return NsRedisNamespace(
            key_prefix=normalized_prefix,
            namespace=f"{normalized_scope}_{uuid.uuid4().hex}",
        )

    @staticmethod
    def _resolve_config_filename(filename: str | None) -> str:
        if filename is None:
            return f"ns_config.test.{uuid.uuid4().hex}.json"
        if (
            not isinstance(filename, str)
            or not filename
            or filename != filename.strip()
            or Path(filename).name != filename
            or len(filename) > 128
            or _SAFE_FILE_PREFIX_PATTERN.fullmatch(filename) is None
        ):
            raise NsValidationError(
                "filename must be a safe basename.",
                details={
                    "field": "filename",
                    "maximum_length": 128,
                },
            )
        return filename

    def _build_isolated_config(
        self,
        overrides: Mapping[object, object],
        *,
        redis_namespace: NsRedisNamespace,
    ) -> dict[object, object]:
        isolated_defaults: dict[object, object] = {
            "backend": {
                "databases": {
                    "default": {
                        "ENGINE": "django.db.backends.sqlite3",
                        "NAME": str(self._directories.data / "ns_backend.sqlite3"),
                    },
                },
            },
            "cache": {
                "key_prefix": redis_namespace.key_prefix,
                "django_namespace": redis_namespace.namespace,
                "sqlite_path": str(self._directories.data / "ns_cache.sqlite3"),
            },
            "log": {
                "lock_file_directory": str(self._directories.log),
            },
            "runtime": {
                "state_store": {
                    "namespace": redis_namespace.namespace,
                    "sqlite_path": str(
                        self._directories.data / "ns_runtime_state.sqlite3"
                    ),
                },
            },
        }
        merged = _deep_merge_config(isolated_defaults, overrides)
        self._enforce_isolated_fields(
            merged,
            redis_namespace=redis_namespace,
        )
        return merged

    def _enforce_isolated_fields(
        self,
        config: dict[object, object],
        *,
        redis_namespace: NsRedisNamespace,
    ) -> None:
        cache = config.get("cache")
        if isinstance(cache, dict):
            cache["key_prefix"] = redis_namespace.key_prefix
            cache["django_namespace"] = redis_namespace.namespace
            cache["sqlite_path"] = str(
                self._directories.data / "ns_cache.sqlite3"
            )

        log = config.get("log")
        if isinstance(log, dict):
            log["lock_file_directory"] = str(self._directories.log)

        runtime = config.get("runtime")
        if isinstance(runtime, dict):
            state_store = runtime.get("state_store")
            if isinstance(state_store, dict):
                state_store["namespace"] = redis_namespace.namespace
                state_store["sqlite_path"] = str(
                    self._directories.data / "ns_runtime_state.sqlite3"
                )

        backend = config.get("backend")
        if not isinstance(backend, dict):
            return
        databases = backend.get("databases")
        if not isinstance(databases, dict):
            return
        for index, database in enumerate(databases.values()):
            if not isinstance(database, dict):
                continue
            engine = database.get("ENGINE", "")
            if isinstance(engine, str) and "sqlite" in engine.casefold():
                database["NAME"] = str(
                    self._directories.data / f"ns_backend_{index}.sqlite3"
                )


TemporaryDirectories = NsTemporaryDirectories
RedisNamespace = NsRedisNamespace
TemporaryConfig = NsTemporaryConfig
InMemorySinkBundle = NsInMemorySinkBundle
ReservedPort = NsReservedPort
TestResourceFactory = NsTestResourceFactory


__all__ = [
    "DEFAULT_REDIS_CLEANUP_BATCH_SIZE",
    "DEFAULT_TEST_REDIS_KEY_PREFIX",
    "InMemorySinkBundle",
    "NsInMemorySinkBundle",
    "NsRedisNamespace",
    "NsReservedPort",
    "NsTemporaryConfig",
    "NsTemporaryDirectories",
    "NsTestResourceFactory",
    "RedisNamespace",
    "ReservedPort",
    "TemporaryConfig",
    "TemporaryDirectories",
    "TestResourceFactory",
]
