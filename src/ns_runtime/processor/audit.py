# -*- coding: utf-8 -*-
"""Typed final processor audit boundary without P08 authority storage."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from ns_common.exceptions import NsValidationError

from .contracts import ProcessorSafeSummary, ProcessorTraceReference


class AuditConsistency(str, Enum):
    ORDINARY = "ordinary"
    STRONG_REQUIRED = "strong_required"


class AuditAction(str, Enum):
    SUCCEEDED = "succeeded"
    REJECTED = "rejected"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True, kw_only=True)
class ProcessorAuditRecord:
    safe_summary: ProcessorSafeSummary
    processor: str
    action: AuditAction
    error: str | None
    trace: ProcessorTraceReference
    config_version: str
    policy_version: str
    required_consistency: AuditConsistency
    occurred_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.safe_summary, ProcessorSafeSummary):
            _invalid("safe_summary")
        if not isinstance(self.processor, str) or not self.processor or len(self.processor) > 256:
            _invalid("processor")
        if not isinstance(self.action, AuditAction):
            _invalid("action")
        if self.error is not None and (
            not isinstance(self.error, str)
            or not self.error.startswith("RUNTIME_")
            or len(self.error) > 128
        ):
            _invalid("error")
        if not isinstance(self.trace, ProcessorTraceReference):
            _invalid("trace")
        for name in ("config_version", "policy_version"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value or len(value) > 256:
                _invalid(name)
        if not isinstance(self.required_consistency, AuditConsistency):
            _invalid("required_consistency")
        if (
            not isinstance(self.occurred_at, datetime)
            or self.occurred_at.tzinfo is None
            or self.occurred_at.utcoffset() is None
        ):
            _invalid("occurred_at")
        object.__setattr__(self, "occurred_at", self.occurred_at.astimezone(timezone.utc))


class AuditSink(ABC):
    """A sink receives safe typed records; it is never a global singleton."""

    @abstractmethod
    async def emit(self, record: ProcessorAuditRecord) -> None:
        raise NotImplementedError


class DeterministicTestAuditSink(AuditSink):
    def __init__(self) -> None:
        self._records: list[ProcessorAuditRecord] = []
        self.failure: Exception | None = None
        self.attempted_count = 0

    @property
    def records(self) -> tuple[ProcessorAuditRecord, ...]:
        return tuple(self._records)

    async def emit(self, record: ProcessorAuditRecord) -> None:
        if not isinstance(record, ProcessorAuditRecord):
            _invalid("record")
        self.attempted_count += 1
        if self.failure is not None:
            raise self.failure
        self._records.append(record)


class LoggingAuditSink(AuditSink):
    """Ordinary local sink; records retain strong-required as a requirement only."""

    def __init__(self, *, logger: logging.Logger) -> None:
        if not isinstance(logger, logging.Logger):
            _invalid("logger")
        self._logger = logger

    async def emit(self, record: ProcessorAuditRecord) -> None:
        if not isinstance(record, ProcessorAuditRecord):
            _invalid("record")
        self._logger.info(
            "Runtime processor final audit.",
            extra={
                "event": "runtime_processor_final_audit",
                "message_type": record.safe_summary.message_type,
                "message_category": record.safe_summary.category,
                "object_reference": record.safe_summary.object_reference,
                "processor": record.processor,
                "action": record.action.value,
                "error_code": record.error,
                "trace_reference": record.trace.value,
                "config_version": record.config_version,
                "policy_version": record.policy_version,
                "required_consistency": record.required_consistency.value,
            },
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class AuditWriteOutcome:
    succeeded: bool
    required_consistency: AuditConsistency


class ProcessorAuditBoundary:
    """Attempt exactly one final write and keep sink failure semantics explicit."""

    def __init__(self, *, sink: AuditSink) -> None:
        if not isinstance(sink, AuditSink):
            _invalid("sink")
        self._sink = sink

    async def write_final(self, record: ProcessorAuditRecord) -> AuditWriteOutcome:
        if not isinstance(record, ProcessorAuditRecord):
            _invalid("record")
        try:
            await self._sink.emit(record)
        except asyncio.CancelledError:
            raise
        except Exception:
            return AuditWriteOutcome(
                succeeded=False,
                required_consistency=record.required_consistency,
            )
        return AuditWriteOutcome(
            succeeded=True,
            required_consistency=record.required_consistency,
        )


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Processor audit value is invalid.",
        details={"component": "processor_audit", "field": field_name},
    )


__all__ = (
    "AuditAction",
    "AuditConsistency",
    "AuditSink",
    "AuditWriteOutcome",
    "DeterministicTestAuditSink",
    "LoggingAuditSink",
    "ProcessorAuditBoundary",
    "ProcessorAuditRecord",
)
