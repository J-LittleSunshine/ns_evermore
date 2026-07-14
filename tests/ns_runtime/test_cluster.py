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
from ns_runtime.service import RuntimeService


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


class RuntimeClusterCoordinatorTestCase(
    unittest.TestCase
):
    def test_default_coordinator_is_singleton(
            self,
    ) -> None:
        coordinator = (
            LocalRuntimeClusterCoordinator(
                runtime_id="runtime-1",
            )
        )

        snapshot = coordinator.build_snapshot()

        self.assertEqual(
            snapshot.role,
            "singleton",
        )
        self.assertEqual(
            snapshot.state,
            "ready",
        )
        self.assertFalse(
            snapshot.lease_valid
        )
        self.assertTrue(
            snapshot.can_write_cluster_state
        )
        self.assertEqual(
            snapshot.leader_epoch,
            0,
        )
        self.assertEqual(
            snapshot.fencing_token,
            "",
        )

    def test_standby_master_can_acquire_leadership(
            self,
    ) -> None:
        coordinator = (
            LocalRuntimeClusterCoordinator(
                runtime_id="runtime-1",
                initial_role="standby_master",
                fencing_token_factory=(
                    lambda: "fencing-1"
                ),
            )
        )

        lease = coordinator.acquire_leadership()
        snapshot = coordinator.build_snapshot()

        self.assertEqual(
            lease.holder_runtime_id,
            "runtime-1",
        )
        self.assertEqual(
            lease.epoch,
            1,
        )
        self.assertEqual(
            lease.fencing_token,
            "fencing-1",
        )
        self.assertEqual(
            snapshot.role,
            "active_master",
        )
        self.assertTrue(
            snapshot.lease_valid
        )
        self.assertTrue(
            snapshot.can_write_cluster_state
        )

    def test_sub_node_cannot_acquire_leadership(
            self,
    ) -> None:
        coordinator = (
            LocalRuntimeClusterCoordinator(
                runtime_id="runtime-1",
                initial_role="sub_node",
            )
        )
        snapshot_before = (
            coordinator.build_snapshot()
            .to_dict()
        )

        with self.assertRaises(
                NsRuntimeClusterStateError
        ) as raised:
            coordinator.acquire_leadership()

        self.assertEqual(
            raised.exception.code,
            "RUNTIME_CLUSTER_STATE_ERROR",
        )
        self.assertEqual(
            coordinator.build_snapshot().to_dict(),
            snapshot_before,
        )

    def test_singleton_does_not_fake_leader_lease(
            self,
    ) -> None:
        coordinator = (
            LocalRuntimeClusterCoordinator(
                runtime_id="runtime-1",
            )
        )
        snapshot_before = (
            coordinator.build_snapshot()
            .to_dict()
        )

        with self.assertRaises(
                NsRuntimeClusterStateError
        ):
            coordinator.acquire_leadership()

        self.assertEqual(
            coordinator.build_snapshot().to_dict(),
            snapshot_before,
        )

    def test_leader_renew_preserves_epoch_and_token(
            self,
    ) -> None:
        clock = _MutableClock()
        coordinator = (
            LocalRuntimeClusterCoordinator(
                runtime_id="runtime-1",
                initial_role="standby_master",
                clock=clock,
                fencing_token_factory=(
                    lambda: "fencing-1"
                ),
            )
        )

        first = coordinator.acquire_leadership()
        clock.advance(seconds=5)

        renewed = coordinator.renew_leadership(
            fencing_token=first.fencing_token,
        )

        self.assertEqual(
            renewed.epoch,
            first.epoch,
        )
        self.assertEqual(
            renewed.fencing_token,
            first.fencing_token,
        )
        self.assertEqual(
            renewed.acquired_at,
            first.acquired_at,
        )
        self.assertGreater(
            datetime.fromisoformat(
                renewed.expires_at
            ),
            datetime.fromisoformat(
                first.expires_at
            ),
        )

    def test_stale_fencing_token_cannot_mutate_state(
            self,
    ) -> None:
        coordinator = (
            LocalRuntimeClusterCoordinator(
                runtime_id="runtime-1",
                initial_role="standby_master",
                fencing_token_factory=(
                    lambda: "fencing-1"
                ),
            )
        )

        coordinator.acquire_leadership()

        snapshot_before = (
            coordinator.build_snapshot()
            .to_dict()
        )

        with self.assertRaises(
                NsRuntimeClusterFencingError
        ) as renew_raised:
            coordinator.renew_leadership(
                fencing_token="stale-token",
            )

        self.assertEqual(
            renew_raised.exception.code,
            "RUNTIME_CLUSTER_FENCING_ERROR",
        )
        self.assertEqual(
            coordinator.build_snapshot().to_dict(),
            snapshot_before,
        )

        with self.assertRaises(
                NsRuntimeClusterFencingError
        ):
            coordinator.release_leadership(
                fencing_token="stale-token",
            )

        self.assertEqual(
            coordinator.build_snapshot().to_dict(),
            snapshot_before,
        )

    def test_expired_lease_revokes_write_authority(
            self,
    ) -> None:
        clock = _MutableClock()
        coordinator = (
            LocalRuntimeClusterCoordinator(
                runtime_id="runtime-1",
                initial_role="standby_master",
                lease_ttl_seconds=15,
                clock=clock,
                fencing_token_factory=(
                    lambda: "fencing-1"
                ),
            )
        )

        lease = coordinator.acquire_leadership()

        clock.advance(seconds=16)
        snapshot = coordinator.refresh()

        self.assertEqual(
            snapshot.role,
            "transitioning",
        )
        self.assertEqual(
            snapshot.state,
            "transitioning",
        )
        self.assertFalse(
            snapshot.lease_valid
        )
        self.assertFalse(
            snapshot.can_write_cluster_state
        )
        self.assertEqual(
            snapshot.leader_epoch,
            lease.epoch,
        )
        self.assertEqual(
            snapshot.fencing_token,
            lease.fencing_token,
        )

        with self.assertRaises(
                NsRuntimeClusterStateError
        ):
            coordinator.renew_leadership(
                fencing_token=(
                    lease.fencing_token
                ),
            )

    def test_transitioning_can_complete_leadership_loss(
            self,
    ) -> None:
        clock = _MutableClock()
        coordinator = (
            LocalRuntimeClusterCoordinator(
                runtime_id="runtime-1",
                initial_role="standby_master",
                lease_ttl_seconds=15,
                clock=clock,
                fencing_token_factory=(
                    lambda: "fencing-1"
                ),
            )
        )

        lease = coordinator.acquire_leadership()

        clock.advance(seconds=16)
        coordinator.refresh()

        snapshot = (
            coordinator
            .complete_leadership_loss()
        )

        self.assertEqual(
            snapshot.role,
            "standby_master",
        )
        self.assertEqual(
            snapshot.state,
            "ready",
        )
        self.assertFalse(
            snapshot.lease_valid
        )
        self.assertFalse(
            snapshot.can_write_cluster_state
        )
        self.assertEqual(
            snapshot.leader_epoch,
            lease.epoch,
        )
        self.assertEqual(
            snapshot.leader_runtime_id,
            "",
        )
        self.assertEqual(
            snapshot.fencing_token,
            "",
        )

    def test_active_master_can_release_to_standby(
            self,
    ) -> None:
        coordinator = (
            LocalRuntimeClusterCoordinator(
                runtime_id="runtime-1",
                initial_role="standby_master",
                fencing_token_factory=(
                    lambda: "fencing-1"
                ),
            )
        )

        lease = coordinator.acquire_leadership()

        snapshot = (
            coordinator.release_leadership(
                fencing_token=(
                    lease.fencing_token
                ),
            )
        )

        self.assertEqual(
            snapshot.role,
            "standby_master",
        )
        self.assertFalse(
            snapshot.lease_valid
        )
        self.assertFalse(
            snapshot.can_write_cluster_state
        )
        self.assertEqual(
            snapshot.leader_epoch,
            lease.epoch,
        )
        self.assertEqual(
            snapshot.fencing_token,
            "",
        )

    def test_new_epoch_cannot_reuse_previous_fencing_token(
            self,
    ) -> None:
        tokens = iter(
            (
                "fencing-1",
                "fencing-1",
            )
        )

        coordinator = (
            LocalRuntimeClusterCoordinator(
                runtime_id="runtime-1",
                initial_role="standby_master",
                fencing_token_factory=(
                    lambda: next(tokens)
                ),
            )
        )

        first_lease = (
            coordinator.acquire_leadership()
        )

        coordinator.release_leadership(
            fencing_token=(
                first_lease.fencing_token
            ),
        )

        snapshot_before = (
            coordinator.build_snapshot()
        )

        with self.assertRaises(
                NsRuntimeClusterFencingError
        ) as raised:
            coordinator.acquire_leadership()

        self.assertEqual(
            raised.exception.code,
            "RUNTIME_CLUSTER_FENCING_ERROR",
        )

        snapshot_after = (
            coordinator.build_snapshot()
        )

        self.assertEqual(
            snapshot_after.role,
            "standby_master",
        )
        self.assertEqual(
            snapshot_after.leader_epoch,
            snapshot_before.leader_epoch,
        )
        self.assertFalse(
            snapshot_after.lease_valid
        )
        self.assertFalse(
            snapshot_after
            .can_write_cluster_state
        )

    def test_new_epoch_cannot_reuse_any_historical_fencing_token(
            self,
    ) -> None:
        tokens = iter(
            (
                "fencing-1",
                "fencing-2",
                "fencing-1",
            )
        )

        coordinator = (
            LocalRuntimeClusterCoordinator(
                runtime_id="runtime-1",
                initial_role="standby_master",
                fencing_token_factory=(
                    lambda: next(tokens)
                ),
            )
        )

        first_lease = (
            coordinator.acquire_leadership()
        )
        coordinator.release_leadership(
            fencing_token=(
                first_lease.fencing_token
            ),
        )

        second_lease = (
            coordinator.acquire_leadership()
        )
        coordinator.release_leadership(
            fencing_token=(
                second_lease.fencing_token
            ),
        )

        snapshot_before = (
            coordinator.build_snapshot()
        )

        self.assertEqual(
            snapshot_before.leader_epoch,
            2,
        )
        self.assertEqual(
            snapshot_before.role,
            "standby_master",
        )

        with self.assertRaises(
                NsRuntimeClusterFencingError
        ) as raised:
            coordinator.acquire_leadership()

        self.assertEqual(
            raised.exception.code,
            "RUNTIME_CLUSTER_FENCING_ERROR",
        )

        snapshot_after = (
            coordinator.build_snapshot()
        )

        self.assertEqual(
            snapshot_after.role,
            "standby_master",
        )
        self.assertEqual(
            snapshot_after.leader_epoch,
            2,
        )
        self.assertFalse(
            snapshot_after.lease_valid
        )
        self.assertFalse(
            snapshot_after.can_write_cluster_state
        )
        self.assertEqual(
            snapshot_after.to_dict(),
            snapshot_before.to_dict(),
        )

    def test_service_exposes_cluster_snapshot(
            self,
    ) -> None:
        service = RuntimeService.build_default(
            runtime_id="runtime-1",
            runtime_role="standby_master",
        )

        snapshot = (
            service.build_runtime_snapshot()
        )

        cluster = snapshot["cluster"]
        connections = snapshot["connections"]

        self.assertEqual(
            cluster["runtime_id"],
            "runtime-1",
        )
        self.assertEqual(
            cluster["role"],
            "standby_master",
        )
        self.assertFalse(
            cluster["can_write_cluster_state"]
        )
        self.assertEqual(
            connections["runtime_id"],
            "runtime-1",
        )

    def test_service_rejects_mismatched_coordinator_runtime_id(
            self,
    ) -> None:
        coordinator = (
            LocalRuntimeClusterCoordinator(
                runtime_id="runtime-2",
            )
        )

        with self.assertRaises(ValueError):
            RuntimeService.build_default(
                runtime_id="runtime-1",
                cluster_coordinator=coordinator,
            )

if __name__ == "__main__":
    unittest.main()
