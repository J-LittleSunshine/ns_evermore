# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import unittest

from ns_common.async_runtime import TaskSupervisor
from ns_common.config import NsConfig
from ns_common.exceptions import (
    NsRuntimeFeatureDisabledError,
    NsValidationError,
)
from ns_common.observability import InMemoryMetricsSink, InMemoryTraceSink
from ns_common.time import SystemClock
from ns_runtime.context import RuntimeContext
from ns_runtime.roles import (
    RuntimeCapability,
    RuntimeHealth,
    RuntimeRole,
    RuntimeRoleState,
)
from ns_runtime.service import RuntimeService


class _ListHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def _context_for_role(role: str, logger: logging.Logger) -> RuntimeContext:
    raw_config: dict[str, object] = {"runtime": {"cluster": {"role": role}}}
    if role == "sub_node":
        raw_config["runtime"]["cluster"]["active_master_url"] = (  # type: ignore[index]
            "https://master.example.test"
        )
    return RuntimeContext(
        config=NsConfig.from_dict(raw_config),
        clock=SystemClock(),
        logger=logger,
        metrics=InMemoryMetricsSink(),
        traces=InMemoryTraceSink(),
        task_supervisor=TaskSupervisor(),
    )


class RuntimeRoleStateTestCase(unittest.TestCase):

    def test_all_configured_initial_roles_are_preserved_without_coordination(self) -> None:
        for configured_role in (
            "singleton",
            "sub_node",
            "standby_master",
            "active_master",
        ):
            with self.subTest(role=configured_role):
                logger = logging.Logger(f"role-{configured_role}")
                service = RuntimeService(
                    context=_context_for_role(configured_role, logger),
                )

                self.assertEqual(configured_role, service.role.role.value)
                self.assertIs(RuntimeHealth.HEALTHY, service.role.health)
                self.assertEqual(
                    {
                        RuntimeCapability.TRANSPORT: False,
                        RuntimeCapability.CLUSTER_COORDINATION: False,
                        RuntimeCapability.DELIVERY: False,
                    },
                    dict(service.role.capability_enabled),
                )

    def test_role_and_health_domains_remain_separate(self) -> None:
        self.assertEqual(
            (
                "singleton",
                "sub_node",
                "standby_master",
                "active_master",
                "transitioning",
                "draining",
            ),
            tuple(role.value for role in RuntimeRole),
        )
        self.assertEqual(
            ("healthy", "degraded", "isolated", "unavailable"),
            tuple(health.value for health in RuntimeHealth),
        )

    def test_each_deferred_capability_is_audited_and_fails_closed(self) -> None:
        logger = logging.Logger("runtime-role-audit")
        handler = _ListHandler()
        logger.addHandler(handler)
        service = RuntimeService(context=_context_for_role("active_master", logger))

        for capability in RuntimeCapability:
            with self.subTest(capability=capability.value):
                with self.assertRaises(
                    NsRuntimeFeatureDisabledError,
                ) as context:
                    service.require_capability(capability)

                self.assertEqual("RUNTIME_FEATURE_DISABLED", context.exception.code)
                self.assertEqual(
                    {
                        "component": "runtime_role_state",
                        "capability": capability.value,
                        "role": "active_master",
                        "reason": "phase_not_implemented",
                    },
                    context.exception.details,
                )

        self.assertEqual(3, len(handler.records))
        for record, capability in zip(handler.records, RuntimeCapability):
            self.assertEqual("runtime_feature_disabled", record.event)
            self.assertEqual(capability.value, record.capability)
            self.assertEqual("active_master", record.role)
            self.assertEqual("RUNTIME_FEATURE_DISABLED", record.error_code)
            self.assertNotIn("active_master_url", vars(record))

    def test_audit_logger_failure_cannot_enable_a_capability(self) -> None:
        logger = logging.Logger("runtime-role-audit-failure")
        logger.error = lambda *args, **kwargs: (_ for _ in ()).throw(  # type: ignore[method-assign]
            RuntimeError("audit failure sentinel")
        )
        state = RuntimeRoleState(configured_role="singleton", logger=logger)

        with self.assertRaises(NsRuntimeFeatureDisabledError):
            state.require_capability(RuntimeCapability.DELIVERY)

    def test_invalid_direct_role_and_capability_inputs_have_safe_details(self) -> None:
        secret_role = object()
        with self.assertRaises(NsValidationError) as role_context:
            RuntimeRoleState(
                configured_role=secret_role,
                logger=logging.Logger("invalid-role"),
            )
        self.assertNotIn("value", role_context.exception.details)
        self.assertNotIn(repr(secret_role), str(role_context.exception.details))

        state = RuntimeRoleState(
            configured_role="singleton",
            logger=logging.Logger("invalid-capability"),
        )
        with self.assertRaises(NsValidationError) as capability_context:
            state.require_capability("delivery")  # type: ignore[arg-type]
        self.assertEqual(
            "str",
            capability_context.exception.details["actual_type"],
        )


if __name__ == "__main__":
    unittest.main()
