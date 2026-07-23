# -*- coding: utf-8 -*-
"""Bounded event-loop lag sampling and internal metric snapshots."""

from __future__ import annotations

import asyncio
import math
from collections import deque
from dataclasses import dataclass, replace
from typing import Callable

from ns_common.async_runtime import NsEventLoopImplementation
from ns_common.exceptions import NsValidationError
from ns_common.observability import NsMetricKind, NsMetricRecord
from ns_runtime.context import RuntimeContext


DEFAULT_EVENT_LOOP_SAMPLE_INTERVAL_SECONDS = 1.0
DEFAULT_EVENT_LOOP_LAG_HISTORY_SIZE = 1024
EVENT_LOOP_MONITOR_TASK_NAME = "runtime.event_loop_monitor"

PendingTaskProbe = Callable[[asyncio.AbstractEventLoop], int]
ExecutorQueueDepthProbe = Callable[[asyncio.AbstractEventLoop], int]


@dataclass(frozen=True, slots=True)
class RuntimeEventLoopSnapshot:
    implementation: NsEventLoopImplementation
    latest_lag_ms: float
    lag_p95_ms: float
    lag_p99_ms: float
    sample_count: int
    slow_callback_count: int
    pending_task_count: int | None
    cancelled_task_count: int
    executor_queue_depth: int | None
    probe_failure_count: int
    metric_rejection_count: int


def _default_pending_task_probe(loop: asyncio.AbstractEventLoop) -> int:
    current = asyncio.current_task(loop=loop)
    return sum(
        1
        for task in asyncio.all_tasks(loop)
        if task is not current and not task.done()
    )


def _default_executor_queue_depth_probe(
    loop: asyncio.AbstractEventLoop,
) -> int:
    executor = getattr(loop, "_default_executor", None)
    if executor is None:
        return 0
    work_queue = getattr(executor, "_work_queue", None)
    qsize = getattr(work_queue, "qsize", None)
    if not callable(qsize):
        raise RuntimeError("default executor queue depth is unavailable")
    depth = qsize()
    if isinstance(depth, bool) or not isinstance(depth, int) or depth < 0:
        raise RuntimeError("default executor queue depth is invalid")
    return depth


def _nearest_rank_percentile(values: tuple[float, ...], percentile: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, math.ceil((percentile / 100) * len(ordered)) - 1)
    return ordered[index]


