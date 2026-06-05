# -*- coding: utf-8 -*-
from __future__ import annotations

import signal
import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from ns_backend.backend.runtime.ipc import NsRuntimeIpcRequest, NsRuntimeIpcServer
from ns_common.config import ns_config
from ns_common.runtime.config import NsRuntimeConfig
from ns_common.runtime.errors import NsRuntimeError
from ns_common.runtime.messages import NsRuntimeAck, NsRuntimeMessage
from ns_common.runtime.outbox import build_runtime_outbox

if TYPE_CHECKING:
    pass


@dataclass(slots=True, frozen=True, kw_only=True)
class NsBackendRuntimeConnectorStats:
    """Runtime connector in-process statistics."""

    claimed_count: int = 0
    acked_count: int = 0
    retry_count: int = 0
    dead_count: int = 0
    last_error: str | None = None


class NsBackendRuntimeStubSender:
    """Stub runtime sender used before WebSocket integration.

    The sender pretends that ns_runtime master accepted the message. This is
    intentional for P4 so the connector drain loop can be verified without
    networking.
    """

    def send(self, message: NsRuntimeMessage) -> NsRuntimeAck:
        """Send one runtime message and return accepted ack."""
        return NsRuntimeAck(
            message_id=str(message.message_id),
            status="accepted",
            handled_by="backend-runtime-stub-sender",
            trace_id=message.trace_id,
        )


class NsBackendRuntimeConnector:
    """Backend runtime connector.

    The connector owns local IPC server and outbox drain loop. It does not
    connect to ns_runtime master in this stage. Future WebSocket sender will
    replace NsBackendRuntimeStubSender.
    """

    def __init__(
            self,
            *,
            config: NsRuntimeConfig | None = None,
            sender: NsBackendRuntimeSender | None = None,
    ) -> None:
        """Initialize backend runtime connector."""
        self._config: NsRuntimeConfig = config or ns_config.runtime_config
        self._outbox = build_runtime_outbox(self._config)
        self._sender = sender or NsBackendRuntimeStubSender()

        self._stop_event = threading.Event()
        self._wakeup_event = threading.Event()
        self._stats_lock = threading.RLock()
        self._stats = NsBackendRuntimeConnectorStats()

        self._ipc_server = NsRuntimeIpcServer(
            self._config,
            wakeup_handler=self._handle_wakeup,
        )
        self._ipc_thread: threading.Thread | None = None

    @property
    def stats(self) -> NsBackendRuntimeConnectorStats:
        """Return connector stats snapshot."""
        with self._stats_lock:
            return self._stats

    def start(self) -> None:
        """Start connector lifecycle resources."""
        self._ensure_enabled()
        self._start_sender()
        self._start_ipc_server()

    def run_forever(self) -> None:
        """Run connector until stop() is called."""
        self._install_signal_handlers()
        self.start()

        try:
            self._drain_loop()
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop connector resources."""
        self._stop_event.set()
        self._wakeup_event.set()
        sender_close = getattr(self._sender, "close", None)
        if sender_close is not None:
            try:
                sender_close()
            except Exception:  # noqa
                pass
        try:
            self._ipc_server.stop()
        except Exception:  # noqa
            pass

        if self._ipc_thread is not None and self._ipc_thread.is_alive():
            self._ipc_thread.join(timeout=2.0)

        close = getattr(self._outbox, "close", None)
        if close is not None:
            close()

    def drain_once(self) -> int:
        """Drain one batch of outbox messages.

        Returns the number of claimed messages.
        """
        messages = self._outbox.claim_batch(
            consumer_id=self._config.node_id,
            limit=self._config.outbox_claim_batch_size,
        )

        if not messages:
            return 0

        self._add_stats(claimed_count=len(messages))

        for message in messages:
            self._send_one(message)

        return len(messages)

    def _send_one(self, message: NsRuntimeMessage) -> None:
        """Send one claimed message and update outbox state."""
        message_id = str(message.message_id or "")
        try:
            ack = self._sender.send(message)
            normalized_ack = ack.normalized()
            if normalized_ack.status in {"accepted", "forwarded", "delivered"}:
                self._outbox.mark_acked(message_id=message_id, ack=normalized_ack)
                self._add_stats(acked_count=1)
                return

            self._outbox.mark_retry(
                message_id=message_id,
                reason=f"runtime ack status is not accepted: {normalized_ack.status}",
            )
            self._add_stats(retry_count=1)
        except Exception as exc:  # noqa
            self._outbox.mark_retry(message_id=message_id, reason=str(exc))
            self._add_stats(retry_count=1, last_error=str(exc))

    def _drain_loop(self) -> None:
        """Continuously drain outbox."""
        idle_sleep_seconds = 1.0

        while not self._stop_event.is_set():
            drained = self.drain_once()

            if drained > 0:
                continue

            # 没有消息时等待 wakeup；超时后也会周期性扫描 outbox。
            self._wakeup_event.wait(timeout=idle_sleep_seconds)
            self._wakeup_event.clear()

    def _handle_wakeup(self, request: NsRuntimeIpcRequest) -> None:
        """Handle local IPC wakeup request."""
        self._wakeup_event.set()

    def _start_ipc_server(self) -> None:
        """Start local IPC server in background thread."""
        if self._ipc_thread is not None and self._ipc_thread.is_alive():
            return

        self._ipc_thread = threading.Thread(
            target=self._ipc_server.serve_forever,
            name="ns-backend-runtime-ipc",
            daemon=True,
        )
        self._ipc_thread.start()

    def _start_sender(self) -> None:
        """Start sender if it has lifecycle hook."""
        sender_start = getattr(self._sender, "start", None)
        if sender_start is not None:
            sender_start()

    def _ensure_enabled(self) -> None:
        """Ensure runtime connector is enabled."""
        if not self._config.enabled:
            raise NsRuntimeError("runtime connector is disabled")

    def _install_signal_handlers(self) -> None:
        """Install best-effort signal handlers for graceful shutdown."""
        try:
            signal.signal(signal.SIGINT, lambda _sig, _frame: self.stop())
            signal.signal(signal.SIGTERM, lambda _sig, _frame: self.stop())
        except ValueError:
            # Signal handlers can only be installed in main thread.
            pass

    def _add_stats(
            self,
            *,
            claimed_count: int = 0,
            acked_count: int = 0,
            retry_count: int = 0,
            dead_count: int = 0,
            last_error: str | None = None,
    ) -> None:
        """Update connector stats."""
        with self._stats_lock:
            self._stats = NsBackendRuntimeConnectorStats(
                claimed_count=self._stats.claimed_count + claimed_count,
                acked_count=self._stats.acked_count + acked_count,
                retry_count=self._stats.retry_count + retry_count,
                dead_count=self._stats.dead_count + dead_count,
                last_error=last_error if last_error is not None else self._stats.last_error,
            )


class NsBackendRuntimeSender(Protocol):
    """Runtime sender protocol used by backend runtime connector."""

    def send(self, message: NsRuntimeMessage) -> NsRuntimeAck:
        """Send one runtime message and return runtime ack."""
