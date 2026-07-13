# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import unittest
from typing import Any

from ns_runtime.admission import RuntimeAdmissionPolicy
from ns_runtime.auth import RuntimeAuthResult
from ns_runtime.models import (
    RuntimeSessionContext,
    utc_now_iso,
)
from ns_runtime.service import RuntimeService


class _MemoryWebSocket:
    def __init__(self) -> None:
        self.frames: list[str] = []

    async def send(self, frame: str) -> None:
        self.frames.append(frame)


class RuntimeAdmissionTestCase(unittest.TestCase):
    def test_duplicate_bypasses_full_admission_capacity(
            self,
    ) -> None:
        service = self._build_service(
            RuntimeAdmissionPolicy(
                max_runtime_active_delivery=1,
                system_reserved_active_delivery=0,
                max_tenant_active_delivery=1,
                max_tenant_inflight_delivery=1,
                max_tenant_retry_backlog=10,
                max_target_inflight_delivery=1,
            )
        )
        source = self._build_source(
            tenant_id="tenant-1",
            connection_id="source-1",
        )
        target, websocket = self._activate_target(
            service=service,
            tenant_id="tenant-1",
            identity="target-1",
        )

        frame = self._build_dispatch_frame(
            message_id="duplicate-capacity-1",
            target_connection_id=(
                target.connection_id
            ),
        )

        first = asyncio.run(
            service.process_frame(
                frame,
                source,
            )
        )
        second = asyncio.run(
            service.process_frame(
                frame,
                source,
            )
        )

        self.assertEqual(
            first.envelope["message"]["type"],
            "delivery.accepted",
        )
        self.assertEqual(
            second.envelope["message"]["type"],
            "delivery.duplicate",
        )
        self.assertEqual(
            len(
                service.delivery_registry
                .list_records()
            ),
            1,
        )
        self.assertEqual(
            service.delivery_registry
            .build_delivery_snapshot()[
                "attempt_count"
            ],
            1,
        )
        self.assertEqual(
            len(websocket.frames),
            1,
        )

    def test_backpressure_rejection_recovers_after_ack(
            self,
    ) -> None:
        service = self._build_service(
            RuntimeAdmissionPolicy(
                max_runtime_active_delivery=10,
                system_reserved_active_delivery=0,
                max_tenant_active_delivery=1,
                max_tenant_inflight_delivery=1,
                max_tenant_retry_backlog=10,
                max_target_inflight_delivery=10,
            )
        )
        source = self._build_source(
            tenant_id="tenant-1",
            connection_id="source-1",
        )
        target_1, _websocket_1 = self._activate_target(
            service=service,
            tenant_id="tenant-1",
            identity="target-1",
        )
        target_2, websocket_2 = self._activate_target(
            service=service,
            tenant_id="tenant-1",
            identity="target-2",
        )

        first_frame = self._build_dispatch_frame(
            message_id="active-1",
            target_connection_id=(
                target_1.connection_id
            ),
        )
        second_frame = self._build_dispatch_frame(
            message_id="backpressure-1",
            target_connection_id=(
                target_2.connection_id
            ),
        )

        first_response = asyncio.run(
            service.process_frame(
                first_frame,
                source,
            )
        )
        rejected_response = asyncio.run(
            service.process_frame(
                second_frame,
                source,
            )
        )

        self.assertEqual(
            first_response.envelope["message"]["type"],
            "delivery.accepted",
        )
        self.assertEqual(
            rejected_response.envelope[
                "message"
            ]["type"],
            "delivery.rejected",
        )
        self.assertEqual(
            rejected_response.envelope[
                "payload"
            ]["inline"]["reason_code"],
            "RUNTIME_BACKPRESSURE",
        )
        self.assertTrue(
            rejected_response.envelope[
                "payload"
            ]["inline"]["retryable"]
        )

        rejected_summary = (
            service.get_message_summary(
                "backpressure-1",
                tenant_id="tenant-1",
            )
        )
        self.assertIsNotNone(
            rejected_summary
        )
        rejected_summary_id = (
            rejected_summary.summary_id
        )

        first_record = next(
            record
            for record in (
                service.delivery_registry
                .list_records()
            )
            if record.message_id == "active-1"
        )

        ack_response = asyncio.run(
            service.process_frame(
                self._build_ack_frame(
                    message_id="ack-active-1",
                    record=first_record,
                ),
                target_1,
            )
        )

        self.assertEqual(
            ack_response.envelope["message"]["type"],
            "delivery.ack_result",
        )
        self.assertEqual(
            first_record.state,
            "acked",
        )

        accepted_response = asyncio.run(
            service.process_frame(
                second_frame,
                source,
            )
        )

        self.assertEqual(
            accepted_response.envelope[
                "message"
            ]["type"],
            "delivery.accepted",
        )

        recovered_summary = (
            service.get_message_summary(
                "backpressure-1",
                tenant_id="tenant-1",
            )
        )
        self.assertIsNotNone(
            recovered_summary
        )
        self.assertEqual(
            recovered_summary.summary_id,
            rejected_summary_id,
        )
        self.assertEqual(
            recovered_summary.delivery_count,
            1,
        )
        self.assertEqual(
            recovered_summary.accepted_count,
            1,
        )
        self.assertEqual(
            recovered_summary.rejected_count,
            0,
        )
        self.assertEqual(
            recovered_summary.last_rejection_code,
            "",
        )
        self.assertEqual(
            recovered_summary.state,
            "pending",
        )
        self.assertEqual(
            len(websocket_2.frames),
            1,
        )

    def test_runtime_system_reserve_blocks_tenant_pool(
            self,
    ) -> None:
        service = self._build_service(
            RuntimeAdmissionPolicy(
                max_runtime_active_delivery=2,
                system_reserved_active_delivery=1,
                max_tenant_active_delivery=10,
                max_tenant_inflight_delivery=10,
                max_tenant_retry_backlog=10,
                max_target_inflight_delivery=10,
            )
        )

        source_1 = self._build_source(
            tenant_id="tenant-1",
            connection_id="source-1",
        )
        source_2 = self._build_source(
            tenant_id="tenant-2",
            connection_id="source-2",
        )

        target_1, _websocket_1 = self._activate_target(
            service=service,
            tenant_id="tenant-1",
            identity="target-1",
        )
        target_2, websocket_2 = self._activate_target(
            service=service,
            tenant_id="tenant-2",
            identity="target-2",
        )

        first = asyncio.run(
            service.process_frame(
                self._build_dispatch_frame(
                    message_id="reserve-1",
                    target_connection_id=(
                        target_1.connection_id
                    ),
                ),
                source_1,
            )
        )
        second = asyncio.run(
            service.process_frame(
                self._build_dispatch_frame(
                    message_id="reserve-2",
                    target_connection_id=(
                        target_2.connection_id
                    ),
                ),
                source_2,
            )
        )

        self.assertEqual(
            first.envelope["message"]["type"],
            "delivery.accepted",
        )
        self.assertEqual(
            second.envelope["message"]["type"],
            "delivery.rejected",
        )
        self.assertEqual(
            second.envelope[
                "payload"
            ]["inline"]["reason_code"],
            "RUNTIME_BACKPRESSURE",
        )
        self.assertEqual(
            len(websocket_2.frames),
            0,
        )

        admission = (
            service.admission_controller
            .evaluate(
                envelope=service._codec.parse_inbound(
                    self._build_dispatch_frame(
                        message_id="reserve-check",
                        target_connection_id=(
                            target_2.connection_id
                        ),
                    ),
                    source_2,
                ),
                decision=(
                    service.target_resolver.resolve(
                        service._codec.parse_inbound(
                            self._build_dispatch_frame(
                                message_id="reserve-check",
                                target_connection_id=(
                                    target_2.connection_id
                                ),
                            ),
                            source_2,
                        ),
                        source_2,
                    )
                ),
            )
        )

        self.assertFalse(
            admission.accepted
        )
        self.assertEqual(
            admission.reason,
            "runtime_tenant_pool_limit",
        )

    def test_target_inflight_limit_is_independent(
            self,
    ) -> None:
        service = self._build_service(
            RuntimeAdmissionPolicy(
                max_runtime_active_delivery=10,
                system_reserved_active_delivery=0,
                max_tenant_active_delivery=10,
                max_tenant_inflight_delivery=10,
                max_tenant_retry_backlog=10,
                max_target_inflight_delivery=1,
            )
        )
        source = self._build_source(
            tenant_id="tenant-1",
            connection_id="source-1",
        )

        target_1, _websocket_1 = self._activate_target(
            service=service,
            tenant_id="tenant-1",
            identity="target-1",
        )
        target_2, websocket_2 = self._activate_target(
            service=service,
            tenant_id="tenant-1",
            identity="target-2",
        )

        first = asyncio.run(
            service.process_frame(
                self._build_dispatch_frame(
                    message_id="target-limit-1",
                    target_connection_id=(
                        target_1.connection_id
                    ),
                ),
                source,
            )
        )
        same_target = asyncio.run(
            service.process_frame(
                self._build_dispatch_frame(
                    message_id="target-limit-2",
                    target_connection_id=(
                        target_1.connection_id
                    ),
                ),
                source,
            )
        )
        other_target = asyncio.run(
            service.process_frame(
                self._build_dispatch_frame(
                    message_id="target-limit-3",
                    target_connection_id=(
                        target_2.connection_id
                    ),
                ),
                source,
            )
        )

        self.assertEqual(
            first.envelope["message"]["type"],
            "delivery.accepted",
        )
        self.assertEqual(
            same_target.envelope[
                "message"
            ]["type"],
            "delivery.rejected",
        )
        self.assertEqual(
            same_target.envelope[
                "payload"
            ]["inline"]["reason_code"],
            "RUNTIME_BACKPRESSURE",
        )
        self.assertEqual(
            other_target.envelope[
                "message"
            ]["type"],
            "delivery.accepted",
        )
        self.assertEqual(
            len(websocket_2.frames),
            1,
        )

    @staticmethod
    def _build_service(
            policy: RuntimeAdmissionPolicy,
    ) -> RuntimeService:
        return RuntimeService.build_default(
            runtime_id="runtime-test",
            admission_policy=policy,
        )

    @staticmethod
    def _build_source(
            *,
            tenant_id: str,
            connection_id: str,
    ) -> RuntimeSessionContext:
        return RuntimeSessionContext(
            runtime_id="runtime-test",
            connection_id=connection_id,
            session_id=f"session:{connection_id}",
            identity=f"identity:{connection_id}",
            tenant_id=tenant_id,
            component_type="management",
            capabilities=("task.dispatch",),
            auth_snapshot_id=(
                f"snapshot:{connection_id}"
            ),
            auth_issued_at=utc_now_iso(),
            auth_expires_at=utc_now_iso(),
            connection_epoch=0,
            role="singleton",
            iam_mode="cached",
        )

    @staticmethod
    def _activate_target(
            *,
            service: RuntimeService,
            tenant_id: str,
            identity: str,
    ) -> tuple[
        RuntimeSessionContext,
        _MemoryWebSocket,
    ]:
        record = (
            service.session_registry
            .create_handshaking(
                remote_address="test"
            )
        )
        session = (
            service.session_registry.activate(
                record,
                RuntimeAuthResult(
                    accepted=True,
                    identity=identity,
                    tenant_id=tenant_id,
                    component_type="client",
                    capabilities=("task.execute",),
                    snapshot_id=(
                        f"snapshot:{identity}"
                    ),
                    issued_at=utc_now_iso(),
                    expires_at=utc_now_iso(),
                    iam_mode="cached",
                    role="singleton",
                ),
            )
        )

        websocket = _MemoryWebSocket()
        service.writer_registry.register(
            connection_id=session.connection_id,
            connection_epoch=(
                session.connection_epoch
            ),
            websocket=websocket,
        )

        return session, websocket

    @staticmethod
    def _build_dispatch_frame(
            *,
            message_id: str,
            target_connection_id: str,
    ) -> str:
        return json.dumps(
            {
                "protocol": {
                    "version": "1.0.0",
                },
                "message": {
                    "message_id": message_id,
                    "type": "task.dispatch",
                    "category": "task",
                    "priority": 50,
                    "created_at": utc_now_iso(),
                    "reliability": "critical",
                },
                "target": {
                    "kind": "connection",
                    "connection_id": (
                        target_connection_id
                    ),
                },
                "payload": {
                    "mode": "inline",
                    "inline": {
                        "task_name": "demo-task",
                    },
                },
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _build_ack_frame(
            *,
            message_id: str,
            record: Any,
    ) -> str:
        return json.dumps(
            {
                "protocol": {
                    "version": "1.0.0",
                },
                "message": {
                    "message_id": message_id,
                    "type": "delivery.ack",
                    "category": "delivery",
                    "priority": 100,
                    "created_at": utc_now_iso(),
                    "reliability": "critical",
                },
                "delivery": {
                    "delivery_id": record.delivery_id,
                    "summary_id": record.summary_id,
                    "root_delivery_id": (
                        record.root_delivery_id
                    ),
                    "attempt": record.attempt_count,
                    "ack_timeout_ms": (
                        record.ack_timeout_ms
                    ),
                    "replay_epoch": 0,
                },
            },
            ensure_ascii=False,
        )
