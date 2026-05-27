# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Mapping


@dataclass(frozen=True)
class RuntimeExtension:
    name: str
    extension_type: str
    provider: Any
    metadata: dict[str, Any] = field(default_factory=dict)


class RuntimeExtensionRegistry:
    def __init__(self) -> None:
        self._lock = RLock()
        self._extensions: dict[str, RuntimeExtension] = {}

    def register(self, extension: RuntimeExtension) -> RuntimeExtension:
        name = extension.name.strip()
        extension_type = extension.extension_type.strip()
        if not name:
            raise ValueError("extension name must be non-empty")
        if not extension_type:
            raise ValueError("extension_type must be non-empty")

        with self._lock:
            normalized = RuntimeExtension(
                name=name,
                extension_type=extension_type,
                provider=extension.provider,
                metadata=dict(extension.metadata),
            )
            self._extensions[name] = normalized
            return normalized

    def unregister(self, name: str) -> None:
        with self._lock:
            self._extensions.pop(name, None)

    def get(self, name: str) -> RuntimeExtension | None:
        with self._lock:
            return self._extensions.get(name)

    def list_all(self) -> tuple[RuntimeExtension, ...]:
        with self._lock:
            return tuple(self._extensions.values())

