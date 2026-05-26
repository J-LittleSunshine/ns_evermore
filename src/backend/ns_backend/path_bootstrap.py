# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path


def ensure_project_src_on_path() -> None:
    """Ensure project-level src directory is importable for entrypoints."""
    src_dir = Path(__file__).resolve().parents[2]
    src_path = str(src_dir)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)


__all__ = ["ensure_project_src_on_path"]

