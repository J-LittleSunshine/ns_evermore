# -*- coding: utf-8 -*-
"""Backend-neutral StateStore lifecycle and operation boundary."""

from __future__ import annotations

import asyncio
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import hashlib
from types import MappingProxyType

from ns_common.exceptions import (
    NsRuntimeStateStoreCapabilityUnavailableError,
    NsRuntimeStateStoreClosedError,
    NsRuntimeStateStoreError,
    NsRuntimeStateStoreIndeterminateWriteError,
    NsRuntimeStateStoreNamespaceViolationError,
    NsRuntimeStateStoreNotReadyError,
    NsRuntimeStateStoreStaleReadError,
    NsRuntimeStateStoreTimeoutError,
    NsRuntimeStateStoreUnavailableError,
    NsValidationError,
)
from ns_common.time import Clock

from .authority import (
    StateAccessScope,
    StateCallerCapability,
    StateStoreCapabilities,
    StateStoreCapability,
    StateNamespaceKind,
    StateAtomicScope,
    StateAuthorityKind,
    StateNamespace,
    _new_state_scope_issuer,
)
from .model import (
    StateAppendResult,
    StateAssertion,
    StateConsistency,
    StateDocument,
    StateKey,
    StateMutation,
    StateOrderedIndexKey,
    StateOrderedIndexReadResult,
    StateReadResult,
    StateRecord,
    StateRevision,
    StateScanResult,
    StateStoreHealth,
    StateStoreHealthStatus,
    StateTransaction,
    StateTransactionResult,
)


class StateStoreLifecycleState(str, Enum):
    NEW = "new"
    OPENING = "opening"
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"


_PolicySpec = tuple[
    frozenset[tuple[str, str]],
    frozenset[tuple[str, str]],
    frozenset[tuple[str, str]],
    frozenset[tuple[str, str]],
    bool,
]

_STATE_RESOURCE_POLICIES = MappingProxyType({
    "delivery-admission.v1": (
        frozenset({("dedup", "delivery_dedup")}),
        frozenset({
            ("dedup", "delivery_dedup"),
            ("payload_body", "delivery_payload_body"),
            ("summary", "delivery_summary"),
            ("delivery", "delivery_delivery"),
        }),
        frozenset({("delivery_transition_log", "delivery_transition_event")}),
        frozenset({("delivery.prepared", "delivery")}),
        False,
    ),
    "delivery-scheduler.v1": (
        frozenset({
            ("delivery", "delivery_delivery"),
            ("summary", "delivery_summary"),
            ("attempt", "delivery_attempt"),
            ("delivery_scheduler_cursor", "delivery_scheduler_cursor"),
        }),
        frozenset({
            ("delivery", "delivery_delivery"),
            ("summary", "delivery_summary"),
            ("attempt", "delivery_attempt"),
            ("delivery_scheduler_cursor", "delivery_scheduler_cursor"),
        }),
        frozenset({
            ("delivery_transition_log", "delivery_transition_event"),
            ("delivery_scheduler_repair_log", "delivery_index_repair_event"),
        }),
        frozenset({
            ("delivery.prepared", "delivery"), ("delivery.ready", "delivery"),
            ("delivery.claimed", "delivery"), ("delivery.lease", "delivery"),
            ("delivery.sending", "delivery"), ("delivery.ack", "delivery"),
            ("delivery.write_failed", "delivery"), ("delivery.waiting", "delivery"),
            ("delivery.expired", "delivery"), ("delivery.payload_rejected", "delivery"),
            ("delivery.write_uncertain", "delivery"),
            ("delivery.scheduler_quarantine", "delivery"),
            ("delivery.runtime.ready", "delivery"),
        }),
        True,
    ),
    "delivery-payload.v1": (
        frozenset({("payload_body", "delivery_payload_body")}),
        frozenset(), frozenset(), frozenset(), False,
    ),
    "delivery-registry.v1": (
        frozenset({
            ("delivery_authority_layout", "delivery.authority_layout"),
            ("delivery_tenant_registration", "delivery.tenant_registration"),
        }),
        frozenset({
            ("delivery_authority_layout", "delivery.authority_layout"),
            ("delivery_tenant_registration", "delivery.tenant_registration"),
        }),
        frozenset(),
        frozenset({("delivery.tenant_registry", "runtime")}),
        False,
    ),
    "strong-audit.v1": (
        frozenset(), frozenset(),
        frozenset({("processor_audit_log", "runtime.processor_audit")}),
        frozenset(), False,
    ),
})


