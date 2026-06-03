# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, asdict, field
from pathlib import Path
from threading import RLock
from typing import Any, ClassVar, Dict, Literal

import portalocker

from ns_common import NS_CONFIG_FILE_PATH, TMP_DIR, NS_ENV


@dataclass(slots=True, kw_only=True)
class _NsCacheConfig:
    """Unified cache configuration loaded through ns_config."""

    backend: Literal["default", "sql_wal", "redis", "valkey"] = "default"
    location: str = ""
    key_prefix: str = "ns"
    default_timeout_seconds: int | None = 300
    serializer: Literal["pickle", "json", "raw"] = "pickle"

    sql_table: str = "ns_cache"
    sql_timeout_seconds: float = 5.0
    sql_max_entries: int = 10000
    sql_cull_frequency: int = 3

    socket_timeout: float = 3.0
    socket_connect_timeout: float = 3.0
    max_connections: int = 64
    health_check_interval: int = 30

    def resolved_backend(self) -> Literal["sql_wal", "redis", "valkey"]:
        """Resolve default backend to sql_wal without probing external services."""
        if self.backend in {"default", "sql_wal"}:
            return "sql_wal"
        return self.backend

@dataclass(slots=True, kw_only=True)
class _NsLogConfig:
    level: str = "DEBUG"
    file_level: str = "DEBUG"
    console_level: str = "DEBUG"
    console: bool = True
    format: str = "%(asctime)s - %(levelname)-8s - %(process)d:%(threadName)s - %(name)s - %(filename)s:%(lineno)d - %(message)s"
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
    level_files: tuple[str, ...] = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


@dataclass(slots=True, kw_only=True)
class _NsBackendConfig:
    debug: bool = True
    secret_key: str = "default_secret_key"
    jwt_secret_key: str = "default_jwt_secret_key"
    allowed_hosts: list[str] = field(default_factory=lambda: ["127.0.0.1", "localhost"])
    loaded_apps: dict[str, bool] = field(default_factory=dict)
    databases: dict[str, dict[str, Any]] = field(default_factory=dict)
    infra_db_router_map: dict[str, str] = field(default_factory=dict)
    database_router_map: dict[str, str] = field(default_factory=dict)
    language_code: str = "zh-hans"
    time_zone: str = "Asia/Shanghai"
    use_i18n: bool = True
    use_tz: bool = True
    static_url: str = "static/"

    # JWT / auth settings aligned with backup backend.
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14
    jwt_issuer: str = "ns_evermore"
    jwt_leeway_seconds: int = 30
    jwt_min_secret_length: int = 32

    # Password transport settings aligned with backup backend.
    password_transport_mode: str = "plain"
    password_transport_max_payload_length: int = 4096
    password_plaintext_max_length: int = 256
    password_rsa_private_key: str = ""
    password_rsa_private_key_file: str = ""
    password_rsa_private_key_passphrase: str = ""

    # Login lock settings aligned with backup backend.
    login_max_failed_count: int = 5
    login_lock_minutes: int = 15

    # Audit and proxy settings aligned with backup backend.
    extra_sensitive_keys: list[str] = field(default_factory=list)
    audit_extra_sensitive_keys: list[str] = field(default_factory=list)
    iam_decision_audit_strict_mode: bool = False
    trust_x_forwarded_for: bool = False

    # Permission provider settings aligned with backup backend.
    iam_permission_providers: list[str] = field(default_factory=list)
    iam_module_registration_hooks: list[str] = field(default_factory=list)

    # Authorization-context cache settings.
    iam_auth_context_cache_alias: str = "default"
    iam_auth_context_ttl_seconds: int = 300
    iam_auth_context_redis_url: str = ""

    # Authorization fallback resilience settings.
    iam_auth_backoff_enabled: bool = True
    iam_auth_backoff_max_retries: int = 3
    iam_auth_backoff_base_delay_ms: int = 50
    iam_auth_backoff_max_delay_ms: int = 1000
    iam_auth_backoff_jitter_ratio: float = 0.5
    iam_auth_local_fallback_cache_enabled: bool = True
    iam_auth_local_fallback_cache_ttl_seconds: int = 3
    iam_auth_local_fallback_cache_max_size: int = 1024
    iam_auth_single_flight_enabled: bool = True


@dataclass(slots=True, kw_only=True)
class _NsRuntimeConfig:
    pass


@dataclass(slots=True, kw_only=True)
class _NsExecutorConfig:
    pass


