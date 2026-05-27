# -*- coding: utf-8 -*-
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from ns_runtime.endpoints import RuntimeEndpoint
from ns_runtime.packets import RuntimeEndpointStatus, RuntimeEndpointType
from ns_runtime.tasks import RuntimeTask


class RuntimeTaskDispatchStrategy(ABC):
    @abstractmethod
    def select_endpoint(
        self,
        task: RuntimeTask,
        endpoints: Iterable[RuntimeEndpoint],
    ) -> RuntimeEndpoint | None:
        raise NotImplementedError


class CapabilityMatchDispatchStrategy(RuntimeTaskDispatchStrategy):
    def select_endpoint(
        self,
        task: RuntimeTask,
        endpoints: Iterable[RuntimeEndpoint],
    ) -> RuntimeEndpoint | None:
        # 第一版 capability_match 策略：仅按在线 EXECUTOR 与能力覆盖匹配，不做负载、优先级或分组调度。
        required = set(task.required_capabilities)

        for endpoint in endpoints:
            if endpoint.endpoint_type != RuntimeEndpointType.EXECUTOR:
                continue
            if endpoint.status != RuntimeEndpointStatus.ONLINE:
                continue

            if not required:
                return endpoint

            capabilities = set(endpoint.capabilities)
            if required.issubset(capabilities):
                return endpoint

        return None


