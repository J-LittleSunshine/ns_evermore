# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
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
    NsRuntimeBackpressureError,
    NsRuntimeDeferRejectedError,
    NsRuntimeDeliveryStateError,
    NsRuntimeEnvelopeSchemaError,
    NsRuntimeNackRejectedError,
    NsRuntimeTargetUnavailableError,
    RUNTIME_NACK_REASON_ERROR_CODES
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

RuntimeDeliveryDuplicateStatus = Literal[
    "delivery_in_progress",
    "already_delivered",
    "dead_lettered",
    "expired",
    "cancelled",
]

RuntimeDeliveryAttemptWriteStatus = Literal[
    "created",
    "sending",
    "sent_to_transport",
    "write_failed",
]

RuntimeMessageDeliverySummaryState = Literal[
    "initializing",
    "pending",
    "partial_acked",
    "all_acked",
    "partial_failed",
    "failed",
    "cancelled",
]

RuntimeDeadLetterReplayability = Literal[
    "replayable",
    "not_replayable",
    "manual_confirm_required",
]

_RETRYABLE_ADMISSION_REJECTION_CODES: frozenset[str] = frozenset(
    {
        NsRuntimeBackpressureError.code,
        NsRuntimeTargetUnavailableError.code,
    }
)


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
class RuntimeAckTimeoutRecord:
    timeout_id: str
    delivery_id: str
    message_id: str
    tenant_id: str
    target_connection_id: str
    target_connection_epoch: int
    previous_state: RuntimeDeliveryState
    new_state: RuntimeDeliveryState
    timeout_sequence: int
    ack_deadline_at: str
    expires_at: str
    timed_out_at: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "timeout_id": self.timeout_id,
            "delivery_id": self.delivery_id,
            "message_id": self.message_id,
            "tenant_id": self.tenant_id,
            "target_connection_id": self.target_connection_id,
            "target_connection_epoch": self.target_connection_epoch,
            "previous_state": self.previous_state,
            "new_state": self.new_state,
            "timeout_sequence": self.timeout_sequence,
            "ack_deadline_at": self.ack_deadline_at,
            "expires_at": self.expires_at,
            "timed_out_at": self.timed_out_at,
            "reason": self.reason,
        }


@dataclass(slots=True, kw_only=True)
class RuntimeAckTimeoutScanResult:
    scanned_count: int
    timed_out_count: int
    retry_scheduled_count: int
    expired_count: int
    timeout_records: tuple[RuntimeAckTimeoutRecord, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "scanned_count": self.scanned_count,
            "timed_out_count": self.timed_out_count,
            "retry_scheduled_count": self.retry_scheduled_count,
            "expired_count": self.expired_count,
            "timeout_records": [
                record.to_dict()
                for record in self.timeout_records
            ],
        }


@dataclass(slots=True, kw_only=True)
class RuntimeDeadLetterRecord:
    dead_letter_id: str
    delivery_id: str
    message_id: str
    tenant_id: str
    message_type: str
    terminal_state: RuntimeDeliveryState
    reason: str
    last_error_code: str
    last_error_message: str
    attempt_count: int
    target_connection_id: str
    target_connection_epoch: int
    budget_exhausted: bool
    route_segment: str
    last_owner_runtime_id: str
    replayable: RuntimeDeadLetterReplayability
    recommended_action: str
    created_at: str
    dead_lettered_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "dead_letter_id": self.dead_letter_id,
            "delivery_id": self.delivery_id,
            "message_id": self.message_id,
            "tenant_id": self.tenant_id,
            "message_type": self.message_type,
            "terminal_state": self.terminal_state,
            "reason": self.reason,
            "last_error_code": self.last_error_code,
            "last_error_message": self.last_error_message,
            "attempt_count": self.attempt_count,
            "target_connection_id": self.target_connection_id,
            "target_connection_epoch": self.target_connection_epoch,
            "budget_exhausted": self.budget_exhausted,
            "route_segment": self.route_segment,
            "last_owner_runtime_id": self.last_owner_runtime_id,
            "replayable": self.replayable,
            "recommended_action": self.recommended_action,
            "created_at": self.created_at,
            "dead_lettered_at": self.dead_lettered_at,
        }


