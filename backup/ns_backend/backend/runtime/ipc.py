# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import socket
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal, TYPE_CHECKING

from ns_common.runtime.config import NsRuntimeConfig
from ns_common.runtime.constants import (
    RUNTIME_CONNECTOR_IPC_MEMORY,
    RUNTIME_CONNECTOR_IPC_TCP,
    RUNTIME_CONNECTOR_IPC_UNIX_SOCKET,
)
from ns_common.runtime.errors import NsRuntimeIpcError

if TYPE_CHECKING:
    pass

RuntimeIpcRequestType = Literal["ping", "wakeup"]


@dataclass(slots=True, frozen=True, kw_only=True)
class NsRuntimeIpcRequest:
    """Request payload sent from backend worker to backend runtime connector."""

    request_type: RuntimeIpcRequestType
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at_epoch_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize IPC request."""
        request_type = str(self.request_type or "").strip().lower()
        if request_type not in {
            "ping",
            "wakeup"
        }:
            raise NsRuntimeIpcError(f"runtime ipc request_type is invalid: {self.request_type}")

        return {
            "request_type": request_type,
            "request_id": str(self.request_id or "").strip() or uuid.uuid4().hex,
            "created_at_epoch_ms": int(self.created_at_epoch_ms),
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NsRuntimeIpcRequest":
        """Deserialize IPC request."""
        if not isinstance(data, dict):
            raise NsRuntimeIpcError("runtime ipc request must be a JSON object")

        request_type = str(data.get("request_type") or "").strip().lower()
        if request_type not in {
            "ping",
            "wakeup"
        }:
            raise NsRuntimeIpcError(f"runtime ipc request_type is invalid: {request_type}")

        return cls(
            request_type=request_type,  # type: ignore[arg-type]
            request_id=str(data.get("request_id") or "").strip() or uuid.uuid4().hex,
            created_at_epoch_ms=int(data.get("created_at_epoch_ms") or int(time.time() * 1000)),
            payload=dict(data.get("payload") or {}),
        )


@dataclass(slots=True, frozen=True, kw_only=True)
class NsRuntimeIpcResponse:
    """Response payload returned by backend runtime connector IPC server."""

    request_id: str
    ok: bool
    message: str = ""
    created_at_epoch_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize IPC response."""
        return {
            "request_id": str(self.request_id or "").strip(),
            "ok": bool(self.ok),
            "message": str(self.message or ""),
            "created_at_epoch_ms": int(self.created_at_epoch_ms),
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NsRuntimeIpcResponse":
        """Deserialize IPC response."""
        if not isinstance(data, dict):
            raise NsRuntimeIpcError("runtime ipc response must be a JSON object")

        return cls(
            request_id=str(data.get("request_id") or "").strip(),
            ok=bool(data.get("ok")),
            message=str(data.get("message") or ""),
            created_at_epoch_ms=int(data.get("created_at_epoch_ms") or int(time.time() * 1000)),
            payload=dict(data.get("payload") or {}),
        )


class NsRuntimeIpcClient:
    """Local IPC client used by backend workers to notify backend runtime connector.

    The IPC notification is intentionally best-effort. Durable delivery is
    provided by SqlWalRuntimeOutbox, not by this IPC channel.
    """

    def __init__(self, config: NsRuntimeConfig, *, timeout_seconds: float = 0.2) -> None:
        """Initialize runtime IPC client."""
        self._config = config
        self._timeout_seconds = max(float(timeout_seconds), 0.001)

    def ping(self) -> NsRuntimeIpcResponse:
        """Send ping request to local runtime connector."""
        return self._send(NsRuntimeIpcRequest(request_type="ping"))

    def wakeup(self, *, message_id: str | None = None) -> NsRuntimeIpcResponse:
        """Notify local runtime connector that outbox has pending messages."""
        payload: dict[str, Any] = {}
        if message_id:
            payload["message_id"] = str(message_id)

        return self._send(NsRuntimeIpcRequest(request_type="wakeup", payload=payload))

    def wakeup_best_effort(self, *, message_id: str | None = None) -> bool:
        """Notify connector without failing caller when IPC is unavailable."""
        try:
            response = self.wakeup(message_id=message_id)
            return bool(response.ok)
        except NsRuntimeIpcError:
            return False

    def _send(self, request: NsRuntimeIpcRequest) -> NsRuntimeIpcResponse:
        """Send one IPC request based on configured IPC mode."""
        ipc_mode = self._config.ipc_mode

        if ipc_mode == RUNTIME_CONNECTOR_IPC_MEMORY:
            return NsRuntimeIpcResponse(
                request_id=request.request_id,
                ok=True,
                message="memory ipc noop",
            )

        if ipc_mode == RUNTIME_CONNECTOR_IPC_UNIX_SOCKET:
            return self._send_unix_socket(request)

        if ipc_mode == RUNTIME_CONNECTOR_IPC_TCP:
            return self._send_tcp(request)

        raise NsRuntimeIpcError(f"unsupported runtime ipc mode: {ipc_mode}")

    def _send_unix_socket(self, request: NsRuntimeIpcRequest) -> NsRuntimeIpcResponse:
        """Send IPC request through Unix Domain Socket."""
        socket_path = str(self._config.ipc_socket_path or "").strip()
        if not socket_path:
            raise NsRuntimeIpcError("runtime ipc_socket_path is required")

        if not Path(socket_path).exists():
            raise NsRuntimeIpcError(f"runtime ipc socket does not exist: {socket_path}")

        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(self._timeout_seconds)
                client.connect(socket_path)
                self._write_frame(client, request.to_dict())
                return NsRuntimeIpcResponse.from_dict(self._read_frame(client))
        except OSError as exc:
            raise NsRuntimeIpcError("runtime unix socket ipc failed") from exc

    def _send_tcp(self, request: NsRuntimeIpcRequest) -> NsRuntimeIpcResponse:
        """Send IPC request through localhost TCP."""
        host = str(self._config.ipc_host or "").strip()
        port = int(self._config.ipc_port)
        if not host or port <= 0:
            raise NsRuntimeIpcError("runtime ipc_host/ipc_port is invalid")

        try:
            with socket.create_connection(
                    (
                            host,
                            port
                    ), timeout=self._timeout_seconds
            ) as client:
                client.settimeout(self._timeout_seconds)
                self._write_frame(client, request.to_dict())
                return NsRuntimeIpcResponse.from_dict(self._read_frame(client))
        except OSError as exc:
            raise NsRuntimeIpcError("runtime tcp ipc failed") from exc

    @staticmethod
    def _write_frame(sock: socket.socket, data: dict[str, Any]) -> None:
        """Write one newline-delimited JSON frame."""
        payload = json.dumps(
            data, ensure_ascii=False, separators=(
                ",",
                ":"
            )
        ).encode("utf-8") + b"\n"
        sock.sendall(payload)

    @staticmethod
    def _read_frame(sock: socket.socket) -> dict[str, Any]:
        """Read one newline-delimited JSON frame."""
        chunks: list[bytes] = []
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
            if b"\n" in chunk:
                break

        raw = b"".join(chunks).split(b"\n", 1)[0].strip()
        if not raw:
            raise NsRuntimeIpcError("runtime ipc response is empty")

        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise NsRuntimeIpcError("runtime ipc response is invalid JSON") from exc

        if not isinstance(data, dict):
            raise NsRuntimeIpcError("runtime ipc response must be a JSON object")

        return data


class NsRuntimeIpcServer:
    """Small local IPC server stub for backend runtime connector.

    This server only handles local IPC requests. It does not drain outbox and
    does not connect to ns_runtime master. The future connector process will
    use this server to receive wakeup notifications from backend workers.
    """

    def __init__(self, config: NsRuntimeConfig, *, wakeup_handler: Callable[[NsRuntimeIpcRequest], None] | None = None) -> None:
        """Initialize runtime IPC server."""
        self._config = config
        self._wakeup_handler = wakeup_handler
        self._stop_event = threading.Event()
        self._server_socket: socket.socket | None = None

    def serve_forever(self) -> None:
        """Run IPC server forever until stop() is called."""
        ipc_mode = self._config.ipc_mode

        if ipc_mode == RUNTIME_CONNECTOR_IPC_MEMORY:
            return

        if ipc_mode == RUNTIME_CONNECTOR_IPC_UNIX_SOCKET:
            self._serve_unix_socket()
            return

        if ipc_mode == RUNTIME_CONNECTOR_IPC_TCP:
            self._serve_tcp()
            return

        raise NsRuntimeIpcError(f"unsupported runtime ipc mode: {ipc_mode}")

    def stop(self) -> None:
        """Stop IPC server."""
        self._stop_event.set()
        if self._server_socket is not None:
            try:
                self._server_socket.close()
            except OSError:
                pass

    def _serve_unix_socket(self) -> None:
        """Run Unix Domain Socket IPC server."""
        socket_path = Path(str(self._config.ipc_socket_path or "").strip())
        if not str(socket_path):
            raise NsRuntimeIpcError("runtime ipc_socket_path is required")

        socket_path.parent.mkdir(parents=True, exist_ok=True)
        if socket_path.exists():
            socket_path.unlink()

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            self._server_socket = server
            server.bind(str(socket_path))
            server.listen(16)
            server.settimeout(0.5)

            try:
                self._accept_loop(server)
            finally:
                try:
                    socket_path.unlink()
                except FileNotFoundError:
                    pass

    def _serve_tcp(self) -> None:
        """Run localhost TCP IPC server."""
        host = str(self._config.ipc_host or "").strip()
        port = int(self._config.ipc_port)
        if not host or port <= 0:
            raise NsRuntimeIpcError("runtime ipc_host/ipc_port is invalid")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            self._server_socket = server
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(
                (
                    host,
                    port
                )
            )
            server.listen(16)
            server.settimeout(0.5)
            self._accept_loop(server)

    def _accept_loop(self, server: socket.socket) -> None:
        """Accept and handle IPC clients."""
        while not self._stop_event.is_set():
            try:
                client, _addr = server.accept()
            except TimeoutError:
                continue
            except OSError:
                if self._stop_event.is_set():
                    break
                raise

            thread = threading.Thread(
                target=self._handle_client_safe, args=(
                    client,
                ), daemon=True
            )
            thread.start()

    def _handle_client_safe(self, client: socket.socket) -> None:
        """Handle one IPC client and never leak socket resources."""
        with client:
            try:
                data = NsRuntimeIpcClient._read_frame(client)
                request = NsRuntimeIpcRequest.from_dict(data)
                response = self._handle_request(request)
            except Exception as exc:  # noqa
                response = NsRuntimeIpcResponse(
                    request_id="",
                    ok=False,
                    message=str(exc),
                )

            NsRuntimeIpcClient._write_frame(client, response.to_dict())

    def _handle_request(self, request: NsRuntimeIpcRequest) -> NsRuntimeIpcResponse:
        """Handle one IPC request."""
        if request.request_type == "ping":
            return NsRuntimeIpcResponse(
                request_id=request.request_id,
                ok=True,
                message="pong",
            )

        if request.request_type == "wakeup":
            if self._wakeup_handler is not None:
                self._wakeup_handler(request)

            return NsRuntimeIpcResponse(
                request_id=request.request_id,
                ok=True,
                message="wakeup accepted",
            )

        return NsRuntimeIpcResponse(
            request_id=request.request_id,
            ok=False,
            message=f"unsupported request_type: {request.request_type}",
        )