class _ProductionStateScopeValidator:
    """Secret-free validator for one closed, fixed repository set."""

    __slots__ = ("_repository_specs", "_scopes", "_closed", "_realm")

    def __init__(self, *args: object, **kwargs: object) -> None:
        del self, args, kwargs
        _invalid("production_scope_validator")

    def is_valid(self) -> bool:
        return bool(
            type(self) is _ProductionStateScopeValidator
            and self._closed is True
            and type(self._repository_specs) is dict
            and type(self._scopes) is dict
            and self._realm in {"production", "contract_test"}
        )

    def __call__(self, scope: StateAccessScope) -> bool:
        if not self.is_valid() or type(scope) is not StateAccessScope:
            return False
        snapshot = self._scopes.get(id(scope))
        return bool(
            snapshot is not None
            and snapshot[0] is scope
            and snapshot[1:] == (
                scope.atomic_scope,
                scope.authority,
                scope.caller,
                scope.capabilities,
                scope._policy_id,
                scope._repository_binding,
            )
        )

    def scope_for(
        self,
        repository: "StateStoreRepository",
        atomic_scope: StateAtomicScope,
    ) -> StateAccessScope:
        if not self.is_valid() or type(repository) is not StateStoreRepository:
            _invalid("repository.scope")
        spec = self._repository_specs.get(repository)
        if spec is None or not _repository_allows_scope(repository, atomic_scope):
            _invalid("repository.scope")
        authority, caller, capabilities, policy_id, binding = spec
        for value in self._scopes.values():
            if value[1] == atomic_scope and value[6] is binding:
                return value[0]
        value = object.__new__(StateAccessScope)
        for name, field_value in (
            ("atomic_scope", atomic_scope), ("authority", authority),
            ("caller", caller), ("capabilities", capabilities),
            ("_issuer_realm", self._realm), ("_issuer_identity", b""),
            ("_authority_signature", b""), ("_policy_id", policy_id),
            ("_repository_binding", binding),
        ):
            object.__setattr__(value, name, field_value)
        value.__post_init__()
        self._scopes[id(value)] = (
            value, atomic_scope, authority, caller, capabilities, policy_id, binding,
        )
        return value

    def policy_for(self, scope: StateAccessScope) -> _PolicySpec | None:
        if not self(scope):
            return None
        return _STATE_RESOURCE_POLICIES.get(scope._policy_id)

    def __copy__(self) -> "_ProductionStateScopeValidator":
        _invalid("production_scope_validator.copy")

    def __deepcopy__(self, memo: dict[int, object]) -> "_ProductionStateScopeValidator":
        del memo
        _invalid("production_scope_validator.copy")


class StateStoreRepositoryRole(str, Enum):
    STRONG_AUDIT = "strong_audit"
    DELIVERY_ADMISSION = "delivery_admission"
    DELIVERY_SCHEDULER = "delivery_scheduler"
    DELIVERY_PAYLOAD = "delivery_payload"
    DELIVERY_REGISTRY = "delivery_registry"


class StateStoreRepository:
    """Opaque fixed-capability repository handle issued by one composition."""

    __slots__ = (
        "_store", "_role", "_runtime_id", "_audit_namespace", "_binding",
        "_contract_issue_scope", "_contract_is_current",
    )

    def __init__(
        self,
        *args: object,
        **kwargs: object,
    ) -> None:
        del self, args, kwargs
        _invalid("repository.issuer")

    @property
    def role(self) -> StateStoreRepositoryRole:
        return self._role

    def delivery_scope(
        self,
        *,
        tenant_id: str,
        bucket_id: int,
        layout_generation: int,
    ) -> StateAccessScope:
        if self._role not in {
            StateStoreRepositoryRole.DELIVERY_ADMISSION,
            StateStoreRepositoryRole.DELIVERY_SCHEDULER,
            StateStoreRepositoryRole.DELIVERY_PAYLOAD,
        }:
            _invalid("repository.delivery_scope")
        if type(tenant_id) is not str or not tenant_id:
            _invalid("repository.tenant_id")
        if isinstance(bucket_id, bool) or not isinstance(bucket_id, int) or bucket_id < 0:
            _invalid("repository.bucket_id")
        if (
            isinstance(layout_generation, bool)
            or not isinstance(layout_generation, int)
            or layout_generation <= 0
        ):
            _invalid("repository.layout_generation")
        return self._issue_scope(StateAtomicScope(
                namespace=StateNamespace.tenant(
                    tenant_id=tenant_id,
                    domain="delivery",
                ),
                partition=f"layout-{layout_generation}-bucket-{bucket_id}",
            ))

    def registry_scope(self) -> StateAccessScope:
        if (
            self._role is not StateStoreRepositoryRole.DELIVERY_REGISTRY
            or self._runtime_id is None
        ):
            _invalid("repository.registry_scope")
        synthetic_tenant = "runtime-registry:" + hashlib.sha256(
            self._runtime_id.encode(),
        ).hexdigest()
        return self._issue_scope(StateAtomicScope(
                namespace=StateNamespace.tenant(
                    tenant_id=synthetic_tenant,
                    domain="delivery",
                ),
                partition="authority-registry",
            ))

    def audit_scope(self) -> StateAccessScope:
        if (
            self._role is not StateStoreRepositoryRole.STRONG_AUDIT
            or self._audit_namespace is None
        ):
            _invalid("repository.audit_scope")
        return self._issue_scope(StateAtomicScope(
                namespace=self._audit_namespace,
                partition="processor-final",
            ))

    def _issue_scope(self, atomic_scope: StateAtomicScope) -> StateAccessScope:
        if type(self) is not StateStoreRepository:
            _invalid("repository.scope")
        value = (
            self._contract_issue_scope(atomic_scope)
            if self._contract_issue_scope is not None
            else self._store._scope_for_repository(self, atomic_scope)
        )
        if type(value) is not StateAccessScope:
            _invalid("repository.scope")
        return value

    def _require_role(self, role: StateStoreRepositoryRole) -> None:
        if (
            not isinstance(role, StateStoreRepositoryRole)
            or self._role is not role
            or not (
                self._contract_is_current(self)
                if self._contract_is_current is not None
                else self._store._is_current_repository(self)
            )
        ):
            _invalid("repository.role")

    def __copy__(self) -> "StateStoreRepository":
        del self
        _invalid("repository.copy")

    def __deepcopy__(self, memo: dict[int, object]) -> "StateStoreRepository":
        del self, memo
        _invalid("repository.copy")


