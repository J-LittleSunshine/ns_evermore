# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any, Mapping

from .codec import from_dict, load_config, save_config, to_dict
from .groups.backend import NsBackendConfig
from .groups.cache import NsCacheConfig
from .groups.logging import NsLogConfig
from .groups.runtime import NsRuntimeConfig
from .resolver import NsConfigResolver, create_validated_snapshot
from .validation import (
    config_groups,
    get_consistent_metadata_value,
    runtime_config_groups,
    validate_config,
)


_NS_CONFIG_UNSET = object()
_NS_CONFIG_LOCK = RLock()


@dataclass(frozen=True, slots=True, kw_only=True)
class NsConfig:
    backend: NsBackendConfig = field(default_factory=NsBackendConfig)
    cache: NsCacheConfig = field(default_factory=NsCacheConfig)
    log: NsLogConfig = field(default_factory=NsLogConfig)
    runtime: NsRuntimeConfig = field(default_factory=NsRuntimeConfig)

    _lock = RLock()

    @classmethod
    def load(
        cls,
        config_path: str | Path | None = None,
        *,
        environment: str | None = None,
        backend_override: Mapping[str, Any] | None = None,
        validated_snapshot: "NsConfig" | None = None,
        effective_at: datetime | str | None = None,
    ) -> "NsConfig":
        return load_config(
            cls,
            config_path,
            environment=environment,
            backend_override=backend_override,
            validated_snapshot=validated_snapshot,
            effective_at=effective_at,
        )

    @classmethod
    def resolve(
        cls,
        local_config: Mapping[str, Any],
        *,
        environment: str | None = None,
        backend_override: Mapping[str, Any] | None = None,
        validated_snapshot: "NsConfig" | None = None,
        effective_at: datetime | str | None = None,
    ) -> "NsConfig":
        resolver = NsConfigResolver(
            config_type=cls,
            environment=environment,
            effective_at=effective_at,
        )
        return resolver.resolve(
            local_config,
            backend_override=backend_override,
            validated_snapshot=validated_snapshot,
        )

    @classmethod
    def from_dict(
        cls,
        raw_config: Mapping[str, Any],
        *,
        environment: str | None = None,
    ) -> "NsConfig":
        return from_dict(cls, raw_config, environment=environment)

    def save(
        self,
        config_path: str | Path | None = None,
        *,
        environment: str | None = None,
    ) -> None:
        save_config(self, config_path, environment=environment)

    def to_dict(self) -> dict[str, Any]:
        return to_dict(self)

    def as_validated_snapshot(
        self,
        *,
        effective_at: datetime | str | None = None,
        environment: str | None = None,
    ) -> "NsConfig":
        return create_validated_snapshot(
            self,
            effective_at=effective_at,
            environment=environment,
        )

    @property
    def backend_config(self) -> NsBackendConfig:
        return self.backend

    @property
    def cache_config(self) -> NsCacheConfig:
        return self.cache

    @property
    def log_config(self) -> NsLogConfig:
        return self.log

    @property
    def runtime_config(self) -> NsRuntimeConfig:
        return self.runtime

    @property
    def config_version(self) -> str:
        return get_consistent_metadata_value(self, "config_version")

    @property
    def policy_version(self) -> str:
        return get_consistent_metadata_value(self, "policy_version")

    def validate(self, *, environment: str | None = None) -> None:
        validate_config(self, environment=environment)

    @staticmethod
    def _config_groups(config: "NsConfig") -> tuple[tuple[str, Any], ...]:
        """Compatibility view of the four root groups."""
        return config_groups(config)

    @staticmethod
    def _runtime_config_groups(runtime: NsRuntimeConfig) -> tuple[tuple[str, Any], ...]:
        """Compatibility view of the stable runtime subgroup order."""
        return runtime_config_groups(runtime)

def __getattr__(name: str) -> Any:
    """Lazily initialize the legacy global config on explicit access only."""

    if name != "ns_config":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    with _NS_CONFIG_LOCK:
        current = globals().get("ns_config", _NS_CONFIG_UNSET)
        if current is _NS_CONFIG_UNSET:
            current = NsConfig.load()
            globals()["ns_config"] = current
        return current
