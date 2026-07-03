# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass

from ns_common.logger import get_ns_logger
from ns_runtime._compat import StrEnum
from ns_runtime.processor import (
    BuiltinProcessorRegistryFactory,
    ProcessorRegistry,
)
from ns_runtime.protocol import EnvelopeProtocol


class RuntimeNodeRole(StrEnum):
    SINGLETON = "singleton"
    SUB_NODE = "sub_node"
    STANDBY_MASTER = "standby_master"
    ACTIVE_MASTER = "active_master"
    TRANSITIONING = "transitioning"
    DRAINING = "draining"


class RuntimeHealthFlag(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    ISOLATED = "isolated"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class RuntimeServiceSnapshot:
    role: RuntimeNodeRole
    health_flag: RuntimeHealthFlag
    registered_message_type_count: int
    protocol_major: int
    protocol_minor: int
    protocol_patch: int


class RuntimeService:
    def __init__(self, *, role: RuntimeNodeRole, health_flag: RuntimeHealthFlag, registry: ProcessorRegistry, envelope_protocol: EnvelopeProtocol) -> None:
        self.role: RuntimeNodeRole = role
        self.health_flag: RuntimeHealthFlag = health_flag
        self.registry: ProcessorRegistry = registry
        self.envelope_protocol: EnvelopeProtocol = envelope_protocol
        self._logger = get_ns_logger("ns_runtime.service")

    @classmethod
    def bootstrap(cls, *, role: RuntimeNodeRole = RuntimeNodeRole.SINGLETON) -> "RuntimeService":
        registry = BuiltinProcessorRegistryFactory.build()
        envelope_protocol = EnvelopeProtocol(registry=registry)

        return cls(
            role=role,
            health_flag=RuntimeHealthFlag.HEALTHY,
            registry=registry,
            envelope_protocol=envelope_protocol,
        )

    def self_check(self) -> RuntimeServiceSnapshot:
        protocol_version = self.envelope_protocol.compatibility_policy.runtime_version
        snapshot = RuntimeServiceSnapshot(
            role=self.role,
            health_flag=self.health_flag,
            registered_message_type_count=len(self.registry.values()),
            protocol_major=protocol_version.major,
            protocol_minor=protocol_version.minor,
            protocol_patch=protocol_version.patch,
        )

        self._logger.info(
            "Runtime service self check completed.",
            extra={
                "role": snapshot.role,
                "health_flag": snapshot.health_flag,
                "registered_message_type_count": snapshot.registered_message_type_count,
                "protocol_major": snapshot.protocol_major,
                "protocol_minor": snapshot.protocol_minor,
                "protocol_patch": snapshot.protocol_patch,
            },
        )

        return snapshot
