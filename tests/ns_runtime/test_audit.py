# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import unittest

from ns_runtime.audit import (
    InMemoryRuntimeAuditSink,
)
from ns_runtime.models import (
    MessageTypeSpec,
    ProcessorRequest,
    ProcessorResponse,
    RuntimeSessionContext,
    utc_now_iso,
)
from ns_runtime.processors import (
    BaseRuntimeProcessor,
    ProcessorRegistry,
    build_default_processor_pipeline,
)
from ns_runtime.protocol import EnvelopeCodec
from ns_runtime.service import RuntimeService


class _RaisingProcessor(
    BaseRuntimeProcessor
):
    async def process(
            self,
            request: ProcessorRequest,
    ) -> ProcessorResponse:
        raise RuntimeError(
            "processor boom"
        )


class RuntimeAuditTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.audit_sink = (
            InMemoryRuntimeAuditSink()
        )
        self.service = (
            RuntimeService.build_default(
                runtime_id="runtime-test",
                audit_sink=self.audit_sink,
            )
        )
        self.session = self._build_session(
            capabilities=(
                "runtime.management",
                "task.dispatch",
            )
        )

    def test_responded_message_is_written_to_audit_sink(
            self,
    ) -> None:
        response = asyncio.run(
            self.service.process_frame(
                self._build_frame(
                    message_id="msg-heartbeat",
                    message_type=(
                        "connection.heartbeat"
                    ),
                    category="control",
                ),
                self.session,
            )
        )

        self.assertEqual(
            response.action,
            "respond",
        )

        events = self.service.list_audit_events(
            message_id="msg-heartbeat",
            tenant_id="tenant-1",
        )

        self.assertEqual(
            len(events),
            1,
        )

        event = events[0]

        self.assertEqual(
            event.audit_action,
            (
                "runtime.message."
                "connection.heartbeat"
            ),
        )
        self.assertEqual(
            event.outcome,
            "responded",
        )
        self.assertEqual(
            event.result_action,
            "respond",
        )
        self.assertEqual(
            event.processor_name,
            "HeartbeatProcessor",
        )
        self.assertEqual(
            event.response_message_type,
            "connection.heartbeat_ack",
        )
        self.assertEqual(
            event.error_code,
            "",
        )
        self.assertEqual(
            event.capabilities_summary,
            (
                "runtime.management",
                "task.dispatch",
            ),
        )

        event_data = event.to_dict()

        self.assertNotIn(
            "payload",
            event_data,
        )
        self.assertNotIn(
            "token",
            event_data,
        )

    def test_auth_rejection_is_written_to_audit_sink(
            self,
    ) -> None:
        unauthorized_session = (
            self._build_session(
                capabilities=(),
            )
        )

        response = asyncio.run(
            self.service.process_frame(
                self._build_frame(
                    message_id="msg-unauthorized",
                    message_type="task.dispatch",
                    category="task",
                    target={
                        "kind": "runtime",
                        "runtime_id": "runtime-test",
                    },
                ),
                unauthorized_session,
            )
        )

        self.assertEqual(
            response.action,
            "reject",
        )

        events = self.audit_sink.list_events(
            message_id="msg-unauthorized",
        )

        self.assertEqual(
            len(events),
            1,
        )

        event = events[0]

        self.assertEqual(
            event.outcome,
            "rejected",
        )
        self.assertEqual(
            event.processor_name,
            "MessageTypeAuthProcessor",
        )
        self.assertEqual(
            event.response_message_type,
            "runtime.error",
        )
        self.assertEqual(
            event.error_code,
            (
                "RUNTIME_UNAUTHORIZED_"
                "MESSAGE_TYPE"
            ),
        )

    def test_type_schema_rejection_is_audited_once(
            self,
    ) -> None:
        response = asyncio.run(
            self.service.process_frame(
                self._build_frame(
                    message_id="msg-schema",
                    message_type="task.dispatch",
                    category="task",
                ),
                self.session,
            )
        )

        self.assertEqual(
            response.action,
            "reject",
        )

        events = self.audit_sink.list_events(
            message_id="msg-schema",
        )

        self.assertEqual(
            len(events),
            1,
        )
        self.assertEqual(
            events[0].outcome,
            "rejected",
        )
        self.assertEqual(
            events[0].processor_name,
            "MessageTypeAuthProcessor",
        )
        self.assertEqual(
            events[0].error_code,
            "RUNTIME_ENVELOPE_SCHEMA_ERROR",
        )

    def test_processor_exception_is_audited_before_reraise(
            self,
    ) -> None:
        audit_sink = (
            InMemoryRuntimeAuditSink()
        )
        codec = EnvelopeCodec(
            runtime_id="runtime-test"
        )
        registry = ProcessorRegistry()

        registry.register(
            MessageTypeSpec(
                message_type="test.raise",
                category="task",
                reliability="best_effort",
                audit_action=(
                    "runtime.message.test.raise"
                ),
                implemented=True,
            ),
            _RaisingProcessor(),
        )

        pipeline = (
            build_default_processor_pipeline(
                codec,
                registry,
                audit_sink=audit_sink,
            )
        )

        envelope = codec.parse_inbound(
            self._build_frame(
                message_id="msg-exception",
                message_type="test.raise",
                category="task",
            ),
            self.session,
        )

        with self.assertRaisesRegex(
                RuntimeError,
                "processor boom",
        ):
            asyncio.run(
                pipeline.process(
                    envelope,
                    self.session,
                    config_version="config:1",
                    policy_version="policy:1",
                )
            )

        events = audit_sink.list_events(
            message_id="msg-exception",
        )

        self.assertEqual(
            len(events),
            1,
        )

        event = events[0]

        self.assertEqual(
            event.audit_action,
            "runtime.message.test.raise",
        )
        self.assertEqual(
            event.outcome,
            "exception",
        )
        self.assertEqual(
            event.result_action,
            "exception",
        )
        self.assertEqual(
            event.processor_name,
            "_RaisingProcessor",
        )
        self.assertEqual(
            event.exception_class,
            "RuntimeError",
        )
        self.assertEqual(
            event.exception_message,
            "processor boom",
        )
        self.assertEqual(
            event.config_version,
            "config:1",
        )
        self.assertEqual(
            event.policy_version,
            "policy:1",
        )

    def _build_session(
            self,
            *,
            capabilities: tuple[str, ...],
    ) -> RuntimeSessionContext:
        return RuntimeSessionContext(
            runtime_id="runtime-test",
            connection_id="conn-1",
            session_id="session-1",
            identity="manager-1",
            tenant_id="tenant-1",
            component_type="management",
            capabilities=capabilities,
            auth_snapshot_id="auth-1",
            auth_issued_at=utc_now_iso(),
            auth_expires_at=utc_now_iso(),
            connection_epoch=1,
            iam_mode="cached",
        )

    @staticmethod
    def _build_frame(
            *,
            message_id: str,
            message_type: str,
            category: str,
            target: dict[str, object] | None = None,
    ) -> str:
        frame: dict[str, object] = {
            "protocol": {
                "version": "1.0.0",
            },
            "message": {
                "message_id": message_id,
                "type": message_type,
                "category": category,
                "priority": 100,
                "created_at": utc_now_iso(),
                "reliability": "best_effort",
            },
            "trace": {
                "trace_id": (
                    f"trace:{message_id}"
                ),
                "request_id": (
                    f"request:{message_id}"
                ),
            },
        }

        if target is not None:
            frame["target"] = target

        return json.dumps(
            frame,
            ensure_ascii=False,
        )


if __name__ == "__main__":
    unittest.main()
