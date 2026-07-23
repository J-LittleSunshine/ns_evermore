# -*- coding: utf-8 -*-
"""Typed in-process notification bus; never a state authority."""

from __future__ import annotations

import asyncio
import math
import re
from dataclasses import dataclass
from enum import Enum
from typing import Awaitable, Callable, Generic, TypeVar

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import NsValidationError

from .contracts import ProcessorSafeSummary, ProcessorTraceReference


@dataclass(frozen=True, slots=True, kw_only=True)
class RuntimeEvent:
    object_id: str
    safe_summary: ProcessorSafeSummary
    trace_reference: ProcessorTraceReference

    def __post_init__(self) -> None:
        if (
            not isinstance(self.object_id, str)
            or not self.object_id
            or len(self.object_id) > 512
            or any(character.isspace() for character in self.object_id)
        ):
            _invalid("event.object_id")
        if not isinstance(self.safe_summary, ProcessorSafeSummary):
            _invalid("event.safe_summary")
        if not isinstance(self.trace_reference, ProcessorTraceReference):
            _invalid("event.trace_reference")


EventT = TypeVar("EventT", bound=RuntimeEvent)
EventSubscriber = Callable[[EventT], Awaitable[None]]


class SubscriberOutcome(str, Enum):
    SUCCEEDED = "succeeded"
    TIMED_OUT = "timed_out"
    FAILED = "failed"


class UnsubscribeOutcome(str, Enum):
    REMOVED = "removed"
    NOT_FOUND = "not_found"


@dataclass(frozen=True, slots=True, kw_only=True)
class SubscriptionHandle:
    subscription_id: int
    subscriber: str
    event_type: str

    def __post_init__(self) -> None:
        if (
            isinstance(self.subscription_id, bool)
            or not isinstance(self.subscription_id, int)
            or self.subscription_id <= 0
        ):
            _invalid("subscription_handle.subscription_id")
        _subscriber_name(self.subscriber, "subscription_handle.subscriber")
        if not isinstance(self.event_type, str) or not self.event_type:
            _invalid("subscription_handle.event_type")


@dataclass(frozen=True, slots=True, kw_only=True)
class SubscriberResult:
    subscriber: str
    outcome: SubscriberOutcome


@dataclass(frozen=True, slots=True, kw_only=True)
class EventPublishReport:
    event_type: str
    results: tuple[SubscriberResult, ...]

    @property
    def succeeded_count(self) -> int:
        return sum(item.outcome is SubscriberOutcome.SUCCEEDED for item in self.results)


@dataclass(frozen=True, slots=True)
class _Subscription(Generic[EventT]):
    handle: SubscriptionHandle
    event_type: type[EventT]
    subscriber: EventSubscriber[EventT]
    name: str
    timeout_seconds: float


