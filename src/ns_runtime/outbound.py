# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import (
    datetime,
    timezone,
)
from typing import (
    Any,
    TYPE_CHECKING
)

from ns_common.exceptions import NsRuntimeTargetUnavailableError
from ns_runtime.delivery import RuntimeDeliveryRegistry
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
    delivery_id: str = ""
    attempt_id: str = ""
    delivery_state: str = ""
    ack_deadline_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = {
            "connection_id": self.connection_id,
            "connection_epoch": self.connection_epoch,
            "status": self.status,
        }

        if self.delivery_id:
            data["delivery_id"] = self.delivery_id
        if self.attempt_id:
            data["attempt_id"] = self.attempt_id
        if self.delivery_state:
            data["delivery_state"] = self.delivery_state
        if self.ack_deadline_at:
            data["ack_deadline_at"] = self.ack_deadline_at

        return data


@dataclass(slots=True, kw_only=True)
class RuntimeLocalRetryResult:
    delivery_id: str
    status: str
    delivery_state: str
    attempt_id: str = ""
    attempt: int = 0
    connection_id: str = ""
    connection_epoch: int = 0
    error_code: str = ""
    error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = {
            "delivery_id": self.delivery_id,
            "status": self.status,
            "delivery_state": self.delivery_state,
        }

        if self.attempt_id:
            data["attempt_id"] = self.attempt_id
        if self.attempt:
            data["attempt"] = self.attempt
        if self.connection_id:
            data["connection_id"] = self.connection_id
        if self.connection_epoch:
            data["connection_epoch"] = self.connection_epoch
        if self.error_code:
            data["error_code"] = self.error_code
        if self.error_message:
            data["error_message"] = self.error_message

        return data


