# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import unittest
from typing import Any

from ns_runtime.auth import RuntimeAuthResult
from ns_runtime.models import (
    RuntimeSessionContext,
    utc_now_iso,
)
from ns_runtime.payload_reference import (
    PayloadReferenceValidationRequest,
    PayloadReferenceValidationResult,
    PayloadReferenceValidator,
    RuntimePayloadReference,
)
from ns_runtime.protocol import EnvelopeCodec
from ns_runtime.service import RuntimeService


class _MemoryWebSocket:
    def __init__(self) -> None:
        self.frames: list[str] = []

    async def send(self, frame: str) -> None:
        self.frames.append(frame)


class _SequencePayloadReferenceValidator(PayloadReferenceValidator):
    def __init__(self, *outcomes: PayloadReferenceValidationResult | Exception) -> None:
        if not outcomes:
            raise ValueError(
                "At least one validation outcome is required."
            )

        self._outcomes = outcomes
        self.requests: list[PayloadReferenceValidationRequest] = []

    async def validate(self, request: PayloadReferenceValidationRequest) -> PayloadReferenceValidationResult:
        self.requests.append(request)

        index = min(
            len(self.requests) - 1,
            len(self._outcomes) - 1,
        )
        outcome = self._outcomes[index]

        if isinstance(outcome, Exception):
            raise outcome

        return outcome


class RuntimePayloadReferenceProtocolTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.codec = EnvelopeCodec(runtime_id="runtime-test")
        self.session = RuntimeSessionContext(
            runtime_id="runtime-test",
            connection_id="source-1",
            session_id="session-1",
            identity="source-identity",
            tenant_id="tenant-1",
            component_type="management",
            capabilities=("task.dispatch",),
            auth_snapshot_id="snapshot-1",
            auth_issued_at=utc_now_iso(),
            auth_expires_at=utc_now_iso(),
            connection_epoch=0,
            role="singleton",
            iam_mode="cached",
        )

    def test_valid_reference_payload_is_parsed(self) -> None:
        envelope = self.codec.parse_inbound(self._build_frame(payload=self._reference_payload()), self.session)

        reference = RuntimePayloadReference.from_envelope(envelope)

        self.assertIsNotNone(reference)
        self.assertEqual(reference.object_id, "object-1")
        self.assertEqual(reference.version, "version-1")
        self.assertEqual(reference.checksum, "sha256:abcdef")
        self.assertEqual(reference.content_type, "application/json")
        self.assertEqual(reference.size_bytes, 1024)

    def test_inline_payload_remains_supported(self) -> None:
        envelope = self.codec.parse_inbound(
            self._build_frame(
                payload={
                    "mode": "inline",
                    "inline": {
                        "task_name": "demo-task",
                    },
                }
            ),
            self.session,
        )

        self.assertIsNone(
            RuntimePayloadReference.from_envelope(
                envelope
            )
        )

    def test_invalid_reference_schema_is_rejected(self) -> None:
        invalid_payloads: tuple[
            tuple[str, dict[str, Any]],
            ...,
        ] = (
            (
                "missing_payload_ref",
                {
                    "mode": "reference",
                    "checksum": "sha256:abcdef",
                },
            ),
            (
                "missing_object_id",
                {
                    "mode": "reference",
                    "payload_ref": {
                        "version": "version-1",
                    },
                    "checksum": "sha256:abcdef",
                },
            ),
            (
                "missing_version",
                {
                    "mode": "reference",
                    "payload_ref": {
                        "object_id": "object-1",
                    },
                    "checksum": "sha256:abcdef",
                },
            ),
            (
                "missing_checksum",
                {
                    "mode": "reference",
                    "payload_ref": {
                        "object_id": "object-1",
                        "version": "version-1",
                    },
                },
            ),
            (
                "inline_and_reference",
                {
                    "mode": "reference",
                    "inline": {
                        "task_name": "demo-task",
                    },
                    "payload_ref": {
                        "object_id": "object-1",
                        "version": "version-1",
                    },
                    "checksum": "sha256:abcdef",
                },
            ),
            (
                "unknown_reference_field",
                {
                    "mode": "reference",
                    "payload_ref": {
                        "object_id": "object-1",
                        "version": "version-1",
                        "tenant_id": "tenant-2",
                    },
                    "checksum": "sha256:abcdef",
                },
            ),
            (
                "negative_size",
                {
                    "mode": "reference",
                    "payload_ref": {
                        "object_id": "object-1",
                        "version": "version-1",
                    },
                    "checksum": "sha256:abcdef",
                    "size_bytes": -1,
                },
            ),
            (
                "bool_size",
                {
                    "mode": "reference",
                    "payload_ref": {
                        "object_id": "object-1",
                        "version": "version-1",
                    },
                    "checksum": "sha256:abcdef",
                    "size_bytes": True,
                },
            ),
        )

        for name, payload in invalid_payloads:
            with self.subTest(name=name):
                response = asyncio.run(
                    RuntimeService.build_default(
                        runtime_id="runtime-test"
                    ).process_frame(
                        self._build_frame(
                            payload=payload
                        ),
                        self.session,
                    )
                )

                self.assertEqual(
                    response.action,
                    "reject",
                )
                self.assertIsNotNone(
                    response.envelope
                )
                self.assertEqual(
                    response.envelope[
                        "payload"
                    ]["inline"]["error"]["code"],
                    "RUNTIME_ENVELOPE_SCHEMA_ERROR",
                )

    @staticmethod
    def _reference_payload() -> dict[str, Any]:
        return {
            "mode": "reference",
            "payload_ref": {
                "object_id": "object-1",
                "version": "version-1",
            },
            "checksum": "sha256:abcdef",
            "content_type": "application/json",
            "size_bytes": 1024,
        }

    @staticmethod
    def _build_frame(*, payload: dict[str, Any]) -> str:
        return json.dumps(
            {
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
                    "connection_id": "target-1",
                },
                "payload": payload,
            }, ensure_ascii=False
        )


