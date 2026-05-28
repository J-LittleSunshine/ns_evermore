# -*- coding: utf-8 -*-
from __future__ import annotations

from threading import RLock
from typing import Callable, Mapping, Any

from ns_common.protocol import RuntimeTask

RuntimeTaskHandler = Callable[[RuntimeTask], Mapping[str, Any] | None]


class TaskHandlerRegistry:
    def __init__(self) -> None:
        self._lock = RLock()
        self._handlers: dict[str, RuntimeTaskHandler] = {}

    def register(self, task_type: str, handler: RuntimeTaskHandler) -> None:
        task_type_text = self._validate_task_type(task_type)
        if not callable(handler):
            raise ValueError("handler must be callable")
        with self._lock:
            self._handlers[task_type_text] = handler

    def unregister(self, task_type: str) -> None:
        task_type_text = self._validate_task_type(task_type)
        with self._lock:
            self._handlers.pop(task_type_text, None)

    def get(self, task_type: str) -> RuntimeTaskHandler | None:
        task_type_text = self._validate_task_type(task_type)
        with self._lock:
            return self._handlers.get(task_type_text)

    def list_task_types(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(self._handlers.keys())

    def handle(self, task: RuntimeTask) -> Mapping[str, Any] | None:
        # handler 只保留在主执行进程内，避免跨进程传递不可 pickle 的函数对象。
        handler = self.get(task.task_type)
        if handler is None:
            raise KeyError(f"handler not found for task_type: {task.task_type}")
        return handler(task)

    @staticmethod
    def _validate_task_type(task_type: str) -> str:
        task_type_text = str(task_type).strip()
        if not task_type_text:
            raise ValueError("task_type must be non-empty")
        return task_type_text

