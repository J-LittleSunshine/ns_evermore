# -*- coding: utf-8 -*-
"""Low-cardinality fail-soft transport metrics over OBS-1 sinks."""

from __future__ import annotations

from threading import Lock

from ns_common.exceptions import NsValidationError
from ns_common.observability import (
    MetricsSink,
    NsMetricKind,
    NsMetricRecord,
)
from ns_common.time import Clock

from .models import TransportCloseReason


class TransportMetricsRecorder:
    def __init__(self, *, clock: Clock, sink: MetricsSink) -> None:
        if not isinstance(clock, Clock):
            raise NsValidationError(
                "Transport metrics clock is invalid.",
                details={"component": "transport_metrics", "field": "clock"},
            )
        if not isinstance(sink, MetricsSink):
            raise NsValidationError(
                "Transport metrics sink is invalid.",
                details={"component": "transport_metrics", "field": "sink"},
            )
        self._clock = clock
        self._sink = sink
        self._connection_count = 0
        self._rejection_count = 0
        self._lock = Lock()

    @property
    def rejection_count(self) -> int:
        with self._lock:
            return self._rejection_count

    def connection_opened(self) -> None:
        with self._lock:
            self._connection_count += 1
            value = self._connection_count
        self._record(
            "runtime_transport_connections",
            NsMetricKind.GAUGE,
            value,
            attributes={
                "component_type": "runtime",
                "tenant_scope": "unknown",
                "transport_type": "websocket_tcp",
            },
        )

    def connection_closed(self, reason: TransportCloseReason) -> None:
        if not isinstance(reason, TransportCloseReason):
            raise NsValidationError(
                "Transport close metric reason is invalid.",
                details={"component": "transport_metrics", "field": "close_reason"},
            )
        with self._lock:
            self._connection_count = max(0, self._connection_count - 1)
            value = self._connection_count
        self._record(
            "runtime_transport_connections",
            NsMetricKind.GAUGE,
            value,
            attributes={
                "component_type": "runtime",
                "tenant_scope": "unknown",
                "transport_type": "websocket_tcp",
            },
        )
        self._record(
            "runtime_transport_close_total",
            NsMetricKind.COUNTER,
            1,
            attributes={
                "close_reason": reason.value,
                "transport_type": "websocket_tcp",
            },
        )

    def handshake_completed(self, duration_ms: float) -> None:
        self._record(
            "runtime_transport_handshake_duration_ms",
            NsMetricKind.HISTOGRAM,
            duration_ms,
            unit="ms",
        )

    def bytes_received(self, byte_count: int) -> None:
        self._record(
            "runtime_transport_bytes_received_total",
            NsMetricKind.COUNTER,
            byte_count,
            unit="By",
        )

    def bytes_sent(self, byte_count: int) -> None:
        self._record(
            "runtime_transport_bytes_sent_total",
            NsMetricKind.COUNTER,
            byte_count,
            unit="By",
        )

    def receive_error(self, error_code: str) -> None:
        self._error_metric("runtime_transport_receive_errors_total", error_code)

    def send_error(self, error_code: str) -> None:
        self._error_metric("runtime_transport_send_errors_total", error_code)

    def backpressure(self, duration_ms: float) -> None:
        self._record(
            "runtime_transport_backpressure_duration_ms",
            NsMetricKind.HISTOGRAM,
            duration_ms,
            unit="ms",
        )

    def read_queue_depth(self, depth: int) -> None:
        self._queue_depth("runtime_transport_read_queue_depth", depth)

    def write_queue_depth(self, depth: int) -> None:
        self._queue_depth("runtime_transport_write_queue_depth", depth)

    def _error_metric(self, name: str, error_code: str) -> None:
        self._record(
            name,
            NsMetricKind.COUNTER,
            1,
            attributes={
                "error_code": error_code,
                "transport_type": "websocket_tcp",
            },
        )

    def _queue_depth(self, name: str, depth: int) -> None:
        self._record(name, NsMetricKind.GAUGE, depth)

    def _record(
        self,
        name: str,
        kind: NsMetricKind,
        value: int | float,
        *,
        unit: str | None = None,
        attributes: dict[str, object] | None = None,
    ) -> None:
        safe_attributes = (
            {"transport_type": "websocket_tcp"}
            if attributes is None
            else attributes
        )
        try:
            accepted = self._sink.record(NsMetricRecord(
                name=name,
                kind=kind,
                value=float(value),
                observed_at=self._clock.utc_now(),
                unit=unit,
                attributes=safe_attributes,
            ))
        except Exception:
            accepted = False
        if not accepted:
            with self._lock:
                self._rejection_count += 1


__all__ = ("TransportMetricsRecorder",)

