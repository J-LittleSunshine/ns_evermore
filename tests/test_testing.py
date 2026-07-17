# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
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
from threading import Event, Lock, Thread
from typing import Iterator
from unittest import mock

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
    NsTestResourceFactoryState,
    RedisNamespace,
    ReservedPort,
    TemporaryConfig,
    TemporaryDirectories,
    TestResourceFactory,
    TestResourceFactoryState,
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
    "NsTestResourceFactoryState",
    "RedisNamespace",
    "ReservedPort",
    "TemporaryConfig",
    "TemporaryDirectories",
    "TestResourceFactory",
    "TestResourceFactoryState",
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


class _FlakyCloseSocket(socket.socket):
    """Real bound TCP socket whose close failures occur before OS release."""

    def __init__(self, *close_errors: BaseException) -> None:
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        self.close_attempt_count = 0
        self.successful_close_count = 0
        self._close_errors = list(close_errors)
        self.bind(("127.0.0.1", 0))
        self.listen(1)

    def close(self) -> None:
        self.close_attempt_count += 1
        if self._close_errors:
            raise self._close_errors.pop(0)
        super().close()
        self.successful_close_count += 1

    def allow_successful_close(self) -> None:
        self._close_errors.clear()


class _BlockingCloseSocket(socket.socket):
    """Real bound TCP socket with a controllable first close boundary."""

    def __init__(self, *, first_close_error: BaseException | None = None) -> None:
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        self.first_close_entered = Event()
        self.allow_first_close = Event()
        self.close_attempt_count = 0
        self.successful_close_count = 0
        self.maximum_concurrent_close_count = 0
        self.retry_observed_same_socket = False
        self.retry_observed_unreleased = False
        self.reservation: NsReservedPort | None = None
        self._first_close_error = first_close_error
        self._active_close_count = 0
        self._counter_lock = Lock()
        self.bind(("127.0.0.1", 0))
        self.listen(1)

    def close(self) -> None:
        with self._counter_lock:
            self.close_attempt_count += 1
            attempt = self.close_attempt_count
            self._active_close_count += 1
            self.maximum_concurrent_close_count = max(
                self.maximum_concurrent_close_count,
                self._active_close_count,
            )
        if attempt == 1:
            self.first_close_entered.set()
        try:
            if attempt == 1:
                if not self.allow_first_close.wait(5):
                    raise AssertionError("socket close gate timed out")
                if self._first_close_error is not None:
                    raise self._first_close_error
            if attempt == 2 and self.reservation is not None:
                self.retry_observed_same_socket = (
                    self.reservation.socket is self
                )
                self.retry_observed_unreleased = (
                    not self.reservation.is_released
                )
            super().close()
            with self._counter_lock:
                self.successful_close_count += 1
        finally:
            with self._counter_lock:
                self._active_close_count -= 1

    def allow_cleanup(self) -> None:
        self._first_close_error = None
        self.allow_first_close.set()


def _force_close_test_socket(test_socket: socket.socket) -> None:
    if test_socket.fileno() >= 0:
        socket.socket.close(test_socket)


def _adopt_test_reservation(
    factory: NsTestResourceFactory,
    reservation: NsReservedPort,
) -> None:
    # White-box ownership setup keeps failure injection out of the production API.
    with factory._lock:
        factory._ports.append(reservation)


def _wait_for_factory_state(
    factory: NsTestResourceFactory,
    expected: NsTestResourceFactoryState,
    *,
    timeout: float = 5.0,
) -> None:
    deadline = time.monotonic() + timeout
    while factory.state is not expected:
        if time.monotonic() >= deadline:
            raise AssertionError(
                f"factory did not enter {expected.value!r} within {timeout}s"
            )
        time.sleep(0.005)


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


