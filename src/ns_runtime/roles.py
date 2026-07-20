# -*- coding: utf-8 -*-
"""Runtime role state and fail-closed gates for deferred capabilities."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from ns_common.exceptions import (
    NsRuntimeFeatureDisabledError,
    NsValidationError,
)


class RuntimeRole(str, Enum):
    """Operational and transitional runtime roles from the design boundary."""

    SINGLETON = "singleton"
    SUB_NODE = "sub_node"
    STANDBY_MASTER = "standby_master"
    ACTIVE_MASTER = "active_master"
    TRANSITIONING = "transitioning"
    DRAINING = "draining"


class RuntimeHealth(str, Enum):
    """Health is orthogonal to role and must not be encoded as a role value."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    ISOLATED = "isolated"
    UNAVAILABLE = "unavailable"


class RuntimeCapability(str, Enum):
    """Capabilities that P02 must keep explicitly unavailable."""

    TRANSPORT = "transport"
    CLUSTER_COORDINATION = "cluster_coordination"
    DELIVERY = "delivery"


_INITIAL_ROLES: Mapping[str, RuntimeRole] = MappingProxyType({
    role.value: role
    for role in (
        RuntimeRole.SINGLETON,
        RuntimeRole.SUB_NODE,
        RuntimeRole.STANDBY_MASTER,
        RuntimeRole.ACTIVE_MASTER,
    )
})

_CAPABILITY_ENABLED: Mapping[RuntimeCapability, bool] = MappingProxyType({
    RuntimeCapability.TRANSPORT: False,
    RuntimeCapability.CLUSTER_COORDINATION: False,
    RuntimeCapability.DELIVERY: False,
})


@dataclass(frozen=True, slots=True)
class RuntimeRoleSnapshot:
    """Immutable, non-authoritative view of the current local role state."""

    role: RuntimeRole
    health: RuntimeHealth
    capability_enabled: Mapping[RuntimeCapability, bool]


class RuntimeRoleState:
    """Hold the configured initial role without claiming coordination rights.

    Role transitions, leader leases, fencing and health transitions belong to
    later cluster work packages.  P02 deliberately exposes no mutation API.
    """

    def __init__(self, *, configured_role: object, logger: logging.Logger) -> None:
        if not isinstance(logger, logging.Logger):
            raise NsValidationError(
                "Runtime role state logger is invalid.",
                details={
                    "component": "runtime_role_state",
                    "dependency": "logger",
                    "expected_type": "Logger",
                    "actual_type": type(logger).__name__,
                },
            )
        role = (
            _INITIAL_ROLES.get(configured_role)
            if isinstance(configured_role, str)
            else None
        )
        if role is None:
            raise NsValidationError(
                "Runtime initial role is invalid.",
                details={
                    "component": "runtime_role_state",
                    "field": "runtime.cluster.role",
                    "actual_type": type(configured_role).__name__,
                    "allowed_values": sorted(_INITIAL_ROLES),
                },
            )
        self._role = role
        self._health = RuntimeHealth.HEALTHY
        self._logger = logger

    @property
    def role(self) -> RuntimeRole:
        return self._role

    @property
    def health(self) -> RuntimeHealth:
        return self._health

    @property
    def snapshot(self) -> RuntimeRoleSnapshot:
        return RuntimeRoleSnapshot(
            role=self._role,
            health=self._health,
            capability_enabled=_CAPABILITY_ENABLED,
        )

    def require_capability(self, capability: RuntimeCapability) -> None:
        if not isinstance(capability, RuntimeCapability):
            raise NsValidationError(
                "Runtime capability query is invalid.",
                details={
                    "component": "runtime_role_state",
                    "field": "capability",
                    "expected_type": "RuntimeCapability",
                    "actual_type": type(capability).__name__,
                },
            )
        if _CAPABILITY_ENABLED[capability]:
            return

        audit_fields = {
            "event": "runtime_feature_disabled",
            "component": "runtime_role_state",
            "capability": capability.value,
            "role": self._role.value,
            "error_code": NsRuntimeFeatureDisabledError.code,
            "reason": "phase_not_implemented",
        }
        try:
            self._logger.error(
                "Runtime capability request rejected.",
                extra=audit_fields,
            )
        except Exception:
            # Logging is best-effort until the strong audit path is introduced;
            # an audit sink failure must never turn a disabled feature into success.
            pass
        raise NsRuntimeFeatureDisabledError(
            details={
                "component": "runtime_role_state",
                "capability": capability.value,
                "role": self._role.value,
                "reason": "phase_not_implemented",
            },
        )


__all__ = [
    "RuntimeCapability",
    "RuntimeHealth",
    "RuntimeRole",
    "RuntimeRoleSnapshot",
    "RuntimeRoleState",
]
