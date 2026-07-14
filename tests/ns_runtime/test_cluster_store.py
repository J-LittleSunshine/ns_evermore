# -*- coding: utf-8 -*-
from __future__ import annotations

import unittest
from datetime import (
    datetime,
    timedelta,
    timezone,
)

from ns_common.exceptions import (
    NsRuntimeClusterFencingError,
    NsRuntimeClusterStateError,
)
from ns_runtime.cluster import (
    LocalRuntimeClusterCoordinator,
)
from ns_runtime.cluster_store import (
    InMemoryRuntimeLeaderLeaseStore,
    RuntimeLeaderLeaseStore,
    RuntimeLeaderLeaseStoreSnapshot,
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


class _FailingAcquireLeaseStore(
        RuntimeLeaderLeaseStore
):
    def __init__(self) -> None:
        self.snapshot = (
            RuntimeLeaderLeaseStoreSnapshot(
                lease=None,
                version=0,
                last_epoch=0,
                issued_fencing_tokens=(),
                lease_valid=False,
                observed_at=(
                    datetime(
                        2026,
                        1,
                        1,
                        tzinfo=timezone.utc,
                    ).isoformat(
                        timespec="milliseconds"
                    )
                ),
            )
        )

    def read(
            self,
    ) -> RuntimeLeaderLeaseStoreSnapshot:
        return self.snapshot

    def try_acquire(
            self,
            **kwargs,
    ) -> RuntimeLeaderLeaseStoreSnapshot:
        raise NsRuntimeClusterStateError(
            "simulated store failure"
        )

    def try_renew(
            self,
            **kwargs,
    ) -> RuntimeLeaderLeaseStoreSnapshot:
        raise NotImplementedError

    def try_release(
            self,
            **kwargs,
    ) -> RuntimeLeaderLeaseStoreSnapshot:
        raise NotImplementedError


class RuntimeLeaderLeaseStoreTestCase(
        unittest.TestCase
):
    def setUp(self) -> None:
        self.clock = _MutableClock()
        self.store = (
            InMemoryRuntimeLeaderLeaseStore(
                clock=self.clock
            )
        )

    def test_acquire_renew_and_release_preserve_invariants(
            self,
    ) -> None:
        empty = self.store.read()

        acquired = self.store.try_acquire(
            runtime_id="runtime-1",
            fencing_token="token-1",
            ttl_seconds=15,
            expected_version=empty.version,
        )

        self.assertEqual(
            acquired.version,
            1,
        )
        self.assertEqual(
            acquired.lease.epoch,
            1,
        )
        self.assertEqual(
            acquired.lease.fencing_token,
            "token-1",
        )
        self.assertTrue(
            acquired.lease_valid
        )

        self.clock.advance(
            seconds=5
        )

        renewed = self.store.try_renew(
            runtime_id="runtime-1",
            epoch=acquired.lease.epoch,
            fencing_token=(
                acquired.lease.fencing_token
            ),
            ttl_seconds=15,
            expected_version=acquired.version,
        )

        self.assertEqual(
            renewed.version,
            2,
        )
        self.assertEqual(
            renewed.lease.epoch,
            acquired.lease.epoch,
        )
        self.assertEqual(
            renewed.lease.fencing_token,
            acquired.lease.fencing_token,
        )
        self.assertGreater(
            datetime.fromisoformat(
                renewed.lease.expires_at
            ),
            datetime.fromisoformat(
                acquired.lease.expires_at
            ),
        )

        released = self.store.try_release(
            runtime_id="runtime-1",
            epoch=renewed.lease.epoch,
            fencing_token=(
                renewed.lease.fencing_token
            ),
            expected_version=renewed.version,
        )

        self.assertEqual(
            released.version,
            3,
        )
        self.assertIsNone(
            released.lease
        )
        self.assertEqual(
            released.last_epoch,
            1,
        )
        self.assertEqual(
            released.issued_fencing_tokens,
            (
                "token-1",
            ),
        )

    def test_wrong_token_cannot_renew_or_release(
            self,
    ) -> None:
        acquired = self.store.try_acquire(
            runtime_id="runtime-1",
            fencing_token="token-1",
            ttl_seconds=15,
            expected_version=0,
        )

        snapshot_before = self.store.read()

        with self.assertRaises(
                NsRuntimeClusterFencingError
        ):
            self.store.try_renew(
                runtime_id="runtime-1",
                epoch=acquired.lease.epoch,
                fencing_token="wrong-token",
                ttl_seconds=15,
                expected_version=(
                    acquired.version
                ),
            )

        with self.assertRaises(
                NsRuntimeClusterFencingError
        ):
            self.store.try_release(
                runtime_id="runtime-1",
                epoch=acquired.lease.epoch,
                fencing_token="wrong-token",
                expected_version=(
                    acquired.version
                ),
            )

        self.assertEqual(
            self.store.read(),
            snapshot_before,
        )

    def test_expired_lease_can_be_replaced_with_new_epoch(
            self,
    ) -> None:
        first = self.store.try_acquire(
            runtime_id="runtime-1",
            fencing_token="token-1",
            ttl_seconds=15,
            expected_version=0,
        )

        self.clock.advance(
            seconds=16
        )

        expired = self.store.read()

        self.assertFalse(
            expired.lease_valid
        )

        second = self.store.try_acquire(
            runtime_id="runtime-2",
            fencing_token="token-2",
            ttl_seconds=15,
            expected_version=expired.version,
        )

        self.assertEqual(
            second.lease.epoch,
            2,
        )
        self.assertEqual(
            second.lease.holder_runtime_id,
            "runtime-2",
        )
        self.assertEqual(
            second.last_epoch,
            2,
        )
        self.assertEqual(
            second.issued_fencing_tokens,
            (
                "token-1",
                "token-2",
            ),
        )
        self.assertEqual(
            first.lease.epoch,
            1,
        )

    def test_any_historical_token_is_rejected(
            self,
    ) -> None:
        first = self.store.try_acquire(
            runtime_id="runtime-1",
            fencing_token="token-1",
            ttl_seconds=15,
            expected_version=0,
        )

        released_first = (
            self.store.try_release(
                runtime_id="runtime-1",
                epoch=1,
                fencing_token="token-1",
                expected_version=(
                    first.version
                ),
            )
        )

        second = self.store.try_acquire(
            runtime_id="runtime-1",
            fencing_token="token-2",
            ttl_seconds=15,
            expected_version=(
                released_first.version
            ),
        )

        released_second = (
            self.store.try_release(
                runtime_id="runtime-1",
                epoch=2,
                fencing_token="token-2",
                expected_version=(
                    second.version
                ),
            )
        )

        snapshot_before = self.store.read()

        with self.assertRaises(
                NsRuntimeClusterFencingError
        ):
            self.store.try_acquire(
                runtime_id="runtime-1",
                fencing_token="token-1",
                ttl_seconds=15,
                expected_version=(
                    released_second.version
                ),
            )

        self.assertEqual(
            self.store.read(),
            snapshot_before,
        )

    def test_stale_version_does_not_mutate_state(
            self,
    ) -> None:
        acquired = self.store.try_acquire(
            runtime_id="runtime-1",
            fencing_token="token-1",
            ttl_seconds=15,
            expected_version=0,
        )

        snapshot_before = self.store.read()

        with self.assertRaises(
                NsRuntimeClusterStateError
        ):
            self.store.try_renew(
                runtime_id="runtime-1",
                epoch=1,
                fencing_token="token-1",
                ttl_seconds=15,
                expected_version=(
                    acquired.version + 1
                ),
            )

        self.assertEqual(
            self.store.read(),
            snapshot_before,
        )

    def test_two_coordinators_share_single_leader_authority(
            self,
    ) -> None:
        coordinator_1 = (
            LocalRuntimeClusterCoordinator(
                runtime_id="runtime-1",
                initial_role="standby_master",
                clock=self.clock,
                fencing_token_factory=(
                    lambda: "token-1"
                ),
                lease_store=self.store,
            )
        )
        coordinator_2 = (
            LocalRuntimeClusterCoordinator(
                runtime_id="runtime-2",
                initial_role="standby_master",
                clock=self.clock,
                fencing_token_factory=(
                    lambda: "token-2"
                ),
                lease_store=self.store,
            )
        )

        coordinator_1.acquire_leadership()

        with self.assertRaises(
                NsRuntimeClusterStateError
        ):
            coordinator_2.acquire_leadership()

        self.assertEqual(
            coordinator_1
            .build_snapshot()
            .role,
            "active_master",
        )

        coordinator_2_snapshot = (
            coordinator_2.build_snapshot()
        )

        self.assertEqual(
            coordinator_2_snapshot.role,
            "standby_master",
        )
        self.assertEqual(
            coordinator_2_snapshot
            .leader_runtime_id,
            "runtime-1",
        )
        self.assertFalse(
            coordinator_2_snapshot
            .can_write_cluster_state
        )

    def test_stale_same_runtime_coordinator_loses_authority(
            self,
    ) -> None:
        coordinator_1 = (
            LocalRuntimeClusterCoordinator(
                runtime_id="runtime-1",
                initial_role="standby_master",
                lease_ttl_seconds=15,
                clock=self.clock,
                fencing_token_factory=(
                    lambda: "token-1"
                ),
                lease_store=self.store,
            )
        )

        coordinator_2 = (
            LocalRuntimeClusterCoordinator(
                runtime_id="runtime-1",
                initial_role="standby_master",
                lease_ttl_seconds=15,
                clock=self.clock,
                fencing_token_factory=(
                    lambda: "token-2"
                ),
                lease_store=self.store,
            )
        )

        first = (
            coordinator_1
            .acquire_leadership()
        )

        self.assertEqual(
            first.epoch,
            1,
        )
        self.assertEqual(
            coordinator_1.role,
            "active_master",
        )

        self.clock.advance(
            seconds=16
        )

        second = (
            coordinator_2
            .acquire_leadership()
        )

        self.assertEqual(
            second.epoch,
            2,
        )
        self.assertEqual(
            second.fencing_token,
            "token-2",
        )

        stale_snapshot = (
            coordinator_1.refresh()
        )

        self.assertEqual(
            stale_snapshot.role,
            "transitioning",
        )
        self.assertEqual(
            stale_snapshot.state,
            "transitioning",
        )
        self.assertEqual(
            stale_snapshot.leader_epoch,
            2,
        )
        self.assertFalse(
            stale_snapshot
            .can_write_cluster_state
        )

    def test_store_failure_does_not_promote_coordinator(
            self,
    ) -> None:
        coordinator = (
            LocalRuntimeClusterCoordinator(
                runtime_id="runtime-1",
                initial_role="standby_master",
                fencing_token_factory=(
                    lambda: "token-1"
                ),
                lease_store=(
                    _FailingAcquireLeaseStore()
                ),
            )
        )

        snapshot_before = (
            coordinator.build_snapshot()
        )

        with self.assertRaises(
                NsRuntimeClusterStateError
        ):
            coordinator.acquire_leadership()

        snapshot_after = (
            coordinator.build_snapshot()
        )

        self.assertEqual(
            snapshot_after.role,
            "standby_master",
        )
        self.assertFalse(
            snapshot_after
            .can_write_cluster_state
        )
        self.assertEqual(
            snapshot_after.to_dict(),
            snapshot_before.to_dict(),
        )


if __name__ == "__main__":
    unittest.main()