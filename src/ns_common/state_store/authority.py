# -*- coding: utf-8 -*-
"""State authority, namespace, and caller capability contracts for P08."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
from dataclasses import dataclass, field as dataclass_field
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
    ORDERED_INDEX = "ordered_index"


class StateCallerCapability(str, Enum):
    READ = "read"
    COMPARE_AND_SET = "compare_and_set"
    TRANSACT = "transact"
    APPEND = "append"
    SCAN = "scan"
    ORDERED_INDEX = "ordered_index"


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


class _StateScopeIssuer:
    """One store-owned capability issuer; never shared through a registry."""

    __slots__ = ("realm", "_key", "_identity")

    def __init__(self, *, realm: str) -> None:
        if realm != "contract_test":
            _invalid("issuer.realm")
        self.realm = realm
        self._identity = secrets.token_bytes(32)
        self._key = secrets.token_bytes(32)


@dataclass(frozen=True, slots=True, kw_only=True)
class _StateResourcePolicy:
    """Issuer-owned exact resource policy carried by one repository scope."""

    read_resources: frozenset[tuple[str, str]] = frozenset()
    transact_resources: frozenset[tuple[str, str]] = frozenset()
    append_resources: frozenset[tuple[str, str]] = frozenset()
    ordered_indexes: frozenset[tuple[str, str]] = frozenset()
    allow_delivery_target_index: bool = False
    allow_contract_test_resources: bool = False

    def __post_init__(self) -> None:
        for field_name in (
            "read_resources",
            "transact_resources",
            "append_resources",
        ):
            values = getattr(self, field_name)
            if not isinstance(values, frozenset) or any(
                not isinstance(value, tuple)
                or len(value) != 2
                or any(
                    not isinstance(part, str)
                    or _NAME_PATTERN.fullmatch(part) is None
                    for part in value
                )
                for value in values
            ):
                _invalid(f"resource_policy.{field_name}")
        if not isinstance(self.ordered_indexes, frozenset) or any(
            not isinstance(value, tuple)
            or len(value) != 2
            or any(
                not isinstance(part, str)
                or _NAME_PATTERN.fullmatch(part) is None
                for part in value
            )
            for value in self.ordered_indexes
        ):
            _invalid("resource_policy.ordered_indexes")
        if (
            type(self.allow_delivery_target_index) is not bool
            or type(self.allow_contract_test_resources) is not bool
        ):
            _invalid("resource_policy.flags")
        if self.allow_contract_test_resources and any((
            self.read_resources,
            self.transact_resources,
            self.append_resources,
            self.ordered_indexes,
            self.allow_delivery_target_index,
        )):
            _invalid("resource_policy.contract_test")

    def allows_resource(
        self,
        *,
        operation: str,
        object_type: str,
        schema_name: str | None,
    ) -> bool:
        if self.allow_contract_test_resources:
            return True
        resources = {
            "read": self.read_resources,
            "compare_and_set": self.transact_resources,
            "scan": self.read_resources,
            "transact": self.transact_resources,
            "append": self.append_resources,
        }.get(operation)
        if resources is None:
            return False
        if schema_name is None:
            return any(value[0] == object_type for value in resources)
        return (object_type, schema_name) in resources

    def allows_index(self, name: str, bucket: str) -> bool:
        if (
            self.allow_contract_test_resources
            or (name, bucket) in self.ordered_indexes
        ):
            return True
        if not self.allow_delivery_target_index:
            return False
        return bool(
            bucket == "delivery"
            and re.fullmatch(
                r"delivery\.target\.[0-9a-f]{64}",
                name,
            ) is not None
        )

    def canonical_values(self) -> Mapping[str, object]:
        return {
            "read_resources": sorted(
                [list(value) for value in self.read_resources],
            ),
            "transact_resources": sorted(
                [list(value) for value in self.transact_resources],
            ),
            "append_resources": sorted(
                [list(value) for value in self.append_resources],
            ),
            "ordered_indexes": sorted(
                [list(value) for value in self.ordered_indexes],
            ),
            "allow_delivery_target_index": self.allow_delivery_target_index,
            "allow_contract_test_resources": self.allow_contract_test_resources,
        }


_CONTRACT_TEST_RESOURCE_POLICY = _StateResourcePolicy(
    allow_contract_test_resources=True,
)


@dataclass(frozen=True, slots=True, kw_only=True, init=False)
class StateAccessScope:
    atomic_scope: StateAtomicScope
    authority: StateAuthorityKind
    caller: str
    capabilities: frozenset[StateCallerCapability]
    _issuer_realm: str = dataclass_field(
        init=False, repr=False, compare=False,
    )
    _issuer_identity: bytes = dataclass_field(
        init=False, repr=False, compare=False,
    )
    _authority_signature: bytes = dataclass_field(
        init=False, repr=False, compare=False,
    )
    _policy_id: str = dataclass_field(
        init=False, repr=False, compare=False,
    )
    _repository_binding: object | None = dataclass_field(
        init=False, repr=False, compare=False,
    )

    def __init__(
        self,
        *,
        atomic_scope: StateAtomicScope,
        authority: StateAuthorityKind,
        caller: str,
        capabilities: frozenset[StateCallerCapability],
        _issuer: _StateScopeIssuer | None = None,
        _resource_policy: _StateResourcePolicy | None = None,
        _repository_binding: object | None = None,
        _policy_id: str | None = None,
    ) -> None:
        if (
            type(self) is not StateAccessScope
            or type(_issuer) is not _StateScopeIssuer
            or _issuer.realm != "contract_test"
            or _resource_policy is not _CONTRACT_TEST_RESOURCE_POLICY
            or _repository_binding is not None
            or _policy_id is not None
        ):
            _invalid("access_scope.issuer")
        for name, value in (
            ("atomic_scope", atomic_scope),
            ("authority", authority),
            ("caller", caller),
            ("capabilities", capabilities),
            ("_issuer_realm", _issuer.realm),
            ("_issuer_identity", _issuer._identity),
            ("_authority_signature", b""),
            ("_policy_id", "contract-test.v1"),
            ("_repository_binding", _repository_binding),
        ):
            object.__setattr__(self, name, value)
        self.__post_init__()
        object.__setattr__(
            self,
            "_authority_signature",
            _state_scope_signature(self, issuer=_issuer),
        )

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

    def _issued_by(self, issuer: _StateScopeIssuer) -> bool:
        if (
            type(self) is not StateAccessScope
            or type(issuer) is not _StateScopeIssuer
            or self._issuer_realm != issuer.realm
            or not hmac.compare_digest(
                self._issuer_identity,
                issuer._identity,
            )
        ):
            return False
        if issuer.realm == "contract_test":
            return hmac.compare_digest(
                self._authority_signature,
                _state_scope_signature(self, issuer=issuer),
            )
        return False


def _new_state_scope_issuer(*, contract_test: bool = False) -> _StateScopeIssuer:
    if not contract_test:
        _invalid("issuer.production_removed")
    return _StateScopeIssuer(
        realm="contract_test",
    )


def _issue_state_access_scope(
    issuer: _StateScopeIssuer,
    *,
    atomic_scope: StateAtomicScope,
    authority: StateAuthorityKind,
    caller: str,
    capabilities: frozenset[StateCallerCapability],
    resource_policy: _StateResourcePolicy | None = None,
    repository_binding: object | None = None,
) -> StateAccessScope:
    if type(issuer) is not _StateScopeIssuer:
        _invalid("access_scope.issuer")
    if issuer.realm == "contract_test":
        if resource_policy is not None or repository_binding is not None:
            _invalid("access_scope.contract_test_policy")
        resource_policy = _CONTRACT_TEST_RESOURCE_POLICY
    else:
        _invalid("access_scope.production_issuer_removed")
    return StateAccessScope(
        atomic_scope=atomic_scope,
        authority=authority,
        caller=caller,
        capabilities=capabilities,
        _issuer=issuer,
        _resource_policy=resource_policy,
        _repository_binding=repository_binding,
    )


def _state_scope_signature(
    scope: StateAccessScope,
    *,
    issuer: _StateScopeIssuer,
) -> bytes:
    if type(issuer) is not _StateScopeIssuer:
        _invalid("access_scope.issuer")
    payload = _state_scope_payload(scope)
    return hmac.new(issuer._key, payload, hashlib.sha256).digest()


def _state_scope_payload(scope: StateAccessScope) -> bytes:
    namespace = scope.atomic_scope.namespace
    return json.dumps({
        "issuer_realm": scope._issuer_realm,
        "issuer_identity": scope._issuer_identity.hex(),
        "namespace_kind": namespace.kind.value,
        "domain": namespace.domain,
        "tenant_id": namespace.tenant_id,
        "runtime_id": namespace.runtime_id,
        "plugin_name": namespace.plugin_name,
        "partition": scope.atomic_scope.partition,
        "authority": scope.authority.value,
        "caller": scope.caller,
        "capabilities": sorted(value.value for value in scope.capabilities),
        "policy_id": scope._policy_id,
        "repository_binding": (
            None
            if scope._repository_binding is None
            else id(scope._repository_binding)
        ),
    }, sort_keys=True, separators=(",", ":")).encode("utf-8")


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
