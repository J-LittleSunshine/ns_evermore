# -*- coding: utf-8 -*-
from __future__ import annotations

from abc import ABC, abstractmethod

from ns_common.protocol import RuntimeTask, RuntimeTaskStatus


class RuntimeTaskStore(ABC):
    @abstractmethod
    def save(self, task: RuntimeTask) -> RuntimeTask:
        raise NotImplementedError

    @abstractmethod
    def get(self, task_id: str) -> RuntimeTask | None:
        raise NotImplementedError

    @abstractmethod
    def update_status(self, task_id: str, status: RuntimeTaskStatus) -> RuntimeTask:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> tuple[RuntimeTask, ...]:
        raise NotImplementedError

    @staticmethod
    def validate_task_id(task_id: str) -> str:
        task_id_text = str(task_id).strip()
        if not task_id_text:
            raise ValueError("task_id must be non-empty")
        return task_id_text

