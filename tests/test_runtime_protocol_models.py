# -*- coding: utf-8 -*-
from __future__ import annotations

import unittest

from ns_common.exceptions import (
    NsRuntimeAuthContextForgedError,
    NsRuntimeEnvelopeSchemaError,
    NsRuntimeSourceForgedError,
)
from ns_runtime.protocol import (
    ENVELOPE_GROUP_NAMES,
    ExtensionsGroup,
    InboundEnvelope,
    MessageGroup,
    PayloadGroup,
    ProtocolGroup,
    SourceGroup,
    TargetGroup,
    TraceGroup,
    AuthContextGroup,
    RuntimeAuthority,
    envelope_from_mapping,
    inbound_envelope_from_mapping,
    normalize_inbound,
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
        )
        for group_type, value in group_cases:
            with self.subTest(group=group_type.__name__):
                with_unknown = dict(value)
                with_unknown["unknown"] = "no"
                with self.assertRaises(NsRuntimeEnvelopeSchemaError):
                    group_type.from_mapping(with_unknown)

        extensions = ExtensionsGroup.from_mapping({"example.plugin": {"x": 1}})
        self.assertEqual({"example.plugin": {"x": 1}}, extensions.to_dict())

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

    def test_inbound_model_cannot_contain_runtime_authority_groups(self) -> None:
        for forged_group, error_type in (
            ("source", NsRuntimeSourceForgedError),
            ("auth_context", NsRuntimeAuthContextForgedError),
        ):
            with self.subTest(group=forged_group):
                raw = _minimal_envelope()
                raw[forged_group] = {"credential": "must-not-echo"}
                with self.assertRaises(error_type) as context:
                    inbound_envelope_from_mapping(raw)
                self.assertNotIn("must-not-echo", str(context.exception))
                self.assertTrue(context.exception.details["reason"] == "runtime_authority_only")

    def test_normalization_injects_only_explicit_runtime_authority(self) -> None:
        inbound = inbound_envelope_from_mapping(_minimal_envelope())
        self.assertIsInstance(inbound, InboundEnvelope)
        self.assertFalse(hasattr(inbound, "source"))
        self.assertFalse(hasattr(inbound, "auth_context"))

        source = SourceGroup(
            runtime_id="runtime_1",
            connection_id="connection_1",
            identity_digest="sha256:identity",
            tenant_id="tenant_1",
            component_type="client",
            capabilities_digest="sha256:capabilities",
        )
        auth_context = AuthContextGroup(
            permission_snapshot_ref="tenant_1:snapshot_1",
            permission_digest="sha256:permissions",
            iam_mode="online",
            issued_at="2026-07-20T12:00:00Z",
            expires_at="2026-07-20T13:00:00Z",
        )
        normalized = normalize_inbound(
            inbound,
            authority=RuntimeAuthority(source=source, auth_context=auth_context),
        )
        self.assertIs(source, normalized.source)
        self.assertIs(auth_context, normalized.auth_context)

    def test_sender_capability_request_never_becomes_authority(self) -> None:
        raw = _minimal_envelope()
        raw["target"] = {
            "kind": "capability",
            "capabilities": ["cluster.admin"],
        }
        inbound = inbound_envelope_from_mapping(raw)
        authority = RuntimeAuthority(
            source=SourceGroup(
                runtime_id="runtime_1", connection_id="connection_1",
                identity_digest="sha256:i", tenant_id="tenant_1",
                component_type="client", capabilities_digest="sha256:read_only",
            ),
            auth_context=AuthContextGroup(
                permission_snapshot_ref="tenant_1:snapshot_1",
                permission_digest="sha256:read_only", iam_mode="online",
                issued_at="2026-07-20T12:00:00Z", expires_at="2026-07-20T13:00:00Z",
            ),
        )
        normalized = normalize_inbound(inbound, authority=authority)
        self.assertEqual(("cluster.admin",), normalized.target.capabilities)
        self.assertEqual("sha256:read_only", normalized.source.capabilities_digest)
        self.assertEqual("sha256:read_only", normalized.auth_context.permission_digest)


if __name__ == "__main__":
    unittest.main()
