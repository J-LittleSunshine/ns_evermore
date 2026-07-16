# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping as MappingABC
from dataclasses import MISSING, fields, is_dataclass, replace
from pathlib import Path
from typing import Any, Mapping, get_type_hints

from ..exceptions import NsConfigError
from ..paths import ensure_runtime_dirs
from .defaults import get_default_config_path
from .groups.backend import NsBackendConfig
from .groups.cache import NsCacheConfig
from .groups.logging import NsLogConfig
from .groups.runtime import NsRuntimeConfig
from .metadata import NsConfigGroupMetadata, NsConfigSource
from .primitives import _to_json_value
from .validation import resolve_environment, runtime_config_groups


def load_config(
    config_type: type[Any],
    config_path: str | Path | None = None,
    *,
    environment: str | None = None,
    backend_override: Mapping[str, Any] | None = None,
    validated_snapshot: Any | None = None,
    effective_at: Any | None = None,
) -> Any:
    resolved_environment = resolve_environment(environment)
    if config_path is None:
        ensure_runtime_dirs()
        path = get_default_config_path(resolved_environment)
    else:
        path = Path(config_path).resolve()

    with config_type._lock:
        raw_config = _load_json_config(path)
        return config_type.resolve(
            raw_config,
            environment=resolved_environment,
            backend_override=backend_override,
            validated_snapshot=validated_snapshot,
            effective_at=effective_at,
        )


def from_dict(
    config_type: type[Any],
    raw_config: Mapping[str, Any],
    *,
    environment: str | None = None,
) -> Any:
    resolved_environment = resolve_environment(environment)
    if not isinstance(raw_config, MappingABC):
        raise NsConfigError(
            "Config root must be a mapping.",
            details={
                "field": "config",
                "actual_type": type(raw_config).__name__,
            },
        )

    allowed_top_level_fields = {
        "backend",
        "backend_config",
        "cache",
        "cache_config",
        "log",
        "log_config",
        "runtime",
        "runtime_config",
    }
    _reject_unknown_fields(
        raw_config,
        allowed_fields=allowed_top_level_fields,
        path="config",
    )

    backend_raw = _get_section(raw_config, preferred_key="backend", compatible_key="backend_config")
    cache_raw = _get_section(raw_config, preferred_key="cache", compatible_key="cache_config")
    log_raw = _get_section(raw_config, preferred_key="log", compatible_key="log_config")
    runtime_raw = _get_section(raw_config, preferred_key="runtime", compatible_key="runtime_config")

    if "cache" in backend_raw:
        raise NsConfigError(
            "backend.cache is deprecated. Move cache config to top-level cache.",
            details={
                "field": "backend.cache",
                "expected_field": "cache",
            },
        )

    config = config_type(
        backend=_build_config_group(NsBackendConfig, backend_raw, path="backend"),
        cache=_build_config_group(NsCacheConfig, cache_raw, path="cache"),
        log=_build_config_group(NsLogConfig, log_raw, path="log"),
        runtime=_build_config_group(NsRuntimeConfig, runtime_raw, path="runtime"),
    )
    config.validate(environment=resolved_environment)
    return config


def save_config(
    config: Any,
    config_path: str | Path | None = None,
    *,
    environment: str | None = None,
) -> None:
    resolved_environment = resolve_environment(environment)
    if config_path is None:
        ensure_runtime_dirs()
        path = get_default_config_path(resolved_environment)
    else:
        path = Path(config_path).resolve()

    with config.__class__._lock:
        config.validate(environment=resolved_environment)
        _atomic_write_json(path, to_dict(config))


def to_dict(config: Any) -> dict[str, Any]:
    return _to_json_value(config)


def _reject_unknown_fields(
    raw_config: Mapping[str, Any],
    *,
    allowed_fields: set[str],
    path: str,
) -> None:
    unknown_fields = sorted(
        str(key)
        for key in raw_config
        if key not in allowed_fields
    )
    if unknown_fields:
        raise NsConfigError(
            f"{path} contains unknown fields.",
            details={
                "field": path,
                "unknown_fields": unknown_fields,
                "allowed_fields": sorted(allowed_fields),
            },
        )


