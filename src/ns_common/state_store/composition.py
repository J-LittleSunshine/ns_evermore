# -*- coding: utf-8 -*-
"""Explicit composition boundary for production StateStore providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ns_common.exceptions import NsRuntimeStateStoreCapabilityUnavailableError
from ns_common.time import Clock

from .authority import StateStoreCapabilities
from .redis_provider import (
    RedisStateStoreOptions,
    RedisValkeyStateStore,
    password_source_from_reference,
)
from .store import StateStore

if TYPE_CHECKING:
    from ns_common.config import NsRuntimeStateStoreConfig


def create_state_store_provider(
    *,
    config: "NsRuntimeStateStoreConfig",
    clock: Clock,
    capabilities: StateStoreCapabilities | None = None,
) -> StateStore | None:
    """Build a configured provider without opening it or creating another owner."""

    from ns_common.config import NsRuntimeStateStoreConfig

    if not isinstance(config, NsRuntimeStateStoreConfig):
        raise NsRuntimeStateStoreCapabilityUnavailableError(
            details={
                "component": "state_store_composition",
                "reason": "typed_config_required",
            },
        )
    if config.backend == "sqlite":
        return None
    if config.backend not in {"redis", "valkey"}:
        raise NsRuntimeStateStoreCapabilityUnavailableError(
            details={
                "component": "state_store_composition",
                "reason": "provider_unavailable",
            },
        )
    return RedisValkeyStateStore(
        options=RedisStateStoreOptions(
            backend=config.backend,
            endpoint=config.resolved_endpoint,
            username=config.username,
            password_source=password_source_from_reference(
                config.password_source,
            ),
            namespace=config.namespace,
            operation_timeout_seconds=config.operation_timeout_seconds,
        ),
        capabilities=capabilities or StateStoreCapabilities.p10_contract(),
        clock=clock,
    )


__all__ = ("create_state_store_provider",)
