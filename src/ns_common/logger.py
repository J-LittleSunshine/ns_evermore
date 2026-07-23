# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import importlib
import json
import logging
import os
import sys
from dataclasses import asdict
from datetime import (
    datetime,
    time,
    timezone
)
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from threading import RLock
from typing import (
    Any,
    Mapping,
    TYPE_CHECKING
)

from ns_common.paths import LOG_DIR
from ns_common.security import (
    REDACTED,
    Sanitizer,
)

if TYPE_CHECKING:
    pass

_LOGGER_LOCK: RLock = RLock()
_LOGGER_MAP: dict[str, "NsLogger"] = {}

_DEFAULT_LEVEL_FILES: tuple[str, ...] = (
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL"
)

_LOG_RECORD_RESERVED_KEYS = frozenset({
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "message",
    "asctime",
})

_JSON_OUTPUT_RESERVED_KEYS = frozenset({
    "timestamp",
    "level",
    "logger",
    "message",
    "module",
    "filename",
    "lineno",
    "func_name",
    "process",
    "process_name",
    "thread",
    "thread_name",
    "exception",
    "stack",
    "extra_fields",
})

_TEXT_OUTPUT_RESERVED_KEYS = frozenset({
    "levelname",
    "name",
    "processName",
    "threadName",
    "filename",
    "funcName",
    "lineno",
    "exc_info",
    "exc_text",
    "stack_info",
    "message",
    "asctime",
})

_CALLER_EXTRA_CONFLICT_KEYS = (
    _JSON_OUTPUT_RESERVED_KEYS | _TEXT_OUTPUT_RESERVED_KEYS
)


class _ExactLevelFilter(logging.Filter):

    def __init__(self, _levelno: int) -> None:
        super().__init__()
        self._levelno: int = _levelno

    def filter(self, _record: logging.LogRecord) -> bool:
        return _record.levelno == self._levelno


def _safe_record_message(
    record: logging.LogRecord,
    sanitizer: Sanitizer,
) -> str:
    if not isinstance(record.msg, str):
        sanitized_message = sanitizer.sanitize(
            record.msg,
            path=("log", "message"),
        )
        if record.args:
            sanitized_message = {
                "message": sanitized_message,
                "args": _sanitize_message_args(record.args, sanitizer),
            }
        if isinstance(sanitized_message, str):
            return sanitized_message
        try:
            return json.dumps(
                sanitized_message,
                allow_nan=False,
                ensure_ascii=False,
                separators=(",", ":"),
            )
        except Exception:
            return REDACTED

    safe_record = copy.copy(record)
    safe_record.args = _sanitize_message_args(record.args, sanitizer)
    try:
        message = safe_record.getMessage()
    except Exception:
        return REDACTED
    return sanitizer.sanitize_text(message)


def _sanitize_message_args(args: Any, sanitizer: Sanitizer) -> Any:
    if isinstance(args, tuple):
        return tuple(
            sanitizer.sanitize(
                item,
                path=("log", "message_args", str(index)),
            )
            for index, item in enumerate(args)
        )
    if isinstance(args, Mapping):
        sanitized_args = sanitizer.sanitize(
            args,
            path=("log", "message_args"),
        )
        return sanitized_args if isinstance(sanitized_args, dict) else {}
    return ()


def _traceback_metadata(exc_info: Any) -> list[dict[str, object]]:
    try:
        traceback_object = exc_info[2]
    except Exception:
        return []

    result: list[dict[str, object]] = []
    while traceback_object is not None:
        try:
            code = traceback_object.tb_frame.f_code
            result.append({
                "filename": code.co_filename,
                "lineno": traceback_object.tb_lineno,
                "function": code.co_name,
            })
            traceback_object = traceback_object.tb_next
        except Exception:
            return []
    return result


