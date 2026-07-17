# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import asyncio
import json
import unittest
from collections.abc import Iterator, Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Barrier
from types import MappingProxyType
from unittest.mock import patch
from uuid import uuid4

import ns_common
import ns_common.observability as observability_module
from ns_common.exceptions import NsValidationError
from ns_common.observability import (
    DiagnosticSnapshotSink,
    HIGH_CARDINALITY_METRIC_ATTRIBUTE_KEYS,
    InMemoryDiagnosticSnapshotSink,
    InMemoryMetricsSink,
    InMemoryTraceSink,
    MAX_METRIC_ATTRIBUTES,
    MAX_METRIC_ATTRIBUTE_VALUE_LENGTH,
    MAX_OBSERVABILITY_RECORD_BYTES,
    MetricAttributeDefinition,
    MetricAttributeValueType,
    MetricDefinition,
    MetricTenantScope,
    MetricsSink,
    NsDiagnosticSnapshot,
    NsMetricAttributeDefinition,
    NsMetricAttributeValueType,
    NsMetricDefinition,
    NsMetricKind,
    NsMetricRecord,
    NsMetricTenantScope,
    NsObservabilitySinkState,
    NsTraceRecord,
    NsTraceStatus,
    RUNTIME_EVENT_LOOP_METRIC_NAMES,
    RUNTIME_QUIC_METRIC_NAMES,
    RUNTIME_STANDARD_METRIC_DEFINITIONS,
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


class ExitingSanitizer(Sanitizer):
    def sanitize(self, *args: object, **kwargs: object) -> object:
        del args, kwargs
        raise SystemExit("observability-system-exit-secret")


class FailingSanitizer(Sanitizer):
    def sanitize(self, *args: object, **kwargs: object) -> object:
        del args, kwargs
        raise RuntimeError("observability-sanitizer-failure-secret")


class SchemaBreakingSanitizer(Sanitizer):
    def sanitize(self, *args: object, **kwargs: object) -> object:
        del args, kwargs
        return {"mode": "unexpected"}


class DuplicateItemsMapping(Mapping[str, NsMetricAttributeDefinition]):
    def __init__(self, definition: NsMetricAttributeDefinition) -> None:
        self._definition = definition

    def __getitem__(self, key: str) -> NsMetricAttributeDefinition:
        if key != self._definition.key:
            raise KeyError(key)
        return self._definition

    def __iter__(self) -> Iterator[str]:
        return iter((self._definition.key,))

    def __len__(self) -> int:
        return 1

    def items(self):  # type: ignore[no-untyped-def]
        return (
            (self._definition.key, self._definition),
            (self._definition.key, self._definition),
        )


def strict_record_bytes(value: Mapping[str, object]) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


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
            "NsMetricAttributeDefinition": NsMetricAttributeDefinition,
            "NsMetricAttributeValueType": NsMetricAttributeValueType,
            "NsMetricDefinition": NsMetricDefinition,
            "NsMetricTenantScope": NsMetricTenantScope,
            "RUNTIME_STANDARD_METRIC_DEFINITIONS": (
                RUNTIME_STANDARD_METRIC_DEFINITIONS
            ),
        }
        for name, expected in expected_objects.items():
            with self.subTest(name=name):
                self.assertIs(expected, getattr(ns_common, name))
                self.assertIn(name, ns_common.__all__)

        alias_pairs = (
            (MetricAttributeDefinition, NsMetricAttributeDefinition),
            (MetricAttributeValueType, NsMetricAttributeValueType),
            (MetricDefinition, NsMetricDefinition),
            (MetricTenantScope, NsMetricTenantScope),
        )
        for plain_alias, ns_alias in alias_pairs:
            self.assertIs(plain_alias, ns_alias)
        self.assertEqual(len(ns_common.__all__), len(set(ns_common.__all__)))
        self.assertEqual(
            len(observability_module.__all__),
            len(set(observability_module.__all__)),
        )

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
        self.assertEqual(35, len(RUNTIME_STANDARD_METRIC_DEFINITIONS))
        self.assertEqual(
            RUNTIME_STANDARD_METRIC_NAMES,
            frozenset(RUNTIME_STANDARD_METRIC_DEFINITIONS),
        )
        for name, definition in RUNTIME_STANDARD_METRIC_DEFINITIONS.items():
            with self.subTest(name=name):
                self.assertEqual(name, definition.name)
                self.assertIsInstance(definition.allowed_attributes, Mapping)
                self.assertNotIn("*", definition.allowed_attributes)
                for key, attribute in definition.allowed_attributes.items():
                    self.assertEqual(key, attribute.key)
                    self.assertTrue(attribute.is_finite_enum)
                    self.assertIsInstance(attribute.allowed_values, frozenset)
                    self.assertTrue(attribute.allowed_values)

        with self.assertRaises(TypeError):
            RUNTIME_STANDARD_METRIC_DEFINITIONS["runtime_new"] = (  # type: ignore[index]
                RUNTIME_STANDARD_METRIC_DEFINITIONS[
                    "runtime_pending_task_count"
                ]
            )
        standard_definition = RUNTIME_STANDARD_METRIC_DEFINITIONS[
            "runtime_transport_connections"
        ]
        with self.assertRaises(FrozenInstanceError):
            standard_definition.name = "runtime_mutated"  # type: ignore[misc]
        with self.assertRaises(TypeError):
            standard_definition.allowed_attributes["wildcard"] = (  # type: ignore[index]
                standard_definition.allowed_attributes["transport_type"]
            )
        transport_attribute = standard_definition.allowed_attributes[
            "transport_type"
        ]
        with self.assertRaises(FrozenInstanceError):
            transport_attribute.key = "mutated"  # type: ignore[misc]

    def test_metric_record_is_utc_immutable_sanitized_and_json_safe(self) -> None:
        raw_attributes: dict[str, object] = {
            "component_type": "runtime",
            "transport_type": "websocket_tcp",
            "tenant_scope": "system",
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
        self.assertEqual("system", record.attributes["tenant_scope"])
        self.assertIs(
            RUNTIME_STANDARD_METRIC_DEFINITIONS[
                "runtime_transport_connections"
            ],
            record.definition,
        )
        with self.assertRaises(TypeError):
            record.attributes["new"] = "value"  # type: ignore[index]
        self.assert_json_safe_and_no_leak(record.to_dict())

    def test_metric_record_enforces_value_and_cardinality_boundaries(self) -> None:
        forbidden_variants = (
            "connection_id",
            "Connection-ID",
            "target_connection_id",
            "current_session_id",
            "source_message_id",
            "original_delivery_id",
            "customer_tenant_id",
            "worker_trace_id",
            "peer_request_id",
            "transport.connection.id",
        )
        for key in forbidden_variants:
            with self.subTest(key=key):
                with self.assertRaises(NsValidationError):
                    NsMetricRecord(
                        name="runtime_transport_connections",
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

        identity_attribute = NsMetricAttributeDefinition(
            key="identity",
            value_type=NsMetricAttributeValueType.STRING,
            allowed_values=frozenset({"aggregate"}),
        )
        identity_definition = NsMetricDefinition(
            name="runtime_identity_aggregate",
            allowed_attributes={"identity": identity_attribute},
        )
        identity_record = NsMetricRecord(
            name=identity_definition.name,
            kind=NsMetricKind.GAUGE,
            value=1,
            observed_at=UTC_START,
            attributes={"identity": "aggregate"},
            definition=identity_definition,
        )
        self.assertEqual("aggregate", identity_record.attributes["identity"])

    def test_metric_definition_model_requires_immutable_finite_domains(self) -> None:
        boolean_attribute = NsMetricAttributeDefinition(
            key="sampled",
            value_type=NsMetricAttributeValueType.BOOLEAN,
        )
        self.assertEqual(
            frozenset({False, True}),
            boolean_attribute.allowed_values,
        )
        self.assertTrue(boolean_attribute.is_finite_enum)

        for kwargs in (
            {
                "key": "mode",
                "value_type": NsMetricAttributeValueType.STRING,
            },
            {
                "key": "code",
                "value_type": NsMetricAttributeValueType.INTEGER,
                "allowed_values": frozenset(),
            },
            {
                "key": "target_connection_id",
                "value_type": NsMetricAttributeValueType.STRING,
                "allowed_values": frozenset({"fixed"}),
            },
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(NsValidationError):
                    NsMetricAttributeDefinition(**kwargs)  # type: ignore[arg-type]

        mode_attribute = NsMetricAttributeDefinition(
            key="mode",
            value_type=NsMetricAttributeValueType.STRING,
            allowed_values=frozenset({"ready", "busy"}),
        )
        definition = NsMetricDefinition(
            name="runtime_custom_state",
            allowed_attributes={"mode": mode_attribute},
        )
        self.assertIsInstance(definition.allowed_attributes, MappingProxyType)
        self.assertIs(mode_attribute, definition.allowed_attributes["mode"])
        with self.assertRaises(NsValidationError):
            NsMetricDefinition(
                name="runtime_custom_state",
                allowed_attributes={"other": mode_attribute},
            )
        with self.assertRaises(NsValidationError):
            NsMetricDefinition(
                name="runtime_custom_state",
                allowed_attributes=DuplicateItemsMapping(mode_attribute),
            )

    def test_metric_attributes_require_explicit_finite_schema(self) -> None:
        mode_attribute = NsMetricAttributeDefinition(
            key="mode",
            value_type=NsMetricAttributeValueType.STRING,
            allowed_values=frozenset({"ready", "busy"}),
        )
        code_attribute = NsMetricAttributeDefinition(
            key="status_code",
            value_type=NsMetricAttributeValueType.INTEGER,
            allowed_values=frozenset({200, 503}),
        )
        sampled_attribute = NsMetricAttributeDefinition(
            key="sampled",
            value_type=NsMetricAttributeValueType.BOOLEAN,
        )
        definition = NsMetricDefinition(
            name="runtime_custom_state",
            allowed_attributes={
                "mode": mode_attribute,
                "sampled": sampled_attribute,
                "status_code": code_attribute,
            },
        )
        record = NsMetricRecord(
            name=definition.name,
            kind=NsMetricKind.GAUGE,
            value=2,
            observed_at=UTC_START,
            attributes={
                "mode": "ready",
                "sampled": True,
                "status_code": 200,
            },
            definition=definition,
        )
        self.assertEqual("ready", record.attributes["mode"])
        self.assertIs(True, record.attributes["sampled"])
        self.assertEqual(200, record.attributes["status_code"])

        for attributes in (
            {"mode": "unregistered"},
            {"status_code": 201},
            {"sampled": 1.0},
            {"mode": {"nested": "value"}},
            {"mode": ["ready"]},
        ):
            with self.subTest(attributes=attributes):
                with self.assertRaises(NsValidationError):
                    NsMetricRecord(
                        name=definition.name,
                        kind=NsMetricKind.GAUGE,
                        value=1,
                        observed_at=UTC_START,
                        attributes=attributes,
                        definition=definition,
                    )

        empty_custom = NsMetricRecord(
            name="runtime_custom_without_attributes",
            kind=NsMetricKind.GAUGE,
            value=1,
            observed_at=UTC_START,
        )
        self.assertEqual({}, empty_custom.to_dict()["attributes"])
        self.assertIsNone(empty_custom.definition)
        with self.assertRaises(NsValidationError):
            NsMetricRecord(
                name="runtime_custom_without_definition",
                kind=NsMetricKind.GAUGE,
                value=1,
                observed_at=UTC_START,
                attributes={"mode": "ready"},
            )
        with self.assertRaises(NsValidationError):
            NsMetricRecord(
                name="runtime_definition_name_mismatch",
                kind=NsMetricKind.GAUGE,
                value=1,
                observed_at=UTC_START,
                definition=definition,
            )

    def test_tenant_scope_is_a_finite_classification_not_a_tenant_id(self) -> None:
        self.assertEqual(
            {
                "cross_tenant",
                "shared",
                "system",
                "tenant",
                "unknown",
            },
            {item.value for item in NsMetricTenantScope},
        )
        record = NsMetricRecord(
            name="runtime_transport_connections",
            kind=NsMetricKind.GAUGE,
            value=1,
            observed_at=UTC_START,
            attributes={"tenant_scope": "system"},
        )
        self.assertEqual("system", record.attributes["tenant_scope"])

        invalid_scopes = (
            "tenant_5f598c0f-e8cd-4b93-b460-092e1bcb5440",
            "customer@example.com",
            str(uuid4()),
        )
        for tenant_scope in invalid_scopes:
            with self.subTest(tenant_scope=tenant_scope):
                with self.assertRaises(NsValidationError):
                    NsMetricRecord(
                        name="runtime_transport_connections",
                        kind=NsMetricKind.GAUGE,
                        value=1,
                        observed_at=UTC_START,
                        attributes={"tenant_scope": tenant_scope},
                    )

    def test_metric_schema_is_rechecked_after_sanitization(self) -> None:
        definition = NsMetricDefinition(
            name="runtime_sanitized_metric",
            allowed_attributes={
                "mode": NsMetricAttributeDefinition(
                    key="mode",
                    value_type=NsMetricAttributeValueType.STRING,
                    allowed_values=frozenset({"ready"}),
                ),
            },
        )
        with self.assertRaises(NsValidationError):
            NsMetricRecord(
                name=definition.name,
                kind=NsMetricKind.GAUGE,
                value=1,
                observed_at=UTC_START,
                attributes={"mode": "ready"},
                definition=definition,
                sanitizer=SchemaBreakingSanitizer(),
            )

        bearer = "metric-schema-bearer-secret"
        authorization_definition = NsMetricDefinition(
            name="runtime_authorization_metric",
            allowed_attributes={
                "authorization": NsMetricAttributeDefinition(
                    key="authorization",
                    value_type=NsMetricAttributeValueType.STRING,
                    allowed_values=frozenset({f"Bearer {bearer}"}),
                ),
            },
        )
        with self.assertRaises(NsValidationError) as raised:
            NsMetricRecord(
                name=authorization_definition.name,
                kind=NsMetricKind.GAUGE,
                value=1,
                observed_at=UTC_START,
                attributes={"authorization": f"Bearer {bearer}"},
                definition=authorization_definition,
            )
        self.assertNotIn(bearer, str(raised.exception))
        self.assertNotIn(bearer, json.dumps(raised.exception.details))

        with self.assertRaises(NsValidationError) as failed:
            NsMetricRecord(
                name=definition.name,
                kind=NsMetricKind.GAUGE,
                value=1,
                observed_at=UTC_START,
                attributes={"mode": "ready"},
                definition=definition,
                sanitizer=FailingSanitizer(),
            )
        self.assertNotIn("observability-sanitizer-failure-secret", str(failed.exception))

        for sanitizer, exception_type in (
            (InterruptingSanitizer(), KeyboardInterrupt),
            (ExitingSanitizer(), SystemExit),
        ):
            with self.subTest(exception_type=exception_type.__name__):
                with self.assertRaises(exception_type):
                    NsMetricRecord(
                        name=definition.name,
                        kind=NsMetricKind.GAUGE,
                        value=1,
                        observed_at=UTC_START,
                        attributes={"mode": "ready"},
                        definition=definition,
                        sanitizer=sanitizer,
                    )

    def test_trace_record_preserves_trace_context_and_sanitizes_attributes(self) -> None:
        token = "trace-token-secret"
        bearer = "trace-bearer-secret"
        payload = "trace-payload-secret"
        auth_context = "trace-auth-context-secret"
        signature = "trace-signature-secret"
        attributes: dict[str, object] = {
            "connection_id": "connection_safe_for_trace",
            "token": token,
            "authorization": f"Bearer {bearer}",
            "payload": {"body": payload},
            "auth_context": {"principal": auth_context},
            "signed_url": f"https://example.test/object?signature={signature}",
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
        self.assertEqual(REDACTED, record.attributes["token"])
        self.assertEqual(REDACTED, record.attributes["authorization"])
        self.assertEqual(REDACTED, record.attributes["payload"])
        self.assertEqual(REDACTED, record.attributes["auth_context"])
        self.assertEqual(REDACTED, record.attributes["signed_url"])
        frozen_nested = record.attributes["nested"]
        self.assertIsInstance(frozen_nested, Mapping)
        assert isinstance(frozen_nested, Mapping)
        self.assertEqual((1, 2), frozen_nested["values"])
        with self.assertRaises(TypeError):
            frozen_nested["new"] = "value"  # type: ignore[index]
        self.assert_json_safe_and_no_leak(
            record.to_dict(),
            token,
            bearer,
            payload,
            auth_context,
            signature,
        )

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

        sanitizer_failed = NsDiagnosticSnapshot(
            name="runtime.failed_sanitizer_snapshot",
            captured_at=UTC_START,
            snapshot={"token": "ordinary-failure-secret"},
            sanitizer=FailingSanitizer(),
        )
        failed_encoded = self.assert_json_safe_and_no_leak(
            sanitizer_failed.to_dict(),
            "ordinary-failure-secret",
            "observability-sanitizer-failure-secret",
        )
        self.assertIn("sanitization_failed", failed_encoded)

        with self.assertRaises(KeyboardInterrupt):
            NsDiagnosticSnapshot(
                name="runtime.interrupted_snapshot",
                captured_at=UTC_START,
                snapshot={"safe": True},
                sanitizer=InterruptingSanitizer(),
            )
        with self.assertRaises(SystemExit):
            NsDiagnosticSnapshot(
                name="runtime.exiting_snapshot",
                captured_at=UTC_START,
                snapshot={"safe": True},
                sanitizer=ExitingSanitizer(),
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
                {
                    "aiohttp",
                    "httpx",
                    "importlib",
                    "pkgutil",
                    "requests",
                    "ns_config",
                    "ns_runtime",
                }
            )
        )
        source = source_path.read_text(encoding="utf-8")
        self.assertNotIn("__subclasses__", source)
        self.assertNotIn("get_async_http_client", source)


class ObservabilityRecordSizeTestCase(unittest.TestCase):
    def assert_complete_record_is_bounded(self, record: object) -> int:
        to_dict = getattr(record, "to_dict")
        public_record = to_dict()
        encoded = strict_record_bytes(public_record)
        self.assertLessEqual(
            len(encoded),
            MAX_OBSERVABILITY_RECORD_BYTES,
        )
        json.loads(encoded.decode("utf-8"))
        return len(encoded)

    def test_all_public_record_types_use_the_complete_strict_json_boundary(self) -> None:
        records = (
            NsMetricRecord(
                name="runtime_transport_connections",
                kind=NsMetricKind.GAUGE,
                value=2,
                observed_at=UTC_START,
                attributes={
                    "component_type": "runtime",
                    "tenant_scope": "system",
                    "transport_type": "websocket_tcp",
                },
            ),
            NsTraceRecord(
                name="processor.execute",
                started_at=UTC_START,
                trace_id="trace-safe",
                span_id="span-safe",
                attributes={"message": "多字节记录"},
            ),
            NsDiagnosticSnapshot(
                name="runtime.health",
                captured_at=UTC_START,
                snapshot={"state": "healthy", "message": "多字节快照"},
            ),
        )
        for record in records:
            with self.subTest(record_type=type(record).__name__):
                self.assertGreater(self.assert_complete_record_is_bounded(record), 0)

    def test_metric_full_record_overhead_is_included_in_size_error(self) -> None:
        secret = "metric-size-secret-"
        finite_value = secret + "x" * (
            MAX_METRIC_ATTRIBUTE_VALUE_LENGTH - len(secret)
        )
        definition = NsMetricDefinition(
            name="runtime_metric_size_boundary",
            allowed_attributes={
                "state": NsMetricAttributeDefinition(
                    key="state",
                    value_type=NsMetricAttributeValueType.STRING,
                    allowed_values=frozenset({finite_value}),
                ),
            },
        )
        attribute_bytes = len(strict_record_bytes({"state": finite_value}))
        reduced_boundary = attribute_bytes + 1
        with patch.object(
            observability_module,
            "MAX_OBSERVABILITY_RECORD_BYTES",
            reduced_boundary,
        ):
            with self.assertRaises(NsValidationError) as raised:
                NsMetricRecord(
                    name=definition.name,
                    kind=NsMetricKind.GAUGE,
                    value=1,
                    observed_at=UTC_START,
                    attributes={"state": finite_value},
                    definition=definition,
                )
        self.assertEqual(
            {
                "field",
                "maximum_bytes",
                "actual_bytes",
                "record_type",
            },
            set(raised.exception.details),
        )
        self.assertEqual("record", raised.exception.details["field"])
        self.assertEqual("metric", raised.exception.details["record_type"])
        self.assertEqual(
            reduced_boundary,
            raised.exception.details["maximum_bytes"],
        )
        self.assertGreater(
            raised.exception.details["actual_bytes"],
            reduced_boundary,
        )
        self.assertNotIn(secret, str(raised.exception))
        self.assertIsNone(raised.exception.__cause__)

    def test_trace_mapping_can_fit_while_complete_record_exceeds_limit(self) -> None:
        secret = "trace-size-secret-"
        value = secret + "x" * (
            MAX_OBSERVABILITY_RECORD_BYTES - 128 - len(secret)
        )
        self.assertLess(
            len(strict_record_bytes({"details": value})),
            MAX_OBSERVABILITY_RECORD_BYTES,
        )
        with self.assertRaises(NsValidationError) as raised:
            NsTraceRecord(
                name="processor.complete_record_boundary",
                started_at=UTC_START,
                trace_id="trace-boundary",
                span_id="span-boundary",
                attributes={"details": value},
            )
        self.assertEqual(
            {
                "field",
                "maximum_bytes",
                "actual_bytes",
                "record_type",
            },
            set(raised.exception.details),
        )
        self.assertEqual("trace", raised.exception.details["record_type"])
        self.assertGreater(
            raised.exception.details["actual_bytes"],
            MAX_OBSERVABILITY_RECORD_BYTES,
        )
        self.assertNotIn(secret, str(raised.exception))
        self.assertNotIn(secret, json.dumps(raised.exception.details))
        self.assertIsNone(raised.exception.__cause__)

    def test_multibyte_size_is_measured_as_utf8_bytes(self) -> None:
        multibyte_value = "界" * (MAX_OBSERVABILITY_RECORD_BYTES // 2)
        self.assertLess(
            len(multibyte_value),
            MAX_OBSERVABILITY_RECORD_BYTES,
        )
        with self.assertRaises(NsValidationError) as raised:
            NsTraceRecord(
                name="trace.multibyte_boundary",
                started_at=UTC_START,
                attributes={"message": multibyte_value},
            )
        self.assertGreater(
            raised.exception.details["actual_bytes"],
            MAX_OBSERVABILITY_RECORD_BYTES,
        )

    def test_diagnostic_full_record_overflow_degrades_and_rechecks(self) -> None:
        value = "x" * (MAX_OBSERVABILITY_RECORD_BYTES - 64)
        self.assertLess(
            len(strict_record_bytes({"details": value})),
            MAX_OBSERVABILITY_RECORD_BYTES,
        )
        record = NsDiagnosticSnapshot(
            name="runtime.complete_record_boundary",
            captured_at=UTC_START,
            snapshot={"details": value},
        )
        self.assertEqual(
            {"observability_status": "size_limit_exceeded"},
            dict(record.snapshot),
        )
        self.assert_complete_record_is_bounded(record)

        with patch.object(
            observability_module,
            "MAX_OBSERVABILITY_RECORD_BYTES",
            16,
        ):
            with self.assertRaises(NsValidationError) as raised:
                NsDiagnosticSnapshot(
                    name="runtime.placeholder_too_large",
                    captured_at=UTC_START,
                    snapshot={"state": "healthy"},
                )
        self.assertEqual("record", raised.exception.details["field"])
        self.assertEqual(
            "diagnostic_snapshot",
            raised.exception.details["record_type"],
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
        self.assertEqual(0, sink.rejected_count)

        self.assertEqual(2, sink.clear())
        self.assertEqual((), sink.records)
        self.assertEqual(0, sink.dropped_count)
        self.assertEqual(0, sink.rejected_count)

        asyncio.run(sink.aclose())
        self.assertFalse(sink.record(first))
        self.assertEqual((), sink.records)
        self.assertEqual(0, sink.dropped_count)
        self.assertEqual(1, sink.rejected_count)
        self.assertEqual(0, sink.clear())
        self.assertEqual(1, sink.rejected_count)

    def test_sink_capacity_type_and_record_type_are_strict(self) -> None:
        for capacity in (0, -1, True, 1.5):
            with self.subTest(capacity=capacity):
                with self.assertRaises(NsValidationError):
                    InMemoryMetricsSink(capacity=capacity)  # type: ignore[arg-type]

        sink = InMemoryMetricsSink()
        trace = NsTraceRecord(name="trace", started_at=UTC_START)
        with self.assertRaises(NsValidationError):
            sink.record(trace)  # type: ignore[arg-type]
        asyncio.run(sink.aclose())
        with self.assertRaises(NsValidationError):
            sink.record(trace)  # type: ignore[arg-type]
        self.assertEqual(0, sink.rejected_count)

    def test_concurrent_recording_is_bounded_and_counts_drops(self) -> None:
        sink = InMemoryMetricsSink(capacity=100)
        record = self.make_metric("runtime_concurrent")

        with ThreadPoolExecutor(max_workers=8) as executor:
            accepted = tuple(executor.map(sink.record, (record,) * 250))

        self.assertTrue(all(accepted))
        self.assertEqual(100, len(sink.records))
        self.assertEqual(150, sink.dropped_count)
        self.assertEqual(0, sink.rejected_count)

    def test_record_and_aclose_race_has_only_atomic_accept_or_reject(self) -> None:
        sink = InMemoryMetricsSink(capacity=1000)
        record = self.make_metric("runtime_close_race")
        barrier = Barrier(9)

        def writer() -> tuple[bool, ...]:
            barrier.wait()
            return tuple(sink.record(record) for _ in range(100))

        def closer() -> None:
            barrier.wait()
            asyncio.run(sink.aclose())

        with ThreadPoolExecutor(max_workers=9) as executor:
            writer_futures = tuple(executor.submit(writer) for _ in range(8))
            close_future = executor.submit(closer)
            results = tuple(
                result
                for future in writer_futures
                for result in future.result()
            )
            close_future.result()

        accepted_count = sum(results)
        rejected_count = len(results) - accepted_count
        self.assertTrue(all(result in (True, False) for result in results))
        self.assertEqual(accepted_count, len(sink.records))
        self.assertEqual(rejected_count, sink.rejected_count)
        self.assertEqual(0, sink.dropped_count)
        self.assertTrue(sink.is_closed)


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
                self.assertFalse(sink.record(record))  # type: ignore[arg-type]
                self.assertEqual((record,), sink.records)
                self.assertEqual(1, sink.rejected_count)
                self.assertEqual(0, sink.dropped_count)
                with self.assertRaises(NsValidationError):
                    sink.record(object())  # type: ignore[arg-type]
                self.assertEqual(1, sink.rejected_count)


if __name__ == "__main__":
    unittest.main()
