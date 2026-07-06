# -*- coding: utf-8 -*-
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import (
    datetime,
    timedelta,
    timezone
)
from typing import (
    Any,
    Literal,
    TYPE_CHECKING
)

from ns_common.exceptions import (
    NsRuntimeAckRejectedError,
    NsRuntimeDeliveryStateError,
    NsRuntimeEnvelopeSchemaError,
)
from ns_runtime.models import (
    Envelope,
    MessageReliability,
    utc_now_iso
)
from ns_runtime.routing import (
    RuntimeRouteDecision,
    RuntimeRouteTarget
)

if TYPE_CHECKING:
    from ns_runtime.outbound import RuntimeLocalWriteResult

RuntimeDeliveryState = Literal[
    "prepared",
    "queued",
    "sending",
    "ack_waiting",
    "retry_scheduled",
    "replay_requested",
    "acked",
    "dead_lettered",
    "cancelled",
    "expired",
    "transferred",
]

RuntimeDeliveryAttemptWriteStatus = Literal[
    "created",
    "sending",
    "sent_to_transport",
    "write_failed",
]


@dataclass(slots=True, kw_only=True)
class RuntimeAckRecord:
    ack_id: str
    delivery_id: str
    message_id: str
    tenant_id: str
    ack_connection_id: str
    ack_connection_epoch: int
    ack_message_id: str
    acked_at: str
    duplicate_count: int = 0
    last_seen_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ack_id": self.ack_id,
            "delivery_id": self.delivery_id,
            "message_id": self.message_id,
            "tenant_id": self.tenant_id,
            "ack_connection_id": self.ack_connection_id,
            "ack_connection_epoch": self.ack_connection_epoch,
            "ack_message_id": self.ack_message_id,
            "acked_at": self.acked_at,
            "duplicate_count": self.duplicate_count,
            "last_seen_at": self.last_seen_at,
        }


@dataclass(slots=True, kw_only=True)
class RuntimeAckResult:
    status: str
    delivery_record: RuntimeDeliveryRecord
    ack_record: RuntimeAckRecord
    duplicate: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "duplicate": self.duplicate,
            "delivery": self.delivery_record.to_dict(),
            "ack": self.ack_record.to_dict(),
        }


@dataclass(slots=True, kw_only=True)
class RuntimeDeliveryRecord:
    delivery_id: str
    summary_id: str
    root_delivery_id: str
    parent_delivery_id: str
    message_id: str
    message_type: str
    tenant_id: str
    source_connection_id: str
    target_kind: str
    target_connection_id: str
    target_connection_epoch: int
    target_identity: str
    target_component_type: str
    target_fingerprint: str
    reliability: MessageReliability
    state: RuntimeDeliveryState
    attempt_count: int
    current_attempt_id: str
    ack_timeout_ms: int
    ack_deadline_at: str
    created_at: str
    updated_at: str
    expires_at: str = ""
    last_error_code: str = ""
    last_error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "delivery_id": self.delivery_id,
            "summary_id": self.summary_id,
            "root_delivery_id": self.root_delivery_id,
            "parent_delivery_id": self.parent_delivery_id,
            "message_id": self.message_id,
            "message_type": self.message_type,
            "tenant_id": self.tenant_id,
            "source_connection_id": self.source_connection_id,
            "target_kind": self.target_kind,
            "target_connection_id": self.target_connection_id,
            "target_connection_epoch": self.target_connection_epoch,
            "target_identity": self.target_identity,
            "target_component_type": self.target_component_type,
            "target_fingerprint": self.target_fingerprint,
            "reliability": self.reliability,
            "state": self.state,
            "attempt_count": self.attempt_count,
            "current_attempt_id": self.current_attempt_id,
            "ack_timeout_ms": self.ack_timeout_ms,
            "ack_deadline_at": self.ack_deadline_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
            "last_error_code": self.last_error_code,
            "last_error_message": self.last_error_message,
        }


