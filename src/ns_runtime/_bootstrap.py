# -*- coding: utf-8 -*-
"""Side-effect-free imports required by the runtime composition root.

The objects re-exported here are the authoritative ``ns_common`` definitions;
this module never constructs the legacy global ``ns_config`` and never prepares
runtime directories.  Ordinary public imports remain available from the
``ns_common`` facades.
"""

from __future__ import annotations

from ns_common.config.defaults import get_default_config_path
from ns_common.config.model import NsConfig
from ns_common.exceptions import (
    NsConfigError,
    NsDependencyError,
    NsRuntimeConfigInvalidError,
    NsRuntimeStartupSecurityError,
    NsRuntimeTransportDisabledError,
    NsValidationError,
)
from ns_common.paths import DATA_DIR, ETC_DIR, LOG_DIR, ROOT_DIR, TMP_DIR


__all__ = (
    "DATA_DIR",
    "ETC_DIR",
    "LOG_DIR",
    "ROOT_DIR",
    "TMP_DIR",
    "NsConfig",
    "NsConfigError",
    "NsDependencyError",
    "NsRuntimeConfigInvalidError",
    "NsRuntimeStartupSecurityError",
    "NsRuntimeTransportDisabledError",
    "NsValidationError",
    "get_default_config_path",
)
