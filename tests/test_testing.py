# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import os
import shutil
import socket
import subprocess
import sys
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import ns_common
import ns_common.testing as testing_module
from ns_common.config import NsConfig, ns_config
from ns_common.exceptions import NsStateError, NsValidationError
from ns_common.observability import NsMetricKind, NsMetricRecord
from ns_common.testing import (
    DEFAULT_REDIS_CLEANUP_BATCH_SIZE,
    DEFAULT_TEST_REDIS_KEY_PREFIX,
    InMemorySinkBundle,
    NsInMemorySinkBundle,
    NsRedisNamespace,
    NsReservedPort,
    NsTemporaryConfig,
    NsTemporaryDirectories,
    NsTestResourceFactory,
    RedisNamespace,
    ReservedPort,
    TemporaryConfig,
    TemporaryDirectories,
    TestResourceFactory,
)
from ns_common.time import UTC_EPOCH


PROJECT_ROOT = Path(__file__).resolve().parents[1]

TESTING_PUBLIC_EXPORTS = frozenset({
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
})


class _SyncRedisClient:
    def __init__(self) -> None:
        self.keys: set[str] = set()
        self.calls: list[tuple[object, ...]] = []
        self.delete_batches: list[tuple[str, ...]] = []

    def scan_iter(self, *, match: str, count: int) -> Iterator[str]:
        self.calls.append(("scan_iter", match, count))
        prefix = match[:-1]
        yield from sorted(key for key in self.keys if key.startswith(prefix))

    def delete(self, *keys: str) -> int:
        self.calls.append(("delete", *keys))
        self.delete_batches.append(keys)
        deleted = 0
        for key in keys:
            if key in self.keys:
                self.keys.remove(key)
                deleted += 1
        return deleted


class _EscapingSyncRedisClient(_SyncRedisClient):
    def __init__(self, owned_key: str, foreign_key: str) -> None:
        super().__init__()
        self.keys.update({owned_key, foreign_key})
        self._owned_key = owned_key
        self._foreign_key = foreign_key

    def scan_iter(self, *, match: str, count: int) -> Iterator[str]:
        self.calls.append(("scan_iter", match, count))
        yield self._owned_key
        yield self._foreign_key


class _AsyncRedisClient:
    def __init__(self) -> None:
        self.keys: set[str] = set()
        self.calls: list[tuple[object, ...]] = []
        self.delete_batches: list[tuple[str, ...]] = []

    async def scan_iter(self, *, match: str, count: int):
        self.calls.append(("scan_iter", match, count))
        prefix = match[:-1]
        for key in sorted(key for key in self.keys if key.startswith(prefix)):
            await asyncio.sleep(0)
            yield key

    async def delete(self, *keys: str) -> int:
        self.calls.append(("delete", *keys))
        self.delete_batches.append(keys)
        deleted = 0
        for key in keys:
            if key in self.keys:
                self.keys.remove(key)
                deleted += 1
        return deleted


