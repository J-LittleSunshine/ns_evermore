# -*- coding: utf-8 -*-
from __future__ import annotations

import unittest
from datetime import (
    datetime,
    timedelta,
    timezone,
)

from ns_runtime.state_store import (
    InMemoryRuntimeStateStore,
)


class _MutableClock:
    def __init__(self) -> None:
        self.current = datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        )

    def __call__(self) -> datetime:
        return self.current

    def advance(
            self,
            *,
            seconds: float,
    ) -> None:
        self.current += timedelta(
            seconds=seconds
        )


class RuntimeStateStoreTestCase(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.clock = _MutableClock()
        self.store = InMemoryRuntimeStateStore(
            clock=self.clock
        )

    def test_capabilities_describe_memory_backend(
            self,
    ) -> None:
        capabilities = self.store.capabilities

        self.assertEqual(
            capabilities.backend_name,
            "memory",
        )
        self.assertTrue(
            capabilities.supports_atomic_create
        )
        self.assertTrue(
            capabilities
            .supports_compare_and_swap
        )
        self.assertTrue(
            capabilities.supports_ttl
        )
        self.assertFalse(
            capabilities.durable
        )
        self.assertFalse(
            capabilities.distributed_authority
        )

    def test_put_if_absent_is_atomic(
            self,
    ) -> None:
        first = self.store.put_if_absent(
            namespace="tenant:1",
            key="item",
            value={
                "status": "created",
            },
        )
        second = self.store.put_if_absent(
            namespace="tenant:1",
            key="item",
            value={
                "status": "overwritten",
            },
        )

        self.assertTrue(first.success)
        self.assertEqual(
            first.status,
            "created",
        )
        self.assertEqual(
            first.entry.version,
            1,
        )

        self.assertFalse(second.success)
        self.assertEqual(
            second.status,
            "conflict",
        )

        self.assertEqual(
            self.store.get(
                namespace="tenant:1",
                key="item",
            ).value,
            {
                "status": "created",
            },
        )

    def test_compare_and_swap_requires_current_version(
            self,
    ) -> None:
        created = self.store.put_if_absent(
            namespace="system",
            key="config",
            value={
                "revision": 1,
            },
        )

        stale = self.store.compare_and_swap(
            namespace="system",
            key="config",
            expected_version=(
                    created.entry.version + 1
            ),
            value={
                "revision": 2,
            },
        )

        self.assertFalse(stale.success)
        self.assertEqual(
            stale.status,
            "conflict",
        )
        self.assertEqual(
            stale.current_entry.version,
            1,
        )
        self.assertEqual(
            self.store.get(
                namespace="system",
                key="config",
            ).value,
            {
                "revision": 1,
            },
        )

        updated = self.store.compare_and_swap(
            namespace="system",
            key="config",
            expected_version=(
                created.entry.version
            ),
            value={
                "revision": 2,
            },
        )

        self.assertTrue(updated.success)
        self.assertEqual(
            updated.status,
            "updated",
        )
        self.assertEqual(
            updated.entry.version,
            2,
        )
        self.assertEqual(
            updated.entry.value,
            {
                "revision": 2,
            },
        )

    def test_namespace_isolation(
            self,
    ) -> None:
        self.store.put_if_absent(
            namespace="tenant:1",
            key="same-key",
            value={
                "tenant": 1,
            },
        )
        self.store.put_if_absent(
            namespace="tenant:2",
            key="same-key",
            value={
                "tenant": 2,
            },
        )

        self.assertEqual(
            self.store.get(
                namespace="tenant:1",
                key="same-key",
            ).value,
            {
                "tenant": 1,
            },
        )
        self.assertEqual(
            self.store.get(
                namespace="tenant:2",
                key="same-key",
            ).value,
            {
                "tenant": 2,
            },
        )

    def test_expired_entry_is_not_returned(
            self,
    ) -> None:
        self.store.put_if_absent(
            namespace="system",
            key="temporary",
            value={
                "active": True,
            },
            ttl_seconds=10,
        )

        self.clock.advance(
            seconds=10
        )

        self.assertIsNone(
            self.store.get(
                namespace="system",
                key="temporary",
            )
        )

    def test_returned_values_do_not_mutate_store(
            self,
    ) -> None:
        result = self.store.put_if_absent(
            namespace="system",
            key="copy-test",
            value={
                "items": [
                    "a",
                ],
            },
        )

        result.entry.value[
            "items"
        ].append(
            "b"
        )

        read_entry = self.store.get(
            namespace="system",
            key="copy-test",
        )

        read_entry.value[
            "items"
        ].append(
            "c"
        )

        self.assertEqual(
            self.store.get(
                namespace="system",
                key="copy-test",
            ).value,
            {
                "items": [
                    "a",
                ],
            },
        )

    def test_delete_if_version_is_failure_atomic(
            self,
    ) -> None:
        created = self.store.put_if_absent(
            namespace="system",
            key="delete-test",
            value={
                "active": True,
            },
        )

        stale = self.store.delete_if_version(
            namespace="system",
            key="delete-test",
            expected_version=(
                    created.entry.version + 1
            ),
        )

        self.assertFalse(stale.success)
        self.assertEqual(
            stale.status,
            "conflict",
        )
        self.assertIsNotNone(
            self.store.get(
                namespace="system",
                key="delete-test",
            )
        )

        deleted = self.store.delete_if_version(
            namespace="system",
            key="delete-test",
            expected_version=(
                created.entry.version
            ),
        )

        self.assertTrue(deleted.success)
        self.assertEqual(
            deleted.status,
            "deleted",
        )
        self.assertIsNone(
            self.store.get(
                namespace="system",
                key="delete-test",
            )
        )

    def test_version_does_not_reset_after_delete(
            self,
    ) -> None:
        first = self.store.put_if_absent(
            namespace="system",
            key="aba-delete",
            value={
                "generation": 1,
            },
        )

        deleted = self.store.delete_if_version(
            namespace="system",
            key="aba-delete",
            expected_version=(
                first.entry.version
            ),
        )

        self.assertTrue(deleted.success)

        second = self.store.put_if_absent(
            namespace="system",
            key="aba-delete",
            value={
                "generation": 2,
            },
        )

        self.assertTrue(second.success)
        self.assertGreater(
            second.entry.version,
            first.entry.version,
        )

        stale = self.store.compare_and_swap(
            namespace="system",
            key="aba-delete",
            expected_version=(
                first.entry.version
            ),
            value={
                "generation": 999,
            },
        )

        self.assertFalse(stale.success)
        self.assertEqual(
            stale.status,
            "conflict",
        )
        self.assertEqual(
            self.store.get(
                namespace="system",
                key="aba-delete",
            ).value,
            {
                "generation": 2,
            },
        )

    def test_version_does_not_reset_after_expiry(
            self,
    ) -> None:
        first = self.store.put_if_absent(
            namespace="system",
            key="aba-expiry",
            value={
                "generation": 1,
            },
            ttl_seconds=10,
        )

        self.clock.advance(
            seconds=10
        )

        self.assertIsNone(
            self.store.get(
                namespace="system",
                key="aba-expiry",
            )
        )

        second = self.store.put_if_absent(
            namespace="system",
            key="aba-expiry",
            value={
                "generation": 2,
            },
        )

        self.assertTrue(second.success)
        self.assertGreater(
            second.entry.version,
            first.entry.version,
        )

if __name__ == "__main__":
    unittest.main()
