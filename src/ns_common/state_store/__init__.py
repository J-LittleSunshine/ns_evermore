# -*- coding: utf-8 -*-
"""P08 backend-neutral StateStore authority contract."""

from .authority import (
    STATE_AUTHORITY_BOUNDARIES,
    StateAccessScope,
    StateAtomicScope,
    StateAuthorityClassification,
    StateAuthorityKind,
    StateCallerCapability,
    StateNamespace,
    StateNamespaceKind,
    StateStoreCapabilities,
    StateStoreCapability,
    classify_state_authority,
)
from .model import (
    StateAppendResult,
    StateAssertion,
    StateConsistency,
    StateDocument,
    StateKey,
    StateMutation,
    StateMutationKind,
    StateReadResult,
    StateRecord,
    StateRevision,
    StateStoreHealth,
    StateStoreHealthStatus,
    StateTransaction,
    StateTransactionResult,
)
from .store import StateStore, StateStoreLifecycleState


__all__ = (
    "STATE_AUTHORITY_BOUNDARIES",
    "StateAccessScope",
    "StateAppendResult",
    "StateAssertion",
    "StateAtomicScope",
    "StateAuthorityClassification",
    "StateAuthorityKind",
    "StateCallerCapability",
    "StateConsistency",
    "StateDocument",
    "StateKey",
    "StateMutation",
    "StateMutationKind",
    "StateNamespace",
    "StateNamespaceKind",
    "StateReadResult",
    "StateRecord",
    "StateRevision",
    "StateStore",
    "StateStoreCapabilities",
    "StateStoreCapability",
    "StateStoreHealth",
    "StateStoreHealthStatus",
    "StateStoreLifecycleState",
    "StateTransaction",
    "StateTransactionResult",
    "classify_state_authority",
)
