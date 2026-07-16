# -*- coding: utf-8 -*-
from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from django.core.cache.backends.base import DEFAULT_TIMEOUT

from ns_common.cache.backends.dummy import DummyCacheBackend
from ns_common.cache.backends.sqlite import SQLiteCacheBackend
from ns_common.cache.clients import CacheClient
from ns_common.cache.django import NsDjangoCacheBackend
from ns_common.config import NsCacheConfig
from ns_common.exceptions import NsValidationError


class CacheTestFactory:
    """
    测试客户端工厂。

    测试不依赖全局 ns_config，避免污染真实 data/ns_cache.sqlite3。
    """

    @staticmethod
    def build_sqlite_client(sqlite_path: Path, *, none_ttl_means_forever: bool = False) -> CacheClient:
        cache_config = NsCacheConfig(
            backend="sqlite",
            key_prefix="test_ns",
            django_namespace="ns_backend",
            default_ttl_seconds=1,
            none_ttl_means_forever=none_ttl_means_forever,
            sqlite_path=str(sqlite_path),
            cleanup_interval_seconds=1,
            cleanup_batch_size=100,
        )
        backend = SQLiteCacheBackend(
            config=cache_config,
            sqlite_path=sqlite_path,
        )
        backend.initialize()

        return CacheClient(
            namespace="iam",
            backend=backend,
            cache_config=cache_config,
        )


class SQLiteCacheBackendTestCase(unittest.TestCase):

    def test_set_get_delete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            client = CacheTestFactory.build_sqlite_client(
                Path(temp_dir) / "ns_cache.sqlite3",
            )

            self.assertTrue(client.set("user:1", {"id": 1}, ttl=60))
            self.assertEqual({"id": 1}, client.get("user:1"))

            self.assertTrue(client.exists("user:1"))
            self.assertTrue(client.delete("user:1"))
            self.assertIsNone(client.get("user:1"))

    def test_get_many_set_many_delete_many(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            client = CacheTestFactory.build_sqlite_client(
                Path(temp_dir) / "ns_cache.sqlite3",
            )

            self.assertTrue(
                client.set_many(
                    {
                        "a": 1,
                        "b": {
                            "value": 2,
                        },
                    },
                    ttl=60,
                )
            )

            self.assertEqual(
                {
                    "a": 1,
                    "b": {
                        "value": 2,
                    },
                },
                client.get_many([
                    "a",
                    "b",
                    "c"
                ]
                ),
            )

            self.assertEqual(2, client.delete_many([
                "a",
                "b"
            ]
            )
            )
            self.assertEqual({}, client.get_many([
                "a",
                "b"
            ]
            )
            )

    def test_ttl_expired(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            client = CacheTestFactory.build_sqlite_client(
                Path(temp_dir) / "ns_cache.sqlite3",
            )

            self.assertTrue(client.set("short", "value", ttl=1))
            self.assertEqual("value", client.get("short"))

            time.sleep(1.2)
            self.assertIsNone(client.get("short"))

    def test_none_ttl_can_mean_forever(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            client = CacheTestFactory.build_sqlite_client(
                Path(temp_dir) / "ns_cache.sqlite3",
                none_ttl_means_forever=True,
            )

            self.assertTrue(client.set("forever", "value", ttl=None))
            time.sleep(1.2)

            self.assertEqual("value", client.get("forever"))

    def test_incr_decr(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            client = CacheTestFactory.build_sqlite_client(
                Path(temp_dir) / "ns_cache.sqlite3",
            )

            self.assertTrue(client.set("counter", 1, ttl=60))
            self.assertEqual(2, client.incr("counter"))
            self.assertEqual(1, client.decr("counter"))

    def test_clear_only_namespace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            sqlite_path = Path(temp_dir) / "ns_cache.sqlite3"
            client = CacheTestFactory.build_sqlite_client(sqlite_path)

            another_config = NsCacheConfig(
                backend="sqlite",
                key_prefix="test_ns",
                default_ttl_seconds=60,
                sqlite_path=str(sqlite_path),
            )
            backend = SQLiteCacheBackend(
                config=another_config,
                sqlite_path=sqlite_path,
            )
            backend.initialize()

            another_client = CacheClient(
                namespace="other",
                backend=backend,
                cache_config=another_config,
            )

            client.set("k1", "v1", ttl=60)
            another_client.set("k1", "v2", ttl=60)

            self.assertTrue(client.clear())
            self.assertIsNone(client.get("k1"))
            self.assertEqual("v2", another_client.get("k1"))

    def test_invalid_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            client = CacheTestFactory.build_sqlite_client(
                Path(temp_dir) / "ns_cache.sqlite3",
            )

            with self.assertRaises(NsValidationError):
                client.set("bad key", "value", ttl=60)

            with self.assertRaises(NsValidationError):
                client.set("bad*key", "value", ttl=60)

    def test_json_serialization_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            client = CacheTestFactory.build_sqlite_client(
                Path(temp_dir) / "ns_cache.sqlite3",
            )

            with self.assertRaises(NsValidationError):
                client.set("obj", object(), ttl=60)


class DummyCacheBackendTestCase(unittest.TestCase):

    def test_dummy_backend(self) -> None:
        cache_config = NsCacheConfig(
            backend="dummy",
            key_prefix="test_ns",
            default_ttl_seconds=60,
        )
        backend = DummyCacheBackend()
        backend.initialize()

        client = CacheClient(
            namespace="iam",
            backend=backend,
            cache_config=cache_config,
        )

        self.assertTrue(client.set("k1", "v1", ttl=60))
        self.assertIsNone(client.get("k1"))
        self.assertFalse(client.exists("k1"))
        self.assertTrue(client.clear())


class NsDjangoCacheBackendTestCase(unittest.TestCase):

    def test_django_cache_backend_uses_version_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            client = CacheTestFactory.build_sqlite_client(
                Path(temp_dir) / "ns_cache.sqlite3",
            )

            with patch("ns_common.cache.django.get_cache_client", return_value=client):
                backend = NsDjangoCacheBackend(
                    "default",
                    {
                        "TIMEOUT": 300,
                        "OPTIONS": {},
                    },
                )

                self.assertTrue(
                    backend.set(
                        "user:1",
                        {
                            "name": "test",
                        },
                        timeout=60,
                        version=2,
                    )
                )

                self.assertEqual(
                    {
                        "name": "test",
                    },
                    backend.get(
                        "user:1",
                        version=2,
                    ),
                )

                self.assertIsNone(
                    backend.get(
                        "user:1",
                        version=1,
                    )
                )

    def test_django_timeout_default_uses_common_default_ttl(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            client = CacheTestFactory.build_sqlite_client(
                Path(temp_dir) / "ns_cache.sqlite3",
            )

            with patch("ns_common.cache.django.get_cache_client", return_value=client):
                backend = NsDjangoCacheBackend(
                    "default",
                    {
                        "TIMEOUT": 300,
                        "OPTIONS": {},
                    },
                )

                self.assertTrue(
                    backend.set(
                        "short",
                        "value",
                        timeout=DEFAULT_TIMEOUT,
                    )
                )

                self.assertEqual("value", backend.get("short"))
                time.sleep(1.2)
                self.assertIsNone(backend.get("short"))


if __name__ == "__main__":
    unittest.main()
