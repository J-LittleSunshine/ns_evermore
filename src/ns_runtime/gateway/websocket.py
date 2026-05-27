# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from importlib import import_module
from typing import Any
from uuid import uuid4

from ns_runtime.endpoints import RuntimeEndpoint
from ns_runtime.packets import RuntimeEndpointType, RuntimePacket, RuntimePacketCodec, RuntimePacketType
from ns_runtime.service import RuntimeService


@dataclass(frozen=True)
class WebSocketGatewayConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    path: str = "/runtime"
    max_message_size: int = 1024 * 1024
    close_timeout_seconds: float = 5.0

    def __post_init__(self) -> None:
        host = str(self.host).strip()
        path = str(self.path).strip()

        if not host:
            raise ValueError("host must be non-empty")
        if not (1 <= self.port <= 65535):
            raise ValueError("port must be between 1 and 65535")
        if not path.startswith("/"):
            raise ValueError("path must start with '/'")
        if self.max_message_size <= 0:
            raise ValueError("max_message_size must be > 0")
        if self.close_timeout_seconds <= 0:
            raise ValueError("close_timeout_seconds must be > 0")

        # 这是 standalone runtime gateway 配置，独立于 Django settings，初始化时在 frozen dataclass 内完成归一化。
        object.__setattr__(self, "host", host)
        object.__setattr__(self, "path", path)


@dataclass(frozen=True)
class WebSocketConnection:
    connection_id: str
    endpoint_id: str | None
    websocket: Any
    connected_at: datetime
    last_seen_at: datetime
    remote_address: str | None = None

    def __post_init__(self) -> None:
        connection_id = str(self.connection_id).strip()
        if not connection_id:
            raise ValueError("connection_id must be non-empty")
        object.__setattr__(self, "connection_id", connection_id)

    def bind_endpoint(self, endpoint_id: str) -> WebSocketConnection:
        endpoint_id_text = str(endpoint_id).strip()
        if not endpoint_id_text:
            raise ValueError("endpoint_id must be non-empty")
        return replace(self, endpoint_id=endpoint_id_text)

    def touch(self) -> WebSocketConnection:
        return replace(self, last_seen_at=datetime.now(timezone.utc))


class WebSocketConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, WebSocketConnection] = {}
        self._endpoint_to_connection: dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def register_connection(self, connection: WebSocketConnection) -> WebSocketConnection:
        async with self._lock:
            self._connections[connection.connection_id] = connection
            if connection.endpoint_id:
                self._endpoint_to_connection[connection.endpoint_id] = connection.connection_id
            return connection

    async def bind_endpoint(self, connection_id: str, endpoint_id: str) -> WebSocketConnection:
        connection_id_text = self._validate_non_empty_text("connection_id", connection_id)
        endpoint_id_text = self._validate_non_empty_text("endpoint_id", endpoint_id)

        async with self._lock:
            connection = self._connections.get(connection_id_text)
            if connection is None:
                raise KeyError(f"connection not found: {connection_id_text}")

            previous_connection_id = self._endpoint_to_connection.get(endpoint_id_text)
            if previous_connection_id and previous_connection_id != connection_id_text:
                previous_connection = self._connections.get(previous_connection_id)
                if previous_connection is not None and previous_connection.endpoint_id == endpoint_id_text:
                    self._connections[previous_connection_id] = replace(previous_connection, endpoint_id=None)

            if connection.endpoint_id and self._endpoint_to_connection.get(connection.endpoint_id) == connection_id_text:
                self._endpoint_to_connection.pop(connection.endpoint_id, None)

            bound = connection.bind_endpoint(endpoint_id_text)
            self._connections[connection_id_text] = bound
            self._endpoint_to_connection[endpoint_id_text] = connection_id_text
            return bound

    async def unregister_connection(self, connection_id: str) -> WebSocketConnection | None:
        connection_id_text = self._validate_non_empty_text("connection_id", connection_id)
        async with self._lock:
            removed = self._connections.pop(connection_id_text, None)
            if removed is None:
                return None
            if removed.endpoint_id and self._endpoint_to_connection.get(removed.endpoint_id) == connection_id_text:
                self._endpoint_to_connection.pop(removed.endpoint_id, None)
            return removed

    async def get_by_connection_id(self, connection_id: str) -> WebSocketConnection | None:
        connection_id_text = self._validate_non_empty_text("connection_id", connection_id)
        async with self._lock:
            return self._connections.get(connection_id_text)

    async def get_by_endpoint_id(self, endpoint_id: str) -> WebSocketConnection | None:
        endpoint_id_text = self._validate_non_empty_text("endpoint_id", endpoint_id)
        async with self._lock:
            connection_id = self._endpoint_to_connection.get(endpoint_id_text)
            if connection_id is None:
                return None
            return self._connections.get(connection_id)

    async def touch(self, connection_id: str) -> WebSocketConnection:
        connection_id_text = self._validate_non_empty_text("connection_id", connection_id)
        async with self._lock:
            connection = self._connections.get(connection_id_text)
            if connection is None:
                raise KeyError(f"connection not found: {connection_id_text}")
            updated = connection.touch()
            self._connections[connection_id_text] = updated
            return updated

    async def list_all(self) -> tuple[WebSocketConnection, ...]:
        async with self._lock:
            return tuple(self._connections.values())

    async def send_to_endpoint(self, endpoint_id: str, message: str | bytes) -> bool:
        endpoint_id_text = self._validate_non_empty_text("endpoint_id", endpoint_id)
        async with self._lock:
            connection_id = self._endpoint_to_connection.get(endpoint_id_text)
            if connection_id is None:
                return False
            connection = self._connections.get(connection_id)
            if connection is None:
                self._endpoint_to_connection.pop(endpoint_id_text, None)
                return False

        await connection.websocket.send(message)
        return True

    async def broadcast(self, message: str | bytes) -> int:
        async with self._lock:
            connections = tuple(self._connections.values())

        success_count = 0
        for connection in connections:
            try:
                await connection.websocket.send(message)
                success_count += 1
            except Exception:
                # 广播允许跳过失败连接，避免单个连接异常影响其他在线连接发送。
                continue
        return success_count

    @staticmethod
    def _validate_non_empty_text(field_name: str, value: object) -> str:
        text = str(value).strip()
        if not text:
            raise ValueError(f"{field_name} must be non-empty")
        return text


