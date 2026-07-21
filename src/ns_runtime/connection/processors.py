# -*- coding: utf-8 -*-
"""P05-only immutable processor boundary for connection lifecycle messages."""

from __future__ import annotations

from abc import ABC, abstractmethod
from types import MappingProxyType
from typing import Iterable, Mapping

from ns_common.exceptions import NsRuntimeProtocolViolationError, NsStateError, NsValidationError
from ns_runtime.protocol import (
    BUILTIN_MESSAGE_REGISTRY,
    Envelope,
    MessageDirection,
    MessageTypeContract,
    MessageTypeRegistry,
)

from .drain import ConnectionDrainService
from .heartbeat import ConnectionHeartbeatService
from .index import LocalConnectionIndex
from .reauth import (
    ConnectionReauthCoordinator,
    ConnectionReauthEnvelopeHandler,
)
from .session import SessionContext
from .state import LogicalConnectionState


P05_EXECUTABLE_PROCESSOR_KEYS = frozenset({
    "connection.heartbeat",
    "connection.drain",
    "connection.reauth",
})


class ConnectionLifecycleProcessor(ABC):
    """One explicit P05 message executor, not the future P07 pipeline."""

    def __init__(self, *, contract: MessageTypeContract) -> None:
        if not isinstance(contract, MessageTypeContract):
            _invalid("contract")
        if not contract.feature_enabled:
            _invalid("contract.feature_enabled")
        if contract.direction is not MessageDirection.INBOUND:
            _invalid("contract.direction")
        if contract.processor_key not in P05_EXECUTABLE_PROCESSOR_KEYS:
            _invalid("contract.processor_key")
        self._contract = contract

    @property
    def contract(self) -> MessageTypeContract:
        return self._contract

    @abstractmethod
    async def process(self, envelope: Envelope) -> object:
        raise NotImplementedError

    def _validate_contract(self, envelope: Envelope) -> None:
        if not isinstance(envelope, Envelope):
            _invalid("envelope")
        if envelope.message.type != self._contract.message_type:
            raise NsRuntimeProtocolViolationError(
                details={
                    "component": "connection_lifecycle_processor",
                    "operation": "dispatch",
                    "reason": "processor_contract_mismatch",
                },
            )


class _CurrentSessionGuard:
    def __init__(
        self,
        *,
        session_context: SessionContext,
        connection_index: LocalConnectionIndex,
    ) -> None:
        if not isinstance(session_context, SessionContext):
            _invalid("session_context")
        if not isinstance(connection_index, LocalConnectionIndex):
            _invalid("connection_index")
        self._context = session_context
        self._index = connection_index

    async def check(
        self,
        envelope: Envelope,
        *,
        allowed_states: frozenset[LogicalConnectionState],
    ) -> None:
        if (
            envelope.protocol.major != self._context.protocol_version.major
            or envelope.protocol.minor != self._context.protocol_version.minor
            or envelope.protocol.patch != self._context.protocol_version.patch
        ):
            _protocol_error("session_protocol_mismatch")
        entry = await self._index.lookup_connection(self._context.connection_id)
        if entry is None or entry.session_context != self._context:
            _protocol_error("logical_session_not_current")
        if entry.state not in allowed_states:
            _protocol_error("logical_session_state_not_allowed")


class ConnectionHeartbeatProcessor(ConnectionLifecycleProcessor):
    def __init__(
        self,
        *,
        contract: MessageTypeContract,
        session_context: SessionContext,
        connection_index: LocalConnectionIndex,
        heartbeat_service: ConnectionHeartbeatService,
    ) -> None:
        super().__init__(contract=contract)
        if contract.message_type != "connection.heartbeat":
            _invalid("contract.message_type")
        if not isinstance(heartbeat_service, ConnectionHeartbeatService):
            _invalid("heartbeat_service")
        self._guard = _CurrentSessionGuard(
            session_context=session_context,
            connection_index=connection_index,
        )
        self._service = heartbeat_service

    async def process(self, envelope: Envelope) -> object:
        self._validate_contract(envelope)
        await self._guard.check(
            envelope,
            allowed_states=frozenset({
                LogicalConnectionState.ACTIVE,
                LogicalConnectionState.DRAINING,
            }),
        )
        return await self._service.process_envelope(envelope)


class ConnectionDrainProcessor(ConnectionLifecycleProcessor):
    def __init__(
        self,
        *,
        contract: MessageTypeContract,
        session_context: SessionContext,
        connection_index: LocalConnectionIndex,
        drain_service: ConnectionDrainService,
    ) -> None:
        super().__init__(contract=contract)
        if contract.message_type != "connection.drain":
            _invalid("contract.message_type")
        if not isinstance(drain_service, ConnectionDrainService):
            _invalid("drain_service")
        self._guard = _CurrentSessionGuard(
            session_context=session_context,
            connection_index=connection_index,
        )
        self._service = drain_service

    async def process(self, envelope: Envelope) -> object:
        self._validate_contract(envelope)
        await self._guard.check(
            envelope,
            allowed_states=frozenset({LogicalConnectionState.ACTIVE}),
        )
        return await self._service.begin()