@dataclass(slots=True, kw_only=True)
class RuntimeLocalRetryScanResult:
    scanned_count: int
    retried_count: int
    expired_count: int
    write_failed_count: int
    cache_missing_count: int
    retry_results: tuple[RuntimeLocalRetryResult, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "scanned_count": self.scanned_count,
            "retried_count": self.retried_count,
            "expired_count": self.expired_count,
            "write_failed_count": self.write_failed_count,
            "cache_missing_count": self.cache_missing_count,
            "retry_results": [
                result.to_dict()
                for result in self.retry_results
            ],
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
    def __init__(self, *, writer_registry: RuntimeConnectionWriterRegistry, delivery_registry: RuntimeDeliveryRegistry | None = None) -> None:
        self._writer_registry = writer_registry
        self._delivery_registry = delivery_registry
        self._retry_envelopes_by_delivery: dict[str, dict[str, Any]] = {}

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

        for target in writable_targets:
            results.append(
                await self._send_to_target(
                    decision=decision,
                    envelope=envelope,
                    target=target,
                )
            )

        return tuple(results)

    async def _send_to_target(self, *, decision: RuntimeRouteDecision, envelope: Envelope, target: RuntimeRouteTarget) -> RuntimeLocalWriteResult:
        if self._delivery_registry is None:
            return await self._writer_registry.send_to_connection(
                connection_id=target.connection_id,
                connection_epoch=target.connection_epoch,
                envelope=envelope.to_dict(),
            )

        record = self._delivery_registry.create_prepared_record(
            decision=decision,
            envelope=envelope,
            target=target,
        )
        self._retry_envelopes_by_delivery[record.delivery_id] = envelope.to_dict()
        attempt = self._delivery_registry.start_sending(record=record)
        envelope_data = self._delivery_registry.inject_delivery_group(
            envelope=envelope,
            record=record,
            attempt=attempt,
        )

        try:
            write_result = await self._writer_registry.send_to_connection(
                connection_id=target.connection_id,
                connection_epoch=target.connection_epoch,
                envelope=envelope_data,
            )
            self._delivery_registry.mark_sent_to_transport(
                record=record,
                attempt=attempt,
                write_result=write_result,
            )
            return RuntimeLocalWriteResult(
                connection_id=write_result.connection_id,
                connection_epoch=write_result.connection_epoch,
                status="sent_to_transport",
                delivery_id=record.delivery_id,
                attempt_id=attempt.attempt_id,
                delivery_state=record.state,
                ack_deadline_at=record.ack_deadline_at,
            )
        except Exception as exc:
            self._delivery_registry.mark_write_failed(
                record=record,
                attempt=attempt,
                exc=exc,
            )
            raise

    async def scan_retry_scheduled(self, *, now: datetime | None = None) -> RuntimeLocalRetryScanResult:
        if self._delivery_registry is None:
            return RuntimeLocalRetryScanResult(
                scanned_count=0,
                retried_count=0,
                expired_count=0,
                write_failed_count=0,
                cache_missing_count=0,
                retry_results=(),
            )

        resolved_now = now or datetime.now(timezone.utc)
        scanned_count = 0
        results: list[RuntimeLocalRetryResult] = []

        for record in self._delivery_registry.list_records():
            if record.state != "retry_scheduled":
                continue

            scanned_count += 1
            if self._record_is_expired(record.expires_at, resolved_now):
                record.state = "expired"
                record.updated_at = resolved_now.isoformat(timespec="milliseconds")
                record.last_error_code = "RUNTIME_DELIVERY_EXPIRED"
                record.last_error_message = "message_expired_before_retry"
                self._delivery_registry.refresh_message_summary_for_delivery(record.delivery_id)
                results.append(
                    RuntimeLocalRetryResult(
                        delivery_id=record.delivery_id,
                        status="expired",
                        delivery_state=record.state,
                        error_code=record.last_error_code,
                        error_message=record.last_error_message,
                    )
                )
                continue

            cached_envelope = self._retry_envelopes_by_delivery.get(record.delivery_id)
            if cached_envelope is None:
                record.last_error_code = "RUNTIME_RETRY_ENVELOPE_CACHE_MISSING"
                record.last_error_message = "retry_envelope_cache_missing"
                results.append(
                    RuntimeLocalRetryResult(
                        delivery_id=record.delivery_id,
                        status="retry_cache_missing",
                        delivery_state=record.state,
                        error_code=record.last_error_code,
                        error_message=record.last_error_message,
                    )
                )
                continue

            results.append(
                await self._retry_delivery(
                    record=record,
                    cached_envelope=cached_envelope,
                )
            )

        retried_count = sum(1 for result in results if result.status == "retried_to_transport")
        expired_count = sum(1 for result in results if result.status == "expired")
        write_failed_count = sum(1 for result in results if result.status == "retry_write_failed")
        cache_missing_count = sum(1 for result in results if result.status == "retry_cache_missing")

        return RuntimeLocalRetryScanResult(
            scanned_count=scanned_count,
            retried_count=retried_count,
            expired_count=expired_count,
            write_failed_count=write_failed_count,
            cache_missing_count=cache_missing_count,
            retry_results=tuple(results),
        )

    async def _retry_delivery(self, *, record, cached_envelope: dict[str, Any]) -> RuntimeLocalRetryResult:
        if self._delivery_registry is None:
            return RuntimeLocalRetryResult(
                delivery_id=record.delivery_id,
                status="retry_registry_unavailable",
                delivery_state=record.state,
                error_code="RUNTIME_DELIVERY_REGISTRY_UNAVAILABLE",
                error_message="delivery_registry_unavailable",
            )

        attempt = self._delivery_registry.start_sending(record=record)
        envelope_data = self._delivery_registry.inject_delivery_group(
            envelope=_CachedEnvelopeAdapter(cached_envelope),
            record=record,
            attempt=attempt,
        )

        try:
            write_result = await self._writer_registry.send_to_connection(
                connection_id=record.target_connection_id,
                connection_epoch=record.target_connection_epoch,
                envelope=envelope_data,
            )
            self._delivery_registry.mark_sent_to_transport(
                record=record,
                attempt=attempt,
                write_result=write_result,
            )
            return RuntimeLocalRetryResult(
                delivery_id=record.delivery_id,
                status="retried_to_transport",
                delivery_state=record.state,
                attempt_id=attempt.attempt_id,
                attempt=attempt.attempt,
                connection_id=write_result.connection_id,
                connection_epoch=write_result.connection_epoch,
            )
        except Exception as exc:
            self._delivery_registry.mark_write_failed(
                record=record,
                attempt=attempt,
                exc=exc,
            )
            return RuntimeLocalRetryResult(
                delivery_id=record.delivery_id,
                status="retry_write_failed",
                delivery_state=record.state,
                attempt_id=attempt.attempt_id,
                attempt=attempt.attempt,
                connection_id=record.target_connection_id,
                connection_epoch=record.target_connection_epoch,
                error_code=exc.__class__.__name__,
                error_message=str(exc),
            )

    @staticmethod
    def _record_is_expired(expires_at: str, now: datetime) -> bool:
        if not expires_at:
            return False

        try:
            parsed = datetime.fromisoformat(expires_at)
        except ValueError:
            return False

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed <= now


class _CachedEnvelopeAdapter:
    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    def to_dict(self) -> dict[str, Any]:
        return dict(self._data)
