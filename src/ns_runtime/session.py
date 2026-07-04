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
        self._active_connection_ids: set[str] = set()
        self._identity_connections: dict[str, set[str]] = {}
        self._tenant_connections: dict[str, set[str]] = {}
        self._component_type_connections: dict[str, set[str]] = {}
        self._capability_connections: dict[str, set[str]] = {}
        self._session_connections: dict[str, str] = {}

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
        self._add_active_indexes(record)
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

        self._remove_active_indexes(record)
        record.mark(state, reason=reason)

    def close(self, record: RuntimeConnectionRecord, *, reason: str) -> None:
        self._remove_active_indexes(record)
        record.mark("closed", reason=reason)

    def get(self, connection_id: str) -> RuntimeConnectionRecord | None:
        return self._connections.get(connection_id)

    def get_active_record(self, connection_id: str) -> RuntimeConnectionRecord | None:
        record = self._connections.get(connection_id)
        if record is None or record.state != "active":
            return None

        return record

    def get_active_session(self, connection_id: str) -> RuntimeSessionContext | None:
        record = self.get_active_record(connection_id)
        if record is None:
            return None

        return record.session_context

    def get_by_session_id(self, session_id: str) -> RuntimeConnectionRecord | None:
        connection_id = self._session_connections.get(session_id)
        if connection_id is None:
            return None

        return self.get_active_record(connection_id)

    def list_records(self) -> tuple[RuntimeConnectionRecord, ...]:
        return tuple(self._connections[key] for key in sorted(self._connections.keys()))

    def list_active_records(self) -> tuple[RuntimeConnectionRecord, ...]:
        return self._records_by_ids(self._active_connection_ids)

    def list_by_identity(self, identity: str) -> tuple[RuntimeConnectionRecord, ...]:
        return self._records_by_ids(self._identity_connections.get(identity, set()))

    def list_by_tenant(self, tenant_id: str) -> tuple[RuntimeConnectionRecord, ...]:
        return self._records_by_ids(self._tenant_connections.get(tenant_id, set()))

    def list_by_component_type(self, component_type: str) -> tuple[RuntimeConnectionRecord, ...]:
        return self._records_by_ids(self._component_type_connections.get(component_type, set()))

    def list_by_capability(self, capability: str) -> tuple[RuntimeConnectionRecord, ...]:
        return self._records_by_ids(self._capability_connections.get(capability, set()))

    def build_health_snapshot(self) -> dict[str, object]:
        return {
            "runtime_id": self._runtime_id,
            "active_connection_count": len(self._active_connection_ids),
            "total_connection_count": len(self._connections),
            "identity_count": len(self._identity_connections),
            "tenant_count": len(self._tenant_connections),
            "component_type_count": len(self._component_type_connections),
            "capability_count": len(self._capability_connections),
            "by_tenant": self._count_index(self._tenant_connections),
            "by_component_type": self._count_index(self._component_type_connections),
            "server_time": utc_now_iso(),
        }

    def _add_active_indexes(self, record: RuntimeConnectionRecord) -> None:
        session = record.session_context
        if session is None:
            return

        self._active_connection_ids.add(record.connection_id)
        self._session_connections[session.session_id] = record.connection_id
        self._index_add(self._identity_connections, session.identity, record.connection_id)
        self._index_add(self._tenant_connections, session.tenant_id, record.connection_id)
        self._index_add(self._component_type_connections, session.component_type, record.connection_id)

        for capability in session.capabilities:
            self._index_add(self._capability_connections, capability, record.connection_id)

    def _remove_active_indexes(self, record: RuntimeConnectionRecord) -> None:
        session = record.session_context
        if session is None:
            return

        self._active_connection_ids.discard(record.connection_id)
        self._session_connections.pop(session.session_id, None)
        self._index_remove(self._identity_connections, session.identity, record.connection_id)
        self._index_remove(self._tenant_connections, session.tenant_id, record.connection_id)
        self._index_remove(self._component_type_connections, session.component_type, record.connection_id)

        for capability in session.capabilities:
            self._index_remove(self._capability_connections, capability, record.connection_id)

    def _records_by_ids(self, connection_ids: set[str]) -> tuple[RuntimeConnectionRecord, ...]:
        records: list[RuntimeConnectionRecord] = []

        for connection_id in sorted(connection_ids):
            record = self._connections.get(connection_id)
            if record is not None and record.state == "active":
                records.append(record)

        return tuple(records)

    @staticmethod
    def _index_add(index: dict[str, set[str]], key: str, connection_id: str) -> None:
        index.setdefault(key, set()).add(connection_id)

    @staticmethod
    def _index_remove(index: dict[str, set[str]], key: str, connection_id: str) -> None:
        values = index.get(key)
        if values is None:
            return

        values.discard(connection_id)
        if not values:
            index.pop(key, None)

    @staticmethod
    def _count_index(index: dict[str, set[str]]) -> dict[str, int]:
        return {
            key: len(value)
            for key, value in sorted(index.items())
        }
