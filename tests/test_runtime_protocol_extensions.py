# -*- coding: utf-8 -*-
from __future__ import annotations

import unittest

from ns_common.exceptions import (
    NsRuntimeEnvelopeSchemaError,
    NsRuntimeUnauthorizedMessageTypeError,
)
from ns_runtime.protocol import (
    ExtensionNamespaceContract,
    ExtensionNamespaceRegistry,
    ExtensionObjectSchema,
    ExtensionsGroup,
    UnknownExtensionPolicy,
    envelope_from_mapping,
)


def _contract(*, enabled: bool = True) -> ExtensionNamespaceContract:
    return ExtensionNamespaceContract(
        namespace="com.example.safe",
        schema=ExtensionObjectSchema(
            required_fields=("mode",),
            optional_fields=("hint",),
        ),
        required_capabilities=("extension.example.use",),
        enabled=enabled,
    )


class RuntimeProtocolExtensionsTestCase(unittest.TestCase):
    def test_wire_shape_uses_direct_namespace_keys(self) -> None:
        envelope = envelope_from_mapping({
            "protocol": {"major": 1, "minor": 0, "patch": 0},
            "message": {
                "message_id": "message_1", "type": "task.dispatch",
                "category": "task", "priority": 0,
                "created_at": "2026-07-20T12:00:00Z",
            },
            "extensions": {"com.example.safe": {"mode": "fast"}},
        })
        self.assertEqual(
            {"com.example.safe": {"mode": "fast"}},
            envelope.to_dict()["extensions"],
        )

    def test_registered_enabled_authorized_namespace_is_accepted(self) -> None:
        extensions = ExtensionsGroup.from_mapping({
            "com.example.safe": {"mode": "fast", "hint": "bounded"},
        })
        result = ExtensionNamespaceRegistry((_contract(),)).validate(
            extensions,
            authorized_capabilities=frozenset({"extension.example.use"}),
        )
        self.assertEqual(0, result.ignored_count)
        self.assertFalse(result.audit_required)
        self.assertEqual({"mode": "fast", "hint": "bounded"}, dict(result.accepted["com.example.safe"]))

    def test_unregistered_namespace_is_rejected_or_ignored_with_audit(self) -> None:
        secret_namespace = "com.attacker.secret"
        extensions = ExtensionsGroup.from_mapping({secret_namespace: {"token": "secret"}})
        with self.assertRaises(NsRuntimeEnvelopeSchemaError) as rejected:
            ExtensionNamespaceRegistry().validate(
                extensions,
                authorized_capabilities=frozenset(),
            )
        self.assertEqual("namespace_not_registered", rejected.exception.details["reason"])
        self.assertNotIn(secret_namespace, str(rejected.exception))
        self.assertNotIn("secret", str(rejected.exception))

        ignored = ExtensionNamespaceRegistry(
            unknown_policy=UnknownExtensionPolicy.IGNORE_AND_AUDIT,
        ).validate(extensions, authorized_capabilities=frozenset())
        self.assertEqual({}, dict(ignored.accepted))
        self.assertEqual(1, ignored.ignored_count)
        self.assertTrue(ignored.audit_required)

    def test_invalid_wire_namespaces_fail_before_unknown_policy(self) -> None:
        invalid_namespaces = (
            "INVALID NAMESPACE",
            "com",
            ".example",
            "com.",
            "Com.Example",
            "com.example!",
        )
        for policy in UnknownExtensionPolicy:
            registry = ExtensionNamespaceRegistry(unknown_policy=policy)
            for namespace in invalid_namespaces:
                with self.subTest(policy=policy.value, namespace=namespace):
                    extensions = ExtensionsGroup.from_mapping({namespace: {"x": 1}})
                    with self.assertRaises(NsRuntimeEnvelopeSchemaError) as context:
                        registry.validate(
                            extensions,
                            authorized_capabilities=frozenset(),
                        )
                    self.assertEqual(
                        {
                            "group": "extensions",
                            "field": "$namespace",
                            "reason": "invalid_namespace",
                        },
                        context.exception.details,
                    )
                    self.assertNotIn(namespace, str(context.exception))

    def test_disabled_unauthorized_and_schema_failures_are_distinct(self) -> None:
        cases = (
            (
                ExtensionNamespaceRegistry((_contract(enabled=False),)),
                {"mode": "fast"}, frozenset({"extension.example.use"}),
                NsRuntimeEnvelopeSchemaError, "namespace_disabled",
            ),
            (
                ExtensionNamespaceRegistry((_contract(),)),
                {"mode": "fast"}, frozenset(),
                NsRuntimeUnauthorizedMessageTypeError, "extension_capability_required",
            ),
            (
                ExtensionNamespaceRegistry((_contract(),)),
                {"hint": "missing mode"}, frozenset({"extension.example.use"}),
                NsRuntimeEnvelopeSchemaError, "extension_field_missing",
            ),
            (
                ExtensionNamespaceRegistry((_contract(),)),
                {"mode": "fast", "admin": True}, frozenset({"extension.example.use"}),
                NsRuntimeEnvelopeSchemaError, "extension_field_not_allowed",
            ),
        )
        for registry, value, capabilities, error_type, reason in cases:
            with self.subTest(reason=reason):
                with self.assertRaises(error_type) as context:
                    registry.validate(
                        ExtensionsGroup.from_mapping({"com.example.safe": value}),
                        authorized_capabilities=capabilities,
                    )
                self.assertEqual(reason, context.exception.details["reason"])


if __name__ == "__main__":
    unittest.main()