@dataclass(slots=True, kw_only=True)
class RuntimeDeliveryAttempt:
    attempt_id: str
    delivery_id: str
    attempt: int
    target_connection_id: str
    target_connection_epoch: int
    write_status: RuntimeDeliveryAttemptWriteStatus
    started_at: str
    completed_at: str = ""
    write_error_code: str = ""
    write_error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt_id": self.attempt_id,
            "delivery_id": self.delivery_id,
            "attempt": self.attempt,
            "target_connection_id": self.target_connection_id,
            "target_connection_epoch": self.target_connection_epoch,
            "write_status": self.write_status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "write_error_code": self.write_error_code,
            "write_error_message": self.write_error_message,
        }


class RuntimeDeliveryRegistry:
    def __init__(self, *, default_ack_timeout_ms: int = 30000) -> None:
        self._default_ack_timeout_ms = default_ack_timeout_ms
        self._records: dict[str, RuntimeDeliveryRecord] = {}
        self._attempts: dict[str, RuntimeDeliveryAttempt] = {}
        self._attempt_ids_by_delivery: dict[str, list[str]] = {}
        self._acks: dict[str, RuntimeAckRecord] = {}
        self._ack_id_by_delivery: dict[str, str] = {}

    def create_prepared_record(self, *, decision: RuntimeRouteDecision, envelope: Envelope, target: RuntimeRouteTarget) -> RuntimeDeliveryRecord:
        delivery_id = str(uuid.uuid4())
        now = utc_now_iso()
        summary_id = f"summary:{envelope.message_id}"
        target_fingerprint = self._build_target_fingerprint(target)

        record = RuntimeDeliveryRecord(
            delivery_id=delivery_id,
            summary_id=summary_id,
            root_delivery_id=delivery_id,
            parent_delivery_id="",
            message_id=envelope.message_id,
            message_type=envelope.message_type,
            tenant_id=decision.source_tenant_id,
            source_connection_id=decision.source_connection_id,
            target_kind=decision.target_kind,
            target_connection_id=target.connection_id,
            target_connection_epoch=target.connection_epoch,
            target_identity=target.identity,
            target_component_type=target.component_type,
            target_fingerprint=target_fingerprint,
            reliability=envelope.reliability,
            state="prepared",
            attempt_count=0,
            current_attempt_id="",
            ack_timeout_ms=self._default_ack_timeout_ms,
            ack_deadline_at="",
            created_at=now,
            updated_at=now,
            expires_at=self._read_expires_at(envelope),
        )
        self._records[delivery_id] = record
        self._attempt_ids_by_delivery[delivery_id] = []
        return record

    def start_sending(self, *, record: RuntimeDeliveryRecord) -> RuntimeDeliveryAttempt:
        if record.state not in {"prepared", "queued", "retry_scheduled"}:
            raise NsRuntimeDeliveryStateError(
                "Delivery cannot enter sending from current state.",
                details={
                    "delivery_id": record.delivery_id,
                    "state": record.state,
                },
            )

        attempt = RuntimeDeliveryAttempt(
            attempt_id=str(uuid.uuid4()),
            delivery_id=record.delivery_id,
            attempt=record.attempt_count + 1,
            target_connection_id=record.target_connection_id,
            target_connection_epoch=record.target_connection_epoch,
            write_status="sending",
            started_at=utc_now_iso(),
        )

        record.state = "sending"
        record.attempt_count = attempt.attempt
        record.current_attempt_id = attempt.attempt_id
        record.updated_at = utc_now_iso()

        self._attempts[attempt.attempt_id] = attempt
        self._attempt_ids_by_delivery.setdefault(record.delivery_id, []).append(attempt.attempt_id)
        return attempt

    def mark_sent_to_transport(self, *, record: RuntimeDeliveryRecord, attempt: RuntimeDeliveryAttempt, write_result: "RuntimeLocalWriteResult") -> None:
        self._ensure_current_attempt(record, attempt)

        attempt.write_status = "sent_to_transport"
        attempt.completed_at = utc_now_iso()

        record.state = "ack_waiting"
        record.ack_deadline_at = self._compute_ack_deadline(record.ack_timeout_ms)
        record.updated_at = utc_now_iso()
        record.last_error_code = ""
        record.last_error_message = ""

    def mark_write_failed(self, *, record: RuntimeDeliveryRecord, attempt: RuntimeDeliveryAttempt, exc: Exception) -> None:
        self._ensure_current_attempt(record, attempt)

        attempt.write_status = "write_failed"
        attempt.completed_at = utc_now_iso()
        attempt.write_error_code = exc.__class__.__name__
        attempt.write_error_message = str(exc)

        record.state = "retry_scheduled"
        record.updated_at = utc_now_iso()
        record.last_error_code = exc.__class__.__name__
        record.last_error_message = str(exc)

    def mark_acked(self, *, envelope: Envelope, session_connection_id: str, session_connection_epoch: int, session_tenant_id: str) -> RuntimeAckResult:
        delivery_id = self._read_required_delivery_id(envelope)
        record = self._records.get(delivery_id)
        if record is None:
            raise NsRuntimeAckRejectedError(
                "ACK references unknown delivery.",
                details={
                    "delivery_id": delivery_id,
                    "ack_message_id": envelope.message_id,
                },
            )

        self._validate_ack_source(
            record=record,
            session_connection_id=session_connection_id,
            session_connection_epoch=session_connection_epoch,
            session_tenant_id=session_tenant_id,
        )

        existing_ack_id = self._ack_id_by_delivery.get(delivery_id)
        if existing_ack_id is not None:
            ack_record = self._acks[existing_ack_id]
            ack_record.duplicate_count += 1
            ack_record.last_seen_at = utc_now_iso()
            return RuntimeAckResult(
                status="duplicate_ack",
                delivery_record=record,
                ack_record=ack_record,
                duplicate=True,
            )

        if record.state not in {"sending", "ack_waiting", "retry_scheduled"}:
            raise NsRuntimeAckRejectedError(
                "ACK is not allowed from current delivery state.",
                details={
                    "delivery_id": delivery_id,
                    "state": record.state,
                },
            )

        now = utc_now_iso()
        ack_record = RuntimeAckRecord(
            ack_id=str(uuid.uuid4()),
            delivery_id=record.delivery_id,
            message_id=record.message_id,
            tenant_id=record.tenant_id,
            ack_connection_id=session_connection_id,
            ack_connection_epoch=session_connection_epoch,
            ack_message_id=envelope.message_id,
            acked_at=now,
            last_seen_at=now,
        )

        record.state = "acked"
        record.updated_at = now
        record.last_error_code = ""
        record.last_error_message = ""

        self._acks[ack_record.ack_id] = ack_record
        self._ack_id_by_delivery[record.delivery_id] = ack_record.ack_id

        return RuntimeAckResult(
            status="acked",
            delivery_record=record,
            ack_record=ack_record,
        )

    def get_ack_for_delivery(self, delivery_id: str) -> RuntimeAckRecord | None:
        ack_id = self._ack_id_by_delivery.get(delivery_id)
        if ack_id is None:
            return None

        return self._acks.get(ack_id)

    def list_acks(self) -> tuple[RuntimeAckRecord, ...]:
        return tuple(
            self._acks[key]
            for key in sorted(self._acks.keys())
        )

    def inject_delivery_group(self, *, envelope: Envelope, record: RuntimeDeliveryRecord, attempt: RuntimeDeliveryAttempt) -> dict[str, Any]:
        data = envelope.to_dict()
        data["delivery"] = {
            "delivery_id": record.delivery_id,
            "summary_id": record.summary_id,
            "root_delivery_id": record.root_delivery_id,
            "attempt": attempt.attempt,
            "ack_timeout_ms": record.ack_timeout_ms,
            "replay_epoch": 0,
        }
        return data

    def get_record(self, delivery_id: str) -> RuntimeDeliveryRecord | None:
        return self._records.get(delivery_id)

    def get_attempt(self, attempt_id: str) -> RuntimeDeliveryAttempt | None:
        return self._attempts.get(attempt_id)

    def list_records(self) -> tuple[RuntimeDeliveryRecord, ...]:
        return tuple(
            self._records[key]
            for key in sorted(self._records.keys())
        )

    def list_attempts_for_delivery(self, delivery_id: str) -> tuple[RuntimeDeliveryAttempt, ...]:
        return tuple(
            self._attempts[attempt_id]
            for attempt_id in self._attempt_ids_by_delivery.get(delivery_id, [])
        )

    def build_delivery_snapshot(self) -> dict[str, Any]:
        by_state: dict[str, int] = {}
        for record in self._records.values():
            by_state[record.state] = by_state.get(record.state, 0) + 1

        return {
            "delivery_count": len(self._records),
            "attempt_count": len(self._attempts),
            "ack_count": len(self._acks),
            "by_state": {
                key: by_state[key]
                for key in sorted(by_state.keys())
            },
            "server_time": utc_now_iso(),
        }

    @staticmethod
    def _build_target_fingerprint(target: RuntimeRouteTarget) -> str:
        return "|".join(
            (
                target.tenant_id,
                target.kind,
                target.connection_id,
                target.identity,
                target.component_type,
                ",".join(sorted(target.capabilities)),
            )
        )

    @staticmethod
    def _read_expires_at(envelope: Envelope) -> str:
        value = envelope.raw.get("message", {}).get("expires_at", "")
        if not isinstance(value, str):
            return ""
        return value

    @staticmethod
    def _read_required_delivery_id(envelope: Envelope) -> str:
        delivery = envelope.raw.get("delivery")
        if not isinstance(delivery, dict):
            raise NsRuntimeEnvelopeSchemaError("delivery group must be an object.")

        delivery_id = delivery.get("delivery_id")
        if not isinstance(delivery_id, str) or not delivery_id.strip():
            raise NsRuntimeEnvelopeSchemaError("delivery.delivery_id must be a non-empty string.")

        return delivery_id.strip()

    @staticmethod
    def _validate_ack_source(*, record: RuntimeDeliveryRecord, session_connection_id: str, session_connection_epoch: int, session_tenant_id: str) -> None:
        if record.tenant_id != session_tenant_id:
            raise NsRuntimeAckRejectedError(
                "ACK tenant does not match delivery tenant.",
                details={
                    "delivery_id": record.delivery_id,
                    "delivery_tenant_id": record.tenant_id,
                    "ack_tenant_id": session_tenant_id,
                },
            )

        if record.target_connection_id != session_connection_id:
            raise NsRuntimeAckRejectedError(
                "ACK connection does not match delivery target connection.",
                details={
                    "delivery_id": record.delivery_id,
                    "target_connection_id": record.target_connection_id,
                    "ack_connection_id": session_connection_id,
                },
            )

        if record.target_connection_epoch != session_connection_epoch:
            raise NsRuntimeAckRejectedError(
                "ACK connection epoch does not match delivery target epoch.",
                details={
                    "delivery_id": record.delivery_id,
                    "target_connection_epoch": record.target_connection_epoch,
                    "ack_connection_epoch": session_connection_epoch,
                },
            )

    @staticmethod
    def _compute_ack_deadline(ack_timeout_ms: int) -> str:
        deadline = datetime.now(timezone.utc) + timedelta(milliseconds=ack_timeout_ms)
        return deadline.isoformat(timespec="milliseconds")

    @staticmethod
    def _ensure_current_attempt(record: RuntimeDeliveryRecord, attempt: RuntimeDeliveryAttempt) -> None:
        if record.current_attempt_id != attempt.attempt_id:
            raise NsRuntimeDeliveryStateError(
                "Delivery attempt is not current.",
                details={
                    "delivery_id": record.delivery_id,
                    "current_attempt_id": record.current_attempt_id,
                    "attempt_id": attempt.attempt_id,
                },
            )