@dataclass(slots=True, kw_only=True)
class NsConfig:
    backend_config: _NsBackendConfig = field(default_factory=_NsBackendConfig)
    cache_config: _NsCacheConfig = field(default_factory=_NsCacheConfig)
    log_config: _NsLogConfig = field(default_factory=_NsLogConfig)
    _lock: ClassVar[RLock] = RLock()

    @classmethod
    def load(cls, config_path: Path = NS_CONFIG_FILE_PATH) -> "NsConfig":
        with cls._lock:
            with cls._file_lock(config_path):
                raw_config: dict[str, Any] = cls._load_json_config(config_path)

                backend_config_raw: Any = raw_config.get("backend_config")
                if backend_config_raw is None:
                    backend_config_raw = raw_config.get("backend", {})
                if not isinstance(backend_config_raw, dict):
                    raise ValueError("backend_config/backend must be a JSON object")

                log_config_raw: Any = raw_config.get("log_config", {})
                if not isinstance(log_config_raw, dict):
                    raise ValueError("log_config must be a JSON object")

                normalized_backend_config = cls._normalize_backend_config(dict(backend_config_raw))
                config: NsConfig = cls(backend_config=_NsBackendConfig(**normalized_backend_config), log_config=_NsLogConfig(**log_config_raw))
                config._validate()
                return config

    def save(self, config_path: Path = NS_CONFIG_FILE_PATH) -> None:
        with self.__class__._lock:
            with self.__class__._file_lock(config_path):
                self._validate()
                self.__class__._atomic_write_json(config_path, asdict(self))

    def _validate(self) -> None:
        if self.backend_config.secret_key == "default_secret_key":
            if NS_ENV == "prod":
                raise RuntimeError("The system detected that the current environment is a production environment, but the backend secret key is not set. For security reasons, please set the secret key first.")
            if NS_ENV == "test":
                print("Warning: The system detected that the current environment is a test environment, but the backend secret key is not set. For security reasons, it is recommended to set a unique secret key for testing.")

        if self.backend_config.jwt_secret_key == "default_jwt_secret_key":
            if NS_ENV == "prod":
                raise RuntimeError("The system detected that the current environment is a production environment, but the JWT secret key is not set. For security reasons, please set the JWT secret key first.")
            if NS_ENV == "test":
                print("Warning: The system detected that the current environment is a test environment, but the JWT secret key is not set. For security reasons, it is recommended to set a unique JWT secret key for testing.")

        if self.backend_config.debug and NS_ENV == "prod":
            raise RuntimeError("DEBUG must be False when NS_ENV is prod.")

        allowed_hosts = self.backend_config.allowed_hosts
        if len(allowed_hosts) == 1 and allowed_hosts[0] == "*":
            if NS_ENV not in {"dev", "local"}:
                print("Warning: The system detected that the current environment is not a development or local environment, but the allowed hosts are set to '*'. For security reasons, it is recommended to set the allowed hosts to specific domain names or IP addresses for testing or production.")

    @classmethod
    def _normalize_backend_config(cls, raw_config: dict[str, Any]) -> dict[str, Any]:
        """Normalize backup-compatible config keys before dataclass construction."""
        alias_map: dict[str, str] = {
            "log_in_max_failed_count": "login_max_failed_count",
            "log_in_lock_minutes": "login_lock_minutes",
        }

        for old_key, new_key in alias_map.items():
            if old_key in raw_config and new_key not in raw_config:
                raw_config[new_key] = raw_config[old_key]
            raw_config.pop(old_key, None)

        return raw_config

    @classmethod
    def _file_lock(cls, config_path: Path) -> portalocker.Lock:
        lock_path: Path = config_path.with_suffix(config_path.suffix + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        return portalocker.Lock(str(lock_path), mode="a", timeout=10)

    @classmethod
    def _load_json_config(cls, config_path: Path) -> dict[str, Any]:
        if not config_path.exists():
            return {}

        try:
            with open(config_path, "r", encoding="utf-8") as _file:
                raw_config: Any = json.load(_file)
        except json.JSONDecodeError as _error:
            raise ValueError(f"Invalid JSON config file: {config_path}") from _error

        if not isinstance(raw_config, dict):
            raise ValueError("Config root must be a JSON object")

        return raw_config

    @classmethod
    def _atomic_write_json(cls, config_path: Path, _data: dict[str, Any]) -> None:
        config_path.parent.mkdir(parents=True, exist_ok=True)

        temp_file_path: Path | None = None
        temp_io_config: Dict[str, Any] = {"mode": "w", "encoding": "utf-8", "delete": False, "dir": TMP_DIR, "prefix": "ns_config_", "suffix": ".json.tmp"}
        try:
            with tempfile.NamedTemporaryFile(**temp_io_config) as _file:
                temp_file_path = Path(_file.name)
                json.dump(_data, _file, ensure_ascii=False, indent=4)
                _file.flush()
                os.fsync(_file.fileno())

            os.replace(temp_file_path, config_path)

        finally:
            if temp_file_path is not None and temp_file_path.exists():
                temp_file_path.unlink()


ns_config: NsConfig = NsConfig.load()