@dataclass(frozen=True, slots=True, kw_only=True)
class StateStoreDeliveryRepositories:
    admission: StateStoreRepository
    scheduler: StateStoreRepository
    payload: StateStoreRepository
    registry: StateStoreRepository

    def __post_init__(self) -> None:
        if any(
            type(value) is not StateStoreRepository
            for value in (
                self.admission, self.scheduler, self.payload, self.registry,
            )
        ):
            _invalid("repository_set.repository")
        self.admission._require_role(StateStoreRepositoryRole.DELIVERY_ADMISSION)
        self.scheduler._require_role(StateStoreRepositoryRole.DELIVERY_SCHEDULER)
        self.payload._require_role(StateStoreRepositoryRole.DELIVERY_PAYLOAD)
        self.registry._require_role(StateStoreRepositoryRole.DELIVERY_REGISTRY)
        stores = {
            value._store
            for value in (
                self.admission, self.scheduler, self.payload, self.registry,
            )
        }
        if len(stores) != 1:
            _invalid("repository_set.store")


def _bind_state_store_repository(
    *,
    store: "StateStore",
    role: StateStoreRepositoryRole,
    runtime_id: str | None,
    audit_namespace: StateNamespace | None,
    binding: object | None = None,
    issue_atomic_scope: object | None = None,
    is_current_repository: object | None = None,
) -> StateStoreRepository:
    """Low-level assembly for a fixed binding; it contains no issuer."""

    if (
        not isinstance(store, StateStore)
        or not isinstance(role, StateStoreRepositoryRole)
        or (
            binding is None
            and (not callable(issue_atomic_scope) or not callable(is_current_repository))
        )
    ):
        _invalid("repository.binding")
    value = object.__new__(StateStoreRepository)
    value._store = store
    value._role = role
    value._runtime_id = runtime_id
    value._audit_namespace = audit_namespace
    value._binding = binding
    value._contract_issue_scope = issue_atomic_scope
    value._contract_is_current = is_current_repository
    return value


def _repository_allows_scope(
    repository: StateStoreRepository,
    atomic_scope: StateAtomicScope,
) -> bool:
    if not isinstance(atomic_scope, StateAtomicScope):
        return False
    role = repository._role
    if role in {
        StateStoreRepositoryRole.DELIVERY_ADMISSION,
        StateStoreRepositoryRole.DELIVERY_SCHEDULER,
        StateStoreRepositoryRole.DELIVERY_PAYLOAD,
    }:
        return bool(
            repository._runtime_id is not None
            and atomic_scope.namespace.kind is StateNamespaceKind.TENANT
            and atomic_scope.namespace.domain == "delivery"
            and __import__("re").fullmatch(
                r"layout-[1-9][0-9]*-bucket-(0|[1-9][0-9]*)",
                atomic_scope.partition,
            ) is not None
        )
    if role is StateStoreRepositoryRole.DELIVERY_REGISTRY:
        expected_tenant = "runtime-registry:" + hashlib.sha256(
            repository._runtime_id.encode(),
        ).hexdigest()
        return bool(
            atomic_scope.namespace == StateNamespace.tenant(
                tenant_id=expected_tenant, domain="delivery",
            )
            and atomic_scope.partition == "authority-registry"
        )
    return bool(
        role is StateStoreRepositoryRole.STRONG_AUDIT
        and atomic_scope.namespace == repository._audit_namespace
        and atomic_scope.partition == "processor-final"
    )


