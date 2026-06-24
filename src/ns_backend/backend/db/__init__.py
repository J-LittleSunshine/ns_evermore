# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from backend.db.sql import SqlScriptRunner
from backend.db.vendor import (
    DB_VENDOR_DM8,
    DB_VENDOR_MYSQL,
    DB_VENDOR_POSTGRESQL,
    DB_VENDOR_SQLITE,
    DB_VENDOR_UNKNOWN,
    SUPPORTED_DB_VENDORS,
    detect_db_vendor_from_config,
    detect_db_vendor_from_connection,
    normalize_db_vendor,
)

if TYPE_CHECKING:
    pass

__all__ = [
    "DB_VENDOR_DM8",
    "DB_VENDOR_MYSQL",
    "DB_VENDOR_POSTGRESQL",
    "DB_VENDOR_SQLITE",
    "DB_VENDOR_UNKNOWN",
    "SUPPORTED_DB_VENDORS",
    "SqlScriptRunner",
    "detect_db_vendor_from_config",
    "detect_db_vendor_from_connection",
    "normalize_db_vendor",
]
