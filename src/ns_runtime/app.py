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
from ns_runtime.protocol import (
    JsonRuntimeCodec,
    RuntimeEnvelope,
    RuntimeResult,
    validate_envelope,
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

    def build_default_codec(self) -> JsonRuntimeCodec:
        return JsonRuntimeCodec(
            max_message_size_bytes=self.config.runtime.server.websocket.max_message_size_bytes,
        )

    def validate_message(self, envelope: RuntimeEnvelope) -> None:
        validate_envelope(
            envelope,
            max_message_size_bytes=self.config.runtime.server.websocket.max_message_size_bytes,
        )

    @staticmethod
    def make_success_result(data: object | None = None) -> RuntimeResult:
        return RuntimeResult.ok(data=data)

    @staticmethod
    def make_error_result(error: Exception) -> RuntimeResult:
        return RuntimeResult.from_exception(error)
