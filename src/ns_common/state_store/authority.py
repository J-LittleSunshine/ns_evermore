# -*- coding: utf-8 -*-
"""State authority, namespace, and caller capability contracts for P08."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from ns_common.exceptions import NsValidationError


_NAME_PATTERN = re.compile(r"[a-z][a-z0-9_.-]{0,127}")
_SCOPE_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,255}")


class StateAuthorityKind(str, Enum):
    CONNECTION = "connection"
    SESSION = "session"
    PERMISSION_SNAPSHOT = "permission_snapshot"
    CREDENTIAL = "credential"
    PROCESSOR_EXECUTION = "processor_execution"
    STRONG_AUDIT = "strong_audit"
    DELIVERY_ADMISSION = "delivery_admission"
    FUTURE_AUTHORITY = "future_authority"


class StateAuthorityClassification(str, Enum):
    LOCAL = "local"
    EXTERNAL = "external"
    TRANSIENT = "transient"
    STATE_STORE = "state_store"
    RESERVED = "reserved"


STATE_AUTHORITY_BOUNDARIES: Mapping[
    StateAuthorityKind,
    StateAuthorityClassification,
] = MappingProxyType({
    StateAuthorityKind.CONNECTION: StateAuthorityClassification.LOCAL,
    StateAuthorityKind.SESSION: StateAuthorityClassification.LOCAL,
    StateAuthorityKind.PERMISSION_SNAPSHOT: StateAuthorityClassification.EXTERNAL,
    StateAuthorityKind.CREDENTIAL: StateAuthorityClassification.EXTERNAL,
    StateAuthorityKind.PROCESSOR_EXECUTION: StateAuthorityClassification.TRANSIENT,
    StateAuthorityKind.STRONG_AUDIT: StateAuthorityClassification.STATE_STORE,
    StateAuthorityKind.DELIVERY_ADMISSION: StateAuthorityClassification.STATE_STORE,
    StateAuthorityKind.FUTURE_AUTHORITY: StateAuthorityClassification.RESERVED,
})


def classify_state_authority(
    authority: StateAuthorityKind,
) -> StateAuthorityClassification:
    if not isinstance(authority, StateAuthorityKind):
        _invalid("authority")
    return STATE_AUTHORITY_BOUNDARIES[authority]


class StateStoreCapability(str, Enum):
    READ = "read"
    COMPARE_AND_SET = "compare_and_set"
    TRANSACTION = "transaction"
    APPEND = "append"
    LINEARIZABLE_READ = "linearizable_read"
    MINIMUM_REVISION_READ = "minimum_revision_read"
    STALE_READ = "stale_read"
    SCAN = "scan"


class StateCallerCapability(str, Enum):
    READ = "read"
    COMPARE_AND_SET = "compare_and_set"
    TRANSACT = "transact"
    APPEND = "append"
    SCAN = "scan"


@dataclass(frozen=True, slots=True, kw_only=True)
class StateStoreCapabilities:
    features: frozenset[StateStoreCapability]
    authorities: frozenset[StateAuthorityKind]
    contract_generation: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.features, frozenset) or any(
            not isinstance(value, StateStoreCapability)
            for value in self.features
        ):
            _invalid("features")
        if not isinstance(self.authorities, frozenset) or any(
            not isinstance(value, StateAuthorityKind)
            for value in self.authorities
        ):
            _invalid("authorities")
        if any(
            classify_state_authority(value)
            is not StateAuthorityClassification.STATE_STORE
            for value in self.authorities
        ):
            _invalid("authorities.classification")
        if (
            isinstance(self.contract_generation, bool)
            or not isinstance(self.contract_generation, int)
            or self.contract_generation <= 0
        ):
            _invalid("contract_generation")

    def supports(self, capability: StateStoreCapability) -> bool:
        if not isinstance(capability, StateStoreCapability):
            _invalid("capability")
        return capability in self.features

    @classmethod
    def p08_contract(cls) -> "StateStoreCapabilities":
        return cls(
            features=frozenset(StateStoreCapability),
            authorities=frozenset({StateAuthorityKind.STRONG_AUDIT}),
        )

    @classmethod
    def p10_contract(cls) -> "StateStoreCapabilities":
        """Capabilities required by the DR-1 admission authority."""
        return cls(
            features=frozenset(StateStoreCapability),
            authorities=frozenset({
                StateAuthorityKind.STRONG_AUDIT,
                StateAuthorityKind.DELIVERY_ADMISSION,
            }),
        )


class StateNamespaceKind(str, Enum):
    TENANT = "tenant"
    SYSTEM = "system"
    RUNTIME = "runtime"
    PLUGIN = "plugin"
    AUDIT = "audit"


@dataclass(frozen=True, slots=True, kw_only=True)
class StateNamespace:
    kind: StateNamespaceKind
    domain: str
    tenant_id: str | None = None
    runtime_id: str | None = None
    plugin_name: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, StateNamespaceKind):
            _invalid("namespace.kind")
        _validate_name(self.domain, "namespace.domain")
        for field_name in ("tenant_id", "runtime_id"):
            value = getattr(self, field_name)
            if value is not None:
                _validate_scope_id(value, f"namespace.{field_name}")
        if self.plugin_name is not None:
            _validate_name(self.plugin_name, "namespace.plugin_name")

        if self.kind is StateNamespaceKind.TENANT:
            if (
                self.tenant_id is None
                or self.runtime_id is not None
                or self.plugin_name is not None
            ):
                _invalid("namespace.tenant_dimensions")
        elif self.kind is StateNamespaceKind.SYSTEM:
            dimensions = (self.tenant_id, self.runtime_id, self.plugin_name)
            if any(value is not None for value in dimensions):
                _invalid("namespace.system_dimensions")
        elif self.kind is StateNamespaceKind.RUNTIME:
            if (
                self.runtime_id is None
                or self.tenant_id is not None
                or self.plugin_name is not None
            ):
                _invalid("namespace.runtime_dimensions")
        elif self.kind is StateNamespaceKind.PLUGIN:
            if self.plugin_name is None or self.runtime_id is not None:
                _invalid("namespace.plugin_dimensions")
        elif self.kind is StateNamespaceKind.AUDIT:
            if self.runtime_id is not None or self.plugin_name is not None:
                _invalid("namespace.audit_dimensions")

    @classmethod
    def tenant(cls, *, tenant_id: str, domain: str) -> "StateNamespace":
        return cls(kind=StateNamespaceKind.TENANT, tenant_id=tenant_id, domain=domain)

    @classmethod
    def system(cls, *, domain: str) -> "StateNamespace":
        return cls(kind=StateNamespaceKind.SYSTEM, domain=domain)

    @classmethod
    def runtime(cls, *, runtime_id: str, domain: str) -> "StateNamespace":
        return cls(kind=StateNamespaceKind.RUNTIME, runtime_id=runtime_id, domain=domain)

    @classmethod
    def plugin(
        cls,
        *,
        plugin_name: str,
        domain: str,
        tenant_id: str | None = None,
    ) -> "StateNamespace":
        return cls(
            kind=StateNamespaceKind.PLUGIN,
            plugin_name=plugin_name,
            tenant_id=tenant_id,
            domain=domain,
        )

    @classmethod
    def audit(
        cls,
        *,
        domain: str,
        tenant_id: str | None = None,
    ) -> "StateNamespace":
        return cls(
            kind=StateNamespaceKind.AUDIT,
            domain=domain,
            tenant_id=tenant_id,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class StateAtomicScope:
    namespace: StateNamespace
    partition: str

    def __post_init__(self) -> None:
        if not isinstance(self.namespace, StateNamespace):
            _invalid("atomic_scope.namespace")
        _validate_name(self.partition, "atomic_scope.partition")


@dataclass(frozen=True, slots=True, kw_only=True)
class StateAccessScope:
    atomic_scope: StateAtomicScope
    authority: StateAuthorityKind
    caller: str
    capabilities: frozenset[StateCallerCapability]

    def __post_init__(self) -> None:
        if not isinstance(self.atomic_scope, StateAtomicScope):
            _invalid("access_scope.atomic_scope")
        if not isinstance(self.authority, StateAuthorityKind):
            _invalid("access_scope.authority")
        classification = classify_state_authority(self.authority)
        if classification is not StateAuthorityClassification.STATE_STORE:
            _invalid("access_scope.authority_classification")
        _validate_name(self.caller, "access_scope.caller")
        if not isinstance(self.capabilities, frozenset) or any(
            not isinstance(value, StateCallerCapability)
            for value in self.capabilities
        ):
            _invalid("access_scope.capabilities")
        if not self.capabilities:
            _invalid("access_scope.capabilities")
        if self.authority is StateAuthorityKind.STRONG_AUDIT:
            if self.atomic_scope.namespace.kind is not StateNamespaceKind.AUDIT:
                _invalid("access_scope.strong_audit_namespace")
        elif self.authority is StateAuthorityKind.DELIVERY_ADMISSION:
            if self.atomic_scope.namespace.kind is not StateNamespaceKind.TENANT:
                _invalid("access_scope.delivery_admission_namespace")
            if self.atomic_scope.namespace.domain != "delivery":
                _invalid("access_scope.delivery_admission_domain")

    @property
    def namespace(self) -> StateNamespace:
        return self.atomic_scope.namespace


def _validate_name(value: object, field_name: str) -> None:
    if not isinstance(value, str) or _NAME_PATTERN.fullmatch(value) is None:
        _invalid(field_name)


def _validate_scope_id(value: object, field_name: str) -> None:
    if not isinstance(value, str) or _SCOPE_ID_PATTERN.fullmatch(value) is None:
        _invalid(field_name)


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "StateStore authority value is invalid.",
        details={"component": "state_store_authority", "field": field_name},
    )


__all__ = (
    "STATE_AUTHORITY_BOUNDARIES",
    "StateAccessScope",
    "StateAtomicScope",
    "StateAuthorityClassification",
    "StateAuthorityKind",
    "StateCallerCapability",
    "StateNamespace",
    "StateNamespaceKind",
    "StateStoreCapabilities",
    "StateStoreCapability",
    "classify_state_authority",
)
