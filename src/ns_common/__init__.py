# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_common.cache import (
    aclose_cache_clients,
    close_cache_clients,
    get_async_cache_client,
    get_cache_client,
    validate_cache_backend,
)
from ns_common.config import (
    NS_CONFIG_FILE_PATH,
    NS_ENV,
    ns_config
)
from ns_common.exceptions import (
    NsConfigError,
    NsDependencyError,
    NsEvermoreError,
    NsRuntimeAdminError,
    NsRuntimeAuthError,
    NsRuntimeCodecError,
    NsRuntimeError,
    NsRuntimeMessageError,
    NsRuntimeMessageStoreError,
    NsRuntimeNodeError,
    NsRuntimePluginError,
    NsRuntimeProtocolError,
    NsRuntimeRoutingError,
    NsRuntimeStateStoreError,
    NsStateError,
    NsValidationError,
)
from ns_common.logger import (
    close_ns_loggers,
    get_ns_logger
)
from ns_common.paths import (
    DATA_DIR,
    ETC_DIR,
    LOG_DIR,
    ROOT_DIR,
    SQL_DIR,
    TMP_DIR
)
from ns_common.runtime_config import (
    NsRuntimeAdminAccessCheckConfig,
    NsRuntimeAdminConfig,
    NsRuntimeAdminHttpConfig,
    NsRuntimeAuditStoreConfig,
    NsRuntimeClusterConfig,
    NsRuntimeConfig,
    NsRuntimeIamConfig,
    NsRuntimeIamConnectionAccessCheckConfig,
    NsRuntimePluginsConfig,
    NsRuntimeRoutingConfig,
    NsRuntimeServerConfig,
    NsRuntimeStoreConfig,
    NsRuntimeWebSocketConfig,
)

if TYPE_CHECKING:
    pass

__all__ = [
    "__version__",
    "DATA_DIR",
    "ETC_DIR",
    "LOG_DIR",
    "NS_CONFIG_FILE_PATH",
    "NS_ENV",
    "ROOT_DIR",
    "SQL_DIR",
    "TMP_DIR",
    "ns_config",
    "close_ns_loggers",
    "get_ns_logger",
    "NsConfigError",
    "NsDependencyError",
    "NsEvermoreError",
    "NsRuntimeError",
    "NsRuntimeProtocolError",
    "NsRuntimeCodecError",
    "NsRuntimeAuthError",
    "NsRuntimeRoutingError",
    "NsRuntimeNodeError",
    "NsRuntimeMessageError",
    "NsRuntimeStateStoreError",
    "NsRuntimeMessageStoreError",
    "NsRuntimePluginError",
    "NsRuntimeAdminError",
    "NsStateError",
    "NsValidationError",
    "NsRuntimeAdminAccessCheckConfig",
    "NsRuntimeAdminConfig",
    "NsRuntimeAdminHttpConfig",
    "NsRuntimeAuditStoreConfig",
    "NsRuntimeClusterConfig",
    "NsRuntimeConfig",
    "NsRuntimeIamConfig",
    "NsRuntimeIamConnectionAccessCheckConfig",
    "NsRuntimePluginsConfig",
    "NsRuntimeRoutingConfig",
    "NsRuntimeServerConfig",
    "NsRuntimeStoreConfig",
    "NsRuntimeWebSocketConfig",
    "close_cache_clients",
    "get_async_cache_client",
    "get_cache_client",
    "validate_cache_backend",
    "aclose_cache_clients",
]

__version__ = "0.0.1"
