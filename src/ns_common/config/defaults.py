# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from pathlib import Path

from ..paths import ETC_DIR


_ALLOWED_ENVIRONMENTS = {
    "local",
    "dev",
    "test",
    "prod",
}


def get_ns_env() -> str:
    env = os.getenv("NS_ENV", "local").strip().lower()

    if env not in _ALLOWED_ENVIRONMENTS:
        return "local"

    return env


NS_ENV = get_ns_env()


def get_default_config_path(environment: str | None = None) -> Path:
    selected_environment = (environment or get_ns_env()).strip().lower()
    if selected_environment not in _ALLOWED_ENVIRONMENTS:
        selected_environment = "local"

    return ETC_DIR / f"ns_config.{selected_environment}.json"


NS_CONFIG_FILE_PATH = get_default_config_path()