@dataclass(slots=True, kw_only=True)
class RuntimeDeadLetterScanResult:
    scanned_count: int
    created_count: int
    skipped_count: int
    dead_letter_records: tuple[RuntimeDeadLetterRecord, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "scanned_count": self.scanned_count,
            "created_count": self.created_count,
            "skipped_count": self.skipped_count,
            "dead_letter_records": [
                record.to_dict()
                for record in self.dead_letter_records
            ],
        }


@dataclass(slots=True, kw_only=True)
class RuntimeMessageDeliverySummary:
    summary_id: str
    message_id: str
    tenant_id: str
    message_type: str
    source_connection_id: str
    state: RuntimeMessageDeliverySummaryState
    target_count: int
    accepted_count: int
    rejected_count: int
    delivery_count: int
    acked_count: int
    dead_lettered_count: int
    expired_count: int
    cancelled_count: int
    pending_count: int
    prepared_count: int
    queued_count: int
    sending_count: int
    ack_waiting_count: int
    retry_scheduled_count: int
    replay_requested_count: int
    transferred_count: int
    created_at: str
    updated_at: str
    last_rejection_code: str = ""
    last_rejection_message: str = ""
    last_rejected_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary_id": self.summary_id,
            "message_id": self.message_id,
            "tenant_id": self.tenant_id,
            "message_type": self.message_type,
            "source_connection_id": self.source_connection_id,
            "state": self.state,
            "target_count": self.target_count,
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "delivery_count": self.delivery_count,
            "acked_count": self.acked_count,
            "dead_lettered_count": self.dead_lettered_count,
            "expired_count": self.expired_count,
            "cancelled_count": self.cancelled_count,
            "pending_count": self.pending_count,
            "prepared_count": self.prepared_count,
            "queued_count": self.queued_count,
            "sending_count": self.sending_count,
            "ack_waiting_count": self.ack_waiting_count,
            "retry_scheduled_count": self.retry_scheduled_count,
            "replay_requested_count": self.replay_requested_count,
            "transferred_count": self.transferred_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_rejection_code": self.last_rejection_code,
            "last_rejection_message": self.last_rejection_message,
            "last_rejected_at": self.last_rejected_at,
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
class RuntimeDeliveryRegistrationResult:
    created: bool
    record: RuntimeDeliveryRecord
    duplicate_status: RuntimeDeliveryDuplicateStatus | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "created": self.created,
            "duplicate_status": self.duplicate_status,
            "delivery": self.record.to_dict(),
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
    def __init__(self, *, default_ack_timeout_ms: int = 30000, max_defer_count: int = 3, max_single_defer_ms: int = 30000, max_total_defer_ms: int = 90000, dedupe_window_seconds: int = 300) -> None:
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
        self._ack_timeouts: dict[str, RuntimeAckTimeoutRecord] = {}
        self._ack_timeout_ids_by_delivery: dict[str, list[str]] = {}
        self._dead_letters: dict[str, RuntimeDeadLetterRecord] = {}
        self._dead_letter_id_by_delivery: dict[str, str] = {}
        self._summaries: dict[str, RuntimeMessageDeliverySummary] = {}
        self._summary_id_by_tenant_message: dict[tuple[str, str], str] = {}
        self._dedupe_window_seconds = max(0, dedupe_window_seconds)
        self._delivery_id_by_dedupe_key: dict[tuple[str, str, str], str] = {}
        self._dedupe_expires_at_by_key: dict[tuple[str, str, str], datetime] = {}
        self._dedupe_fingerprint_by_key: dict[tuple[str, str, str], str] = {}

    def register_prepared_record(self, *, decision: RuntimeRouteDecision, envelope: Envelope, target: RuntimeRouteTarget) -> RuntimeDeliveryRegistrationResult:
        target_fingerprint = self._build_target_fingerprint(
            target
        )
        dedupe_key = (
            decision.source_tenant_id,
            envelope.message_id,
            target_fingerprint,
        )
        request_fingerprint = self._build_dedupe_request_fingerprint(envelope)
        now = datetime.now(timezone.utc)

        if self._dedupe_window_seconds > 0:
            existing_delivery_id = (
                self._delivery_id_by_dedupe_key.get(
                    dedupe_key
                )
            )
            dedupe_expires_at = (
                self._dedupe_expires_at_by_key.get(
                    dedupe_key
                )
            )

            if (
                    existing_delivery_id is not None
                    and dedupe_expires_at is not None
                    and dedupe_expires_at > now
            ):
                existing_record = self._records.get(
                    existing_delivery_id
                )

                if existing_record is not None:
                    existing_fingerprint = (
                        self._dedupe_fingerprint_by_key.get(
                            dedupe_key
                        )
                    )

                    if (
                            existing_fingerprint
                            != request_fingerprint
                    ):
                        raise NsRuntimeDeliveryStateError(
                            "message_id and target were reused with different envelope content.",
                            details={
                                "message_id": envelope.message_id,
                            },
                        )

                    return RuntimeDeliveryRegistrationResult(
                        created=False,
                        record=existing_record,
                        duplicate_status=(
                            self._resolve_duplicate_status(
                                existing_record.state
                            )
                        ),
                    )

            self._remove_dedupe_key(dedupe_key)

        record = self.create_prepared_record(
            decision=decision,
            envelope=envelope,
            target=target,
        )

        if self._dedupe_window_seconds > 0:
            self._delivery_id_by_dedupe_key[
                dedupe_key
            ] = record.delivery_id
            self._dedupe_expires_at_by_key[
                dedupe_key
            ] = now + timedelta(
                seconds=self._dedupe_window_seconds
            )
            self._dedupe_fingerprint_by_key[
                dedupe_key
            ] = request_fingerprint

        return RuntimeDeliveryRegistrationResult(
            created=True,
            record=record,
        )

    def estimate_new_delivery_count(self, *, decision: RuntimeRouteDecision, envelope: Envelope, now: datetime | None = None) -> int:
        writable_targets = tuple(
            target
            for target in decision.targets
            if target.connection_id != "runtime"
        )

        if not writable_targets:
            return 0

        if (
                decision.target_count != 1
                or len(writable_targets) != 1
        ):
            return len(writable_targets)

        if self._dedupe_window_seconds <= 0:
            return 1

        target = writable_targets[0]
        target_fingerprint = (
            self._build_target_fingerprint(
                target
            )
        )
        dedupe_key = (
            decision.source_tenant_id,
            envelope.message_id,
            target_fingerprint,
        )

        existing_delivery_id = (
            self._delivery_id_by_dedupe_key.get(
                dedupe_key
            )
        )
        dedupe_expires_at = (
            self._dedupe_expires_at_by_key.get(
                dedupe_key
            )
        )
        resolved_now = (
                now
                or datetime.now(timezone.utc)
        )

        if (
                existing_delivery_id is not None
                and dedupe_expires_at is not None
                and dedupe_expires_at > resolved_now
                and existing_delivery_id in self._records
        ):
            return 0

        return 1

    def create_prepared_record(self, *, decision: RuntimeRouteDecision, envelope: Envelope, target: RuntimeRouteTarget) -> RuntimeDeliveryRecord:
        existing_summary = self.get_message_summary(envelope.message_id, tenant_id=decision.source_tenant_id)

        if existing_summary is not None and existing_summary.delivery_count == 0 and existing_summary.rejected_count > 0:
            if existing_summary.last_rejection_code in _RETRYABLE_ADMISSION_REJECTION_CODES:
                self._reset_retryable_rejection_summary(summary=existing_summary, target_count=decision.target_count)
            else:
                details = {
                    "message_id": envelope.message_id,
                    "summary_id": existing_summary.summary_id,
                    "rejected_count": (
                        existing_summary.rejected_count
                    ),
                    "last_rejection_code": (
                        existing_summary.last_rejection_code
                    ),
                }
                raise NsRuntimeDeliveryStateError("Previously rejected task dispatch message_id cannot be reused for a new delivery.", details=details)
        delivery_id = str(uuid.uuid4())
        now = utc_now_iso()
        summary = self._ensure_message_summary(
            envelope=envelope,
            source_connection_id=decision.source_connection_id,
            source_tenant_id=decision.source_tenant_id,
            target_count=decision.target_count,
            now=now,
        )
        summary_id = summary.summary_id
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
        self._refresh_message_summary(summary_id)
        return record

    def start_sending(self, *, record: RuntimeDeliveryRecord) -> RuntimeDeliveryAttempt:
        if record.state not in {
            "prepared",
            "queued",
            "retry_scheduled"
        }:
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
        self._refresh_message_summary(record.summary_id)

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
        self._refresh_message_summary(record.summary_id)

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
        self._refresh_message_summary(record.summary_id)

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

        if record.state not in {
            "sending",
            "ack_waiting",
            "retry_scheduled"
        }:
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
        self._refresh_message_summary(record.summary_id)

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

        if record.state not in {
            "sending",
            "ack_waiting",
            "retry_scheduled"
        }:
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

        self._refresh_message_summary(record.summary_id)

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

        if record.state not in {
            "sending",
            "ack_waiting",
            "retry_scheduled"
        }:
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
        self._refresh_message_summary(record.summary_id)

        self._defers[defer_record.defer_id] = defer_record
        self._defer_ids_by_delivery.setdefault(record.delivery_id, []).append(defer_record.defer_id)

        return RuntimeDeferResult(
            status="deferred",
            delivery_record=record,
            defer_record=defer_record,
            total_defer_ms=self._compute_total_defer_ms(record.delivery_id),
            defer_count=len(self._defer_ids_by_delivery.get(record.delivery_id, [])),
        )

    def scan_ack_timeouts(self, *, now: datetime | None = None) -> RuntimeAckTimeoutScanResult:
        resolved_now = now or datetime.now(timezone.utc)
        scanned_count = 0
        timeout_records: list[RuntimeAckTimeoutRecord] = []

        for record in self.list_records():
            if record.state != "ack_waiting":
                continue

            scanned_count += 1
            ack_deadline = self._parse_datetime(record.ack_deadline_at)
            if ack_deadline is None or ack_deadline > resolved_now:
                continue

            timeout_records.append(
                self._mark_ack_timed_out(
                    record=record,
                    now=resolved_now,
                )
            )

        retry_scheduled_count = sum(
            1
            for record in timeout_records
            if record.new_state == "retry_scheduled"
        )
        expired_count = sum(
            1
            for record in timeout_records
            if record.new_state == "expired"
        )

        return RuntimeAckTimeoutScanResult(
            scanned_count=scanned_count,
            timed_out_count=len(timeout_records),
            retry_scheduled_count=retry_scheduled_count,
            expired_count=expired_count,
            timeout_records=tuple(timeout_records),
        )

    def list_ack_timeouts_for_delivery(self, delivery_id: str) -> tuple[RuntimeAckTimeoutRecord, ...]:
        return tuple(
            self._ack_timeouts[timeout_id]
            for timeout_id in self._ack_timeout_ids_by_delivery.get(delivery_id, [])
        )

    def list_ack_timeouts(self) -> tuple[RuntimeAckTimeoutRecord, ...]:
        return tuple(
            self._ack_timeouts[key]
            for key in sorted(self._ack_timeouts.keys())
        )

    def scan_dead_letters(self, *, now: datetime | None = None) -> RuntimeDeadLetterScanResult:
        resolved_now = now or datetime.now(timezone.utc)
        scanned_count = 0
        created_records: list[RuntimeDeadLetterRecord] = []

        for record in self.list_records():
            if record.state != "dead_lettered":
                continue

            scanned_count += 1
            if record.delivery_id in self._dead_letter_id_by_delivery:
                continue

            created_records.append(
                self._create_dead_letter_record(
                    record=record,
                    now=resolved_now,
                )
            )

        return RuntimeDeadLetterScanResult(
            scanned_count=scanned_count,
            created_count=len(created_records),
            skipped_count=scanned_count - len(created_records),
            dead_letter_records=tuple(created_records),
        )

    def get_dead_letter_for_delivery(self, delivery_id: str) -> RuntimeDeadLetterRecord | None:
        dead_letter_id = self._dead_letter_id_by_delivery.get(delivery_id)
        if dead_letter_id is None:
            return None

        return self._dead_letters.get(dead_letter_id)

    def list_dead_letters(self) -> tuple[RuntimeDeadLetterRecord, ...]:
        return tuple(
            self._dead_letters[key]
            for key in sorted(self._dead_letters.keys())
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

    def register_rejected_summary(
            self,
            *,
            envelope: Envelope,
            source_connection_id: str,
            source_tenant_id: str,
            target_count: int,
            rejected_count: int,
            reason_code: str,
            reason_message: str,
    ) -> RuntimeMessageDeliverySummary:
        now = utc_now_iso()
        resolved_rejected_count = max(1, rejected_count)
        resolved_target_count = max(
            resolved_rejected_count,
            target_count,
        )

        summary = self._ensure_message_summary(
            envelope=envelope,
            source_connection_id=source_connection_id,
            source_tenant_id=source_tenant_id,
            target_count=resolved_target_count,
            now=now,
        )

        if summary.delivery_count > 0:
            raise NsRuntimeDeliveryStateError(
                "Cannot register an all-target rejection after delivery records were created.",
                details={
                    "message_id": envelope.message_id,
                    "summary_id": summary.summary_id,
                    "delivery_count": summary.delivery_count,
                    "rejected_count": summary.rejected_count,
                },
            )

        summary.target_count = max(
            summary.target_count,
            resolved_target_count,
        )
        summary.rejected_count = max(
            summary.rejected_count,
            resolved_rejected_count,
        )
        summary.last_rejection_code = reason_code
        summary.last_rejection_message = reason_message
        summary.last_rejected_at = now
        summary.updated_at = now

        refreshed = self._refresh_message_summary(
            summary.summary_id
        )
        if refreshed is None:
            raise NsRuntimeDeliveryStateError(
                "Rejected MessageDeliverySummary disappeared during refresh.",
                details={
                    "message_id": envelope.message_id,
                    "summary_id": summary.summary_id,
                },
            )

        return refreshed

    def get_summary(self, summary_id: str) -> RuntimeMessageDeliverySummary | None:
        return self._summaries.get(summary_id)

    def get_message_summary(self, message_id: str, *, tenant_id: str | None = None) -> RuntimeMessageDeliverySummary | None:
        if tenant_id is not None:
            summary_id = (
                self._summary_id_by_tenant_message.get(
                    (
                        tenant_id,
                        message_id,
                    )
                )
            )
            if summary_id is None:
                return None

            return self._summaries.get(summary_id)

        matches = tuple(
            summary
            for summary in self._summaries.values()
            if summary.message_id == message_id
        )
        if len(matches) != 1:
            return None

        return matches[0]

    def list_message_summaries(self) -> tuple[RuntimeMessageDeliverySummary, ...]:
        return tuple(
            self._summaries[key]
            for key in sorted(self._summaries.keys())
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

        summary_by_state: dict[str, int] = {}
        for summary in self._summaries.values():
            summary_by_state[summary.state] = summary_by_state.get(summary.state, 0) + 1

        return {
            "delivery_count": len(self._records),
            "message_summary_count": len(self._summaries),
            "attempt_count": len(self._attempts),
            "ack_count": len(self._acks),
            "nack_count": len(self._nacks),
            "defer_count": len(self._defers),
            "ack_timeout_count": len(self._ack_timeouts),
            "dead_letter_count": len(self._dead_letters),
            "by_state": {
                key: by_state[key]
                for key in sorted(by_state.keys())
            },
            "summary_by_state": {
                key: summary_by_state[key]
                for key in sorted(summary_by_state.keys())
            },
            "server_time": utc_now_iso(),
        }

    def refresh_message_summary_for_delivery(self, delivery_id: str) -> RuntimeMessageDeliverySummary | None:
        record = self._records.get(delivery_id)
        if record is None:
            return None

        return self._refresh_message_summary(record.summary_id)

    def _ensure_message_summary(self, *, envelope: Envelope, source_connection_id: str, source_tenant_id: str, target_count: int, now: str, ) -> RuntimeMessageDeliverySummary:
        tenant_message_key = (
            source_tenant_id,
            envelope.message_id,
        )
        summary_id = (
            self._summary_id_by_tenant_message.get(
                tenant_message_key
            )
        )

        if summary_id is not None:
            summary = self._summaries[summary_id]
            summary.target_count = max(
                summary.target_count,
                target_count,
            )
            summary.updated_at = now
            return summary

        summary_id = self._build_summary_id(
            tenant_id=source_tenant_id,
            message_id=envelope.message_id,
        )

        summary = RuntimeMessageDeliverySummary(
            summary_id=summary_id,
            message_id=envelope.message_id,
            tenant_id=source_tenant_id,
            message_type=envelope.message_type,
            source_connection_id=source_connection_id,
            state="initializing",
            target_count=target_count,
            accepted_count=0,
            rejected_count=0,
            delivery_count=0,
            acked_count=0,
            dead_lettered_count=0,
            expired_count=0,
            cancelled_count=0,
            pending_count=0,
            prepared_count=0,
            queued_count=0,
            sending_count=0,
            ack_waiting_count=0,
            retry_scheduled_count=0,
            replay_requested_count=0,
            transferred_count=0,
            created_at=now,
            updated_at=now,
        )

        self._summaries[summary_id] = summary
        self._summary_id_by_tenant_message[
            tenant_message_key
        ] = summary_id

        return summary

    @staticmethod
    def _reset_retryable_rejection_summary(*, summary: RuntimeMessageDeliverySummary, target_count: int) -> None:
        summary.state = "initializing"
        summary.target_count = max(1, target_count)
        summary.accepted_count = 0
        summary.rejected_count = 0
        summary.delivery_count = 0

        summary.last_rejection_code = ""
        summary.last_rejection_message = ""
        summary.last_rejected_at = ""
        summary.updated_at = utc_now_iso()

    def _refresh_message_summary(self, summary_id: str) -> RuntimeMessageDeliverySummary | None:
        summary = self._summaries.get(summary_id)
        if summary is None:
            return None

        records = [
            record
            for record in self._records.values()
            if record.summary_id == summary_id
        ]
        by_state: dict[str, int] = {}
        for record in records:
            by_state[record.state] = by_state.get(record.state, 0) + 1

        summary.delivery_count = len(records)
        summary.accepted_count = len(records)
        summary.target_count = max(summary.target_count, summary.accepted_count + summary.rejected_count)
        summary.acked_count = by_state.get("acked", 0)
        summary.dead_lettered_count = by_state.get("dead_lettered", 0)
        summary.expired_count = by_state.get("expired", 0)
        summary.cancelled_count = by_state.get("cancelled", 0)
        summary.prepared_count = by_state.get("prepared", 0)
        summary.queued_count = by_state.get("queued", 0)
        summary.sending_count = by_state.get("sending", 0)
        summary.ack_waiting_count = by_state.get("ack_waiting", 0)
        summary.retry_scheduled_count = by_state.get("retry_scheduled", 0)
        summary.replay_requested_count = by_state.get("replay_requested", 0)
        summary.transferred_count = by_state.get("transferred", 0)
        summary.pending_count = (
                summary.prepared_count
                + summary.queued_count
                + summary.sending_count
                + summary.ack_waiting_count
                + summary.retry_scheduled_count
                + summary.replay_requested_count
                + summary.transferred_count
        )
        summary.state = self._resolve_summary_state(summary)
        summary.updated_at = utc_now_iso()
        return summary

    @staticmethod
    def _resolve_summary_state(summary: RuntimeMessageDeliverySummary) -> RuntimeMessageDeliverySummaryState:
        failure_count = summary.rejected_count + summary.dead_lettered_count + summary.expired_count
        terminal_count = summary.acked_count + summary.dead_lettered_count + summary.expired_count + summary.cancelled_count

        if summary.delivery_count == 0:
            if summary.rejected_count > 0:
                return "failed"
            return "pending"

        if summary.acked_count == summary.delivery_count:
            return "all_acked"

        if summary.cancelled_count == summary.delivery_count:
            return "cancelled"

        if failure_count > 0 and terminal_count == summary.delivery_count and summary.acked_count == 0:
            return "failed"

        if failure_count > 0:
            return "partial_failed"

        if summary.acked_count > 0:
            return "partial_acked"

        return "pending"

    @staticmethod
    def _resolve_duplicate_status(state: RuntimeDeliveryState) -> RuntimeDeliveryDuplicateStatus:
        if state == "acked":
            return "already_delivered"

        if state == "dead_lettered":
            return "dead_lettered"

        if state == "expired":
            return "expired"

        if state == "cancelled":
            return "cancelled"

        return "delivery_in_progress"

    @staticmethod
    def _build_dedupe_request_fingerprint(envelope: Envelope) -> str:
        raw = envelope.to_dict()

        stable_envelope = {
            key: value
            for key, value in raw.items()
            if key not in {
                "source",
                "auth_context",
                "trace",
                "delivery",
            }
        }

        message = stable_envelope.get("message")
        if isinstance(message, dict):
            stable_message = dict(message)

            stable_message.pop("created_at", None)
            stable_envelope["message"] = stable_message

        encoded = json.dumps(
            stable_envelope,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return hashlib.sha256(encoded).hexdigest()

    def _remove_dedupe_key(self, dedupe_key: tuple[str, str, str]) -> None:
        self._delivery_id_by_dedupe_key.pop(dedupe_key, None)
        self._dedupe_expires_at_by_key.pop(dedupe_key, None)
        self._dedupe_fingerprint_by_key.pop(dedupe_key, None)

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

    def _create_dead_letter_record(self, *, record: RuntimeDeliveryRecord, now: datetime) -> RuntimeDeadLetterRecord:
        nack_record = self.get_nack_for_delivery(record.delivery_id)
        reason = record.last_error_message or "dead_lettered"
        if nack_record is not None and nack_record.reason:
            reason = nack_record.reason

        replayable = self._resolve_dead_letter_replayability(
            reason=reason,
            last_error_code=record.last_error_code,
        )
        created_at = now.isoformat(timespec="milliseconds")
        dead_letter_record = RuntimeDeadLetterRecord(
            dead_letter_id=str(uuid.uuid4()),
            delivery_id=record.delivery_id,
            message_id=record.message_id,
            tenant_id=record.tenant_id,
            message_type=record.message_type,
            terminal_state=record.state,
            reason=reason,
            last_error_code=record.last_error_code,
            last_error_message=record.last_error_message,
            attempt_count=record.attempt_count,
            target_connection_id=record.target_connection_id,
            target_connection_epoch=record.target_connection_epoch,
            budget_exhausted=False,
            route_segment="local",
            last_owner_runtime_id="",
            replayable=replayable,
            recommended_action=self._resolve_dead_letter_recommended_action(replayable),
            created_at=created_at,
            dead_lettered_at=record.updated_at or created_at,
        )

        self._dead_letters[dead_letter_record.dead_letter_id] = dead_letter_record
        self._dead_letter_id_by_delivery[record.delivery_id] = dead_letter_record.dead_letter_id
        return dead_letter_record

    @staticmethod
    def _resolve_dead_letter_replayability(*, reason: str, last_error_code: str) -> RuntimeDeadLetterReplayability:
        if reason in {
            "ack_timeout",
            "target_overloaded",
            "temporarily_unavailable",
            "queue_full",
            "dependency_unavailable",
            "target_draining",
            "node_degraded",
        }:
            return "replayable"

        if reason in {
            "permission_denied",
            "tenant_mismatch",
            "invalid_payload",
            "invalid_payload_ref",
            "payload_ref_denied",
            "source_forged",
            "auth_context_forged",
            "protocol_violation",
        }:
            return "not_replayable"

        if last_error_code in {
            "RUNTIME_UNAUTHORIZED_MESSAGE_TYPE",
            "RUNTIME_ENVELOPE_SCHEMA_ERROR",
        }:
            return "not_replayable"

        return "manual_confirm_required"

    @staticmethod
    def _resolve_dead_letter_recommended_action(replayable: RuntimeDeadLetterReplayability) -> str:
        if replayable == "replayable":
            return "review_then_replay"

        if replayable == "not_replayable":
            return "do_not_replay"

        return "manual_review"

    def _mark_ack_timed_out(self, *, record: RuntimeDeliveryRecord, now: datetime) -> RuntimeAckTimeoutRecord:
        previous_state = record.state
        timed_out_at = now.isoformat(timespec="milliseconds")

        if self._record_is_expired(record=record, now=now):
            new_state: RuntimeDeliveryState = "expired"
            reason = "message_expired"
            last_error_code = "RUNTIME_DELIVERY_EXPIRED"
        else:
            new_state = "retry_scheduled"
            reason = "ack_timeout"
            last_error_code = "RUNTIME_ACK_TIMEOUT"

        self._refresh_message_summary(record.summary_id)

        timeout_record = RuntimeAckTimeoutRecord(
            timeout_id=str(uuid.uuid4()),
            delivery_id=record.delivery_id,
            message_id=record.message_id,
            tenant_id=record.tenant_id,
            target_connection_id=record.target_connection_id,
            target_connection_epoch=record.target_connection_epoch,
            previous_state=previous_state,
            new_state=new_state,
            timeout_sequence=self._next_ack_timeout_sequence(record.delivery_id),
            ack_deadline_at=record.ack_deadline_at,
            expires_at=record.expires_at,
            timed_out_at=timed_out_at,
            reason=reason,
        )

        record.state = new_state
        record.updated_at = timed_out_at
        record.last_error_code = last_error_code
        record.last_error_message = reason
        self._refresh_message_summary(record.summary_id)

        self._ack_timeouts[timeout_record.timeout_id] = timeout_record
        self._ack_timeout_ids_by_delivery.setdefault(record.delivery_id, []).append(timeout_record.timeout_id)

        return timeout_record

    def _next_ack_timeout_sequence(self, delivery_id: str) -> int:
        return len(self._ack_timeout_ids_by_delivery.get(delivery_id, [])) + 1

    def _record_is_expired(self, *, record: RuntimeDeliveryRecord, now: datetime) -> bool:
        expires_at = self._parse_datetime(record.expires_at)
        if expires_at is None:
            return False

        return expires_at <= now

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

    @staticmethod
    def _build_summary_id(*, tenant_id: str, message_id: str) -> str:
        digest = hashlib.sha256(
            f"{tenant_id}\0{message_id}".encode("utf-8")
        ).hexdigest()[:24]

        return f"summary:{digest}"
