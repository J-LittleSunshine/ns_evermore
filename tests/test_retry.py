# -*- coding: utf-8 -*-
from __future__ import annotations

import math
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from ns_common.exceptions import NsStateError, NsValidationError
from ns_common.retry import (
    DEFAULT_MAX_RETRIES,
    BackoffStrategy,
    ExponentialBackoff,
    FixedBackoff,
    JitterBackoff,
    RetryBudget,
    schedule_next_retry,
)
from ns_common.time import ControlledClock


class BackoffStrategyTestCase(unittest.TestCase):

    def test_fixed_backoff_is_constant_and_implements_protocol(self) -> None:
        strategy = FixedBackoff(3)

        self.assertIsInstance(strategy, BackoffStrategy)
        self.assertEqual(3.0, strategy.delay_for(1))
        self.assertEqual(3.0, strategy.delay_for(1000))
        with self.assertRaises(FrozenInstanceError):
            strategy.delay_seconds = 4.0  # type: ignore[misc]

    def test_exponential_backoff_uses_one_based_retries_and_cap(self) -> None:
        strategy = ExponentialBackoff(1, 16)

        self.assertEqual(
            [1.0, 2.0, 4.0, 8.0, 16.0, 16.0],
            [strategy.delay_for(number) for number in range(1, 7)],
        )
        self.assertEqual(16.0, strategy.delay_for(1_000_000))

    def test_exponential_supports_zero_and_custom_multiplier(self) -> None:
        zero = ExponentialBackoff(0, 0)
        custom = ExponentialBackoff(0.5, 20, multiplier=3)

        self.assertEqual(0.0, zero.delay_for(100))
        self.assertEqual(
            [0.5, 1.5, 4.5, 13.5, 20.0],
            [custom.delay_for(number) for number in range(1, 6)],
        )

    def test_symmetric_jitter_is_deterministic(self) -> None:
        samples = iter((0.0, 0.5, 1.0))
        strategy = JitterBackoff(
            FixedBackoff(10),
            ratio=0.25,
            random_source=lambda: next(samples),
        )

        self.assertEqual(7.5, strategy.delay_for(1))
        self.assertEqual(10.0, strategy.delay_for(2))
        self.assertEqual(12.5, strategy.delay_for(3))

    def test_zero_delay_or_ratio_does_not_consume_randomness(self) -> None:
        def unexpected_randomness() -> float:
            raise AssertionError("random source must not be called")

        self.assertEqual(
            0.0,
            JitterBackoff(
                FixedBackoff(0),
                ratio=1,
                random_source=unexpected_randomness,
            ).delay_for(1),
        )
        self.assertEqual(
            10.0,
            JitterBackoff(
                FixedBackoff(10),
                ratio=0,
                random_source=unexpected_randomness,
            ).delay_for(1),
        )

    def test_configuration_and_retry_number_validation_is_strict(self) -> None:
        invalid_factories = (
            lambda: FixedBackoff(-1),
            lambda: FixedBackoff(math.inf),
            lambda: ExponentialBackoff(2, 1),
            lambda: ExponentialBackoff(1, 2, multiplier=0.5),
            lambda: JitterBackoff(FixedBackoff(1), ratio=-0.1),
            lambda: JitterBackoff(FixedBackoff(1), ratio=1.1),
            lambda: JitterBackoff(object(), ratio=0.1),  # type: ignore[arg-type]
        )
        for factory in invalid_factories:
            with self.subTest(factory=factory):
                with self.assertRaises(NsValidationError):
                    factory()

        for retry_number in (0, -1, True, 1.5):
            with self.subTest(retry_number=retry_number):
                with self.assertRaises(NsValidationError):
                    FixedBackoff(1).delay_for(retry_number)  # type: ignore[arg-type]

    def test_invalid_random_source_output_is_a_state_error(self) -> None:
        for sample in (-0.1, 1.1, math.nan, math.inf, True, "0.5"):
            with self.subTest(sample=sample):
                strategy = JitterBackoff(
                    FixedBackoff(1),
                    ratio=0.5,
                    random_source=lambda sample=sample: sample,  # type: ignore[return-value]
                )
                with self.assertRaises(NsStateError):
                    strategy.delay_for(1)


