# -*- coding: utf-8 -*-
"""Single absolute monotonic budget for one P05 logical handshake attempt."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from ns_common.exceptions import NsStateError, NsValidationError
from ns_common.time import Clock


@dataclass(frozen=True, slots=True, kw_only=True)
class HandshakeDeadlineBudget:
    """Share one absolute deadline across receive, parse, IAM and negotiation."""

    clock: Clock = field(repr=False)
    deadline_monotonic: float

    def __post_init__(self) -> None:
        if not isinstance(self.clock, Clock):
            _invalid("clock")
        if (
            isinstance(self.deadline_monotonic, bool)
            or not isinstance(self.deadline_monotonic, (int, float))
            or not math.isfinite(float(self.deadline_monotonic))
        ):
            _invalid("deadline_monotonic")

    @classmethod
    def start(
        cls,
        *,
        clock: Clock,
        timeout_seconds: float,
    ) -> "HandshakeDeadlineBudget":
        if not isinstance(clock, Clock):
            _invalid("clock")
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or not math.isfinite(float(timeout_seconds))
            or float(timeout_seconds) <= 0
        ):
            _invalid("timeout_seconds")
        started_at = clock.monotonic()
        deadline = started_at + float(timeout_seconds)
        if not math.isfinite(started_at) or not math.isfinite(deadline):
            _state_error("invalid_clock_deadline")
        return cls(clock=clock, deadline_monotonic=deadline)

    def remaining_seconds(self) -> float:
        now = self.clock.monotonic()
        if not math.isfinite(now):
            _state_error("invalid_clock_observation")
        return max(0.0, self.deadline_monotonic - now)

    def expired(self) -> bool:
        return self.remaining_seconds() <= 0.0


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Handshake deadline budget is invalid.",
        details={"component": "logical_connection", "field": field_name},
    )


def _state_error(reason: str) -> None:
    raise NsStateError(
        "Handshake deadline budget cannot be evaluated.",
        details={
            "component": "logical_connection",
            "operation": "handshake_deadline",
            "reason": reason,
        },
    )


__all__ = ("HandshakeDeadlineBudget",)
