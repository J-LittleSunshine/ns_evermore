# -*- coding: utf-8 -*-
"""Explicit composition boundary for production StateStore providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ns_common.exceptions import NsRuntimeStateStoreCapabilityUnavailableError
from ns_common.time import Clock

from .authority import (
    StateAuthorityKind,
    StateCallerCapability,
    StateNamespace,
    StateNamespaceKind,
    StateStoreCapabilities,
)
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
    _ProductionStateScopeValidator,
)

if TYPE_CHECKING:
    from ns_common.config import NsRuntimeStateStoreConfig


class StateStoreComposition:
    """Closed repository set; it contains no repository creation capability."""

    __slots__ = ("store", "_delivery", "_runtime_id", "_audit", "_lease")

    def __init__(self, *args: object, **kwargs: object) -> None:
        del self, args, kwargs
        raise NsRuntimeStateStoreCapabilityUnavailableError(details={
            "component": "state_store_composition",
            "reason": "composition_authority_required",
        })

    def delivery_repositories(
        self,
        *,
        runtime_id: str,
    ) -> StateStoreDeliveryRepositories:
        if (
            type(runtime_id) is not str
            or not runtime_id
            or runtime_id != self._runtime_id
            or self._delivery is None
        ):
            _unavailable("delivery_repository_set_unavailable")
        return self._delivery

    def strong_audit_repository(
        self,
        *,
        namespace: StateNamespace,
    ) -> StateStoreRepository:
        if not isinstance(namespace, StateNamespace):
            _unavailable("audit_namespace_invalid")
        value = self._audit.get(namespace)
        if value is None:
            _unavailable("audit_repository_unavailable")
        return value


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


def create_contract_test_state_store_composition(
    *,
    config: "NsRuntimeStateStoreConfig",
    clock: Clock,
    capabilities: StateStoreCapabilities | None = None,
    runtime_id: str | None = None,
    audit_namespaces: tuple[StateNamespace, ...] = (),
) -> object:
    """Return a deterministic test realm that cannot select a network provider."""

    from ns_common.config import NsRuntimeStateStoreConfig
    from .contract_test_provider import ContractTestStateStoreComposition

    if type(config) is not NsRuntimeStateStoreConfig:
        _unavailable("typed_config_required")
    if (
        config.backend != "sqlite"
        or config.resolved_endpoint
        or config.username
        or config.password_source != "none"
    ):
        _unavailable("contract_test_network_provider_forbidden")
    if runtime_id is not None and (
        type(runtime_id) is not str or not runtime_id
    ):
        _unavailable("runtime_id_invalid")
    if (
        type(audit_namespaces) is not tuple
        or any(
            type(value) is not StateNamespace
            or value.kind is not StateNamespaceKind.AUDIT
            for value in audit_namespaces
        )
        or len(set(audit_namespaces)) != len(audit_namespaces)
    ):
        _unavailable("audit_namespaces_invalid")
    return ContractTestStateStoreComposition(
        clock=clock,
        capabilities=capabilities,
        runtime_id=runtime_id,
        audit_namespaces=audit_namespaces,
    )


def _create_redis_valkey_provider(
    *,
    config: "NsRuntimeStateStoreConfig",
    clock: Clock,
    capabilities: StateStoreCapabilities | None,
    production_scope_validator: object | None = None,
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
        _production_scope_validator=production_scope_validator,
    )


def _unavailable(reason: str) -> None:
    raise NsRuntimeStateStoreCapabilityUnavailableError(details={
        "component": "state_store_composition",
        "reason": reason,
    })


__all__ = (
    "StateStoreComposition",
    "create_contract_test_state_store_composition",
    "create_state_store_provider",
)
