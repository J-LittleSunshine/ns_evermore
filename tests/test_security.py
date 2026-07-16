# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import unittest
from dataclasses import dataclass
from urllib.parse import (
    parse_qsl,
    urlsplit,
)

from ns_common.exceptions import (
    NsValidationError,
)
from ns_common.security import (
    CIRCULAR_REFERENCE,
    MAX_DEPTH_REACHED,
    REDACTED,
    NsSanitizer,
    Sanitizer,
    sanitize,
    sanitize_text,
    sanitize_url,
)


@dataclass
class SecretRecord:
    username: str
    access_token: str
    payload: dict[str, object]
    requested_capabilities: list[str]


class SanitizerTestCase(unittest.TestCase):

    def test_nested_mapping_uses_field_rules_without_mutating_input(self) -> None:
        source = {
            "token": "token-secret",
            "payload": {"body": "payload-secret"},
            "auth_context": {"identity": "identity-secret"},
            "fencing_token": "fencing-secret",
            "capabilities": ["admin-secret", "read-secret"],
            "safe": {"message": "ordinary-value"},
        }

        result = Sanitizer().sanitize(source)

        self.assertEqual(REDACTED, result["token"])
        self.assertEqual(REDACTED, result["payload"])
        self.assertEqual(REDACTED, result["auth_context"])
        self.assertEqual(REDACTED, result["fencing_token"])
        self.assertRegex(
            result["capabilities"],
            r"^\[REDACTED sha256:[0-9a-f]{16}\]$",
        )
        self.assertEqual("ordinary-value", result["safe"]["message"])
        self.assertEqual("token-secret", source["token"])
        self.assertEqual(
            {"body": "payload-secret"},
            source["payload"],
        )
        serialized = json.dumps(result, ensure_ascii=False)
        for secret in (
            "token-secret",
            "payload-secret",
            "identity-secret",
            "fencing-secret",
            "admin-secret",
            "read-secret",
        ):
            self.assertNotIn(secret, serialized)

    def test_path_rules_cover_signed_url_peer_and_certificate(self) -> None:
        source = {
            "payload_ref": {
                "url": "https://objects.example.test/private?signature=url-secret",
                "object_id": "safe-object-id",
            },
            "peer": {"address": "192.0.2.10:443"},
            "certificate": {"fingerprint": "certificate-secret"},
        }

        result = Sanitizer().sanitize(source)

        self.assertEqual(REDACTED, result["payload_ref"]["url"])
        self.assertEqual(
            "safe-object-id",
            result["payload_ref"]["object_id"],
        )
        self.assertRegex(
            result["peer"]["address"],
            r"^\[REDACTED sha256:[0-9a-f]{16}\]$",
        )
        self.assertRegex(
            result["certificate"]["fingerprint"],
            r"^\[REDACTED sha256:[0-9a-f]{16}\]$",
        )
        serialized = json.dumps(result)
        self.assertNotIn("url-secret", serialized)
        self.assertNotIn("192.0.2.10", serialized)
        self.assertNotIn("certificate-secret", serialized)

    def test_dataclass_and_regular_object_fields_are_sanitized(self) -> None:
        record = SecretRecord(
            username="safe-user",
            access_token="dataclass-token",
            payload={"raw": "dataclass-payload"},
            requested_capabilities=["dataclass-capability"],
        )

        class Connection:
            def __init__(self) -> None:
                self.connection_id = "safe-connection-id"
                self.peer_address = "198.51.100.8:8443"

        dataclass_result = Sanitizer().sanitize(record)
        object_result = Sanitizer().sanitize(Connection())

        self.assertEqual("SecretRecord", dataclass_result["__type__"])
        self.assertEqual("safe-user", dataclass_result["username"])
        self.assertEqual(REDACTED, dataclass_result["access_token"])
        self.assertEqual(REDACTED, dataclass_result["payload"])
        self.assertNotIn(
            "dataclass-capability",
            dataclass_result["requested_capabilities"],
        )
        self.assertEqual("Connection", object_result["__type__"])
        self.assertEqual(
            "safe-connection-id",
            object_result["connection_id"],
        )
        self.assertNotIn("198.51.100.8", object_result["peer_address"])

    def test_exception_message_and_details_are_sanitized(self) -> None:
        error = NsValidationError(
            "token=message-secret is invalid.",
            details={
                "access_token": "details-token",
                "payload": {"value": "details-payload"},
                "safe_detail": "safe-value",
            },
        )

        result = Sanitizer().sanitize(error)

        self.assertEqual("NsValidationError", result["type"])
        self.assertEqual("NS_VALIDATION_ERROR", result["code"])
        self.assertEqual(100200, result["numeric_code"])
        self.assertIn(REDACTED, result["message"])
        self.assertEqual(REDACTED, result["details"]["access_token"])
        self.assertEqual(REDACTED, result["details"]["payload"])
        self.assertEqual("safe-value", result["details"]["safe_detail"])
        serialized = json.dumps(result)
        self.assertNotIn("message-secret", serialized)
        self.assertNotIn("details-token", serialized)
        self.assertNotIn("details-payload", serialized)

    def test_url_removes_userinfo_and_sensitive_query_values(self) -> None:
        result = Sanitizer().sanitize_url(
            "https://user:password@example.test:8443/object"
            "?part=1&token=query-secret&X-Amz-Signature=signature-secret"
            "#fragment-secret"
        )
        parsed = urlsplit(result)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))

        self.assertEqual("example.test:8443", parsed.netloc)
        self.assertEqual("1", query["part"])
        self.assertEqual(REDACTED, query["token"])
        self.assertEqual(REDACTED, query["X-Amz-Signature"])
        self.assertEqual(REDACTED, parsed.fragment)
        for secret in (
            "user",
            "password",
            "query-secret",
            "signature-secret",
            "fragment-secret",
        ):
            self.assertNotIn(secret, result)

    def test_free_text_redacts_bearer_assignments_and_embedded_urls(self) -> None:
        result = Sanitizer().sanitize_text(
            "Authorization: Bearer bearer-secret; token=plain-secret; "
            "fetch=https://example.test/item?signature=url-secret&part=1"
        )

        self.assertIn(REDACTED, result)
        self.assertIn("part=1", result)
        for secret in ("bearer-secret", "plain-secret", "url-secret"):
            self.assertNotIn(secret, result)

    def test_digest_is_deterministic_and_does_not_reveal_value(self) -> None:
        sanitizer = Sanitizer()
        first = sanitizer.sanitize(
            ["alpha-secret", "beta-secret"],
            field_name="capabilities",
        )
        second = sanitizer.sanitize(
            ["alpha-secret", "beta-secret"],
            field_name="capabilities",
        )
        different = sanitizer.sanitize(
            ["other-secret"],
            field_name="capabilities",
        )

        self.assertEqual(first, second)
        self.assertNotEqual(first, different)
        self.assertNotIn("alpha-secret", first)
        self.assertNotIn("beta-secret", first)

    def test_cycles_and_depth_are_bounded(self) -> None:
        circular: dict[str, object] = {}
        circular["self"] = circular
        circular_result = Sanitizer().sanitize(circular)
        depth_result = Sanitizer(max_depth=1).sanitize({
            "outer": {"inner": {"safe": "too-deep"}},
        })

        self.assertEqual(CIRCULAR_REFERENCE, circular_result["self"])
        self.assertEqual(MAX_DEPTH_REACHED, depth_result["outer"]["inner"])

    def test_public_helpers_and_validation_are_stable(self) -> None:
        self.assertIs(NsSanitizer, Sanitizer)
        self.assertEqual(REDACTED, sanitize("secret", field_name="token"))
        self.assertNotIn(
            "helper-secret",
            sanitize_url("https://example.test/?token=helper-secret"),
        )
        self.assertNotIn(
            "helper-secret",
            sanitize_text("Bearer helper-secret"),
        )

        invalid_calls = (
            lambda: Sanitizer(max_depth=0),
            lambda: Sanitizer(max_depth=True),
            lambda: Sanitizer().sanitize({}, field_name=""),
            lambda: Sanitizer().sanitize({}, path="not-a-path"),
            lambda: Sanitizer().sanitize_url(1),
            lambda: Sanitizer().sanitize_text(None),
        )
        for call in invalid_calls:
            with self.subTest(call=call):
                with self.assertRaises(NsValidationError):
                    call()


if __name__ == "__main__":
    unittest.main()
