# -*- coding: utf-8 -*-
from __future__ import annotations

import errno
import logging
import os
import shutil
import time
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


class _LevelFilter(logging.Filter):
    def __init__(self, level: int):
        super().__init__()
        self._level = level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno == self._level


def _resolve_log_root(log_root: Path | str | None) -> Path:
    if log_root is not None:
        return Path(log_root).expanduser().resolve()

    env_root = os.getenv("NS_LOG_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()

    return (Path.cwd() / "log").resolve()


def _validate_component(component: str) -> str:
    value = str(component or "").strip()
    if not value:
        raise ValueError("component cannot be empty")

    if value in {".", ".."} or ".." in value:
        raise ValueError("component cannot contain '..'")

    if "/" in value or "\\" in value:
        raise ValueError("component must be a single directory name")

    return value


def _validate_log_name(log_name: str | None, component: str) -> str:
    value = str(log_name).strip() if log_name is not None else component
    if not value:
        raise ValueError("log_name cannot be empty")

    if value in {".", ".."} or ".." in value:
        raise ValueError("log_name cannot contain '..'")

    if "/" in value or "\\" in value:
        raise ValueError("log_name must be a single file name")

    return value


def _validate_pid_folder_prefix(pid_folder_prefix: str) -> str:
    value = str(pid_folder_prefix or "").strip()
    if not value:
        raise ValueError("pid_folder_prefix cannot be empty")

    if value in {".", ".."} or ".." in value:
        raise ValueError("pid_folder_prefix cannot contain '..'")

    if "/" in value or "\\" in value:
        raise ValueError("pid_folder_prefix must be a single directory name prefix")

    return value


class NsLogger(logging.Logger):
    _FMT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def __init__(
        self,
        *,
        logger_name: str,
        component_dir: Path,
        log_name: str,
        level: int = logging.DEBUG,
        rotation: int = 1,
        backup_count: int = 30,
        utc: bool = False,
    ):
        super().__init__(logger_name, logging.DEBUG)
        self.propagate = False

        component_dir.mkdir(parents=True, exist_ok=True)

        formatter = logging.Formatter(self._FMT)

        self._add_console_handler(level=level, formatter=formatter)

        self._add_file_handler(
            component_dir=component_dir,
            file_name=f"{log_name}.log",
            level=logging.DEBUG,
            formatter=formatter,
            rotation=rotation,
            backup_count=backup_count,
            utc=utc,
            exact_level=False,
        )

        for log_level in (
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL,
        ):
            self._add_file_handler(
                component_dir=component_dir,
                file_name=f"{logging.getLevelName(log_level).lower()}.log",
                level=log_level,
                formatter=formatter,
                rotation=rotation,
                backup_count=backup_count,
                utc=utc,
                exact_level=True,
            )

    def _add_console_handler(self, level: int, formatter: logging.Formatter) -> None:
        console = logging.StreamHandler()
        console.setLevel(level)
        console.setFormatter(formatter)
        self.addHandler(console)

    def _add_file_handler(
        self,
        *,
        component_dir: Path,
        file_name: str,
        level: int,
        formatter: logging.Formatter,
        rotation: int,
        backup_count: int,
        utc: bool,
        exact_level: bool,
    ) -> None:
        live_file = component_dir / file_name

        handler = TimedRotatingFileHandler(
            filename=live_file,
            when="D",
            interval=rotation,
            backupCount=backup_count,
            encoding="utf-8",
            utc=utc,
        )

        handler.setLevel(level)
        if exact_level:
            handler.addFilter(_LevelFilter(level))

        handler.setFormatter(formatter)

        backup_dir = component_dir / "backup" / Path(file_name).stem
        backup_dir.mkdir(parents=True, exist_ok=True)

        def namer(default_name: str) -> str:
            return str(backup_dir / Path(default_name).name)

        def rotator(src: str, dst: str) -> None:
            self._safe_rotate(src=src, dst=dst)

        handler.namer = namer
        handler.rotator = rotator
        self.addHandler(handler)

    @staticmethod
    def _safe_rotate(src: str, dst: str) -> None:
        max_tries = 10
        backoff = 0.2
        dst_path = Path(dst)

        if dst_path.exists():
            try:
                os.remove(dst)
            except PermissionError:
                pass

        for _ in range(max_tries):
            try:
                try:
                    os.replace(src, dst)
                except OSError as exc:
                    if exc.errno == errno.EXDEV:
                        shutil.move(src, dst)
                    else:
                        raise
                return
            except PermissionError:
                time.sleep(backoff)
                backoff *= 1.5
            except FileNotFoundError:
                return

        try:
            shutil.copy2(src, dst)
            with open(src, "w", encoding="utf-8"):
                pass
        except Exception:  # noqa
            pass


_LOGGER_CACHE: dict[tuple[str, str, str, bool, int | None, str], NsLogger] = {}


def get_logger(
    *,
    component: str,
    log_name: str | None = None,
    log_root: Path | str | None = None,
    level: int = logging.DEBUG,
    rotation: int = 1,
    backup_count: int = 30,
    utc: bool = False,
    multi_process: bool = False,
    pid_folder_prefix: str = "pid",
) -> NsLogger:
    component_name = _validate_component(component)
    resolved_root = _resolve_log_root(log_root)
    resolved_log_name = _validate_log_name(log_name=log_name, component=component_name)
    resolved_pid_folder_prefix = _validate_pid_folder_prefix(pid_folder_prefix)
    pid_value = os.getpid() if multi_process else None

    cache_key = (
        str(resolved_root),
        component_name,
        resolved_log_name,
        multi_process,
        pid_value,
        resolved_pid_folder_prefix,
    )
    cached = _LOGGER_CACHE.get(cache_key)
    if cached is not None:
        return cached

    logger_name = f"{component_name}.{resolved_log_name}"
    component_dir = resolved_root / component_name
    if multi_process:
        component_dir = component_dir / f"{resolved_pid_folder_prefix}{pid_value}"

    logger = NsLogger(
        logger_name=logger_name,
        component_dir=component_dir,
        log_name=resolved_log_name,
        level=level,
        rotation=rotation,
        backup_count=backup_count,
        utc=utc,
    )

    _LOGGER_CACHE[cache_key] = logger
    return logger


__all__ = ["NsLogger", "get_logger"]

