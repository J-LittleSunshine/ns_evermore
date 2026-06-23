# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

ROOT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
ETC_DIR = ROOT_DIR / "etc"
LOG_DIR = ROOT_DIR / "log"
TMP_DIR = ROOT_DIR / "tmp"
SQL_DIR = ROOT_DIR / "sql"
SRC_DIR = ROOT_DIR / "src"


def ensure_runtime_dirs() -> None:
    must_dirs = {
        DATA_DIR,
        ETC_DIR,
        LOG_DIR,
        TMP_DIR,
    }
    for directory in must_dirs:
        directory.mkdir(parents=True, exist_ok=True)