def _partition_record_extra(
    record: logging.LogRecord,
) -> tuple[dict[object, object], dict[object, object]]:
    ordinary: dict[object, object] = {}
    conflicting: dict[object, object] = {}
    for key, value in record.__dict__.items():
        if key in {"message", "asctime"}:
            conflicting[key] = value
            continue
        if key in _LOG_RECORD_RESERVED_KEYS:
            continue
        if isinstance(key, str) and key.startswith("_"):
            continue
        target = conflicting if key in _CALLER_EXTRA_CONFLICT_KEYS else ordinary
        target[key] = value
    return ordinary, conflicting


class _JsonLogFormatter(logging.Formatter):
    """Format log records as one-line JSON."""

    _RESERVED_KEYS = _LOG_RECORD_RESERVED_KEYS

    def __init__(
        self,
        *,
        sanitizer: Sanitizer,
        datefmt: str | None = None,
        utc_enabled: bool = False,
    ) -> None:
        super().__init__(datefmt=datefmt)
        self._sanitizer = sanitizer
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
        payload: dict[object, object] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": _safe_record_message(record, self._sanitizer),
            "module": record.module,
            "filename": record.filename,
            "lineno": record.lineno,
            "func_name": record.funcName,
            "process": record.process,
            "process_name": record.processName,
            "thread": record.thread,
            "thread_name": record.threadName,
        }

        if record.exc_info:
            payload["exception"] = {
                "error": record.exc_info[1],
                "traceback": _traceback_metadata(record.exc_info),
            }

        if record.stack_info:
            payload["stack"] = record.stack_info

        ordinary_extra, conflicting_extra = _partition_record_extra(record)
        payload.update(ordinary_extra)
        if conflicting_extra:
            payload["extra_fields"] = conflicting_extra

        sanitized_payload = self._sanitizer.sanitize(payload)
        if not isinstance(sanitized_payload, dict):
            sanitized_payload = {"message": REDACTED}
        return json.dumps(
            sanitized_payload,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
        )


class _SanitizingTextLogFormatter(logging.Formatter):
    """Delegate all value safety decisions to an injected Sanitizer."""

    _RESERVED_KEYS = _JsonLogFormatter._RESERVED_KEYS

    def __init__(
        self,
        *,
        sanitizer: Sanitizer,
        fmt: str,
        datefmt: str | None = None,
    ) -> None:
        super().__init__(fmt=fmt, datefmt=datefmt)
        self._sanitizer = sanitizer

    def format(self, record: logging.LogRecord) -> str:
        safe_record = copy.copy(record)
        safe_message = _safe_record_message(record, self._sanitizer)
        safe_record.msg = safe_message
        safe_record.args = ()
        if record.exc_info:
            safe_record.exc_text = self.formatException(record.exc_info)
            safe_record.exc_info = None
        else:
            safe_record.exc_text = None

        ordinary_extra, conflicting_extra = _partition_record_extra(record)
        raw_extra: dict[object, object] = dict(ordinary_extra)
        if conflicting_extra:
            raw_extra["extra_fields"] = conflicting_extra
        sanitized_extra = self._sanitizer.sanitize(raw_extra)
        if isinstance(sanitized_extra, dict):
            safe_record.__dict__.update(sanitized_extra)
        elif raw_extra:
            safe_record.__dict__["extra"] = REDACTED

        safe_stack: str | None = None
        if isinstance(record.stack_info, str):
            safe_stack = self._sanitizer.sanitize_text(
                record.stack_info
            )
        safe_record.stack_info = safe_stack

        # Restore every formatter-owned field after caller extras are applied.
        # JSON-style aliases are also authoritative in text format strings; a
        # caller can inspect its conflicting values only through extra_fields.
        safe_record.__dict__.update({
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": safe_message,
            "module": record.module,
            "filename": record.filename,
            "lineno": record.lineno,
            "func_name": record.funcName,
            "process": record.process,
            "process_name": record.processName,
            "thread": record.thread,
            "thread_name": record.threadName,
            "exception": safe_record.exc_text,
            "stack": safe_stack,
            "levelname": record.levelname,
            "name": record.name,
            "processName": record.processName,
            "threadName": record.threadName,
            "funcName": record.funcName,
            "exc_info": None if record.exc_info else record.exc_info,
            "exc_text": safe_record.exc_text,
            "stack_info": safe_stack,
        })

        return super().format(safe_record)

    def formatException(self, exc_info: Any) -> str:
        sanitized_exception = self._sanitizer.sanitize({
            "error": exc_info[1],
            "traceback": _traceback_metadata(exc_info),
        })
        return json.dumps(
            sanitized_exception,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
        )


