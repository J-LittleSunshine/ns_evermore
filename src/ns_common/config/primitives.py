# -*- coding: utf-8 -*-
from __future__ import annotations

import types
from collections.abc import Mapping as MappingABC
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import (
    Any,
    get_args,
    get_origin,
    get_type_hints,
    Iterator,
    Literal,
    Mapping,
    Union,
)

from ..exceptions import NsConfigError


class FrozenDict(MappingABC[str, Any]):
    """A read-only mapping used by deeply immutable config snapshots."""

    __slots__ = ("_values",)

    def __init__(self, values: Mapping[str, Any] | None = None) -> None:
        object.__setattr__(self, "_values", types.MappingProxyType(dict(values or {})))

    def __getitem__(self, key: str) -> Any:
        return self._values[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def __repr__(self) -> str:
        return f"FrozenDict({dict(self._values)!r})"

    def __setattr__(self, name: str, value: Any) -> None:
        del name, value
        raise TypeError("configuration snapshots are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise TypeError("configuration snapshots are immutable")

    def __copy__(self) -> "FrozenDict":
        return self

    def __deepcopy__(self, memo: dict[int, Any]) -> "FrozenDict":
        del memo
        return self


def _freeze_config_value(value: Any) -> Any:
    if isinstance(value, FrozenDict):
        return value

    if isinstance(value, MappingABC):
        return FrozenDict({
            key: _freeze_config_value(item)
            for key, item in value.items()
        })

    if isinstance(value, (list, tuple)):
        return tuple(_freeze_config_value(item) for item in value)

    return value


def _to_json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value

    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _to_json_value(getattr(value, item.name))
            for item in fields(value)
        }

    if isinstance(value, MappingABC):
        return {
            str(key): _to_json_value(item)
            for key, item in value.items()
        }

    if isinstance(value, tuple):
        return [_to_json_value(item) for item in value]

    return value


def _value_matches_type(value: Any, expected_type: Any) -> bool:
    if expected_type is Any:
        return True

    origin = get_origin(expected_type)
    arguments = get_args(expected_type)

    if origin is Literal:
        return any(
            value == item and type(value) is type(item)
            for item in arguments
        )

    if origin in {types.UnionType, Union}:
        return any(_value_matches_type(value, item) for item in arguments)

    if origin is tuple:
        if not isinstance(value, tuple):
            return False

        if len(arguments) == 2 and arguments[1] is Ellipsis:
            return all(_value_matches_type(item, arguments[0]) for item in value)

        return len(value) == len(arguments) and all(
            _value_matches_type(item, item_type)
            for item, item_type in zip(value, arguments)
        )

    if origin in {dict, MappingABC}:
        if not isinstance(value, MappingABC):
            return False

        if not arguments:
            return True

        key_type, item_type = arguments
        return all(
            _value_matches_type(key, key_type)
            and _value_matches_type(item, item_type)
            for key, item in value.items()
        )

    if origin is list:
        return isinstance(value, list) and (
            not arguments
            or all(_value_matches_type(item, arguments[0]) for item in value)
        )

    if expected_type is bool:
        return type(value) is bool

    if expected_type is int:
        return type(value) is int

    if expected_type is float:
        return not isinstance(value, bool) and isinstance(value, (int, float))

    if expected_type is None or expected_type is type(None):
        return value is None

    try:
        return isinstance(value, expected_type)
    except TypeError:
        return False


def _validate_dataclass_types(instance: Any, *, path: str = "") -> None:
    type_hints = get_type_hints(type(instance))

    for item in fields(instance):
        value = getattr(instance, item.name)
        field_path = f"{path}.{item.name}" if path else item.name
        expected_type = type_hints.get(item.name, Any)

        if not _value_matches_type(value, expected_type):
            raise NsConfigError(
                f"{field_path} has an invalid type.",
                details={
                    "field": field_path,
                    "actual_type": type(value).__name__,
                    "expected_type": str(expected_type),
                },
            )

        if is_dataclass(value) and not isinstance(value, type):
            _validate_dataclass_types(value, path=field_path)
