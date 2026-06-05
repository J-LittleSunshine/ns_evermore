# -*- coding: utf-8 -*-
from __future__ import annotations

import time
import uuid
from dataclasses import replace
from threading import RLock
from typing import TYPE_CHECKING, ClassVar

from ns_backend.backend.runtime.inbox import SqliteBackendRuntimeInbox, build_backend_runtime_inbox
from ns_backend.backend.runtime.ipc import NsRuntimeIpcClient
from ns_backend.backend.runtime.request_reply import NsBackendRuntimeRequestReplyResult
from ns_common.config import ns_config
from ns_common.runtime.config import NsRuntimeConfig
from ns_common.runtime.constants import RUNTIME_PRODUCER_BACKEND
from ns_common.runtime.contracts import NsRuntimeOutbox
from ns_common.runtime.errors import NsRuntimePublishError
from ns_common.runtime.messages import NsRuntimeMessage, RuntimeTargetType
from ns_common.runtime.outbox import build_runtime_outbox

if TYPE_CHECKING:
    pass


class NsBackendRuntimeClient:
    """Backend-side runtime client.

    This client is used by ns_backend workers and business modules to publish
    runtime messages into the local durable outbox.

    It does not connect to ns_runtime master directly. The backend runtime
    connector drains the same outbox and sends messages through the single
    WebSocket connection.
    """

    _instances: ClassVar[dict[str, "NsBackendRuntimeClient"]] = {}
    _instances_lock: ClassVar[RLock] = RLock()

    def __init__(self, *, config: NsRuntimeConfig | None = None, outbox: NsRuntimeOutbox | None = None, ipc_client: NsRuntimeIpcClient | None = None, inbox: SqliteBackendRuntimeInbox | None = None) -> None:
        """Initialize backend runtime client."""
        self._config: NsRuntimeConfig = config or ns_config.runtime_config
        self._outbox: NsRuntimeOutbox = outbox or build_runtime_outbox(self._config)
        self._ipc_client: NsRuntimeIpcClient = ipc_client or NsRuntimeIpcClient(self._config)
        self._inbox: SqliteBackendRuntimeInbox | None = inbox

    @classmethod
    def get_default(cls) -> "NsBackendRuntimeClient":
        """Return default singleton backend runtime client."""
        return cls.get("default")

    @classmethod
    def get(cls, name: str = "default", *, config: NsRuntimeConfig | None = None) -> "NsBackendRuntimeClient":
        """Return named singleton backend runtime client."""
        normalized_name = str(name or "").strip() or "default"

        with cls._instances_lock:
            if normalized_name not in cls._instances:
                cls._instances[normalized_name] = cls(config=config)
            return cls._instances[normalized_name]

    @classmethod
    def clear_instances(cls) -> None:
        """Clear runtime client singleton instances.

        This is mainly intended for tests and controlled process reloads.
        """
        with cls._instances_lock:
            for instance in cls._instances.values():
                instance.close()
            cls._instances.clear()

    def publish(self, message: NsRuntimeMessage, *, require_enabled: bool = True, notify_connector: bool = True) -> str:
        """Publish one runtime message into local durable outbox."""
        if require_enabled:
            self._ensure_enabled()

        normalized_message: NsRuntimeMessage = self._prepare_message(message)
        message_id: str = self._outbox.enqueue(normalized_message)

        # IPC only wakes connector. Reliability is owned by the durable outbox.
        if notify_connector:
            self._ipc_client.wakeup_best_effort(message_id=message_id)

        return message_id

    def publish_event(
            self,
            *,
            topic: str,
            event: str,
            payload: dict | None = None,
            target_type: RuntimeTargetType = "user",
            target_id: str | int | None = None,
            trace_id: str | None = None,
            idempotency_key: str | None = None,
            ttl_seconds: int | None = 300,
            require_ack: bool = True,
            headers: dict[str, str] | None = None,
            require_enabled: bool = True,
            notify_connector: bool = True,
    ) -> str:
        """Build and publish one backend runtime event."""
        message = NsRuntimeMessage.new(
            topic=topic,
            event=event,
            payload=payload or {},
            target_type=target_type,
            target_id=target_id,
            producer_type=RUNTIME_PRODUCER_BACKEND,  # type: ignore[arg-type]
            producer_id=self._config.node_id,
            trace_id=trace_id,
            idempotency_key=idempotency_key,
            ttl_seconds=ttl_seconds,
            require_ack=require_ack,
            headers=headers or {},
        )
        return self.publish(message, require_enabled=require_enabled, notify_connector=notify_connector)

    def request_reply(self, message: NsRuntimeMessage, *, correlation_id: str | None = None, timeout_seconds: float = 5.0, poll_interval_seconds: float = 0.05, require_enabled: bool = True, notify_connector: bool = True) -> NsBackendRuntimeRequestReplyResult:
        """Publish one request message and wait briefly for a correlated reply.

        This is a short-timeout request/reply helper for Django/ADRF views.
        It is not a long-running task mechanism. On timeout, the method returns
        a result with reply=None instead of marking the outbound message failed.
        """
        if require_enabled:
            self._ensure_enabled()

        started_monotonic = time.monotonic()
        min_received_at_epoch_ms = int(time.time() * 1000)
        prepared_message = self._prepare_request_reply_message(message, correlation_id=correlation_id)
        normalized_correlation_id = str(prepared_message.headers["correlation_id"])

        self.publish(
            prepared_message,
            require_enabled=False,
            notify_connector=notify_connector,
        )

        reply = self._get_inbox().wait_for_correlation_id(
            normalized_correlation_id,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
            min_received_at_epoch_ms=min_received_at_epoch_ms,
        )

        elapsed_seconds = time.monotonic() - started_monotonic
        return NsBackendRuntimeRequestReplyResult(
            request_message_id=str(prepared_message.message_id),
            correlation_id=normalized_correlation_id,
            timeout_seconds=float(timeout_seconds),
            elapsed_seconds=elapsed_seconds,
            reply=reply,
        )

    def request_reply_event(
            self,
            *,
            topic: str,
            event: str,
            payload: dict | None = None,
            target_type: RuntimeTargetType = "user",
            target_id: str | int | None = None,
            correlation_id: str | None = None,
            trace_id: str | None = None,
            idempotency_key: str | None = None,
            ttl_seconds: int | None = 300,
            require_ack: bool = True,
            headers: dict[str, str] | None = None,
            timeout_seconds: float = 5.0,
            poll_interval_seconds: float = 0.05,
            require_enabled: bool = True,
            notify_connector: bool = True,
    ) -> NsBackendRuntimeRequestReplyResult:
        """Build one request message, publish it, and wait briefly for reply."""
        message = NsRuntimeMessage.new(
            topic=topic,
            event=event,
            payload=payload or {},
            target_type=target_type,
            target_id=target_id,
            producer_type=RUNTIME_PRODUCER_BACKEND,  # type: ignore[arg-type]
            producer_id=self._config.node_id,
            trace_id=trace_id,
            idempotency_key=idempotency_key,
            ttl_seconds=ttl_seconds,
            require_ack=require_ack,
            headers=headers or {},
        )

        return self.request_reply(
            message,
            correlation_id=correlation_id,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
            require_enabled=require_enabled,
            notify_connector=notify_connector,
        )

    def publish_on_commit(self, message: NsRuntimeMessage, *, require_enabled: bool = True, notify_connector: bool = True) -> str:
        """Publish one runtime message after current Django transaction commits."""
        if require_enabled:
            self._ensure_enabled()

        normalized_message = self._prepare_message(message)
        message_id = str(normalized_message.message_id or "")

        try:
            from django.db import transaction
        except Exception as exc:  # noqa
            raise NsRuntimePublishError("django transaction support is required for publish_on_commit") from exc

        transaction.on_commit(
            lambda: self.publish(
                normalized_message,
                require_enabled=require_enabled,
                notify_connector=notify_connector,
            )
        )
        return message_id

    def publish_event_on_commit(
            self,
            *,
            topic: str,
            event: str,
            payload: dict | None = None,
            target_type: RuntimeTargetType = "user",
            target_id: str | int | None = None,
            trace_id: str | None = None,
            idempotency_key: str | None = None,
            ttl_seconds: int | None = 300,
            require_ack: bool = True,
            headers: dict[str, str] | None = None,
            require_enabled: bool = True,
            notify_connector: bool = True,
    ) -> str:
        """Build and publish one backend runtime event after current transaction commits."""
        message = NsRuntimeMessage.new(
            topic=topic,
            event=event,
            payload=payload or {},
            target_type=target_type,
            target_id=target_id,
            producer_type=RUNTIME_PRODUCER_BACKEND,  # type: ignore[arg-type]
            producer_id=self._config.node_id,
            trace_id=trace_id,
            idempotency_key=idempotency_key,
            ttl_seconds=ttl_seconds,
            require_ack=require_ack,
            headers=headers or {},
        )
        return self.publish_on_commit(
            message,
            require_enabled=require_enabled,
            notify_connector=notify_connector,
        )

    def count_outbox_status(self, status: str) -> int:
        """Return local outbox count by status when the backend supports it."""
        counter = getattr(self._outbox, "count_by_status", None)
        if counter is None:
            raise NsRuntimePublishError("runtime outbox does not support count_by_status")
        return int(counter(status))

    def close(self) -> None:
        """Close runtime client resources."""
        close = getattr(self._outbox, "close", None)
        if close is not None:
            close()

        if self._inbox is not None:
            self._inbox.close()
            self._inbox = None

    def _prepare_message(self, message: NsRuntimeMessage) -> NsRuntimeMessage:
        """Normalize message and fill backend producer defaults."""
        normalized_message = message.normalized()

        producer_id = normalized_message.producer_id
        if producer_id is None:
            producer_id = self._config.node_id

        return replace(
            normalized_message,
            producer_type=RUNTIME_PRODUCER_BACKEND,  # type: ignore[arg-type]
            producer_id=producer_id,
        ).normalized()

    def _prepare_request_reply_message(self, message: NsRuntimeMessage, *, correlation_id: str | None = None) -> NsRuntimeMessage:
        """Prepare runtime message as request/reply request."""
        normalized_message = self._prepare_message(message)

        normalized_correlation_id = str(
            correlation_id
            or normalized_message.headers.get("correlation_id")
            or normalized_message.trace_id
            or uuid.uuid4().hex
        ).strip()

        if not normalized_correlation_id:
            normalized_correlation_id = uuid.uuid4().hex

        headers = dict(normalized_message.headers)
        headers["runtime_pattern"] = "request_reply"
        headers["correlation_id"] = normalized_correlation_id
        headers["reply_to_backend_id"] = self._config.node_id
        headers["reply_to_message_id"] = str(normalized_message.message_id)

        trace_id = normalized_message.trace_id or normalized_correlation_id

        return replace(
            normalized_message,
            trace_id=trace_id,
            headers=headers,
        ).normalized()

    def _get_inbox(self) -> SqliteBackendRuntimeInbox:
        """Return lazy backend runtime inbox."""
        if self._inbox is None:
            self._inbox = build_backend_runtime_inbox(self._config)
        return self._inbox

    def _ensure_enabled(self) -> None:
        """Ensure runtime publishing is enabled."""
        if not self._config.enabled:
            raise NsRuntimePublishError("runtime publishing is disabled")
