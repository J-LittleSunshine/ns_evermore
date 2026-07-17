# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
import unittest
from collections.abc import Iterator, Mapping
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import ns_common
import ns_common.observability as observability_module
from ns_common.exceptions import NsStateError, NsValidationError
from ns_common.observability import (
    DiagnosticSnapshotSink,
    HIGH_CARDINALITY_METRIC_ATTRIBUTE_KEYS,
    InMemoryDiagnosticSnapshotSink,
    InMemoryMetricsSink,
    InMemoryTraceSink,
    MAX_METRIC_ATTRIBUTES,
    MAX_METRIC_ATTRIBUTE_VALUE_LENGTH,
    MAX_OBSERVABILITY_RECORD_BYTES,
    MetricsSink,
    NsDiagnosticSnapshot,
    NsMetricKind,
    NsMetricRecord,
    NsObservabilitySinkState,
    NsTraceRecord,
    NsTraceStatus,
    RUNTIME_EVENT_LOOP_METRIC_NAMES,
    RUNTIME_QUIC_METRIC_NAMES,
    RUNTIME_STANDARD_METRIC_NAMES,
    RUNTIME_TRANSPORT_METRIC_NAMES,
    TraceSink,
)
from ns_common.security import REDACTED, Sanitizer


UTC_START = datetime(2026, 7, 17, 8, 0, tzinfo=timezone.utc)


class ExplodingMapping(Mapping[str, object]):
    def __getitem__(self, key: str) -> object:
        raise RuntimeError(f"mapping-get-secret-{key}")

    def __iter__(self) -> Iterator[str]:
        return iter(("secret",))

    def __len__(self) -> int:
        return 1

    def items(self):  # type: ignore[no-untyped-def]
        raise RuntimeError("mapping-items-secret")


class InterruptingSanitizer(Sanitizer):
    def sanitize(self, *args: object, **kwargs: object) -> object:
        del args, kwargs
        raise KeyboardInterrupt("observability-interrupt-secret")