def _build_config_group(
    group_type: type[Any],
    raw_group: Mapping[str, Any],
    *,
    path: str,
) -> Any:
    group_values = dict(raw_group)
    group_fields = {item.name: item for item in fields(group_type)}
    allowed_fields = set(group_fields)
    _reject_unknown_fields(
        group_values,
        allowed_fields=allowed_fields,
        path=path,
    )

    type_hints = get_type_hints(group_type)
    for field_name, raw_value in tuple(group_values.items()):
        if field_name == "metadata":
            continue

        expected_type = type_hints.get(field_name)
        if not isinstance(expected_type, type) or not is_dataclass(expected_type):
            continue

        if isinstance(raw_value, expected_type):
            continue

        if not isinstance(raw_value, MappingABC):
            raise NsConfigError(
                f"{path}.{field_name} must be a JSON object.",
                details={
                    "field": f"{path}.{field_name}",
                    "actual_type": type(raw_value).__name__,
                },
            )

        nested_values: Mapping[str, Any] = raw_value
        group_field = group_fields[field_name]
        if group_field.default_factory is not MISSING:
            default_value = group_field.default_factory()
            if is_dataclass(default_value) and not isinstance(default_value, type):
                nested_values = _deep_merge(
                    _to_json_value(default_value),
                    raw_value,
                )

        group_values[field_name] = _build_config_group(
            expected_type,
            nested_values,
            path=f"{path}.{field_name}",
        )

    if "metadata" in group_values:
        group_values["metadata"] = _build_group_metadata(
            group_values["metadata"],
            path=f"{path}.metadata",
        )
    try:
        group = group_type(**group_values)
    except TypeError as error:
        raise NsConfigError(
            f"{path} is invalid.",
            details={
                "field": path,
                "reason": str(error),
            },
        ) from error

    if isinstance(group, NsRuntimeConfig):
        runtime_updates: dict[str, Any] = {}
        for runtime_group_name, runtime_group in runtime_config_groups(group):
            raw_runtime_group = raw_group.get(runtime_group_name)
            has_explicit_metadata = (
                isinstance(raw_runtime_group, MappingABC)
                and "metadata" in raw_runtime_group
            )
            if has_explicit_metadata:
                continue

            runtime_updates[runtime_group_name] = replace(
                runtime_group,
                metadata=replace(
                    runtime_group.metadata,
                    source=group.metadata.source,
                    config_version=group.metadata.config_version,
                    policy_version=group.metadata.policy_version,
                    effective_at=group.metadata.effective_at,
                ),
            )

        if runtime_updates:
            group = replace(group, **runtime_updates)

    return group


def _build_group_metadata(raw_metadata: Any, *, path: str) -> NsConfigGroupMetadata:
    if isinstance(raw_metadata, NsConfigGroupMetadata):
        return raw_metadata

    if not isinstance(raw_metadata, MappingABC):
        raise NsConfigError(
            f"{path} must be a JSON object.",
            details={
                "field": path,
                "actual_type": type(raw_metadata).__name__,
            },
        )

    metadata_values = dict(raw_metadata)
    metadata_fields = {item.name for item in fields(NsConfigGroupMetadata)}
    _reject_unknown_fields(
        metadata_values,
        allowed_fields=metadata_fields,
        path=path,
    )
    if "source" in metadata_values and not isinstance(metadata_values["source"], NsConfigSource):
        try:
            metadata_values["source"] = NsConfigSource(metadata_values["source"])
        except (TypeError, ValueError) as error:
            raise NsConfigError(
                f"{path}.source is invalid.",
                details={
                    "field": f"{path}.source",
                    "value": metadata_values["source"],
                    "allowed_values": [item.value for item in NsConfigSource],
                },
            ) from error

    try:
        return NsConfigGroupMetadata(**metadata_values)
    except TypeError as error:
        raise NsConfigError(
            f"{path} is invalid.",
            details={
                "field": path,
                "reason": str(error),
            },
        ) from error


def _get_section(
    raw_config: Mapping[str, Any],
    *,
    preferred_key: str,
    compatible_key: str,
) -> Mapping[str, Any]:
    has_preferred = preferred_key in raw_config
    has_compatible = compatible_key in raw_config

    if has_preferred and has_compatible:
        raise NsConfigError(
            f"Use only {preferred_key}; do not also provide {compatible_key}.",
            details={
                "field": preferred_key,
                "conflicting_field": compatible_key,
            },
        )

    if not has_preferred and not has_compatible:
        return {}

    selected_key = preferred_key if has_preferred else compatible_key
    section = raw_config[selected_key]
    if not isinstance(section, MappingABC):
        raise NsConfigError(
            f"{selected_key} must be a JSON object.",
            details={
                "field": selected_key,
                "actual_type": type(section).__name__,
            },
        )

    return section


def _load_json_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        return {}

    try:
        with config_path.open("r", encoding="utf-8") as file:
            raw_config = json.load(file)
    except json.JSONDecodeError as error:
        raise NsConfigError(
            f"Invalid JSON config file: {config_path}",
            details={
                "config_path": str(config_path),
                "line": error.lineno,
                "column": error.colno,
            },
        ) from error

    if not isinstance(raw_config, dict):
        raise NsConfigError(
            f"Config root must be a JSON object: {config_path}",
            details={
                "config_path": str(config_path),
                "actual_type": type(raw_config).__name__,
            },
        )

    return raw_config


def _atomic_write_json(config_path: Path, data: dict[str, Any]) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        dir=config_path.parent,
        prefix=f".{config_path.name}.",
        suffix=".tmp",
        text=True,
    )
    temp_path = Path(temp_name)

    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())

        os.replace(temp_path, config_path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise


def _deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    merged = {
        key: _to_json_value(value)
        for key, value in base.items()
    }
    for key, value in override.items():
        current = merged.get(key)
        if isinstance(current, MappingABC) and isinstance(value, MappingABC):
            merged[key] = _deep_merge(current, value)
        else:
            merged[key] = _to_json_value(value)

    return merged