class NsReservedPortReleaseTestCase(unittest.TestCase):
    def test_bottom_close_failure_preserves_socket_for_real_retry(self) -> None:
        close_error = OSError("bottom-close-secret")
        controlled_socket = _FlakyCloseSocket(close_error)
        self.addCleanup(_force_close_test_socket, controlled_socket)
        reservation = NsReservedPort(controlled_socket)
        released_port = reservation.port

        self.assertIs(NsReservedPort.close, NsReservedPort.release)
        with self.assertRaises(OSError) as caught:
            reservation.release()

        self.assertIs(close_error, caught.exception)
        self.assertFalse(reservation.is_released)
        self.assertIs(controlled_socket, reservation.socket)
        self.assertGreaterEqual(reservation.fileno(), 0)
        self.assertEqual(1, controlled_socket.close_attempt_count)
        self.assertEqual(0, controlled_socket.successful_close_count)

        self.assertTrue(reservation.release())
        self.assertTrue(reservation.is_released)
        self.assertEqual(2, controlled_socket.close_attempt_count)
        self.assertEqual(1, controlled_socket.successful_close_count)
        self.assertEqual(-1, controlled_socket.fileno())
        with self.assertRaises(NsStateError) as released_socket_error:
            _ = reservation.socket
        self.assertEqual(
            {"operation": "get_socket"},
            released_socket_error.exception.details,
        )

        self.assertFalse(reservation.release())
        self.assertEqual(2, controlled_socket.close_attempt_count)
        self.assertEqual(1, controlled_socket.successful_close_count)

        available = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            available.bind((reservation.host, released_port))
        finally:
            available.close()

    def test_concurrent_direct_release_waits_for_successful_close(self) -> None:
        controlled_socket = _BlockingCloseSocket()
        self.addCleanup(_force_close_test_socket, controlled_socket)
        reservation = NsReservedPort(controlled_socket)
        controlled_socket.reservation = reservation
        start_gate = Event()
        called = [Event() for _ in range(4)]
        completed = [Event() for _ in range(4)]
        results: list[bool | None] = [None] * 4
        errors: list[BaseException | None] = [None] * 4

        def release_in_thread(index: int) -> None:
            if not start_gate.wait(5):
                errors[index] = AssertionError("start gate timed out")
                completed[index].set()
                return
            called[index].set()
            try:
                results[index] = reservation.release()
            except BaseException as error:
                errors[index] = error
            finally:
                completed[index].set()

        threads = [
            Thread(target=release_in_thread, args=(index,), daemon=True)
            for index in range(4)
        ]
        for thread in threads:
            thread.start()
        start_gate.set()
        try:
            self.assertTrue(controlled_socket.first_close_entered.wait(5))
            self.assertTrue(all(event.wait(5) for event in called))
            self.assertFalse(any(event.is_set() for event in completed))
            self.assertEqual(1, controlled_socket.close_attempt_count)
            self.assertEqual(
                1,
                controlled_socket.maximum_concurrent_close_count,
            )
        finally:
            controlled_socket.allow_first_close.set()
            for event in completed:
                event.wait(5)
            for thread in threads:
                thread.join(timeout=1)

        self.assertTrue(all(event.is_set() for event in completed))
        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual([None] * 4, errors)
        self.assertEqual(1, sum(result is True for result in results))
        self.assertEqual(3, sum(result is False for result in results))
        self.assertEqual(1, controlled_socket.close_attempt_count)
        self.assertEqual(1, controlled_socket.successful_close_count)
        self.assertEqual(1, controlled_socket.maximum_concurrent_close_count)
        self.assertTrue(reservation.is_released)

    def test_concurrent_direct_release_retries_after_first_failure(self) -> None:
        close_error = OSError("concurrent-direct-close-secret")
        controlled_socket = _BlockingCloseSocket(
            first_close_error=close_error,
        )
        self.addCleanup(_force_close_test_socket, controlled_socket)
        reservation = NsReservedPort(controlled_socket)
        controlled_socket.reservation = reservation
        start_gate = Event()
        called = [Event() for _ in range(4)]
        completed = [Event() for _ in range(4)]
        results: list[bool | None] = [None] * 4
        errors: list[BaseException | None] = [None] * 4

        def release_in_thread(index: int) -> None:
            if not start_gate.wait(5):
                errors[index] = AssertionError("start gate timed out")
                completed[index].set()
                return
            called[index].set()
            try:
                results[index] = reservation.release()
            except BaseException as error:
                errors[index] = error
            finally:
                completed[index].set()

        threads = [
            Thread(target=release_in_thread, args=(index,), daemon=True)
            for index in range(4)
        ]
        for thread in threads:
            thread.start()
        start_gate.set()
        try:
            self.assertTrue(controlled_socket.first_close_entered.wait(5))
            self.assertTrue(all(event.wait(5) for event in called))
            self.assertFalse(any(event.is_set() for event in completed))
            self.assertEqual(1, controlled_socket.close_attempt_count)
            self.assertEqual(
                1,
                controlled_socket.maximum_concurrent_close_count,
            )
        finally:
            controlled_socket.allow_first_close.set()
            for event in completed:
                event.wait(5)
            for thread in threads:
                thread.join(timeout=1)

        self.assertTrue(all(event.is_set() for event in completed))
        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(1, sum(error is close_error for error in errors))
        self.assertEqual(3, sum(error is None for error in errors))
        self.assertEqual(1, sum(result is True for result in results))
        self.assertEqual(2, sum(result is False for result in results))
        self.assertEqual(1, sum(result is None for result in results))
        self.assertEqual(2, controlled_socket.close_attempt_count)
        self.assertEqual(1, controlled_socket.successful_close_count)
        self.assertEqual(1, controlled_socket.maximum_concurrent_close_count)
        self.assertTrue(controlled_socket.retry_observed_same_socket)
        self.assertTrue(controlled_socket.retry_observed_unreleased)
        self.assertTrue(reservation.is_released)

    def test_factory_retries_same_socket_after_bottom_close_failure(self) -> None:
        factory = NsTestResourceFactory()
        root = factory.directories.root
        close_secret = "factory-bottom-close-secret"
        close_error = OSError(close_secret)
        controlled_socket = _FlakyCloseSocket(close_error)
        reservation = NsReservedPort(controlled_socket)
        released_port = reservation.port
        _adopt_test_reservation(factory, reservation)

        try:
            with self.assertRaises(NsStateError) as caught:
                factory.close()

            error = caught.exception
            self.assertEqual(
                {
                    "operation": "close_test_resources",
                    "state": "closing",
                    "failed_resource_types": ["reserved_port"],
                    "failed_resource_count": 1,
                    "remaining_port_count": 1,
                    "temporary_directory_pending": False,
                    "failures": [
                        {
                            "resource_type": "reserved_port",
                            "error_type": "OSError",
                        }
                    ],
                },
                error.details,
            )
            self.assertIsNone(error.__cause__)
            self.assertIsNone(error.__context__)
            self.assertIs(factory.state, NsTestResourceFactoryState.CLOSING)
            self.assertEqual([reservation], factory._ports)
            self.assertFalse(reservation.is_released)
            self.assertIs(controlled_socket, reservation.socket)
            self.assertGreaterEqual(reservation.fileno(), 0)
            self.assertEqual(1, controlled_socket.close_attempt_count)
            self.assertEqual(0, controlled_socket.successful_close_count)
            self.assertTrue(factory._temporary_directory_released)
            self.assertFalse(root.exists())

            serialized = "\n".join(
                (
                    str(error),
                    json.dumps(error.details, sort_keys=True),
                    json.dumps(error.to_dict(), sort_keys=True),
                )
            )
            for sensitive in (
                close_secret,
                reservation.host,
                str(reservation.port),
                repr(controlled_socket),
            ):
                self.assertNotIn(sensitive, serialized)
            self.assertNotIn('"host"', serialized)
            self.assertNotIn('"port"', serialized)
            self.assertNotIn('"fileno"', serialized)
            self.assertNotIn('"socket"', serialized)

            factory.close()
            self.assertIs(factory.state, NsTestResourceFactoryState.CLOSED)
            self.assertEqual([], factory._ports)
            self.assertTrue(reservation.is_released)
            self.assertEqual(2, controlled_socket.close_attempt_count)
            self.assertEqual(1, controlled_socket.successful_close_count)
        finally:
            controlled_socket.allow_successful_close()
            if not factory.is_closed:
                factory.close()
            _force_close_test_socket(controlled_socket)

        available = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            available.bind((reservation.host, released_port))
        finally:
            available.close()

    def test_direct_release_and_factory_close_share_success_barrier(self) -> None:
        factory = NsTestResourceFactory()
        root = factory.directories.root
        controlled_socket = _BlockingCloseSocket()
        reservation = NsReservedPort(controlled_socket)
        controlled_socket.reservation = reservation
        _adopt_test_reservation(factory, reservation)
        direct_result: list[bool] = []
        direct_errors: list[BaseException] = []
        factory_errors: list[BaseException] = []
        direct_completed = Event()
        factory_started = Event()
        factory_completed = Event()

        def release_directly() -> None:
            try:
                direct_result.append(reservation.release())
            except BaseException as error:
                direct_errors.append(error)
            finally:
                direct_completed.set()

        def close_factory() -> None:
            factory_started.set()
            try:
                factory.close()
            except BaseException as error:
                factory_errors.append(error)
            finally:
                factory_completed.set()

        direct_thread = Thread(target=release_directly, daemon=True)
        factory_thread = Thread(target=close_factory, daemon=True)
        direct_thread.start()
        try:
            self.assertTrue(controlled_socket.first_close_entered.wait(5))
            factory_thread.start()
            self.assertTrue(factory_started.wait(5))
            _wait_for_factory_state(
                factory,
                NsTestResourceFactoryState.CLOSING,
            )
            self.assertFalse(direct_completed.is_set())
            self.assertFalse(factory_completed.is_set())
            self.assertEqual([reservation], factory._ports)
            self.assertTrue(root.exists())
            self.assertEqual(1, controlled_socket.close_attempt_count)
            self.assertEqual(
                1,
                controlled_socket.maximum_concurrent_close_count,
            )
        finally:
            controlled_socket.allow_first_close.set()
            direct_completed.wait(5)
            factory_completed.wait(5)
            direct_thread.join(timeout=1)
            if factory_thread.ident is not None:
                factory_thread.join(timeout=1)

        try:
            self.assertFalse(direct_thread.is_alive())
            self.assertFalse(factory_thread.is_alive())
            self.assertEqual([True], direct_result)
            self.assertEqual([], direct_errors)
            self.assertEqual([], factory_errors)
            self.assertEqual(1, controlled_socket.close_attempt_count)
            self.assertEqual(1, controlled_socket.successful_close_count)
            self.assertEqual(
                1,
                controlled_socket.maximum_concurrent_close_count,
            )
            self.assertIs(factory.state, NsTestResourceFactoryState.CLOSED)
            self.assertEqual([], factory._ports)
            self.assertTrue(reservation.is_released)
            self.assertFalse(root.exists())
        finally:
            controlled_socket.allow_cleanup()
            if not factory.is_closed:
                factory.close()
            _force_close_test_socket(controlled_socket)

    def test_direct_release_failure_allows_factory_retry(self) -> None:
        factory = NsTestResourceFactory()
        root = factory.directories.root
        close_error = OSError("direct-failure-before-factory-retry")
        controlled_socket = _BlockingCloseSocket(
            first_close_error=close_error,
        )
        reservation = NsReservedPort(controlled_socket)
        controlled_socket.reservation = reservation
        _adopt_test_reservation(factory, reservation)
        direct_errors: list[BaseException] = []
        factory_errors: list[BaseException] = []
        direct_completed = Event()
        factory_started = Event()
        factory_completed = Event()

        def release_directly() -> None:
            try:
                reservation.release()
            except BaseException as error:
                direct_errors.append(error)
            finally:
                direct_completed.set()

        def close_factory() -> None:
            factory_started.set()
            try:
                factory.close()
            except BaseException as error:
                factory_errors.append(error)
            finally:
                factory_completed.set()

        direct_thread = Thread(target=release_directly, daemon=True)
        factory_thread = Thread(target=close_factory, daemon=True)
        direct_thread.start()
        try:
            self.assertTrue(controlled_socket.first_close_entered.wait(5))
            factory_thread.start()
            self.assertTrue(factory_started.wait(5))
            _wait_for_factory_state(
                factory,
                NsTestResourceFactoryState.CLOSING,
            )
            self.assertFalse(direct_completed.is_set())
            self.assertFalse(factory_completed.is_set())
            self.assertEqual([reservation], factory._ports)
            self.assertEqual(1, controlled_socket.close_attempt_count)
            self.assertEqual(
                1,
                controlled_socket.maximum_concurrent_close_count,
            )
        finally:
            controlled_socket.allow_first_close.set()
            direct_completed.wait(5)
            factory_completed.wait(5)
            direct_thread.join(timeout=1)
            if factory_thread.ident is not None:
                factory_thread.join(timeout=1)

        try:
            self.assertFalse(direct_thread.is_alive())
            self.assertFalse(factory_thread.is_alive())
            self.assertEqual([close_error], direct_errors)
            self.assertEqual([], factory_errors)
            self.assertEqual(2, controlled_socket.close_attempt_count)
            self.assertEqual(1, controlled_socket.successful_close_count)
            self.assertEqual(
                1,
                controlled_socket.maximum_concurrent_close_count,
            )
            self.assertTrue(controlled_socket.retry_observed_same_socket)
            self.assertTrue(controlled_socket.retry_observed_unreleased)
            self.assertIs(factory.state, NsTestResourceFactoryState.CLOSED)
            self.assertEqual([], factory._ports)
            self.assertTrue(reservation.is_released)
            self.assertFalse(root.exists())
        finally:
            controlled_socket.allow_cleanup()
            if not factory.is_closed:
                factory.close()
            _force_close_test_socket(controlled_socket)

    def test_factory_preserves_socket_after_process_level_close_error(self) -> None:
        for exception_type in (KeyboardInterrupt, SystemExit):
            with self.subTest(exception_type=exception_type.__name__):
                factory = NsTestResourceFactory()
                root = factory.directories.root
                process_error = exception_type("process-close-stop")
                controlled_socket = _FlakyCloseSocket(process_error)
                reservation = NsReservedPort(controlled_socket)
                _adopt_test_reservation(factory, reservation)

                try:
                    with self.assertRaises(exception_type) as caught:
                        factory.close()

                    self.assertIs(process_error, caught.exception)
                    self.assertIs(
                        factory.state,
                        NsTestResourceFactoryState.CLOSING,
                    )
                    self.assertEqual([reservation], factory._ports)
                    self.assertFalse(reservation.is_released)
                    self.assertIs(controlled_socket, reservation.socket)
                    self.assertGreaterEqual(reservation.fileno(), 0)
                    self.assertEqual(1, controlled_socket.close_attempt_count)
                    self.assertEqual(
                        0,
                        controlled_socket.successful_close_count,
                    )
                    self.assertFalse(factory._temporary_directory_released)
                    self.assertTrue(root.exists())

                    factory.close()
                    self.assertIs(
                        factory.state,
                        NsTestResourceFactoryState.CLOSED,
                    )
                    self.assertEqual([], factory._ports)
                    self.assertTrue(reservation.is_released)
                    self.assertEqual(2, controlled_socket.close_attempt_count)
                    self.assertEqual(
                        1,
                        controlled_socket.successful_close_count,
                    )
                    self.assertFalse(root.exists())
                finally:
                    controlled_socket.allow_successful_close()
                    if not factory.is_closed:
                        factory.close()
                    _force_close_test_socket(controlled_socket)