class ObservabilityRecordTestCase(unittest.TestCase):
    def assert_json_safe_and_no_leak(
        self,
        value: object,
        *secrets: str,
    ) -> str:
        encoded = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            sort_keys=True,
        )
        for secret in secrets:
            with self.subTest(secret=secret):
                self.assertNotIn(secret, encoded)
        return encoded

    @staticmethod
    def make_metric(
        name: str = "runtime_pending_task_count",
    ) -> NsMetricRecord:
        return NsMetricRecord(
            name=name,
            kind=NsMetricKind.GAUGE,
            value=1,
            observed_at=UTC_START,
            attributes={"component_type": "runtime"},
        )

    def test_public_aliases_and_protocols_are_available_from_facade(self) -> None:
        expected_objects = {
            "MetricsSink": MetricsSink,
            "TraceSink": TraceSink,
            "DiagnosticSnapshotSink": DiagnosticSnapshotSink,
            "NsMetricRecord": NsMetricRecord,
            "NsTraceRecord": NsTraceRecord,
            "NsDiagnosticSnapshot": NsDiagnosticSnapshot,
            "InMemoryMetricsSink": InMemoryMetricsSink,
            "InMemoryTraceSink": InMemoryTraceSink,
            "InMemoryDiagnosticSnapshotSink": InMemoryDiagnosticSnapshotSink,
        }
        for name, expected in expected_objects.items():
            with self.subTest(name=name):
                self.assertIs(expected, getattr(ns_common, name))
                self.assertIn(name, ns_common.__all__)

        self.assertIsInstance(InMemoryMetricsSink(), MetricsSink)
        self.assertIsInstance(InMemoryTraceSink(), TraceSink)
        self.assertIsInstance(
            InMemoryDiagnosticSnapshotSink(),
            DiagnosticSnapshotSink,
        )

    def test_standard_metric_names_are_exact_unique_and_reserved(self) -> None:
        self.assertEqual(
            (
                "runtime_event_loop_implementation",
                "runtime_event_loop_lag_ms",
                "runtime_event_loop_lag_p95_ms",
                "runtime_event_loop_lag_p99_ms",
                "runtime_slow_callback_total",
                "runtime_pending_task_count",
                "runtime_cancelled_task_total",
                "runtime_executor_queue_depth",
            ),
            RUNTIME_EVENT_LOOP_METRIC_NAMES,
        )
        self.assertEqual(
            (
                "runtime_transport_connections",
                "runtime_transport_handshake_duration_ms",
                "runtime_transport_bytes_received_total",
                "runtime_transport_bytes_sent_total",
                "runtime_transport_receive_errors_total",
                "runtime_transport_send_errors_total",
                "runtime_transport_close_total",
                "runtime_transport_backpressure_duration_ms",
                "runtime_transport_read_queue_depth",
                "runtime_transport_write_queue_depth",
            ),
            RUNTIME_TRANSPORT_METRIC_NAMES,
        )
        self.assertEqual(
            (
                "runtime_transport_rtt_ms",
                "runtime_transport_smoothed_rtt_ms",
                "runtime_transport_packet_loss_ratio",
                "runtime_transport_bytes_in_flight",
                "runtime_transport_congestion_window_bytes",
                "runtime_transport_flow_control_blocked_duration_ms",
                "runtime_transport_streams_active",
                "runtime_transport_streams_blocked",
                "runtime_transport_path_migration_total",
                "runtime_transport_path_migration_success_total",
                "runtime_transport_path_migration_failed_total",
                "runtime_transport_path_validation_duration_ms",
                "runtime_transport_datagrams_sent_total",
                "runtime_transport_datagrams_received_total",
                "runtime_transport_datagrams_dropped_total",
                "runtime_transport_zero_rtt_attempt_total",
                "runtime_transport_zero_rtt_rejected_total",
            ),
            RUNTIME_QUIC_METRIC_NAMES,
        )
        combined = (
            RUNTIME_EVENT_LOOP_METRIC_NAMES
            + RUNTIME_TRANSPORT_METRIC_NAMES
            + RUNTIME_QUIC_METRIC_NAMES
        )
        self.assertEqual(35, len(combined))
        self.assertEqual(35, len(set(combined)))
        self.assertEqual(frozenset(combined), RUNTIME_STANDARD_METRIC_NAMES)
        self.assertTrue(
            all(name.startswith("runtime_") for name in combined)
        )

    def test_metric_record_is_utc_immutable_sanitized_and_json_safe(self) -> None:
        token = "metric-token-secret"
        bearer = "metric-bearer-secret"
        raw_attributes: dict[str, object] = {
            "component_type": "runtime",
            "transport_type": f"Bearer {bearer}",
            "token": token,
            "tenant_scope": "paid_tenants",
            "sampled": True,
        }
        record = NsMetricRecord(
            name="runtime_transport_connections",
            kind=NsMetricKind.GAUGE,
            value=3,
            observed_at=datetime(
                2026,
                7,
                17,
                16,
                0,
                tzinfo=timezone(timedelta(hours=8)),
            ),
            unit="connections",
            attributes=raw_attributes,
        )
        raw_attributes["component_type"] = "mutated"

        self.assertEqual(3.0, record.value)
        self.assertIs(timezone.utc, record.observed_at.tzinfo)
        self.assertEqual("runtime", record.attributes["component_type"])
        self.assertEqual(REDACTED, record.attributes["token"])
        with self.assertRaises(TypeError):
            record.attributes["new"] = "value"  # type: ignore[index]
        self.assert_json_safe_and_no_leak(record.to_dict(), token, bearer)

    def test_metric_record_enforces_value_and_cardinality_boundaries(self) -> None:
        forbidden_variants = (
            "connection_id",
            "Connection-ID",
            "message.id",
            "tenant-id",
            "TRACE_ID",
        )
        for key in forbidden_variants:
            with self.subTest(key=key):
                with self.assertRaises(NsValidationError):
                    NsMetricRecord(
                        name="runtime_test_metric",
                        kind=NsMetricKind.GAUGE,
                        value=1,
                        observed_at=UTC_START,
                        attributes={key: "high-cardinality-value"},
                    )

        invalid_cases = (
            {"name": "metric with spaces"},
            {"kind": "gauge"},
            {"value": True},
            {"value": float("nan")},
            {"observed_at": datetime(2026, 7, 17)},
            {"attributes": {"nested": {"value": 1}}},
            {"attributes": {"label": "x" * (MAX_METRIC_ATTRIBUTE_VALUE_LENGTH + 1)}},
            {"attributes": {f"label_{index}": index for index in range(MAX_METRIC_ATTRIBUTES + 1)}},
        )
        defaults: dict[str, object] = {
            "name": "runtime_test_metric",
            "kind": NsMetricKind.GAUGE,
            "value": 1,
            "observed_at": UTC_START,
            "attributes": {},
        }
        for overrides in invalid_cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises(NsValidationError):
                    NsMetricRecord(**(defaults | overrides))  # type: ignore[arg-type]

        with self.assertRaises(NsValidationError):
            NsMetricRecord(
                name="runtime_test_counter",
                kind=NsMetricKind.COUNTER,
                value=-1,
                observed_at=UTC_START,
            )

        self.assertIn("connection_id", HIGH_CARDINALITY_METRIC_ATTRIBUTE_KEYS)
        self.assertNotIn("runtime_id", HIGH_CARDINALITY_METRIC_ATTRIBUTE_KEYS)

    def test_trace_record_preserves_trace_context_and_sanitizes_attributes(self) -> None:
        token = "trace-token-secret"
        payload = "trace-payload-secret"
        attributes: dict[str, object] = {
            "connection_id": "connection_safe_for_trace",
            "authorization": token,
            "payload": {"body": payload},
            "nested": {"values": [1, 2]},
        }
        record = NsTraceRecord(
            name="processor.execute",
            started_at=UTC_START,
            status=NsTraceStatus.OK,
            duration_ms=2.5,
            trace_id="trace-safe",
            span_id="span-safe",
            parent_span_id="span-parent-safe",
            correlation_id="correlation-safe",
            request_id="request-safe",
            attributes=attributes,
        )
        attributes["connection_id"] = "mutated"
        nested = attributes["nested"]
        assert isinstance(nested, dict)
        nested["values"] = [99]

        self.assertEqual(
            "connection_safe_for_trace",
            record.attributes["connection_id"],
        )
        self.assertEqual(REDACTED, record.attributes["authorization"])
        self.assertEqual(REDACTED, record.attributes["payload"])
        frozen_nested = record.attributes["nested"]
        self.assertIsInstance(frozen_nested, Mapping)
        assert isinstance(frozen_nested, Mapping)
        self.assertEqual((1, 2), frozen_nested["values"])
        with self.assertRaises(TypeError):
            frozen_nested["new"] = "value"  # type: ignore[index]
        self.assert_json_safe_and_no_leak(record.to_dict(), token, payload)

    def test_trace_record_validates_context_relationships_and_duration(self) -> None:
        invalid_cases = (
            {"status": "ok"},
            {"duration_ms": -0.1},
            {"duration_ms": float("inf")},
            {"span_id": "span-without-trace"},
            {"trace_id": "trace", "parent_span_id": "parent-without-span"},
        )
        for overrides in invalid_cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises(NsValidationError):
                    NsTraceRecord(
                        name="trace.test",
                        started_at=UTC_START,
                        **overrides,  # type: ignore[arg-type]
                    )

    def test_diagnostic_snapshot_is_detached_sanitized_and_bounded(self) -> None:
        token = "snapshot-token-secret"
        payload = "snapshot-payload-secret"
        raw_snapshot: dict[str, object] = {
            "runtime_id": "runtime-safe",
            "token": token,
            "payload": {"body": payload},
            "queues": {"pending": [1, 2]},
        }
        record = NsDiagnosticSnapshot(
            name="runtime.health",
            captured_at=UTC_START,
            snapshot=raw_snapshot,
        )
        raw_snapshot["runtime_id"] = "mutated"

        self.assertEqual("runtime-safe", record.snapshot["runtime_id"])
        self.assertEqual(REDACTED, record.snapshot["token"])
        self.assertEqual(REDACTED, record.snapshot["payload"])
        with self.assertRaises(TypeError):
            record.snapshot["new"] = "value"  # type: ignore[index]
        self.assert_json_safe_and_no_leak(record.to_dict(), token, payload)

        oversized = NsDiagnosticSnapshot(
            name="runtime.oversized",
            captured_at=UTC_START,
            snapshot={"details": "x" * (MAX_OBSERVABILITY_RECORD_BYTES + 1)},
        )
        self.assertEqual(
            {"observability_status": "size_limit_exceeded"},
            dict(oversized.snapshot),
        )

    def test_structured_sanitization_fails_closed_but_preserves_interrupts(self) -> None:
        failed = NsDiagnosticSnapshot(
            name="runtime.failed_snapshot",
            captured_at=UTC_START,
            snapshot=ExplodingMapping(),
        )
        encoded = self.assert_json_safe_and_no_leak(
            failed.to_dict(),
            "mapping-items-secret",
            "mapping-get-secret",
        )
        self.assertIn("sanitization_failed", encoded)

        with self.assertRaises(KeyboardInterrupt):
            NsDiagnosticSnapshot(
                name="runtime.interrupted_snapshot",
                captured_at=UTC_START,
                snapshot={"safe": True},
                sanitizer=InterruptingSanitizer(),
            )

    def test_observability_module_has_no_exporter_or_runtime_dependency(self) -> None:
        source_path = Path(observability_module.__file__).resolve()
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        imported_roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(
                    alias.name.partition(".")[0]
                    for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.partition(".")[0])

        self.assertTrue(
            imported_roots.isdisjoint(
                {"aiohttp", "httpx", "requests", "ns_runtime"}
            )
        )