class RuntimePayloadReferenceProcessorTestCase(unittest.TestCase):
    def test_inline_payload_does_not_call_validator(self, ) -> None:
        validator = _SequencePayloadReferenceValidator(
            RuntimeError(
                "inline payload must not call validator"
            )
        )
        service, source, target, websocket = (
            self._build_runtime(
                validator=validator,
            )
        )

        response = asyncio.run(
            service.process_frame(
                self._build_dispatch_frame(
                    message_id="inline-1",
                    target_connection_id=(
                        target.connection_id
                    ),
                    payload={
                        "mode": "inline",
                        "inline": {
                            "task_name": "demo-task",
                        },
                    },
                ),
                source,
            )
        )

        self.assertEqual(
            response.action,
            "respond",
        )
        self.assertEqual(
            response.envelope["message"]["type"],
            "delivery.accepted",
        )
        self.assertEqual(
            validator.requests,
            [],
        )
        self.assertEqual(
            len(websocket.frames),
            1,
        )

    def test_valid_reference_is_accepted(self, ) -> None:
        validator = _SequencePayloadReferenceValidator(
            PayloadReferenceValidationResult.valid()
        )
        service, source, target, websocket = (
            self._build_runtime(
                validator=validator,
            )
        )

        response = asyncio.run(
            service.process_frame(
                self._build_dispatch_frame(
                    message_id="reference-valid-1",
                    target_connection_id=(
                        target.connection_id
                    ),
                    payload=self._reference_payload(),
                ),
                source,
            )
        )

        self.assertEqual(
            response.action,
            "respond",
        )
        self.assertEqual(
            response.envelope["message"]["type"],
            "delivery.accepted",
        )
        self.assertEqual(
            len(websocket.frames),
            1,
        )

        snapshot = (
            service.delivery_registry
            .build_delivery_snapshot()
        )

        self.assertEqual(
            snapshot["delivery_count"],
            1,
        )
        self.assertEqual(
            snapshot["attempt_count"],
            1,
        )
        self.assertEqual(
            len(validator.requests),
            1,
        )

        validation_request = validator.requests[0]
        self.assertEqual(
            validation_request.reference.object_id,
            "private-object-1",
        )
        self.assertEqual(
            validation_request.source_tenant_id,
            "tenant-1",
        )
        self.assertEqual(
            validation_request.targets[0].connection_id,
            target.connection_id,
        )

    def test_rejected_reference_does_not_create_delivery(self, ) -> None:
        cases = (
            (
                "invalid",
                "RUNTIME_PAYLOAD_REF_INVALID",
            ),
            (
                "denied",
                "RUNTIME_PAYLOAD_REF_DENIED",
            ),
            (
                "expired",
                "RUNTIME_PAYLOAD_REF_EXPIRED",
            ),
            (
                "checksum_mismatch",
                "RUNTIME_PAYLOAD_REF_CHECKSUM_MISMATCH",
            ),
            (
                "version_mismatch",
                "RUNTIME_PAYLOAD_REF_VERSION_MISMATCH",
            ),
        )

        for reason, expected_code in cases:
            with self.subTest(reason=reason):
                validator = (
                    _SequencePayloadReferenceValidator(
                        PayloadReferenceValidationResult.rejected(
                            reason=reason,
                        )
                    )
                )
                service, source, target, websocket = (
                    self._build_runtime(
                        validator=validator,
                    )
                )

                message_id = f"reference-{reason}"
                response = asyncio.run(
                    service.process_frame(
                        self._build_dispatch_frame(
                            message_id=message_id,
                            target_connection_id=(
                                target.connection_id
                            ),
                            payload=(
                                self._reference_payload()
                            ),
                        ),
                        source,
                    )
                )

                self.assertEqual(
                    response.action,
                    "reject",
                )
                self.assertEqual(
                    response.envelope[
                        "message"
                    ]["type"],
                    "delivery.rejected",
                )

                inline = response.envelope[
                    "payload"
                ]["inline"]

                self.assertEqual(
                    inline["reason_code"],
                    expected_code,
                )
                self.assertFalse(
                    inline["retryable"]
                )
                self.assertNotIn(
                    "details",
                    inline,
                )
                self.assertNotIn(
                    "delivery",
                    response.envelope,
                )

                serialized = json.dumps(
                    response.envelope,
                    ensure_ascii=False,
                )
                self.assertNotIn(
                    "private-object-1",
                    serialized,
                )
                self.assertNotIn(
                    "sha256:private-checksum",
                    serialized,
                )

                summary = (
                    service.get_message_summary(
                        message_id,
                        tenant_id="tenant-1",
                    )
                )

                self.assertIsNotNone(summary)
                self.assertEqual(
                    summary.target_count,
                    1,
                )
                self.assertEqual(
                    summary.accepted_count,
                    0,
                )
                self.assertEqual(
                    summary.rejected_count,
                    1,
                )
                self.assertEqual(
                    summary.delivery_count,
                    0,
                )
                self.assertEqual(
                    summary.state,
                    "failed",
                )

                snapshot = (
                    service.delivery_registry
                    .build_delivery_snapshot()
                )

                self.assertEqual(
                    snapshot["delivery_count"],
                    0,
                )
                self.assertEqual(
                    snapshot["attempt_count"],
                    0,
                )
                self.assertEqual(
                    len(websocket.frames),
                    0,
                )

    def test_unavailable_reference_validation_is_runtime_error(self, ) -> None:
        cases: tuple[
            tuple[
                object,
                str,
            ],
            ...,
        ] = (
            (
                PayloadReferenceValidationResult.unavailable(
                    reason="validation_unavailable"
                ),
                "RUNTIME_PAYLOAD_REF_VALIDATION_UNAVAILABLE",
            ),
            (
                PayloadReferenceValidationResult.unavailable(
                    reason="validation_timeout"
                ),
                "RUNTIME_PAYLOAD_REF_VALIDATION_TIMEOUT",
            ),
            (
                TimeoutError(
                    "private validator timeout"
                ),
                "RUNTIME_PAYLOAD_REF_VALIDATION_TIMEOUT",
            ),
            (
                RuntimeError(
                    "private backend failure"
                ),
                "RUNTIME_PAYLOAD_REF_VALIDATION_UNAVAILABLE",
            ),
        )

        for outcome, expected_code in cases:
            with self.subTest(
                    expected_code=expected_code
            ):
                validator = (
                    _SequencePayloadReferenceValidator(
                        outcome
                    )
                )
                service, source, target, websocket = (
                    self._build_runtime(
                        validator=validator,
                    )
                )

                message_id = (
                    f"unavailable-{expected_code}"
                )
                response = asyncio.run(
                    service.process_frame(
                        self._build_dispatch_frame(
                            message_id=message_id,
                            target_connection_id=(
                                target.connection_id
                            ),
                            payload=(
                                self._reference_payload()
                            ),
                        ),
                        source,
                    )
                )

                self.assertEqual(
                    response.action,
                    "reject",
                )
                self.assertEqual(
                    response.envelope[
                        "message"
                    ]["type"],
                    "runtime.error",
                )

                error = response.envelope[
                    "payload"
                ]["inline"]["error"]

                self.assertEqual(
                    error["code"],
                    expected_code,
                )
                self.assertEqual(
                    error["details"],
                    {
                        "message_id": message_id,
                    },
                )

                serialized = json.dumps(
                    response.envelope,
                    ensure_ascii=False,
                )
                self.assertNotIn(
                    "private-object-1",
                    serialized,
                )
                self.assertNotIn(
                    "private backend failure",
                    serialized,
                )
                self.assertNotIn(
                    "private validator timeout",
                    serialized,
                )

                self.assertIsNone(
                    service.get_message_summary(
                        message_id,
                        tenant_id="tenant-1",
                    )
                )

                snapshot = (
                    service.delivery_registry
                    .build_delivery_snapshot()
                )

                self.assertEqual(
                    snapshot["delivery_count"],
                    0,
                )
                self.assertEqual(
                    snapshot["attempt_count"],
                    0,
                )
                self.assertEqual(
                    len(websocket.frames),
                    0,
                )

    def test_multi_target_reference_rejection_rejects_all_targets(self, ) -> None:
        validator = _SequencePayloadReferenceValidator(
            PayloadReferenceValidationResult.rejected(
                reason="denied"
            )
        )
        service = RuntimeService.build_default(
            runtime_id="runtime-test",
            payload_reference_validator=validator,
        )
        source = self._build_source_session(
            tenant_id="tenant-1",
            connection_id="source-1",
        )

        target_1, websocket_1 = self._activate_target(
            service=service,
            tenant_id="tenant-1",
            identity="shared-target",
        )
        target_2, websocket_2 = self._activate_target(
            service=service,
            tenant_id="tenant-1",
            identity="shared-target",
        )

        response = asyncio.run(
            service.process_frame(
                self._build_dispatch_frame(
                    message_id="multi-target-1",
                    target={
                        "kind": "identity",
                        "identity": "shared-target",
                        "strategy": "all",
                    },
                    payload=self._reference_payload(),
                ),
                source,
            )
        )

        self.assertEqual(
            response.envelope["message"]["type"],
            "delivery.rejected",
        )

        summary = service.get_message_summary(
            "multi-target-1",
            tenant_id="tenant-1",
        )

        self.assertIsNotNone(summary)
        self.assertEqual(
            summary.target_count,
            2,
        )
        self.assertEqual(
            summary.rejected_count,
            2,
        )
        self.assertEqual(
            summary.delivery_count,
            0,
        )
        self.assertEqual(
            summary.state,
            "failed",
        )

        self.assertEqual(
            len(validator.requests[0].targets),
            2,
        )
        self.assertEqual(
            len(websocket_1.frames),
            0,
        )
        self.assertEqual(
            len(websocket_2.frames),
            0,
        )
        self.assertNotEqual(
            target_1.connection_id,
            target_2.connection_id,
        )

    def test_valid_duplicate_reference_does_not_write_twice(self, ) -> None:
        validator = _SequencePayloadReferenceValidator(
            PayloadReferenceValidationResult.valid(),
            PayloadReferenceValidationResult.valid(),
        )
        service, source, target, websocket = (
            self._build_runtime(
                validator=validator,
            )
        )

        frame = self._build_dispatch_frame(
            message_id="duplicate-reference-1",
            target_connection_id=(
                target.connection_id
            ),
            payload=self._reference_payload(),
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
            second.envelope["payload"]["inline"][
                "duplicate_status"
            ],
            "delivery_in_progress",
        )

        snapshot = (
            service.delivery_registry
            .build_delivery_snapshot()
        )

        self.assertEqual(
            snapshot["delivery_count"],
            1,
        )
        self.assertEqual(
            snapshot["attempt_count"],
            1,
        )
        self.assertEqual(
            len(websocket.frames),
            1,
        )
        self.assertEqual(
            len(validator.requests),
            2,
        )

    def test_same_rejected_message_id_isolated_by_tenant(self, ) -> None:
        validator = _SequencePayloadReferenceValidator(
            PayloadReferenceValidationResult.rejected(
                reason="invalid"
            )
        )
        service = RuntimeService.build_default(
            runtime_id="runtime-test",
            payload_reference_validator=validator,
        )

        source_1 = self._build_source_session(
            tenant_id="tenant-1",
            connection_id="source-1",
        )
        source_2 = self._build_source_session(
            tenant_id="tenant-2",
            connection_id="source-2",
        )

        target_1, _websocket_1 = self._activate_target(
            service=service,
            tenant_id="tenant-1",
            identity="target-1",
        )
        target_2, _websocket_2 = self._activate_target(
            service=service,
            tenant_id="tenant-2",
            identity="target-2",
        )

        message_id = "shared-message-id"

        asyncio.run(
            service.process_frame(
                self._build_dispatch_frame(
                    message_id=message_id,
                    target_connection_id=(
                        target_1.connection_id
                    ),
                    payload=self._reference_payload(),
                ),
                source_1,
            )
        )
        asyncio.run(
            service.process_frame(
                self._build_dispatch_frame(
                    message_id=message_id,
                    target_connection_id=(
                        target_2.connection_id
                    ),
                    payload=self._reference_payload(),
                ),
                source_2,
            )
        )

        summary_1 = service.get_message_summary(
            message_id,
            tenant_id="tenant-1",
        )
        summary_2 = service.get_message_summary(
            message_id,
            tenant_id="tenant-2",
        )

        self.assertIsNotNone(summary_1)
        self.assertIsNotNone(summary_2)
        self.assertNotEqual(
            summary_1.summary_id,
            summary_2.summary_id,
        )
        self.assertEqual(
            summary_1.tenant_id,
            "tenant-1",
        )
        self.assertEqual(
            summary_2.tenant_id,
            "tenant-2",
        )
        self.assertIsNone(
            service.get_message_summary(
                message_id
            )
        )
        self.assertEqual(
            service.delivery_registry.list_records(),
            (),
        )

    def test_rejected_validation_after_accepted_delivery_keeps_existing_summary(self) -> None:
        validator = _SequencePayloadReferenceValidator(
            PayloadReferenceValidationResult.valid(),
            PayloadReferenceValidationResult.rejected(
                reason="denied"
            ),
        )
        service, source, target, websocket = (
            self._build_runtime(
                validator=validator,
            )
        )

        frame = self._build_dispatch_frame(
            message_id="accepted-then-denied-1",
            target_connection_id=(
                target.connection_id
            ),
            payload=self._reference_payload(),
        )

        first_response = asyncio.run(
            service.process_frame(
                frame,
                source,
            )
        )

        summary_before = service.get_message_summary(
            "accepted-then-denied-1",
            tenant_id="tenant-1",
        )
        self.assertIsNotNone(summary_before)
        summary_before_snapshot = summary_before.to_dict()

        second_response = asyncio.run(
            service.process_frame(
                frame,
                source,
            )
        )

        self.assertEqual(
            first_response.envelope["message"]["type"],
            "delivery.accepted",
        )
        self.assertEqual(
            second_response.action,
            "reject",
        )
        self.assertEqual(
            second_response.envelope["message"]["type"],
            "runtime.error",
        )
        self.assertEqual(
            second_response.envelope[
                "payload"
            ]["inline"]["error"]["code"],
            "RUNTIME_PAYLOAD_REF_DENIED",
        )

        summary_after = service.get_message_summary(
            "accepted-then-denied-1",
            tenant_id="tenant-1",
        )
        self.assertIsNotNone(summary_after)
        self.assertEqual(
            summary_after.to_dict(),
            summary_before_snapshot,
        )

        snapshot = (
            service.delivery_registry
            .build_delivery_snapshot()
        )
        self.assertEqual(
            snapshot["delivery_count"],
            1,
        )
        self.assertEqual(
            snapshot["attempt_count"],
            1,
        )
        self.assertEqual(
            len(websocket.frames),
            1,
        )
        self.assertEqual(
            len(validator.requests),
            2,
        )

    def test_previously_rejected_message_id_cannot_be_accepted(self) -> None:
        validator = _SequencePayloadReferenceValidator(
            PayloadReferenceValidationResult.rejected(
                reason="invalid"
            ),
            PayloadReferenceValidationResult.valid(),
        )
        service, source, target, websocket = (
            self._build_runtime(
                validator=validator,
            )
        )

        frame = self._build_dispatch_frame(
            message_id="rejected-then-valid-1",
            target_connection_id=(
                target.connection_id
            ),
            payload=self._reference_payload(),
        )

        first_response = asyncio.run(
            service.process_frame(
                frame,
                source,
            )
        )

        summary_before = service.get_message_summary(
            "rejected-then-valid-1",
            tenant_id="tenant-1",
        )
        self.assertIsNotNone(summary_before)
        summary_before_snapshot = summary_before.to_dict()

        second_response = asyncio.run(
            service.process_frame(
                frame,
                source,
            )
        )

        self.assertEqual(
            first_response.envelope["message"]["type"],
            "delivery.rejected",
        )
        self.assertEqual(
            second_response.action,
            "reject",
        )
        self.assertEqual(
            second_response.envelope["message"]["type"],
            "runtime.error",
        )
        self.assertEqual(
            second_response.envelope[
                "payload"
            ]["inline"]["error"]["code"],
            "RUNTIME_DELIVERY_STATE_ERROR",
        )

        summary_after = service.get_message_summary(
            "rejected-then-valid-1",
            tenant_id="tenant-1",
        )
        self.assertIsNotNone(summary_after)
        self.assertEqual(
            summary_after.to_dict(),
            summary_before_snapshot,
        )
        self.assertEqual(
            summary_after.delivery_count,
            0,
        )
        self.assertEqual(
            summary_after.rejected_count,
            1,
        )
        self.assertEqual(
            summary_after.target_count,
            1,
        )
        self.assertEqual(
            summary_after.state,
            "failed",
        )

        snapshot = (
            service.delivery_registry
            .build_delivery_snapshot()
        )
        self.assertEqual(
            snapshot["delivery_count"],
            0,
        )
        self.assertEqual(
            snapshot["attempt_count"],
            0,
        )
        self.assertEqual(
            len(websocket.frames),
            0,
        )
        self.assertEqual(
            len(validator.requests),
            2,
        )

    def _build_runtime(self, *, validator: PayloadReferenceValidator) -> tuple[RuntimeService, RuntimeSessionContext, RuntimeSessionContext, _MemoryWebSocket]:
        service = RuntimeService.build_default(
            runtime_id="runtime-test",
            payload_reference_validator=validator,
        )
        source = self._build_source_session(
            tenant_id="tenant-1",
            connection_id="source-1",
        )
        target, websocket = self._activate_target(
            service=service,
            tenant_id="tenant-1",
            identity="target-1",
        )

        return (
            service,
            source,
            target,
            websocket,
        )

    @staticmethod
    def _build_source_session(*, tenant_id: str, connection_id: str) -> RuntimeSessionContext:
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
    def _activate_target(*, service: RuntimeService, tenant_id: str, identity: str) -> tuple[RuntimeSessionContext, _MemoryWebSocket]:
        record = (
            service.session_registry
            .create_handshaking(
                remote_address="test"
            )
        )
        session = service.session_registry.activate(
            record,
            RuntimeAuthResult(
                accepted=True,
                identity=identity,
                tenant_id=tenant_id,
                component_type="client",
                capabilities=("task.execute",),
                snapshot_id=f"snapshot:{identity}",
                issued_at=utc_now_iso(),
                expires_at=utc_now_iso(),
                iam_mode="cached",
                role="singleton",
            ),
        )

        websocket = _MemoryWebSocket()
        service.writer_registry.register(
            connection_id=session.connection_id,
            connection_epoch=session.connection_epoch,
            websocket=websocket,
        )

        return session, websocket

    @staticmethod
    def _reference_payload() -> dict[str, Any]:
        return {
            "mode": "reference",
            "payload_ref": {
                "object_id": "private-object-1",
                "version": "version-1",
            },
            "checksum": "sha256:private-checksum",
            "content_type": "application/json",
            "size_bytes": 1024,
        }

    @staticmethod
    def _build_dispatch_frame(*, message_id: str, payload: dict[str, Any], target_connection_id: str | None = None, target: dict[str, Any] | None = None) -> str:
        resolved_target = target

        if resolved_target is None:
            if target_connection_id is None:
                raise ValueError(
                    "target_connection_id or target is required."
                )

            resolved_target = {
                "kind": "connection",
                "connection_id": target_connection_id,
            }

        return json.dumps(
            {
                "protocol": {
                    "version": "1.0.0",
                },
                "message": {
                    "message_id": message_id,
                    "type": "task.dispatch",
                    "category": "task",
                    "priority": 100,
                    "created_at": utc_now_iso(),
                    "reliability": "critical",
                },
                "target": resolved_target,
                "payload": payload,
            },
            ensure_ascii=False,
        )


if __name__ == "__main__":
    unittest.main()
