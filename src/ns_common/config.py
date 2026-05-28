# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, asdict, field
from pathlib import Path
from threading import RLock
from typing import Any, ClassVar, Dict

import portalocker

from . import NS_CONFIG_FILE_PATH, TMP_DIR


@dataclass(slots=True, kw_only=True)
class _NsBackendConfig:
    debug: bool = True


@dataclass(slots=True, kw_only=True)
class _NsRuntimeConfig:
    pass


@dataclass(slots=True, kw_only=True)
class _NsExecutorConfig:
    pass


@dataclass(slots=True, kw_only=True)
class NsConfig:
    backend_config: _NsBackendConfig = field(default_factory=_NsBackendConfig)
    _lock: ClassVar[RLock] = RLock()

    @classmethod
    def load(cls, config_path: Path = NS_CONFIG_FILE_PATH) -> "NsConfig":
        with cls._lock:
            with cls._file_lock(config_path):
                raw_config: dict[str, Any] = cls._load_json_config(config_path)

                backend_config_raw: Any = raw_config.get("backend_config", {})
                if not isinstance(backend_config_raw, dict):
                    raise ValueError("backend_config must be a JSON object")

                config: NsConfig = cls(
                    backend_config=_NsBackendConfig(**backend_config_raw),
                )
                config._validate()
                return config

    def save(self, config_path: Path = NS_CONFIG_FILE_PATH) -> None:
        with self.__class__._lock:
            with self.__class__._file_lock(config_path):
                self._validate()
                self.__class__._atomic_write_json(config_path, asdict(self))

    def _validate(self) -> None:
        pass

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
        temp_io_config: Dict[str, Any] = {
            "mode": "w",
            "encoding": "utf-8",
            "delete": False,
            "dir": TMP_DIR,
            "prefix": "ns_config_",
            "suffix": ".json.tmp"
        }
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
