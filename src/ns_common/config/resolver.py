# -*- coding: utf-8 -*-
from __future__ import annotations

from collections.abc import Mapping as MappingABC
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Mapping

from ..exceptions import NsConfigError
from .codec import _build_group_metadata, _deep_merge, _reject_unknown_fields
from .groups.runtime import RUNTIME_CONFIG_GROUP_NAMES
from .metadata import NsConfigGroupMetadata, NsConfigSource
from .primitives import _to_json_value
from .validation import (
    config_groups,
    normalize_effective_at,
    resolve_environment,
    runtime_config_groups,
    validate_group_metadata,
)


class NsConfigResolver:
    GROUP_NAMES: tuple[str, ...] = (
        "backend",
        "cache",
        "log",
        "runtime",
    )
    REQUIRED_OVERRIDE_METADATA_FIELDS: frozenset[str] = frozenset({
        "source",
        "config_version",
        "policy_version",
        "group_version",
        "effective_at",
        "rollback_from_version",
        "apply_mode",
    })

    def __init__(
        self,
        *,
        config_type: type[Any] | None = None,
        environment: str | None = None,
        effective_at: datetime | str | None = None,
    ) -> None:
        if config_type is None:
            # Preserve the public NsConfigResolver() constructor while keeping
            # resolver.py free of an import-time dependency on the root model.
            from .model import NsConfig

            config_type = NsConfig

        self._config_type = config_type
        self._environment = resolve_environment(environment)
        self._effective_at = normalize_effective_at(
            effective_at or datetime.now(timezone.utc),
            field_name="effective_at",
            allow_none=False,
        )

    def resolve(
        self,
        local_config: Mapping[str, Any],
        *,
        backend_override: Mapping[str, Any] | None = None,
        validated_snapshot: Any | None = None,
    ) -> Any:
        effective_config = self._resolve_local_config(local_config)

        if backend_override is not None:
            effective_config = self._apply_backend_override(
                effective_config,
                backend_override,
            )

        if validated_snapshot is not None:
            effective_config = self._accept_validated_snapshot(validated_snapshot)

        return effective_config

    def _resolve_local_config(self, raw_config: Mapping[str, Any]) -> Any:
        config = self._config_type.from_dict(
            raw_config,
            environment=self._environment,
        )
        group_updates: dict[str, Any] = {}

        for group_name, group_config in config_groups(config):
            metadata = group_config.metadata
            if metadata.source is not NsConfigSource.LOCAL_FILE:
                self._raise_source_mismatch(
                    layer="local config",
                    group_name=group_name,
                    expected=NsConfigSource.LOCAL_FILE,
                    actual=metadata.source,
                )

            timestamp = normalize_effective_at(
                metadata.effective_at or self._effective_at,
                field_name=f"{group_name}.metadata.effective_at",
                allow_none=False,
            )
            resolved_group = replace(
                group_config,
                metadata=replace(metadata, effective_at=timestamp),
            )
            if group_name == "runtime":
                runtime_updates: dict[str, Any] = {}
                for runtime_group_name, runtime_group in runtime_config_groups(group_config):
                    runtime_metadata = runtime_group.metadata
                    if runtime_metadata.source is not NsConfigSource.LOCAL_FILE:
                        self._raise_source_mismatch(
                            layer="local config",
                            group_name=f"runtime.{runtime_group_name}",
                            expected=NsConfigSource.LOCAL_FILE,
                            actual=runtime_metadata.source,
                        )
                    runtime_timestamp = normalize_effective_at(
                        runtime_metadata.effective_at or self._effective_at,
                        field_name=f"runtime.{runtime_group_name}.metadata.effective_at",
                        allow_none=False,
                    )
                    runtime_updates[runtime_group_name] = replace(
                        runtime_group,
                        metadata=replace(runtime_metadata, effective_at=runtime_timestamp),
                    )
                resolved_group = replace(resolved_group, **runtime_updates)

            group_updates[group_name] = resolved_group

        resolved = replace(config, **group_updates)
        self._validate_effective_config(resolved, layer="local config")
        return resolved

    def _apply_backend_override(self, base_config: Any, raw_override: Mapping[str, Any]) -> Any:
        if not isinstance(raw_override, MappingABC):
            raise NsConfigError(
                "backend override must be a mapping.",
                details={
                    "field": "backend_override",
                    "actual_type": type(raw_override).__name__,
                },
            )

        _reject_unknown_fields(
            raw_override,
            allowed_fields=set(self.GROUP_NAMES),
            path="backend_override",
        )
        if not raw_override:
            return base_config

        base_dict = base_config.to_dict()
        effective_dict = base_config.to_dict()
        override_metadata: dict[str, NsConfigGroupMetadata] = {}
        runtime_override_metadata: dict[str, NsConfigGroupMetadata] = {}
        payload_changed = False

        for group_name, raw_group in raw_override.items():
            if not isinstance(raw_group, MappingABC):
                raise NsConfigError(
                    f"backend_override.{group_name} must be a JSON object.",
                    details={
                        "field": f"backend_override.{group_name}",
                        "actual_type": type(raw_group).__name__,
                    },
                )

            raw_metadata = raw_group.get("metadata")
            if not isinstance(raw_metadata, MappingABC):
                raise NsConfigError(
                    f"backend_override.{group_name}.metadata is required.",
                    details={
                        "field": f"backend_override.{group_name}.metadata",
                        "actual_type": type(raw_metadata).__name__,
                    },
                )

            missing_metadata_fields = sorted(
                self.REQUIRED_OVERRIDE_METADATA_FIELDS.difference(raw_metadata)
            )
            if missing_metadata_fields:
                raise NsConfigError(
                    f"backend_override.{group_name}.metadata is incomplete.",
                    details={
                        "field": f"backend_override.{group_name}.metadata",
                        "missing_fields": missing_metadata_fields,
                    },
                )

            metadata = _build_group_metadata(
                raw_metadata,
                path=f"backend_override.{group_name}.metadata",
            )
            validate_group_metadata(group_name, metadata)
            if metadata.source is not NsConfigSource.BACKEND_OVERRIDE:
                self._raise_source_mismatch(
                    layer="backend override",
                    group_name=group_name,
                    expected=NsConfigSource.BACKEND_OVERRIDE,
                    actual=metadata.source,
                )

            timestamp = normalize_effective_at(
                metadata.effective_at,
                field_name=f"backend_override.{group_name}.metadata.effective_at",
                allow_none=False,
            )
            metadata = replace(metadata, effective_at=timestamp)
            base_metadata = getattr(base_config, group_name).metadata

            if (
                metadata.rollback_from_version is not None
                and metadata.rollback_from_version != base_metadata.group_version
            ):
                raise NsConfigError(
                    f"backend_override.{group_name} rollback source does not match the effective group version.",
                    details={
                        "field": f"backend_override.{group_name}.metadata.rollback_from_version",
                        "value": metadata.rollback_from_version,
                        "effective_group_version": base_metadata.group_version,
                    },
                )

            if group_name == "runtime":
                for runtime_group_name in RUNTIME_CONFIG_GROUP_NAMES:
                    if runtime_group_name not in raw_group:
                        continue

                    raw_runtime_group = raw_group[runtime_group_name]
                    if not isinstance(raw_runtime_group, MappingABC):
                        raise NsConfigError(
                            f"backend_override.runtime.{runtime_group_name} must be a JSON object.",
                            details={
                                "field": f"backend_override.runtime.{runtime_group_name}",
                                "actual_type": type(raw_runtime_group).__name__,
                            },
                        )

                    base_runtime_group = getattr(base_config.runtime, runtime_group_name)
                    base_runtime_dict = _to_json_value(base_runtime_group)
                    base_runtime_payload = {
                        key: value
                        for key, value in base_runtime_dict.items()
                        if key != "metadata"
                    }
                    runtime_override_payload = {
                        key: value
                        for key, value in raw_runtime_group.items()
                        if key != "metadata"
                    }
                    merged_runtime_payload = self._deep_merge(
                        base_runtime_payload,
                        runtime_override_payload,
                    )
                    runtime_group_changed = merged_runtime_payload != base_runtime_payload
                    raw_runtime_metadata = raw_runtime_group.get("metadata")
                    if runtime_group_changed and not isinstance(raw_runtime_metadata, MappingABC):
                        raise NsConfigError(
                            f"backend_override.runtime.{runtime_group_name}.metadata is required when values change.",
                            details={
                                "field": f"backend_override.runtime.{runtime_group_name}.metadata",
                            },
                        )
                    if raw_runtime_metadata is None:
                        continue
                    if not isinstance(raw_runtime_metadata, MappingABC):
                        raise NsConfigError(
                            f"backend_override.runtime.{runtime_group_name}.metadata must be a JSON object.",
                            details={
                                "field": f"backend_override.runtime.{runtime_group_name}.metadata",
                                "actual_type": type(raw_runtime_metadata).__name__,
                            },
                        )

                    missing_runtime_metadata = sorted(
                        self.REQUIRED_OVERRIDE_METADATA_FIELDS.difference(raw_runtime_metadata)
                    )
                    if missing_runtime_metadata:
                        raise NsConfigError(
                            f"backend_override.runtime.{runtime_group_name}.metadata is incomplete.",
                            details={
                                "field": f"backend_override.runtime.{runtime_group_name}.metadata",
                                "missing_fields": missing_runtime_metadata,
                            },
                        )

                    runtime_metadata = _build_group_metadata(
                        raw_runtime_metadata,
                        path=f"backend_override.runtime.{runtime_group_name}.metadata",
                    )
                    validate_group_metadata(
                        f"runtime.{runtime_group_name}",
                        runtime_metadata,
                    )
                    runtime_timestamp = normalize_effective_at(
                        runtime_metadata.effective_at,
                        field_name=f"backend_override.runtime.{runtime_group_name}.metadata.effective_at",
                        allow_none=False,
                    )
                    runtime_metadata = replace(
                        runtime_metadata,
                        effective_at=runtime_timestamp,
                    )
                    if runtime_metadata.source is not NsConfigSource.BACKEND_OVERRIDE:
                        self._raise_source_mismatch(
                            layer="backend override",
                            group_name=f"runtime.{runtime_group_name}",
                            expected=NsConfigSource.BACKEND_OVERRIDE,
                            actual=runtime_metadata.source,
                        )
                    if (
                        runtime_metadata.config_version != metadata.config_version
                        or runtime_metadata.policy_version != metadata.policy_version
                    ):
                        raise NsConfigError(
                            f"backend_override.runtime.{runtime_group_name} versions must match runtime metadata.",
                            details={
                                "field": f"backend_override.runtime.{runtime_group_name}.metadata",
                                "config_version": runtime_metadata.config_version,
                                "policy_version": runtime_metadata.policy_version,
                                "expected_config_version": metadata.config_version,
                                "expected_policy_version": metadata.policy_version,
                            },
                        )
                    base_runtime_metadata = base_runtime_group.metadata
                    if (
                        runtime_metadata.rollback_from_version is not None
                        and runtime_metadata.rollback_from_version != base_runtime_metadata.group_version
                    ):
                        raise NsConfigError(
                            f"backend_override.runtime.{runtime_group_name} rollback source does not match the effective group version.",
                            details={
                                "field": f"backend_override.runtime.{runtime_group_name}.metadata.rollback_from_version",
                                "value": runtime_metadata.rollback_from_version,
                                "effective_group_version": base_runtime_metadata.group_version,
                            },
                        )
                    if (
                        runtime_group_changed
                        and runtime_metadata.group_version == base_runtime_metadata.group_version
                    ):
                        raise NsConfigError(
                            f"backend_override.runtime.{runtime_group_name} changed values without a new group_version.",
                            details={
                                "field": f"backend_override.runtime.{runtime_group_name}.metadata.group_version",
                                "value": runtime_metadata.group_version,
                            },
                        )
                    runtime_override_metadata[runtime_group_name] = runtime_metadata

            base_payload = {
                key: value
                for key, value in base_dict[group_name].items()
                if key != "metadata"
            }
            override_payload = {
                key: value
                for key, value in raw_group.items()
                if key != "metadata"
            }
            merged_payload = self._deep_merge(base_payload, override_payload)
            if group_name == "runtime":
                for runtime_group_name, runtime_metadata in runtime_override_metadata.items():
                    merged_payload[runtime_group_name]["metadata"] = _to_json_value(runtime_metadata)
            group_changed = merged_payload != base_payload
            if group_changed and metadata.group_version == base_metadata.group_version:
                raise NsConfigError(
                    f"backend_override.{group_name} changed values without a new group_version.",
                    details={
                        "field": f"backend_override.{group_name}.metadata.group_version",
                        "value": metadata.group_version,
                    },
                )

            payload_changed = payload_changed or group_changed
            merged_payload["metadata"] = _to_json_value(metadata)
            effective_dict[group_name] = merged_payload
            override_metadata[group_name] = metadata

        config_versions = {item.config_version for item in override_metadata.values()}
        policy_versions = {item.policy_version for item in override_metadata.values()}
        if len(config_versions) != 1 or len(policy_versions) != 1:
            raise NsConfigError(
                "backend override versions must be consistent across groups.",
                details={
                    "field": "backend_override.metadata",
                    "config_versions": sorted(config_versions),
                    "policy_versions": sorted(policy_versions),
                },
            )

        target_config_version = next(iter(config_versions))
        target_policy_version = next(iter(policy_versions))
        if payload_changed and target_config_version == base_config.config_version:
            raise NsConfigError(
                "backend override changed values without a new config_version.",
                details={
                    "field": "backend_override.metadata.config_version",
                    "value": target_config_version,
                },
            )

        for group_name in self.GROUP_NAMES:
            if group_name in override_metadata:
                continue

            metadata_dict = effective_dict[group_name]["metadata"]
            metadata_dict["config_version"] = target_config_version
            metadata_dict["policy_version"] = target_policy_version

        for runtime_group_name in RUNTIME_CONFIG_GROUP_NAMES:
            runtime_metadata_dict = effective_dict["runtime"][runtime_group_name]["metadata"]
            runtime_metadata_dict["config_version"] = target_config_version
            runtime_metadata_dict["policy_version"] = target_policy_version

        resolved = self._config_type.from_dict(
            effective_dict,
            environment=self._environment,
        )
        self._validate_effective_config(resolved, layer="backend override")
        return resolved

    def _accept_validated_snapshot(self, snapshot: Any) -> Any:
        if not isinstance(snapshot, self._config_type):
            raise NsConfigError(
                "validated_snapshot must be an immutable NsConfig instance.",
                details={
                    "field": "validated_snapshot",
                    "actual_type": type(snapshot).__name__,
                },
            )

        snapshot.validate(environment=self._environment)
        for group_name, group_config in config_groups(snapshot):
            metadata = group_config.metadata
            if metadata.source is not NsConfigSource.VALIDATED_SNAPSHOT:
                self._raise_source_mismatch(
                    layer="validated snapshot",
                    group_name=group_name,
                    expected=NsConfigSource.VALIDATED_SNAPSHOT,
                    actual=metadata.source,
                )

            normalize_effective_at(
                metadata.effective_at,
                field_name=f"validated_snapshot.{group_name}.metadata.effective_at",
                allow_none=False,
            )

        for runtime_group_name, runtime_group in runtime_config_groups(snapshot.runtime):
            metadata = runtime_group.metadata
            if metadata.source is not NsConfigSource.VALIDATED_SNAPSHOT:
                self._raise_source_mismatch(
                    layer="validated snapshot",
                    group_name=f"runtime.{runtime_group_name}",
                    expected=NsConfigSource.VALIDATED_SNAPSHOT,
                    actual=metadata.source,
                )
            normalize_effective_at(
                metadata.effective_at,
                field_name=f"validated_snapshot.runtime.{runtime_group_name}.metadata.effective_at",
                allow_none=False,
            )

        self._validate_effective_config(snapshot, layer="validated snapshot")
        return snapshot

    def _validate_effective_config(self, config: Any, *, layer: str) -> None:
        config.validate(environment=self._environment)
        try:
            config.config_version
            config.policy_version
        except NsConfigError as error:
            error.details["layer"] = layer
            raise

    @staticmethod
    def _deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
        return _deep_merge(base, override)

    @staticmethod
    def _raise_source_mismatch(
        *,
        layer: str,
        group_name: str,
        expected: NsConfigSource,
        actual: NsConfigSource,
    ) -> None:
        raise NsConfigError(
            f"{layer} source is invalid for {group_name}.",
            details={
                "field": f"{group_name}.metadata.source",
                "expected": expected.value,
                "actual": actual.value,
            },
        )


