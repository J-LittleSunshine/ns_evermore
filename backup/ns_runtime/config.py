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
        instance_id = self.instance_id.strip()
        default_topic = self.default_topic.strip()
        if self.fixed_master_instance_id is None:
            fixed_master_instance_id: str | None = None
        else:
            fixed_text = self.fixed_master_instance_id.strip()
            fixed_master_instance_id = fixed_text or None

        if not instance_id:
            raise ValueError("instance_id must be non-empty")
        if not default_topic:
            raise ValueError("default_topic must be non-empty")

        # frozen dataclass 初始化归一化：通过 object.__setattr__ 写回清洗后的字段值。
        object.__setattr__(self, "instance_id", instance_id)
        object.__setattr__(self, "fixed_master_instance_id", fixed_master_instance_id)
        object.__setattr__(self, "default_topic", default_topic)

    @classmethod
    def create_default(cls) -> RuntimeConfig:
        return cls(instance_id=uuid4().hex)

