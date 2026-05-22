# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from typing import Any

from ns_common.logging import NsLogger, get_logger


def _coerce_level(value: Any) -> int:
    if isinstance(value, int):
        return value

    if isinstance(value, str):
        level_name = value.strip().upper()
        if not level_name:
            return logging.DEBUG
        if level_name in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            return int(getattr(logging, level_name))

    return logging.DEBUG


def _coerce_int(value: Any, default: int) -> int:
    try:
        if isinstance(value, str) and not value.strip():
            return default
        converted = int(value)
        if converted <= 0:
            return default
        return converted
    except (TypeError, ValueError):
        return default


def _coerce_bool(value: Any, default: bool) -> bool:
    true_values = {True, 1, "1", "true", "yes", "y", "on"}
    false_values = {False, 0, "0", "false", "no", "n", "off"}

    if isinstance(value, bool):
        return value

    normalized = value
    if isinstance(value, str):
        normalized = value.strip().lower()

    if normalized in true_values:
        return True

    if normalized in false_values:
        return False

    return default


def _coerce_str(value: Any, default: str) -> str:
    if value is None:
        return default

    if isinstance(value, str):
        normalized = value.strip()
        return normalized or default

    normalized = str(value).strip()
    return normalized or default


def _load_ns_logging_config() -> dict[str, Any]:
    # Import settings lazily so module import never triggers logger creation.
    from django.conf import settings

    config = getattr(settings, "NS_LOGGING", None)
    if isinstance(config, dict):
        return dict(config)

    return {}


def get_django_logger(
    *,
    log_name: str | None = None,
    component: str | None = None,
) -> NsLogger:
    config = _load_ns_logging_config()

    resolved_component = _coerce_str(
        component if component is not None else config.get("component"),
        default="ns_backend",
    )
    resolved_log_root = config.get("log_root")
    if isinstance(resolved_log_root, str) and not resolved_log_root.strip():
        resolved_log_root = None

    resolved_level = _coerce_level(config.get("level", "DEBUG"))
    resolved_rotation = _coerce_int(config.get("rotation", 1), default=1)
    resolved_backup_count = _coerce_int(config.get("backup_count", 30), default=30)
    resolved_utc = _coerce_bool(config.get("utc", False), default=False)
    resolved_multi_process = _coerce_bool(config.get("multi_process", False), default=False)
    resolved_pid_folder_prefix = _coerce_str(config.get("pid_folder_prefix"), default="pid")

    return get_logger(
        component=resolved_component,
        log_name=log_name,
        log_root=resolved_log_root,
        level=resolved_level,
        rotation=resolved_rotation,
        backup_count=resolved_backup_count,
        utc=resolved_utc,
        multi_process=resolved_multi_process,
        pid_folder_prefix=resolved_pid_folder_prefix,
    )


__all__ = ["get_django_logger"]