class NsTestResourceFactoryTestCase(unittest.TestCase):
    def test_factory_owns_unique_directories_and_removes_them(self) -> None:
        first = NsTestResourceFactory()
        second = NsTestResourceFactory()
        self.assertIs(first.state, NsTestResourceFactoryState.OPEN)
        self.assertFalse(first.is_closing)
        self.assertFalse(first.is_closed)
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
        self.assertIs(first.state, NsTestResourceFactoryState.CLOSED)
        self.assertFalse(first.is_closing)
        self.assertTrue(first.is_closed)
        first.close()
        second.close()
        self.assertIs(first.state, NsTestResourceFactoryState.CLOSED)

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
        closed_operations = (
            ("directories", lambda: factory.directories),
            ("create_temporary_config", factory.create_temporary_config),
            ("create_controlled_clock", factory.create_controlled_clock),
            ("create_in_memory_sinks", factory.create_in_memory_sinks),
            ("create_redis_namespace", factory.create_redis_namespace),
            ("reserve_tcp_port", factory.reserve_tcp_port),
            (
                "manage_redis_namespace",
                lambda: factory.manage_redis_namespace(_SyncRedisClient()),
            ),
            (
                "amanage_redis_namespace",
                lambda: factory.amanage_redis_namespace(_AsyncRedisClient()),
            ),
        )
        for operation, action in closed_operations:
            with self.subTest(operation=operation):
                with self.assertRaises(NsStateError) as caught:
                    action()
                self.assertEqual(
                    {"operation": operation, "state": "closed"},
                    caught.exception.details,
                )

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
        self.assertIs(factory.state, NsTestResourceFactoryState.CLOSED)
        self.assertEqual([], factory._ports)
        self.assertTrue(factory._temporary_directory_released)
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


