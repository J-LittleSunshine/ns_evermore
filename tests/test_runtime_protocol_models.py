# -*- coding: utf-8 -*-
from __future__ import annotations

import unittest

from ns_common.exceptions import NsRuntimeEnvelopeSchemaError
from ns_runtime.protocol import (
    ENVELOPE_GROUP_NAMES,
    ExtensionsGroup,
    MessageGroup,
    PayloadGroup,
    ProtocolGroup,
    SourceGroup,
    TargetGroup,
    TraceGroup,
    envelope_from_mapping,
)


def _minimal_envelope() -> dict[str, object]:
    return {
        "protocol": {"major": 1, "minor": 0, "patch": 0},
        "message": {
            "message_id": "message_123",
            "type": "task.dispatch",
            "category": "task",
            "priority": 0,
            "created_at": "2026-07-20T12:00:00Z",
        },
    }


class RuntimeProtocolModelTestCase(unittest.TestCase):
    def test_all_frozen_core_groups_are_present_in_the_fixed_order(self) -> None:
        self.assertEqual(
            (
                "protocol", "message", "source", "target", "route", "delivery",
                "stream", "auth_context", "payload", "callback", "trace", "extensions",
            ),
            ENVELOPE_GROUP_NAMES,
        )

    def test_minimal_envelope_uses_typed_groups_and_round_trips(self) -> None:
        raw = _minimal_envelope()
        envelope = envelope_from_mapping(raw)
        self.assertIsInstance(envelope.protocol, ProtocolGroup)
        self.assertIsInstance(envelope.message, MessageGroup)
        self.assertEqual(
            {
                **raw,
                "message": {**raw["message"], "reliability": "best_effort"},
            },
            envelope.to_dict(),
        )

    def test_top_level_and_every_group_reject_unknown_fields(self) -> None:
        raw = _minimal_envelope()
        raw["unknown"] = True
        with self.assertRaises(NsRuntimeEnvelopeSchemaError):
            envelope_from_mapping(raw)

        group_cases = (
            (ProtocolGroup, {"major": 1, "minor": 0, "patch": 0}),
            (MessageGroup, _minimal_envelope()["message"]),
            (SourceGroup, {
                "runtime_id": "runtime_1", "connection_id": "connection_1",
                "identity_digest": "sha256:a", "tenant_id": "tenant_1",
                "component_type": "client", "capabilities_digest": "sha256:b",
            }),
            (TargetGroup, {"kind": "runtime", "runtime_id": "runtime_2"}),
            (PayloadGroup, {"mode": "inline", "inline": {"answer": 42}}),
            (TraceGroup, {"trace_id": "trace_1"}),
            (ExtensionsGroup, {"namespaces": {"example.plugin": {"x": 1}}}),
        )
        for group_type, value in group_cases:
            with self.subTest(group=group_type.__name__):
                with_unknown = dict(value)
                with_unknown["unknown"] = "no"
                with self.assertRaises(NsRuntimeEnvelopeSchemaError):
                    group_type.from_mapping(with_unknown)

    def test_null_empty_and_mutable_payload_placeholders_are_rejected_or_frozen(self) -> None:
        raw = _minimal_envelope()
        raw["target"] = None
        with self.assertRaises(NsRuntimeEnvelopeSchemaError):
            envelope_from_mapping(raw)

        inline = {"nested": [1, {"ok": True}]}
        payload = PayloadGroup(mode="inline", inline=inline)
        inline["nested"] = []
        self.assertEqual(
            {"mode": "inline", "inline": {"nested": [1, {"ok": True}]}},
            payload.to_dict(),
        )

    def test_error_details_never_echo_unknown_values(self) -> None:
        secret = "credential-do-not-copy"
        raw = _minimal_envelope()
        raw[secret] = object()
        with self.assertRaises(NsRuntimeEnvelopeSchemaError) as context:
            envelope_from_mapping(raw)
        self.assertNotIn(secret, str(context.exception))
        self.assertNotIn("value", context.exception.details)


if __name__ == "__main__":
    unittest.main()
