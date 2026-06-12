# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path


def runtime_repo_root(script_file: str) -> Path:
    """Return repository root from one script file path."""
    return Path(script_file).resolve().parent.parent


def ensure_runtime_import_paths(script_file: str) -> Path:
    """Ensure repository src and scripts directories are importable.

    This keeps manual smoke scripts runnable from repository root without
    requiring PYTHONPATH=src;scripts.
    """
    repo_root = runtime_repo_root(script_file)
    src_path = repo_root / "src"
    scripts_path = repo_root / "scripts"

    for path in (src_path, scripts_path):
        normalized_path = str(path)
        if normalized_path not in sys.path:
            sys.path.insert(0, normalized_path)

    return repo_root


def resolve_repo_path(script_file: str, value: str) -> Path:
    """Resolve a path relative to repository root when it is not absolute."""
    raw_path = Path(str(value or "").strip())
    if raw_path.is_absolute():
        return raw_path

    return runtime_repo_root(script_file) / raw_path
