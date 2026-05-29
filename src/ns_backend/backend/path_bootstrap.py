# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

def ensure_src_on_sys_path() -> Path:
    # .../src/ns_backend/backend/path_bootstrap.py -> .../src
    src_dir = Path(__file__).resolve().parents[2]
    src_text = str(src_dir)

    normalized_paths = {
        os.path.normcase(os.path.normpath(p))
        for p in sys.path
        if isinstance(p, str)
    }
    normalized_src = os.path.normcase(os.path.normpath(src_text))

    if normalized_src not in normalized_paths:
        sys.path.insert(0, src_text)

    os.environ["PYTHONPATH"] = src_text
    return src_dir
