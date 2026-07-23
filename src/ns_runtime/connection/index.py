# -*- coding: utf-8 -*-
"""Single-process atomic indexes for P05 logical connections."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from ns_common.exceptions import NsStateError, NsValidationError

from .session import SessionContext
from .state import (
    LogicalConnectionCloseReason,
    LogicalConnectionState,
    LogicalConnectionStateMachine,
    LogicalConnectionStateSnapshot,
)


class ConnectionRoutingEligibility(str, Enum):
    ELIGIBLE = "eligible"
    RECONNECT_GRACE = "reconnect_grace"
    DRAINING = "draining"
    AUTHORITY_SUSPENDED = "authority_suspended"
    SESSION_EXPIRY_SUSPENDED = "session_expiry_suspended"


@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionIndexEntrySnapshot:
    session_context: SessionContext = field(repr=False)
    state: LogicalConnectionState
    active_target_eligible: bool
    routing_eligibility: ConnectionRoutingEligibility | None

    def __post_init__(self) -> None:
        if not isinstance(self.session_context, SessionContext):
            _invalid("session_context")
        if not isinstance(self.state, LogicalConnectionState):
            _invalid("state")
        if not isinstance(self.active_target_eligible, bool):
            _invalid("active_target_eligible")
        if self.routing_eligibility is not None and not isinstance(
            self.routing_eligibility,
            ConnectionRoutingEligibility,
        ):
            _invalid("routing_eligibility")
        if self.active_target_eligible and self.state is not LogicalConnectionState.ACTIVE:
            _invalid("active_target_state")
        if self.active_target_eligible != (
            self.routing_eligibility is ConnectionRoutingEligibility.ELIGIBLE
        ):
            _invalid("routing_eligibility_active_mismatch")
        if (
            self.routing_eligibility is ConnectionRoutingEligibility.DRAINING
            and self.state is not LogicalConnectionState.DRAINING
        ):
            _invalid("routing_eligibility_draining_state")


@dataclass(frozen=True, slots=True, kw_only=True)
class LocalConnectionIndexSnapshot:
    by_connection_id: Mapping[str, ConnectionIndexEntrySnapshot] = field(repr=False)
    by_session_id: Mapping[str, str] = field(repr=False)
    by_identity: Mapping[str, frozenset[str]] = field(repr=False)
    by_tenant: Mapping[str, frozenset[str]] = field(repr=False)
    by_component_type: Mapping[str, frozenset[str]] = field(repr=False)
    by_capability: Mapping[str, frozenset[str]] = field(repr=False)
    active_target_connection_ids: frozenset[str] = field(repr=False)
    mutation_sequence: int


@dataclass(slots=True)
class _IndexedConnection:
    context: SessionContext
    state_machine: LogicalConnectionStateMachine
    active_target_eligible: bool = False
    routing_eligibility: ConnectionRoutingEligibility | None = None


@dataclass(frozen=True, slots=True)
class _BuiltIndexes:
    by_session_id: Mapping[str, str]
    by_identity: Mapping[str, frozenset[str]]
    by_tenant: Mapping[str, frozenset[str]]
    by_component_type: Mapping[str, frozenset[str]]
    by_capability: Mapping[str, frozenset[str]]
    active_target_connection_ids: frozenset[str]


class LocalConnectionIndex:
    """The sole local authority for index mutation; no global registry exists."""

    def __init__(self) -> None:
        self._entries: dict[str, _IndexedConnection] = {}
        self._indexes = _build_indexes(self._entries)
        self._mutation_sequence = 0
        self._lock = asyncio.Lock()

    async def add_authenticated(
        self,
        *,
        session_context: SessionContext,
        state_machine: LogicalConnectionStateMachine,
    ) -> LocalConnectionIndexSnapshot:
        _validate_owned_entry(session_context, state_machine)
        async with self._lock:
            connection_id = session_context.connection_id
            if connection_id in self._entries:
                _state_error("duplicate_connection_id")
            if session_context.session_id in self._indexes.by_session_id:
                _state_error("duplicate_session_id")
            entries = dict(self._entries)
            entries[connection_id] = _IndexedConnection(
                context=session_context,
                state_machine=state_machine,
            )
            self._commit(entries)
            return self._snapshot_unlocked()

    async def transition(
        self,
        connection_id: str,
        requested_state: LogicalConnectionState,
        *,
        close_reason: LogicalConnectionCloseReason | None = None,
    ) -> LogicalConnectionStateSnapshot:
        _validate_connection_id_query(connection_id)
        if not isinstance(requested_state, LogicalConnectionState):
            _invalid("requested_state")
        async with self._lock:
            entry = self._require_entry(connection_id)
            state_snapshot = await entry.state_machine.transition(
                requested_state,
                close_reason=close_reason,
            )
            entries = dict(self._entries)
            if requested_state is LogicalConnectionState.CLOSED:
                del entries[connection_id]
            else:
                entries[connection_id] = _IndexedConnection(
                    context=entry.context,
                    state_machine=entry.state_machine,
                    active_target_eligible=(
                        requested_state is LogicalConnectionState.ACTIVE
                    ),
                    routing_eligibility=(
                        ConnectionRoutingEligibility.ELIGIBLE
                        if requested_state is LogicalConnectionState.ACTIVE
                        else ConnectionRoutingEligibility.DRAINING
                        if requested_state is LogicalConnectionState.DRAINING
                        else None
                    ),
                )
            self._commit(entries)
            return state_snapshot

    async def suspend_active_target(
        self,
        connection_id: str,
        *,
        reason: ConnectionRoutingEligibility,
    ) -> LocalConnectionIndexSnapshot:
        if reason not in {
            ConnectionRoutingEligibility.RECONNECT_GRACE,
            ConnectionRoutingEligibility.AUTHORITY_SUSPENDED,
            ConnectionRoutingEligibility.SESSION_EXPIRY_SUSPENDED,
        }:
            _invalid("routing_eligibility_suspend_reason")
        return await self._set_target_eligibility(
            connection_id,
            eligibility=reason,
        )

    async def restore_active_target(
        self,
        connection_id: str,
    ) -> LocalConnectionIndexSnapshot:
        return await self._set_target_eligibility(
            connection_id,
            eligibility=ConnectionRoutingEligibility.ELIGIBLE,
        )

    async def replace_session_context(
        self,
        session_context: SessionContext,
    ) -> LocalConnectionIndexSnapshot:
        if not isinstance(session_context, SessionContext):
            _invalid("session_context")
        async with self._lock:
            connection_id = session_context.connection_id
            entry = self._require_entry(connection_id)
            previous = entry.context
            if session_context.session_id == previous.session_id:
                _state_error("logical_session_not_replaced")
            if session_context.connection_epoch != previous.connection_epoch + 1:
                _state_error("connection_epoch_not_next")
            owner = self._indexes.by_session_id.get(session_context.session_id)
            if owner is not None and owner != connection_id:
                _state_error("duplicate_session_id")
            entries = dict(self._entries)
            entries[connection_id] = _IndexedConnection(
                context=session_context,
                state_machine=entry.state_machine,
                active_target_eligible=False,
                routing_eligibility=None,
            )
            self._commit(entries)
            return self._snapshot_unlocked()

    async def replace_authority_context(
        self,
        session_context: SessionContext,
        *,
        expected_session_context: SessionContext | None = None,
        allowed_states: frozenset[LogicalConnectionState] | None = None,
    ) -> LocalConnectionIndexSnapshot:
        if not isinstance(session_context, SessionContext):
            _invalid("session_context")
        if expected_session_context is not None and not isinstance(
            expected_session_context,
            SessionContext,
        ):
            _invalid("expected_session_context")
        if allowed_states is not None and (
            not isinstance(allowed_states, frozenset)
            or not allowed_states
            or any(
                not isinstance(state, LogicalConnectionState)
                for state in allowed_states
            )
        ):
            _invalid("allowed_states")
        async with self._lock:
            entry = self._require_entry(session_context.connection_id)
            previous = entry.context
            if (
                expected_session_context is not None
                and previous != expected_session_context
            ):
                _state_error("authority_context_fenced")
            if (
                allowed_states is not None
                and entry.state_machine.state not in allowed_states
            ):
                _state_error("authority_context_state_fenced")
            if (
                session_context.session_id != previous.session_id
                or session_context.connection_epoch != previous.connection_epoch
            ):
                _state_error("logical_identity_changed")
            entries = dict(self._entries)
            entries[session_context.connection_id] = _IndexedConnection(
                context=session_context,
                state_machine=entry.state_machine,
                active_target_eligible=entry.active_target_eligible,
                routing_eligibility=entry.routing_eligibility,
            )
            self._commit(entries)
            return self._snapshot_unlocked()

    async def lookup_connection(
        self,
        connection_id: str,
    ) -> ConnectionIndexEntrySnapshot | None:
        _validate_connection_id_query(connection_id)
        async with self._lock:
            entry = self._entries.get(connection_id)
            return _entry_snapshot(entry) if entry is not None else None

    async def lookup_session(
        self,
        session_id: str,
    ) -> ConnectionIndexEntrySnapshot | None:
        if not isinstance(session_id, str) or not session_id:
            _invalid("session_id")
        async with self._lock:
            connection_id = self._indexes.by_session_id.get(session_id)
            if connection_id is None:
                return None
            return _entry_snapshot(self._entries[connection_id])

    async def connections_for_identity(
        self,
        identity: str,
    ) -> tuple[ConnectionIndexEntrySnapshot, ...]:
        return await self._query_secondary(self._indexes.by_identity, identity)

    async def connections_for_tenant(
        self,
        tenant_id: str,
    ) -> tuple[ConnectionIndexEntrySnapshot, ...]:
        return await self._query_secondary(self._indexes.by_tenant, tenant_id)

    async def connections_for_component_type(
        self,
        component_type: str,
    ) -> tuple[ConnectionIndexEntrySnapshot, ...]:
        return await self._query_secondary(
            self._indexes.by_component_type,
            component_type,
        )

    async def connections_for_capability(
        self,
        capability: str,
    ) -> tuple[ConnectionIndexEntrySnapshot, ...]:
        return await self._query_secondary(self._indexes.by_capability, capability)

    async def active_targets(self) -> tuple[ConnectionIndexEntrySnapshot, ...]:
        async with self._lock:
            return tuple(
                _entry_snapshot(self._entries[connection_id])
                for connection_id in sorted(
                    self._indexes.active_target_connection_ids,
                )
            )

    async def snapshot(self) -> LocalConnectionIndexSnapshot:
        async with self._lock:
            return self._snapshot_unlocked()

    async def _set_target_eligibility(
        self,
        connection_id: str,
        *,
        eligibility: ConnectionRoutingEligibility,
    ) -> LocalConnectionIndexSnapshot:
        _validate_connection_id_query(connection_id)
        async with self._lock:
            entry = self._require_entry(connection_id)
            if entry.state_machine.state is not LogicalConnectionState.ACTIVE:
                _state_error("active_state_required")
            eligible = eligibility is ConnectionRoutingEligibility.ELIGIBLE
            if (
                not eligible
                and entry.routing_eligibility in {
                    ConnectionRoutingEligibility.RECONNECT_GRACE,
                    ConnectionRoutingEligibility.AUTHORITY_SUSPENDED,
                    ConnectionRoutingEligibility.SESSION_EXPIRY_SUSPENDED,
                }
            ):
                # Suspension classification is first-reason-wins.  A later
                # lifecycle action may close or explicitly restore the entry,
                # but cannot rewrite the reason observed by Router snapshots.
                return self._snapshot_unlocked()
            if entry.routing_eligibility is eligibility:
                return self._snapshot_unlocked()
            entries = dict(self._entries)
            entries[connection_id] = _IndexedConnection(
                context=entry.context,
                state_machine=entry.state_machine,
                active_target_eligible=eligible,
                routing_eligibility=eligibility,
            )
            self._commit(entries)
            return self._snapshot_unlocked()

    async def _query_secondary(
        self,
        index: Mapping[str, frozenset[str]],
        key: str,
    ) -> tuple[ConnectionIndexEntrySnapshot, ...]:
        if not isinstance(key, str) or not key:
            _invalid("index_query")
        async with self._lock:
            return tuple(
                _entry_snapshot(self._entries[connection_id])
                for connection_id in sorted(index.get(key, frozenset()))
            )

    def _require_entry(self, connection_id: str) -> _IndexedConnection:
        entry = self._entries.get(connection_id)
        if entry is None:
            _state_error("connection_not_indexed")
        return entry

    def _commit(self, entries: dict[str, _IndexedConnection]) -> None:
        indexes = _build_indexes(entries)
        self._entries = entries
        self._indexes = indexes
        self._mutation_sequence += 1

    def _snapshot_unlocked(self) -> LocalConnectionIndexSnapshot:
        return LocalConnectionIndexSnapshot(
            by_connection_id=MappingProxyType({
                connection_id: _entry_snapshot(entry)
                for connection_id, entry in self._entries.items()
            }),
            by_session_id=self._indexes.by_session_id,
            by_identity=self._indexes.by_identity,
            by_tenant=self._indexes.by_tenant,
            by_component_type=self._indexes.by_component_type,
            by_capability=self._indexes.by_capability,
            active_target_connection_ids=(
                self._indexes.active_target_connection_ids
            ),
            mutation_sequence=self._mutation_sequence,
        )


def _build_indexes(entries: Mapping[str, _IndexedConnection]) -> _BuiltIndexes:
    by_session_id: dict[str, str] = {}
    by_identity: dict[str, set[str]] = {}
    by_tenant: dict[str, set[str]] = {}
    by_component_type: dict[str, set[str]] = {}
    by_capability: dict[str, set[str]] = {}
    active_targets: set[str] = set()
    for connection_id, entry in entries.items():
        context = entry.context
        if context.connection_id != connection_id:
            _state_error("connection_index_key_mismatch")
        if context.session_id in by_session_id:
            _state_error("duplicate_session_id")
        by_session_id[context.session_id] = connection_id
        _add_secondary(by_identity, context.identity, connection_id)
        _add_secondary(by_tenant, context.tenant_id, connection_id)
        _add_secondary(by_component_type, context.component_type, connection_id)
        for capability in context.capabilities:
            _add_secondary(by_capability, capability, connection_id)
        if entry.active_target_eligible:
            if entry.state_machine.state is not LogicalConnectionState.ACTIVE:
                _state_error("active_target_state_inconsistent")
            active_targets.add(connection_id)
        if entry.active_target_eligible != (
            entry.routing_eligibility is ConnectionRoutingEligibility.ELIGIBLE
        ):
            _state_error("routing_eligibility_inconsistent")
    return _BuiltIndexes(
        by_session_id=MappingProxyType(by_session_id),
        by_identity=_freeze_secondary(by_identity),
        by_tenant=_freeze_secondary(by_tenant),
        by_component_type=_freeze_secondary(by_component_type),
        by_capability=_freeze_secondary(by_capability),
        active_target_connection_ids=frozenset(active_targets),
    )


def _add_secondary(index: dict[str, set[str]], key: str, connection_id: str) -> None:
    index.setdefault(key, set()).add(connection_id)


def _freeze_secondary(
    index: Mapping[str, set[str]],
) -> Mapping[str, frozenset[str]]:
    return MappingProxyType({
        key: frozenset(connection_ids)
        for key, connection_ids in index.items()
    })


def _entry_snapshot(entry: _IndexedConnection) -> ConnectionIndexEntrySnapshot:
    return ConnectionIndexEntrySnapshot(
        session_context=entry.context,
        state=entry.state_machine.state,
        active_target_eligible=entry.active_target_eligible,
        routing_eligibility=entry.routing_eligibility,
    )


def _validate_owned_entry(
    context: SessionContext,
    machine: LogicalConnectionStateMachine,
) -> None:
    if not isinstance(context, SessionContext):
        _invalid("session_context")
    if not isinstance(machine, LogicalConnectionStateMachine):
        _invalid("state_machine")
    if (
        context.established_state is not LogicalConnectionState.AUTHENTICATED
        or machine.state is not LogicalConnectionState.AUTHENTICATED
    ):
        _state_error("authenticated_state_required")


def _validate_connection_id_query(connection_id: str) -> None:
    if not isinstance(connection_id, str) or not connection_id:
        _invalid("connection_id")


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Local connection index value is invalid.",
        details={"component": "logical_connection_index", "field": field_name},
    )


def _state_error(reason: str) -> None:
    raise NsStateError(
        "Local connection index operation is invalid.",
        details={
            "component": "logical_connection_index",
            "operation": "index_mutation",
            "reason": reason,
        },
    )


__all__ = (
    "ConnectionRoutingEligibility",
    "ConnectionIndexEntrySnapshot",
    "LocalConnectionIndex",
    "LocalConnectionIndexSnapshot",
)