class _RespRedisClient:
    """Tiny test-only RESP2 client; no production Redis dependency is needed."""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.commands: list[str] = []

    def execute(self, *arguments: object) -> object:
        command = str(arguments[0]).upper()
        self.commands.append(command)
        encoded_arguments = [str(argument).encode("utf-8") for argument in arguments]
        request = [f"*{len(encoded_arguments)}\r\n".encode("ascii")]
        for argument in encoded_arguments:
            request.extend([
                f"${len(argument)}\r\n".encode("ascii"),
                argument,
                b"\r\n",
            ])

        with socket.create_connection((self.host, self.port), timeout=1.0) as connection:
            connection.sendall(b"".join(request))
            with connection.makefile("rb") as reader:
                return self._read_response(reader)

    def scan_iter(self, *, match: str, count: int) -> Iterator[str]:
        cursor = 0
        while True:
            response = self.execute(
                "SCAN",
                cursor,
                "MATCH",
                match,
                "COUNT",
                count,
            )
            if not isinstance(response, list) or len(response) != 2:
                raise AssertionError("Redis SCAN returned an unexpected response")
            cursor_value, keys = response
            cursor = int(self._decode(cursor_value))
            if not isinstance(keys, list):
                raise AssertionError("Redis SCAN keys must be a list")
            for key in keys:
                yield self._decode(key)
            if cursor == 0:
                return

    def delete(self, *keys: str) -> int:
        return int(self.execute("DEL", *keys))

    def set(self, key: str, value: str) -> None:
        response = self.execute("SET", key, value)
        if self._decode(response) != "OK":
            raise AssertionError("Redis SET failed")

    def get(self, key: str) -> str | None:
        response = self.execute("GET", key)
        return None if response is None else self._decode(response)

    @classmethod
    def _read_response(cls, reader: object) -> object:
        prefix = reader.read(1)
        if not prefix:
            raise ConnectionError("Redis closed the connection")
        line = reader.readline()
        if not line.endswith(b"\r\n"):
            raise ConnectionError("Redis returned an incomplete response")
        payload = line[:-2]
        if prefix == b"+":
            return payload
        if prefix == b"-":
            raise RuntimeError(payload.decode("utf-8", errors="replace"))
        if prefix == b":":
            return int(payload)
        if prefix == b"$":
            length = int(payload)
            if length == -1:
                return None
            value = reader.read(length)
            terminator = reader.read(2)
            if len(value) != length or terminator != b"\r\n":
                raise ConnectionError("Redis returned an incomplete bulk response")
            return value
        if prefix == b"*":
            length = int(payload)
            if length == -1:
                return None
            return [cls._read_response(reader) for _ in range(length)]
        raise ConnectionError("Redis returned an unknown RESP type")

    @staticmethod
    def _decode(value: object) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return str(value)


