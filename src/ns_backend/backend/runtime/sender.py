# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import threading
import time
from typing import Any, TYPE_CHECKING

from ns_backend.backend.runtime.inbox import build_backend_runtime_inbox
from ns_backend.backend.runtime.protocol import (
    NsBackendRuntimeFrame,
    build_backend_ack_frame,
    build_backend_heartbeat_frame,
    build_backend_publish_frame,
    build_backend_register_frame,
    parse_ack_frame,
    parse_backend_deliver_frame,
)
from ns_common.runtime.config import NsRuntimeConfig
from ns_common.runtime.errors import NsRuntimeAckTimeoutError, NsRuntimePublishError
from ns_common.runtime.messages import NsRuntimeAck, NsRuntimeMessage

if TYPE_CHECKING:
    pass


class NsBackendRuntimeWebSocketSender:
    """WebSocket sender used by backend runtime connector.

    This sender owns one long-lived WebSocket connection to ns_runtime master.
    It sends backend.register on connect, emits backend.heartbeat periodically,
    and sends backend.publish frames for outbox messages.
    """

    def __init__(self, config: NsRuntimeConfig) -> None:
        """Initialize WebSocket sender."""
        self._config: NsRuntimeConfig = config
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._ready_event = threading.Event()
        self._stop_event = threading.Event()
        self._pending_lock = threading.RLock()
        self._pending_acks: dict[str, asyncio.Future[NsRuntimeAck]] = {}
        self._websocket: Any | None = None
        self._send_lock: asyncio.Lock | None = None
        self._inbox = build_backend_runtime_inbox(config)

    def start(self) -> None:
        """Start WebSocket sender background event loop."""
        if self._thread is not None and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop_thread, name="ns-backend-runtime-websocket", daemon=True)
        self._thread.start()

        # 这里不强制等待连接成功。master 尚未启动时，connector 仍可运行；
        # drain 时 send() 会等待连接或超时后触发 retry。
        self._ready_event.wait(timeout=0.1)

    def close(self) -> None:
        """Close WebSocket sender."""
        self._stop_event.set()

        if self._loop is not None and self._loop.is_running():
            future = asyncio.run_coroutine_threadsafe(self._close_async(), self._loop)
            try:
                future.result(timeout=2.0)
            except Exception:  # noqa
                pass
            self._loop.call_soon_threadsafe(self._loop.stop)

        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        try:
            self._inbox.close()
        except Exception:  # noqa
            pass

    def send(self, message: NsRuntimeMessage) -> NsRuntimeAck:
        """Send one runtime message through WebSocket and wait for master ack."""
        if self._loop is None or not self._loop.is_running():
            raise NsRuntimePublishError("runtime websocket sender is not running")

        future = asyncio.run_coroutine_threadsafe(self._send_message_async(message), self._loop)
        try:
            return future.result(timeout=float(self._config.ack_timeout_seconds) + 1.0)
        except TimeoutError as exc:
            raise NsRuntimeAckTimeoutError("runtime websocket sender ack timed out") from exc
        except Exception as exc:
            if isinstance(exc, NsRuntimePublishError | NsRuntimeAckTimeoutError):
                raise
            raise NsRuntimePublishError("runtime websocket sender failed to send message") from exc

    def _run_loop_thread(self) -> None:
        """Run asyncio loop in background thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._send_lock = asyncio.Lock()

        self._loop.create_task(self._connection_loop())
        self._loop.run_forever()

        pending = asyncio.all_tasks(self._loop)
        for task in pending:
            task.cancel()

        try:
            self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        finally:
            self._loop.close()

    async def _connection_loop(self) -> None:
        """Maintain WebSocket connection with reconnect."""
        try:
            import websockets
        except ImportError as exc:
            self._fail_pending(NsRuntimePublishError("websockets package is required for runtime websocket sender"))
            return

        reconnect_delay: float = max(float(self._config.retry_base_delay_seconds), 1.0)
        max_delay: float = max(float(self._config.retry_max_delay_seconds), reconnect_delay)

        while not self._stop_event.is_set():
            try:
                async with websockets.connect(self._config.master_url) as websocket:
                    self._websocket = websocket
                    self._ready_event.set()
                    await self._send_register()
                    heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                    receive_task = asyncio.create_task(self._receive_loop())

                    done, pending = await asyncio.wait(
                        {heartbeat_task, receive_task},
                        return_when=asyncio.FIRST_EXCEPTION,
                    )

                    for task in pending:
                        task.cancel()

                    for task in done:
                        task.result()
            except Exception as exc:
                self._ready_event.clear()
                self._websocket = None
                self._fail_pending(exc)

                if self._stop_event.is_set():
                    break

                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, max_delay)
                continue

            reconnect_delay = max(float(self._config.retry_base_delay_seconds), 1.0)

    async def _send_register(self) -> None:
        """Send backend.register frame."""
        frame = build_backend_register_frame(
            node_id=self._config.node_id,
            auth_token=self._config.service_token,
        )
        await self._send_frame(frame)

    async def _heartbeat_loop(self) -> None:
        """Send backend.heartbeat periodically."""
        interval_seconds: float = max(float(self._config.heartbeat_interval_seconds), 1.0)

        while not self._stop_event.is_set():
            await asyncio.sleep(interval_seconds)
            frame = build_backend_heartbeat_frame(
                node_id=self._config.node_id,
                health={
                    "timestamp_epoch_ms": int(time.time() * 1000),
                },
            )
            await self._send_frame(frame)

    async def _receive_loop(self) -> None:
        """Receive frames from ns_runtime master."""
        websocket = self._websocket
        if websocket is None:
            raise NsRuntimePublishError("runtime websocket is not connected")

        async for raw_message in websocket:
            data = self._loads_frame(raw_message)
            frame_type = str(data.get("type") or "")

            if frame_type == "ack":
                ack = parse_ack_frame(data)
                self._resolve_ack(ack)
                continue

            if frame_type == "backend.deliver":
                await self._handle_backend_deliver(data)
                continue

    async def _handle_backend_deliver(self, data: dict[str, Any]) -> None:
        """Persist one inbound runtime message and ack runtime."""
        message, correlation_id, reply_to_message_id = parse_backend_deliver_frame(data)
        self._inbox.put(
            message,
            correlation_id=correlation_id,
            reply_to_message_id=reply_to_message_id,
        )

        frame = NsBackendRuntimeFrame.from_dict(data)
        ack = NsRuntimeAck(
            message_id=frame.message_id,
            status="accepted",  # type: ignore[arg-type]
            handled_by=self._config.node_id,
            trace_id=frame.trace_id,
        ).normalized()
        await self._send_frame(build_backend_ack_frame(ack))

    async def _send_message_async(self, message: NsRuntimeMessage) -> NsRuntimeAck:
        """Send backend.publish frame and wait for ack."""
        normalized_message: NsRuntimeMessage = message.normalized()
        message_id: str = str(normalized_message.message_id)

        loop = asyncio.get_running_loop()
        ack_future: asyncio.Future[NsRuntimeAck] = loop.create_future()

        with self._pending_lock:
            self._pending_acks[message_id] = ack_future

        try:
            frame = build_backend_publish_frame(normalized_message)
            await self._send_frame(frame)
            return await asyncio.wait_for(ack_future, timeout=float(self._config.ack_timeout_seconds))
        finally:
            with self._pending_lock:
                self._pending_acks.pop(message_id, None)

    async def _send_frame(self, frame: NsBackendRuntimeFrame) -> None:
        """Send one JSON frame through active WebSocket."""
        websocket = self._websocket
        if websocket is None:
            raise NsRuntimePublishError("runtime websocket is not connected")

        if self._send_lock is None:
            raise NsRuntimePublishError("runtime websocket send lock is not initialized")

        payload = json.dumps(frame.to_dict(), ensure_ascii=False, separators=(",", ":"))

        async with self._send_lock:
            await websocket.send(payload)

    async def _close_async(self) -> None:
        """Close active websocket."""
        websocket = self._websocket
        if websocket is not None:
            await websocket.close()

    def _resolve_ack(self, ack: NsRuntimeAck) -> None:
        """Resolve one pending ack future."""
        with self._pending_lock:
            future = self._pending_acks.get(str(ack.message_id))

        if future is not None and not future.done():
            future.set_result(ack)

    def _fail_pending(self, exc: BaseException) -> None:
        """Fail all pending ack futures."""
        with self._pending_lock:
            pending = list(self._pending_acks.values())
            self._pending_acks.clear()

        for future in pending:
            if not future.done():
                future.set_exception(exc)

    @staticmethod
    def _loads_frame(raw_message: Any) -> dict[str, Any]:
        """Decode one JSON websocket frame."""
        if isinstance(raw_message, bytes):
            raw_text = raw_message.decode("utf-8")
        else:
            raw_text = str(raw_message)

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise NsRuntimePublishError("runtime websocket frame is invalid JSON") from exc

        if not isinstance(data, dict):
            raise NsRuntimePublishError("runtime websocket frame must be a JSON object")

        return data
