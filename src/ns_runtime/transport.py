# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import (
    Any,
    TYPE_CHECKING
)

from ns_common.exceptions import NsRuntimeEnvelopeSchemaError
from ns_common.logger import get_ns_logger
from ns_runtime.handshake import RuntimeHandshakeService
from ns_runtime.outbound import RuntimeConnectionWriterRegistry
from ns_runtime.session import RuntimeSessionRegistry

if TYPE_CHECKING:
    from ns_runtime.service import RuntimeService


@dataclass(slots=True, kw_only=True)
class RuntimeWebSocketTransportConfig:
    host: str = "0.0.0.0"
    port: int = 8765
    handshake_timeout_seconds: float = 10.0
    max_frame_bytes: int = 1024 * 1024
    read_queue_high_water: int = 16
    write_limit_bytes: int = 32768
    ping_interval_seconds: float = 20.0
    ping_timeout_seconds: float = 20.0
    close_timeout_seconds: float = 10.0
    allowed_origins: tuple[str | None, ...] = (None,)


class RuntimeWebSocketTransport:
    def __init__(self, *, service: "RuntimeService", handshake_service: RuntimeHandshakeService, session_registry: RuntimeSessionRegistry, writer_registry: RuntimeConnectionWriterRegistry, config: RuntimeWebSocketTransportConfig) -> None:
        self._service = service
        self._handshake_service = handshake_service
        self._session_registry = session_registry
        self._writer_registry = writer_registry
        self._config = config
        self._logger = get_ns_logger("ns_runtime.transport", True)

    async def serve_forever(self) -> None:
        try:
            from websockets.asyncio.server import serve
        except ImportError as exc:
            raise RuntimeError("Missing runtime WebSocket dependency. Install websockets>=16.0,<17.0.") from exc

        self._logger.info(
            "runtime websocket transport starting",
            extra={
                "host": self._config.host,
                "port": self._config.port,
                "max_frame_bytes": self._config.max_frame_bytes,
                "read_queue_high_water": self._config.read_queue_high_water,
            },
        )

        async with serve(
                self.handle_connection,
                self._config.host,
                self._config.port,
                origins=list(self._config.allowed_origins),
                compression=None,
                max_size=self._config.max_frame_bytes,
                max_queue=self._config.read_queue_high_water,
                write_limit=self._config.write_limit_bytes,
                ping_interval=self._config.ping_interval_seconds,
                ping_timeout=self._config.ping_timeout_seconds,
                close_timeout=self._config.close_timeout_seconds,
                server_header=None,
        ):
            await asyncio.Future()

    async def handle_connection(self, websocket: Any) -> None:
        record = self._session_registry.create_handshaking(remote_address=self._get_remote_address(websocket))

        try:
            first_frame = await asyncio.wait_for(
                websocket.recv(),
                timeout=self._config.handshake_timeout_seconds,
            )

            if not isinstance(first_frame, str):
                raise NsRuntimeEnvelopeSchemaError("First runtime WebSocket frame must be a JSON text frame.")

            outcome = await self._handshake_service.accept(
                frame_text=first_frame,
                record=record,
                remote_address=record.remote_address,
            )
            await self._send_envelope(websocket, outcome.envelope)

            if not outcome.accepted or outcome.session is None:
                await websocket.close(code=outcome.close_code, reason=outcome.close_reason[:120])
                return

            self._writer_registry.register(
                connection_id=record.connection_id,
                connection_epoch=record.connection_epoch,
                websocket=websocket,
            )

            async for frame in websocket:
                if not isinstance(frame, str):
                    response = self._service.build_protocol_error_response(
                        NsRuntimeEnvelopeSchemaError("Runtime WebSocket protocol only accepts JSON text frames."),
                        outcome.session,
                    )
                else:
                    response = await self._service.process_frame(frame, outcome.session)

                if response.envelope is not None:
                    await self._send_envelope(websocket, response.envelope)

                if response.should_close:
                    await websocket.close(code=1002, reason="runtime protocol error")
                    break
        except asyncio.TimeoutError:
            self._session_registry.reject(record, state="timeout_closed", reason="connection.hello timeout")
            await websocket.close(code=1008, reason="connection.hello timeout")
        except Exception as exc:  # noqa
            self._logger.warning(
                "runtime websocket connection failed",
                exc_info=True,
                extra={
                    "connection_id": record.connection_id,
                    "state": record.state,
                    "remote_address": record.remote_address,
                    "exception_class": exc.__class__.__name__,
                },
            )
            try:
                await websocket.close(code=1011, reason="runtime transport error")
            except Exception:  # noqa
                pass
        finally:
            self._writer_registry.unregister(
                connection_id=record.connection_id,
                connection_epoch=record.connection_epoch,
            )
            self._session_registry.close(record, reason="websocket handler exited")

    @staticmethod
    async def _send_envelope(websocket: Any, envelope: dict[str, Any]) -> None:
        await websocket.send(
            json.dumps(
                envelope,
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )

    @staticmethod
    def _get_remote_address(websocket: Any) -> str:
        remote_address = getattr(websocket, "remote_address", None)
        if remote_address is None:
            return "unknown"

        return str(remote_address)