class NsTestResourceFactoryTestCase(unittest.TestCase):
    def test_factory_owns_unique_directories_and_removes_them(self) -> None:
        first = NsTestResourceFactory()
        second = NsTestResourceFactory()
        first_root = first.directories.root
        second_root = second.directories.root
        try:
            self.assertNotEqual(first_root, second_root)
            self.assertTrue(first_root.is_dir())
            self.assertTrue(second_root.is_dir())
            for directory in (
                first.directories.data,
                first.directories.etc,
                first.directories.log,
                first.directories.tmp,
            ):
                self.assertTrue(directory.is_dir())
                self.assertTrue(first.directories.contains(directory))
            self.assertFalse(first.directories.contains(PROJECT_ROOT / "data"))
        finally:
            first.close()
            second.close()

        self.assertFalse(first_root.exists())
        self.assertFalse(second_root.exists())
        first.close()
        second.close()

    def test_factory_rejects_invalid_roots_and_use_after_close(self) -> None:
        with self.assertRaises(NsValidationError):
            NsTestResourceFactory(prefix="../escape")
        with self.assertRaises(NsValidationError):
            NsTestResourceFactory(base_directory=True)  # type: ignore[arg-type]

        with NsTestResourceFactory() as owner:
            file_path = owner.directories.root / "not-a-directory"
            file_path.write_text("file", encoding="utf-8")
            with self.assertRaises(NsValidationError):
                NsTestResourceFactory(base_directory=file_path)

        factory = NsTestResourceFactory()
        factory.close()
        with self.assertRaises(NsStateError):
            _ = factory.directories
        with self.assertRaises(NsStateError):
            factory.create_controlled_clock()
        with self.assertRaises(NsStateError):
            factory.create_in_memory_sinks()
        with self.assertRaises(NsStateError):
            factory.create_redis_namespace()
        with self.assertRaises(NsStateError):
            factory.reserve_tcp_port()

    def test_temporary_config_is_frozen_explicit_and_path_isolated(self) -> None:
        original_overrides = {
            "backend": {
                "databases": {
                    "default": {
                        "ENGINE": "django.db.backends.sqlite3",
                        "NAME": str(PROJECT_ROOT / "data" / "must-not-be-used.sqlite3"),
                    },
                },
            },
            "cache": {
                "key_prefix": "unsafe_shared_prefix",
                "django_namespace": "unsafe_shared_namespace",
                "sqlite_path": str(PROJECT_ROOT / "data" / "must-not-be-used-cache.sqlite3"),
            },
            "log": {
                "lock_file_directory": str(PROJECT_ROOT / "log"),
            },
            "runtime": {
                "state_store": {
                    "namespace": "unsafe_shared_runtime",
                    "sqlite_path": str(PROJECT_ROOT / "data" / "must-not-be-used-state.sqlite3"),
                },
                "worker": {
                    "concurrency": 7,
                },
            },
        }
        untouched_overrides = deepcopy(original_overrides)
        global_config = ns_config

        with NsTestResourceFactory() as factory:
            temporary = factory.create_temporary_config(original_overrides)
            second = factory.create_temporary_config()

            self.assertIsInstance(temporary, NsTemporaryConfig)
            self.assertIs(temporary.config, temporary.snapshot)
            self.assertTrue(temporary.path.is_file())
            self.assertTrue(temporary.directories.contains(temporary.path))
            self.assertEqual("test", temporary.environment)
            self.assertEqual(
                "1970-01-01T00:00:00Z",
                temporary.config.backend.metadata.effective_at,
            )
            self.assertEqual(7, temporary.config.runtime.worker.concurrency)
            self.assertNotEqual(
                temporary.redis_namespace.namespace,
                second.redis_namespace.namespace,
            )

            isolated_paths = (
                temporary.config.backend.databases["default"]["NAME"],
                temporary.config.cache.sqlite_path,
                temporary.config.log.lock_file_directory,
                temporary.config.runtime.state_store.sqlite_path,
            )
            for isolated_path in isolated_paths:
                self.assertTrue(temporary.directories.contains(isolated_path))

            self.assertEqual(
                temporary.redis_namespace.key_prefix,
                temporary.config.cache.key_prefix,
            )
            self.assertEqual(
                temporary.redis_namespace.namespace,
                temporary.config.cache.django_namespace,
            )
            self.assertEqual(
                temporary.redis_namespace.namespace,
                temporary.config.runtime.state_store.namespace,
            )
            restored = NsConfig.load(
                temporary.path,
                environment="test",
                effective_at=UTC_EPOCH,
            )
            self.assertEqual(temporary.config, restored)

        self.assertEqual(untouched_overrides, original_overrides)
        self.assertIs(ns_config, global_config)

    def test_temporary_config_rejects_escape_filename_and_bad_overrides(self) -> None:
        with NsTestResourceFactory() as factory:
            for filename in ("../config.json", "nested/config.json", " config.json"):
                with self.subTest(filename=filename):
                    with self.assertRaises(NsValidationError):
                        factory.create_temporary_config(filename=filename)
            with self.assertRaises(NsValidationError):
                factory.create_temporary_config([])  # type: ignore[arg-type]
            with self.assertRaises(NsValidationError):
                factory.create_temporary_config(
                    redis_namespace=False,  # type: ignore[arg-type]
                )

            normalized = factory.create_temporary_config(
                environment=" TEST ",
                filename="normalized.json",
            )
            self.assertEqual("test", normalized.environment)
            with self.assertRaises(NsStateError):
                factory.create_temporary_config(filename="normalized.json")

    def test_controlled_clocks_are_fresh_and_do_not_use_real_sleep(self) -> None:
        with NsTestResourceFactory() as factory:
            first = factory.create_controlled_clock()
            second = factory.create_controlled_clock()
            self.assertIsNot(first, second)
            self.assertEqual(UTC_EPOCH, first.utc_now())
            self.assertEqual(0.0, first.monotonic())

            first.advance(12.5)
            self.assertEqual(12.5, first.monotonic())
            self.assertEqual(0.0, second.monotonic())
            self.assertEqual(UTC_EPOCH, second.utc_now())

    def test_in_memory_sink_bundles_are_fresh_and_capacity_bound(self) -> None:
        with NsTestResourceFactory() as factory:
            first = factory.create_in_memory_sinks(capacity=1)
            second = factory.create_in_memory_sinks(capacity=1)
            self.assertIsInstance(first, NsInMemorySinkBundle)
            self.assertIs(first.metrics, first.metrics_sink)
            self.assertIs(first.traces, first.trace_sink)
            self.assertIs(first.diagnostics, first.diagnostic_snapshot_sink)
            self.assertIsNot(first.metrics, second.metrics)

            first.metrics.record(
                NsMetricRecord(
                    name="test_resource_metric",
                    kind=NsMetricKind.GAUGE,
                    value=1,
                    observed_at=datetime(2026, 7, 17, tzinfo=timezone.utc),
                )
            )
            self.assertEqual(1, len(first.metrics.records))
            self.assertEqual(0, len(second.metrics.records))
            self.assertEqual(1, first.clear())
            self.assertEqual(0, len(first.metrics.records))

            with self.assertRaises(NsValidationError):
                NsInMemorySinkBundle(
                    metrics=object(),  # type: ignore[arg-type]
                    traces=first.traces,
                    diagnostics=first.diagnostics,
                )

    def test_reserved_ports_remain_bound_and_factory_releases_them(self) -> None:
        factory = NsTestResourceFactory()
        root = factory.directories.root
        first = factory.reserve_tcp_port()
        second = factory.reserve_tcp_port()
        self.assertIsInstance(first, NsReservedPort)
        self.assertNotEqual(first.port, second.port)
        self.assertGreater(first.port, 0)
        self.assertGreaterEqual(first.fileno(), 0)

        blocked = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            with self.assertRaises(OSError):
                blocked.bind((first.host, first.port))
        finally:
            blocked.close()

        first_port = first.port
        self.assertTrue(first.release())
        self.assertFalse(first.release())
        with self.assertRaises(NsStateError):
            _ = first.socket

        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            udp_socket.bind(("127.0.0.1", 0))
            with self.assertRaises(NsValidationError):
                NsReservedPort(udp_socket)
        finally:
            udp_socket.close()

        available = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            available.bind(("127.0.0.1", first_port))
        finally:
            available.close()

        second_port = second.port
        factory.close()
        self.assertTrue(second.is_released)
        self.assertFalse(root.exists())
        available_after_close = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            available_after_close.bind(("127.0.0.1", second_port))
        finally:
            available_after_close.close()

    def test_parallel_namespace_allocation_is_unique(self) -> None:
        with NsTestResourceFactory() as factory:
            with ThreadPoolExecutor(max_workers=8) as executor:
                namespaces = tuple(
                    executor.map(
                        lambda _: factory.create_redis_namespace().namespace,
                        range(400),
                    )
                )
        self.assertEqual(400, len(set(namespaces)))

    def test_factory_managed_namespace_uses_fresh_scoped_cleanup(self) -> None:
        client = _SyncRedisClient()
        with NsTestResourceFactory() as factory:
            with factory.manage_redis_namespace(client, scope="managed") as namespace:
                key = namespace.key("inside")
                client.keys.add(key)
                self.assertIn(key, client.keys)
            self.assertNotIn(key, client.keys)
            with self.assertRaises(NsValidationError):
                factory.create_redis_namespace(scope="x" * 65)


