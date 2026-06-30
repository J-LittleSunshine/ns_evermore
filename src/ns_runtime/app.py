# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)
from typing import TYPE_CHECKING

from ns_common.config import NsConfig
from ns_common.exceptions import NsStateError
from ns_common.runtime_config import (
    RuntimeMode,
    validate_runtime_config,
)

if TYPE_CHECKING:
    pass


@dataclass(slots=True, kw_only=True)
class RuntimeApplication:
    config: NsConfig
    mode: RuntimeMode | None = None

    _started: bool = field(default=False, init=False)

    @property
    def effective_mode(self) -> RuntimeMode:
        return self.mode or self.config.runtime.mode

    async def start(self) -> None:
        if self._started:
            raise NsStateError(
                "ns_runtime application is already started.",
                details={
                    "runtime_id": self.config.runtime.runtime_id,
                    "mode": self.effective_mode,
                },
            )

        self.config.runtime.mode = self.effective_mode
        validate_runtime_config(self.config.runtime)

        self._started = True

    async def stop(self) -> None:
        if not self._started:
            return

        self._started = False

    async def run_once_for_bootstrap_check(self) -> None:
        await self.start()
        await self.stop()
