# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import replace
from threading import RLock
from typing import TYPE_CHECKING, ClassVar

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

    It does not connect to ns_runtime master directly. The future backend
    runtime connector will drain the same outbox and send messages through
    the single WebSocket connection.
    """

    _instances: ClassVar[dict[str, "NsBackendRuntimeClient"]] = {}
    _instances_lock: ClassVar[RLock] = RLock()

    def __init__(self, *, config: NsRuntimeConfig | None = None, outbox: NsRuntimeOutbox | None = None) -> None:
        """Initialize backend runtime client."""
        self._config: NsRuntimeConfig = config or ns_config.runtime_config
        self._outbox: NsRuntimeOutbox = outbox or build_runtime_outbox(self._config)

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

    def publish(self, message: NsRuntimeMessage, *, require_enabled: bool = True) -> str:
        """Publish one runtime message into local durable outbox."""
        if require_enabled:
            self._ensure_enabled()

        normalized_message: NsRuntimeMessage = self._prepare_message(message)
        return self._outbox.enqueue(normalized_message)

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
        return self.publish(message, require_enabled=require_enabled)

    def publish_on_commit(self, message: NsRuntimeMessage, *, require_enabled: bool = True) -> str:
        """Publish one runtime message after current Django transaction commits."""
        if require_enabled:
            self._ensure_enabled()

        normalized_message: NsRuntimeMessage = self._prepare_message(message)
        message_id = str(normalized_message.message_id or "")

        try:
            from django.db import transaction
        except Exception as exc:  # noqa
            raise NsRuntimePublishError("django transaction support is required for publish_on_commit") from exc

        transaction.on_commit(lambda: self.publish(normalized_message, require_enabled=require_enabled))
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
        return self.publish_on_commit(message, require_enabled=require_enabled)

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

    def _ensure_enabled(self) -> None:
        """Ensure runtime publishing is enabled."""
        if not self._config.enabled:
            raise NsRuntimePublishError("runtime publishing is disabled")
