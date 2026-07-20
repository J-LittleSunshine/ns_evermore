# -*- coding: utf-8 -*-
from __future__ import annotations

import unittest

from ns_common.exceptions import NsRuntimeEnvelopeSchemaError
from ns_runtime.protocol import (
    EnvelopeSchemaValidator,
    InlinePayloadSchema,
    MessageTypeSchema,
    envelope_from_mapping,
)


def _envelope(
    message_type: str = "connection.hello",
    **groups: object,
):
    return envelope_from_mapping({
        "protocol": {"major": 1, "minor": 0, "patch": 0},
        "message": {
            "message_id": "message_123",
            "type": message_type,
            "category": message_type.split(".", 1)[0],
            "priority": 0,
            "created_at": "2026-07-20T12:00:00Z",
        },
        **groups,
    })


class RuntimeProtocolSchemaTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = EnvelopeSchemaValidator()
        self.hello_schema = MessageTypeSchema(
            message_type="connection.hello",
            required_groups=("payload",),
            forbidden_groups=("delivery", "stream"),
            inline_payload=InlinePayloadSchema(
                required_fields=("token", "component_type"),
                optional_fields=("requested_capabilities",),
            ),
        )

    def test_base_and_exact_message_schema_are_both_applied(self) -> None:
        envelope = _envelope(payload={
            "mode": "inline",
            "inline": {"token": "opaque", "component_type": "client"},
        })
        self.assertIs(
            envelope,
            self.validator.validate(envelope, message_schema=self.hello_schema),
        )

    def test_missing_message_specific_group_or_field_is_stable(self) -> None:
        with self.assertRaises(NsRuntimeEnvelopeSchemaError) as missing_group:
            self.validator.validate(_envelope(), message_schema=self.hello_schema)
        self.assertEqual("required_group_missing", missing_group.exception.details["reason"])

        with self.assertRaises(NsRuntimeEnvelopeSchemaError) as missing_field:
            self.validator.validate(
                _envelope(payload={
                    "mode": "inline",
                    "inline": {"token": "opaque"},
                }),
                message_schema=self.hello_schema,
            )
        self.assertEqual("message_field_missing", missing_field.exception.details["reason"])
        self.assertNotIn("component_type", str(missing_field.exception))

    def test_message_specific_unknown_and_forbidden_groups_are_rejected(self) -> None:
        with self.assertRaises(NsRuntimeEnvelopeSchemaError) as unknown:
            self.validator.validate(
                _envelope(payload={
                    "mode": "inline",
                    "inline": {
                        "token": "opaque",
                        "component_type": "client",
                        "admin": True,
                    },
                }),
                message_schema=self.hello_schema,
            )
        self.assertEqual("message_field_not_allowed", unknown.exception.details["reason"])

        with self.assertRaises(NsRuntimeEnvelopeSchemaError) as forbidden:
            self.validator.validate(
                _envelope(
                    payload={
                        "mode": "inline",
                        "inline": {"token": "opaque", "component_type": "client"},
                    },
                    delivery={"delivery_id": "delivery_1", "attempt": 1},
                ),
                message_schema=self.hello_schema,
            )
        self.assertEqual("group_not_allowed", forbidden.exception.details["reason"])

    def test_base_target_route_and_delivery_invariants_cannot_be_relaxed(self) -> None:
        permissive = MessageTypeSchema(message_type="task.dispatch")
        cases = (
            (_envelope("task.dispatch", target={"kind": "runtime"}), "required_for_target_kind"),
            (_envelope("task.dispatch", route={
                "root_runtime_id": "runtime_1", "current_runtime_id": "runtime_1",
                "hop": 1, "max_hops": 2,
                "route_segment": ["runtime_1", "runtime_1"],
            }), "duplicate_route_segment"),
            (_envelope("task.dispatch", delivery={
                "delivery_id": "delivery_1", "attempt": 0,
            }), "positive_integer_required"),
        )
        for envelope, reason in cases:
            with self.subTest(reason=reason):
                with self.assertRaises(NsRuntimeEnvelopeSchemaError) as context:
                    self.validator.validate(envelope, message_schema=permissive)
                self.assertEqual(reason, context.exception.details["reason"])

    def test_schema_mismatch_is_rejected_without_echoing_message_type(self) -> None:
        forged_type = "evil.secret"
        with self.assertRaises(NsRuntimeEnvelopeSchemaError) as context:
            self.validator.validate(
                _envelope(forged_type),
                message_schema=MessageTypeSchema(message_type="task.dispatch"),
            )
        self.assertEqual("message_schema_mismatch", context.exception.details["reason"])
        self.assertNotIn(forged_type, str(context.exception))


if __name__ == "__main__":
    unittest.main()
