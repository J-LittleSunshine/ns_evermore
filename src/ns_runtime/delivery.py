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
    NsRuntimeDeferRejectedError,
    NsRuntimeDeliveryStateError,
    NsRuntimeEnvelopeSchemaError,
    NsRuntimeNackRejectedError,
    RUNTIME_NACK_REASON_ERROR_CODES,
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
class RuntimeNackRecord:
    nack_id: str
    delivery_id: str
    message_id: str
    tenant_id: str
    nack_connection_id: str
    nack_connection_epoch: int
    nack_message_id: str
    reason: str
    reason_error_code: str
    retryable: bool
    nacked_at: str
    duplicate_count: int = 0
    last_seen_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "nack_id": self.nack_id,
            "delivery_id": self.delivery_id,
            "message_id": self.message_id,
            "tenant_id": self.tenant_id,
            "nack_connection_id": self.nack_connection_id,
            "nack_connection_epoch": self.nack_connection_epoch,
            "nack_message_id": self.nack_message_id,
            "reason": self.reason,
            "reason_error_code": self.reason_error_code,
            "retryable": self.retryable,
            "nacked_at": self.nacked_at,
            "duplicate_count": self.duplicate_count,
            "last_seen_at": self.last_seen_at,
        }


@dataclass(slots=True, kw_only=True)
class RuntimeNackResult:
    status: str
    delivery_record: RuntimeDeliveryRecord
    nack_record: RuntimeNackRecord
    duplicate: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "duplicate": self.duplicate,
            "delivery": self.delivery_record.to_dict(),
            "nack": self.nack_record.to_dict(),
        }


@dataclass(slots=True, kw_only=True)
class RuntimeDeferRecord:
    defer_id: str
    delivery_id: str
    message_id: str
    tenant_id: str
    defer_connection_id: str
    defer_connection_epoch: int
    defer_message_id: str
    defer_ms: int
    defer_sequence: int
    previous_ack_deadline_at: str
    new_ack_deadline_at: str
    deferred_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "defer_id": self.defer_id,
            "delivery_id": self.delivery_id,
            "message_id": self.message_id,
            "tenant_id": self.tenant_id,
            "defer_connection_id": self.defer_connection_id,
            "defer_connection_epoch": self.defer_connection_epoch,
            "defer_message_id": self.defer_message_id,
            "defer_ms": self.defer_ms,
            "defer_sequence": self.defer_sequence,
            "previous_ack_deadline_at": self.previous_ack_deadline_at,
            "new_ack_deadline_at": self.new_ack_deadline_at,
            "deferred_at": self.deferred_at,
        }


