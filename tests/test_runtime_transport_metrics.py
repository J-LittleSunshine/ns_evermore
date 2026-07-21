# -*- coding: utf-8 -*-
from __future__ import annotations

import unittest

from ns_common.observability import (
    InMemoryMetricsSink,
    RUNTIME_TRANSPORT_METRIC_NAMES,
)
from ns_common.time import ControlledClock
from ns_runtime.transport import (
    TransportCloseReason,
    TransportMetricsRecorder,
)


class _FailingMetricsSink:
    def __init__(self, *, returns: bool | None = None) -> None:
        self.returns = returns

    def record(self, _record: object) -> bool:
        if self.returns is not None:
            return self.returns
        raise RuntimeError("metric sink credential must not escape")

    async def flush(self) -> None:
        return None

    async def aclose(self) -> None:
        return None


class TransportMetricsTestCase(unittest.TestCase):
    def test_all_standard_transport_metrics_use_only_finite_attributes(self) -> None:
        clock = ControlledClock()
        sink = InMemoryMetricsSink(capacity=64)
        recorder = TransportMetricsRecorder(clock=clock, sink=sink)

        recorder.connection_opened()
        recorder.handshake_completed(1.5)
        recorder.bytes_received(10)
        recorder.bytes_sent(11)
        recorder.receive_error("RUNTIME_TRANSPORT_RECEIVE_FAILED")
        recorder.send_error("RUNTIME_TRANSPORT_SEND_FAILED")
        recorder.backpressure(2.5)
        recorder.read_queue_depth(1)
        recorder.write_queue_depth(2)
        recorder.connection_closed(TransportCloseReason.REMOTE_CLOSED)

        self.assertEqual(set(RUNTIME_TRANSPORT_METRIC_NAMES), {
            record.name for record in sink.records
        })
        forbidden = {
            "connection_id", "session_id", "peer", "path", "message_id",
            "tenant_id", "exception", "transport_connection_id",
            "transport_session_id", "transport_stream_id",
        }
        for record in sink.records:
            self.assertFalse(forbidden.intersection(record.attributes))
            self.assertLessEqual(
                set(record.attributes),
                {
                    "close_reason",
                    "component_type",
                    "error_code",
                    "tenant_scope",
                    "transport_type",
                },
            )
        close_record = next(
            item for item in sink.records
            if item.name == "runtime_transport_close_total"
        )
        self.assertEqual("remote_closed", close_record.attributes["close_reason"])

    def test_sink_failure_and_rejection_are_fail_soft(self) -> None:
        clock = ControlledClock()
        raising = TransportMetricsRecorder(
            clock=clock,
            sink=_FailingMetricsSink(),
        )
        rejecting = TransportMetricsRecorder(
            clock=clock,
            sink=_FailingMetricsSink(returns=False),
        )

        raising.bytes_sent(1)
        rejecting.bytes_received(1)
        self.assertEqual(1, raising.rejection_count)
        self.assertEqual(1, rejecting.rejection_count)

