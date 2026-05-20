# -*- coding: utf-8 -*-
from __future__ import annotations

import errno
import logging
import os
import shutil
import time
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    pass


class _LevelFilter(logging.Filter):
    def __init__(self, level: int):
        super().__init__()
        self._level = level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno == self._level


class _Logger(logging.Logger):
    _FMT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def __init__(self, log_name: str, log_path: Path, backup_folder: Optional[Path] = None, level: int = logging.DEBUG, rotation: int = 1, backup_count: int = 30, utc: bool = False):
        super().__init__(log_name, logging.DEBUG)
        self.propagate = False
        self._log_path = log_path
        self._backup_folder = backup_folder if backup_folder is not None else log_path / "backup"

        self._log_path.mkdir(exist_ok=True, parents=True)
        self._backup_folder.mkdir(exist_ok=True, parents=True)

        self.handlers.clear()

        formatter = logging.Formatter(self._FMT)

        self._add_console_handler(level=level, formatter=formatter, )

        self._add_file_handler(
            level=logging.DEBUG,
            formatter=formatter,
            rotation=rotation,
            backup_count=backup_count,
            utc=utc,
            level_name=log_name,
            exact_level=False,
        )

        for log_level in (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL):
            self._add_file_handler(
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

    def _add_file_handler(self, level: int, formatter: logging.Formatter, rotation: int, backup_count: int, utc: bool, level_name: Optional[str] = None, exact_level: bool = True) -> None:
        level_name = level_name or logging.getLevelName(level).lower()
        live_file = self._log_path / f"{level_name}.log"

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

        backup_dir = self._backup_folder / level_name
        backup_dir.mkdir(parents=True, exist_ok=True)

        def namer(default_name: str) -> str:
            filename = Path(default_name).name
            return str(backup_dir / filename)

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


_LOGGER_CACHE: dict[str, _Logger] = {}


def get_logger(
        log_name: str = "backend",
        log_path: Optional[Path] = None,
        backup_folder: Optional[Path] = None,
        level: int = logging.DEBUG,
        rotation: int = 1,
        backup_count: int = 30,
        utc: bool = False,
) -> _Logger:
    if log_name in _LOGGER_CACHE:
        return _LOGGER_CACHE[log_name]

    if log_path is None:
        from django.conf import settings

        _log_path = settings.LOG_DIR / log_name
    else:
        _log_path = log_path

    if backup_folder is None:
        from django.conf import settings
        _backup_folder = settings.LOG_BACKUP_DIR
    else:
        _backup_folder = backup_folder

    _logger = _Logger(
        log_name=log_name,
        log_path=_log_path,
        backup_folder=_backup_folder,
        level=level,
        rotation=rotation,
        backup_count=backup_count,
        utc=utc,
    )

    _LOGGER_CACHE[log_name] = _logger
    return _logger