@dataclass(slots=True, kw_only=True)
class RuntimeDeferResult:
    status: str
    delivery_record: RuntimeDeliveryRecord
    defer_record: RuntimeDeferRecord
    total_defer_ms: int
    defer_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "delivery": self.delivery_record.to_dict(),
            "defer": self.defer_record.to_dict(),
            "total_defer_ms": self.total_defer_ms,
            "defer_count": self.defer_count,
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
    def __init__(self, *, default_ack_timeout_ms: int = 30000, max_defer_count: int = 3, max_single_defer_ms: int = 30000, max_total_defer_ms: int = 90000) -> None:
        self._default_ack_timeout_ms = default_ack_timeout_ms
        self._records: dict[str, RuntimeDeliveryRecord] = {}
        self._attempts: dict[str, RuntimeDeliveryAttempt] = {}
        self._attempt_ids_by_delivery: dict[str, list[str]] = {}
        self._acks: dict[str, RuntimeAckRecord] = {}
        self._ack_id_by_delivery: dict[str, str] = {}
        self._nacks: dict[str, RuntimeNackRecord] = {}
        self._nack_id_by_delivery: dict[str, str] = {}
        self._max_defer_count = max_defer_count
        self._max_single_defer_ms = max_single_defer_ms
        self._max_total_defer_ms = max_total_defer_ms
        self._defers: dict[str, RuntimeDeferRecord] = {}
        self._defer_ids_by_delivery: dict[str, list[str]] = {}

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

    def mark_nacked(self, *, envelope: Envelope, session_connection_id: str, session_connection_epoch: int, session_tenant_id: str) -> RuntimeNackResult:
        delivery_id = self._read_required_delivery_id(envelope)
        reason = self._read_required_nack_reason(envelope)
        reason_error_code = self._resolve_nack_reason_error_code(reason)
        retryable = self._is_retryable_nack_reason(reason)

        record = self._records.get(delivery_id)
        if record is None:
            raise NsRuntimeNackRejectedError(
                "NACK references unknown delivery.",
                details={
                    "delivery_id": delivery_id,
                    "nack_message_id": envelope.message_id,
                    "reason": reason,
                },
            )

        self._validate_nack_source(
            record=record,
            session_connection_id=session_connection_id,
            session_connection_epoch=session_connection_epoch,
            session_tenant_id=session_tenant_id,
        )

        existing_nack_id = self._nack_id_by_delivery.get(delivery_id)
        if existing_nack_id is not None:
            nack_record = self._nacks[existing_nack_id]
            nack_record.duplicate_count += 1
            nack_record.last_seen_at = utc_now_iso()
            return RuntimeNackResult(
                status="duplicate_nack",
                delivery_record=record,
                nack_record=nack_record,
                duplicate=True,
            )

        if record.state not in {"sending", "ack_waiting", "retry_scheduled"}:
            raise NsRuntimeNackRejectedError(
                "NACK is not allowed from current delivery state.",
                details={
                    "delivery_id": delivery_id,
                    "state": record.state,
                    "reason": reason,
                },
            )

        now = utc_now_iso()
        nack_record = RuntimeNackRecord(
            nack_id=str(uuid.uuid4()),
            delivery_id=record.delivery_id,
            message_id=record.message_id,
            tenant_id=record.tenant_id,
            nack_connection_id=session_connection_id,
            nack_connection_epoch=session_connection_epoch,
            nack_message_id=envelope.message_id,
            reason=reason,
            reason_error_code=reason_error_code,
            retryable=retryable,
            nacked_at=now,
            last_seen_at=now,
        )

        if retryable:
            record.state = "retry_scheduled"
            status = "nacked_retry_scheduled"
        else:
            record.state = "dead_lettered"
            status = "nacked_dead_lettered"

        record.updated_at = now
        record.last_error_code = reason_error_code
        record.last_error_message = reason

        self._nacks[nack_record.nack_id] = nack_record
        self._nack_id_by_delivery[record.delivery_id] = nack_record.nack_id

        return RuntimeNackResult(
            status=status,
            delivery_record=record,
            nack_record=nack_record,
        )

    def mark_deferred(self, *, envelope: Envelope, session_connection_id: str, session_connection_epoch: int, session_tenant_id: str) -> RuntimeDeferResult:
        delivery_id = self._read_required_delivery_id(envelope)
        defer_ms = self._read_required_defer_ms(envelope)

        record = self._records.get(delivery_id)
        if record is None:
            raise NsRuntimeDeferRejectedError(
                "Defer references unknown delivery.",
                details={
                    "delivery_id": delivery_id,
                    "defer_message_id": envelope.message_id,
                    "defer_ms": defer_ms,
                },
            )

        self._validate_defer_source(
            record=record,
            session_connection_id=session_connection_id,
            session_connection_epoch=session_connection_epoch,
            session_tenant_id=session_tenant_id,
        )

        if record.state not in {"sending", "ack_waiting", "retry_scheduled"}:
            raise NsRuntimeDeferRejectedError(
                "Defer is not allowed from current delivery state.",
                details={
                    "delivery_id": delivery_id,
                    "state": record.state,
                    "defer_ms": defer_ms,
                },
            )

        self._ensure_defer_budget(
            record=record,
            requested_defer_ms=defer_ms,
        )

        now = utc_now_iso()
        previous_deadline = record.ack_deadline_at
        new_deadline = self._extend_ack_deadline(
            record=record,
            defer_ms=defer_ms,
        )
        defer_sequence = self._next_defer_sequence(record.delivery_id)

        defer_record = RuntimeDeferRecord(
            defer_id=str(uuid.uuid4()),
            delivery_id=record.delivery_id,
            message_id=record.message_id,
            tenant_id=record.tenant_id,
            defer_connection_id=session_connection_id,
            defer_connection_epoch=session_connection_epoch,
            defer_message_id=envelope.message_id,
            defer_ms=defer_ms,
            defer_sequence=defer_sequence,
            previous_ack_deadline_at=previous_deadline,
            new_ack_deadline_at=new_deadline,
            deferred_at=now,
        )

        record.state = "ack_waiting"
        record.ack_deadline_at = new_deadline
        record.updated_at = now
        record.last_error_code = ""
        record.last_error_message = ""

        self._defers[defer_record.defer_id] = defer_record
        self._defer_ids_by_delivery.setdefault(record.delivery_id, []).append(defer_record.defer_id)

        return RuntimeDeferResult(
            status="deferred",
            delivery_record=record,
            defer_record=defer_record,
            total_defer_ms=self._compute_total_defer_ms(record.delivery_id),
            defer_count=len(self._defer_ids_by_delivery.get(record.delivery_id, [])),
        )

    def list_defers_for_delivery(self, delivery_id: str) -> tuple[RuntimeDeferRecord, ...]:
        return tuple(
            self._defers[defer_id]
            for defer_id in self._defer_ids_by_delivery.get(delivery_id, [])
        )

    def list_defers(self) -> tuple[RuntimeDeferRecord, ...]:
        return tuple(
            self._defers[key]
            for key in sorted(self._defers.keys())
        )

    def get_nack_for_delivery(self, delivery_id: str) -> RuntimeNackRecord | None:
        nack_id = self._nack_id_by_delivery.get(delivery_id)
        if nack_id is None:
            return None

        return self._nacks.get(nack_id)

    def list_nacks(self) -> tuple[RuntimeNackRecord, ...]:
        return tuple(
            self._nacks[key]
            for key in sorted(self._nacks.keys())
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
            "nack_count": len(self._nacks),
            "defer_count": len(self._defers),
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
    def _read_required_nack_reason(envelope: Envelope) -> str:
        payload = envelope.raw.get("payload")
        if not isinstance(payload, dict):
            raise NsRuntimeEnvelopeSchemaError("delivery.nack must contain payload group.")

        inline = payload.get("inline")
        if not isinstance(inline, dict):
            raise NsRuntimeEnvelopeSchemaError("delivery.nack payload.inline must be an object.")

        reason = inline.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise NsRuntimeEnvelopeSchemaError("delivery.nack payload.inline.reason must be a non-empty string.")

        normalized = reason.strip()
        allowed_reasons = RuntimeDeliveryRegistry._nack_reason_error_code_map()
        if normalized not in allowed_reasons:
            raise NsRuntimeNackRejectedError(
                "NACK reason is not supported.",
                details={
                    "reason": normalized,
                    "allowed_reasons": sorted(allowed_reasons.keys()),
                },
            )

        return normalized

    @staticmethod
    def _read_required_defer_ms(envelope: Envelope) -> int:
        payload = envelope.raw.get("payload")
        if not isinstance(payload, dict):
            raise NsRuntimeEnvelopeSchemaError("delivery.defer must contain payload group.")

        inline = payload.get("inline")
        if not isinstance(inline, dict):
            raise NsRuntimeEnvelopeSchemaError("delivery.defer payload.inline must be an object.")

        defer_ms = inline.get("defer_ms")
        if isinstance(defer_ms, bool) or not isinstance(defer_ms, int):
            raise NsRuntimeEnvelopeSchemaError("delivery.defer payload.inline.defer_ms must be an integer.")

        if defer_ms <= 0:
            raise NsRuntimeDeferRejectedError(
                "Defer duration must be positive.",
                details={
                    "defer_ms": defer_ms,
                },
            )

        return defer_ms

    @staticmethod
    def _resolve_nack_reason_error_code(reason: str) -> str:
        return RuntimeDeliveryRegistry._nack_reason_error_code_map()[reason]

    @staticmethod
    def _nack_reason_error_code_map() -> dict[str, str]:
        values = {
            reason: error_code
            for reason, error_code in RUNTIME_NACK_REASON_ERROR_CODES
        }
        values.setdefault("invalid_payload", "RUNTIME_ENVELOPE_SCHEMA_ERROR")
        return values

    @staticmethod
    def _is_retryable_nack_reason(reason: str) -> bool:
        return reason in {
            "target_overloaded",
            "temporarily_unavailable",
            "queue_full",
            "dependency_unavailable",
            "target_draining",
            "node_degraded",
        }

    @staticmethod
    def _validate_nack_source(*, record: RuntimeDeliveryRecord, session_connection_id: str, session_connection_epoch: int, session_tenant_id: str) -> None:
        if record.tenant_id != session_tenant_id:
            raise NsRuntimeNackRejectedError(
                "NACK tenant does not match delivery tenant.",
                details={
                    "delivery_id": record.delivery_id,
                    "delivery_tenant_id": record.tenant_id,
                    "nack_tenant_id": session_tenant_id,
                },
            )

        if record.target_connection_id != session_connection_id:
            raise NsRuntimeNackRejectedError(
                "NACK connection does not match delivery target connection.",
                details={
                    "delivery_id": record.delivery_id,
                    "target_connection_id": record.target_connection_id,
                    "nack_connection_id": session_connection_id,
                },
            )

        if record.target_connection_epoch != session_connection_epoch:
            raise NsRuntimeNackRejectedError(
                "NACK connection epoch does not match delivery target epoch.",
                details={
                    "delivery_id": record.delivery_id,
                    "target_connection_epoch": record.target_connection_epoch,
                    "nack_connection_epoch": session_connection_epoch,
                },
            )

    @staticmethod
    def _validate_defer_source(*, record: RuntimeDeliveryRecord, session_connection_id: str, session_connection_epoch: int, session_tenant_id: str) -> None:
        if record.tenant_id != session_tenant_id:
            raise NsRuntimeDeferRejectedError(
                "Defer tenant does not match delivery tenant.",
                details={
                    "delivery_id": record.delivery_id,
                    "delivery_tenant_id": record.tenant_id,
                    "defer_tenant_id": session_tenant_id,
                },
            )

        if record.target_connection_id != session_connection_id:
            raise NsRuntimeDeferRejectedError(
                "Defer connection does not match delivery target connection.",
                details={
                    "delivery_id": record.delivery_id,
                    "target_connection_id": record.target_connection_id,
                    "defer_connection_id": session_connection_id,
                },
            )

        if record.target_connection_epoch != session_connection_epoch:
            raise NsRuntimeDeferRejectedError(
                "Defer connection epoch does not match delivery target epoch.",
                details={
                    "delivery_id": record.delivery_id,
                    "target_connection_epoch": record.target_connection_epoch,
                    "defer_connection_epoch": session_connection_epoch,
                },
            )

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

    def _ensure_defer_budget(self, *, record: RuntimeDeliveryRecord, requested_defer_ms: int) -> None:
        current_count = len(self._defer_ids_by_delivery.get(record.delivery_id, []))
        if current_count >= self._max_defer_count:
            raise NsRuntimeDeferRejectedError(
                "Defer budget count is exhausted.",
                details={
                    "delivery_id": record.delivery_id,
                    "current_count": current_count,
                    "max_defer_count": self._max_defer_count,
                },
            )

        if requested_defer_ms > self._max_single_defer_ms:
            raise NsRuntimeDeferRejectedError(
                "Single defer duration exceeds policy limit.",
                details={
                    "delivery_id": record.delivery_id,
                    "defer_ms": requested_defer_ms,
                    "max_single_defer_ms": self._max_single_defer_ms,
                },
            )

        total_after = self._compute_total_defer_ms(record.delivery_id) + requested_defer_ms
        if total_after > self._max_total_defer_ms:
            raise NsRuntimeDeferRejectedError(
                "Total defer duration exceeds policy limit.",
                details={
                    "delivery_id": record.delivery_id,
                    "requested_defer_ms": requested_defer_ms,
                    "total_after_ms": total_after,
                    "max_total_defer_ms": self._max_total_defer_ms,
                },
            )

    def _compute_total_defer_ms(self, delivery_id: str) -> int:
        return sum(
            self._defers[defer_id].defer_ms
            for defer_id in self._defer_ids_by_delivery.get(delivery_id, [])
        )

    def _next_defer_sequence(self, delivery_id: str) -> int:
        return len(self._defer_ids_by_delivery.get(delivery_id, [])) + 1

    def _extend_ack_deadline(self, *, record: RuntimeDeliveryRecord, defer_ms: int) -> str:
        now = datetime.now(timezone.utc)
        current_deadline = self._parse_datetime(record.ack_deadline_at)
        base = now

        if current_deadline is not None and current_deadline > now:
            base = current_deadline

        return (base + timedelta(milliseconds=defer_ms)).isoformat(timespec="milliseconds")

    @staticmethod
    def _parse_datetime(value: str) -> datetime | None:
        if not value:
            return None

        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None

        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)

        return parsed

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
