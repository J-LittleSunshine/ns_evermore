# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import unittest

from ns_common.exceptions import (
    NsRuntimeFeatureDisabledError,
    NsRuntimeSourceForgedError,
)
from ns_common.security import Sanitizer
from ns_runtime.protocol import (
    BUILTIN_MESSAGE_REGISTRY,
    CURRENT_PROTOCOL_SCHEMA_KEY,
    ErrorEnvelopeBuilder,
    ErrorEnvelopeContext,
    ProtocolGroup,
    SourceGroup,
)


def _context() -> ErrorEnvelopeContext:
    return ErrorEnvelopeContext(
        protocol=ProtocolGroup(major=1, minor=0, patch=0),
        source=SourceGroup(
            runtime_id="runtime_1", connection_id="connection_1",
            identity_digest="sha256:runtime", tenant_id="tenant_1",
            component_type="runtime", capabilities_digest="sha256:protocol",
        ),
        error_message_id="message_error_1",
        created_at="2026-07-20T12:00:00Z",
        referenced_message_id="message_request_1",
        referenced_delivery_id="delivery_1",
    )


class RuntimeProtocolErrorEnvelopeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = ErrorEnvelopeBuilder(sanitizer=Sanitizer())

    def test_registered_error_uses_only_err_1_metadata(self) -> None:
        error = NsRuntimeFeatureDisabledError(
            "token=secret-message",
            details={"payload": "secret-payload", "credential": "secret-credential"},
        )
        envelope = self.builder.build(error, context=_context())
        payload = envelope.payload.to_dict()["inline"]
        self.assertEqual("RUNTIME_FEATURE_DISABLED", payload["error_code"])
        self.assertEqual(200165, payload["numeric_code"])
        self.assertEqual("Runtime feature is disabled.", payload["message"])
        self.assertTrue(payload["audit_required"])
        self.assertEqual({"action": "reject_disabled_feature"}, payload["detail"])
        encoded = json.dumps(envelope.to_dict(), sort_keys=True)
        for secret in ("secret-message", "secret-payload", "secret-credential"):
            self.assertNotIn(secret, encoded)
        self.assertIs(
            envelope,
            BUILTIN_MESSAGE_REGISTRY.validate_envelope(
                envelope,
                CURRENT_PROTOCOL_SCHEMA_KEY,
            ),
        )

    def test_security_error_preserves_stable_policy_without_details(self) -> None:
        envelope = self.builder.build(
            NsRuntimeSourceForgedError(details={"source": "token=secret"}),
            context=_context(),
        )
        payload = envelope.payload.to_dict()["inline"]
        self.assertEqual("critical", payload["severity"])
        self.assertEqual("security", payload["category"])
        self.assertTrue(payload["disconnect_required"])
        self.assertTrue(payload["audit_required"])
        self.assertNotIn("source", payload["detail"])

    def test_unknown_exception_never_stringifies_and_maps_to_generic_runtime_error(self) -> None:
        class DangerousError(Exception):
            def __str__(self) -> str:
                raise AssertionError("must not stringify")

            def __repr__(self) -> str:
                raise AssertionError("must not repr")

        envelope = self.builder.build(DangerousError(), context=_context())
        payload = envelope.payload.to_dict()["inline"]
        self.assertEqual("NS_RUNTIME_ERROR", payload["error_code"])
        self.assertEqual("NsEvermore runtime error.", payload["message"])

    def test_process_level_exceptions_are_not_swallowed(self) -> None:
        for error in (KeyboardInterrupt(), SystemExit()):
            with self.subTest(error=type(error).__name__):
                with self.assertRaises(type(error)):
                    self.builder.build(error, context=_context())


if __name__ == "__main__":
    unittest.main()