class RuntimeEventLoopMonitor:
    """Sample one running loop without owning sinks, threads, or exporters.

    A sample whose scheduling lag reaches the configured asyncio slow-callback
    threshold increments the bounded operational slow-callback counter.  This
    avoids parsing asyncio log text or installing a second logging handler.
    """

    def __init__(
        self,
        *,
        context: RuntimeContext,
        implementation: NsEventLoopImplementation,
        sample_interval_seconds: float = DEFAULT_EVENT_LOOP_SAMPLE_INTERVAL_SECONDS,
        history_size: int = DEFAULT_EVENT_LOOP_LAG_HISTORY_SIZE,
        pending_task_probe: PendingTaskProbe = _default_pending_task_probe,
        executor_queue_depth_probe: ExecutorQueueDepthProbe = (
            _default_executor_queue_depth_probe
        ),
    ) -> None:
        if not isinstance(context, RuntimeContext):
            raise NsValidationError(
                "Runtime event-loop monitor context is invalid.",
                details={
                    "component": "runtime_event_loop_monitor",
                    "dependency": "context",
                    "expected_type": "RuntimeContext",
                    "actual_type": type(context).__name__,
                },
            )
        if not isinstance(implementation, NsEventLoopImplementation):
            raise NsValidationError(
                "Runtime event-loop implementation is invalid.",
                details={
                    "component": "runtime_event_loop_monitor",
                    "field": "implementation",
                    "expected_type": "NsEventLoopImplementation",
                    "actual_type": type(implementation).__name__,
                },
            )
        if (
            isinstance(sample_interval_seconds, bool)
            or not isinstance(sample_interval_seconds, (int, float))
            or not math.isfinite(float(sample_interval_seconds))
            or float(sample_interval_seconds) <= 0
        ):
            raise NsValidationError(
                "Runtime event-loop sample interval is invalid.",
                details={
                    "component": "runtime_event_loop_monitor",
                    "field": "sample_interval_seconds",
                },
            )
        if (
            isinstance(history_size, bool)
            or not isinstance(history_size, int)
            or history_size <= 0
        ):
            raise NsValidationError(
                "Runtime event-loop lag history size is invalid.",
                details={
                    "component": "runtime_event_loop_monitor",
                    "field": "history_size",
                },
            )
        for field_name, probe in (
            ("pending_task_probe", pending_task_probe),
            ("executor_queue_depth_probe", executor_queue_depth_probe),
        ):
            if not callable(probe):
                raise NsValidationError(
                    "Runtime event-loop monitor probe is invalid.",
                    details={
                        "component": "runtime_event_loop_monitor",
                        "dependency": field_name,
                        "expected_type": "Callable",
                        "actual_type": type(probe).__name__,
                    },
                )

        self._context = context
        self._implementation = implementation
        self._sample_interval_seconds = float(sample_interval_seconds)
        self._lag_history: deque[float] = deque(maxlen=history_size)
        self._pending_task_probe = pending_task_probe
        self._executor_queue_depth_probe = executor_queue_depth_probe
        self._slow_callback_count = 0
        self._sample_count = 0
        self._probe_failure_count = 0
        self._metric_rejection_count = 0
        self._snapshot = RuntimeEventLoopSnapshot(
            implementation=implementation,
            latest_lag_ms=0.0,
            lag_p95_ms=0.0,
            lag_p99_ms=0.0,
            sample_count=0,
            slow_callback_count=0,
            pending_task_count=0,
            cancelled_task_count=0,
            executor_queue_depth=0,
            probe_failure_count=0,
            metric_rejection_count=0,
        )
        self._task: asyncio.Task[None] | None = None

    @property
    def context(self) -> RuntimeContext:
        return self._context

    @property
    def snapshot(self) -> RuntimeEventLoopSnapshot:
        return self._snapshot

    def start(self) -> asyncio.Task[None]:
        if self._task is not None:
            return self._task
        loop = asyncio.get_running_loop()
        loop.set_debug(self._context.config.runtime.event_loop.debug)
        loop.slow_callback_duration = (
            self._context.config.runtime.event_loop.slow_callback_threshold_ms
            / 1000.0
        )
        self._capture_sample(loop, lag_ms=0.0)
        self._task = self._context.task_supervisor.create_task(
            self._run(loop),
            name=EVENT_LOOP_MONITOR_TASK_NAME,
            cancel_order=900,
        )
        return self._task

    async def _run(self, loop: asyncio.AbstractEventLoop) -> None:
        expected = loop.time() + self._sample_interval_seconds
        while True:
            await asyncio.sleep(max(0.0, expected - loop.time()))
            observed = loop.time()
            lag_ms = max(0.0, (observed - expected) * 1000.0)
            self._capture_sample(loop, lag_ms=lag_ms)
            expected = observed + self._sample_interval_seconds

    def _capture_sample(
        self,
        loop: asyncio.AbstractEventLoop,
        *,
        lag_ms: float,
    ) -> RuntimeEventLoopSnapshot:
        normalized_lag = max(0.0, float(lag_ms))
        self._lag_history.append(normalized_lag)
        self._sample_count += 1
        if normalized_lag >= (
            self._context.config.runtime.event_loop.slow_callback_threshold_ms
        ):
            self._slow_callback_count += 1

        pending_tasks = self._safe_count(self._pending_task_probe, loop)
        executor_depth = self._safe_count(
            self._executor_queue_depth_probe,
            loop,
        )
        cancelled_tasks = self._context.task_supervisor.cancelled_task_count
        history = tuple(self._lag_history)
        snapshot = RuntimeEventLoopSnapshot(
            implementation=self._implementation,
            latest_lag_ms=normalized_lag,
            lag_p95_ms=_nearest_rank_percentile(history, 95),
            lag_p99_ms=_nearest_rank_percentile(history, 99),
            sample_count=self._sample_count,
            slow_callback_count=self._slow_callback_count,
            pending_task_count=pending_tasks,
            cancelled_task_count=cancelled_tasks,
            executor_queue_depth=executor_depth,
            probe_failure_count=self._probe_failure_count,
            metric_rejection_count=self._metric_rejection_count,
        )
        if self._context.config.runtime.observability.metrics_enabled:
            self._record_metrics(snapshot)
            snapshot = replace(
                snapshot,
                metric_rejection_count=self._metric_rejection_count,
            )
        self._snapshot = snapshot
        return snapshot

    def _safe_count(
        self,
        probe: Callable[[asyncio.AbstractEventLoop], int],
        loop: asyncio.AbstractEventLoop,
    ) -> int | None:
        try:
            value = probe(loop)
        except Exception:
            self._probe_failure_count += 1
            return None
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            self._probe_failure_count += 1
            return None
        return value

    def _record_metrics(self, snapshot: RuntimeEventLoopSnapshot) -> None:
        records: list[
            tuple[str, NsMetricKind, float, str | None, dict[str, str]],
        ] = [
            (
                "runtime_event_loop_implementation",
                NsMetricKind.GAUGE,
                1.0,
                None,
                {"implementation": snapshot.implementation.value},
            ),
            (
                "runtime_event_loop_lag_ms",
                NsMetricKind.HISTOGRAM,
                snapshot.latest_lag_ms,
                "ms",
                {},
            ),
            (
                "runtime_event_loop_lag_p95_ms",
                NsMetricKind.GAUGE,
                snapshot.lag_p95_ms,
                "ms",
                {},
            ),
            (
                "runtime_event_loop_lag_p99_ms",
                NsMetricKind.GAUGE,
                snapshot.lag_p99_ms,
                "ms",
                {},
            ),
            (
                "runtime_slow_callback_total",
                NsMetricKind.COUNTER,
                float(snapshot.slow_callback_count),
                None,
                {},
            ),
            (
                "runtime_cancelled_task_total",
                NsMetricKind.COUNTER,
                float(snapshot.cancelled_task_count),
                None,
                {},
            ),
        ]
        if snapshot.pending_task_count is not None:
            records.insert(5, (
                "runtime_pending_task_count",
                NsMetricKind.GAUGE,
                float(snapshot.pending_task_count),
                None,
                {"component_type": "runtime"},
            ))
        if snapshot.executor_queue_depth is not None:
            records.append((
                "runtime_executor_queue_depth",
                NsMetricKind.GAUGE,
                float(snapshot.executor_queue_depth),
                None,
                {},
            ))
        try:
            observed_at = self._context.clock.utc_now()
        except Exception:
            self._metric_rejection_count += len(records)
            return
        for name, kind, value, unit, attributes in records:
            try:
                accepted = self._context.metrics.record(
                    NsMetricRecord(
                        name=name,
                        kind=kind,
                        value=value,
                        observed_at=observed_at,
                        unit=unit,
                        attributes=attributes,
                    ),
                )
            except Exception:
                self._metric_rejection_count += 1
            else:
                if not accepted:
                    self._metric_rejection_count += 1


__all__ = [
    "DEFAULT_EVENT_LOOP_LAG_HISTORY_SIZE",
    "DEFAULT_EVENT_LOOP_SAMPLE_INTERVAL_SECONDS",
    "EVENT_LOOP_MONITOR_TASK_NAME",
    "RuntimeEventLoopMonitor",
    "RuntimeEventLoopSnapshot",
]
