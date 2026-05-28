# -*- coding: utf-8 -*-
from __future__ import annotations

from ns_common.protocol import RuntimeServiceState
from ns_runtime.brokers.base import RuntimeBroker
from ns_runtime.brokers.memory import MemoryBroker
from ns_runtime.config import RuntimeConfig
from ns_runtime.coordinator.master import MasterCoordinator
from ns_runtime.endpoints.registry import EndpointRegistry
from ns_runtime.extensions.registry import RuntimeExtensionRegistry
from ns_runtime.routing.router import RuntimePacketRouter


class RuntimeService:
    def __init__(
        self,
        config: RuntimeConfig | None = None,
        broker: RuntimeBroker | None = None,
        endpoint_registry: EndpointRegistry | None = None,
        router: RuntimePacketRouter | None = None,
        extension_registry: RuntimeExtensionRegistry | None = None,
        master_coordinator: MasterCoordinator | None = None,
    ) -> None:
        self.config = config or RuntimeConfig.create_default()
        self.broker = broker or MemoryBroker()
        self.endpoint_registry = endpoint_registry or EndpointRegistry()
        self.router = router or RuntimePacketRouter()
        self.extension_registry = extension_registry or RuntimeExtensionRegistry()
        self.master_coordinator = master_coordinator or MasterCoordinator(
            instance_id=self.config.instance_id,
            fixed_master_instance_id=self.config.fixed_master_instance_id,
        )
        self._state = RuntimeServiceState.CREATED

    @property
    def is_running(self) -> bool:
        return self._state == RuntimeServiceState.RUNNING

    @property
    def state(self) -> RuntimeServiceState:
        return self._state

    @property
    def is_master(self) -> bool:
        return self.master_coordinator.is_master()

    def start(self) -> None:
        if self._state == RuntimeServiceState.RUNNING:
            return

        self._state = RuntimeServiceState.STARTING
        self.broker.start()
        self._state = RuntimeServiceState.RUNNING

    def stop(self) -> None:
        if self._state in {RuntimeServiceState.STOPPED, RuntimeServiceState.CREATED}:
            self._state = RuntimeServiceState.STOPPED
            return

        self._state = RuntimeServiceState.STOPPING
        self.broker.stop()
        self._state = RuntimeServiceState.STOPPED

