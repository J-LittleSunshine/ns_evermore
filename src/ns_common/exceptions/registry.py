# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Iterable, Mapping

from .base import NsEvermoreError
from .cluster import CLUSTER_ERROR_DEFINITIONS
from .common import COMMON_ERROR_DEFINITIONS
from .delivery import DELIVERY_ERROR_DEFINITIONS
from .metadata import NsErrorDefinition
from .payload_ref import PAYLOAD_REF_ERROR_DEFINITIONS
from .protocol import PROTOCOL_ERROR_DEFINITIONS


ALL_ERROR_DEFINITIONS: tuple[NsErrorDefinition, ...] = (
    *COMMON_ERROR_DEFINITIONS,
    *PROTOCOL_ERROR_DEFINITIONS,
    *PAYLOAD_REF_ERROR_DEFINITIONS,
    *DELIVERY_ERROR_DEFINITIONS,
    *CLUSTER_ERROR_DEFINITIONS,
)


def _build_registry_indices(
    definitions: tuple[NsErrorDefinition, ...],
) -> tuple[
    Mapping[type[NsEvermoreError], NsErrorDefinition],
    Mapping[str, NsErrorDefinition],
    Mapping[int, NsErrorDefinition],
]:
    by_error_type: dict[type[NsEvermoreError], NsErrorDefinition] = {}
    by_code: dict[str, NsErrorDefinition] = {}
    by_numeric_code: dict[int, NsErrorDefinition] = {}

    for definition in definitions:
        if not isinstance(definition, NsErrorDefinition):
            raise TypeError("definitions must contain NsErrorDefinition values")
        if definition.code != definition.error_type.code:
            raise ValueError(
                "definition code must match the current error_type.code"
            )
        if definition.numeric_code != definition.error_type.numeric_code:
            raise ValueError(
                "definition numeric_code must match the current "
                "error_type.numeric_code"
            )
        if definition.error_type in by_error_type:
            raise ValueError(
                f"duplicate error type: {definition.error_type.__name__}"
            )
        if definition.code in by_code:
            raise ValueError(f"duplicate error code: {definition.code}")
        if definition.numeric_code in by_numeric_code:
            raise ValueError(
                f"duplicate numeric error code: {definition.numeric_code}"
            )
        by_error_type[definition.error_type] = definition
        by_code[definition.code] = definition
        by_numeric_code[definition.numeric_code] = definition

    return (
        MappingProxyType(by_error_type),
        MappingProxyType(by_code),
        MappingProxyType(by_numeric_code),
    )


@dataclass(frozen=True, slots=True, init=False)
class NsErrorRegistry:
    _definitions: tuple[NsErrorDefinition, ...] = field(repr=False)
    _by_error_type: Mapping[
        type[NsEvermoreError], NsErrorDefinition
    ] = field(repr=False)
    _by_code: Mapping[str, NsErrorDefinition] = field(repr=False)
    _by_numeric_code: Mapping[int, NsErrorDefinition] = field(repr=False)

    def __init__(self, definitions: Iterable[NsErrorDefinition]) -> None:
        normalized_definitions = tuple(definitions)
        by_error_type, by_code, by_numeric_code = _build_registry_indices(
            normalized_definitions
        )
        object.__setattr__(self, "_definitions", normalized_definitions)
        object.__setattr__(self, "_by_error_type", by_error_type)
        object.__setattr__(self, "_by_code", by_code)
        object.__setattr__(self, "_by_numeric_code", by_numeric_code)

    @property
    def definitions(self) -> tuple[NsErrorDefinition, ...]:
        return self._definitions

    def get_by_error_type(
        self, error_type: type[NsEvermoreError]
    ) -> NsErrorDefinition | None:
        return self._by_error_type.get(error_type)

    def get_by_code(self, code: str) -> NsErrorDefinition | None:
        return self._by_code.get(code)

    def get_by_numeric_code(
        self, numeric_code: int
    ) -> NsErrorDefinition | None:
        return self._by_numeric_code.get(numeric_code)

    def validate(self) -> None:
        _build_registry_indices(self._definitions)

    def to_dict(self) -> list[dict[str, object]]:
        return [definition.to_dict() for definition in self._definitions]


ERROR_REGISTRY = NsErrorRegistry(ALL_ERROR_DEFINITIONS)


def get_error_definition(
    error_type: type[NsEvermoreError],
) -> NsErrorDefinition | None:
    return ERROR_REGISTRY.get_by_error_type(error_type)


def get_error_definition_by_code(code: str) -> NsErrorDefinition | None:
    return ERROR_REGISTRY.get_by_code(code)


def get_error_definition_by_numeric_code(
    numeric_code: int,
) -> NsErrorDefinition | None:
    return ERROR_REGISTRY.get_by_numeric_code(numeric_code)


def list_error_definitions() -> tuple[NsErrorDefinition, ...]:
    return ERROR_REGISTRY.definitions


def validate_error_registry(registry: NsErrorRegistry = ERROR_REGISTRY) -> None:
    if not isinstance(registry, NsErrorRegistry):
        raise TypeError("registry must be NsErrorRegistry")
    registry.validate()
