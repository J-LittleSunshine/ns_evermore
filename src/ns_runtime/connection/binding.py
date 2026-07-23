# -*- coding: utf-8 -*-
"""Atomic logical/transport/network-path mapping without driver objects."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime

from ns_common.exceptions import NsStateError, NsValidationError
from ns_common.identifiers import IdentifierFactory, NsIdentifierKind
from ns_runtime.transport import (
    TransportCapabilities,
    TransportCapability,
    TransportIdentity,
    TransportPathSnapshot,
    TransportSession,
)

from .session import LogicalSessionIdentity, SessionContext


@dataclass(frozen=True, slots=True, kw_only=True)
class NetworkPathBinding:
    path_id: str = field(repr=False)
    path_epoch: int
    migration_count: int
    validated_at: datetime
    local_summary: str = field(repr=False)
    peer_summary: str = field(repr=False)

    @classmethod
    def from_snapshot(cls, value: TransportPathSnapshot) -> "NetworkPathBinding":
        if not isinstance(value, TransportPathSnapshot):
            _invalid("transport_path")
        return cls(
            path_id=value.path_id,
            path_epoch=value.path_epoch,
            migration_count=value.migration_count,
            validated_at=value.validated_at,
            local_summary=value.local_summary,
            peer_summary=value.peer_summary,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class TransportSessionBinding:
    transport_type: str
    capabilities: TransportCapabilities
    transport_connection_id: str = field(repr=False)
    transport_session_id: str = field(repr=False)
    transport_stream_id: str = field(repr=False)
    path: NetworkPathBinding = field(repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.transport_type, str) or not self.transport_type:
            _invalid("transport_type")
        if not isinstance(self.capabilities, TransportCapabilities):
            _invalid("transport_capabilities")
        if not isinstance(self.path, NetworkPathBinding):
            _invalid("network_path")
        identity = TransportIdentity(
            transport_connection_id=self.transport_connection_id,
            transport_session_id=self.transport_session_id,
            transport_stream_id=self.transport_stream_id,
            path=TransportPathSnapshot(
                path_id=self.path.path_id,
                path_epoch=self.path.path_epoch,
                local_summary=self.path.local_summary,
                peer_summary=self.path.peer_summary,
                validated_at=self.path.validated_at,
                migration_count=self.path.migration_count,
            ),
        )
        del identity

    @classmethod
    def from_session(cls, session: TransportSession) -> "TransportSessionBinding":
        if not isinstance(session, TransportSession):
            _invalid("transport_session")
        identity = session.identity
        capabilities = session.capabilities
        transport_type = session.transport_type
        if not isinstance(identity, TransportIdentity):
            _invalid("transport_identity")
        if not isinstance(capabilities, TransportCapabilities):
            _invalid("transport_capabilities")
        if not isinstance(transport_type, str) or not transport_type:
            _invalid("transport_type")
        return cls(
            transport_type=transport_type,
            capabilities=capabilities,
            transport_connection_id=identity.transport_connection_id,
            transport_session_id=identity.transport_session_id,
            transport_stream_id=identity.transport_stream_id,
            path=NetworkPathBinding.from_snapshot(identity.path),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class LogicalTransportMappingSnapshot:
    session_context: SessionContext = field(repr=False)
    transport: TransportSessionBinding | None = field(repr=False)
    binding_sequence: int

    def __post_init__(self) -> None:
        if not isinstance(self.session_context, SessionContext):
            _invalid("session_context")
        if self.transport is not None and not isinstance(
            self.transport,
            TransportSessionBinding,
        ):
            _invalid("transport_binding")
        if (
            isinstance(self.binding_sequence, bool)
            or not isinstance(self.binding_sequence, int)
            or self.binding_sequence < 0
        ):
            _invalid("binding_sequence")


class LogicalSessionIdentityFactory:
    """Create P01 logical IDs independently from all P04 transport IDs."""

    def __init__(self, identifier_factory: IdentifierFactory) -> None:
        if not isinstance(identifier_factory, IdentifierFactory):
            _invalid("identifier_factory")
        self._identifier_factory = identifier_factory

    def create(self) -> LogicalSessionIdentity:
        return LogicalSessionIdentity(
            connection_id=self._identifier_factory.generate(
                NsIdentifierKind.CONNECTION_ID,
            ),
            session_id=self._identifier_factory.generate(
                NsIdentifierKind.SESSION_ID,
            ),
            connection_epoch=0,
        )

    def resume(self, previous: LogicalSessionIdentity) -> LogicalSessionIdentity:
        if not isinstance(previous, LogicalSessionIdentity):
            _invalid("previous_logical_identity")
        return LogicalSessionIdentity(
            connection_id=previous.connection_id,
            session_id=self._identifier_factory.generate(
                NsIdentifierKind.SESSION_ID,
            ),
            connection_epoch=previous.connection_epoch + 1,
        )


class LogicalConnectionTransportMap:
    """Single-owner atomic mapping; never retains a TransportSession object."""

    def __init__(
        self,
        *,
        session_context: SessionContext,
        transport_session: TransportSession,
    ) -> None:
        if not isinstance(session_context, SessionContext):
            _invalid("session_context")
        binding = TransportSessionBinding.from_session(transport_session)
        _validate_identity_separation(session_context, binding)
        self._session_context = session_context
        self._transport: TransportSessionBinding | None = binding
        self._binding_sequence = 0
        self._lock = asyncio.Lock()

    async def snapshot(self) -> LogicalTransportMappingSnapshot:
        async with self._lock:
            return self._snapshot_unlocked()

    async def update_network_path(
        self,
        transport_session: TransportSession,
    ) -> LogicalTransportMappingSnapshot:
        candidate = TransportSessionBinding.from_session(transport_session)
        async with self._lock:
            current = self._transport
            if current is None:
                _state_error("path_update_without_transport")
            assert current is not None
            if (
                candidate.transport_type != current.transport_type
                or candidate.capabilities != current.capabilities
                or candidate.transport_connection_id
                != current.transport_connection_id
                or candidate.transport_session_id != current.transport_session_id
                or candidate.transport_stream_id != current.transport_stream_id
            ):
                _state_error("path_update_changed_transport_identity")
            if candidate.path == current.path:
                return self._snapshot_unlocked()
            if not current.capabilities.supports(
                TransportCapability.CONNECTION_PATH_MIGRATION,
            ):
                _state_error("path_migration_not_supported")
            if (
                candidate.path.path_epoch <= current.path.path_epoch
                or candidate.path.migration_count <= current.path.migration_count
            ):
                _state_error("path_update_not_monotonic")
            self._transport = candidate
            self._binding_sequence += 1
            return self._snapshot_unlocked()

    async def detach_transport_session(
        self,
        *,
        transport_session_id: str,
    ) -> LogicalTransportMappingSnapshot:
        if not isinstance(transport_session_id, str) or not transport_session_id:
            _invalid("transport_session_id")
        async with self._lock:
            current = self._transport
            if current is None:
                _state_error("transport_already_detached")
            assert current is not None
            if current.transport_session_id != transport_session_id:
                _state_error("transport_session_owner_mismatch")
            self._transport = None
            self._binding_sequence += 1
            return self._snapshot_unlocked()

    async def replace_transport_session(
        self,
        *,
        session_context: SessionContext,
        transport_session: TransportSession,
    ) -> LogicalTransportMappingSnapshot:
        if not isinstance(session_context, SessionContext):
            _invalid("session_context")
        candidate = TransportSessionBinding.from_session(transport_session)
        _validate_identity_separation(session_context, candidate)
        async with self._lock:
            previous = self._session_context
            if session_context.connection_id != previous.connection_id:
                _state_error("logical_connection_changed")
            if session_context.session_id == previous.session_id:
                _state_error("logical_session_not_replaced")
            if session_context.connection_epoch != previous.connection_epoch + 1:
                _state_error("connection_epoch_not_next")
            current = self._transport
            if current is not None and (
                candidate.transport_connection_id
                == current.transport_connection_id
                or candidate.transport_session_id == current.transport_session_id
            ):
                _state_error("transport_session_not_replaced")
            self._session_context = session_context
            self._transport = candidate
            self._binding_sequence += 1
            return self._snapshot_unlocked()

    def _snapshot_unlocked(self) -> LogicalTransportMappingSnapshot:
        return LogicalTransportMappingSnapshot(
            session_context=self._session_context,
            transport=self._transport,
            binding_sequence=self._binding_sequence,
        )


def _validate_identity_separation(
    context: SessionContext,
    binding: TransportSessionBinding,
) -> None:
    logical_ids = {context.connection_id, context.session_id}
    transport_ids = {
        binding.transport_connection_id,
        binding.transport_session_id,
        binding.transport_stream_id,
        binding.path.path_id,
    }
    if logical_ids.intersection(transport_ids):
        _state_error("logical_transport_identity_collision")


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Logical transport mapping value is invalid.",
        details={"component": "logical_connection", "field": field_name},
    )


def _state_error(reason: str) -> None:
    raise NsStateError(
        "Logical transport mapping operation is invalid.",
        details={
            "component": "logical_connection",
            "operation": "transport_mapping",
            "reason": reason,
        },
    )


__all__ = (
    "LogicalConnectionTransportMap",
    "LogicalSessionIdentityFactory",
    "LogicalTransportMappingSnapshot",
    "NetworkPathBinding",
    "TransportSessionBinding",
)
