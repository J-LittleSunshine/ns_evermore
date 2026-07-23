# -*- coding: utf-8 -*-
"""Backend-neutral StateStore lifecycle and operation boundary."""

from __future__ import annotations

import asyncio
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import hashlib

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
    _issue_state_access_scope,
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


class StateStoreRepositoryRole(str, Enum):
    STRONG_AUDIT = "strong_audit"
    DELIVERY_ADMISSION = "delivery_admission"
    DELIVERY_SCHEDULER = "delivery_scheduler"
    DELIVERY_PAYLOAD = "delivery_payload"
    DELIVERY_REGISTRY = "delivery_registry"


class StateStoreRepository:
    """Opaque fixed-capability repository handle issued by one composition."""

    __slots__ = (
        "_store", "_role", "_runtime_id", "_audit_namespace",
    )

    def __init__(
        self,
        *,
        store: "StateStore",
        role: StateStoreRepositoryRole,
        runtime_id: str | None,
        audit_namespace: StateNamespace | None,
        _token: object,
    ) -> None:
        if (
            type(self) is not StateStoreRepository
            or not isinstance(store, StateStore)
            or not store._consume_repository_token(_token)
        ):
            _invalid("repository.issuer")
        self._store = store
        self._role = role
        self._runtime_id = runtime_id
        self._audit_namespace = audit_namespace

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
        return self._store._scope_for_repository(
            self,
            StateAtomicScope(
                namespace=StateNamespace.tenant(
                    tenant_id=tenant_id,
                    domain="delivery",
                ),
                partition=f"layout-{layout_generation}-bucket-{bucket_id}",
            ),
        )

    def registry_scope(self) -> StateAccessScope:
        if (
            self._role is not StateStoreRepositoryRole.DELIVERY_REGISTRY
            or self._runtime_id is None
        ):
            _invalid("repository.registry_scope")
        synthetic_tenant = "runtime-registry:" + hashlib.sha256(
            self._runtime_id.encode(),
        ).hexdigest()
        return self._store._scope_for_repository(
            self,
            StateAtomicScope(
                namespace=StateNamespace.tenant(
                    tenant_id=synthetic_tenant,
                    domain="delivery",
                ),
                partition="authority-registry",
            ),
        )

    def audit_scope(self) -> StateAccessScope:
        if (
            self._role is not StateStoreRepositoryRole.STRONG_AUDIT
            or self._audit_namespace is None
        ):
            _invalid("repository.audit_scope")
        return self._store._scope_for_repository(
            self,
            StateAtomicScope(
                namespace=self._audit_namespace,
                partition="processor-final",
            ),
        )

    def _require_role(self, role: StateStoreRepositoryRole) -> None:
        if (
            not isinstance(role, StateStoreRepositoryRole)
            or self._role is not role
            or not self._store._owns_repository(self)
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
        _repository_owner: object | None = None,
    ) -> None:
        if not isinstance(capabilities, StateStoreCapabilities):
            _invalid("capabilities")
        if not isinstance(clock, Clock):
            _invalid("clock")
        self._capabilities = capabilities
        self._clock = clock
        if type(_contract_test_authority) is not bool:
            _invalid("contract_test_authority")
        self.__scope_issuer = (
            _scope_issuer
            if _scope_issuer is not None
            else _new_state_scope_issuer(
                contract_test=_contract_test_authority,
            )
        )
        self.__repository_owner = _repository_owner
        self.__repositories: list[StateStoreRepository] = []
        self.__pending_repository_token: object | None = None
        self._state = StateStoreLifecycleState.NEW
        self._lifecycle_condition = asyncio.Condition()
        self._active_operations = 0

    @property
    def state(self) -> StateStoreLifecycleState:
        return self._state

    def capabilities(self) -> StateStoreCapabilities:
        return self._capabilities

    def _create_repository(
        self,
        *,
        owner: object,
        role: StateStoreRepositoryRole,
        runtime_id: str | None = None,
        audit_namespace: StateNamespace | None = None,
    ) -> StateStoreRepository:
        """Create one fixed role only for the composition that owns this store."""

        if (
            owner is None
            or owner is not self.__repository_owner
            or not isinstance(role, StateStoreRepositoryRole)
        ):
            _invalid("repository.owner")
        if role is StateStoreRepositoryRole.STRONG_AUDIT:
            if (
                not isinstance(audit_namespace, StateNamespace)
                or audit_namespace.kind is not StateNamespaceKind.AUDIT
                or runtime_id is not None
            ):
                _invalid("repository.audit_namespace")
        elif role is StateStoreRepositoryRole.DELIVERY_REGISTRY:
            if type(runtime_id) is not str or not runtime_id or audit_namespace is not None:
                _invalid("repository.runtime_id")
        elif runtime_id is None or type(runtime_id) is not str or not runtime_id:
            _invalid("repository.runtime_id")
        elif audit_namespace is not None:
            _invalid("repository.audit_namespace")
        token = object()
        self.__pending_repository_token = token
        try:
            repository = StateStoreRepository(
                store=self,
                role=role,
                runtime_id=runtime_id,
                audit_namespace=audit_namespace,
                _token=token,
            )
        finally:
            self.__pending_repository_token = None
        self.__repositories.append(repository)
        return repository

    def _consume_repository_token(self, token: object) -> bool:
        return token is not None and self.__pending_repository_token is token

    def _owns_repository(self, repository: StateStoreRepository) -> bool:
        return bool(
            type(repository) is StateStoreRepository
            and repository._store is self
            and any(repository is current for current in self.__repositories)
        )

    def _scope_for_repository(
        self,
        repository: StateStoreRepository,
        atomic_scope: StateAtomicScope,
    ) -> StateAccessScope:
        if not self._owns_repository(repository):
            _invalid("repository.scope")
        specs = {
            StateStoreRepositoryRole.STRONG_AUDIT: (
                StateAuthorityKind.STRONG_AUDIT,
                "strong-audit-authority",
                frozenset({StateCallerCapability.APPEND}),
            ),
            StateStoreRepositoryRole.DELIVERY_ADMISSION: (
                StateAuthorityKind.DELIVERY_ADMISSION,
                "delivery.admission",
                frozenset({
                    StateCallerCapability.READ,
                    StateCallerCapability.TRANSACT,
                    StateCallerCapability.ORDERED_INDEX,
                    StateCallerCapability.APPEND,
                }),
            ),
            StateStoreRepositoryRole.DELIVERY_SCHEDULER: (
                StateAuthorityKind.DELIVERY_ADMISSION,
                "delivery.scheduling",
                frozenset({
                    StateCallerCapability.READ,
                    StateCallerCapability.TRANSACT,
                    StateCallerCapability.ORDERED_INDEX,
                    StateCallerCapability.APPEND,
                }),
            ),
            StateStoreRepositoryRole.DELIVERY_PAYLOAD: (
                StateAuthorityKind.DELIVERY_ADMISSION,
                "delivery.payload_authority",
                frozenset({StateCallerCapability.READ}),
            ),
            StateStoreRepositoryRole.DELIVERY_REGISTRY: (
                StateAuthorityKind.DELIVERY_ADMISSION,
                "delivery.authority_registry",
                frozenset({
                    StateCallerCapability.READ,
                    StateCallerCapability.TRANSACT,
                    StateCallerCapability.ORDERED_INDEX,
                }),
            ),
        }
        authority, caller, capabilities = specs[repository.role]
        return _issue_state_access_scope(
            self.__scope_issuer,
            atomic_scope=atomic_scope,
            authority=authority,
            caller=caller,
            capabilities=capabilities,
        )

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
        for assertion in transaction.record_assertions:
            self._validate_key_scope(scope, assertion.key)
        for mutation in transaction.ordered_index_mutations:
            if (mutation.index.namespace != scope.namespace
                    and mutation.index.namespace.kind is not StateNamespaceKind.SYSTEM):
                raise NsRuntimeStateStoreNamespaceViolationError(details={
                    "component": "state_store", "reason": "namespace_scope_mismatch",
                })
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
        for append in transaction.log_appends:
            self._validate_key_scope(scope, append.key)
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
        caller_capability: StateCallerCapability,
        store_capability: StateStoreCapability,
    ) -> None:
        if not isinstance(scope, StateAccessScope):
            _invalid("scope")
        self._require_caller_capability(scope, caller_capability)
        self._require_authority(scope)
        self._require_store_capability(store_capability)
        self._validate_key_scope(scope, key)

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
        if (
            type(scope) is not StateAccessScope
            or not scope._issued_by(self.__scope_issuer)
        ):
            raise NsRuntimeStateStoreCapabilityUnavailableError(
                details={
                    "component": "state_store",
                    "capability": "authority",
                    "source": "caller",
                    "reason": "scope_issuer_mismatch",
                },
            )

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