class StateStore(ABC):
    """Strict StateStore template with one explicit lifecycle owner.

    Concrete providers implement only the protected hooks.  This base class
    owns no task supervisor, event loop, thread, registry, or retry policy.
    """

    def __init__(
        self,
        *,
        capabilities: StateStoreCapabilities,
        clock: Clock,
        _contract_test_authority: bool = False,
        _scope_issuer: object | None = None,
        _production_scope_validator: Callable[[StateAccessScope], bool] | None = None,
    ) -> None:
        if not isinstance(capabilities, StateStoreCapabilities):
            _invalid("capabilities")
        if not isinstance(clock, Clock):
            _invalid("clock")
        self._capabilities = capabilities
        self._clock = clock
        if type(_contract_test_authority) is not bool:
            _invalid("contract_test_authority")
        if _contract_test_authority:
            self.__scope_issuer = (
                _scope_issuer
                if _scope_issuer is not None
                else _new_state_scope_issuer(contract_test=True)
            )
            self.__production_scope_validator = None
        else:
            if _scope_issuer is not None:
                _invalid("scope_issuer")
            self.__scope_issuer = None
            if _production_scope_validator is None:
                self.__production_scope_validator = None
            elif (
                type(_production_scope_validator)
                is not _ProductionStateScopeValidator
                or getattr(_production_scope_validator, "_closed", None) is not False
                or type(getattr(
                    _production_scope_validator, "_repository_specs", None,
                )) is not dict
                or type(getattr(_production_scope_validator, "_scopes", None)) is not dict
                or getattr(_production_scope_validator, "_realm", None)
                not in {"production", "contract_test"}
            ):
                _invalid("production_scope_validator")
            else:
                self.__production_scope_validator = (
                    _production_scope_validator
                )
        self._state = StateStoreLifecycleState.NEW
        self._lifecycle_condition = asyncio.Condition()
        self._active_operations = 0

    def _install_repositories(
        self,
        specs: tuple[
            tuple[
                StateStoreRepositoryRole, str | None, StateNamespace | None,
                StateAuthorityKind, str, frozenset[StateCallerCapability], str,
            ],
            ...,
        ],
    ) -> tuple[StateStoreRepository, ...]:
        validator = self.__production_scope_validator
        if (
            type(validator) is not _ProductionStateScopeValidator
            or validator._closed
            or validator._repository_specs
            or not isinstance(specs, tuple)
        ):
            _invalid("repository.install")
        repositories: list[StateStoreRepository] = []
        for (
            role, runtime_id, audit_namespace, authority, caller,
            capabilities, policy_id,
        ) in specs:
            if (
                not isinstance(role, StateStoreRepositoryRole)
                or policy_id not in _STATE_RESOURCE_POLICIES
                or not isinstance(authority, StateAuthorityKind)
                or not isinstance(capabilities, frozenset)
            ):
                _invalid("repository.spec")
            binding = object()
            repository = _bind_state_store_repository(
                store=self, role=role, runtime_id=runtime_id,
                audit_namespace=audit_namespace, binding=binding,
            )
            validator._repository_specs[repository] = (
                authority, caller, capabilities, policy_id, binding,
            )
            repositories.append(repository)
        validator._closed = True
        return tuple(repositories)

    def _is_current_repository(self, repository: StateStoreRepository) -> bool:
        validator = self.__production_scope_validator
        spec = (
            None if type(validator) is not _ProductionStateScopeValidator
            else validator._repository_specs.get(repository)
        )
        return bool(
            type(repository) is StateStoreRepository
            and repository._store is self
            and spec is not None
            and spec[4] is repository._binding
        )

    def _scope_for_repository(
        self,
        repository: StateStoreRepository,
        atomic_scope: StateAtomicScope,
    ) -> StateAccessScope:
        validator = self.__production_scope_validator
        if (
            type(validator) is not _ProductionStateScopeValidator
            or not self._is_current_repository(repository)
        ):
            _invalid("repository.scope")
        return validator.scope_for(repository, atomic_scope)

    @property
    def state(self) -> StateStoreLifecycleState:
        return self._state

    def capabilities(self) -> StateStoreCapabilities:
        return self._capabilities

    async def open(self) -> None:
        async with self._lifecycle_condition:
            if self._state is StateStoreLifecycleState.OPEN:
                return
            if self._state is StateStoreLifecycleState.CLOSED:
                raise _closed("open")
            if self._state is not StateStoreLifecycleState.NEW:
                raise _not_ready("open", self._state)
            self._state = StateStoreLifecycleState.OPENING
            try:
                await self._open()
            except asyncio.CancelledError:
                self._state = StateStoreLifecycleState.NEW
                raise
            except NsRuntimeStateStoreError:
                self._state = StateStoreLifecycleState.NEW
                raise
            except asyncio.TimeoutError:
                self._state = StateStoreLifecycleState.NEW
                raise NsRuntimeStateStoreTimeoutError(
                    details={"component": "state_store", "operation": "open"},
                ) from None
            except Exception:
                self._state = StateStoreLifecycleState.NEW
                raise NsRuntimeStateStoreUnavailableError(
                    details={"component": "state_store", "operation": "open"},
                ) from None
            except BaseException:
                self._state = StateStoreLifecycleState.NEW
                raise
            self._state = StateStoreLifecycleState.OPEN

    async def close(self) -> None:
        async with self._lifecycle_condition:
            if self._state is StateStoreLifecycleState.CLOSED:
                return
            if self._state is StateStoreLifecycleState.NEW:
                self._state = StateStoreLifecycleState.CLOSED
                return
            if self._state is not StateStoreLifecycleState.OPEN:
                raise _not_ready("close", self._state)
            self._state = StateStoreLifecycleState.CLOSING
            try:
                while self._active_operations:
                    await self._lifecycle_condition.wait()
                await self._close()
            except asyncio.CancelledError:
                self._state = StateStoreLifecycleState.OPEN
                raise
            except NsRuntimeStateStoreError:
                self._state = StateStoreLifecycleState.OPEN
                raise
            except asyncio.TimeoutError:
                self._state = StateStoreLifecycleState.OPEN
                raise NsRuntimeStateStoreTimeoutError(
                    details={"component": "state_store", "operation": "close"},
                ) from None
            except Exception:
                self._state = StateStoreLifecycleState.OPEN
                raise NsRuntimeStateStoreUnavailableError(
                    details={"component": "state_store", "operation": "close"},
                ) from None
            except BaseException:
                self._state = StateStoreLifecycleState.OPEN
                raise
            self._state = StateStoreLifecycleState.CLOSED

    async def read(
        self,
        *,
        scope: StateAccessScope,
        key: StateKey,
        consistency: StateConsistency,
        minimum_revision: StateRevision | None = None,
    ) -> StateReadResult:
        self._validate_access(
            scope=scope,
            key=key,
            operation="read",
            document=None,
            caller_capability=StateCallerCapability.READ,
            store_capability=StateStoreCapability.READ,
        )
        if not isinstance(consistency, StateConsistency):
            _invalid("read.consistency")
        if consistency is StateConsistency.LINEARIZABLE:
            self._require_store_capability(StateStoreCapability.LINEARIZABLE_READ)
            if minimum_revision is not None:
                _invalid("read.minimum_revision")
        elif consistency is StateConsistency.AT_LEAST_REVISION:
            self._require_store_capability(StateStoreCapability.MINIMUM_REVISION_READ)
            if not isinstance(minimum_revision, StateRevision):
                _invalid("read.minimum_revision")
        else:
            self._require_store_capability(StateStoreCapability.STALE_READ)
            if minimum_revision is not None and not isinstance(
                minimum_revision,
                StateRevision,
            ):
                _invalid("read.minimum_revision")

        await self._enter_operation("read")
        try:
            try:
                result = await self._read(
                    scope=scope,
                    key=key,
                    consistency=consistency,
                    minimum_revision=minimum_revision,
                )
            except asyncio.CancelledError:
                raise
            except NsRuntimeStateStoreError:
                raise
            except asyncio.TimeoutError:
                raise NsRuntimeStateStoreTimeoutError(
                    details={"component": "state_store", "operation": "read"},
                ) from None
            except Exception:
                raise NsRuntimeStateStoreUnavailableError(
                    details={"component": "state_store", "operation": "read"},
                ) from None
            if not isinstance(result, StateReadResult):
                raise NsRuntimeStateStoreError(
                    details={"component": "state_store", "operation": "read"},
                )
            if result.stale and consistency is not StateConsistency.STALE_ALLOWED:
                raise NsRuntimeStateStoreStaleReadError(
                    details={"component": "state_store", "operation": "read"},
                )
            if result.record is not None:
                self._validate_resource(
                    scope=scope,
                    operation="read",
                    object_type=result.record.key.object_type,
                    schema_name=result.record.document.schema_name,
                )
            return result
        finally:
            await self._exit_operation()

    async def compare_and_set(
        self,
        *,
        scope: StateAccessScope,
        mutation: StateMutation,
    ) -> StateRecord | None:
        if not isinstance(mutation, StateMutation):
            _invalid("compare_and_set.mutation")
        self._validate_access(
            scope=scope,
            key=mutation.key,
            operation="compare_and_set",
            document=mutation.document,
            caller_capability=StateCallerCapability.COMPARE_AND_SET,
            store_capability=StateStoreCapability.COMPARE_AND_SET,
        )
        await self._enter_operation("compare_and_set")
        try:
            return await self._run_write(
                "compare_and_set",
                self._compare_and_set(scope=scope, mutation=mutation),
                expected_type=(StateRecord, type(None)),
            )
        finally:
            await self._exit_operation()

    async def scan(
        self,
        *,
        scope: StateAccessScope,
        object_type: str,
        cursor: str | None = None,
        limit: int = 100,
    ) -> StateScanResult:
        if type(object_type) is not str or not object_type:
            _invalid("scan.object_type")
        if cursor is not None and (
            type(cursor) is not str or not cursor.isdigit() or cursor == "0"
        ):
            _invalid("scan.cursor")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 0 < limit <= 1000:
            _invalid("scan.limit")
        self._require_caller_capability(scope, StateCallerCapability.SCAN)
        self._require_authority(scope)
        self._require_store_capability(StateStoreCapability.SCAN)
        self._validate_resource(
            scope=scope,
            operation="scan",
            object_type=object_type,
            schema_name=None,
        )
        await self._enter_operation("scan")
        try:
            try:
                result = await self._scan(
                    scope=scope,
                    object_type=object_type,
                    cursor=cursor,
                    limit=limit,
                )
            except asyncio.CancelledError:
                raise
            except NsRuntimeStateStoreError:
                raise
            except asyncio.TimeoutError:
                raise NsRuntimeStateStoreTimeoutError(
                    details={"component": "state_store", "operation": "scan"},
                ) from None
            except Exception:
                raise NsRuntimeStateStoreUnavailableError(
                    details={"component": "state_store", "operation": "scan"},
                ) from None
            if not isinstance(result, StateScanResult):
                raise NsRuntimeStateStoreError(
                    details={"component": "state_store", "operation": "scan"},
                )
            if any(
                record.key.namespace != scope.namespace
                or record.key.object_type != object_type
                for record in result.records
            ):
                raise NsRuntimeStateStoreNamespaceViolationError(
                    details={
                        "component": "state_store",
                        "operation": "scan",
                        "reason": "provider_scope_mismatch",
                    },
                )
            for record in result.records:
                self._validate_resource(
                    scope=scope,
                    operation="scan",
                    object_type=record.key.object_type,
                    schema_name=record.document.schema_name,
                )
            return result
        finally:
            await self._exit_operation()

    async def transact(
        self,
        transaction: StateTransaction,
    ) -> StateTransactionResult:
        if not isinstance(transaction, StateTransaction):
            _invalid("transaction")
        scope = transaction.scope
        self._require_caller_capability(scope, StateCallerCapability.TRANSACT)
        self._require_authority(scope)
        self._require_store_capability(StateStoreCapability.TRANSACTION)
        if (
            transaction.ordered_index_mutations
            or transaction.ordered_index_assertions
        ):
            self._require_caller_capability(
                scope, StateCallerCapability.ORDERED_INDEX,
            )
            self._require_store_capability(StateStoreCapability.ORDERED_INDEX)
        if transaction.log_appends:
            self._require_caller_capability(scope, StateCallerCapability.APPEND)
            self._require_store_capability(StateStoreCapability.APPEND)
        for mutation in transaction.mutations:
            self._validate_key_scope(scope, mutation.key)
            self._validate_resource(
                scope=scope,
                operation="transact",
                object_type=mutation.key.object_type,
                schema_name=(
                    None
                    if mutation.document is None
                    else mutation.document.schema_name
                ),
            )
        for assertion in transaction.record_assertions:
            self._validate_key_scope(scope, assertion.key)
            self._validate_resource(
                scope=scope,
                operation="transact",
                object_type=assertion.key.object_type,
                schema_name=None,
            )
        for mutation in transaction.ordered_index_mutations:
            if (mutation.index.namespace != scope.namespace
                    and mutation.index.namespace.kind is not StateNamespaceKind.SYSTEM):
                raise NsRuntimeStateStoreNamespaceViolationError(details={
                    "component": "state_store", "reason": "namespace_scope_mismatch",
                })
            self._validate_index_resource(scope, mutation.index)
        for assertion in transaction.ordered_index_assertions:
            if (
                assertion.index.namespace != scope.namespace
                and assertion.index.namespace.kind
                is not StateNamespaceKind.SYSTEM
            ):
                raise NsRuntimeStateStoreNamespaceViolationError(details={
                    "component": "state_store",
                    "reason": "namespace_scope_mismatch",
                })
            self._validate_index_resource(scope, assertion.index)
        for append in transaction.log_appends:
            self._validate_key_scope(scope, append.key)
            self._validate_resource(
                scope=scope,
                operation="append",
                object_type=append.key.object_type,
                schema_name=append.document.schema_name,
            )
        await self._enter_operation("transact")
        try:
            result = await self._run_write(
                "transact",
                self._transact(transaction),
                expected_type=StateTransactionResult,
            )
            if not result.is_for_transaction(transaction):
                raise NsRuntimeStateStoreIndeterminateWriteError(
                    details={
                        "component": "state_store",
                        "operation": "transact",
                        "reason": "provider_result_transaction_mismatch",
                    },
                )
            return result
        finally:
            await self._exit_operation()

    async def read_ordered_index(
        self, *, scope: StateAccessScope, index: StateOrderedIndexKey,
        limit: int, max_score: float | None = None,
        start_after: "StateOrderedIndexCursor | None" = None,
    ) -> StateOrderedIndexReadResult:
        if (not isinstance(index, StateOrderedIndexKey)
                or (index.namespace != scope.namespace
                    and index.namespace.kind is not StateNamespaceKind.SYSTEM)):
            _invalid("ordered_index.index")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 0 < limit <= 1000:
            _invalid("ordered_index.limit")
        if max_score is not None and (
            type(max_score) not in {int, float} or not math.isfinite(max_score)
        ):
            _invalid("ordered_index.max_score")
        from .model import StateOrderedIndexCursor
        if start_after is not None and not isinstance(start_after, StateOrderedIndexCursor):
            _invalid("ordered_index.start_after")
        if (
            start_after is not None
            and max_score is not None
            and start_after.score > max_score
        ):
            _invalid("ordered_index.start_after_max_score")
        self._require_caller_capability(scope, StateCallerCapability.ORDERED_INDEX)
        self._require_authority(scope)
        self._require_store_capability(StateStoreCapability.ORDERED_INDEX)
        self._validate_index_resource(scope, index)
        await self._enter_operation("read_ordered_index")
        try:
            try:
                result = await self._read_ordered_index(
                    scope=scope, index=index, limit=limit, max_score=max_score,
                    start_after=start_after,
                )
            except asyncio.CancelledError:
                raise
            except NsRuntimeStateStoreError:
                raise
            except asyncio.TimeoutError:
                raise NsRuntimeStateStoreTimeoutError(details={
                    "component": "state_store", "operation": "read_ordered_index",
                }) from None
            except Exception:
                raise NsRuntimeStateStoreUnavailableError(details={
                    "component": "state_store", "operation": "read_ordered_index",
                }) from None
            if not isinstance(result, StateOrderedIndexReadResult):
                raise NsRuntimeStateStoreError(details={
                    "component": "state_store", "operation": "read_ordered_index",
                })
            return result
        finally:
            await self._exit_operation()

    async def append(
        self,
        *,
        scope: StateAccessScope,
        key: StateKey,
        document: StateDocument,
        assertion: StateAssertion | None = None,
    ) -> StateAppendResult:
        if not isinstance(document, StateDocument):
            _invalid("append.document")
        if assertion is not None and not isinstance(assertion, StateAssertion):
            _invalid("append.assertion")
        self._validate_access(
            scope=scope,
            key=key,
            operation="append",
            document=document,
            caller_capability=StateCallerCapability.APPEND,
            store_capability=StateStoreCapability.APPEND,
        )
        await self._enter_operation("append")
        try:
            return await self._run_write(
                "append",
                self._append(
                    scope=scope,
                    key=key,
                    document=document,
                    assertion=assertion,
                ),
                expected_type=StateAppendResult,
            )
        finally:
            await self._exit_operation()

    async def health(self) -> StateStoreHealth:
        async with self._lifecycle_condition:
            state = self._state
        if state is StateStoreLifecycleState.NEW:
            return self._local_health(StateStoreHealthStatus.NOT_READY)
        if state is StateStoreLifecycleState.CLOSED:
            return self._local_health(StateStoreHealthStatus.CLOSED)
        await self._enter_operation("health")
        try:
            try:
                result = await self._health()
            except asyncio.CancelledError:
                raise
            except NsRuntimeStateStoreError:
                raise
            except asyncio.TimeoutError:
                raise NsRuntimeStateStoreTimeoutError(
                    details={"component": "state_store", "operation": "health"},
                ) from None
            except Exception:
                raise NsRuntimeStateStoreUnavailableError(
                    details={"component": "state_store", "operation": "health"},
                ) from None
            if not isinstance(result, StateStoreHealth):
                raise NsRuntimeStateStoreError(
                    details={"component": "state_store", "operation": "health"},
                )
            if result.contract_generation != self._capabilities.contract_generation:
                raise NsRuntimeStateStoreUnavailableError(
                    details={
                        "component": "state_store",
                        "operation": "health",
                        "reason": "contract_generation_mismatch",
                    },
                )
            return result
        finally:
            await self._exit_operation()

    async def _run_write(
        self,
        operation: str,
        awaitable: object,
        *,
        expected_type: object,
    ) -> object:
        try:
            result = await awaitable  # type: ignore[misc]
        except asyncio.CancelledError:
            raise
        except NsRuntimeStateStoreTimeoutError:
            raise NsRuntimeStateStoreIndeterminateWriteError(
                details={"component": "state_store", "operation": operation},
            ) from None
        except NsRuntimeStateStoreError:
            raise
        except asyncio.TimeoutError:
            raise NsRuntimeStateStoreIndeterminateWriteError(
                details={"component": "state_store", "operation": operation},
            ) from None
        except Exception:
            raise NsRuntimeStateStoreIndeterminateWriteError(
                details={"component": "state_store", "operation": operation},
            ) from None
        if not isinstance(result, expected_type):
            raise NsRuntimeStateStoreIndeterminateWriteError(
                details={"component": "state_store", "operation": operation},
            )
        return result

    def _validate_access(
        self,
        *,
        scope: StateAccessScope,
        key: StateKey,
        operation: str,
        document: StateDocument | None,
        caller_capability: StateCallerCapability,
        store_capability: StateStoreCapability,
    ) -> None:
        if not isinstance(scope, StateAccessScope):
            _invalid("scope")
        self._require_caller_capability(scope, caller_capability)
        self._require_authority(scope)
        self._require_store_capability(store_capability)
        self._validate_key_scope(scope, key)
        self._validate_resource(
            scope=scope,
            operation=operation,
            object_type=key.object_type,
            schema_name=None if document is None else document.schema_name,
        )

    def _require_caller_capability(
        self,
        scope: StateAccessScope,
        capability: StateCallerCapability,
    ) -> None:
        self._require_scope_issuer(scope)
        if capability not in scope.capabilities:
            raise NsRuntimeStateStoreCapabilityUnavailableError(
                details={
                    "component": "state_store",
                    "capability": capability.value,
                    "source": "caller",
                },
            )

    def _require_authority(self, scope: StateAccessScope) -> None:
        self._require_scope_issuer(scope)
        if scope.authority not in self._capabilities.authorities:
            raise NsRuntimeStateStoreCapabilityUnavailableError(
                details={
                    "component": "state_store",
                    "capability": "authority",
                    "source": "store",
                },
            )

    def _require_scope_issuer(self, scope: StateAccessScope) -> None:
        valid = False
        if type(scope) is StateAccessScope:
            if self.__scope_issuer is not None:
                valid = scope._issued_by(self.__scope_issuer)
            elif self.__production_scope_validator is not None:
                try:
                    valid = self.__production_scope_validator(scope) is True
                except BaseException:
                    valid = False
        if not valid:
            raise NsRuntimeStateStoreCapabilityUnavailableError(
                details={
                    "component": "state_store",
                    "capability": "authority",
                    "source": "caller",
                    "reason": "scope_issuer_mismatch",
                },
            )

    def _validate_resource(
        self,
        *,
        scope: StateAccessScope,
        operation: str,
        object_type: str,
        schema_name: str | None,
    ) -> None:
        self._require_scope_issuer(scope)
        policy = self._policy_for(scope)
        resources = {
            "read": policy[0] if policy else frozenset(),
            "scan": policy[0] if policy else frozenset(),
            "compare_and_set": policy[1] if policy else frozenset(),
            "transact": policy[1] if policy else frozenset(),
            "append": policy[2] if policy else frozenset(),
        }.get(operation, frozenset())
        if (
            self.__scope_issuer is not None
            and getattr(scope, "_policy_id", None) == "contract-test.v1"
        ):
            return
        if (
            (object_type, schema_name) not in resources
            and not (
                schema_name is None
                and any(item[0] == object_type for item in resources)
            )
        ):
            raise NsRuntimeStateStoreCapabilityUnavailableError(
                details={
                    "component": "state_store",
                    "capability": "resource",
                    "source": "caller",
                    "operation": operation,
                    "reason": "resource_policy_denied",
                },
            )

    def _validate_index_resource(
        self,
        scope: StateAccessScope,
        index: StateOrderedIndexKey,
    ) -> None:
        self._require_scope_issuer(scope)
        policy = self._policy_for(scope)
        if (
            self.__scope_issuer is not None
            and getattr(scope, "_policy_id", None) == "contract-test.v1"
        ):
            return
        allowed_indexes = policy[3] if policy else frozenset()
        allow_target = policy[4] if policy else False
        if (
            index.namespace != scope.namespace
            or (
                (index.name, index.bucket) not in allowed_indexes
                and not (
                    allow_target
                    and index.bucket == "delivery"
                    and __import__("re").fullmatch(
                        r"delivery\.target\.[0-9a-f]{64}", index.name,
                    ) is not None
                )
            )
        ):
            raise NsRuntimeStateStoreCapabilityUnavailableError(
                details={
                    "component": "state_store",
                    "capability": "ordered_index",
                    "source": "caller",
                    "reason": "resource_policy_denied",
                },
            )

    def _policy_for(self, scope: StateAccessScope) -> _PolicySpec | None:
        self._require_scope_issuer(scope)
        if self.__scope_issuer is not None:
            return None
        validator = self.__production_scope_validator
        if type(validator) is not _ProductionStateScopeValidator:
            return None
        return validator.policy_for(scope)

    def _require_store_capability(self, capability: StateStoreCapability) -> None:
        if not self._capabilities.supports(capability):
            raise NsRuntimeStateStoreCapabilityUnavailableError(
                details={
                    "component": "state_store",
                    "capability": capability.value,
                    "source": "store",
                },
            )

    @staticmethod
    def _validate_key_scope(scope: StateAccessScope, key: StateKey) -> None:
        if not isinstance(key, StateKey):
            raise NsRuntimeStateStoreNamespaceViolationError(
                details={
                    "component": "state_store",
                    "reason": "typed_key_required",
                },
            )
        if key.namespace != scope.namespace:
            raise NsRuntimeStateStoreNamespaceViolationError(
                details={
                    "component": "state_store",
                    "reason": "namespace_scope_mismatch",
                },
            )

    async def _enter_operation(self, operation: str) -> None:
        async with self._lifecycle_condition:
            if self._state is StateStoreLifecycleState.CLOSED:
                raise _closed(operation)
            if self._state is not StateStoreLifecycleState.OPEN:
                raise _not_ready(operation, self._state)
            self._active_operations += 1

    async def _exit_operation(self) -> None:
        async with self._lifecycle_condition:
            self._active_operations -= 1
            if self._active_operations == 0:
                self._lifecycle_condition.notify_all()

    def _local_health(self, status: StateStoreHealthStatus) -> StateStoreHealth:
        return StateStoreHealth(
            status=status,
            checked_at=self._clock.utc_now(),
            contract_generation=self._capabilities.contract_generation,
        )

    @abstractmethod
    async def _open(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def _close(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def _read(
        self,
        *,
        scope: StateAccessScope,
        key: StateKey,
        consistency: StateConsistency,
        minimum_revision: StateRevision | None,
    ) -> StateReadResult:
        raise NotImplementedError

    @abstractmethod
    async def _compare_and_set(
        self,
        *,
        scope: StateAccessScope,
        mutation: StateMutation,
    ) -> StateRecord | None:
        raise NotImplementedError

    @abstractmethod
    async def _scan(
        self,
        *,
        scope: StateAccessScope,
        object_type: str,
        cursor: str | None,
        limit: int,
    ) -> StateScanResult:
        raise NotImplementedError

    @abstractmethod
    async def _transact(
        self,
        transaction: StateTransaction,
    ) -> StateTransactionResult:
        raise NotImplementedError

    @abstractmethod
    async def _read_ordered_index(
        self, *, scope: StateAccessScope, index: StateOrderedIndexKey,
        limit: int, max_score: float | None,
        start_after: "StateOrderedIndexCursor | None",
    ) -> StateOrderedIndexReadResult:
        raise NotImplementedError

    @abstractmethod
    async def _append(
        self,
        *,
        scope: StateAccessScope,
        key: StateKey,
        document: StateDocument,
        assertion: StateAssertion | None,
    ) -> StateAppendResult:
        raise NotImplementedError

    @abstractmethod
    async def _health(self) -> StateStoreHealth:
        raise NotImplementedError


def _not_ready(
    operation: str,
    state: StateStoreLifecycleState,
) -> NsRuntimeStateStoreNotReadyError:
    return NsRuntimeStateStoreNotReadyError(
        details={
            "component": "state_store",
            "operation": operation,
            "state": state.value,
        },
    )


def _closed(operation: str) -> NsRuntimeStateStoreClosedError:
    return NsRuntimeStateStoreClosedError(
        details={
            "component": "state_store",
            "operation": operation,
            "state": StateStoreLifecycleState.CLOSED.value,
        },
    )


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "StateStore dependency or operation is invalid.",
        details={"component": "state_store", "field": field_name},
    )


__all__ = (
    "StateStore",
    "StateStoreLifecycleState",
)
