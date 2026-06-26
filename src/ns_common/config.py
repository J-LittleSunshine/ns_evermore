# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from dataclasses import (
    asdict,
    dataclass,
    field
)
from pathlib import Path
from threading import RLock
from typing import (
    Any,
    Literal,
    TYPE_CHECKING
)

from ns_common.exceptions import NsConfigError
from ns_common.paths import (
    ETC_DIR,
    TMP_DIR,
    ensure_runtime_dirs
)

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
    database_router_map: dict[str, str] = field(default_factory=dict)

    jwt_secret_key: str = ""
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14
    jwt_issuer: str = "ns_evermore"
    jwt_leeway_seconds: int = 30
    jwt_min_secret_length: int = 32

    password_transport_mode: Literal["plain", "rsa_oaep"] = "plain"
    password_transport_max_payload_length: int = 4096
    password_plaintext_max_length: int = 256
    password_rsa_private_key: str = ""
    password_rsa_private_key_file: str = ""
    password_rsa_private_key_passphrase: str = ""
    iam_internal_token: str = "change-me-iam-internal-token-at-least-32-chars"
    iam_decision_audit_enabled: bool = True
    iam_decision_audit_strict_mode: bool = False


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

            backend_raw = cls._get_section(raw_config, preferred_key="backend", compatible_key="backend_config")
            log_raw = cls._get_section(raw_config, preferred_key="log", compatible_key="log_config")

            config = cls(backend=NsBackendConfig(**backend_raw), log=NsLogConfig(**log_raw))
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
            raise NsConfigError("backend.debug must be False when NS_ENV is prod.",
                details={
                    "field": "backend.debug",
                    "env": NS_ENV,
                },
            )

        if not self.backend.secret_key.strip():
            raise NsConfigError("backend.secret_key must not be empty.",
                details={
                    "field": "backend.secret_key",
                },
            )

        if NS_ENV == "prod" and self.backend.secret_key.startswith("change-me-"):
            raise NsConfigError("backend.secret_key must be changed in prod.",
                details={
                    "field": "backend.secret_key",
                    "env": NS_ENV,
                },
            )

        if not isinstance(self.backend.allowed_hosts, list):
            raise NsConfigError("backend.allowed_hosts must be a list.",
                details={
                    "field": "backend.allowed_hosts",
                    "actual_type": type(self.backend.allowed_hosts).__name__,
                },
            )

        if not isinstance(self.backend.databases, dict):
            raise NsConfigError("backend.databases must be a dict.",
                details={
                    "field": "backend.databases",
                    "actual_type": type(self.backend.databases).__name__,
                },
            )

        if not isinstance(self.backend.database_router_map, dict):
            raise NsConfigError("backend.database_router_map must be a dict.",
                details={
                    "field": "backend.database_router_map",
                    "actual_type": type(self.backend.database_router_map).__name__,
                },
            )

        for app_label, db_alias in self.backend.database_router_map.items():
            if not isinstance(app_label, str) or not app_label.strip():
                raise NsConfigError("backend.database_router_map app label must be a non-empty string.",
                    details={
                        "field": "backend.database_router_map",
                        "app_label": app_label,
                    },
                )

            if not isinstance(db_alias, str) or not db_alias.strip():
                raise NsConfigError("backend.database_router_map database alias must be a non-empty string.",
                    details={
                        "field": "backend.database_router_map",
                        "app_label": app_label,
                        "db_alias": db_alias,
                    },
                )

        self._validate_positive_int("backend.access_token_expire_minutes", self.backend.access_token_expire_minutes, )
        self._validate_positive_int("backend.refresh_token_expire_days", self.backend.refresh_token_expire_days, )
        self._validate_positive_int("backend.jwt_leeway_seconds", self.backend.jwt_leeway_seconds, )
        self._validate_positive_int("backend.jwt_min_secret_length", self.backend.jwt_min_secret_length, )
        self._validate_positive_int("backend.password_transport_max_payload_length", self.backend.password_transport_max_payload_length, )
        self._validate_positive_int("backend.password_plaintext_max_length", self.backend.password_plaintext_max_length, )

        if self.backend.password_transport_mode not in {"plain", "rsa_oaep"}:
            raise NsConfigError("backend.password_transport_mode is invalid.",
                details={
                    "field": "backend.password_transport_mode",
                    "value": self.backend.password_transport_mode,
                    "allowed_values": [
                        "plain",
                        "rsa_oaep",
                    ],
                },
            )

    @staticmethod
    def _validate_positive_int(field_name: str, value: Any) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise NsConfigError(f"{field_name} must be a positive integer.",
                details={
                    "field": field_name,
                    "value": value,
                    "actual_type": type(value).__name__,
                },
            )

    @staticmethod
    def _get_section(raw_config: dict[str, Any], *, preferred_key: str, compatible_key: str) -> dict[str, Any]:
        section = raw_config.get(preferred_key)

        if section is None:
            section = raw_config.get(compatible_key, {})

        if not isinstance(section, dict):
            raise NsConfigError(f"{preferred_key}/{compatible_key} must be a JSON object.",
                details={
                    "preferred_key": preferred_key,
                    "compatible_key": compatible_key,
                    "actual_type": type(section).__name__,
                },
            )

        return section

    @staticmethod
    def _load_json_config(config_path: Path) -> dict[str, Any]:
        if not config_path.exists():
            return {}

        try:
            with config_path.open("r", encoding="utf-8") as file:
                raw_config = json.load(file)
        except json.JSONDecodeError as error:
            raise NsConfigError(f"Invalid JSON config file: {config_path}",
                details={
                    "config_path": str(config_path),
                    "line": error.lineno,
                    "column": error.colno,
                },
            ) from error

        if not isinstance(raw_config, dict):
            raise NsConfigError(f"Config root must be a JSON object: {config_path}",
                details={
                    "config_path": str(config_path),
                    "actual_type": type(raw_config).__name__,
                },
            )

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
