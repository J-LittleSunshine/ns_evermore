# -*- coding: utf-8 -*-
"""Extension namespace registration and fail-closed schema boundaries."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Iterable, Mapping

from ns_common.exceptions import (
    NsRuntimeEnvelopeSchemaError,
    NsRuntimeUnauthorizedMessageTypeError,
)

from .models import ExtensionsGroup, JSONValue


_NAMESPACE_PATTERN = re.compile(
    r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+"
)


class UnknownExtensionPolicy(str, Enum):
    REJECT = "reject"
    IGNORE_AND_AUDIT = "ignore_and_audit"


@dataclass(frozen=True, slots=True)
class ExtensionObjectSchema:
    required_fields: tuple[str, ...] = ()
    optional_fields: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("required_fields", self.required_fields),
            ("optional_fields", self.optional_fields),
        ):
            if not isinstance(value, tuple) or any(
                not isinstance(item, str) or not item for item in value
            ):
                raise TypeError(f"{name} must be a tuple of non-empty strings")
            if len(set(value)) != len(value):
                raise ValueError(f"{name} must not contain duplicates")
        if set(self.required_fields) & set(self.optional_fields):
            raise ValueError("extension required and optional fields must be disjoint")

    @property
    def allowed_fields(self) -> frozenset[str]:
        return frozenset((*self.required_fields, *self.optional_fields))


@dataclass(frozen=True, slots=True)
class ExtensionNamespaceContract:
    namespace: str
    schema: ExtensionObjectSchema
    required_capabilities: tuple[str, ...] = ()
    enabled: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.namespace, str) or _NAMESPACE_PATTERN.fullmatch(
            self.namespace
        ) is None:
            raise ValueError("namespace must use dotted lowercase naming")
        if not isinstance(self.schema, ExtensionObjectSchema):
            raise TypeError("schema must be ExtensionObjectSchema")
        if not isinstance(self.required_capabilities, tuple) or any(
            not isinstance(item, str) or not item
            for item in self.required_capabilities
        ):
            raise TypeError(
                "required_capabilities must be a tuple of non-empty strings"
            )
        if len(set(self.required_capabilities)) != len(self.required_capabilities):
            raise ValueError("required_capabilities must not contain duplicates")
        if type(self.enabled) is not bool:
            raise TypeError("enabled must be a boolean")


@dataclass(frozen=True, slots=True)
class ExtensionValidationResult:
    accepted: Mapping[str, Mapping[str, JSONValue]]
    ignored_count: int
    audit_required: bool


@dataclass(frozen=True, slots=True, init=False)
class ExtensionNamespaceRegistry:
    _contracts: tuple[ExtensionNamespaceContract, ...] = field(repr=False)
    _by_namespace: Mapping[str, ExtensionNamespaceContract] = field(repr=False)
    _unknown_policy: UnknownExtensionPolicy

    def __init__(
        self,
        contracts: Iterable[ExtensionNamespaceContract] = (),
        *,
        unknown_policy: UnknownExtensionPolicy = UnknownExtensionPolicy.REJECT,
    ) -> None:
        if not isinstance(unknown_policy, UnknownExtensionPolicy):
            raise TypeError("unknown_policy must be UnknownExtensionPolicy")
        values = tuple(contracts)
        by_namespace: dict[str, ExtensionNamespaceContract] = {}
        for contract in values:
            if not isinstance(contract, ExtensionNamespaceContract):
                raise TypeError("registry entries must be ExtensionNamespaceContract")
            if contract.namespace in by_namespace:
                raise ValueError("extension namespaces must be unique")
            by_namespace[contract.namespace] = contract
        object.__setattr__(self, "_contracts", values)
        object.__setattr__(self, "_by_namespace", MappingProxyType(by_namespace))
        object.__setattr__(self, "_unknown_policy", unknown_policy)

    @property
    def contracts(self) -> tuple[ExtensionNamespaceContract, ...]:
        return self._contracts

    @property
    def unknown_policy(self) -> UnknownExtensionPolicy:
        return self._unknown_policy

    def validate(
        self,
        extensions: ExtensionsGroup | None,
        *,
        authorized_capabilities: frozenset[str],
    ) -> ExtensionValidationResult:
        if not isinstance(authorized_capabilities, frozenset) or any(
            not isinstance(item, str) for item in authorized_capabilities
        ):
            raise TypeError("authorized_capabilities must be a frozenset of strings")
        if extensions is None:
            return ExtensionValidationResult(
                accepted=MappingProxyType({}),
                ignored_count=0,
                audit_required=False,
            )
        if not isinstance(extensions, ExtensionsGroup):
            raise TypeError("extensions must be ExtensionsGroup or None")

        accepted: dict[str, Mapping[str, JSONValue]] = {}
        ignored_count = 0
        for namespace, value in extensions.namespaces.items():
            contract = self._by_namespace.get(namespace)
            if contract is None:
                if self._unknown_policy is UnknownExtensionPolicy.IGNORE_AND_AUDIT:
                    ignored_count += 1
                    continue
                raise _extension_error("namespace_not_registered")
            if not contract.enabled:
                raise _extension_error("namespace_disabled")
            if not set(contract.required_capabilities).issubset(
                authorized_capabilities
            ):
                raise NsRuntimeUnauthorizedMessageTypeError(
                    details={
                        "component": "extension_registry",
                        "reason": "extension_capability_required",
                    },
                )
            if not isinstance(value, Mapping):
                raise _extension_error("namespace_object_required")
            keys = set(value)
            if set(contract.schema.required_fields) - keys:
                raise _extension_error("extension_field_missing")
            if keys - contract.schema.allowed_fields:
                raise _extension_error("extension_field_not_allowed")
            accepted[namespace] = value
        return ExtensionValidationResult(
            accepted=MappingProxyType(accepted),
            ignored_count=ignored_count,
            audit_required=ignored_count > 0,
        )


def _extension_error(reason: str) -> NsRuntimeEnvelopeSchemaError:
    return NsRuntimeEnvelopeSchemaError(
        "Runtime extension validation failed.",
        details={
            "group": "extensions",
            "field": "$namespace",
            "reason": reason,
        },
    )


EMPTY_EXTENSION_REGISTRY = ExtensionNamespaceRegistry()


__all__ = (
    "EMPTY_EXTENSION_REGISTRY",
    "ExtensionNamespaceContract",
    "ExtensionNamespaceRegistry",
    "ExtensionObjectSchema",
    "ExtensionValidationResult",
    "UnknownExtensionPolicy",
)
