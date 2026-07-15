# -*- coding: utf-8 -*-
from __future__ import annotations

import unittest

from ns_runtime.cluster import (
    RuntimeClusterSnapshot,
)
from ns_runtime.role_admission import (
    LocalRuntimeRoleAdmissionPolicy,
)


class RuntimeRoleAdmissionPolicyTestCase(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.policy = (
            LocalRuntimeRoleAdmissionPolicy()
        )

    def test_singleton_accepts_ordinary_connection(
            self,
    ) -> None:
        decision = (
            self.policy.evaluate_connection(
                snapshot=self._snapshot(
                    role="singleton",
                ),
                component_type="client",
                active_sub_node_count=0,
            )
        )

        self.assertTrue(decision.accepted)

    def test_sub_node_accepts_ordinary_connection(
            self,
    ) -> None:
        decision = (
            self.policy.evaluate_connection(
                snapshot=self._snapshot(
                    role="sub_node",
                ),
                component_type="frontend",
                active_sub_node_count=0,
            )
        )

        self.assertTrue(decision.accepted)

    def test_standby_master_only_accepts_internal_connections(
            self,
    ) -> None:
        for component_type in (
                "runtime",
                "sub_node",
                "management",
        ):
            with self.subTest(
                    component_type=component_type
            ):
                decision = (
                    self.policy
                    .evaluate_connection(
                        snapshot=self._snapshot(
                            role=(
                                "standby_master"
                            ),
                        ),
                        component_type=(
                            component_type
                        ),
                        active_sub_node_count=0,
                    )
                )

                self.assertTrue(
                    decision.accepted
                )

        rejected = (
            self.policy.evaluate_connection(
                snapshot=self._snapshot(
                    role="standby_master",
                ),
                component_type="client",
                active_sub_node_count=0,
            )
        )

        self.assertFalse(rejected.accepted)
        self.assertEqual(
            rejected.reason_code,
            "RUNTIME_ROLE_ADMISSION_REJECTED",
        )

    def test_active_master_without_sub_node_accepts_ordinary_connection(
            self,
    ) -> None:
        decision = (
            self.policy.evaluate_connection(
                snapshot=self._snapshot(
                    role="active_master",
                ),
                component_type="client",
                active_sub_node_count=0,
            )
        )

        self.assertTrue(decision.accepted)

    def test_active_master_with_sub_node_rejects_new_ordinary_connection(
            self,
    ) -> None:
        rejected = (
            self.policy.evaluate_connection(
                snapshot=self._snapshot(
                    role="active_master",
                ),
                component_type="client",
                active_sub_node_count=1,
            )
        )

        internal = (
            self.policy.evaluate_connection(
                snapshot=self._snapshot(
                    role="active_master",
                ),
                component_type="sub_node",
                active_sub_node_count=1,
            )
        )

        self.assertFalse(rejected.accepted)
        self.assertTrue(internal.accepted)

    def test_transitioning_rejects_new_task_dispatch(
            self,
    ) -> None:
        decision = (
            self.policy.evaluate_message(
                snapshot=self._snapshot(
                    role="transitioning",
                    state="transitioning",
                ),
                component_type="management",
                message_type="task.dispatch",
                message_category="task",
            )
        )

        self.assertFalse(decision.accepted)

    def test_transitioning_allows_continuation_and_control_messages(
            self,
    ) -> None:
        message_types = (
            "connection.heartbeat",
            "connection.drain",
            "delivery.ack",
            "delivery.nack",
            "delivery.defer",
            "runtime.control.health",
            "runtime.control.node_status",
            "cluster.event.heartbeat",
        )

        for message_type in message_types:
            with self.subTest(
                    message_type=message_type
            ):
                decision = (
                    self.policy.evaluate_message(
                        snapshot=self._snapshot(
                            role="transitioning",
                            state="transitioning",
                        ),
                        component_type=(
                            "management"
                        ),
                        message_type=message_type,
                        message_category=(
                            "control"
                        ),
                    )
                )

                self.assertTrue(
                    decision.accepted
                )

    def test_standby_master_rejects_task_but_allows_control(
            self,
    ) -> None:
        task_decision = (
            self.policy.evaluate_message(
                snapshot=self._snapshot(
                    role="standby_master",
                ),
                component_type="management",
                message_type="task.dispatch",
                message_category="task",
            )
        )

        control_decision = (
            self.policy.evaluate_message(
                snapshot=self._snapshot(
                    role="standby_master",
                ),
                component_type="management",
                message_type=(
                    "runtime.control.health"
                ),
                message_category="control",
            )
        )

        self.assertFalse(
            task_decision.accepted
        )
        self.assertTrue(
            control_decision.accepted
        )

    @staticmethod
    def _snapshot(
            *,
            role,
            state="ready",
    ) -> RuntimeClusterSnapshot:
        return RuntimeClusterSnapshot(
            runtime_id="runtime-test",
            role=role,
            state=state,
            leader_runtime_id="",
            leader_epoch=0,
            fencing_token="",
            lease_expires_at="",
            lease_valid=False,
            can_write_cluster_state=False,
            updated_at=(
                "2026-01-01T00:00:00.000+00:00"
            ),
        )


if __name__ == "__main__":
    unittest.main()