class WebSocketGateway:
    def __init__(
        self,
        runtime_service: RuntimeService,
        config: WebSocketGatewayConfig | None = None,
        codec: RuntimePacketCodec | None = None,
    ) -> None:
        self.runtime_service = runtime_service
        self.config = config or WebSocketGatewayConfig()
        self.connection_manager = WebSocketConnectionManager()
        self._codec = codec or RuntimePacketCodec()
        self._server: Any | None = None
        self._serve_func: Any | None = None
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    async def start(self) -> None:
        if self._running:
            return

        if not self.runtime_service.is_running:
            self.runtime_service.start()

        if self._serve_func is None:
            try:
                module = import_module("websockets.asyncio.server")
                self._serve_func = getattr(module, "serve")
            except (ImportError, AttributeError) as exc:
                raise RuntimeError("websockets is not installed, please install package 'websockets'") from exc

        self._server = await self._serve_func(
            self._handle_connection,
            self.config.host,
            self.config.port,
            max_size=self.config.max_message_size,
            close_timeout=self.config.close_timeout_seconds,
        )
        self._running = True

    async def stop(self) -> None:
        if not self._running:
            return

        self._running = False
        server = self._server
        self._server = None
        if server is None:
            return

        close_method = getattr(server, "close", None)
        if callable(close_method):
            close_method()

        wait_closed_method = getattr(server, "wait_closed", None)
        if callable(wait_closed_method):
            await wait_closed_method()

    async def send_packet_to_endpoint(self, endpoint_id: str, packet: RuntimePacket) -> bool:
        encoded = self._codec.encode(packet)
        return await self.connection_manager.send_to_endpoint(endpoint_id, encoded)

    async def broadcast_packet(self, packet: RuntimePacket) -> int:
        encoded = self._codec.encode(packet)
        return await self.connection_manager.broadcast(encoded)

    async def _handle_connection(self, websocket: Any) -> None:
        connection_id = uuid4().hex
        now = datetime.now(timezone.utc)
        connection = WebSocketConnection(
            connection_id=connection_id,
            endpoint_id=None,
            websocket=websocket,
            connected_at=now,
            last_seen_at=now,
            remote_address=self._resolve_remote_address(websocket),
        )
        await self.connection_manager.register_connection(connection)

        try:
            async for raw_message in websocket:
                current = await self.connection_manager.touch(connection_id)
                await self._handle_raw_message(current, raw_message)
        finally:
            removed = await self.connection_manager.unregister_connection(connection_id)
            endpoint_id = removed.endpoint_id if removed is not None else None
            if endpoint_id:
                try:
                    self.runtime_service.endpoint_registry.mark_offline(endpoint_id)
                except KeyError:
                    pass

    async def _handle_raw_message(self, connection: WebSocketConnection, raw_message: str | bytes) -> None:
        try:
            packet = self._codec.decode(raw_message)
        except ValueError as exc:
            error_packet = self._build_error_packet(
                error_message=str(exc),
                source_endpoint_id="gateway",
                target_endpoint_id=connection.endpoint_id,
                trace_id=None,
            )
            await self._send_packet(connection.websocket, error_packet)
            return

        if packet.packet_type == RuntimePacketType.REGISTER:
            response = await self._handle_register_packet(connection, packet)
            await self._send_packet(connection.websocket, response)
            return

        if packet.packet_type == RuntimePacketType.HEARTBEAT:
            response = await self._handle_heartbeat_packet(connection, packet)
            await self._send_packet(connection.websocket, response)
            return

        delivered = False
        if packet.target_endpoint_id:
            delivered = await self.send_packet_to_endpoint(packet.target_endpoint_id, packet)
            if delivered:
                ack_packet = self._build_ack_packet(
                    action="forward",
                    source_endpoint_id="gateway",
                    target_endpoint_id=connection.endpoint_id,
                    trace_id=packet.trace_id,
                    extra_payload={
                        "target_endpoint_id": packet.target_endpoint_id,
                    },
                )
                await self._send_packet(connection.websocket, ack_packet)
                return

        routed_packet = self.runtime_service.router.route(packet)
        if routed_packet is not None:
            await self._send_packet(connection.websocket, routed_packet)
            return

        if packet.target_endpoint_id and not delivered:
            error_packet = self._build_error_packet(
                error_message=f"target endpoint is not online: {packet.target_endpoint_id}",
                source_endpoint_id="gateway",
                target_endpoint_id=connection.endpoint_id,
                trace_id=packet.trace_id,
            )
            await self._send_packet(connection.websocket, error_packet)
            return

        ack_packet = self._build_ack_packet(
            action="received",
            source_endpoint_id="gateway",
            target_endpoint_id=connection.endpoint_id,
            trace_id=packet.trace_id,
            extra_payload={"packet_type": packet.packet_type.value},
        )
        await self._send_packet(connection.websocket, ack_packet)

    async def _handle_register_packet(
        self,
        connection: WebSocketConnection,
        packet: RuntimePacket,
    ) -> RuntimePacket:
        endpoint_id_raw = packet.payload.get("endpoint_id")
        endpoint_id = str(endpoint_id_raw or "").strip()
        if not endpoint_id:
            return self._build_error_packet(
                error_message="register payload.endpoint_id is required",
                source_endpoint_id="gateway",
                target_endpoint_id=connection.endpoint_id,
                trace_id=packet.trace_id,
            )

        endpoint_type_value = str(packet.payload.get("endpoint_type") or RuntimeEndpointType.UNKNOWN.value).strip().upper()
        try:
            endpoint_type = RuntimeEndpointType(endpoint_type_value)
        except ValueError:
            endpoint_type = RuntimeEndpointType.UNKNOWN

        capabilities_raw = packet.payload.get("capabilities", ())
        if isinstance(capabilities_raw, (list, tuple, set)):
            capabilities: tuple[str, ...] = tuple(str(item) for item in capabilities_raw)
        elif capabilities_raw is None:
            capabilities = ()
        else:
            return self._build_error_packet(
                error_message="register payload.capabilities must be list/tuple/set",
                source_endpoint_id="gateway",
                target_endpoint_id=connection.endpoint_id,
                trace_id=packet.trace_id,
            )

        metadata_raw = packet.payload.get("metadata", {})
        if not isinstance(metadata_raw, dict):
            return self._build_error_packet(
                error_message="register payload.metadata must be object",
                source_endpoint_id="gateway",
                target_endpoint_id=connection.endpoint_id,
                trace_id=packet.trace_id,
            )

        endpoint = RuntimeEndpoint.create(
            endpoint_id=endpoint_id,
            endpoint_type=endpoint_type,
            capabilities=capabilities,
            metadata=metadata_raw,
        )
        self.runtime_service.endpoint_registry.register(endpoint)
        await self.connection_manager.bind_endpoint(connection.connection_id, endpoint_id)

        return self._build_ack_packet(
            action="register",
            source_endpoint_id="gateway",
            target_endpoint_id=endpoint_id,
            trace_id=packet.trace_id,
            extra_payload={"endpoint_id": endpoint_id},
        )

    async def _handle_heartbeat_packet(
        self,
        connection: WebSocketConnection,
        packet: RuntimePacket,
    ) -> RuntimePacket:
        endpoint_id = packet.source_endpoint_id or connection.endpoint_id
        endpoint_text = str(endpoint_id or "").strip()
        if not endpoint_text:
            return self._build_error_packet(
                error_message="heartbeat endpoint_id is missing",
                source_endpoint_id="gateway",
                target_endpoint_id=connection.endpoint_id,
                trace_id=packet.trace_id,
            )

        try:
            self.runtime_service.endpoint_registry.heartbeat(endpoint_text)
        except KeyError:
            return self._build_error_packet(
                error_message=f"endpoint not found: {endpoint_text}",
                source_endpoint_id="gateway",
                target_endpoint_id=connection.endpoint_id,
                trace_id=packet.trace_id,
            )

        try:
            await self.connection_manager.touch(connection.connection_id)
        except KeyError:
            pass

        return self._build_ack_packet(
            action="heartbeat",
            source_endpoint_id="gateway",
            target_endpoint_id=endpoint_text,
            trace_id=packet.trace_id,
            extra_payload={"endpoint_id": endpoint_text},
        )

    async def _send_packet(self, websocket: Any, packet: RuntimePacket) -> None:
        encoded = self._codec.encode(packet)
        await websocket.send(encoded)

    @staticmethod
    def _build_ack_packet(
        *,
        action: str,
        source_endpoint_id: str,
        target_endpoint_id: str | None,
        trace_id: str | None,
        extra_payload: dict[str, Any] | None = None,
    ) -> RuntimePacket:
        payload: dict[str, Any] = {
            "ok": True,
            "action": action,
        }
        if extra_payload:
            payload.update(extra_payload)

        return RuntimePacket.create(
            packet_type=RuntimePacketType.SYSTEM,
            source_endpoint_id=source_endpoint_id,
            target_endpoint_id=target_endpoint_id,
            trace_id=trace_id,
            payload=payload,
        )

    @staticmethod
    def _build_error_packet(
        *,
        error_message: str,
        source_endpoint_id: str,
        target_endpoint_id: str | None,
        trace_id: str | None,
    ) -> RuntimePacket:
        return RuntimePacket.create(
            packet_type=RuntimePacketType.ERROR,
            source_endpoint_id=source_endpoint_id,
            target_endpoint_id=target_endpoint_id,
            trace_id=trace_id,
            payload={
                "ok": False,
                "error_message": str(error_message),
            },
        )

    @staticmethod
    def _resolve_remote_address(websocket: Any) -> str | None:
        raw_address = getattr(websocket, "remote_address", None)
        if raw_address is None:
            return None
        if isinstance(raw_address, tuple):
            return ":".join(str(item) for item in raw_address if item is not None)
        return str(raw_address)

