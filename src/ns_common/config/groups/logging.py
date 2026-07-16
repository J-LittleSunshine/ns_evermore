# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from ..metadata import NsConfigGroupMetadata
from ..primitives import _freeze_config_value


@dataclass(frozen=True, slots=True, kw_only=True)
class NsLogConfig:
    level: str = "INFO"
    file_level: str = "INFO"
    console_level: str = "INFO"
    console: bool = True

    format_type: Literal["json", "text", "color_text"] = "json"
    console_format_type: Literal["json", "text", "color_text"] | None = "color_text"
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
    metadata: NsConfigGroupMetadata = field(default_factory=NsConfigGroupMetadata)

    def __post_init__(self) -> None:
        object.__setattr__(self, "level_files", _freeze_config_value(self.level_files))
