# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging
import os
import sys
import traceback
from dataclasses import asdict
from datetime import datetime, time, timezone
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from threading import RLock
from typing import Any, Mapping, TYPE_CHECKING

from ns_common import LOG_DIR
from ns_common.config import ns_config

try:
    from concurrent_log_handler import ConcurrentTimedRotatingFileHandler as _ConcurrentTimedRotatingFileHandler
except ImportError:
    _ConcurrentTimedRotatingFileHandler = None

if TYPE_CHECKING:
    pass

_LOGGER_LOCK: RLock = RLock()
_LOGGER_MAP: dict[str, "NsLogger"] = {}

_DEFAULT_LEVEL_FILES: tuple[str, ...] = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


class _ExactLevelFilter(logging.Filter):

    def __init__(self, _levelno: int) -> None:
        super().__init__()
        self._levelno: int = _levelno

    def filter(self, _record: logging.LogRecord) -> bool:
        return _record.levelno == self._levelno

class _JsonLogFormatter(logging.Formatter):
    """Format log records as one-line JSON."""

    _RESERVED_KEYS: set[str] = {
        "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
        "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "created", "msecs", "relativeCreated", "thread", "threadName",
        "processName", "process", "message", "asctime",
    }

    def __init__(self, datefmt: str | None = None, utc_enabled: bool = False) -> None:
        super().__init__(datefmt=datefmt)
        self._utc_enabled: bool = utc_enabled

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        converter = datetime.fromtimestamp
        if self._utc_enabled:
            dt = datetime.fromtimestamp(record.created, timezone.utc)
        else:
            dt = converter(record.created)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat(timespec="milliseconds")

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()

        payload: dict[str, object] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.message,
            "module": record.module,
            "filename": record.filename,
            "lineno": record.lineno,
            "func_name": record.funcName,
            "process": record.process,
            "process_name": record.processName,
            "thread": record.thread,
            "thread_name": record.threadName,
        }

        for key, value in record.__dict__.items():
            if key in self._RESERVED_KEYS or key.startswith("_"):
                continue
            payload[key] = self._normalize_value(value)

        if record.exc_info:
            payload["exception"] = "".join(traceback.format_exception(*record.exc_info)).rstrip()

        if record.stack_info:
            payload["stack"] = record.stack_info

        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)

    @staticmethod
    def _normalize_value(value: object) -> object:
        """Normalize extra value for JSON serialization."""
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, (list, tuple, set)):
            return list(value)
        if isinstance(value, dict):
            return value
        return str(value)

class _BackupTimedRotatingFileHandler(TimedRotatingFileHandler):

    def __init__(self, filename: Path, backup_dir: Path, **kwargs: Any) -> None:
        self._backup_dir: Path = backup_dir
        self._source_filename: str = filename.name
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        super().__init__(filename=str(filename), **kwargs)

    def rotation_filename(self, _default_name: str) -> str:
        return str(self._backup_dir / Path(_default_name).name)

    def getFilesToDelete(self) -> list[str]:
        if self.backupCount <= 0:
            return []

        candidates: list[str] = sorted(str(_path) for _path in self._backup_dir.glob(f"{self._source_filename}.*") if _path.is_file())

        delete_count: int = len(candidates) - self.backupCount
        if delete_count <= 0:
            return []

        return candidates[:delete_count]


if _ConcurrentTimedRotatingFileHandler is not None:

    class _BackupConcurrentTimedRotatingFileHandler(_ConcurrentTimedRotatingFileHandler):  # type: ignore[misc]
        """Multiprocess-safe timed rotating handler that stores rotated files under backup."""

        def __init__(self, filename: Path, backup_dir: Path, **kwargs: Any) -> None:
            self._backup_dir: Path = backup_dir
            self._source_filename: str = filename.name
            self._backup_dir.mkdir(parents=True, exist_ok=True)
            super().__init__(filename=str(filename), **kwargs)

        def rotation_filename(self, _default_name: str) -> str:
            # Keep the default rotated file name and only change its parent directory.
            return str(self._backup_dir / Path(_default_name).name)

        # noinspection PyPep8Naming
        def getFilesToDelete(self) -> list[str]:
            # With a custom backup directory, cleanup must use backup_dir glob matching.
            backup_count: int = int(getattr(self, "backupCount", 0))
            if backup_count <= 0:
                return []

            candidates: list[str] = sorted(str(_path) for _path in self._backup_dir.glob(f"{self._source_filename}.*") if _path.is_file())

            delete_count: int = len(candidates) - backup_count
            if delete_count <= 0:
                return []

            return candidates[:delete_count]

