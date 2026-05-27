# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class RuntimeConfig:
    instance_id: str
    fixed_master_instance_id: str | None = None
    default_topic: str = "runtime.default"

    def __post_init__(self) -> None:
        if not self.instance_id.strip():
            raise ValueError("instance_id must be non-empty")
        if not self.default_topic.strip():
            raise ValueError("default_topic must be non-empty")

    @classmethod
    def create_default(cls) -> RuntimeConfig:
        return cls(instance_id=uuid4().hex)

