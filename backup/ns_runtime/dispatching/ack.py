# -*- coding: utf-8 -*-
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from threading import RLock

from ns_common.protocol import RuntimePacket


class RuntimeTaskAckStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    TIMEOUT = "TIMEOUT"


@dataclass(frozen=True)
class RuntimeTaskPendingDispatch:
    # pending dispatch 表示 dispatcher 正在等待 executor accept_ack，不代表任务已经进入执行阶段。
    task_id: str
    executor_endpoint_id: str
    original_task_packet: RuntimePacket
    dispatch_packet: RuntimePacket
    dispatched_at: datetime
    deadline_at: datetime
    dispatch_attempts: int = 1

    def __post_init__(self) -> None:
        task_id_text = _validate_non_empty_text("task_id", self.task_id)
        executor_endpoint_id_text = _validate_non_empty_text("executor_endpoint_id", self.executor_endpoint_id)
        if not isinstance(self.dispatched_at, datetime):
            raise ValueError("dispatched_at must be datetime")
        if not isinstance(self.deadline_at, datetime):
            raise ValueError("deadline_at must be datetime")
        if self.deadline_at <= self.dispatched_at:
            raise ValueError("deadline_at must be greater than dispatched_at")
        if self.dispatch_attempts <= 0:
            raise ValueError("dispatch_attempts must be greater than 0")

        object.__setattr__(self, "task_id", task_id_text)
        object.__setattr__(self, "executor_endpoint_id", executor_endpoint_id_text)


class RuntimeTaskAckRegistry(ABC):
    @abstractmethod
    def register_pending(self, pending: RuntimeTaskPendingDispatch) -> RuntimeTaskPendingDispatch:
        raise NotImplementedError

    @abstractmethod
    def accept(self, task_id: str, executor_endpoint_id: str) -> RuntimeTaskPendingDispatch:
        raise NotImplementedError

    @abstractmethod
    def get(self, task_id: str) -> RuntimeTaskPendingDispatch | None:
        raise NotImplementedError

    @abstractmethod
    def remove(self, task_id: str) -> RuntimeTaskPendingDispatch | None:
        raise NotImplementedError

    @abstractmethod
    def list_pending(self) -> tuple[RuntimeTaskPendingDispatch, ...]:
        raise NotImplementedError

    @abstractmethod
    def list_expired(self, now: datetime | None = None) -> tuple[RuntimeTaskPendingDispatch, ...]:
        raise NotImplementedError


class MemoryTaskAckRegistry(RuntimeTaskAckRegistry):
    def __init__(self) -> None:
        self._lock = RLock()
        self._items: dict[str, RuntimeTaskPendingDispatch] = {}

    def register_pending(self, pending: RuntimeTaskPendingDispatch) -> RuntimeTaskPendingDispatch:
        with self._lock:
            self._items[pending.task_id] = pending
            return pending

    def accept(self, task_id: str, executor_endpoint_id: str) -> RuntimeTaskPendingDispatch:
        task_id_text = _validate_non_empty_text("task_id", task_id)
        executor_endpoint_id_text = _validate_non_empty_text("executor_endpoint_id", executor_endpoint_id)

        with self._lock:
            pending = self._items.get(task_id_text)
            if pending is None:
                raise KeyError(f"pending dispatch not found: {task_id_text}")
            if pending.executor_endpoint_id != executor_endpoint_id_text:
                raise ValueError(
                    "executor_endpoint_id does not match pending dispatch "
                    f"(expected={pending.executor_endpoint_id}, actual={executor_endpoint_id_text})"
                )
            self._items.pop(task_id_text, None)
            return pending

    def get(self, task_id: str) -> RuntimeTaskPendingDispatch | None:
        task_id_text = _validate_non_empty_text("task_id", task_id)
        with self._lock:
            return self._items.get(task_id_text)

    def remove(self, task_id: str) -> RuntimeTaskPendingDispatch | None:
        task_id_text = _validate_non_empty_text("task_id", task_id)
        with self._lock:
            return self._items.pop(task_id_text, None)

    def list_pending(self) -> tuple[RuntimeTaskPendingDispatch, ...]:
        with self._lock:
            pending_items: list[RuntimeTaskPendingDispatch] = list(self._items.values())
            return tuple(pending_items)

    def list_expired(self, now: datetime | None = None) -> tuple[RuntimeTaskPendingDispatch, ...]:
        check_now = now or datetime.now(timezone.utc)
        if not isinstance(check_now, datetime):
            raise ValueError("now must be datetime or None")

        with self._lock:
            expired = [item for item in self._items.values() if item.deadline_at <= check_now]
            return tuple(expired)


def _validate_non_empty_text(field_name: str, value: object) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text