class NsTestResourceFactoryCloseTestCase(unittest.TestCase):
    def test_port_release_failure_preserves_only_pending_ownership(self) -> None:
        factory = NsTestResourceFactory()
        self.addCleanup(factory.close)
        root = factory.directories.root
        first = factory.reserve_tcp_port()
        middle = factory.reserve_tcp_port()
        last = factory.reserve_tcp_port()
        first_release = first.release
        middle_release = middle.release
        last_release = last.release
        order: list[str] = []
        middle_attempts = 0

        def release_first() -> bool:
            order.append("first")
            return first_release()

        def release_middle() -> bool:
            nonlocal middle_attempts
            order.append("middle")
            middle_attempts += 1
            if middle_attempts == 1:
                raise OSError("private port cleanup failure")
            return middle_release()

        def release_last() -> bool:
            order.append("last")
            return last_release()

        with (
            mock.patch.object(first, "release", side_effect=release_first) as first_mock,
            mock.patch.object(
                middle,
                "release",
                side_effect=release_middle,
            ) as middle_mock,
            mock.patch.object(last, "release", side_effect=release_last) as last_mock,
        ):
            with self.assertRaises(NsStateError) as caught:
                factory.close()

            self.assertEqual(["last", "middle", "first"], order)
            self.assertEqual(1, first_mock.call_count)
            self.assertEqual(1, middle_mock.call_count)
            self.assertEqual(1, last_mock.call_count)
            self.assertTrue(first.is_released)
            self.assertFalse(middle.is_released)
            self.assertTrue(last.is_released)
            self.assertEqual([middle], factory._ports)
            self.assertTrue(factory._temporary_directory_released)
            self.assertFalse(root.exists())
            self.assertIs(factory.state, NsTestResourceFactoryState.CLOSING)
            self.assertTrue(factory.is_closing)
            self.assertFalse(factory.is_closed)
            self.assertEqual(
                {
                    "operation": "close_test_resources",
                    "state": "closing",
                    "failed_resource_types": ["reserved_port"],
                    "failed_resource_count": 1,
                    "remaining_port_count": 1,
                    "temporary_directory_pending": False,
                    "failures": [
                        {
                            "resource_type": "reserved_port",
                            "error_type": "OSError",
                        }
                    ],
                },
                caught.exception.details,
            )

            factory.close()
            factory.close()
            self.assertEqual(
                ["last", "middle", "first", "middle"],
                order,
            )
            self.assertEqual(1, first_mock.call_count)
            self.assertEqual(2, middle_mock.call_count)
            self.assertEqual(1, last_mock.call_count)

        self.assertIs(factory.state, NsTestResourceFactoryState.CLOSED)
        self.assertFalse(factory.is_closing)
        self.assertTrue(factory.is_closed)
        self.assertEqual([], factory._ports)

    def test_temporary_directory_failure_is_retryable_and_not_repeated(self) -> None:
        factory = NsTestResourceFactory()
        self.addCleanup(factory.close)
        root = factory.directories.root
        cleanup = factory._temporary_directory.cleanup
        cleanup_attempts = 0

        def flaky_cleanup() -> None:
            nonlocal cleanup_attempts
            cleanup_attempts += 1
            if cleanup_attempts == 1:
                raise PermissionError("private temporary directory failure")
            cleanup()

        with mock.patch.object(
            factory._temporary_directory,
            "cleanup",
            side_effect=flaky_cleanup,
        ) as cleanup_mock:
            with self.assertRaises(NsStateError) as caught:
                factory.close()
            self.assertIs(factory.state, NsTestResourceFactoryState.CLOSING)
            self.assertFalse(factory.is_closed)
            self.assertFalse(factory._temporary_directory_released)
            self.assertTrue(root.exists())
            self.assertEqual(1, cleanup_mock.call_count)
            self.assertEqual(
                ["temporary_directory"],
                caught.exception.details["failed_resource_types"],
            )

            factory.close()
            self.assertIs(factory.state, NsTestResourceFactoryState.CLOSED)
            self.assertTrue(factory._temporary_directory_released)
            self.assertFalse(root.exists())
            self.assertEqual(2, cleanup_mock.call_count)

            factory.close()
            self.assertEqual(2, cleanup_mock.call_count)

    def test_port_and_directory_failures_are_aggregated_without_secrets(self) -> None:
        factory = NsTestResourceFactory()
        self.addCleanup(factory.close)
        root = factory.directories.root
        temporary = factory.create_temporary_config(filename="private-config.json")
        namespace = factory.create_redis_namespace(scope="private")
        successful = factory.reserve_tcp_port()
        failing = factory.reserve_tcp_port()
        successful_release = successful.release
        failing_release = failing.release
        cleanup = factory._temporary_directory.cleanup
        secret = "cleanup-secret-do-not-copy"
        release_attempts = 0
        cleanup_attempts = 0

        def release_successful() -> bool:
            return successful_release()

        def release_failing() -> bool:
            nonlocal release_attempts
            release_attempts += 1
            if release_attempts == 1:
                raise OSError(f"{secret}: {failing.host}:{failing.port}")
            return failing_release()

        def cleanup_failing() -> None:
            nonlocal cleanup_attempts
            cleanup_attempts += 1
            if cleanup_attempts == 1:
                raise PermissionError(f"{secret}: {root}")
            cleanup()

        with (
            mock.patch.object(
                successful,
                "release",
                side_effect=release_successful,
            ) as successful_mock,
            mock.patch.object(
                failing,
                "release",
                side_effect=release_failing,
            ) as failing_mock,
            mock.patch.object(
                factory._temporary_directory,
                "cleanup",
                side_effect=cleanup_failing,
            ) as cleanup_mock,
        ):
            with self.assertRaises(NsStateError) as caught:
                factory.close()

            error = caught.exception
            self.assertEqual(
                ["reserved_port", "temporary_directory"],
                error.details["failed_resource_types"],
            )
            self.assertEqual(2, error.details["failed_resource_count"])
            self.assertEqual(1, error.details["remaining_port_count"])
            self.assertTrue(error.details["temporary_directory_pending"])
            self.assertEqual(
                [
                    {
                        "resource_type": "reserved_port",
                        "error_type": "OSError",
                    },
                    {
                        "resource_type": "temporary_directory",
                        "error_type": "PermissionError",
                    },
                ],
                error.details["failures"],
            )
            self.assertIsNone(error.__cause__)
            self.assertIsNone(error.__context__)
            serialized_forms = (
                str(error),
                json.dumps(error.details, sort_keys=True),
                json.dumps(error.to_dict(), sort_keys=True),
            )
            sensitive_values = (
                secret,
                str(root),
                str(temporary.path),
                failing.host,
                str(failing.port),
                namespace.namespace,
            )
            for serialized in serialized_forms:
                for sensitive in sensitive_values:
                    with self.subTest(sensitive=sensitive, serialized=serialized):
                        self.assertNotIn(sensitive, serialized)

            self.assertTrue(successful.is_released)
            self.assertFalse(failing.is_released)
            self.assertEqual([failing], factory._ports)
            self.assertFalse(factory._temporary_directory_released)
            self.assertEqual(1, successful_mock.call_count)
            self.assertEqual(1, failing_mock.call_count)
            self.assertEqual(1, cleanup_mock.call_count)

            factory.close()
            self.assertEqual(1, successful_mock.call_count)
            self.assertEqual(2, failing_mock.call_count)
            self.assertEqual(2, cleanup_mock.call_count)

        self.assertIs(factory.state, NsTestResourceFactoryState.CLOSED)
        self.assertFalse(root.exists())

    def test_concurrent_close_waits_for_one_successful_executor(self) -> None:
        factory = NsTestResourceFactory()
        self.addCleanup(factory.close)
        root = factory.directories.root
        reservation = factory.reserve_tcp_port()
        release = reservation.release
        release_entered = Event()
        allow_release = Event()
        start_gate = Event()
        called = [Event() for _ in range(4)]
        completed = [Event() for _ in range(4)]
        errors: list[BaseException | None] = [None] * 4
        active_lock = Lock()
        active_count = 0
        maximum_active = 0

        def blocking_release() -> bool:
            nonlocal active_count, maximum_active
            with active_lock:
                active_count += 1
                maximum_active = max(maximum_active, active_count)
            release_entered.set()
            try:
                if not allow_release.wait(5):
                    raise AssertionError("release gate timed out")
                return release()
            finally:
                with active_lock:
                    active_count -= 1

        def close_in_thread(index: int) -> None:
            if not start_gate.wait(5):
                errors[index] = AssertionError("start gate timed out")
                completed[index].set()
                return
            called[index].set()
            try:
                factory.close()
            except BaseException as error:
                errors[index] = error
            finally:
                completed[index].set()

        threads = [
            Thread(target=close_in_thread, args=(index,), daemon=True)
            for index in range(4)
        ]
        with mock.patch.object(
            reservation,
            "release",
            side_effect=blocking_release,
        ) as release_mock:
            for thread in threads:
                thread.start()
            start_gate.set()
            try:
                self.assertTrue(release_entered.wait(5))
                self.assertTrue(all(event.wait(5) for event in called))
                self.assertIs(factory.state, NsTestResourceFactoryState.CLOSING)
                self.assertFalse(any(event.is_set() for event in completed))
                self.assertEqual(1, release_mock.call_count)
                self.assertEqual(1, maximum_active)
            finally:
                allow_release.set()

            self.assertTrue(all(event.wait(5) for event in completed))
            for thread in threads:
                thread.join(timeout=1)
                self.assertFalse(thread.is_alive())

            self.assertEqual([None] * 4, errors)
            self.assertEqual(1, release_mock.call_count)
            self.assertEqual(1, maximum_active)

        self.assertIs(factory.state, NsTestResourceFactoryState.CLOSED)
        self.assertTrue(reservation.is_released)
        self.assertFalse(root.exists())

    def test_concurrent_close_retries_after_first_executor_failure(self) -> None:
        factory = NsTestResourceFactory()
        self.addCleanup(factory.close)
        reservation = factory.reserve_tcp_port()
        release = reservation.release
        first_release_entered = Event()
        allow_first_failure = Event()
        start_gate = Event()
        called = [Event() for _ in range(4)]
        completed = [Event() for _ in range(4)]
        errors: list[BaseException | None] = [None] * 4
        active_lock = Lock()
        active_count = 0
        maximum_active = 0
        release_attempts = 0

        def flaky_release() -> bool:
            nonlocal active_count, maximum_active, release_attempts
            with active_lock:
                active_count += 1
                maximum_active = max(maximum_active, active_count)
                release_attempts += 1
                attempt = release_attempts
            try:
                if attempt == 1:
                    first_release_entered.set()
                    if not allow_first_failure.wait(5):
                        raise AssertionError("failure gate timed out")
                    raise OSError("private concurrent cleanup failure")
                return release()
            finally:
                with active_lock:
                    active_count -= 1

        def close_in_thread(index: int) -> None:
            if not start_gate.wait(5):
                errors[index] = AssertionError("start gate timed out")
                completed[index].set()
                return
            called[index].set()
            try:
                factory.close()
            except BaseException as error:
                errors[index] = error
            finally:
                completed[index].set()

        threads = [
            Thread(target=close_in_thread, args=(index,), daemon=True)
            for index in range(4)
        ]
        with mock.patch.object(
            reservation,
            "release",
            side_effect=flaky_release,
        ) as release_mock:
            for thread in threads:
                thread.start()
            start_gate.set()
            try:
                self.assertTrue(first_release_entered.wait(5))
                self.assertTrue(all(event.wait(5) for event in called))
                self.assertFalse(any(event.is_set() for event in completed))
                self.assertEqual(1, release_mock.call_count)
                self.assertEqual(1, maximum_active)
            finally:
                allow_first_failure.set()

            self.assertTrue(all(event.wait(5) for event in completed))
            for thread in threads:
                thread.join(timeout=1)
                self.assertFalse(thread.is_alive())

            stable_errors = [
                error for error in errors if isinstance(error, NsStateError)
            ]
            self.assertEqual(1, len(stable_errors), errors)
            self.assertEqual(3, sum(error is None for error in errors))
            self.assertEqual(2, release_mock.call_count)
            self.assertEqual(2, release_attempts)
            self.assertEqual(1, maximum_active)
            self.assertEqual(
                "closing",
                stable_errors[0].details["state"],
            )

        self.assertIs(factory.state, NsTestResourceFactoryState.CLOSED)
        self.assertTrue(reservation.is_released)

    def test_closing_state_rejects_every_creation_entry_at_call_time(self) -> None:
        factory = NsTestResourceFactory()
        self.addCleanup(factory.close)
        root = factory.directories.root
        entries_before = tuple(sorted(root.rglob("*")))
        owned_port_count = len(factory._ports)
        cleanup = factory._temporary_directory.cleanup
        cleanup_entered = Event()
        allow_cleanup = Event()
        close_completed = Event()
        close_error: list[BaseException] = []

        def blocking_cleanup() -> None:
            cleanup_entered.set()
            if not allow_cleanup.wait(5):
                raise AssertionError("cleanup gate timed out")
            cleanup()

        def close_in_thread() -> None:
            try:
                factory.close()
            except BaseException as error:
                close_error.append(error)
            finally:
                close_completed.set()

        with (
            mock.patch.object(
                factory._temporary_directory,
                "cleanup",
                side_effect=blocking_cleanup,
            ),
            mock.patch.object(
                testing_module.uuid,
                "uuid4",
                side_effect=AssertionError("uuid allocation must not run"),
            ) as uuid_mock,
            mock.patch.object(
                testing_module.socket_module,
                "socket",
                side_effect=AssertionError("socket allocation must not run"),
            ) as socket_mock,
            mock.patch.object(
                testing_module,
                "ControlledClock",
                side_effect=AssertionError("clock allocation must not run"),
            ) as clock_mock,
            mock.patch.object(
                testing_module,
                "InMemoryMetricsSink",
                side_effect=AssertionError("sink allocation must not run"),
            ) as sink_mock,
        ):
            thread = Thread(target=close_in_thread, daemon=True)
            thread.start()
            try:
                self.assertTrue(cleanup_entered.wait(5))
                self.assertIs(factory.state, NsTestResourceFactoryState.CLOSING)
                self.assertTrue(factory.is_closing)
                self.assertFalse(factory.is_closed)

                closing_operations = (
                    ("directories", lambda: factory.directories),
                    (
                        "create_temporary_config",
                        factory.create_temporary_config,
                    ),
                    ("create_controlled_clock", factory.create_controlled_clock),
                    ("create_in_memory_sinks", factory.create_in_memory_sinks),
                    ("reserve_tcp_port", factory.reserve_tcp_port),
                    ("create_redis_namespace", factory.create_redis_namespace),
                    (
                        "manage_redis_namespace",
                        lambda: factory.manage_redis_namespace(_SyncRedisClient()),
                    ),
                    (
                        "amanage_redis_namespace",
                        lambda: factory.amanage_redis_namespace(
                            _AsyncRedisClient()
                        ),
                    ),
                )
                for operation, action in closing_operations:
                    with self.subTest(operation=operation):
                        with self.assertRaises(NsStateError) as caught:
                            action()
                        self.assertEqual(
                            {"operation": operation, "state": "closing"},
                            caught.exception.details,
                        )

                self.assertEqual(entries_before, tuple(sorted(root.rglob("*"))))
                self.assertEqual(owned_port_count, len(factory._ports))
                uuid_mock.assert_not_called()
                socket_mock.assert_not_called()
                clock_mock.assert_not_called()
                sink_mock.assert_not_called()
                self.assertFalse(close_completed.is_set())
            finally:
                allow_cleanup.set()

            self.assertTrue(close_completed.wait(5))
            thread.join(timeout=1)
            self.assertFalse(thread.is_alive())
            self.assertEqual([], close_error)

        self.assertIs(factory.state, NsTestResourceFactoryState.CLOSED)

    def test_process_level_cleanup_exceptions_preserve_pending_ownership(self) -> None:
        for exception_type in (KeyboardInterrupt, SystemExit):
            with self.subTest(exception_type=exception_type.__name__):
                factory = NsTestResourceFactory()
                self.addCleanup(factory.close)
                root = factory.directories.root
                first = factory.reserve_tcp_port()
                interrupting = factory.reserve_tcp_port()
                last = factory.reserve_tcp_port()
                first_release = first.release
                last_release = last.release
                process_error = exception_type("process-level-stop")

                with (
                    mock.patch.object(
                        first,
                        "release",
                        wraps=first_release,
                    ) as first_mock,
                    mock.patch.object(
                        interrupting,
                        "release",
                        side_effect=process_error,
                    ) as interrupting_mock,
                    mock.patch.object(
                        last,
                        "release",
                        wraps=last_release,
                    ) as last_mock,
                ):
                    with self.assertRaises(exception_type) as caught:
                        factory.close()
                    self.assertIs(process_error, caught.exception)
                    self.assertEqual(0, first_mock.call_count)
                    self.assertEqual(1, interrupting_mock.call_count)
                    self.assertEqual(1, last_mock.call_count)
                    self.assertFalse(first.is_released)
                    self.assertFalse(interrupting.is_released)
                    self.assertTrue(last.is_released)
                    self.assertEqual([first, interrupting], factory._ports)
                    self.assertFalse(factory._temporary_directory_released)
                    self.assertTrue(root.exists())
                    self.assertIs(
                        factory.state,
                        NsTestResourceFactoryState.CLOSING,
                    )

                factory.close()
                self.assertIs(factory.state, NsTestResourceFactoryState.CLOSED)
                self.assertTrue(first.is_released)
                self.assertTrue(interrupting.is_released)
                self.assertFalse(root.exists())

    def test_context_manager_preserves_body_and_cleanup_failure_facts(self) -> None:
        normal_body = NsTestResourceFactory()
        self.addCleanup(normal_body.close)
        with mock.patch.object(
            normal_body._temporary_directory,
            "cleanup",
            side_effect=OSError("private cleanup failure"),
        ):
            with self.assertRaises(NsStateError):
                with normal_body:
                    pass
        self.assertIs(normal_body.state, NsTestResourceFactoryState.CLOSING)
        normal_body.close()

        body_failure = NsTestResourceFactory()
        with self.assertRaisesRegex(ValueError, "body-failure"):
            with body_failure:
                raise ValueError("body-failure")
        self.assertIs(body_failure.state, NsTestResourceFactoryState.CLOSED)

        both_fail = NsTestResourceFactory()
        self.addCleanup(both_fail.close)
        with mock.patch.object(
            both_fail._temporary_directory,
            "cleanup",
            side_effect=OSError("private cleanup failure"),
        ):
            with self.assertRaises(NsStateError) as caught:
                with both_fail:
                    raise ValueError("body-failure")
        self.assertIsInstance(caught.exception.__context__, ValueError)
        self.assertEqual("body-failure", str(caught.exception.__context__))
        self.assertNotIn("private cleanup failure", str(caught.exception))
        both_fail.close()


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
        self.assertIs(TestResourceFactoryState, NsTestResourceFactoryState)
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
