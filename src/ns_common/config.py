# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from threading import RLock
from typing import Any, Literal, TYPE_CHECKING

from ns_common.paths import ETC_DIR, TMP_DIR, ensure_runtime_dirs

if TYPE_CHECKING:
    pass

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


def get_default_config_path() -> Path:
    return ETC_DIR / f"ns_config.{NS_ENV}.json"


NS_CONFIG_FILE_PATH = get_default_config_path()


@dataclass(slots=True, kw_only=True)
class NsBackendConfig:
    debug: bool = True
    secret_key: str = "change-me-secret-key-at-least-32-chars"
    allowed_hosts: list[str] = field(
        default_factory=lambda: [
            "127.0.0.1",
            "localhost",
        ]
    )

    language_code: str = "zh-hans"
    time_zone: str = "Asia/Shanghai"
    use_i18n: bool = True
    use_tz: bool = True
    static_url: str = "static/"

    databases: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass(slots=True, kw_only=True)
class NsLogConfig:
    level: str = "INFO"
    file_level: str = "INFO"
    console_level: str = "INFO"
    console: bool = True

    format_type: Literal["json", "text"] = "json"
    console_format_type: Literal["json", "text"] | None = "text"
    file_format_type: Literal["json", "text"] | None = "json"

    format: str = (
        "%(asctime)s - %(levelname)-8s - %(process)d:%(threadName)s - "
        "%(name)s - %(filename)s:%(lineno)d - %(message)s"
    )
    datefmt: str = "%Y-%m-%d %H:%M:%S"

    when: str = "midnight"
    interval: int = 1
    backup_count: int = 14
    encoding: str = "utf-8"
    delay: bool = True
    utc: bool = False
    at_time: str | None = None
    max_bytes: int = 0
    use_gzip: bool = False
    lock_file_directory: str | None = None

    level_files: tuple[str, ...] = (
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    )


@dataclass(slots=True, kw_only=True)
class NsConfig:
    backend: NsBackendConfig = field(default_factory=NsBackendConfig)
    log: NsLogConfig = field(default_factory=NsLogConfig)

    _lock = RLock()

    @classmethod
    def load(cls, config_path: str | Path | None = None) -> "NsConfig":
        ensure_runtime_dirs()

        path = Path(config_path).resolve() if config_path else NS_CONFIG_FILE_PATH

        with cls._lock:
            raw_config = cls._load_json_config(path)

            backend_raw = cls._get_section(
                raw_config,
                preferred_key="backend",
                compatible_key="backend_config",
            )
            log_raw = cls._get_section(
                raw_config,
                preferred_key="log",
                compatible_key="log_config",
            )

            config = cls(
                backend=NsBackendConfig(**backend_raw),
                log=NsLogConfig(**log_raw),
            )
            config.validate()
            return config

    def save(self, config_path: str | Path | None = None) -> None:
        ensure_runtime_dirs()

        path = Path(config_path).resolve() if config_path else NS_CONFIG_FILE_PATH

        with self.__class__._lock:
            self.validate()
            self.__class__._atomic_write_json(path, asdict(self))

    def validate(self) -> None:
        if self.backend.debug and NS_ENV == "prod":
            raise RuntimeError("backend.debug must be False when NS_ENV is prod.")

        if not self.backend.secret_key.strip():
            raise RuntimeError("backend.secret_key must not be empty.")

        if NS_ENV == "prod" and self.backend.secret_key.startswith("change-me-"):
            raise RuntimeError("backend.secret_key must be changed in prod.")

        if not isinstance(self.backend.allowed_hosts, list):
            raise TypeError("backend.allowed_hosts must be a list.")

    @staticmethod
    def _get_section(raw_config: dict[str, Any], *, preferred_key: str, compatible_key: str) -> dict[str, Any]:
        """
        Read config section with backup-compatible key support.

        新配置推荐:
        {
          "backend": {}
        }

        兼容旧配置:
        {
          "backend_config": {}
        }
        """
        section = raw_config.get(preferred_key)

        if section is None:
            section = raw_config.get(compatible_key, {})

        if not isinstance(section, dict):
            raise ValueError(f"{preferred_key}/{compatible_key} must be a JSON object.")

        return section

    @staticmethod
    def _load_json_config(config_path: Path) -> dict[str, Any]:
        """
        Load raw JSON config.

        配置文件不存在时返回空配置，使用 dataclass 默认值。
        """
        if not config_path.exists():
            return {}

        try:
            with config_path.open("r", encoding="utf-8") as file:
                raw_config = json.load(file)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON config file: {config_path}") from error

        if not isinstance(raw_config, dict):
            raise ValueError(f"Config root must be a JSON object: {config_path}")

        return raw_config

    @staticmethod
    def _atomic_write_json(config_path: Path, data: dict[str, Any]) -> None:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        TMP_DIR.mkdir(parents=True, exist_ok=True)

        temp_path = TMP_DIR / f"{config_path.name}.tmp"

        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())

        os.replace(temp_path, config_path)


ns_config = NsConfig.load()
