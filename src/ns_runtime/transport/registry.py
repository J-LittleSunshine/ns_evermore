# -*- coding: utf-8 -*-
"""Explicit adapter registry; registration never starts network resources."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import (
    NsRuntimeTransportDisabledError,
    NsValidationError,
)

from .contracts import TransportAdapter
from .identity import TransportIdentityFactory
from .models import TransportCapabilities
from .metrics import TransportMetricsRecorder
from .websocket_tcp import (
    WEBSOCKET_TCP_CAPABILITIES,
    WEBSOCKET_TCP_TRANSPORT_TYPE,
    WebSocketTcpAdapter,
    WebSocketTcpAdapterOptions,
)


TRANSPORT_ADAPTER_NAMES = (
    "websocket_tcp",
    "websocket_http3",
    "webtransport_http3",
    "quic_native",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class TransportAdapterBuildContext:
    websocket_tcp_options: WebSocketTcpAdapterOptions
    task_supervisor: TaskSupervisor
    identity_factory: TransportIdentityFactory
    metrics: TransportMetricsRecorder

    def __post_init__(self) -> None:
        if not isinstance(self.websocket_tcp_options, WebSocketTcpAdapterOptions):
            _invalid("websocket_tcp_options")
        if not isinstance(self.task_supervisor, TaskSupervisor):
            _invalid("task_supervisor")
        if not isinstance(self.identity_factory, TransportIdentityFactory):
            _invalid("identity_factory")
        if not isinstance(self.metrics, TransportMetricsRecorder):
            _invalid("metrics")


AdapterFactory = Callable[[TransportAdapterBuildContext], TransportAdapter]


@dataclass(frozen=True, slots=True, kw_only=True)
class TransportAdapterRegistration:
    transport_type: str
    available: bool
    capabilities: TransportCapabilities
    factory: AdapterFactory | None = None

    def __post_init__(self) -> None:
        if self.transport_type not in TRANSPORT_ADAPTER_NAMES:
            _invalid("transport_type")
        if not isinstance(self.available, bool):
            _invalid("available")
        if not isinstance(self.capabilities, TransportCapabilities):
            _invalid("capabilities")
        if self.available:
            if not callable(self.factory):
                _invalid("factory")
        elif self.factory is not None or self.capabilities.supported:
            _invalid("unavailable_registration")


class TransportAdapterRegistry:
    """Immutable build registry for available and reserved adapter names."""

    def __init__(self, registrations: Iterable[TransportAdapterRegistration]) -> None:
        try:
            items = tuple(registrations)
        except (TypeError, ValueError):
            _invalid("registrations")
        registrations_by_name: dict[str, TransportAdapterRegistration] = {}
        for registration in items:
            if not isinstance(registration, TransportAdapterRegistration):
                _invalid("registration")
            if registration.transport_type in registrations_by_name:
                _invalid("duplicate_registration")
            registrations_by_name[registration.transport_type] = registration
        if tuple(registrations_by_name) != TRANSPORT_ADAPTER_NAMES:
            _invalid("registration_set")
        self._registrations: Mapping[str, TransportAdapterRegistration] = (
            MappingProxyType(registrations_by_name)
        )

    @classmethod
    def default(cls) -> "TransportAdapterRegistry":
        unavailable = TransportCapabilities()
        return cls((
            TransportAdapterRegistration(
                transport_type=WEBSOCKET_TCP_TRANSPORT_TYPE,
                available=True,
                capabilities=WEBSOCKET_TCP_CAPABILITIES,
                factory=_build_websocket_tcp,
            ),
            TransportAdapterRegistration(
                transport_type="websocket_http3",
                available=False,
                capabilities=unavailable,
            ),
            TransportAdapterRegistration(
                transport_type="webtransport_http3",
                available=False,
                capabilities=unavailable,
            ),
            TransportAdapterRegistration(
                transport_type="quic_native",
                available=False,
                capabilities=unavailable,
            ),
        ))

    @property
    def registrations(self) -> Mapping[str, TransportAdapterRegistration]:
        return self._registrations

    @property
    def available_adapters(self) -> tuple[str, ...]:
        return tuple(
            name
            for name, registration in self._registrations.items()
            if registration.available
        )

    def create_enabled(
        self,
        enabled_adapters: Iterable[str],
        *,
        context: TransportAdapterBuildContext,
    ) -> tuple[TransportAdapter, ...]:
        if not isinstance(context, TransportAdapterBuildContext):
            _invalid("context")
        try:
            enabled = tuple(enabled_adapters)
        except (TypeError, ValueError):
            _invalid("enabled_adapters")
        if len(set(enabled)) != len(enabled):
            _invalid("enabled_adapters")

        adapters: list[TransportAdapter] = []
        for name in enabled:
            registration = self._registrations.get(name)
            if registration is None or not registration.available:
                raise NsRuntimeTransportDisabledError(
                    "Configured runtime transport is unavailable.",
                    details={
                        "component": "transport_registry",
                        "operation": "create",
                        "reason": "adapter_unavailable",
                    },
                )
            assert registration.factory is not None
            adapter = registration.factory(context)
            if not isinstance(adapter, TransportAdapter):
                raise NsValidationError(
                    "Transport adapter factory returned an invalid object.",
                    details={
                        "component": "transport_registry",
                        "field": "factory",
                    },
                )
            adapters.append(adapter)
        return tuple(adapters)


def _build_websocket_tcp(context: TransportAdapterBuildContext) -> TransportAdapter:
    return WebSocketTcpAdapter(
        options=context.websocket_tcp_options,
        task_supervisor=context.task_supervisor,
        identity_factory=context.identity_factory,
        metrics=context.metrics,
    )


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Transport adapter registry value is invalid.",
        details={"component": "transport_registry", "field": field_name},
    )


__all__ = (
    "TRANSPORT_ADAPTER_NAMES",
    "TransportAdapterBuildContext",
    "TransportAdapterRegistration",
    "TransportAdapterRegistry",
)
