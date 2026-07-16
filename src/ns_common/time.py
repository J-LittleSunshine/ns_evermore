# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import heapq
import math
import time as time_module
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from typing import (
    Any,
    Protocol,
    runtime_checkable,
)

from ns_common.exceptions import (
    NsStateError,
    NsValidationError,
)


UTC_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _normalize_utc(value: Any, *, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise NsValidationError(
            f"{field_name} must be a datetime.",
            details={
                "field": field_name,
                "value": value,
                "actual_type": type(value).__name__,
            },
        )

    try:
        offset = value.utcoffset()
    except Exception as error:
        raise NsValidationError(
            f"{field_name} must have a valid timezone.",
            details={
                "field": field_name,
                "value": value,
            },
        ) from error

    if value.tzinfo is None or offset is None:
        raise NsValidationError(
            f"{field_name} must be timezone-aware.",
            details={
                "field": field_name,
                "value": value,
            },
        )

    return value.astimezone(timezone.utc)


def _validate_finite_number(
    value: Any,
    *,
    field_name: str,
    minimum: float | None = None,
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
    if not math.isfinite(normalized) or (
        minimum is not None and normalized < minimum
    ):
        raise NsValidationError(
            f"{field_name} is outside the allowed range.",
            details={
                "field": field_name,
                "value": value,
                "minimum": minimum,
            },
        )

    return normalized


@runtime_checkable
class Clock(Protocol):
    """Explicit time dependency for runtime components."""

    def utc_now(self) -> datetime:
        """Return a timezone-aware UTC wall-clock timestamp."""

    def monotonic(self) -> float:
        """Return monotonic seconds for deadlines and elapsed durations."""

    async def sleep(self, delay_seconds: float) -> None:
        """Wait for a non-negative duration using this clock."""


class SystemClock:
    """Clock backed by the operating system and the active event loop."""

    __slots__ = ()

    def utc_now(self) -> datetime:
        return datetime.now(timezone.utc)

    def monotonic(self) -> float:
        return time_module.monotonic()

    async def sleep(self, delay_seconds: float) -> None:
        delay = _validate_finite_number(
            delay_seconds,
            field_name="delay_seconds",
            minimum=0.0,
        )
        await asyncio.sleep(delay)


class ControlledClock:
    """Manually advanced clock for deterministic asynchronous tests.

    ``sleep()`` never advances time by itself. A test explicitly calls
    ``advance()``; every waiter whose monotonic deadline is due is then
    released in deadline and registration order.
    """

    def __init__(
        self,
        *,
        utc_start: datetime = UTC_EPOCH,
        monotonic_start: float = 0.0,
    ) -> None:
        self._utc_now = _normalize_utc(
            utc_start,
            field_name="utc_start",
        )
        self._monotonic = _validate_finite_number(
            monotonic_start,
            field_name="monotonic_start",
        )
        self._sleep_loop: asyncio.AbstractEventLoop | None = None
        self._sleep_waiters: list[
            tuple[float, int, asyncio.Future[None]]
        ] = []
        self._waiter_sequence = 0

    @property
    def pending_sleep_count(self) -> int:
        return sum(
            1
            for _, _, future in self._sleep_waiters
            if not future.done()
        )

    def utc_now(self) -> datetime:
        return self._utc_now

    def monotonic(self) -> float:
        return self._monotonic

    def set_utc(self, value: datetime) -> None:
        self._utc_now = _normalize_utc(
            value,
            field_name="utc_now",
        )

    def advance(self, seconds: float) -> int:
        delta = _validate_finite_number(
            seconds,
            field_name="advance_seconds",
            minimum=0.0,
        )
        self._validate_advance_context()

        next_monotonic = self._monotonic + delta
        if not math.isfinite(next_monotonic):
            raise NsValidationError(
                "advance_seconds exceeds the monotonic clock range.",
                details={
                    "field": "advance_seconds",
                    "value": seconds,
                },
            )

        try:
            next_utc = self._utc_now + timedelta(seconds=delta)
        except (OverflowError, ValueError) as error:
            raise NsValidationError(
                "advance_seconds exceeds the UTC clock range.",
                details={
                    "field": "advance_seconds",
                    "value": seconds,
                },
            ) from error

        self._monotonic = next_monotonic
        self._utc_now = next_utc
        return self._release_due_sleepers()

    async def sleep(self, delay_seconds: float) -> None:
        delay = _validate_finite_number(
            delay_seconds,
            field_name="delay_seconds",
            minimum=0.0,
        )
        loop = asyncio.get_running_loop()
        self._bind_sleep_loop(loop)

        if delay == 0.0:
            await asyncio.sleep(0)
            return

        deadline = self._monotonic + delay
        if not math.isfinite(deadline):
            raise NsValidationError(
                "delay_seconds exceeds the monotonic clock range.",
                details={
                    "field": "delay_seconds",
                    "value": delay_seconds,
                },
            )

        future: asyncio.Future[None] = loop.create_future()
        waiter = (
            deadline,
            self._waiter_sequence,
            future,
        )
        self._waiter_sequence += 1
        heapq.heappush(self._sleep_waiters, waiter)

        try:
            await future
        finally:
            self._remove_waiter(future)

    def _bind_sleep_loop(
        self,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        if self._sleep_loop is None:
            self._sleep_loop = loop
            return
        if self._sleep_loop is not loop:
            raise NsStateError(
                "ControlledClock cannot be shared across event loops.",
                details={"action": "sleep"},
            )

    def _validate_advance_context(self) -> None:
        if self.pending_sleep_count == 0:
            return

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError as error:
            raise NsStateError(
                "ControlledClock with pending sleepers must advance on its event loop.",
                details={"action": "advance"},
            ) from error

        if loop is not self._sleep_loop:
            raise NsStateError(
                "ControlledClock with pending sleepers must advance on its event loop.",
                details={"action": "advance"},
            )

    def _release_due_sleepers(self) -> int:
        released = 0
        while self._sleep_waiters:
            deadline, _, future = self._sleep_waiters[0]
            if future.done():
                heapq.heappop(self._sleep_waiters)
                continue
            if deadline > self._monotonic:
                break

            heapq.heappop(self._sleep_waiters)
            future.set_result(None)
            released += 1

        return released

    def _remove_waiter(self, target: asyncio.Future[None]) -> None:
        if not any(
            future is target
            for _, _, future in self._sleep_waiters
        ):
            return

        self._sleep_waiters = [
            waiter
            for waiter in self._sleep_waiters
            if waiter[2] is not target
        ]
        heapq.heapify(self._sleep_waiters)


NsClock = Clock
NsSystemClock = SystemClock
NsControlledClock = ControlledClock


__all__ = [
    "Clock",
    "ControlledClock",
    "NsClock",
    "NsControlledClock",
    "NsSystemClock",
    "SystemClock",
    "UTC_EPOCH",
]
