# -*- coding: utf-8 -*-
from __future__ import annotations

import math
import random
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Protocol, runtime_checkable

from ns_common.exceptions import NsStateError, NsValidationError
from ns_common.time import Clock


DEFAULT_MAX_RETRIES = 5
RandomSource = Callable[[], float]


def _finite_number(
    value: Any,
    *,
    field_name: str,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise NsValidationError(
            f"{field_name} must be a number.",
            details={
                "field": field_name,
                "value": value,
                "actual_type": type(value).__name__,
            },
        )
    normalized = float(value)
    if (
        not math.isfinite(normalized)
        or (minimum is not None and normalized < minimum)
        or (maximum is not None and normalized > maximum)
    ):
        raise NsValidationError(
            f"{field_name} is outside the allowed range.",
            details={
                "field": field_name,
                "value": value,
                "minimum": minimum,
                "maximum": maximum,
            },
        )
    return normalized


def _positive_integer(value: Any, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise NsValidationError(
            f"{field_name} must be a positive integer.",
            details={
                "field": field_name,
                "value": value,
                "actual_type": type(value).__name__,
            },
        )
    return value


@runtime_checkable
class BackoffStrategy(Protocol):
    """Pluggable delay calculation for a one-based retry number."""

    def delay_for(self, retry_number: int) -> float:
        """Return finite, non-negative delay seconds for this retry."""


@dataclass(frozen=True, slots=True)
class FixedBackoff:
    delay_seconds: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "delay_seconds",
            _finite_number(
                self.delay_seconds,
                field_name="delay_seconds",
                minimum=0.0,
            ),
        )

    def delay_for(self, retry_number: int) -> float:
        _positive_integer(retry_number, field_name="retry_number")
        return self.delay_seconds


@dataclass(frozen=True, slots=True)
class ExponentialBackoff:
    initial_delay_seconds: float
    maximum_delay_seconds: float
    multiplier: float = 2.0

    def __post_init__(self) -> None:
        initial = _finite_number(
            self.initial_delay_seconds,
            field_name="initial_delay_seconds",
            minimum=0.0,
        )
        maximum = _finite_number(
            self.maximum_delay_seconds,
            field_name="maximum_delay_seconds",
            minimum=initial,
        )
        multiplier = _finite_number(
            self.multiplier,
            field_name="multiplier",
            minimum=1.0,
        )
        object.__setattr__(self, "initial_delay_seconds", initial)
        object.__setattr__(self, "maximum_delay_seconds", maximum)
        object.__setattr__(self, "multiplier", multiplier)

    def delay_for(self, retry_number: int) -> float:
        retry = _positive_integer(retry_number, field_name="retry_number")
        if self.initial_delay_seconds == 0.0:
            return 0.0
        if self.initial_delay_seconds == self.maximum_delay_seconds:
            return self.maximum_delay_seconds
        try:
            delay = self.initial_delay_seconds * math.pow(
                self.multiplier,
                retry - 1,
            )
        except OverflowError:
            return self.maximum_delay_seconds
        if not math.isfinite(delay):
            return self.maximum_delay_seconds
        return min(delay, self.maximum_delay_seconds)


@dataclass(frozen=True, slots=True)
class JitterBackoff:
    """Apply symmetric proportional jitter to another strategy.

    A sample of 0.0 produces ``delay * (1 - ratio)``, 0.5 leaves the
    delay unchanged, and 1.0 produces ``delay * (1 + ratio)``.
    """

    strategy: BackoffStrategy
    ratio: float
    random_source: RandomSource = random.random

    def __post_init__(self) -> None:
        if not isinstance(self.strategy, BackoffStrategy):
            raise NsValidationError(
                "strategy must implement BackoffStrategy.",
                details={
                    "field": "strategy",
                    "actual_type": type(self.strategy).__name__,
                },
            )
        object.__setattr__(
            self,
            "ratio",
            _finite_number(
                self.ratio,
                field_name="jitter_ratio",
                minimum=0.0,
                maximum=1.0,
            ),
        )
        if not callable(self.random_source):
            raise NsValidationError(
                "random_source must be callable.",
                details={
                    "field": "random_source",
                    "actual_type": type(self.random_source).__name__,
                },
            )

    def delay_for(self, retry_number: int) -> float:
        retry = _positive_integer(retry_number, field_name="retry_number")
        base_delay = _strategy_delay(self.strategy, retry)
        if base_delay == 0.0 or self.ratio == 0.0:
            return base_delay
        sample = self.random_source()
        if (
            isinstance(sample, bool)
            or not isinstance(sample, (int, float))
            or not math.isfinite(float(sample))
            or not 0.0 <= float(sample) <= 1.0
        ):
            raise NsStateError(
                "random_source must return a finite number between 0 and 1.",
                details={
                    "field": "random_source",
                    "value": sample,
                    "actual_type": type(sample).__name__,
                },
            )
        factor = 1.0 + self.ratio * ((2.0 * float(sample)) - 1.0)
        jittered = base_delay * factor
        if not math.isfinite(jittered):
            raise NsStateError(
                "jitter calculation exceeded the supported delay range.",
                details={
                    "retry_number": retry,
                    "base_delay_seconds": base_delay,
                    "jitter_ratio": self.ratio,
                },
            )
        return max(0.0, jittered)


@dataclass(frozen=True, slots=True)
class RetryBudget:
    """Immutable automatic retry budget snapshot.

    Persisted delivery state remains authoritative; this value type does not
    provide cross-process atomicity.
    """

    max_retries: int = DEFAULT_MAX_RETRIES
    used_retries: int = 0

    def __post_init__(self) -> None:
        for field_name, value in (
            ("max_retries", self.max_retries),
            ("used_retries", self.used_retries),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise NsValidationError(
                    f"{field_name} must be a non-negative integer.",
                    details={
                        "field": field_name,
                        "value": value,
                        "actual_type": type(value).__name__,
                    },
                )
        if self.used_retries > self.max_retries:
            raise NsValidationError(
                "used_retries cannot exceed max_retries.",
                details={
                    "field": "used_retries",
                    "value": self.used_retries,
                    "max_retries": self.max_retries,
                },
            )

    @property
    def remaining_retries(self) -> int:
        return self.max_retries - self.used_retries

    @property
    def exhausted(self) -> bool:
        return self.remaining_retries == 0

    def can_consume(self, count: int = 1) -> bool:
        normalized = _positive_integer(count, field_name="retry_count")
        return normalized <= self.remaining_retries

    def try_consume(self, count: int = 1) -> RetryBudget | None:
        normalized = _positive_integer(count, field_name="retry_count")
        if normalized > self.remaining_retries:
            return None
        return replace(self, used_retries=self.used_retries + normalized)

    def consume(self, count: int = 1) -> RetryBudget:
        consumed = self.try_consume(count)
        if consumed is None:
            raise NsStateError(
                "automatic retry budget is exhausted.",
                details={
                    "action": "consume_retry_budget",
                    "max_retries": self.max_retries,
                    "used_retries": self.used_retries,
                    "requested_retries": count,
                    "remaining_retries": self.remaining_retries,
                },
            )
        return consumed


@dataclass(frozen=True, slots=True)
class RetrySchedule:
    retry_number: int
    delay_seconds: float
    scheduled_at: datetime
    next_retry_at: datetime
    scheduled_monotonic: float
    monotonic_deadline: float
    budget: RetryBudget


def schedule_next_retry(
    strategy: BackoffStrategy,
    budget: RetryBudget,
    *,
    retry_number: int,
    clock: Clock,
) -> RetrySchedule | None:
    """Reserve one retry and calculate its UTC and monotonic due times.

    ``None`` means the automatic retry budget is exhausted. The returned
    budget is the post-reservation immutable snapshot. ``retry_number`` is
    supplied by the delivery attempt state and is intentionally independent
    from the shared message-level budget's ``used_retries`` value.
    """

    if not isinstance(strategy, BackoffStrategy):
        raise NsValidationError(
            "strategy must implement BackoffStrategy.",
            details={
                "field": "strategy",
                "actual_type": type(strategy).__name__,
            },
        )
    if not isinstance(budget, RetryBudget):
        raise NsValidationError(
            "budget must be a RetryBudget.",
            details={
                "field": "budget",
                "actual_type": type(budget).__name__,
            },
        )
    if not isinstance(clock, Clock):
        raise NsValidationError(
            "clock must implement Clock.",
            details={
                "field": "clock",
                "actual_type": type(clock).__name__,
            },
        )

    normalized_retry_number = _positive_integer(
        retry_number,
        field_name="retry_number",
    )
    consumed_budget = budget.try_consume()
    if consumed_budget is None:
        return None
    delay = _strategy_delay(strategy, normalized_retry_number)
    scheduled_at = _utc_now(clock)
    scheduled_monotonic = _finite_number(
        clock.monotonic(),
        field_name="clock.monotonic",
    )
    monotonic_deadline = scheduled_monotonic + delay
    if not math.isfinite(monotonic_deadline):
        raise NsStateError(
            "retry monotonic deadline exceeded the supported range.",
            details={
                "retry_number": normalized_retry_number,
                "scheduled_monotonic": scheduled_monotonic,
                "delay_seconds": delay,
            },
        )
    try:
        next_retry_at = scheduled_at + timedelta(seconds=delay)
    except (OverflowError, ValueError) as error:
        raise NsStateError(
            "retry UTC deadline exceeded the supported range.",
            details={
                "retry_number": normalized_retry_number,
                "scheduled_at": scheduled_at.isoformat(),
                "delay_seconds": delay,
            },
        ) from error
    return RetrySchedule(
        retry_number=normalized_retry_number,
        delay_seconds=delay,
        scheduled_at=scheduled_at,
        next_retry_at=next_retry_at,
        scheduled_monotonic=scheduled_monotonic,
        monotonic_deadline=monotonic_deadline,
        budget=consumed_budget,
    )


def _strategy_delay(strategy: BackoffStrategy, retry_number: int) -> float:
    try:
        raw_delay = strategy.delay_for(retry_number)
    except (NsStateError, NsValidationError):
        raise
    except Exception as error:
        raise NsStateError(
            "backoff strategy failed to calculate a delay.",
            details={
                "retry_number": retry_number,
                "strategy_type": type(strategy).__name__,
            },
        ) from error
    try:
        return _finite_number(
            raw_delay,
            field_name="backoff_delay_seconds",
            minimum=0.0,
        )
    except NsValidationError as error:
        raise NsStateError(
            "backoff strategy returned an invalid delay.",
            details={
                "retry_number": retry_number,
                "strategy_type": type(strategy).__name__,
                "value": raw_delay,
            },
        ) from error


def _utc_now(clock: Clock) -> datetime:
    value = clock.utc_now()
    if not isinstance(value, datetime):
        raise NsStateError(
            "clock.utc_now() must return a datetime.",
            details={
                "field": "clock.utc_now",
                "actual_type": type(value).__name__,
            },
        )
    try:
        offset = value.utcoffset()
    except Exception as error:
        raise NsStateError(
            "clock.utc_now() returned an invalid timezone.",
            details={"field": "clock.utc_now"},
        ) from error
    if value.tzinfo is None or offset is None:
        raise NsStateError(
            "clock.utc_now() must return a timezone-aware datetime.",
            details={"field": "clock.utc_now"},
        )
    return value.astimezone(timezone.utc)


NsBackoffStrategy = BackoffStrategy
NsFixedBackoff = FixedBackoff
NsExponentialBackoff = ExponentialBackoff
NsJitterBackoff = JitterBackoff
NsRetryBudget = RetryBudget
NsRetrySchedule = RetrySchedule


__all__ = [
    "BackoffStrategy",
    "DEFAULT_MAX_RETRIES",
    "ExponentialBackoff",
    "FixedBackoff",
    "JitterBackoff",
    "NsBackoffStrategy",
    "NsExponentialBackoff",
    "NsFixedBackoff",
    "NsJitterBackoff",
    "NsRetryBudget",
    "NsRetrySchedule",
    "RandomSource",
    "RetryBudget",
    "RetrySchedule",
    "schedule_next_retry",
]
