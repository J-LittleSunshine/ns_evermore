# -*- coding: utf-8 -*-
"""Canonical, bounded and non-sensitive connection rejection responses."""

from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass
from enum import Enum

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import NsValidationError
from ns_common.identifiers import IdentifierFactory, NsIdentifierKind
from ns_common.time import Clock
from ns_runtime.protocol import (
    BUILTIN_MESSAGE_REGISTRY,
    CURRENT_PROTOCOL_SCHEMA_KEY,
    Envelope,
    MessageGroup,
    MessageTypeRegistry,
    PayloadGroup,
    ProtocolGroup,
    canonical_serialize,
)
from ns_runtime.transport import TransportSession

from .accepted import _iso_utc


REJECTED_PAYLOAD_FIELDS = frozenset({"reason", "server_time", "retryable"})


class ConnectionRejectionReason(str, Enum):
    PROTOCOL_INCOMPATIBLE = "protocol_incompatible"
    MINIMUM_VERSION_INCOMPATIBLE = "minimum_version_incompatible"
    CAPABILITY_INCOMPATIBLE = "capability_incompatible"
    IAM_DENIED = "iam_denied"
    IAM_UNAVAILABLE = "iam_unavailable"
    AUTHORITY_INVALID = "authority_invalid"
    INTERNAL_FAILURE = "internal_failure"

    @property
    def retryable(self) -> bool:
        return self is ConnectionRejectionReason.IAM_UNAVAILABLE


class ConnectionRejectedEnvelopeBuilder:
    """Build only the fixed low-cardinality P05 handshake rejection shape."""

    def __init__(
        self,
        *,
        clock: Clock,
        identifier_factory: IdentifierFactory,
        registry: MessageTypeRegistry = BUILTIN_MESSAGE_REGISTRY,
        schema_key: str = CURRENT_PROTOCOL_SCHEMA_KEY,
    ) -> None:
        if not isinstance(clock, Clock):
            _invalid("clock")
        if not isinstance(identifier_factory, IdentifierFactory):
            _invalid("identifier_factory")
        if not isinstance(registry, MessageTypeRegistry):
            _invalid("registry")
        if not isinstance(schema_key, str) or not schema_key:
            _invalid("schema_key")
        self._clock = clock
        self._identifier_factory = identifier_factory
        self._registry = registry
        self._schema_key = schema_key

    def build(
        self,
        *,
        protocol: ProtocolGroup,
        reason: ConnectionRejectionReason,
    ) -> Envelope:
        if not isinstance(protocol, ProtocolGroup):
            _invalid("protocol")
        if not isinstance(reason, ConnectionRejectionReason):
            _invalid("reason")
        now = self._clock.utc_now()
        payload = {
            "reason": reason.value,
            "server_time": _iso_utc(now),
            "retryable": reason.retryable,
        }
        if frozenset(payload) != REJECTED_PAYLOAD_FIELDS:
            _invalid("payload")
        envelope = Envelope(
            protocol=protocol,
            message=MessageGroup(
                message_id=self._identifier_factory.generate(
                    NsIdentifierKind.MESSAGE_ID,
                ),
                type="connection.rejected",
                category="connection",
                priority=0,
                created_at=_iso_utc(now),
                reliability="best_effort",
            ),
            payload=PayloadGroup(mode="inline", inline=payload),
        )
        return self._registry.validate_envelope(envelope, self._schema_key)

    def serialize(
        self,
        *,
        protocol: ProtocolGroup,
        reason: ConnectionRejectionReason,
    ) -> str:
        return canonical_serialize(
            self.build(protocol=protocol, reason=reason),
        ).decode("utf-8")


@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionRejectionSendPolicy:
    timeout_seconds: float

    def __post_init__(self) -> None:
        value = self.timeout_seconds
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) <= 0
        ):
            _invalid("timeout_seconds")


class ConnectionHandshakeRejector:
    """Best-effort bounded send; the original handshake error stays primary."""

    def __init__(
        self,
        *,
        transport_session: TransportSession,
        builder: ConnectionRejectedEnvelopeBuilder,
        clock: Clock,
        task_supervisor: TaskSupervisor,
        task_sequence: int,
        policy: ConnectionRejectionSendPolicy,
    ) -> None:
        dependencies = (
            (transport_session, TransportSession, "transport_session"),
            (builder, ConnectionRejectedEnvelopeBuilder, "builder"),
            (clock, Clock, "clock"),
            (task_supervisor, TaskSupervisor, "task_supervisor"),
            (policy, ConnectionRejectionSendPolicy, "policy"),
        )
        for value, expected, name in dependencies:
            if not isinstance(value, expected):
                _invalid(name)
        if (
            isinstance(task_sequence, bool)
            or not isinstance(task_sequence, int)
            or task_sequence < 0
        ):
            _invalid("task_sequence")
        self._transport = transport_session
        self._builder = builder
        self._clock = clock
        self._supervisor = task_supervisor
        self._task_sequence = task_sequence
        self._policy = policy

    async def send(
        self,
        *,
        protocol: ProtocolGroup,
        reason: ConnectionRejectionReason,
    ) -> bool:
        try:
            text = self._builder.serialize(protocol=protocol, reason=reason)
        except Exception:
            return False
        send_task: asyncio.Task[object] | None = None
        deadline_task: asyncio.Task[object] | None = None
        try:
            send_task = self._supervisor.create_task(
                self._transport.send(text),
                name=f"logical-rejected-{self._task_sequence}-send",
                cancel_order=20,
            )
            deadline_task = self._supervisor.create_task(
                self._clock.sleep(float(self._policy.timeout_seconds)),
                name=f"logical-rejected-{self._task_sequence}-deadline",
                cancel_order=10,
            )
            await asyncio.wait(
                (send_task, deadline_task),
                return_when=asyncio.FIRST_COMPLETED,
            )
            if deadline_task.done() or not send_task.done():
                await _cancel_and_join(send_task)
                return False
            try:
                send_task.result()
            except Exception:
                return False
            return True
        except Exception:
            return False
        finally:
            del text
            await _cancel_and_join(send_task)
            await _cancel_and_join(deadline_task)


async def _cancel_and_join(task: asyncio.Task[object] | None) -> None:
    if task is None:
        return
    if not task.done():
        task.cancel()
    await asyncio.gather(task, return_exceptions=True)


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Connection rejection dependency is invalid.",
        details={"component": "logical_connection", "field": field_name},
    )


__all__ = (
    "ConnectionHandshakeRejector",
    "ConnectionRejectedEnvelopeBuilder",
    "ConnectionRejectionReason",
    "ConnectionRejectionSendPolicy",
    "REJECTED_PAYLOAD_FIELDS",
)
