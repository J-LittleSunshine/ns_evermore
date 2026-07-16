# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import types
from dataclasses import dataclass
from enum import Enum
from typing import Literal, Mapping

from ..exceptions import NsConfigError


_CONFIG_VERSION_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}")


class NsConfigSource(str, Enum):
    LOCAL_FILE = "local_file"
    BACKEND_OVERRIDE = "backend_override"
    VALIDATED_SNAPSHOT = "validated_snapshot"


NS_CONFIG_SOURCE_PRIORITY: Mapping[NsConfigSource, int] = types.MappingProxyType({
    NsConfigSource.LOCAL_FILE: 10,
    NsConfigSource.BACKEND_OVERRIDE: 20,
    NsConfigSource.VALIDATED_SNAPSHOT: 30,
})


RUNTIME_CONFIG_APPLY_MODES: Mapping[str, str] = types.MappingProxyType({
    "event_loop": "restart_required",
    "transport": "restart_required",
    "wire_codec": "restart_required",
    "protocol": "rolling",
    "security": "restart_required",
    "iam": "rolling",
    "state_store": "restart_required",
    "routing": "immediate",
    "delivery": "rolling",
    "worker": "rolling",
    "pool": "rolling",
    "tenant_quota": "immediate",
    "cluster": "restart_required",
    "recovery": "rolling",
    "observability": "immediate",
    "logging": "immediate",
    "debug": "immediate",
})


@dataclass(frozen=True, slots=True, kw_only=True)
class NsConfigGroupMetadata:
    source: NsConfigSource = NsConfigSource.LOCAL_FILE
    config_version: str = "0"
    policy_version: str = "0"
    group_version: str = "0"
    effective_at: str | None = None
    rollback_from_version: str | None = None
    apply_mode: Literal["immediate", "rolling", "restart_required"] = "restart_required"

    def __post_init__(self) -> None:
        if isinstance(self.source, NsConfigSource):
            return

        try:
            source = NsConfigSource(self.source)
        except (TypeError, ValueError) as error:
            raise NsConfigError(
                "config metadata source is invalid.",
                details={
                    "field": "metadata.source",
                    "value": self.source,
                    "allowed_values": [item.value for item in NsConfigSource],
                },
            ) from error

        object.__setattr__(self, "source", source)
