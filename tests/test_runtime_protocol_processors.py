# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging
import unittest

from ns_common.security import Sanitizer
from ns_runtime.protocol import (
    BUILTIN_MESSAGE_CONTRACTS,
    ErrorEnvelopeBuilder,
    ErrorEnvelopeContext,
    FeatureDisabledProcessor,
    ProtocolGroup,
    SourceGroup,
    build_feature_disabled_processors,
    envelope_from_mapping,
)


class _ListHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def _error_context() -> ErrorEnvelopeContext:
    return ErrorEnvelopeContext(
        protocol=ProtocolGroup(major=1, minor=0, patch=0),
        source=SourceGroup(
            runtime_id="runtime_1", connection_id="connection_runtime_1",
            identity_digest="sha256:runtime", tenant_id="tenant_1",
            component_type="runtime", capabilities_digest="sha256:protocol",
        ),
        error_message_id="message_error_1",
        created_at="2026-07-20T12:00:01Z",
    )


def _request(message_type: str, category: str, **groups: object):
    return envelope_from_mapping({
        "protocol": {"major": 1, "minor": 0, "patch": 0},
        "message": {
            "message_id": "message_request_1", "type": message_type,
            "category": category, "priority": 0,
            "created_at": "2026-07-20T12:00:00Z",
        },
        **groups,
    })


class RuntimeProtocolFeatureDisabledProcessorTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.logger = logging.Logger("feature-disabled-test")
        self.handler = _ListHandler()
        self.logger.addHandler(self.handler)
        self.processors = build_feature_disabled_processors(
            error_builder=ErrorEnvelopeBuilder(sanitizer=Sanitizer()),
            logger=self.logger,
        )

    def test_every_unimplemented_type_has_exactly_one_uniform_processor(self) -> None:
        disabled = {
            contract.processor_key
            for contract in BUILTIN_MESSAGE_CONTRACTS
            if not contract.feature_enabled
        }
        self.assertEqual(disabled, set(self.processors))
        self.assertEqual(40, len(self.processors))
        self.assertTrue(all(
            isinstance(processor, FeatureDisabledProcessor)
            for processor in self.processors.values()
        ))
        self.assertNotIn("runtime.error", self.processors)
        for message_type in (
            "connection.hello", "connection.accepted", "connection.rejected",
            "connection.reauth", "connection.reauth_accepted",
            "connection.reauth_rejected", "connection.heartbeat",
            "connection.heartbeat_ack", "connection.drain",
        ):
            self.assertNotIn(message_type, self.processors)

    async def test_task_ack_and_management_requests_only_return_stable_error(self) -> None:
        cases = (
            ("task.dispatch", "task", {
                "target": {"kind": "runtime", "runtime_id": "runtime_2"},
                "payload": {"mode": "inline", "inline": {"token": "secret-task"}},
            }),
            ("delivery.ack", "delivery", {
                "delivery": {"delivery_id": "delivery_1", "attempt": 1},
            }),
            ("runtime.control.switch_master", "control", {
                "payload": {"mode": "inline", "inline": {"credential": "secret-admin"}},
            }),
        )
        for message_type, category, groups in cases:
            with self.subTest(message_type=message_type):
                response = await self.processors[message_type].process(
                    _request(message_type, category, **groups),
                    error_context=_error_context(),
                )
                self.assertEqual("runtime.error", response.message.type)
                payload = response.payload.to_dict()["inline"]
                self.assertEqual("RUNTIME_FEATURE_DISABLED", payload["error_code"])
                self.assertTrue(payload["audit_required"])
                self.assertEqual("message_request_1", payload["message_id"])
                encoded = json.dumps(response.to_dict())
                self.assertNotIn("secret-task", encoded)
                self.assertNotIn("secret-admin", encoded)

        self.assertEqual(3, len(self.handler.records))
        for record in self.handler.records:
            self.assertEqual("runtime_message_feature_disabled", record.event)
            self.assertEqual("RUNTIME_FEATURE_DISABLED", record.error_code)
            self.assertNotIn("payload", vars(record))
            self.assertNotIn("credential", vars(record))

    async def test_logger_failure_cannot_turn_rejection_into_success(self) -> None:
        logger = logging.Logger("feature-disabled-logger-failure")
        logger.error = lambda *args, **kwargs: (_ for _ in ()).throw(  # type: ignore[method-assign]
            RuntimeError("token=secret-logger")
        )
        processors = build_feature_disabled_processors(
            error_builder=ErrorEnvelopeBuilder(sanitizer=Sanitizer()),
            logger=logger,
        )
        response = await processors["delivery.ack"].process(
            _request(
                "delivery.ack", "delivery",
                delivery={"delivery_id": "delivery_1", "attempt": 1},
            ),
            error_context=_error_context(),
        )
        self.assertEqual(
            "RUNTIME_FEATURE_DISABLED",
            response.payload.to_dict()["inline"]["error_code"],
        )
        self.assertNotIn("secret-logger", json.dumps(response.to_dict()))

    async def test_processor_contract_mismatch_is_not_a_dispatch_fallback(self) -> None:
        with self.assertRaises(Exception) as context:
            await self.processors["delivery.ack"].process(
                _request("connection.heartbeat", "connection"),
                error_context=_error_context(),
            )
        self.assertEqual("processor_contract_mismatch", context.exception.details["reason"])


if __name__ == "__main__":
    unittest.main()
