# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import unittest
from datetime import (
    datetime,
    timedelta,
    timezone
)
from typing import (
    Any,
    TYPE_CHECKING
)

from ns_common.exceptions import (
    NsRuntimeAckRejectedError,
    NsRuntimeDeferRejectedError,
    NsRuntimeNackRejectedError,
)
from ns_runtime.auth import RuntimeAuthResult
from ns_runtime.delivery import RuntimeDeliveryRegistry
from ns_runtime.models import (
    RuntimeSessionContext,
    utc_now_iso
)
from ns_runtime.outbound import RuntimeLocalWriteResult
from ns_runtime.protocol import EnvelopeCodec
from ns_runtime.routing import RuntimeTargetResolver
from ns_runtime.session import RuntimeSessionRegistry

if TYPE_CHECKING:
    pass


class RuntimeDeliveryRegistryTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime_id = "runtime-test"
        self.codec = EnvelopeCodec(runtime_id=self.runtime_id)
        self.session_registry = RuntimeSessionRegistry(runtime_id=self.runtime_id)
        self.target_resolver = RuntimeTargetResolver(
            runtime_id=self.runtime_id,
            session_registry=self.session_registry,
        )
        self.delivery_registry = RuntimeDeliveryRegistry(default_ack_timeout_ms=1000)
        self.source_session = self._activate(
            identity="source-1",
            tenant_id="tenant-1",
            component_type="management",
            capabilities=("task.dispatch",),
        )
        self.target_session = self._activate(
            identity="target-1",
            tenant_id="tenant-1",
            component_type="client",
            capabilities=("task.execute",),
        )

    def test_delivery_record_moves_to_ack_waiting_after_transport_send(self) -> None:
        envelope = self.codec.parse_inbound(
            self._build_task_dispatch_frame(
                target_connection_id=self.target_session.connection_id,
            ),
            self.source_session,
        )
        decision = self.target_resolver.resolve(envelope, self.source_session)
        self.assertIsNotNone(decision)

        record = self.delivery_registry.create_prepared_record(
            decision=decision,
            envelope=envelope,
            target=decision.targets[0],
        )
        self.assertEqual(record.state, "prepared")

        attempt = self.delivery_registry.start_sending(record=record)
        self.assertEqual(record.state, "sending")
        self.assertEqual(attempt.write_status, "sending")

        forwarded = self.delivery_registry.inject_delivery_group(
            envelope=envelope,
            record=record,
            attempt=attempt,
        )
        self.assertEqual(forwarded["delivery"]["delivery_id"], record.delivery_id)
        self.assertEqual(forwarded["delivery"]["attempt"], 1)

        self.delivery_registry.mark_sent_to_transport(
            record=record,
            attempt=attempt,
            write_result=RuntimeLocalWriteResult(
                connection_id=self.target_session.connection_id,
                connection_epoch=0,
                status="sent",
            ),
        )

        self.assertEqual(record.state, "ack_waiting")
        self.assertEqual(attempt.write_status, "sent_to_transport")
        self.assertTrue(record.ack_deadline_at)
        self.assertEqual(self.delivery_registry.list_attempts_for_delivery(record.delivery_id), (attempt,))
        self.assertEqual(self.delivery_registry.build_delivery_snapshot()["by_state"]["ack_waiting"], 1)

    def test_delivery_ack_moves_ack_waiting_to_acked(self) -> None:
        envelope = self.codec.parse_inbound(
            self._build_task_dispatch_frame(
                target_connection_id=self.target_session.connection_id,
            ),
            self.source_session,
        )
        decision = self.target_resolver.resolve(envelope, self.source_session)
        self.assertIsNotNone(decision)

        record = self.delivery_registry.create_prepared_record(
            decision=decision,
            envelope=envelope,
            target=decision.targets[0],
        )
        attempt = self.delivery_registry.start_sending(record=record)
        self.delivery_registry.mark_sent_to_transport(
            record=record,
            attempt=attempt,
            write_result=RuntimeLocalWriteResult(
                connection_id=self.target_session.connection_id,
                connection_epoch=self.target_session.connection_epoch,
                status="sent",
            ),
        )

        ack_envelope = self.codec.parse_inbound(
            self._build_ack_frame(delivery_id=record.delivery_id),
            self.target_session,
        )
        result = self.delivery_registry.mark_acked(
            envelope=ack_envelope,
            session_connection_id=self.target_session.connection_id,
            session_connection_epoch=self.target_session.connection_epoch,
            session_tenant_id=self.target_session.tenant_id,
        )

        self.assertEqual(result.status, "acked")
        self.assertFalse(result.duplicate)
        self.assertEqual(record.state, "acked")
        self.assertEqual(result.ack_record.delivery_id, record.delivery_id)
        self.assertEqual(self.delivery_registry.get_ack_for_delivery(record.delivery_id), result.ack_record)
        self.assertEqual(self.delivery_registry.build_delivery_snapshot()["by_state"]["acked"], 1)
        self.assertEqual(self.delivery_registry.build_delivery_snapshot()["ack_count"], 1)

    def test_duplicate_delivery_ack_returns_duplicate_ack(self) -> None:
        envelope = self.codec.parse_inbound(
            self._build_task_dispatch_frame(
                target_connection_id=self.target_session.connection_id,
            ),
            self.source_session,
        )
        decision = self.target_resolver.resolve(envelope, self.source_session)
        self.assertIsNotNone(decision)

        record = self.delivery_registry.create_prepared_record(
            decision=decision,
            envelope=envelope,
            target=decision.targets[0],
        )
        attempt = self.delivery_registry.start_sending(record=record)
        self.delivery_registry.mark_sent_to_transport(
            record=record,
            attempt=attempt,
            write_result=RuntimeLocalWriteResult(
                connection_id=self.target_session.connection_id,
                connection_epoch=self.target_session.connection_epoch,
                status="sent",
            ),
        )

        ack_frame = self._build_ack_frame(delivery_id=record.delivery_id)
        ack_envelope = self.codec.parse_inbound(ack_frame, self.target_session)

        first = self.delivery_registry.mark_acked(
            envelope=ack_envelope,
            session_connection_id=self.target_session.connection_id,
            session_connection_epoch=self.target_session.connection_epoch,
            session_tenant_id=self.target_session.tenant_id,
        )
        second = self.delivery_registry.mark_acked(
            envelope=ack_envelope,
            session_connection_id=self.target_session.connection_id,
            session_connection_epoch=self.target_session.connection_epoch,
            session_tenant_id=self.target_session.tenant_id,
        )

        self.assertEqual(first.status, "acked")
        self.assertEqual(second.status, "duplicate_ack")
        self.assertTrue(second.duplicate)
        self.assertEqual(len(self.delivery_registry.list_acks()), 1)
        self.assertEqual(second.ack_record.duplicate_count, 1)

    def test_ack_from_wrong_connection_is_rejected(self) -> None:
        envelope = self.codec.parse_inbound(
            self._build_task_dispatch_frame(
                target_connection_id=self.target_session.connection_id,
            ),
            self.source_session,
        )
        decision = self.target_resolver.resolve(envelope, self.source_session)
        self.assertIsNotNone(decision)

        record = self.delivery_registry.create_prepared_record(
            decision=decision,
            envelope=envelope,
            target=decision.targets[0],
        )
        attempt = self.delivery_registry.start_sending(record=record)
        self.delivery_registry.mark_sent_to_transport(
            record=record,
            attempt=attempt,
            write_result=RuntimeLocalWriteResult(
                connection_id=self.target_session.connection_id,
                connection_epoch=self.target_session.connection_epoch,
                status="sent",
            ),
        )

        wrong_session = self._activate(
            identity="wrong-target",
            tenant_id="tenant-1",
            component_type="client",
            capabilities=("task.execute",),
        )
        ack_envelope = self.codec.parse_inbound(
            self._build_ack_frame(delivery_id=record.delivery_id),
            wrong_session,
        )

        with self.assertRaises(NsRuntimeAckRejectedError):
            self.delivery_registry.mark_acked(
                envelope=ack_envelope,
                session_connection_id=wrong_session.connection_id,
                session_connection_epoch=wrong_session.connection_epoch,
                session_tenant_id=wrong_session.tenant_id,
            )

    def test_duplicate_ack_from_wrong_connection_is_rejected(self) -> None:
        envelope = self.codec.parse_inbound(
            self._build_task_dispatch_frame(
                target_connection_id=self.target_session.connection_id,
            ),
            self.source_session,
        )
        decision = self.target_resolver.resolve(envelope, self.source_session)
        self.assertIsNotNone(decision)

        record = self.delivery_registry.create_prepared_record(
            decision=decision,
            envelope=envelope,
            target=decision.targets[0],
        )
        attempt = self.delivery_registry.start_sending(record=record)
        self.delivery_registry.mark_sent_to_transport(
            record=record,
            attempt=attempt,
            write_result=RuntimeLocalWriteResult(
                connection_id=self.target_session.connection_id,
                connection_epoch=self.target_session.connection_epoch,
                status="sent",
            ),
        )

        valid_ack_envelope = self.codec.parse_inbound(
            self._build_ack_frame(delivery_id=record.delivery_id),
            self.target_session,
        )
        self.delivery_registry.mark_acked(
            envelope=valid_ack_envelope,
            session_connection_id=self.target_session.connection_id,
            session_connection_epoch=self.target_session.connection_epoch,
            session_tenant_id=self.target_session.tenant_id,
        )

        wrong_session = self._activate(
            identity="wrong-target-after-ack",
            tenant_id="tenant-1",
            component_type="client",
            capabilities=("task.execute",),
        )
        wrong_ack_envelope = self.codec.parse_inbound(
            self._build_ack_frame(delivery_id=record.delivery_id),
            wrong_session,
        )

        with self.assertRaises(NsRuntimeAckRejectedError):
            self.delivery_registry.mark_acked(
                envelope=wrong_ack_envelope,
                session_connection_id=wrong_session.connection_id,
                session_connection_epoch=wrong_session.connection_epoch,
                session_tenant_id=wrong_session.tenant_id,
            )

        self.assertEqual(len(self.delivery_registry.list_acks()), 1)
        self.assertEqual(self.delivery_registry.get_ack_for_delivery(record.delivery_id).duplicate_count, 0)

    def test_retryable_nack_moves_delivery_to_retry_scheduled(self) -> None:
        record = self._create_ack_waiting_delivery()

        nack_envelope = self.codec.parse_inbound(
            self._build_nack_frame(
                delivery_id=record.delivery_id,
                reason="temporarily_unavailable",
            ),
            self.target_session,
        )
        result = self.delivery_registry.mark_nacked(
            envelope=nack_envelope,
            session_connection_id=self.target_session.connection_id,
            session_connection_epoch=self.target_session.connection_epoch,
            session_tenant_id=self.target_session.tenant_id,
        )

        self.assertEqual(result.status, "nacked_retry_scheduled")
        self.assertFalse(result.duplicate)
        self.assertTrue(result.nack_record.retryable)
        self.assertEqual(result.nack_record.reason, "temporarily_unavailable")
        self.assertEqual(record.state, "retry_scheduled")
        self.assertEqual(self.delivery_registry.get_nack_for_delivery(record.delivery_id), result.nack_record)
        self.assertEqual(self.delivery_registry.build_delivery_snapshot()["by_state"]["retry_scheduled"], 1)
        self.assertEqual(self.delivery_registry.build_delivery_snapshot()["nack_count"], 1)

    def test_non_retryable_nack_moves_delivery_to_dead_lettered(self) -> None:
        record = self._create_ack_waiting_delivery()

        nack_envelope = self.codec.parse_inbound(
            self._build_nack_frame(
                delivery_id=record.delivery_id,
                reason="permission_denied",
            ),
            self.target_session,
        )
        result = self.delivery_registry.mark_nacked(
            envelope=nack_envelope,
            session_connection_id=self.target_session.connection_id,
            session_connection_epoch=self.target_session.connection_epoch,
            session_tenant_id=self.target_session.tenant_id,
        )

        self.assertEqual(result.status, "nacked_dead_lettered")
        self.assertFalse(result.duplicate)
        self.assertFalse(result.nack_record.retryable)
        self.assertEqual(result.nack_record.reason, "permission_denied")
        self.assertEqual(record.state, "dead_lettered")
        self.assertEqual(record.last_error_code, "RUNTIME_UNAUTHORIZED_MESSAGE_TYPE")
        self.assertEqual(self.delivery_registry.build_delivery_snapshot()["by_state"]["dead_lettered"], 1)

    def test_duplicate_nack_returns_duplicate_nack_without_second_record(self) -> None:
        record = self._create_ack_waiting_delivery()

        nack_frame = self._build_nack_frame(
            delivery_id=record.delivery_id,
            reason="queue_full",
        )
        nack_envelope = self.codec.parse_inbound(nack_frame, self.target_session)

        first = self.delivery_registry.mark_nacked(
            envelope=nack_envelope,
            session_connection_id=self.target_session.connection_id,
            session_connection_epoch=self.target_session.connection_epoch,
            session_tenant_id=self.target_session.tenant_id,
        )
        second = self.delivery_registry.mark_nacked(
            envelope=nack_envelope,
            session_connection_id=self.target_session.connection_id,
            session_connection_epoch=self.target_session.connection_epoch,
            session_tenant_id=self.target_session.tenant_id,
        )

        self.assertEqual(first.status, "nacked_retry_scheduled")
        self.assertEqual(second.status, "duplicate_nack")
        self.assertTrue(second.duplicate)
        self.assertEqual(len(self.delivery_registry.list_nacks()), 1)
        self.assertEqual(second.nack_record.duplicate_count, 1)

    def test_nack_from_wrong_connection_is_rejected(self) -> None:
        record = self._create_ack_waiting_delivery()
        wrong_session = self._activate(
            identity="wrong-nack-target",
            tenant_id="tenant-1",
            component_type="client",
            capabilities=("task.execute",),
        )

        nack_envelope = self.codec.parse_inbound(
            self._build_nack_frame(
                delivery_id=record.delivery_id,
                reason="temporarily_unavailable",
            ),
            wrong_session,
        )

        with self.assertRaises(NsRuntimeNackRejectedError):
            self.delivery_registry.mark_nacked(
                envelope=nack_envelope,
                session_connection_id=wrong_session.connection_id,
                session_connection_epoch=wrong_session.connection_epoch,
                session_tenant_id=wrong_session.tenant_id,
            )

    def test_duplicate_non_retryable_nack_returns_duplicate_nack_without_second_record(self) -> None:
        record = self._create_ack_waiting_delivery()

        nack_frame = self._build_nack_frame(
            delivery_id=record.delivery_id,
            reason="permission_denied",
        )
        nack_envelope = self.codec.parse_inbound(nack_frame, self.target_session)

        first = self.delivery_registry.mark_nacked(
            envelope=nack_envelope,
            session_connection_id=self.target_session.connection_id,
            session_connection_epoch=self.target_session.connection_epoch,
            session_tenant_id=self.target_session.tenant_id,
        )
        second = self.delivery_registry.mark_nacked(
            envelope=nack_envelope,
            session_connection_id=self.target_session.connection_id,
            session_connection_epoch=self.target_session.connection_epoch,
            session_tenant_id=self.target_session.tenant_id,
        )

        self.assertEqual(first.status, "nacked_dead_lettered")
        self.assertEqual(first.delivery_record.state, "dead_lettered")
        self.assertEqual(second.status, "duplicate_nack")
        self.assertTrue(second.duplicate)
        self.assertEqual(len(self.delivery_registry.list_nacks()), 1)
        self.assertEqual(second.nack_record.duplicate_count, 1)
        self.assertEqual(record.state, "dead_lettered")

    def test_duplicate_nack_from_wrong_connection_is_rejected(self) -> None:
        record = self._create_ack_waiting_delivery()

        valid_nack_envelope = self.codec.parse_inbound(
            self._build_nack_frame(
                delivery_id=record.delivery_id,
                reason="queue_full",
            ),
            self.target_session,
        )
        self.delivery_registry.mark_nacked(
            envelope=valid_nack_envelope,
            session_connection_id=self.target_session.connection_id,
            session_connection_epoch=self.target_session.connection_epoch,
            session_tenant_id=self.target_session.tenant_id,
        )

        wrong_session = self._activate(
            identity="wrong-nack-after-nack",
            tenant_id="tenant-1",
            component_type="client",
            capabilities=("task.execute",),
        )
        wrong_nack_envelope = self.codec.parse_inbound(
            self._build_nack_frame(
                delivery_id=record.delivery_id,
                reason="queue_full",
            ),
            wrong_session,
        )

        with self.assertRaises(NsRuntimeNackRejectedError):
            self.delivery_registry.mark_nacked(
                envelope=wrong_nack_envelope,
                session_connection_id=wrong_session.connection_id,
                session_connection_epoch=wrong_session.connection_epoch,
                session_tenant_id=wrong_session.tenant_id,
            )

        self.assertEqual(len(self.delivery_registry.list_nacks()), 1)
        self.assertEqual(self.delivery_registry.get_nack_for_delivery(record.delivery_id).duplicate_count, 0)

    def test_defer_extends_ack_deadline_and_keeps_ack_waiting(self) -> None:
        record = self._create_ack_waiting_delivery()
        previous_deadline = record.ack_deadline_at

        defer_envelope = self.codec.parse_inbound(
            self._build_defer_frame(
                delivery_id=record.delivery_id,
                defer_ms=1000,
            ),
            self.target_session,
        )
        result = self.delivery_registry.mark_deferred(
            envelope=defer_envelope,
            session_connection_id=self.target_session.connection_id,
            session_connection_epoch=self.target_session.connection_epoch,
            session_tenant_id=self.target_session.tenant_id,
        )

        self.assertEqual(result.status, "deferred")
        self.assertEqual(record.state, "ack_waiting")
        self.assertEqual(result.defer_record.defer_ms, 1000)
        self.assertEqual(result.defer_record.defer_sequence, 1)
        self.assertEqual(result.defer_record.previous_ack_deadline_at, previous_deadline)
        self.assertEqual(record.ack_deadline_at, result.defer_record.new_ack_deadline_at)
        self.assertNotEqual(record.ack_deadline_at, previous_deadline)
        self.assertEqual(result.defer_count, 1)
        self.assertEqual(result.total_defer_ms, 1000)
        self.assertEqual(self.delivery_registry.build_delivery_snapshot()["defer_count"], 1)
        self.assertEqual(self.delivery_registry.build_delivery_snapshot()["by_state"]["ack_waiting"], 1)

    def test_defer_from_retry_scheduled_returns_to_ack_waiting(self) -> None:
        record = self._create_ack_waiting_delivery()

        nack_envelope = self.codec.parse_inbound(
            self._build_nack_frame(
                delivery_id=record.delivery_id,
                reason="queue_full",
            ),
            self.target_session,
        )
        self.delivery_registry.mark_nacked(
            envelope=nack_envelope,
            session_connection_id=self.target_session.connection_id,
            session_connection_epoch=self.target_session.connection_epoch,
            session_tenant_id=self.target_session.tenant_id,
        )
        self.assertEqual(record.state, "retry_scheduled")

        defer_envelope = self.codec.parse_inbound(
            self._build_defer_frame(
                delivery_id=record.delivery_id,
                defer_ms=1000,
            ),
            self.target_session,
        )
        result = self.delivery_registry.mark_deferred(
            envelope=defer_envelope,
            session_connection_id=self.target_session.connection_id,
            session_connection_epoch=self.target_session.connection_epoch,
            session_tenant_id=self.target_session.tenant_id,
        )

        self.assertEqual(result.status, "deferred")
        self.assertEqual(record.state, "ack_waiting")
        self.assertEqual(result.defer_record.defer_sequence, 1)

    def test_defer_from_wrong_connection_is_rejected(self) -> None:
        record = self._create_ack_waiting_delivery()
        wrong_session = self._activate(
            identity="wrong-defer-target",
            tenant_id="tenant-1",
            component_type="client",
            capabilities=("task.execute",),
        )

        defer_envelope = self.codec.parse_inbound(
            self._build_defer_frame(
                delivery_id=record.delivery_id,
                defer_ms=1000,
            ),
            wrong_session,
        )

        with self.assertRaises(NsRuntimeDeferRejectedError):
            self.delivery_registry.mark_deferred(
                envelope=defer_envelope,
                session_connection_id=wrong_session.connection_id,
                session_connection_epoch=wrong_session.connection_epoch,
                session_tenant_id=wrong_session.tenant_id,
            )

    def test_defer_budget_count_limit_is_rejected(self) -> None:
        registry = RuntimeDeliveryRegistry(
            default_ack_timeout_ms=1000,
            max_defer_count=1,
            max_single_defer_ms=1000,
            max_total_defer_ms=2000,
        )
        self.delivery_registry = registry
        record = self._create_ack_waiting_delivery()

        first = self.codec.parse_inbound(
            self._build_defer_frame(
                delivery_id=record.delivery_id,
                defer_ms=500,
            ),
            self.target_session,
        )
        self.delivery_registry.mark_deferred(
            envelope=first,
            session_connection_id=self.target_session.connection_id,
            session_connection_epoch=self.target_session.connection_epoch,
            session_tenant_id=self.target_session.tenant_id,
        )

        second = self.codec.parse_inbound(
            self._build_defer_frame(
                delivery_id=record.delivery_id,
                defer_ms=500,
            ),
            self.target_session,
        )

        with self.assertRaises(NsRuntimeDeferRejectedError):
            self.delivery_registry.mark_deferred(
                envelope=second,
                session_connection_id=self.target_session.connection_id,
                session_connection_epoch=self.target_session.connection_epoch,
                session_tenant_id=self.target_session.tenant_id,
            )

    def test_defer_single_duration_limit_is_rejected(self) -> None:
        registry = RuntimeDeliveryRegistry(
            default_ack_timeout_ms=1000,
            max_defer_count=3,
            max_single_defer_ms=1000,
            max_total_defer_ms=5000,
        )
        self.delivery_registry = registry
        record = self._create_ack_waiting_delivery()

        defer_envelope = self.codec.parse_inbound(
            self._build_defer_frame(
                delivery_id=record.delivery_id,
                defer_ms=1001,
            ),
            self.target_session,
        )

        with self.assertRaises(NsRuntimeDeferRejectedError):
            self.delivery_registry.mark_deferred(
                envelope=defer_envelope,
                session_connection_id=self.target_session.connection_id,
                session_connection_epoch=self.target_session.connection_epoch,
                session_tenant_id=self.target_session.tenant_id,
            )

    def test_ack_timeout_moves_ack_waiting_delivery_to_retry_scheduled(self) -> None:
        record = self._create_ack_waiting_delivery()
        record.ack_deadline_at = (datetime.now(timezone.utc) - timedelta(milliseconds=1)).isoformat(timespec="milliseconds")

        result = self.delivery_registry.scan_ack_timeouts()

        self.assertEqual(result.scanned_count, 1)
        self.assertEqual(result.timed_out_count, 1)
        self.assertEqual(result.retry_scheduled_count, 1)
        self.assertEqual(result.expired_count, 0)
        self.assertEqual(record.state, "retry_scheduled")
        self.assertEqual(record.last_error_code, "RUNTIME_ACK_TIMEOUT")
        self.assertEqual(record.last_error_message, "ack_timeout")
        self.assertEqual(self.delivery_registry.build_delivery_snapshot()["ack_timeout_count"], 1)

        timeout_records = self.delivery_registry.list_ack_timeouts_for_delivery(record.delivery_id)
        self.assertEqual(len(timeout_records), 1)
        self.assertEqual(timeout_records[0].new_state, "retry_scheduled")
        self.assertEqual(timeout_records[0].reason, "ack_timeout")

    def test_ack_timeout_with_expired_message_moves_delivery_to_expired(self) -> None:
        record = self._create_ack_waiting_delivery()
        now = datetime.now(timezone.utc)
        record.ack_deadline_at = (now - timedelta(milliseconds=1)).isoformat(timespec="milliseconds")
        record.expires_at = (now - timedelta(seconds=1)).isoformat(timespec="milliseconds")

        result = self.delivery_registry.scan_ack_timeouts(now=now)

        self.assertEqual(result.scanned_count, 1)
        self.assertEqual(result.timed_out_count, 1)
        self.assertEqual(result.retry_scheduled_count, 0)
        self.assertEqual(result.expired_count, 1)
        self.assertEqual(record.state, "expired")
        self.assertEqual(record.last_error_code, "RUNTIME_DELIVERY_EXPIRED")
        self.assertEqual(record.last_error_message, "message_expired")

        timeout_records = self.delivery_registry.list_ack_timeouts_for_delivery(record.delivery_id)
        self.assertEqual(len(timeout_records), 1)
        self.assertEqual(timeout_records[0].new_state, "expired")
        self.assertEqual(timeout_records[0].reason, "message_expired")

    def test_ack_timeout_scanner_ignores_future_ack_deadline(self) -> None:
        record = self._create_ack_waiting_delivery()
        record.ack_deadline_at = (datetime.now(timezone.utc) + timedelta(seconds=30)).isoformat(timespec="milliseconds")

        result = self.delivery_registry.scan_ack_timeouts()

        self.assertEqual(result.scanned_count, 1)
        self.assertEqual(result.timed_out_count, 0)
        self.assertEqual(result.retry_scheduled_count, 0)
        self.assertEqual(result.expired_count, 0)
        self.assertEqual(record.state, "ack_waiting")
        self.assertEqual(len(self.delivery_registry.list_ack_timeouts_for_delivery(record.delivery_id)), 0)

    def test_ack_timeout_scanner_ignores_non_ack_waiting_delivery(self) -> None:
        record = self._create_ack_waiting_delivery()
        record.ack_deadline_at = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(timespec="milliseconds")

        ack_envelope = self.codec.parse_inbound(
            self._build_ack_frame(delivery_id=record.delivery_id),
            self.target_session,
        )
        self.delivery_registry.mark_acked(
            envelope=ack_envelope,
            session_connection_id=self.target_session.connection_id,
            session_connection_epoch=self.target_session.connection_epoch,
            session_tenant_id=self.target_session.tenant_id,
        )
        self.assertEqual(record.state, "acked")

        result = self.delivery_registry.scan_ack_timeouts()

        self.assertEqual(result.scanned_count, 0)
        self.assertEqual(result.timed_out_count, 0)
        self.assertEqual(record.state, "acked")
        self.assertEqual(len(self.delivery_registry.list_ack_timeouts_for_delivery(record.delivery_id)), 0)

    def test_dead_lettered_delivery_is_registered_as_dead_letter(self) -> None:
        record = self._create_ack_waiting_delivery()

        nack_envelope = self.codec.parse_inbound(
            self._build_nack_frame(
                delivery_id=record.delivery_id,
                reason="permission_denied",
            ),
            self.target_session,
        )
        self.delivery_registry.mark_nacked(
            envelope=nack_envelope,
            session_connection_id=self.target_session.connection_id,
            session_connection_epoch=self.target_session.connection_epoch,
            session_tenant_id=self.target_session.tenant_id,
        )

        result = self.delivery_registry.scan_dead_letters()

        self.assertEqual(result.scanned_count, 1)
        self.assertEqual(result.created_count, 1)
        self.assertEqual(result.skipped_count, 0)

        dead_letter = self.delivery_registry.get_dead_letter_for_delivery(record.delivery_id)
        self.assertIsNotNone(dead_letter)
        self.assertEqual(dead_letter.delivery_id, record.delivery_id)
        self.assertEqual(dead_letter.message_id, record.message_id)
        self.assertEqual(dead_letter.tenant_id, record.tenant_id)
        self.assertEqual(dead_letter.message_type, record.message_type)
        self.assertEqual(dead_letter.terminal_state, "dead_lettered")
        self.assertEqual(dead_letter.reason, "permission_denied")
        self.assertEqual(dead_letter.last_error_code, "RUNTIME_UNAUTHORIZED_MESSAGE_TYPE")
        self.assertEqual(dead_letter.attempt_count, record.attempt_count)
        self.assertEqual(dead_letter.target_connection_id, record.target_connection_id)
        self.assertEqual(dead_letter.target_connection_epoch, record.target_connection_epoch)
        self.assertEqual(dead_letter.replayable, "not_replayable")

    def test_dead_letter_scanner_is_idempotent(self) -> None:
        record = self._create_ack_waiting_delivery()

        nack_envelope = self.codec.parse_inbound(
            self._build_nack_frame(
                delivery_id=record.delivery_id,
                reason="permission_denied",
            ),
            self.target_session,
        )
        self.delivery_registry.mark_nacked(
            envelope=nack_envelope,
            session_connection_id=self.target_session.connection_id,
            session_connection_epoch=self.target_session.connection_epoch,
            session_tenant_id=self.target_session.tenant_id,
        )

        first = self.delivery_registry.scan_dead_letters()
        second = self.delivery_registry.scan_dead_letters()

        self.assertEqual(first.created_count, 1)
        self.assertEqual(second.scanned_count, 1)
        self.assertEqual(second.created_count, 0)
        self.assertEqual(second.skipped_count, 1)
        self.assertEqual(len(self.delivery_registry.list_dead_letters()), 1)

    def test_expired_delivery_is_not_registered_as_dead_letter(self) -> None:
        record = self._create_ack_waiting_delivery()
        record.state = "expired"
        record.last_error_code = "RUNTIME_DELIVERY_EXPIRED"
        record.last_error_message = "message_expired"

        result = self.delivery_registry.scan_dead_letters()

        self.assertEqual(result.scanned_count, 0)
        self.assertEqual(result.created_count, 0)
        self.assertIsNone(self.delivery_registry.get_dead_letter_for_delivery(record.delivery_id))
        self.assertEqual(len(self.delivery_registry.list_dead_letters()), 0)

    def test_dead_letter_scanner_ignores_non_dead_letter_states(self) -> None:
        ack_waiting = self._create_ack_waiting_delivery()

        retry_scheduled = self._create_ack_waiting_delivery()
        retry_scheduled.state = "retry_scheduled"

        acked = self._create_ack_waiting_delivery()
        ack_envelope = self.codec.parse_inbound(
            self._build_ack_frame(delivery_id=acked.delivery_id),
            self.target_session,
        )
        self.delivery_registry.mark_acked(
            envelope=ack_envelope,
            session_connection_id=self.target_session.connection_id,
            session_connection_epoch=self.target_session.connection_epoch,
            session_tenant_id=self.target_session.tenant_id,
        )

        result = self.delivery_registry.scan_dead_letters()

        self.assertEqual(result.scanned_count, 0)
        self.assertEqual(result.created_count, 0)
        self.assertIsNone(self.delivery_registry.get_dead_letter_for_delivery(ack_waiting.delivery_id))
        self.assertIsNone(self.delivery_registry.get_dead_letter_for_delivery(retry_scheduled.delivery_id))
        self.assertIsNone(self.delivery_registry.get_dead_letter_for_delivery(acked.delivery_id))

    def test_delivery_snapshot_includes_dead_letter_count(self) -> None:
        record = self._create_ack_waiting_delivery()

        nack_envelope = self.codec.parse_inbound(
            self._build_nack_frame(
                delivery_id=record.delivery_id,
                reason="permission_denied",
            ),
            self.target_session,
        )
        self.delivery_registry.mark_nacked(
            envelope=nack_envelope,
            session_connection_id=self.target_session.connection_id,
            session_connection_epoch=self.target_session.connection_epoch,
            session_tenant_id=self.target_session.tenant_id,
        )

        before_scan = self.delivery_registry.build_delivery_snapshot()
        self.assertEqual(before_scan["by_state"]["dead_lettered"], 1)
        self.assertEqual(before_scan["dead_letter_count"], 0)

        self.delivery_registry.scan_dead_letters()
        after_scan = self.delivery_registry.build_delivery_snapshot()

        self.assertEqual(after_scan["by_state"]["dead_lettered"], 1)
        self.assertEqual(after_scan["dead_letter_count"], 1)

    def _create_ack_waiting_delivery(self):
        envelope = self.codec.parse_inbound(
            self._build_task_dispatch_frame(
                target_connection_id=self.target_session.connection_id,
            ),
            self.source_session,
        )
        decision = self.target_resolver.resolve(envelope, self.source_session)
        self.assertIsNotNone(decision)

        record = self.delivery_registry.create_prepared_record(
            decision=decision,
            envelope=envelope,
            target=decision.targets[0],
        )
        attempt = self.delivery_registry.start_sending(record=record)
        self.delivery_registry.mark_sent_to_transport(
            record=record,
            attempt=attempt,
            write_result=RuntimeLocalWriteResult(
                connection_id=self.target_session.connection_id,
                connection_epoch=self.target_session.connection_epoch,
                status="sent",
            ),
        )
        return record

    def _activate(self, *, identity: str, tenant_id: str, component_type: str, capabilities: tuple[str, ...]) -> RuntimeSessionContext:
        record = self.session_registry.create_handshaking(remote_address="test")
        return self.session_registry.activate(
            record,
            RuntimeAuthResult(
                accepted=True,
                identity=identity,
                tenant_id=tenant_id,
                component_type=component_type,  # type: ignore[arg-type]
                capabilities=capabilities,
                snapshot_id=f"snapshot:{identity}",
                issued_at=utc_now_iso(),
                expires_at=utc_now_iso(),
                iam_mode="cached",
                role="singleton",
            ),
        )

    @staticmethod
    def _build_task_dispatch_frame(*, target_connection_id: str) -> str:
        raw: dict[str, Any] = {
            "protocol": {
                "version": "1.0.0",
            },
            "message": {
                "message_id": "msg-1",
                "type": "task.dispatch",
                "category": "task",
                "priority": 100,
                "created_at": utc_now_iso(),
                "reliability": "critical",
            },
            "target": {
                "kind": "connection",
                "connection_id": target_connection_id,
            },
            "payload": {
                "mode": "inline",
                "inline": {
                    "task_name": "demo-task",
                },
            },
        }
        return json.dumps(raw, ensure_ascii=False)

    @staticmethod
    def _build_nack_frame(*, delivery_id: str, reason: str) -> str:
        raw: dict[str, Any] = {
            "protocol": {
                "version": "1.0.0",
            },
            "message": {
                "message_id": "nack-1",
                "type": "delivery.nack",
                "category": "delivery",
                "priority": 100,
                "created_at": utc_now_iso(),
                "reliability": "critical",
            },
            "delivery": {
                "delivery_id": delivery_id,
            },
            "payload": {
                "mode": "inline",
                "inline": {
                    "reason": reason,
                },
            },
        }
        return json.dumps(raw, ensure_ascii=False)

    @staticmethod
    def _build_defer_frame(*, delivery_id: str, defer_ms: int) -> str:
        raw: dict[str, Any] = {
            "protocol": {
                "version": "1.0.0",
            },
            "message": {
                "message_id": "defer-1",
                "type": "delivery.defer",
                "category": "delivery",
                "priority": 100,
                "created_at": utc_now_iso(),
                "reliability": "critical",
            },
            "delivery": {
                "delivery_id": delivery_id,
            },
            "payload": {
                "mode": "inline",
                "inline": {
                    "defer_ms": defer_ms,
                },
            },
        }
        return json.dumps(raw, ensure_ascii=False)

    @staticmethod
    def _build_ack_frame(*, delivery_id: str) -> str:
        raw: dict[str, Any] = {
            "protocol": {
                "version": "1.0.0",
            },
            "message": {
                "message_id": "ack-1",
                "type": "delivery.ack",
                "category": "delivery",
                "priority": 100,
                "created_at": utc_now_iso(),
                "reliability": "critical",
            },
            "delivery": {
                "delivery_id": delivery_id,
            },
        }
        return json.dumps(raw, ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()