class _ConsoleTextLogFormatter(_SanitizingTextLogFormatter):
    RESET = "\033[0m"

    LEVEL_COLORS: dict[int, str] = {
        logging.DEBUG: "\033[36m",
        logging.INFO: "\033[32m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[35m",
    }

    STATUS_COLORS: tuple[tuple[int, int, str], ...] = (
        (200, 299, "\033[32m"),
        (300, 399, "\033[36m"),
        (400, 499, "\033[33m"),
        (500, 599, "\033[31m"),
    )

    def __init__(
        self,
        *,
        sanitizer: Sanitizer,
        fmt: str,
        datefmt: str | None = None,
        color_enabled: bool = True,
    ) -> None:
        super().__init__(sanitizer=sanitizer, fmt=fmt, datefmt=datefmt)
        self.color_enabled = color_enabled

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)

        if not self.color_enabled:
            return message

        color = self._resolve_color(record)

        if not color:
            return message

        return f"{color}{message}{self.RESET}"

    def _resolve_color(self, record: logging.LogRecord) -> str | None:
        status_code = getattr(record, "status_code", None)

        if isinstance(status_code, int):
            for min_code, max_code, color in self.STATUS_COLORS:
                if min_code <= status_code <= max_code:
                    return color

        return self.LEVEL_COLORS.get(record.levelno)

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


_BackupConcurrentTimedRotatingFileHandler: type[logging.Handler] | None = None
_CONCURRENT_HANDLER_LOAD_ATTEMPTED = False


def _load_backup_concurrent_handler_class() -> type[logging.Handler] | None:
    """Load the optional multiprocess handler only when it is requested."""
    global _BackupConcurrentTimedRotatingFileHandler
    global _CONCURRENT_HANDLER_LOAD_ATTEMPTED

    with _LOGGER_LOCK:
        if _CONCURRENT_HANDLER_LOAD_ATTEMPTED:
            return _BackupConcurrentTimedRotatingFileHandler

        try:
            module = importlib.import_module("concurrent_log_handler")
            concurrent_handler = module.ConcurrentTimedRotatingFileHandler
        except (AttributeError, ImportError):
            _CONCURRENT_HANDLER_LOAD_ATTEMPTED = True
            return None

        class _LazyBackupConcurrentTimedRotatingFileHandler(concurrent_handler):  # type: ignore[misc, valid-type]
            def __init__(
                self,
                filename: Path,
                backup_dir: Path,
                **kwargs: Any,
            ) -> None:
                self._backup_dir: Path = backup_dir
                self._source_filename: str = filename.name
                self._backup_dir.mkdir(parents=True, exist_ok=True)
                super().__init__(filename=str(filename), **kwargs)

            def rotation_filename(self, _default_name: str) -> str:
                return str(self._backup_dir / Path(_default_name).name)

            # noinspection PyPep8Naming
            def getFilesToDelete(self) -> list[str]:
                backup_count: int = int(getattr(self, "backupCount", 0))
                if backup_count <= 0:
                    return []

                candidates: list[str] = sorted(
                    str(path)
                    for path in self._backup_dir.glob(
                        f"{self._source_filename}.*"
                    )
                    if path.is_file()
                )
                delete_count = len(candidates) - backup_count
                if delete_count <= 0:
                    return []
                return candidates[:delete_count]

        _BackupConcurrentTimedRotatingFileHandler = (
            _LazyBackupConcurrentTimedRotatingFileHandler
        )
        _CONCURRENT_HANDLER_LOAD_ATTEMPTED = True
        return _BackupConcurrentTimedRotatingFileHandler


