# -*- coding: utf-8 -*-
"""Backend-neutral StateStore lifecycle and operation boundary."""

from __future__ import annotations

import asyncio
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import hashlib
import hmac
from pathlib import Path
import secrets
import sys
from typing import Callable

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
    _StateResourcePolicy,
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


def _build_production_scope_validator_type() -> type:
    signing_key = secrets.token_bytes(32)

    class _ProductionStateScopeValidator:
        __slots__ = ("_callback", "_signature")

        def __init__(
            self,
            callback: Callable[[StateAccessScope], bool],
        ) -> None:
            caller = sys._getframe(1)
            if (
                caller.f_code.co_name != "create_state_store_composition"
                or not str(
                    Path(caller.f_code.co_filename).resolve(),
                ).replace("\\", "/").casefold().endswith(
                    "/state_store/composition.py",
                )
                or not callable(callback)
            ):
                _invalid("production_scope_validator")
            self._callback = callback
            self._signature = hmac.new(
                signing_key,
                str(id(callback)).encode("ascii"),
                hashlib.sha256,
            ).digest()

        def is_valid(self) -> bool:
            return bool(
                type(self) is _ProductionStateScopeValidator
                and hmac.compare_digest(
                    self._signature,
                    hmac.new(
                        signing_key,
                        str(id(self._callback)).encode("ascii"),
                        hashlib.sha256,
                    ).digest(),
                )
            )

        def __call__(self, scope: StateAccessScope) -> bool:
            if not self.is_valid():
                return False
            return self._callback(scope) is True

        def __copy__(self) -> "_ProductionStateScopeValidator":
            _invalid("production_scope_validator.copy")

        def __deepcopy__(
            self,
            memo: dict[int, object],
        ) -> "_ProductionStateScopeValidator":
            del memo
            _invalid("production_scope_validator.copy")

    return _ProductionStateScopeValidator


_ProductionStateScopeValidator = _build_production_scope_validator_type()
del _build_production_scope_validator_type
_PRODUCTION_SCOPE_VALIDATOR_IS_VALID = _ProductionStateScopeValidator.is_valid


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
        "_issue_atomic_scope", "_is_current_repository",
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
        if (
            type(self) is not StateStoreRepository
            or not self._is_current_repository(self)
        ):
            _invalid("repository.scope")
        value = self._issue_atomic_scope(atomic_scope)
        if type(value) is not StateAccessScope:
            _invalid("repository.scope")
        return value

    def _require_role(self, role: StateStoreRepositoryRole) -> None:
        if (
            not isinstance(role, StateStoreRepositoryRole)
            or self._role is not role
            or not self._is_current_repository(self)
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
    issue_atomic_scope: Callable[[StateAtomicScope], StateAccessScope],
    is_current_repository: Callable[[StateStoreRepository], bool],
) -> StateStoreRepository:
    """Low-level value assembly; authority remains in the supplied closures."""

    if (
        not isinstance(store, StateStore)
        or not isinstance(role, StateStoreRepositoryRole)
        or not callable(issue_atomic_scope)
        or not callable(is_current_repository)
    ):
        _invalid("repository.binding")
    value = object.__new__(StateStoreRepository)
    value._store = store
    value._role = role
    value._runtime_id = runtime_id
    value._audit_namespace = audit_namespace
    value._issue_atomic_scope = issue_atomic_scope
    value._is_current_repository = is_current_repository
    return value


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
                or getattr(
                    type(_production_scope_validator),
                    "is_valid",
                    None,
                ) is not _PRODUCTION_SCOPE_VALIDATOR_IS_VALID
                or not _production_scope_validator.is_valid()
            ):
                _invalid("production_scope_validator")
            else:
                self.__production_scope_validator = (
                    _production_scope_validator
                )
        self._state = StateStoreLifecycleState.NEW
        self._lifecycle_condition = asyncio.Condition()
        self._active_operations = 0

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
        policy = getattr(scope, "_resource_policy", None)
        if (
            type(policy) is not _StateResourcePolicy
            or not policy.allows_resource(
                operation=operation,
                object_type=object_type,
                schema_name=schema_name,
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
        policy = getattr(scope, "_resource_policy", None)
        if (
            type(policy) is not _StateResourcePolicy
            or (
                not policy.allow_contract_test_resources
                and index.namespace != scope.namespace
            )
            or not policy.allows_index(index.name, index.bucket)
        ):
            raise NsRuntimeStateStoreCapabilityUnavailableError(
                details={
                    "component": "state_store",
                    "capability": "ordered_index",
                    "source": "caller",
                    "reason": "resource_policy_denied",
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
