# -*- coding: utf-8 -*-
"""P03-compliant connection.accepted construction and activation fencing."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

from ns_common.exceptions import NsStateError, NsValidationError
from ns_common.identifiers import (
    IdentifierFactory,
    NsIdentifierKind,
    validate_identifier,
)
from ns_common.time import Clock
from ns_runtime.protocol import (
    BUILTIN_MESSAGE_REGISTRY,
    Envelope,
    MessageGroup,
    PayloadGroup,
    ProtocolGroup,
    WIRE_CODEC_JSON_V1,
    canonical_serialize,
)
from ns_runtime.roles import RuntimeRole
from ns_runtime.transport import TransportSession

from .index import LocalConnectionIndex
from .session import SessionContext
from .state import LogicalConnectionCloseReason, LogicalConnectionState


ACCEPTED_PAYLOAD_FIELDS = frozenset({
    "connection_id",
    "session_id",
    "protocol_version",
    "heartbeat",
    "session_expires_at",
    "server_time",
    "runtime_id",
    "role",
})
ACCEPTED_HEARTBEAT_FIELDS = frozenset({
    "interval_seconds",
    "timeout_seconds",
})


@dataclass(frozen=True, slots=True, kw_only=True)
class AcceptedHeartbeatPolicy:
    interval_seconds: int
    timeout_seconds: int

    def __post_init__(self) -> None:
        for name in ("interval_seconds", "timeout_seconds"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                _invalid(name)
        if self.timeout_seconds <= self.interval_seconds:
            _invalid("timeout_seconds")


class ConnectionAcceptedEnvelopeBuilder:
    def __init__(
        self,
        *,
        clock: Clock,
        identifier_factory: IdentifierFactory,
        runtime_id: str,
        role: RuntimeRole,
        heartbeat_policy: AcceptedHeartbeatPolicy,
    ) -> None:
        if not isinstance(clock, Clock):
            _invalid("clock")
        if not isinstance(identifier_factory, IdentifierFactory):
            _invalid("identifier_factory")
        validate_identifier(runtime_id, expected_kind=NsIdentifierKind.RUNTIME_ID)
        if not isinstance(role, RuntimeRole):
            _invalid("role")
        if not isinstance(heartbeat_policy, AcceptedHeartbeatPolicy):
            _invalid("heartbeat_policy")
        self._clock = clock
        self._identifier_factory = identifier_factory
        self._runtime_id = runtime_id
        self._role = role
        self._heartbeat_policy = heartbeat_policy

    def build(self, context: SessionContext) -> Envelope:
        if not isinstance(context, SessionContext):
            _invalid("session_context")
        if context.established_state is not LogicalConnectionState.AUTHENTICATED:
            _state_error("authenticated_context_required")
        if context.wire_codec != WIRE_CODEC_JSON_V1:
            _state_error("negotiated_codec_not_supported")
        now = self._clock.utc_now()
        payload_value = {
            "connection_id": context.connection_id,
            "session_id": context.session_id,
            "protocol_version": str(context.protocol_version),
            "heartbeat": {
                "interval_seconds": self._heartbeat_policy.interval_seconds,
                "timeout_seconds": self._heartbeat_policy.timeout_seconds,
            },
            "session_expires_at": _iso_utc(context.session_expires_at),
            "server_time": _iso_utc(now),
            "runtime_id": self._runtime_id,
            "role": self._role.value,
        }
        _validate_payload_whitelist(payload_value)
        envelope = Envelope(
            protocol=ProtocolGroup(
                major=context.protocol_version.major,
                minor=context.protocol_version.minor,
                patch=context.protocol_version.patch,
            ),
            message=MessageGroup(
                message_id=self._identifier_factory.generate(
                    NsIdentifierKind.MESSAGE_ID,
                ),
                type="connection.accepted",
                category="connection",
                priority=0,
                created_at=_iso_utc(now),
                reliability="best_effort",
            ),
            payload=PayloadGroup(mode="inline", inline=payload_value),
        )
        return BUILTIN_MESSAGE_REGISTRY.validate_envelope(
            envelope,
            context.protocol_schema_key,
        )

    def serialize(self, context: SessionContext) -> str:
        return canonical_serialize(self.build(context)).decode("utf-8")


class ConnectionAdmissionActivator:
    """Send accepted first; only its completion permits index activation."""

    def __init__(
        self,
        *,
        connection_index: LocalConnectionIndex,
        transport_session: TransportSession,
        envelope_builder: ConnectionAcceptedEnvelopeBuilder,
    ) -> None:
        if not isinstance(connection_index, LocalConnectionIndex):
            _invalid("connection_index")
        if not isinstance(transport_session, TransportSession):
            _invalid("transport_session")
        if not isinstance(envelope_builder, ConnectionAcceptedEnvelopeBuilder):
            _invalid("envelope_builder")
        self._connection_index = connection_index
        self._transport_session = transport_session
        self._envelope_builder = envelope_builder
        self._lock = asyncio.Lock()
        self._claimed = False

    async def activate(self, context: SessionContext) -> None:
        if not isinstance(context, SessionContext):
            _invalid("session_context")
        async with self._lock:
            if self._claimed:
                _state_error("activation_already_attempted")
            self._claimed = True
        try:
            entry = await self._connection_index.lookup_connection(
                context.connection_id,
            )
            if entry is None or entry.session_context != context:
                _state_error("authenticated_session_not_indexed")
            if entry.state is not LogicalConnectionState.AUTHENTICATED:
                _state_error("authenticated_state_required")
            text = self._envelope_builder.serialize(context)
            try:
                await self._transport_session.send(text)
            finally:
                del text
            await self._connection_index.transition(
                context.connection_id,
                LogicalConnectionState.ACTIVE,
            )
        except asyncio.CancelledError:
            await self._rollback(
                context.connection_id,
                LogicalConnectionCloseReason.SHUTDOWN,
            )
            raise
        except Exception:
            await self._rollback(
                context.connection_id,
                LogicalConnectionCloseReason.SEND_FAILED,
            )
            raise

    async def retry_cleanup(self, connection_id: str) -> bool:
        entry = await self._connection_index.lookup_connection(connection_id)
        if entry is None:
            return True
        if entry.state is not LogicalConnectionState.CLOSING:
            _state_error("closing_state_required")
        try:
            await self._transport_session.close()
        except Exception:
            return False
        await self._connection_index.transition(
            connection_id,
            LogicalConnectionState.CLOSED,
        )
        return True

    async def _rollback(
        self,
        connection_id: str,
        reason: LogicalConnectionCloseReason,
    ) -> None:
        entry = await self._connection_index.lookup_connection(connection_id)
        if entry is None:
            return
        if entry.state is not LogicalConnectionState.CLOSING:
            try:
                await self._connection_index.transition(
                    connection_id,
                    LogicalConnectionState.CLOSING,
                    close_reason=reason,
                )
            except Exception:
                return
        await self.retry_cleanup(connection_id)


def _validate_payload_whitelist(value: dict[str, object]) -> None:
    if frozenset(value) != ACCEPTED_PAYLOAD_FIELDS:
        _state_error("accepted_payload_field_mismatch")
    heartbeat = value.get("heartbeat")
    if not isinstance(heartbeat, dict) or frozenset(heartbeat) != ACCEPTED_HEARTBEAT_FIELDS:
        _state_error("accepted_heartbeat_field_mismatch")


def _iso_utc(value: datetime) -> str:
    if not isinstance(value, datetime):
        _invalid("datetime")
    try:
        normalized = value.astimezone(timezone.utc)
        offset = value.utcoffset()
    except Exception:
        offset = None
    if offset is None:
        _invalid("datetime")
    return normalized.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Connection accepted dependency is invalid.",
        details={"component": "logical_connection", "field": field_name},
    )


def _state_error(reason: str) -> None:
    raise NsStateError(
        "Connection accepted operation is invalid.",
        details={
            "component": "logical_connection",
            "operation": "connection_accepted",
            "reason": reason,
        },
    )


__all__ = (
    "ACCEPTED_HEARTBEAT_FIELDS",
    "ACCEPTED_PAYLOAD_FIELDS",
    "AcceptedHeartbeatPolicy",
    "ConnectionAcceptedEnvelopeBuilder",
    "ConnectionAdmissionActivator",
)
