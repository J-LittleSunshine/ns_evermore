# -*- coding: utf-8 -*-
"""Lightweight P10 admission responses and post-commit emission boundary."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone

from ns_common.exceptions import NsValidationError

from .models import (
    ADMISSION_RESPONSE_VERSION, ADMISSION_RESULT_VERSION,
    AdmissionOutcome, AdmissionTrace,
    DuplicateLifecycle, PayloadDependencyDisposition, RejectionReason,
)
from enum import Enum


class AdmissionCommitState(str, Enum):
    NOT_COMMITTED = "not_committed"
    COMMITTED = "committed"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True, kw_only=True)
class DeliveryAcceptedResponse:
    schema_version: str
    message_id: str
    summary_id: str
    accepted_at: datetime
    status_query_hint: str
    trace: AdmissionTrace

    def __post_init__(self) -> None:
        _base(self.schema_version, self.message_id, self.summary_id, self.trace)
        object.__setattr__(self, "accepted_at", _utc(self.accepted_at))
        if self.status_query_hint != f"delivery.summary:{self.summary_id}":
            _invalid("accepted.status_query_hint")

    def to_wire(self) -> dict[str, object]:
        return {
            "message_id": self.message_id, "summary_id": self.summary_id,
            "accepted_at": self.accepted_at.isoformat(),
            "status_query_hint": self.status_query_hint,
            "trace": self.trace.to_wire(),
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class DeliveryRejectedResponse:
    schema_version: str
    message_id: str
    summary_id: str | None
    rejected_at: datetime
    reason: RejectionReason
    disposition: PayloadDependencyDisposition
    trace: AdmissionTrace

    def __post_init__(self) -> None:
        _base(self.schema_version, self.message_id, self.summary_id, self.trace)
        object.__setattr__(self, "rejected_at", _utc(self.rejected_at))
        if not isinstance(self.reason, RejectionReason):
            _invalid("rejected.reason")
        if not isinstance(self.disposition, PayloadDependencyDisposition):
            _invalid("rejected.disposition")

    def to_wire(self) -> dict[str, object]:
        return {
            "message_id": self.message_id, "summary_id": self.summary_id,
            "rejected_at": self.rejected_at.isoformat(),
            "reason": self.reason.value, "disposition": self.disposition.value,
            "trace": self.trace.to_wire(),
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class DeliveryDuplicateResponse:
    schema_version: str
    message_id: str
    summary_id: str
    observed_at: datetime
    lifecycle: DuplicateLifecycle
    status_query_hint: str
    trace: AdmissionTrace

    def __post_init__(self) -> None:
        _base(self.schema_version, self.message_id, self.summary_id, self.trace)
        object.__setattr__(self, "observed_at", _utc(self.observed_at))
        if not isinstance(self.lifecycle, DuplicateLifecycle):
            _invalid("duplicate.lifecycle")
        if self.status_query_hint != f"delivery.summary:{self.summary_id}":
            _invalid("duplicate.status_query_hint")

    def to_wire(self) -> dict[str, object]:
        return {
            "message_id": self.message_id, "summary_id": self.summary_id,
            "observed_at": self.observed_at.isoformat(),
            "lifecycle": self.lifecycle.value,
            "status_query_hint": self.status_query_hint,
            "trace": self.trace.to_wire(),
        }


AdmissionResponse = DeliveryAcceptedResponse | DeliveryRejectedResponse | DeliveryDuplicateResponse


@dataclass(frozen=True, slots=True, kw_only=True)
class AdmissionResult:
    schema_version: str = ADMISSION_RESULT_VERSION
    outcome: AdmissionOutcome
    response: AdmissionResponse
    commit_state: AdmissionCommitState

    def __post_init__(self) -> None:
        if self.schema_version != ADMISSION_RESULT_VERSION:
            _invalid("result.schema_version")
        if not isinstance(self.outcome, AdmissionOutcome):
            _invalid("result.outcome")
        if not isinstance(self.commit_state, AdmissionCommitState):
            _invalid("result.commit_state")
        expected = {
            AdmissionOutcome.ACCEPTED: DeliveryAcceptedResponse,
            AdmissionOutcome.REJECTED: DeliveryRejectedResponse,
            AdmissionOutcome.WAIT_REQUIRED: DeliveryRejectedResponse,
            AdmissionOutcome.DEAD_LETTER_REQUIRED: DeliveryRejectedResponse,
            AdmissionOutcome.UNAVAILABLE: DeliveryRejectedResponse,
            AdmissionOutcome.DUPLICATE: DeliveryDuplicateResponse,
        }[self.outcome]
        if not isinstance(self.response, expected):
            _invalid("result.response")
        if (self.outcome in {AdmissionOutcome.ACCEPTED, AdmissionOutcome.DUPLICATE}
                and self.commit_state is not AdmissionCommitState.COMMITTED):
            _invalid("result.commit")
        if (self.commit_state is AdmissionCommitState.INDETERMINATE
                and self.outcome is not AdmissionOutcome.UNAVAILABLE):
            _invalid("result.indeterminate")

    @property
    def committed(self) -> bool:
        return self.commit_state is AdmissionCommitState.COMMITTED


class AdmissionResponseSender(ABC):
    @abstractmethod
    async def send(self, response: AdmissionResponse) -> None:
        raise NotImplementedError


class AdmissionEmissionObserver(ABC):
    @abstractmethod
    def response_emission_failed(self, *, outcome: AdmissionOutcome) -> None:
        """Record only a bounded enum; never a response, exception, or payload."""
        raise NotImplementedError


async def emit_admission_result(
    result: AdmissionResult, *, sender: AdmissionResponseSender,
    observer: AdmissionEmissionObserver,
) -> bool:
    """Send after commit. A transport failure can never invoke state rollback."""
    if not isinstance(result, AdmissionResult):
        _invalid("emission.result")
    if not isinstance(sender, AdmissionResponseSender):
        _invalid("emission.sender")
    if not isinstance(observer, AdmissionEmissionObserver):
        _invalid("emission.observer")
    try:
        await sender.send(result.response)
    except Exception:
        observer.response_emission_failed(outcome=result.outcome)
        return False
    return True


def _base(schema: object, message_id: object, summary_id: object,
          trace: object) -> None:
    if schema != ADMISSION_RESPONSE_VERSION:
        _invalid("response.schema_version")
    if not isinstance(message_id, str) or not message_id:
        _invalid("response.message_id")
    if summary_id is not None and (not isinstance(summary_id, str) or not summary_id):
        _invalid("response.summary_id")
    if not isinstance(trace, AdmissionTrace):
        _invalid("response.trace")


def _utc(value: object) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        _invalid("response.time")
    return value.astimezone(timezone.utc)


def _invalid(field: str) -> None:
    raise NsValidationError(
        "P10 admission response value is invalid.",
        details={"component": "delivery_admission_response", "field": field},
    )


__all__ = (
    "AdmissionEmissionObserver", "AdmissionResponse", "AdmissionResponseSender",
    "AdmissionCommitState", "AdmissionResult", "DeliveryAcceptedResponse", "DeliveryDuplicateResponse",
    "DeliveryRejectedResponse", "emit_admission_result",
)
