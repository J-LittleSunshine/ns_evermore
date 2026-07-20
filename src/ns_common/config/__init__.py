# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import json
import os
import re
import tempfile
import types
from collections.abc import Mapping as MappingABC
from dataclasses import MISSING, dataclass, field, fields, is_dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from threading import RLock
from typing import (
    Any,
    get_args,
    get_origin,
    get_type_hints,
    Iterator,
    Literal,
    Mapping,
    TYPE_CHECKING,
    Union,
)
from urllib.parse import urlparse

from ..exceptions import NsConfigError, NsDependencyError
from ..paths import ETC_DIR, ensure_runtime_dirs
from .defaults import NS_CONFIG_FILE_PATH, NS_ENV, get_default_config_path, get_ns_env
from .groups.backend import NsBackendConfig
from .groups.cache import NsCacheConfig
from .groups.logging import NsLogConfig
from .groups.runtime import (
    RUNTIME_CLUSTER_ROLES,
    RUNTIME_CONFIG_GROUP_NAMES,
    NsRuntimeClusterConfig,
    NsRuntimeConfig,
    NsRuntimeDebugConfig,
    NsRuntimeDeliveryConfig,
    NsRuntimeEventLoopConfig,
    NsRuntimeIamConfig,
    NsRuntimeLoggingConfig,
    NsRuntimeObservabilityConfig,
    NsRuntimePoolConfig,
    NsRuntimeProtocolConfig,
    NsRuntimeRecoveryConfig,
    NsRuntimeRoutingConfig,
    NsRuntimeSecurityConfig,
    NsRuntimeStateStoreConfig,
    NsRuntimeTenantQuotaConfig,
    NsRuntimeTransportAdapterConfig,
    NsRuntimeTransportConfig,
    NsRuntimeWireCodecConfig,
    NsRuntimeWorkerConfig,
)
from .metadata import (
    NS_CONFIG_SOURCE_PRIORITY,
    RUNTIME_CONFIG_APPLY_MODES,
    NsConfigGroupMetadata,
    NsConfigSource,
)
from .model import NsConfig
from .primitives import FrozenDict
from .resolver import NsConfigResolver


__all__ = [
    "Any",
    "ETC_DIR",
    "Enum",
    "FrozenDict",
    "Iterator",
    "Literal",
    "MISSING",
    "Mapping",
    "MappingABC",
    "NS_CONFIG_FILE_PATH",
    "NS_CONFIG_SOURCE_PRIORITY",
    "NS_ENV",
    "NsBackendConfig",
    "NsCacheConfig",
    "NsConfig",
    "NsConfigError",
    "NsConfigGroupMetadata",
    "NsConfigResolver",
    "NsConfigSource",
    "NsDependencyError",
    "NsLogConfig",
    "NsRuntimeClusterConfig",
    "NsRuntimeConfig",
    "NsRuntimeDebugConfig",
    "NsRuntimeDeliveryConfig",
    "NsRuntimeEventLoopConfig",
    "NsRuntimeIamConfig",
    "NsRuntimeLoggingConfig",
    "NsRuntimeObservabilityConfig",
    "NsRuntimePoolConfig",
    "NsRuntimeProtocolConfig",
    "NsRuntimeRecoveryConfig",
    "NsRuntimeRoutingConfig",
    "NsRuntimeSecurityConfig",
    "NsRuntimeStateStoreConfig",
    "NsRuntimeTenantQuotaConfig",
    "NsRuntimeTransportAdapterConfig",
    "NsRuntimeTransportConfig",
    "NsRuntimeWireCodecConfig",
    "NsRuntimeWorkerConfig",
    "Path",
    "RLock",
    "RUNTIME_CLUSTER_ROLES",
    "RUNTIME_CONFIG_APPLY_MODES",
    "RUNTIME_CONFIG_GROUP_NAMES",
    "TYPE_CHECKING",
    "Union",
    "annotations",
    "dataclass",
    "datetime",
    "ensure_runtime_dirs",
    "field",
    "fields",
    "get_args",
    "get_default_config_path",
    "get_ns_env",
    "get_origin",
    "get_type_hints",
    "importlib",
    "is_dataclass",
    "json",
    "ns_config",
    "os",
    "re",
    "replace",
    "tempfile",
    "timezone",
    "types",
    "urlparse",
]


def __getattr__(name: str) -> Any:
    """Preserve the legacy global config without eager bootstrap effects."""

    if name != "ns_config":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from . import model

    global_config = model.ns_config
    globals()["ns_config"] = global_config
    return global_config