class NsRedisNamespaceTestCase(unittest.TestCase):
    def test_namespace_builds_owned_keys_and_rejects_unsafe_parts(self) -> None:
        namespace = NsRedisNamespace(
            key_prefix="ns_test",
            namespace="runtime-abc123",
        )
        self.assertEqual("ns_test:runtime-abc123:", namespace.prefix)
        self.assertEqual("ns_test:runtime-abc123:*", namespace.match_pattern)
        key = namespace.key("delivery", "one-1")
        self.assertEqual("ns_test:runtime-abc123:delivery:one-1", key)
        self.assertTrue(namespace.owns(key))
        self.assertTrue(namespace.owns(key.encode("utf-8")))
        self.assertFalse(namespace.owns("ns_test:runtime-abc1234:delivery"))
        self.assertFalse(namespace.owns(object()))

        for invalid in ("", "with space", "wild*card", "../escape"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(NsValidationError):
                    NsRedisNamespace(key_prefix="ns_test", namespace=invalid)
        with self.assertRaises(NsValidationError):
            namespace.key()
        with self.assertRaises(NsValidationError):
            namespace.key("wild*card")

    def test_sync_cleanup_batches_and_preserves_other_namespaces(self) -> None:
        namespace = NsRedisNamespace(
            key_prefix="ns_test",
            namespace="owned",
        )
        other = NsRedisNamespace(
            key_prefix="ns_test",
            namespace="other",
        )
        client = _SyncRedisClient()
        client.keys.update(namespace.key("key", str(index)) for index in range(5))
        other_key = other.key("key", "one")
        shared_key = "application:shared:key"
        client.keys.update({other_key, shared_key})

        self.assertEqual(5, namespace.cleanup(client, batch_size=2))
        self.assertEqual([2, 2, 1], [len(batch) for batch in client.delete_batches])
        self.assertEqual({other_key, shared_key}, client.keys)
        self.assertNotIn("flushdb", {str(call[0]).casefold() for call in client.calls})
        self.assertEqual(0, namespace.cleanup(client, batch_size=2))

    def test_managed_namespace_cleans_before_and_after_failure(self) -> None:
        namespace = NsRedisNamespace(
            key_prefix="ns_test",
            namespace="managed",
        )
        client = _SyncRedisClient()
        stale_key = namespace.key("stale")
        created_key = namespace.key("created")
        client.keys.add(stale_key)

        with self.assertRaisesRegex(RuntimeError, "body failed"):
            with namespace.manage(client) as managed:
                self.assertIs(namespace, managed)
                self.assertNotIn(stale_key, client.keys)
                client.keys.add(created_key)
                raise RuntimeError("body failed")

        self.assertNotIn(created_key, client.keys)

    def test_cleanup_stops_if_client_scan_escapes_prefix(self) -> None:
        namespace = NsRedisNamespace(
            key_prefix="ns_test",
            namespace="guarded",
        )
        owned_key = namespace.key("owned")
        foreign_key = "shared:must-survive"
        client = _EscapingSyncRedisClient(owned_key, foreign_key)

        with self.assertRaises(NsStateError):
            namespace.cleanup(client)
        self.assertEqual({owned_key, foreign_key}, client.keys)
        self.assertEqual([], client.delete_batches)

    def test_invalid_client_and_batch_size_fail_without_database_commands(self) -> None:
        namespace = NsRedisNamespace(
            key_prefix="ns_test",
            namespace="validation",
        )
        with self.assertRaises(NsValidationError):
            namespace.cleanup(object())
        for batch_size in (True, 0, 10_001):
            with self.subTest(batch_size=batch_size):
                with self.assertRaises(NsValidationError):
                    namespace.cleanup(_SyncRedisClient(), batch_size=batch_size)


class NsRedisNamespaceAsyncTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_async_cleanup_and_manager_are_scoped(self) -> None:
        namespace = NsRedisNamespace(
            key_prefix="ns_test",
            namespace="async_owned",
        )
        other = NsRedisNamespace(
            key_prefix="ns_test",
            namespace="async_other",
        )
        client = _AsyncRedisClient()
        client.keys.update(namespace.key("key", str(index)) for index in range(3))
        other_key = other.key("key")
        client.keys.add(other_key)

        self.assertEqual(3, await namespace.acleanup(client, batch_size=2))
        self.assertEqual([2, 1], [len(batch) for batch in client.delete_batches])
        self.assertEqual({other_key}, client.keys)

        async with namespace.amanage(client, batch_size=1):
            client.keys.add(namespace.key("inside"))
        self.assertEqual({other_key}, client.keys)

    async def test_sink_bundle_async_close_clears_and_closes_all_sinks(self) -> None:
        with NsTestResourceFactory() as factory:
            sinks = factory.create_in_memory_sinks()
            sinks.metrics.record(
                NsMetricRecord(
                    name="test_resource_async_metric",
                    kind=NsMetricKind.GAUGE,
                    value=1,
                    observed_at=datetime(2026, 7, 17, tzinfo=timezone.utc),
                )
            )
            await sinks.aclose()
            self.assertTrue(sinks.metrics.is_closed)
            self.assertTrue(sinks.traces.is_closed)
            self.assertTrue(sinks.diagnostics.is_closed)
            self.assertEqual((), sinks.metrics.records)

    async def test_factory_async_managed_namespace_cleans_on_exit(self) -> None:
        client = _AsyncRedisClient()
        with NsTestResourceFactory() as factory:
            async with factory.amanage_redis_namespace(
                client,
                scope="async_managed",
            ) as namespace:
                key = namespace.key("inside")
                client.keys.add(key)
                self.assertIn(key, client.keys)
            self.assertNotIn(key, client.keys)


@unittest.skipUnless(shutil.which("redis-server"), "redis-server is not installed")
class NsRedisNamespaceRealIntegrationTestCase(unittest.TestCase):
    def test_real_redis_cleanup_never_flushes_shared_keys(self) -> None:
        redis_server = shutil.which("redis-server")
        if redis_server is None:
            self.skipTest("redis-server is not installed")

        with NsTestResourceFactory() as factory:
            reservation = factory.reserve_tcp_port()
            port = reservation.port
            reservation.release()
            process = subprocess.Popen(
                [
                    redis_server,
                    "--bind",
                    "127.0.0.1",
                    "--protected-mode",
                    "no",
                    "--port",
                    str(port),
                    "--save",
                    "",
                    "--appendonly",
                    "no",
                    "--dir",
                    str(factory.directories.tmp),
                    "--dbfilename",
                    "ns-testing.rdb",
                    "--loglevel",
                    "warning",
                ],
                cwd=factory.directories.root,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.addCleanup(self._stop_process, process)
            client = _RespRedisClient("127.0.0.1", port)
            deadline = time.monotonic() + 5.0
            while True:
                try:
                    if client.execute("PING") == b"PONG":
                        break
                except (ConnectionError, OSError):
                    pass
                if process.poll() is not None:
                    self.fail(f"redis-server exited with code {process.returncode}")
                if time.monotonic() >= deadline:
                    self.fail("redis-server did not become ready within 5 seconds")
                time.sleep(0.02)

            owned = factory.create_redis_namespace(scope="real")
            other = factory.create_redis_namespace(scope="real")
            stale_key = owned.key("stale")
            body_key = owned.key("body")
            other_key = other.key("survivor")
            shared_key = "application:shared:survivor"
            client.set(stale_key, "stale")
            client.set(other_key, "other")
            client.set(shared_key, "shared")

            with owned.manage(client, batch_size=2):
                self.assertIsNone(client.get(stale_key))
                client.set(body_key, "body")
                self.assertEqual("body", client.get(body_key))

            self.assertIsNone(client.get(body_key))
            self.assertEqual("other", client.get(other_key))
            self.assertEqual("shared", client.get(shared_key))
            self.assertNotIn("FLUSHDB", client.commands)
            self.assertNotIn("FLUSHALL", client.commands)
            self.assertEqual(1, other.cleanup(client))
            self.assertEqual("shared", client.get(shared_key))

            self._stop_process(process)

    @staticmethod
    def _stop_process(process: subprocess.Popen[bytes]) -> None:
        if process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


class NsTestingFacadeTestCase(unittest.TestCase):
    def test_facades_export_authoritative_types_and_aliases(self) -> None:
        self.assertEqual(TESTING_PUBLIC_EXPORTS, frozenset(testing_module.__all__))
        self.assertEqual(
            len(testing_module.__all__),
            len(set(testing_module.__all__)),
        )
        self.assertEqual(len(ns_common.__all__), len(set(ns_common.__all__)))

        for name in TESTING_PUBLIC_EXPORTS:
            self.assertIn(name, ns_common.__all__)
            self.assertIs(getattr(ns_common, name), getattr(testing_module, name))

        self.assertIs(TemporaryDirectories, NsTemporaryDirectories)
        self.assertIs(RedisNamespace, NsRedisNamespace)
        self.assertIs(TemporaryConfig, NsTemporaryConfig)
        self.assertIs(InMemorySinkBundle, NsInMemorySinkBundle)
        self.assertIs(ReservedPort, NsReservedPort)
        self.assertIs(TestResourceFactory, NsTestResourceFactory)
        self.assertEqual(500, DEFAULT_REDIS_CLEANUP_BATCH_SIZE)
        self.assertEqual("ns_test", DEFAULT_TEST_REDIS_KEY_PREFIX)

    def test_cold_import_has_no_redis_driver_or_runtime_dependency(self) -> None:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = os.pathsep.join(
            part
            for part in (
                str(PROJECT_ROOT / "src"),
                environment.get("PYTHONPATH", ""),
            )
            if part
        )
        source = (
            "import sys; import ns_common.testing; "
            "assert 'concurrent_log_handler' not in sys.modules; "
            "assert 'portalocker' not in sys.modules; "
            "assert 'redis' not in sys.modules; "
            "assert 'valkey' not in sys.modules; "
            "assert 'ns_runtime' not in sys.modules"
        )
        completed = subprocess.run(
            [sys.executable, "-c", source],
            cwd=PROJECT_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)


if __name__ == "__main__":
    unittest.main()