class EventBus:
    """Instance-owned best-effort notification bus using the runtime supervisor."""

    def __init__(self, *, task_supervisor: TaskSupervisor, default_timeout_seconds: float) -> None:
        if not isinstance(task_supervisor, TaskSupervisor):
            _invalid("task_supervisor")
        _timeout(default_timeout_seconds, "default_timeout_seconds")
        self._supervisor = task_supervisor
        self._default_timeout = float(default_timeout_seconds)
        self._subscriptions: dict[int, _Subscription[RuntimeEvent]] = {}
        self._subscription_sequence = 0
        self._sequence = 0

    @property
    def subscription_count(self) -> int:
        return len(self._subscriptions)

    def subscribe(
        self,
        event_type: type[EventT],
        subscriber: EventSubscriber[EventT],
        *,
        name: str,
        timeout_seconds: float | None = None,
    ) -> SubscriptionHandle:
        if not isinstance(event_type, type) or not issubclass(event_type, RuntimeEvent):
            _invalid("event_type")
        if not callable(subscriber):
            _invalid("subscriber")
        _subscriber_name(name, "subscriber.name")
        timeout = self._default_timeout if timeout_seconds is None else timeout_seconds
        _timeout(timeout, "subscriber.timeout_seconds")
        if any(
            item.event_type is event_type and item.name == name
            for item in self._subscriptions.values()
        ):
            _invalid("subscriber.duplicate")
        self._subscription_sequence += 1
        handle = SubscriptionHandle(
            subscription_id=self._subscription_sequence,
            subscriber=name,
            event_type=event_type.__name__,
        )
        self._subscriptions[handle.subscription_id] = _Subscription(
            handle=handle,
            event_type=event_type,
            subscriber=subscriber,
            name=name,
            timeout_seconds=float(timeout),
        )
        return handle

    def unsubscribe(
        self,
        handle: SubscriptionHandle,
    ) -> UnsubscribeOutcome:
        if not isinstance(handle, SubscriptionHandle):
            _invalid("subscription_handle")
        subscription = self._subscriptions.get(handle.subscription_id)
        if subscription is None or subscription.handle is not handle:
            return UnsubscribeOutcome.NOT_FOUND
        del self._subscriptions[handle.subscription_id]
        return UnsubscribeOutcome.REMOVED

    async def publish(self, event: RuntimeEvent) -> EventPublishReport:
        if not isinstance(event, RuntimeEvent):
            _invalid("event")
        subscriptions = tuple(
            item
            for item in self._subscriptions.values()
            if isinstance(event, item.event_type)
        )
        if not subscriptions:
            return EventPublishReport(event_type=type(event).__name__, results=())
        tasks: list[asyncio.Task[SubscriberResult]] = []
        deadlines: dict[asyncio.Task[SubscriberResult], float] = {}
        positions: dict[asyncio.Task[SubscriberResult], int] = {}
        try:
            loop = asyncio.get_running_loop()
            for position, subscription in enumerate(subscriptions):
                self._sequence += 1
                task = self._supervisor.create_task(
                    self._invoke(subscription, event),
                    name=f"event-subscriber-{self._sequence}-{subscription.name}",
                    cancel_order=80,
                )
                tasks.append(task)
                positions[task] = position
                deadlines[task] = loop.time() + subscription.timeout_seconds
            results_by_position: dict[int, SubscriberResult] = {}
            pending = set(tasks)
            while pending:
                completed_now = tuple(task for task in pending if task.done())
                for task in completed_now:
                    pending.remove(task)
                    results_by_position[positions[task]] = task.result()
                if not pending:
                    break
                now = loop.time()
                expired = tuple(task for task in pending if deadlines[task] <= now)
                for task in expired:
                    task.cancel()
                    pending.remove(task)
                    subscription = subscriptions[positions[task]]
                    results_by_position[positions[task]] = SubscriberResult(
                        subscriber=subscription.name,
                        outcome=SubscriberOutcome.TIMED_OUT,
                    )
                if not pending:
                    break
                timeout = max(0.0, min(deadlines[task] for task in pending) - loop.time())
                done, _ = await asyncio.wait(
                    pending,
                    timeout=timeout,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in done:
                    pending.remove(task)
                    results_by_position[positions[task]] = task.result()
            await asyncio.gather(*tasks, return_exceptions=True)
        except asyncio.CancelledError:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise
        return EventPublishReport(
            event_type=type(event).__name__,
            results=tuple(
                results_by_position[position]
                for position in range(len(subscriptions))
            ),
        )

    async def _invoke(
        self,
        subscription: _Subscription[RuntimeEvent],
        event: RuntimeEvent,
    ) -> SubscriberResult:
        try:
            await subscription.subscriber(event)
        except asyncio.CancelledError:
            raise
        except Exception:
            return SubscriberResult(
                subscriber=subscription.name,
                outcome=SubscriberOutcome.FAILED,
            )
        return SubscriberResult(
            subscriber=subscription.name,
            outcome=SubscriberOutcome.SUCCEEDED,
        )


def _timeout(value: object, field_name: str) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or float(value) <= 0
    ):
        _invalid(field_name)


def _subscriber_name(value: object, field_name: str) -> None:
    if (
        not isinstance(value, str)
        or re.fullmatch(r"[a-z][a-z0-9_.-]{0,127}", value) is None
    ):
        _invalid(field_name)


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "EventBus value is invalid.",
        details={"component": "event_bus", "field": field_name},
    )


__all__ = (
    "EventBus",
    "EventPublishReport",
    "RuntimeEvent",
    "SubscriptionHandle",
    "SubscriberOutcome",
    "SubscriberResult",
    "UnsubscribeOutcome",
)
