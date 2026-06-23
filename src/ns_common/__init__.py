# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_common.config import NS_CONFIG_FILE_PATH, NS_ENV, ns_config
from ns_common.logging import configure_ns_logging, get_logger
from ns_common.paths import DATA_DIR, ETC_DIR, LOG_DIR, ROOT_DIR, SQL_DIR, TMP_DIR

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
    "configure_ns_logging",
    "get_logger",
]

__version__ = "0.0.1"
