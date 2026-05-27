# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeInstance:
    instance_id: str


class MasterCoordinator:
    def __init__(self, instance_id: str, fixed_master_instance_id: str | None = None) -> None:
        normalized_instance_id = instance_id.strip()
        if not normalized_instance_id:
            raise ValueError("instance_id must be non-empty")

        normalized_fixed_master: str | None
        if fixed_master_instance_id is None:
            normalized_fixed_master = None
        else:
            fixed_text = fixed_master_instance_id.strip()
            normalized_fixed_master = fixed_text or None

        self._instance_id = normalized_instance_id
        self._fixed_master_instance_id = normalized_fixed_master

    def is_master(self) -> bool:
        if self._fixed_master_instance_id is None:
            return True
        return self._instance_id == self._fixed_master_instance_id

    def get_master_instance_id(self) -> str:
        if self._fixed_master_instance_id is None:
            return self._instance_id
        return self._fixed_master_instance_id