class InMemorySinkTestCase(unittest.TestCase):
    @staticmethod
    def make_metric(name: str) -> NsMetricRecord:
        return NsMetricRecord(
            name=name,
            kind=NsMetricKind.GAUGE,
            value=1,
            observed_at=UTC_START,
        )

    def test_bounded_sink_drops_oldest_and_clear_resets_test_state(self) -> None:
        sink = InMemoryMetricsSink(capacity=2)
        first = self.make_metric("runtime_first")
        second = self.make_metric("runtime_second")
        third = self.make_metric("runtime_third")

        self.assertTrue(sink.record(first))
        self.assertTrue(sink.record(second))
        self.assertTrue(sink.record(third))
        self.assertEqual((second, third), sink.records)
        self.assertEqual(1, sink.dropped_count)

        self.assertEqual(2, sink.clear())
        self.assertEqual((), sink.records)
        self.assertEqual(0, sink.dropped_count)

    def test_sink_capacity_type_and_record_type_are_strict(self) -> None:
        for capacity in (0, -1, True, 1.5):
            with self.subTest(capacity=capacity):
                with self.assertRaises(NsValidationError):
                    InMemoryMetricsSink(capacity=capacity)  # type: ignore[arg-type]

        sink = InMemoryMetricsSink()
        trace = NsTraceRecord(name="trace", started_at=UTC_START)
        with self.assertRaises(NsValidationError):
            sink.record(trace)  # type: ignore[arg-type]

    def test_concurrent_recording_is_bounded_and_counts_drops(self) -> None:
        sink = InMemoryMetricsSink(capacity=100)
        record = self.make_metric("runtime_concurrent")

        with ThreadPoolExecutor(max_workers=8) as executor:
            accepted = tuple(executor.map(sink.record, (record,) * 250))

        self.assertTrue(all(accepted))
        self.assertEqual(100, len(sink.records))
        self.assertEqual(150, sink.dropped_count)


class InMemorySinkLifecycleTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_all_memory_sinks_flush_and_close_idempotently(self) -> None:
        metric_sink = InMemoryMetricsSink()
        trace_sink = InMemoryTraceSink()
        snapshot_sink = InMemoryDiagnosticSnapshotSink()

        metric = NsMetricRecord(
            name="runtime_pending_task_count",
            kind=NsMetricKind.GAUGE,
            value=1,
            observed_at=UTC_START,
        )
        trace = NsTraceRecord(name="runtime.start", started_at=UTC_START)
        snapshot = NsDiagnosticSnapshot(
            name="runtime.start",
            captured_at=UTC_START,
            snapshot={"state": "starting"},
        )

        for sink, record in (
            (metric_sink, metric),
            (trace_sink, trace),
            (snapshot_sink, snapshot),
        ):
            with self.subTest(sink=type(sink).__name__):
                self.assertTrue(sink.record(record))  # type: ignore[arg-type]
                await sink.flush()
                await sink.aclose()
                await sink.aclose()
                await sink.flush()
                self.assertTrue(sink.is_closed)
                self.assertIs(
                    NsObservabilitySinkState.CLOSED,
                    sink.state,
                )
                self.assertEqual((record,), sink.records)
                with self.assertRaises(NsStateError):
                    sink.record(record)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
