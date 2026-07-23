# -*- coding: utf-8 -*-
"""Explicit composition boundary for production StateStore providers."""

from __future__ import annotations

import hashlib
import re
from types import MappingProxyType
from typing import TYPE_CHECKING

from ns_common.exceptions import NsRuntimeStateStoreCapabilityUnavailableError
from ns_common.time import Clock

from .authority import (
    StateAccessScope,
    StateAtomicScope,
    StateAuthorityKind,
    StateCallerCapability,
    StateNamespace,
    StateNamespaceKind,
    StateStoreCapabilities,
    _StateResourcePolicy,
    _issue_state_access_scope,
    _new_state_scope_issuer,
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
    _bind_state_store_repository,
)

if TYPE_CHECKING:
    from ns_common.config import NsRuntimeStateStoreConfig


class StateStoreComposition:
    """Closed repository set; it contains no repository creation capability."""

    __slots__ = ("store", "_delivery", "_runtime_id", "_audit")

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


def create_state_store_composition(
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

    issuer = _new_state_scope_issuer(contract_test=False)
    active_bindings: dict[
        object,
        tuple[
            _StateResourcePolicy,
            StateAuthorityKind,
            str,
            frozenset[StateCallerCapability],
        ],
    ] = {}
    frozen_bindings = MappingProxyType({})
    creation_closed = False
    scope_public_key = issuer._public_key
    scope_issuer_identity = issuer._identity

    def validate_scope(scope: StateAccessScope) -> bool:
        if not creation_closed or type(scope) is not StateAccessScope:
            return False
        spec = frozen_bindings.get(
            getattr(scope, "_repository_binding", None),
        )
        if spec is None:
            return False
        policy, authority, caller, caller_capabilities = spec
        return bool(
            type(policy) is _StateResourcePolicy
            and getattr(scope, "_resource_policy", None) is policy
            and scope.authority is authority
            and scope.caller == caller
            and scope.capabilities == caller_capabilities
            and scope._verified_by(
                public_key=scope_public_key,
                issuer_identity=scope_issuer_identity,
            )
        )

    scope_validator = _ProductionStateScopeValidator(validate_scope)
    store = _create_redis_valkey_provider(
        config=config,
        clock=clock,
        capabilities=capabilities,
        production_scope_validator=scope_validator,
    )
    if store is None:
        return None

    repositories: list[StateStoreRepository] = []

    def bind_repository(
        *,
        role: StateStoreRepositoryRole,
        authority: StateAuthorityKind,
        caller: str,
        caller_capabilities: frozenset[StateCallerCapability],
        policy: _StateResourcePolicy,
        repository_runtime_id: str | None = None,
        audit_namespace: StateNamespace | None = None,
    ) -> StateStoreRepository:
        if creation_closed:
            _unavailable("repository_creation_closed")
        binding = object()
        repository_ref: StateStoreRepository | None = None
        scope_cache: dict[StateAtomicScope, StateAccessScope] = {}

        def issue_scope(atomic_scope: StateAtomicScope) -> StateAccessScope:
            spec = active_bindings.get(binding)
            if (
                not creation_closed
                or repository_ref is None
                or spec is None
                or spec[0] is not policy
                or not _repository_allows_atomic_scope(
                    role=role,
                    runtime_id=repository_runtime_id,
                    audit_namespace=audit_namespace,
                    atomic_scope=atomic_scope,
                )
            ):
                _unavailable("repository_not_current")
            existing = scope_cache.get(atomic_scope)
            if existing is not None:
                return existing
            value = _issue_state_access_scope(
                issuer,
                atomic_scope=atomic_scope,
                authority=authority,
                caller=caller,
                capabilities=caller_capabilities,
                resource_policy=policy,
                repository_binding=binding,
            )
            scope_cache[atomic_scope] = value
            return value

        def is_current(candidate: StateStoreRepository) -> bool:
            return bool(
                repository_ref is candidate
                and active_bindings.get(binding) is not None
                and active_bindings[binding][0] is policy
            )

        repository_ref = _bind_state_store_repository(
            store=store,
            role=role,
            runtime_id=repository_runtime_id,
            audit_namespace=audit_namespace,
            issue_atomic_scope=issue_scope,
            is_current_repository=is_current,
        )
        active_bindings[binding] = (
            policy,
            authority,
            caller,
            caller_capabilities,
        )
        repositories.append(repository_ref)
        return repository_ref

    delivery: StateStoreDeliveryRepositories | None = None
    if runtime_id is not None:
        delivery = StateStoreDeliveryRepositories(
            admission=bind_repository(
                role=StateStoreRepositoryRole.DELIVERY_ADMISSION,
                authority=StateAuthorityKind.DELIVERY_ADMISSION,
                caller="delivery.admission",
                caller_capabilities=frozenset({
                    StateCallerCapability.READ,
                    StateCallerCapability.TRANSACT,
                    StateCallerCapability.ORDERED_INDEX,
                    StateCallerCapability.APPEND,
                }),
                policy=_delivery_admission_policy(),
                repository_runtime_id=runtime_id,
            ),
            scheduler=bind_repository(
                role=StateStoreRepositoryRole.DELIVERY_SCHEDULER,
                authority=StateAuthorityKind.DELIVERY_ADMISSION,
                caller="delivery.scheduling",
                caller_capabilities=frozenset({
                    StateCallerCapability.READ,
                    StateCallerCapability.TRANSACT,
                    StateCallerCapability.ORDERED_INDEX,
                    StateCallerCapability.APPEND,
                }),
                policy=_delivery_scheduler_policy(),
                repository_runtime_id=runtime_id,
            ),
            payload=bind_repository(
                role=StateStoreRepositoryRole.DELIVERY_PAYLOAD,
                authority=StateAuthorityKind.DELIVERY_ADMISSION,
                caller="delivery.payload_authority",
                caller_capabilities=frozenset({StateCallerCapability.READ}),
                policy=_delivery_payload_policy(),
                repository_runtime_id=runtime_id,
            ),
            registry=bind_repository(
                role=StateStoreRepositoryRole.DELIVERY_REGISTRY,
                authority=StateAuthorityKind.DELIVERY_ADMISSION,
                caller="delivery.authority_registry",
                caller_capabilities=frozenset({
                    StateCallerCapability.READ,
                    StateCallerCapability.TRANSACT,
                    StateCallerCapability.ORDERED_INDEX,
                }),
                policy=_delivery_registry_policy(),
                repository_runtime_id=runtime_id,
            ),
        )
    audit = {
        namespace: bind_repository(
            role=StateStoreRepositoryRole.STRONG_AUDIT,
            authority=StateAuthorityKind.STRONG_AUDIT,
            caller="strong-audit-authority",
            caller_capabilities=frozenset({StateCallerCapability.APPEND}),
            policy=_strong_audit_policy(),
            audit_namespace=namespace,
        )
        for namespace in audit_namespaces
    }
    frozen_bindings = MappingProxyType(dict(active_bindings))
    creation_closed = True
    # The local creation function and issuer are not retained by the store or
    # composition.  Repository closures can issue only their already-fixed
    # scope and cannot register another binding after this point.
    value = object.__new__(StateStoreComposition)
    value.store = store
    value._delivery = delivery
    value._runtime_id = runtime_id
    value._audit = audit
    return value


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


def _delivery_admission_policy() -> _StateResourcePolicy:
    return _StateResourcePolicy(
        read_resources=frozenset({
            ("dedup", "delivery_dedup"),
        }),
        transact_resources=frozenset({
            ("dedup", "delivery_dedup"),
            ("payload_body", "delivery_payload_body"),
            ("summary", "delivery_summary"),
            ("delivery", "delivery_delivery"),
        }),
        append_resources=frozenset({
            ("delivery_transition_log", "delivery_transition_event"),
        }),
        ordered_indexes=frozenset({
            ("delivery.prepared", "delivery"),
        }),
    )


def _delivery_scheduler_policy() -> _StateResourcePolicy:
    return _StateResourcePolicy(
        read_resources=frozenset({
            ("delivery", "delivery_delivery"),
            ("summary", "delivery_summary"),
            ("attempt", "delivery_attempt"),
            ("delivery_scheduler_cursor", "delivery_scheduler_cursor"),
        }),
        transact_resources=frozenset({
            ("delivery", "delivery_delivery"),
            ("summary", "delivery_summary"),
            ("attempt", "delivery_attempt"),
            ("delivery_scheduler_cursor", "delivery_scheduler_cursor"),
        }),
        append_resources=frozenset({
            ("delivery_transition_log", "delivery_transition_event"),
            (
                "delivery_scheduler_repair_log",
                "delivery_index_repair_event",
            ),
        }),
        ordered_indexes=frozenset({
            ("delivery.prepared", "delivery"),
            ("delivery.ready", "delivery"),
            ("delivery.claimed", "delivery"),
            ("delivery.lease", "delivery"),
            ("delivery.sending", "delivery"),
            ("delivery.ack", "delivery"),
            ("delivery.write_failed", "delivery"),
            ("delivery.waiting", "delivery"),
            ("delivery.expired", "delivery"),
            ("delivery.payload_rejected", "delivery"),
            ("delivery.write_uncertain", "delivery"),
            ("delivery.scheduler_quarantine", "delivery"),
            ("delivery.runtime.ready", "delivery"),
        }),
        allow_delivery_target_index=True,
    )


def _delivery_payload_policy() -> _StateResourcePolicy:
    return _StateResourcePolicy(
        read_resources=frozenset({
            ("payload_body", "delivery_payload_body"),
        }),
    )


def _delivery_registry_policy() -> _StateResourcePolicy:
    return _StateResourcePolicy(
        read_resources=frozenset({
            (
                "delivery_authority_layout",
                "delivery.authority_layout",
            ),
            (
                "delivery_tenant_registration",
                "delivery.tenant_registration",
            ),
        }),
        transact_resources=frozenset({
            (
                "delivery_authority_layout",
                "delivery.authority_layout",
            ),
            (
                "delivery_tenant_registration",
                "delivery.tenant_registration",
            ),
        }),
        ordered_indexes=frozenset({
            ("delivery.tenant_registry", "runtime"),
        }),
    )


def _strong_audit_policy() -> _StateResourcePolicy:
    return _StateResourcePolicy(
        append_resources=frozenset({
            ("processor_audit_log", "runtime.processor_audit"),
        }),
    )


def _repository_allows_atomic_scope(
    *,
    role: StateStoreRepositoryRole,
    runtime_id: str | None,
    audit_namespace: StateNamespace | None,
    atomic_scope: StateAtomicScope,
) -> bool:
    if not isinstance(atomic_scope, StateAtomicScope):
        return False
    if role in {
        StateStoreRepositoryRole.DELIVERY_ADMISSION,
        StateStoreRepositoryRole.DELIVERY_SCHEDULER,
        StateStoreRepositoryRole.DELIVERY_PAYLOAD,
    }:
        return bool(
            runtime_id is not None
            and atomic_scope.namespace.kind is StateNamespaceKind.TENANT
            and atomic_scope.namespace.domain == "delivery"
            and re.fullmatch(
                r"layout-[1-9][0-9]*-bucket-(0|[1-9][0-9]*)",
                atomic_scope.partition,
            ) is not None
        )
    if role is StateStoreRepositoryRole.DELIVERY_REGISTRY:
        if runtime_id is None:
            return False
        expected_tenant = "runtime-registry:" + hashlib.sha256(
            runtime_id.encode(),
        ).hexdigest()
        return bool(
            atomic_scope.namespace
            == StateNamespace.tenant(
                tenant_id=expected_tenant,
                domain="delivery",
            )
            and atomic_scope.partition == "authority-registry"
        )
    return bool(
        role is StateStoreRepositoryRole.STRONG_AUDIT
        and audit_namespace is not None
        and atomic_scope.namespace == audit_namespace
        and atomic_scope.partition == "processor-final"
    )


def _unavailable(reason: str) -> None:
    raise NsRuntimeStateStoreCapabilityUnavailableError(details={
        "component": "state_store_composition",
        "reason": reason,
    })


__all__ = (
    "StateStoreComposition",
    "create_state_store_composition",
    "create_state_store_provider",
)
