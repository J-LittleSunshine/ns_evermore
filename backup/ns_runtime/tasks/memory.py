# -*- coding: utf-8 -*-
from __future__ import annotations

from threading import RLock

from ns_common.protocol import RuntimeTask, RuntimeTaskStatus
from ns_runtime.tasks.store import RuntimeTaskStore


class MemoryTaskStore(RuntimeTaskStore):
    def __init__(self) -> None:
        self._lock = RLock()
        self._tasks: dict[str, RuntimeTask] = {}

    def save(self, task: RuntimeTask) -> RuntimeTask:
        with self._lock:
            self._tasks[task.task_id] = task
            return task

    def get(self, task_id: str) -> RuntimeTask | None:
        task_id_text = self.validate_task_id(task_id)
        with self._lock:
            return self._tasks.get(task_id_text)

    def update_status(self, task_id: str, status: RuntimeTaskStatus) -> RuntimeTask:
        task_id_text = self.validate_task_id(task_id)
        with self._lock:
            existing = self._tasks.get(task_id_text)
            if existing is None:
                raise KeyError(f"task not found: {task_id_text}")
            updated = existing.with_status(status)
            self._tasks[task_id_text] = updated
            return updated

    def list_all(self) -> tuple[RuntimeTask, ...]:
        with self._lock:
            return tuple(self._tasks.values())

