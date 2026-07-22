# -*- coding: utf-8 -*-
"""Local trusted processor plugin metadata and registration boundary."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from ns_common.exceptions import NsRuntimeUnauthorizedMessageTypeError, NsValidationError
from ns_runtime.protocol import ExtensionObjectSchema

from .contracts import ProcessorStage, freeze_feature_flags
from .registry import ProcessorRegistration, ProcessorRegistry


_NAMESPACE = re.compile(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+")
_CAPABILITY = re.compile(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+")


@dataclass(frozen=True, slots=True, kw_only=True)
class PluginMetadata:
    namespace: str
    schema: ExtensionObjectSchema
    permissions: tuple[str, ...]
    timeout_seconds: float
    state_namespace: str
    feature_flag: str

    def __post_init__(self) -> None:
        if not isinstance(self.namespace, str) or _NAMESPACE.fullmatch(self.namespace) is None:
            _invalid("metadata.namespace")
        if not isinstance(self.schema, ExtensionObjectSchema):
            _invalid("metadata.schema")
        if (
            not isinstance(self.permissions, tuple)
            or any(
                not isinstance(item, str) or _CAPABILITY.fullmatch(item) is None
                for item in self.permissions
            )
            or len(set(self.permissions)) != len(self.permissions)
        ):
            _invalid("metadata.permissions")
        if (
            isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, (int, float))
            or not math.isfinite(float(self.timeout_seconds))
            or float(self.timeout_seconds) <= 0
        ):
            _invalid("metadata.timeout_seconds")
        if self.state_namespace != f"plugin.{self.namespace}":
            _invalid("metadata.state_namespace")
        if not isinstance(self.feature_flag, str) or _NAMESPACE.fullmatch(self.feature_flag) is None:
            _invalid("metadata.feature_flag")
        object.__setattr__(self, "timeout_seconds", float(self.timeout_seconds))


@dataclass(frozen=True, slots=True, kw_only=True)
class LocalTrustedPlugin:
    metadata: PluginMetadata
    registrations: tuple[ProcessorRegistration, ...] = field(repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.metadata, PluginMetadata):
            _invalid("plugin.metadata")
        if (
            not isinstance(self.registrations, tuple)
            or not self.registrations
            or any(not isinstance(item, ProcessorRegistration) for item in self.registrations)
        ):
            _invalid("plugin.registrations")
        for registration in self.registrations:
            if registration.stage is not ProcessorStage.MESSAGE_PROCESSOR:
                _invalid("plugin.stage")
            if registration.feature_flag != self.metadata.feature_flag:
                _invalid("plugin.feature_flag")


class LocalPluginRegistry:
    """Explicit allowlisted loader; no remote discovery or executable runtime."""

    def __init__(
        self,
        *,
        allowed_namespaces: frozenset[str],
        granted_permissions: frozenset[str],
        feature_flags: Mapping[str, bool],
    ) -> None:
        if (
            not isinstance(allowed_namespaces, frozenset)
            or any(not isinstance(item, str) or _NAMESPACE.fullmatch(item) is None for item in allowed_namespaces)
        ):
            _invalid("allowed_namespaces")
        if (
            not isinstance(granted_permissions, frozenset)
            or any(not isinstance(item, str) or _CAPABILITY.fullmatch(item) is None for item in granted_permissions)
        ):
            _invalid("granted_permissions")
        self._allowed = allowed_namespaces
        self._permissions = granted_permissions
        self._feature_flags = freeze_feature_flags(feature_flags)
        self._plugins: dict[str, LocalTrustedPlugin] = {}

    @property
    def plugins(self) -> Mapping[str, LocalTrustedPlugin]:
        return MappingProxyType(dict(self._plugins))

    def register(self, plugin: LocalTrustedPlugin, *, processor_registry: ProcessorRegistry) -> None:
        if not isinstance(plugin, LocalTrustedPlugin):
            _invalid("plugin")
        if not isinstance(processor_registry, ProcessorRegistry):
            _invalid("processor_registry")
        namespace = plugin.metadata.namespace
        if namespace in self._plugins:
            raise NsValidationError(
                "Duplicate plugin namespace is forbidden.",
                details={"component": "plugin_registry", "reason": "duplicate_namespace"},
            )
        if (
            namespace not in self._allowed
            or not set(plugin.metadata.permissions).issubset(self._permissions)
            or self._feature_flags.get(plugin.metadata.feature_flag) is not True
        ):
            raise NsRuntimeUnauthorizedMessageTypeError(
                details={"component": "plugin_registry", "reason": "plugin_not_authorized"},
            )
        processor_registry.register_many(plugin.registrations)
        self._plugins[namespace] = plugin


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Local plugin value is invalid.",
        details={"component": "plugin_registry", "field": field_name},
    )


__all__ = (
    "LocalPluginRegistry",
    "LocalTrustedPlugin",
    "PluginMetadata",
)
