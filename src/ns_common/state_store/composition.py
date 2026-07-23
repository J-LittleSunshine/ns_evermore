# -*- coding: utf-8 -*-
"""Explicit composition boundary for production StateStore providers."""

from __future__ import annotations

import hashlib
import os
import tempfile
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


def _assemble_contract_test_state_store_composition(
    *,
    config: "NsRuntimeStateStoreConfig",
    clock: Clock,
    capabilities: StateStoreCapabilities | None = None,
    runtime_id: str | None = None,
    audit_namespaces: tuple[StateNamespace, ...] = (),
) -> StateStoreComposition | None:
    """Build one provider and permanently close its fixed repository set."""

    if runtime_id is not None and (type(runtime_id) is not str or not runtime_id):
        _unavailable("runtime_id_invalid")
    if (
        not isinstance(audit_namespaces, tuple)
        or any(
            not isinstance(value, StateNamespace)
            or value.kind is not StateNamespaceKind.AUDIT
            for value in audit_namespaces
        )
        or len(set(audit_namespaces)) != len(audit_namespaces)
    ):
        _unavailable("audit_namespaces_invalid")

    lease = None
    scope_validator = object.__new__(_ProductionStateScopeValidator)
    scope_validator._repository_specs = {}
    scope_validator._scopes = {}
    scope_validator._closed = False
    scope_validator._realm = "contract_test"
    store = _create_redis_valkey_provider(
        config=config,
        clock=clock,
        capabilities=capabilities,
        production_scope_validator=scope_validator,
    )
    if store is None:
        return None

    specs = []
    if runtime_id is not None:
        specs.extend((
            (
                StateStoreRepositoryRole.DELIVERY_ADMISSION, runtime_id, None,
                StateAuthorityKind.DELIVERY_ADMISSION, "delivery.admission",
                frozenset({
                    StateCallerCapability.READ, StateCallerCapability.TRANSACT,
                    StateCallerCapability.ORDERED_INDEX, StateCallerCapability.APPEND,
                }), "delivery-admission.v1",
            ),
            (
                StateStoreRepositoryRole.DELIVERY_SCHEDULER, runtime_id, None,
                StateAuthorityKind.DELIVERY_ADMISSION, "delivery.scheduling",
                frozenset({
                    StateCallerCapability.READ, StateCallerCapability.TRANSACT,
                    StateCallerCapability.ORDERED_INDEX, StateCallerCapability.APPEND,
                }), "delivery-scheduler.v1",
            ),
            (
                StateStoreRepositoryRole.DELIVERY_PAYLOAD, runtime_id, None,
                StateAuthorityKind.DELIVERY_ADMISSION, "delivery.payload_authority",
                frozenset({StateCallerCapability.READ}), "delivery-payload.v1",
            ),
            (
                StateStoreRepositoryRole.DELIVERY_REGISTRY, runtime_id, None,
                StateAuthorityKind.DELIVERY_ADMISSION, "delivery.authority_registry",
                frozenset({
                    StateCallerCapability.READ, StateCallerCapability.TRANSACT,
                    StateCallerCapability.ORDERED_INDEX,
                }), "delivery-registry.v1",
            ),
        ))
    specs.extend(
        (
            StateStoreRepositoryRole.STRONG_AUDIT, None, namespace,
            StateAuthorityKind.STRONG_AUDIT, "strong-audit-authority",
            frozenset({StateCallerCapability.APPEND}), "strong-audit.v1",
        )
        for namespace in audit_namespaces
    )
    repositories = store._install_repositories(tuple(specs))
    offset = 0
    delivery = None
    if runtime_id is not None:
        delivery = StateStoreDeliveryRepositories(
            admission=repositories[0], scheduler=repositories[1],
            payload=repositories[2], registry=repositories[3],
        )
        offset = 4
    audit = {
        namespace: repositories[offset + index]
        for index, namespace in enumerate(audit_namespaces)
    }
    value = object.__new__(StateStoreComposition)
    value.store = store
    value._delivery = delivery
    value._runtime_id = runtime_id
    value._audit = audit
    value._lease = lease
    return value


def create_contract_test_state_store_composition(
    **kwargs: object,
) -> StateStoreComposition | None:
    """Explicit non-production entry used by resource-policy contract tests."""
    return _assemble_contract_test_state_store_composition(  # type: ignore[arg-type]
        **kwargs,
    )


class _ProductionCompositionLease:
    __slots__ = ("_file",)

    def __init__(self, file: object) -> None:
        self._file = file

    def __del__(self) -> None:
        file = getattr(self, "_file", None)
        if file is not None:
            try:
                import portalocker

                portalocker.unlock(file)
                file.close()
            except (OSError, ValueError):
                pass
            self._file = None


def _acquire_production_lease(
    *,
    config: "NsRuntimeStateStoreConfig",
    runtime_id: str,
) -> _ProductionCompositionLease:
    import portalocker

    identity = hashlib.sha256(
        "\0".join((
            config.backend, config.resolved_endpoint, config.namespace, runtime_id,
        )).encode(),
    ).hexdigest()
    path = os.path.join(
        tempfile.gettempdir(), f"ns-runtime-state-authority-{identity}.lock",
    )
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    file = os.fdopen(fd, "a+b", buffering=0)
    try:
        portalocker.lock(
            file,
            portalocker.LockFlags.EXCLUSIVE | portalocker.LockFlags.NON_BLOCKING,
        )
    except portalocker.AlreadyLocked:
        file.close()
        _unavailable("parallel_production_composition")
    return _ProductionCompositionLease(file)


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