class RetryBudgetTestCase(unittest.TestCase):

    def test_default_budget_is_five_and_consumption_is_immutable(self) -> None:
        original = RetryBudget()
        consumed = original.consume(2)

        self.assertEqual(5, DEFAULT_MAX_RETRIES)
        self.assertEqual(5, original.remaining_retries)
        self.assertEqual(0, original.used_retries)
        self.assertEqual(2, consumed.used_retries)
        self.assertEqual(3, consumed.remaining_retries)
        self.assertFalse(consumed.exhausted)
        with self.assertRaises(FrozenInstanceError):
            consumed.used_retries = 3  # type: ignore[misc]

    def test_budget_exhaustion_has_probe_and_strict_paths(self) -> None:
        exhausted = RetryBudget(max_retries=2, used_retries=2)

        self.assertTrue(exhausted.exhausted)
        self.assertFalse(exhausted.can_consume())
        self.assertIsNone(exhausted.try_consume())
        with self.assertRaises(NsStateError) as context:
            exhausted.consume()
        self.assertEqual(
            "consume_retry_budget",
            context.exception.details["action"],
        )

    def test_budget_validation_rejects_invalid_snapshots_and_counts(self) -> None:
        invalid_budgets = (
            lambda: RetryBudget(max_retries=-1),
            lambda: RetryBudget(max_retries=True),
            lambda: RetryBudget(max_retries=1, used_retries=2),
            lambda: RetryBudget(max_retries=1, used_retries=0.5),  # type: ignore[arg-type]
        )
        for factory in invalid_budgets:
            with self.subTest(factory=factory):
                with self.assertRaises(NsValidationError):
                    factory()

        for count in (0, -1, True, 1.5):
            with self.subTest(count=count):
                with self.assertRaises(NsValidationError):
                    RetryBudget().try_consume(count)  # type: ignore[arg-type]


class RetrySchedulingTestCase(unittest.TestCase):

    def test_schedule_calculates_utc_and_monotonic_due_times(self) -> None:
        clock = ControlledClock(
            utc_start=datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc),
            monotonic_start=100,
        )
        strategy = ExponentialBackoff(1, 16)
        budget = RetryBudget()

        first = schedule_next_retry(
            strategy,
            budget,
            retry_number=1,
            clock=clock,
        )
        self.assertIsNotNone(first)
        assert first is not None
        self.assertEqual(1, first.retry_number)
        self.assertEqual(1.0, first.delay_seconds)
        self.assertEqual(101.0, first.monotonic_deadline)
        self.assertEqual(
            datetime(2026, 7, 16, 9, 0, 1, tzinfo=timezone.utc),
            first.next_retry_at,
        )
        self.assertEqual(1, first.budget.used_retries)
        self.assertEqual(0, budget.used_retries)

        second = schedule_next_retry(
            strategy,
            first.budget,
            retry_number=2,
            clock=clock,
        )
        self.assertIsNotNone(second)
        assert second is not None
        self.assertEqual(2, second.retry_number)
        self.assertEqual(2.0, second.delay_seconds)
        self.assertEqual(102.0, second.monotonic_deadline)

    def test_exhausted_budget_returns_no_schedule_or_strategy_call(self) -> None:
        class UnexpectedStrategy:
            def delay_for(self, retry_number: int) -> float:
                raise AssertionError("strategy must not be called")

        schedule = schedule_next_retry(
            UnexpectedStrategy(),
            RetryBudget(max_retries=0),
            retry_number=1,
            clock=ControlledClock(),
        )
        self.assertIsNone(schedule)

    def test_delivery_retry_number_is_independent_from_shared_budget(self) -> None:
        schedule = schedule_next_retry(
            ExponentialBackoff(1, 16),
            RetryBudget(max_retries=5, used_retries=3),
            retry_number=1,
            clock=ControlledClock(),
        )

        self.assertIsNotNone(schedule)
        assert schedule is not None
        self.assertEqual(1, schedule.retry_number)
        self.assertEqual(1.0, schedule.delay_seconds)
        self.assertEqual(4, schedule.budget.used_retries)

    def test_custom_invalid_strategy_output_is_rejected(self) -> None:
        class InvalidStrategy:
            def __init__(self, value: object) -> None:
                self.value = value

            def delay_for(self, retry_number: int) -> float:
                return self.value  # type: ignore[return-value]

        for value in (-1, math.nan, math.inf, True, "1"):
            with self.subTest(value=value):
                with self.assertRaises(NsStateError):
                    schedule_next_retry(
                        InvalidStrategy(value),
                        RetryBudget(max_retries=1),
                        retry_number=1,
                        clock=ControlledClock(),
                    )


if __name__ == "__main__":
    unittest.main()
