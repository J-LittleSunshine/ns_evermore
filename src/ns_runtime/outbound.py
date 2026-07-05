# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import (
    Any,
    TYPE_CHECKING
)

from ns_common.exceptions import NsRuntimeTargetUnavailableError
from ns_runtime.models import Envelope
from ns_runtime.routing import (
    RuntimeRouteDecision,
    RuntimeRouteTarget
)

if TYPE_CHECKING:
    pass


@dataclass(slots=True, kw_only=True)
class RuntimeLocalWriteResult:
    connection_id: str
    connection_epoch: int
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "connection_id": self.connection_id,
            "connection_epoch": self.connection_epoch,
            "status": self.status,
        }


@dataclass(slots=True, kw_only=True)
class RuntimeConnectionWriter:
    connection_id: str
    connection_epoch: int
    websocket: Any
    write_lock: asyncio.Lock

    async def send_envelope(self, envelope: dict[str, Any]) -> RuntimeLocalWriteResult:
        await self._send_json(envelope)
        return RuntimeLocalWriteResult(
            connection_id=self.connection_id,
            connection_epoch=self.connection_epoch,
            status="sent",
        )

    async def _send_json(self, envelope: dict[str, Any]) -> None:
        async with self.write_lock:
            await self.websocket.send(
                json.dumps(
                    envelope,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )


class RuntimeConnectionWriterRegistry:
    def __init__(self) -> None:
        self._writers: dict[str, RuntimeConnectionWriter] = {}

    def register(self, *, connection_id: str, connection_epoch: int, websocket: Any) -> None:
        self._writers[connection_id] = RuntimeConnectionWriter(
            connection_id=connection_id,
            connection_epoch=connection_epoch,
            websocket=websocket,
            write_lock=asyncio.Lock(),
        )

    def unregister(self, *, connection_id: str, connection_epoch: int) -> None:
        writer = self._writers.get(connection_id)
        if writer is None:
            return

        if writer.connection_epoch != connection_epoch:
            return

        self._writers.pop(connection_id, None)

    def get(self, connection_id: str) -> RuntimeConnectionWriter | None:
        return self._writers.get(connection_id)

    def list_connection_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._writers.keys()))

    async def send_to_connection(self, *, connection_id: str, connection_epoch: int, envelope: dict[str, Any]) -> RuntimeLocalWriteResult:
        writer = self._writers.get(connection_id)
        if writer is None:
            raise NsRuntimeTargetUnavailableError(
                "Runtime target writer is unavailable.",
                details={
                    "connection_id": connection_id,
                    "connection_epoch": connection_epoch,
                },
            )

        if writer.connection_epoch != connection_epoch:
            raise NsRuntimeTargetUnavailableError(
                "Runtime target writer epoch is stale.",
                details={
                    "connection_id": connection_id,
                    "expected_epoch": connection_epoch,
                    "actual_epoch": writer.connection_epoch,
                },
            )

        return await writer.send_envelope(envelope)


class RuntimeLocalEnvelopeForwarder:
    def __init__(self, *, writer_registry: RuntimeConnectionWriterRegistry) -> None:
        self._writer_registry = writer_registry

    async def forward(self, *, decision: RuntimeRouteDecision, envelope: Envelope) -> tuple[RuntimeLocalWriteResult, ...]:
        writable_targets = tuple(
            target
            for target in decision.targets
            if target.connection_id != "runtime"
        )

        if not writable_targets:
            raise NsRuntimeTargetUnavailableError(
                "Runtime route decision does not contain writable local connection targets.",
                details={
                    "message_id": decision.message_id,
                    "message_type": decision.message_type,
                    "target_kind": decision.target_kind,
                },
            )

        results: list[RuntimeLocalWriteResult] = []
        envelope_data = envelope.to_dict()

        for target in writable_targets:
            results.append(
                await self._send_to_target(
                    target=target,
                    envelope_data=envelope_data,
                )
            )

        return tuple(results)

    async def _send_to_target(self, *, target: RuntimeRouteTarget, envelope_data: dict[str, Any]) -> RuntimeLocalWriteResult:
        return await self._writer_registry.send_to_connection(
            connection_id=target.connection_id,
            connection_epoch=target.connection_epoch,
            envelope=envelope_data,
        )
