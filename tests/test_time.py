# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import unittest
from datetime import (
    datetime,
    timedelta,
    timezone,
)

from ns_common.exceptions import (
    NsStateError,
    NsValidationError,
)
from ns_common.time import (
    Clock,
    ControlledClock,
    SystemClock,
    UTC_EPOCH,
)


class ClockTestCase(unittest.TestCase):

    def test_system_and_controlled_clocks_implement_protocol(self) -> None:
        self.assertIsInstance(SystemClock(), Clock)
        self.assertIsInstance(ControlledClock(), Clock)

    def test_system_clock_returns_utc_and_monotonic_time(self) -> None:
        clock = SystemClock()
        before = clock.monotonic()
        now = clock.utc_now()
        after = clock.monotonic()

        self.assertIs(timezone.utc, now.tzinfo)
        self.assertEqual(timedelta(0), now.utcoffset())
        self.assertLessEqual(before, after)

    def test_controlled_clock_normalizes_utc_and_keeps_wall_clock_separate(self) -> None:
        local_start = datetime(
            2026,
            7,
            16,
            16,
            0,
            tzinfo=timezone(timedelta(hours=8)),
        )
        clock = ControlledClock(
            utc_start=local_start,
            monotonic_start=10.0,
        )

        self.assertEqual(
            datetime(2026, 7, 16, 8, 0, tzinfo=timezone.utc),
            clock.utc_now(),
        )
        self.assertEqual(10.0, clock.monotonic())

        self.assertEqual(0, clock.advance(2.5))
        self.assertEqual(
            datetime(2026, 7, 16, 8, 0, 2, 500000, tzinfo=timezone.utc),
            clock.utc_now(),
        )
        self.assertEqual(12.5, clock.monotonic())

        clock.set_utc(datetime(2000, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(
            datetime(2000, 1, 1, tzinfo=timezone.utc),
            clock.utc_now(),
        )
        self.assertEqual(12.5, clock.monotonic())

    def test_controlled_clock_validation_and_overflow_are_atomic(self) -> None:
        with self.assertRaises(NsValidationError):
            ControlledClock(utc_start=datetime(2026, 7, 16))
        with self.assertRaises(NsValidationError):
            ControlledClock(monotonic_start=float("inf"))

        clock = ControlledClock()
        for value in (-1, True, float("inf"), "1"):
            with self.subTest(value=value):
                with self.assertRaises(NsValidationError):
                    clock.advance(value)  # type: ignore[arg-type]
        with self.assertRaises(NsValidationError):
            clock.set_utc(datetime(2026, 7, 16))

        near_limit = ControlledClock(
            utc_start=datetime.max.replace(tzinfo=timezone.utc),
            monotonic_start=5.0,
        )
        with self.assertRaises(NsValidationError):
            near_limit.advance(1.0)
        self.assertEqual(
            datetime.max.replace(tzinfo=timezone.utc),
            near_limit.utc_now(),
        )
        self.assertEqual(5.0, near_limit.monotonic())

    def test_default_controlled_clock_is_deterministic(self) -> None:
        clock = ControlledClock()
        self.assertEqual(UTC_EPOCH, clock.utc_now())
        self.assertEqual(0.0, clock.monotonic())
        self.assertEqual(0, clock.pending_sleep_count)


class AsyncClockTestCase(unittest.IsolatedAsyncioTestCase):

    async def test_system_clock_sleep_validates_duration(self) -> None:
        clock = SystemClock()
        await clock.sleep(0)

        for value in (-1, True, float("nan")):
            with self.subTest(value=value):
                with self.assertRaises(NsValidationError):
                    await clock.sleep(value)  # type: ignore[arg-type]

    async def test_controlled_sleep_requires_explicit_advance(self) -> None:
        clock = ControlledClock()
        sleeper = asyncio.create_task(clock.sleep(5.0))
        await asyncio.sleep(0)

        self.assertEqual(1, clock.pending_sleep_count)
        self.assertFalse(sleeper.done())
        self.assertEqual(0, clock.advance(4.5))
        await asyncio.sleep(0)
        self.assertFalse(sleeper.done())

        self.assertEqual(1, clock.advance(0.5))
        await sleeper
        self.assertEqual(5.0, clock.monotonic())
        self.assertEqual(0, clock.pending_sleep_count)

    async def test_concurrent_sleepers_wake_by_deadline_and_registration(self) -> None:
        clock = ControlledClock()
        wake_order: list[str] = []

        async def sleeper(name: str, delay: float) -> None:
            await clock.sleep(delay)
            wake_order.append(name)

        tasks = [
            asyncio.create_task(sleeper("late", 10.0)),
            asyncio.create_task(sleeper("same-first", 5.0)),
            asyncio.create_task(sleeper("early", 2.0)),
            asyncio.create_task(sleeper("same-second", 5.0)),
        ]
        await asyncio.sleep(0)

        self.assertEqual(1, clock.advance(2.0))
        await asyncio.sleep(0)
        self.assertEqual(["early"], wake_order)

        self.assertEqual(2, clock.advance(3.0))
        await asyncio.sleep(0)
        self.assertEqual(
            ["early", "same-first", "same-second"],
            wake_order,
        )

        self.assertEqual(1, clock.advance(5.0))
        await asyncio.gather(*tasks)
        self.assertEqual(
            ["early", "same-first", "same-second", "late"],
            wake_order,
        )
        self.assertEqual(0, clock.pending_sleep_count)

    async def test_cancelled_sleep_is_removed_without_advancing(self) -> None:
        clock = ControlledClock()
        sleeper = asyncio.create_task(clock.sleep(10.0))
        await asyncio.sleep(0)
        self.assertEqual(1, clock.pending_sleep_count)

        sleeper.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await sleeper

        self.assertEqual(0, clock.pending_sleep_count)
        self.assertEqual(0.0, clock.monotonic())

    async def test_zero_sleep_yields_without_registering_waiter(self) -> None:
        clock = ControlledClock()
        await clock.sleep(0)
        self.assertEqual(0, clock.pending_sleep_count)
        self.assertEqual(0.0, clock.monotonic())

        clock = ControlledClock(monotonic_start=1e308)
        with self.assertRaises(NsValidationError):
            await clock.sleep(1e308)
        self.assertEqual(0, clock.pending_sleep_count)


class ControlledClockLoopBindingTestCase(unittest.TestCase):

    def test_controlled_clock_cannot_cross_event_loops(self) -> None:
        clock = ControlledClock()
        asyncio.run(clock.sleep(0))

        async def sleep_on_second_loop() -> None:
            with self.assertRaises(NsStateError):
                await clock.sleep(0)

        asyncio.run(sleep_on_second_loop())


if __name__ == "__main__":
    unittest.main()
