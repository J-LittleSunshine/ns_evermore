# -*- coding: utf-8 -*-
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import (
    Literal,
    TYPE_CHECKING
)

from ns_common.exceptions import NsRuntimeDeliveryStateError
from ns_runtime.models import (
    RuntimeSessionContext,
    utc_now_iso
)

if TYPE_CHECKING:
    from ns_runtime.auth import RuntimeAuthResult

RuntimeConnectionState = Literal[
    "accepted",
    "handshaking",
    "authenticated",
    "active",
    "draining",
    "closing",
    "closed",
    "rejected",
    "auth_failed",
    "protocol_failed",
    "timeout_closed",
]


@dataclass(slots=True, kw_only=True)
class RuntimeConnectionRecord:
    runtime_id: str
    connection_id: str
    session_id: str
    connection_epoch: int
    state: RuntimeConnectionState
    remote_address: str
    created_at: str
    updated_at: str
    session_context: RuntimeSessionContext | None = None
    reject_reason: str = ""
    close_reason: str = ""

    def mark(self, state: RuntimeConnectionState, *, reason: str = "") -> None:
        self.state = state
        self.updated_at = utc_now_iso()

        if state in {"rejected", "auth_failed", "protocol_failed"}:
            self.reject_reason = reason

        if state in {"closing", "closed", "timeout_closed"}:
            self.close_reason = reason


class RuntimeSessionRegistry:
    def __init__(self, *, runtime_id: str) -> None:
        self._runtime_id = runtime_id
        self._connections: dict[str, RuntimeConnectionRecord] = {}

    def create_handshaking(self, *, remote_address: str) -> RuntimeConnectionRecord:
        connection_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())

        record = RuntimeConnectionRecord(
            runtime_id=self._runtime_id,
            connection_id=connection_id,
            session_id=session_id,
            connection_epoch=0,
            state="handshaking",
            remote_address=remote_address,
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
        )
        self._connections[connection_id] = record
        return record

    def activate(self, record: RuntimeConnectionRecord, auth_result: "RuntimeAuthResult") -> RuntimeSessionContext:
        if record.state != "handshaking":
            raise NsRuntimeDeliveryStateError(
                "Only handshaking connection can be activated.",
                details={
                    "connection_id": record.connection_id,
                    "state": record.state,
                },
            )

        if not auth_result.accepted:
            raise NsRuntimeDeliveryStateError(
                "Rejected authentication result cannot activate session.",
                details={
                    "connection_id": record.connection_id,
                    "reject_code": auth_result.reject_code,
                },
            )

        session = RuntimeSessionContext(
            runtime_id=record.runtime_id,
            connection_id=record.connection_id,
            session_id=record.session_id,
            identity=auth_result.identity,
            tenant_id=auth_result.tenant_id,
            component_type=auth_result.component_type,
            capabilities=auth_result.capabilities,
            auth_snapshot_id=auth_result.snapshot_id,
            auth_issued_at=auth_result.issued_at,
            auth_expires_at=auth_result.expires_at,
            connection_epoch=record.connection_epoch,
            role=auth_result.role,
            iam_mode=auth_result.iam_mode,
        )

        record.session_context = session
        record.mark("active")
        return session

    def reject(self, record: RuntimeConnectionRecord, *, state: RuntimeConnectionState, reason: str) -> None:
        if state not in {"rejected", "auth_failed", "protocol_failed", "timeout_closed"}:
            raise NsRuntimeDeliveryStateError(
                "Invalid rejected connection state.",
                details={
                    "connection_id": record.connection_id,
                    "state": state,
                },
            )

        record.mark(state, reason=reason)

    def close(self, record: RuntimeConnectionRecord, *, reason: str) -> None:
        record.mark("closed", reason=reason)

    def get(self, connection_id: str) -> RuntimeConnectionRecord | None:
        return self._connections.get(connection_id)

    def list_records(self) -> tuple[RuntimeConnectionRecord, ...]:
        return tuple(self._connections[key] for key in sorted(self._connections.keys()))