def create_validated_snapshot(
    config: Any,
    *,
    effective_at: datetime | str | None = None,
    environment: str | None = None,
) -> Any:
    timestamp = normalize_effective_at(
        effective_at or datetime.now(timezone.utc),
        field_name="effective_at",
        allow_none=False,
    )
    runtime_group_updates = {
        group_name: replace(
            group_config,
            metadata=replace(
                group_config.metadata,
                source=NsConfigSource.VALIDATED_SNAPSHOT,
                effective_at=timestamp,
            ),
        )
        for group_name, group_config in runtime_config_groups(config.runtime)
    }
    runtime_snapshot = replace(
        config.runtime,
        **runtime_group_updates,
        metadata=replace(
            config.runtime.metadata,
            source=NsConfigSource.VALIDATED_SNAPSHOT,
            effective_at=timestamp,
        ),
    )
    snapshot = replace(
        config,
        backend=replace(
            config.backend,
            metadata=replace(
                config.backend.metadata,
                source=NsConfigSource.VALIDATED_SNAPSHOT,
                effective_at=timestamp,
            ),
        ),
        cache=replace(
            config.cache,
            metadata=replace(
                config.cache.metadata,
                source=NsConfigSource.VALIDATED_SNAPSHOT,
                effective_at=timestamp,
            ),
        ),
        log=replace(
            config.log,
            metadata=replace(
                config.log.metadata,
                source=NsConfigSource.VALIDATED_SNAPSHOT,
                effective_at=timestamp,
            ),
        ),
        runtime=runtime_snapshot,
    )
    snapshot.validate(environment=environment)
    config_version = snapshot.config_version
    policy_version = snapshot.policy_version
    del config_version, policy_version
    return snapshot