else:
    _BackupConcurrentTimedRotatingFileHandler = None


class NsLogger(logging.Logger):
    def __new__(cls, name: str, multiprocessing_mode: bool = False) -> "NsLogger":
        with _LOGGER_LOCK:
            logger: NsLogger | None = _LOGGER_MAP.get(name)
            if logger is None:
                logger = super().__new__(cls)
                _LOGGER_MAP[name] = logger
            return logger

    def __init__(self, name: str, multiprocessing_mode: bool = False) -> None:
        with _LOGGER_LOCK:
            if not getattr(self, "_base_initialized", False):
                super().__init__(name=name, level=logging.DEBUG)
                self._base_initialized: bool = True
                self._initialized: bool = False
                self._owner_pid: int = -1
                self._multiprocessing_mode: bool = multiprocessing_mode

            should_reconfigure: bool = not self._initialized or self._owner_pid != os.getpid() or self._multiprocessing_mode != multiprocessing_mode

            if not should_reconfigure:
                return

            self._multiprocessing_mode = multiprocessing_mode
            self._configure()

    def _log(self, level: int, msg: object, args: Any, exc_info: Any = None, extra: Mapping[str, object] | None = None, stack_info: bool = False, stacklevel: int = 1) -> None:
        self._ensure_current_process()
        super()._log(level, msg, args, exc_info, extra, stack_info, stacklevel)

    def _ensure_current_process(self) -> None:
        if self._owner_pid == os.getpid() and self._initialized:
            return

        with _LOGGER_LOCK:
            if self._owner_pid == os.getpid() and self._initialized:
                return
            self._configure()

    def _configure(self) -> None:
        config: dict[str, Any] = asdict(getattr(ns_config, "log_config"))

        utc_enabled: bool = bool(config.get("utc", False))
        date_text: str = self._get_current_date_text(utc_enabled)

        active_dir: Path = Path(LOG_DIR) / self.name / date_text
        backup_dir: Path = Path(LOG_DIR) / self.name / "backup" / date_text
        active_dir.mkdir(parents=True, exist_ok=True)
        backup_dir.mkdir(parents=True, exist_ok=True)

        self._reset_handlers()

        format_type: str = str(config.get("format_type", "json") or "json").strip().lower()
        datefmt: str = str(config.get("datefmt", "%Y-%m-%d %H:%M:%S"))

        if format_type == "json":
            formatter: logging.Formatter = _JsonLogFormatter(datefmt=datefmt, utc_enabled=utc_enabled)
        elif format_type == "text":
            formatter = logging.Formatter(
                fmt=str(config.get("format", "%(asctime)s - %(levelname)-8s - %(process)d:%(threadName)s - %(name)s - %(filename)s:%(lineno)d - %(message)s")),
                datefmt=datefmt,
            )
        else:
            raise ValueError("log_config.format_type must be json or text")
        main_level: int = self._resolve_level(config.get("file_level", config.get("level", "DEBUG")), logging.DEBUG)
        console_level: int = self._resolve_level(config.get("console_level", config.get("level", "DEBUG")), logging.DEBUG)
        level_files: tuple[str, ...] = self._resolve_level_files(config.get("level_files", _DEFAULT_LEVEL_FILES))

        handler_levels: list[int] = [main_level, console_level]
        handler_levels.extend(self._resolve_level(_level, logging.DEBUG) for _level in level_files)
        self.setLevel(min(handler_levels))
        self.propagate = False
        self.disabled = False

        if bool(config.get("console", True)):
            console_handler: logging.StreamHandler = logging.StreamHandler(stream=sys.stdout)
            console_handler.setLevel(console_level)
            console_handler.setFormatter(formatter)
            self.addHandler(console_handler)

        main_handler: logging.Handler = self._build_file_handler(active_dir / f"{self.name}.log", backup_dir, config)
        main_handler.setLevel(main_level)
        main_handler.setFormatter(formatter)
        self.addHandler(main_handler)

        for level_name in level_files:
            level_no: int = self._resolve_level(level_name, logging.DEBUG)
            level_handler: logging.Handler = self._build_file_handler(active_dir / f"{self.name}.{level_name.lower()}.log", backup_dir, config)
            level_handler.setLevel(level_no)
            level_handler.addFilter(_ExactLevelFilter(level_no))
            level_handler.setFormatter(formatter)
            self.addHandler(level_handler)

        self._owner_pid = os.getpid()
        self._initialized = True

    def _reset_handlers(self) -> None:
        for handler in list(self.handlers):
            self.removeHandler(handler)

            try:
                handler.flush()
            except Exception:  # noqa
                pass

            try:
                handler.close()
            except Exception:  # noqa
                pass

    def _build_file_handler(self, filename: Path, backup_dir: Path, config: Mapping[str, Any]) -> _BackupConcurrentTimedRotatingFileHandler | _BackupTimedRotatingFileHandler:
        at_time: time | None = self._parse_at_time(config.get("at_time"))

        kwargs: dict[str, Any] = {"when": str(config.get("when", "midnight")), "interval": int(config.get("interval", 1)), "backupCount": int(config.get("backup_count", 14)), "encoding": str(config.get("encoding", "utf-8")), "delay": bool(config.get("delay", True)), "utc": bool(config.get("utc", False))}

        if at_time is not None:
            kwargs["atTime"] = at_time

        if self._multiprocessing_mode:
            if _BackupConcurrentTimedRotatingFileHandler is None:
                raise RuntimeError("concurrent-log-handler is required when multiprocessing_mode=True.")

            kwargs["maxBytes"] = int(config.get("max_bytes", 0))
            kwargs["use_gzip"] = bool(config.get("use_gzip", False))

            lock_file_directory: str | None = config.get("lock_file_directory")
            if lock_file_directory:
                kwargs["lock_file_directory"] = lock_file_directory

            return _BackupConcurrentTimedRotatingFileHandler(filename=filename, backup_dir=backup_dir, **kwargs)

        return _BackupTimedRotatingFileHandler(filename=filename, backup_dir=backup_dir, **kwargs)

    @staticmethod
    def _resolve_level(_level: Any, _default: int) -> int:
        if isinstance(_level, int):
            return _level

        if isinstance(_level, str):
            resolved_level: str | int = logging.getLevelName(_level.upper())
            if isinstance(resolved_level, int):
                return resolved_level

        return _default

    @staticmethod
    def _resolve_level_files(_value: Any) -> tuple[str, ...]:
        if not isinstance(_value, (list, tuple, set)):
            return _DEFAULT_LEVEL_FILES

        result: list[str] = []
        for item in _value:
            if not isinstance(item, str):
                continue

            level_name: str = item.upper()
            resolved_level: str | int = logging.getLevelName(level_name)
            if isinstance(resolved_level, int):
                result.append(level_name)

        if not result:
            return _DEFAULT_LEVEL_FILES

        return tuple(result)

    @staticmethod
    def _parse_at_time(_value: Any) -> time | None:
        if _value is None or _value == "":
            return None

        if isinstance(_value, time):
            return _value

        if not isinstance(_value, str):
            raise ValueError("Invalid at_time config.")

        parts: list[str] = _value.split(":")
        if len(parts) not in (2, 3):
            raise ValueError("Invalid at_time config.")

        hour: int = int(parts[0])
        minute: int = int(parts[1])
        second: int = int(parts[2]) if len(parts) == 3 else 0

        return time(hour=hour, minute=minute, second=second)

    @staticmethod
    def _get_current_date_text(_utc_enabled: bool) -> str:
        if _utc_enabled:
            return datetime.now(timezone.utc).strftime("%Y-%m-%d")

        return datetime.now().strftime("%Y-%m-%d")


def get_ns_logger(name: str, multiprocessing_mode: bool = False) -> NsLogger:
    return NsLogger(name=name, multiprocessing_mode=multiprocessing_mode)


def close_ns_loggers() -> None:
    with _LOGGER_LOCK:
        for logger in _LOGGER_MAP.values():
            logger._reset_handlers()  # noqa
            logger._initialized = False
            logger._owner_pid = -1
