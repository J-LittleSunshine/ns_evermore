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
from .store import (
    StateStore,
    StateStoreDeliveryRepositories,
    StateStoreRepository,
    StateStoreRepositoryRole,
)
from .authority import StateNamespace

if TYPE_CHECKING:
    from ns_common.config import NsRuntimeStateStoreConfig


class StateStoreComposition:
    """Composition-owned repository authority for one exact StateStore."""

    __slots__ = ("store", "__owner")

    def __init__(self, *, store: StateStore, owner: object) -> None:
        if not isinstance(store, StateStore) or owner is None:
            raise NsRuntimeStateStoreCapabilityUnavailableError(details={
                "component": "state_store_composition",
                "reason": "composition_authority_required",
            })
        self.store = store
        self.__owner = owner

    def delivery_repositories(
        self,
        *,
        runtime_id: str,
    ) -> StateStoreDeliveryRepositories:
        return StateStoreDeliveryRepositories(
            admission=self.store._create_repository(
                owner=self.__owner,
                role=StateStoreRepositoryRole.DELIVERY_ADMISSION,
                runtime_id=runtime_id,
            ),
            scheduler=self.store._create_repository(
                owner=self.__owner,
                role=StateStoreRepositoryRole.DELIVERY_SCHEDULER,
                runtime_id=runtime_id,
            ),
            payload=self.store._create_repository(
                owner=self.__owner,
                role=StateStoreRepositoryRole.DELIVERY_PAYLOAD,
                runtime_id=runtime_id,
            ),
            registry=self.store._create_repository(
                owner=self.__owner,
                role=StateStoreRepositoryRole.DELIVERY_REGISTRY,
                runtime_id=runtime_id,
            ),
        )

    def strong_audit_repository(
        self,
        *,
        namespace: StateNamespace,
    ) -> StateStoreRepository:
        return self.store._create_repository(
            owner=self.__owner,
            role=StateStoreRepositoryRole.STRONG_AUDIT,
            audit_namespace=namespace,
        )


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
    return _create_redis_valkey_provider(
        config=config,
        clock=clock,
        capabilities=capabilities,
    )


def create_state_store_composition(
    *,
    config: "NsRuntimeStateStoreConfig",
    clock: Clock,
    capabilities: StateStoreCapabilities | None = None,
) -> StateStoreComposition | None:
    """Build one provider and retain its repository capability in the root."""

    owner = object()
    store = _create_redis_valkey_provider(
        config=config,
        clock=clock,
        capabilities=capabilities,
        repository_owner=owner,
    )
    if store is None:
        return None
    return StateStoreComposition(store=store, owner=owner)


def _create_redis_valkey_provider(
    *,
    config: "NsRuntimeStateStoreConfig",
    clock: Clock,
    capabilities: StateStoreCapabilities | None,
    repository_owner: object | None = None,
) -> StateStore | None:
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
        _repository_owner=repository_owner,
    )


__all__ = (
    "StateStoreComposition",
    "create_state_store_composition",
    "create_state_store_provider",
)
