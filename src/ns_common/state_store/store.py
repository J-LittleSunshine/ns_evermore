# -*- coding: utf-8 -*-
"""Backend-neutral StateStore lifecycle and operation boundary."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from enum import Enum

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
)
from .model import (
    StateAppendResult,
    StateAssertion,
    StateConsistency,
    StateDocument,
    StateKey,
    StateMutation,
    StateReadResult,
    StateRecord,
    StateRevision,
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
    ) -> None:
        if not isinstance(capabilities, StateStoreCapabilities):
            _invalid("capabilities")
        if not isinstance(clock, Clock):
            _invalid("clock")
        self._capabilities = capabilities
        self._clock = clock
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
        for mutation in transaction.mutations:
            self._validate_key_scope(scope, mutation.key)
        await self._enter_operation("transact")
        try:
            return await self._run_write(
                "transact",
                self._transact(transaction),
                expected_type=StateTransactionResult,
            )
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
        if capability not in scope.capabilities:
            raise NsRuntimeStateStoreCapabilityUnavailableError(
                details={
                    "component": "state_store",
                    "capability": capability.value,
                    "source": "caller",
                },
            )

    def _require_authority(self, scope: StateAccessScope) -> None:
        if scope.authority not in self._capabilities.authorities:
            raise NsRuntimeStateStoreCapabilityUnavailableError(
                details={
                    "component": "state_store",
                    "capability": "authority",
                    "source": "store",
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
    async def _transact(
        self,
        transaction: StateTransaction,
    ) -> StateTransactionResult:
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
