# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

ROOT_DIR = Path(__file__).parent.parent.parent.absolute()
DATA_DIR = ROOT_DIR / "data"
ETC_DIR = ROOT_DIR / "etc"
LOG_DIR = ROOT_DIR / "log"
TMP_DIR = ROOT_DIR / "tmp"
SQL_DIR = ROOT_DIR / "sql"
_REQUIRED_DIRS = [DATA_DIR, ETC_DIR, LOG_DIR, TMP_DIR]
for _dir in _REQUIRED_DIRS:
    _dir.mkdir(parents=True, exist_ok=True)

NS_ENV = os.environ.get("NS_ENV", "local").lower()
if NS_ENV == "prod":
    NS_CONFIG_FILE_PATH = ETC_DIR / "ns_config.prod.json"
elif NS_ENV == "dev":
    NS_CONFIG_FILE_PATH = ETC_DIR / "ns_config.dev.json"
elif NS_ENV == "test":
    NS_CONFIG_FILE_PATH = ETC_DIR / "ns_config.test.json"
else:
    NS_CONFIG_FILE_PATH = ETC_DIR / "ns_config.local.json"

if not NS_CONFIG_FILE_PATH.exists():
    with open(NS_CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
        f.write("{}")