class NsLogger(logging.Logger):
    def __new__(
        cls,
        name: str,
        multiprocessing_mode: bool = False,
        sanitizer: Sanitizer | None = None,
        config: Mapping[str, object] | None = None,
        log_dir: str | os.PathLike[str] | None = None,
    ) -> "NsLogger":
        if sanitizer is not None and not isinstance(sanitizer, Sanitizer):
            raise TypeError("sanitizer must be a Sanitizer instance")
        if config is not None and not isinstance(config, Mapping):
            raise TypeError("config must be a mapping")
        if log_dir is not None and not isinstance(log_dir, (str, os.PathLike)):
            raise TypeError("log_dir must be path-like")
        with _LOGGER_LOCK:
            logger: NsLogger | None = _LOGGER_MAP.get(name)
            if logger is None:
                logger = super().__new__(cls)
                _LOGGER_MAP[name] = logger
            return logger

    def __init__(
        self,
        name: str,
        multiprocessing_mode: bool = False,
        sanitizer: Sanitizer | None = None,
        config: Mapping[str, object] | None = None,
        log_dir: str | os.PathLike[str] | None = None,
    ) -> None:
        with _LOGGER_LOCK:
            explicit_config = (
                None
                if config is None
                else copy.deepcopy(dict(config))
            )
            explicit_log_dir = None if log_dir is None else Path(log_dir)
            if not getattr(self, "_base_initialized", False):
                super().__init__(name=name, level=logging.DEBUG)
                self._base_initialized: bool = True
                self._initialized: bool = False
                self._owner_pid: int = -1
                self._multiprocessing_mode: bool = multiprocessing_mode
                self._sanitizer: Sanitizer = sanitizer or Sanitizer()
                self._explicit_config: dict[str, object] | None = None
                self._explicit_log_dir: Path | None = None

            next_sanitizer = sanitizer or self._sanitizer
            should_reconfigure: bool = (
                not self._initialized
                or self._owner_pid != os.getpid()
                or self._multiprocessing_mode != multiprocessing_mode
                or next_sanitizer is not self._sanitizer
                or explicit_config != self._explicit_config
                or explicit_log_dir != self._explicit_log_dir
            )

            if not should_reconfigure:
                return

            self._multiprocessing_mode = multiprocessing_mode
            self._sanitizer = next_sanitizer
            self._explicit_config = explicit_config
            self._explicit_log_dir = explicit_log_dir
            self._configure()

    @property
    def sanitizer(self) -> Sanitizer:
        return self._sanitizer

    def close(self) -> None:
        """Flush and close this logger's handlers idempotently."""

        with _LOGGER_LOCK:
            self._reset_handlers()
            self._initialized = False
            self._owner_pid = -1

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
        if self._explicit_config is None:
            from ns_common.config import ns_config

            config: dict[str, Any] = asdict(ns_config.log)
        else:
            config = copy.deepcopy(self._explicit_config)

        utc_enabled: bool = bool(config.get("utc", False))
        date_text: str = self._get_current_date_text(utc_enabled)

        log_root = self._explicit_log_dir or Path(LOG_DIR)
        active_dir: Path = log_root / self.name / date_text
        backup_dir: Path = log_root / self.name / "backup" / date_text
        active_dir.mkdir(parents=True, exist_ok=True)
        backup_dir.mkdir(parents=True, exist_ok=True)

        self._reset_handlers()

        default_format_type: str = str(config.get("format_type", "json") or "json").strip().lower()
        console_format_type: str = str(config.get("console_format_type") or default_format_type).strip().lower()
        file_format_type: str = str(config.get("file_format_type") or default_format_type).strip().lower()
        datefmt: str = str(config.get("datefmt", "%Y-%m-%d %H:%M:%S"))
        text_format: str = str(config.get("format", "%(asctime)s - %(levelname)-8s - %(process)d:%(threadName)s - %(name)s - %(filename)s:%(lineno)d - %(message)s"))

        def _build_formatter(_format_type: str) -> logging.Formatter:
            if _format_type == "json":
                return _JsonLogFormatter(
                    sanitizer=self._sanitizer,
                    datefmt=datefmt,
                    utc_enabled=utc_enabled,
                )

            if _format_type == "text":
                return _SanitizingTextLogFormatter(
                    sanitizer=self._sanitizer,
                    fmt=text_format,
                    datefmt=datefmt,
                )

            if _format_type == "color_text":
                return _ConsoleTextLogFormatter(
                    sanitizer=self._sanitizer,
                    fmt=text_format,
                    datefmt=datefmt,
                    color_enabled=True,
                )

            raise ValueError("log format type must be json or text")

        console_formatter: logging.Formatter = _build_formatter(console_format_type)
        file_formatter: logging.Formatter = _build_formatter(file_format_type)

        main_level: int = self._resolve_level(config.get("file_level", config.get("level", "DEBUG")), logging.DEBUG)
        console_level: int = self._resolve_level(config.get("console_level", config.get("level", "DEBUG")), logging.DEBUG)
        level_files: tuple[str, ...] = self._resolve_level_files(config.get("level_files", _DEFAULT_LEVEL_FILES))

        handler_levels: list[int] = [
            main_level,
            console_level
        ]
        handler_levels.extend(self._resolve_level(_level, logging.DEBUG) for _level in level_files)
        self.setLevel(min(handler_levels))
        self.propagate = False
        self.disabled = False

        if bool(config.get("console", True)):
            console_handler: logging.StreamHandler = logging.StreamHandler(stream=sys.stdout)
            console_handler.setLevel(console_level)
            console_handler.setFormatter(console_formatter)
            self.addHandler(console_handler)

        main_handler: logging.Handler = self._build_file_handler(active_dir / f"{self.name}.log", backup_dir, config)
        main_handler.setLevel(main_level)
        main_handler.setFormatter(file_formatter)
        self.addHandler(main_handler)

        for level_name in level_files:
            level_no: int = self._resolve_level(level_name, logging.DEBUG)
            level_handler: logging.Handler = self._build_file_handler(active_dir / f"{self.name}.{level_name.lower()}.log", backup_dir, config)
            level_handler.setLevel(level_no)
            level_handler.addFilter(_ExactLevelFilter(level_no))
            level_handler.setFormatter(file_formatter)
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

    def _build_file_handler(
        self,
        filename: Path,
        backup_dir: Path,
        config: Mapping[str, Any],
    ) -> logging.Handler:
        at_time: time | None = self._parse_at_time(config.get("at_time"))

        kwargs: dict[str, Any] = {
            "when": str(config.get("when", "midnight")),
            "interval": int(config.get("interval", 1)),
            "backupCount": int(config.get("backup_count", 14)),
            "encoding": str(config.get("encoding", "utf-8")),
            "delay": bool(config.get("delay", True)),
            "utc": bool(config.get("utc", False))
        }

        if at_time is not None:
            kwargs["atTime"] = at_time

        if self._multiprocessing_mode:
            handler_class = _load_backup_concurrent_handler_class()
            if handler_class is None:
                raise RuntimeError("concurrent-log-handler is required when multiprocessing_mode=True.")

            kwargs["maxBytes"] = int(config.get("max_bytes", 0))
            kwargs["use_gzip"] = bool(config.get("use_gzip", False))

            lock_file_directory: str | None = config.get("lock_file_directory")
            if lock_file_directory:
                kwargs["lock_file_directory"] = lock_file_directory

            return handler_class(
                filename=filename,
                backup_dir=backup_dir,
                **kwargs,
            )

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


def get_ns_logger(
    name: str,
    multiprocessing_mode: bool = False,
    sanitizer: Sanitizer | None = None,
    config: Mapping[str, object] | None = None,
    log_dir: str | os.PathLike[str] | None = None,
) -> NsLogger:
    return NsLogger(
        name=name,
        multiprocessing_mode=multiprocessing_mode,
        sanitizer=sanitizer,
        config=config,
        log_dir=log_dir,
    )


def close_ns_loggers() -> None:
    with _LOGGER_LOCK:
        for logger in _LOGGER_MAP.values():
            logger.close()