class ConnectionReauthProcessor(ConnectionLifecycleProcessor):
    def __init__(
        self,
        *,
        contract: MessageTypeContract,
        session_context: SessionContext,
        connection_index: LocalConnectionIndex,
        envelope_handler: ConnectionReauthEnvelopeHandler,
        coordinator: ConnectionReauthCoordinator,
    ) -> None:
        super().__init__(contract=contract)
        if contract.message_type != "connection.reauth":
            _invalid("contract.message_type")
        if not isinstance(envelope_handler, ConnectionReauthEnvelopeHandler):
            _invalid("envelope_handler")
        if not isinstance(coordinator, ConnectionReauthCoordinator):
            _invalid("coordinator")
        self._guard = _CurrentSessionGuard(
            session_context=session_context,
            connection_index=connection_index,
        )
        self._handler = envelope_handler
        self._coordinator = coordinator

    async def process(self, envelope: Envelope) -> object:
        self._validate_contract(envelope)
        await self._guard.check(
            envelope,
            allowed_states=frozenset({
                LogicalConnectionState.ACTIVE,
                LogicalConnectionState.DRAINING,
            }),
        )
        parsed = self._handler.parse_envelope(envelope)
        return await self._coordinator.reauthenticate(parsed)


class ConnectionLifecycleProcessorRegistry:
    """Immutable P05 dispatch map keyed only by canonical processor_key."""

    def __init__(
        self,
        processors: Iterable[ConnectionLifecycleProcessor],
        *,
        protocol_registry: MessageTypeRegistry = BUILTIN_MESSAGE_REGISTRY,
    ) -> None:
        if not isinstance(protocol_registry, MessageTypeRegistry):
            _invalid("protocol_registry")
        try:
            values = tuple(processors)
        except TypeError:
            _invalid("processors")
        by_key: dict[str, ConnectionLifecycleProcessor] = {}
        for processor in values:
            if not isinstance(processor, ConnectionLifecycleProcessor):
                _invalid("processors")
            contract = protocol_registry.require(processor.contract.message_type)
            if contract is not processor.contract:
                _invalid("processor.contract")
            key = contract.processor_key
            if key in by_key:
                _invalid("processor_key")
            by_key[key] = processor
        if frozenset(by_key) != P05_EXECUTABLE_PROCESSOR_KEYS:
            _invalid("processor_keys")
        self._processors: Mapping[str, ConnectionLifecycleProcessor] = MappingProxyType(by_key)
        self._protocol_registry = protocol_registry

    @property
    def processor_keys(self) -> frozenset[str]:
        return frozenset(self._processors)

    def require(self, processor_key: str) -> ConnectionLifecycleProcessor:
        processor = self._processors.get(processor_key)
        if processor is None:
            raise NsStateError(
                "P05 lifecycle processor is unavailable.",
                details={
                    "component": "connection_lifecycle_processor",
                    "operation": "dispatch",
                    "reason": "processor_not_registered",
                },
            )
        return processor

    async def dispatch(self, envelope: Envelope) -> object:
        if not isinstance(envelope, Envelope):
            _invalid("envelope")
        contract = self._protocol_registry.require(envelope.message.type)
        return await self.require(contract.processor_key).process(envelope)


class ConnectionLifecycleProcessorRegistryFactory:
    """Explicit composition dependency for one immutable per-session registry."""

    def __init__(
        self,
        *,
        protocol_registry: MessageTypeRegistry = BUILTIN_MESSAGE_REGISTRY,
    ) -> None:
        if not isinstance(protocol_registry, MessageTypeRegistry):
            _invalid("protocol_registry")
        self._protocol_registry = protocol_registry

    @property
    def protocol_registry(self) -> MessageTypeRegistry:
        return self._protocol_registry

    def build(
        self,
        *,
        session_context: SessionContext,
        connection_index: LocalConnectionIndex,
        heartbeat_service: ConnectionHeartbeatService,
        drain_service: ConnectionDrainService,
        reauth_handler: ConnectionReauthEnvelopeHandler,
        reauth_coordinator: ConnectionReauthCoordinator,
    ) -> ConnectionLifecycleProcessorRegistry:
        return ConnectionLifecycleProcessorRegistry((
            ConnectionHeartbeatProcessor(
                contract=self._protocol_registry.require("connection.heartbeat"),
                session_context=session_context,
                connection_index=connection_index,
                heartbeat_service=heartbeat_service,
            ),
            ConnectionDrainProcessor(
                contract=self._protocol_registry.require("connection.drain"),
                session_context=session_context,
                connection_index=connection_index,
                drain_service=drain_service,
            ),
            ConnectionReauthProcessor(
                contract=self._protocol_registry.require("connection.reauth"),
                session_context=session_context,
                connection_index=connection_index,
                envelope_handler=reauth_handler,
                coordinator=reauth_coordinator,
            ),
        ), protocol_registry=self._protocol_registry)


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Connection lifecycle processor dependency is invalid.",
        details={
            "component": "connection_lifecycle_processor",
            "field": field_name,
        },
    )


def _protocol_error(reason: str) -> None:
    raise NsRuntimeProtocolViolationError(
        details={
            "component": "connection_lifecycle_processor",
            "operation": "session_guard",
            "reason": reason,
        },
    )


__all__ = (
    "ConnectionDrainProcessor",
    "ConnectionHeartbeatProcessor",
    "ConnectionLifecycleProcessor",
    "ConnectionLifecycleProcessorRegistry",
    "ConnectionLifecycleProcessorRegistryFactory",
    "ConnectionReauthProcessor",
    "P05_EXECUTABLE_PROCESSOR_KEYS",
)
