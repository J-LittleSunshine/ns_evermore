# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import unittest
from collections.abc import Mapping
from dataclasses import dataclass
from unittest import mock
from urllib.parse import (
    parse_qsl,
    urlsplit,
)

from ns_common.exceptions import NsValidationError
from ns_common.security import (
    CIRCULAR_REFERENCE,
    DEFAULT_SANITIZER_DIGEST_MAX_BYTES_LENGTH,
    DEFAULT_SANITIZER_DIGEST_MAX_CONTAINER_ITEMS,
    DEFAULT_SANITIZER_DIGEST_MAX_NODES,
    DEFAULT_SANITIZER_DIGEST_MAX_NORMALIZED_BYTES,
    DEFAULT_SANITIZER_DIGEST_MAX_STRING_LENGTH,
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


@dataclass
class ExplodingFieldRecord:
    message: str

    def __getattribute__(self, name: str) -> object:
        if name == "message":
            raise RuntimeError("attribute-access-secret")
        return object.__getattribute__(self, name)


class ExplodingStringError(Exception):

    def __str__(self) -> str:
        raise RuntimeError("exception-str-secret")


class ExplodingAttributeError(Exception):

    def __getattribute__(self, name: str) -> object:
        if name in {"message", "code", "numeric_code", "details"}:
            raise RuntimeError(f"exception-{name}-secret")
        return BaseException.__getattribute__(self, name)


class ExplodingItemsMapping(Mapping[object, object]):

    def __getitem__(self, key: object) -> object:
        raise KeyError(key)

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(())

    def __len__(self) -> int:
        return 0

    def items(self):  # type: ignore[no-untyped-def]
        raise RuntimeError("mapping-items-secret")


class ExplodingVarsObject:

    def __init__(self) -> None:
        object.__setattr__(self, "raw_value", "vars-business-secret")

    def __getattribute__(self, name: str) -> object:
        if name == "__dict__":
            raise RuntimeError("vars-access-secret")
        return object.__getattribute__(self, name)


class SecretObjectKey:

    def __str__(self) -> str:
        return "token=object-key-secret"


class DigestObject:
    pass


@dataclass
class WideDigestRecord:
    field_a: str
    field_b: str
    field_c: str
    field_d: str
    field_e: str


class SanitizerTestCase(unittest.TestCase):

    def assert_json_safe_and_no_leak(
        self,
        result: object,
        *secrets: str,
    ) -> str:
        serialized = json.dumps(
            result,
            allow_nan=False,
            ensure_ascii=False,
            sort_keys=True,
        )
        for secret in secrets:
            with self.subTest(secret=secret):
                self.assertNotIn(secret, serialized)
        return serialized

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
        self.assertEqual({"body": "payload-secret"}, source["payload"])
        self.assert_json_safe_and_no_leak(
            result,
            "token-secret",
            "payload-secret",
            "identity-secret",
            "fencing-secret",
            "admin-secret",
            "read-secret",
        )

    def test_structured_fields_cover_new_secrets_and_addresses(self) -> None:
        source = {
            "api_key": "api-key-secret",
            "credential": "credential-secret",
            "signature": "signature-secret",
            "task_payload": {"raw": "task-payload-secret"},
            "peer_ip": "192.0.2.11",
            "client_ip": "198.51.100.12",
            "remote_ip": "203.0.113.13",
            "peer_address": "192.0.2.21:443",
            "client_address": "198.51.100.22:443",
            "remote_address": "203.0.113.23:443",
            "certificate": "certificate-raw-secret",
            "payload_size": 2048,
            "signature_algorithm": "ed25519",
            "client_address_label": "edge-a",
        }

        result = Sanitizer().sanitize(source)

        for field_name in (
            "api_key",
            "credential",
            "signature",
            "task_payload",
            "peer_ip",
            "client_ip",
            "remote_ip",
            "peer_address",
            "client_address",
            "remote_address",
            "certificate",
        ):
            with self.subTest(field_name=field_name):
                self.assertEqual(REDACTED, result[field_name])
        self.assertEqual(2048, result["payload_size"])
        self.assertEqual("ed25519", result["signature_algorithm"])
        self.assertEqual("edge-a", result["client_address_label"])
        self.assert_json_safe_and_no_leak(
            result,
            "api-key-secret",
            "credential-secret",
            "signature-secret",
            "task-payload-secret",
            "192.0.2.11",
            "198.51.100.12",
            "203.0.113.13",
            "192.0.2.21",
            "198.51.100.22",
            "203.0.113.23",
            "certificate-raw-secret",
        )

    def test_sensitive_field_names_handle_unicode_case_and_separators(self) -> None:
        source = {
            "ACCESS-TOKEN": "令牌秘密一",
            "Client_Secret": "令牌秘密二",
            "private-key": "令牌秘密三",
            "AUTHORIZATION": "令牌秘密四",
            "Set-Cookie": "令牌秘密五",
            "ＦＥＮＣＩＮＧ＿ＴＯＫＥＮ": "令牌秘密六",
            "API-KEY": "令牌秘密七",
        }

        result = Sanitizer().sanitize(source)

        self.assertTrue(all(value == REDACTED for value in result.values()))
        self.assert_json_safe_and_no_leak(
            result,
            "令牌秘密一",
            "令牌秘密二",
            "令牌秘密三",
            "令牌秘密四",
            "令牌秘密五",
            "令牌秘密六",
            "令牌秘密七",
        )

    def test_path_rules_cover_signed_url_peer_and_certificate_digest(self) -> None:
        source = {
            "payload_ref": {
                "url": "https://objects.example.test/private?signature=url-secret",
                "object_id": "safe-object-id",
            },
            "peer": {"address": "192.0.2.10:443"},
            "tls": {"certificate_fingerprint": "certificate-secret"},
        }

        result = Sanitizer().sanitize(source)

        self.assertEqual(REDACTED, result["payload_ref"]["url"])
        self.assertEqual("safe-object-id", result["payload_ref"]["object_id"])
        self.assertEqual(REDACTED, result["peer"]["address"])
        self.assertRegex(
            result["tls"]["certificate_fingerprint"],
            r"^\[REDACTED sha256:[0-9a-f]{16}\]$",
        )
        self.assert_json_safe_and_no_leak(
            result,
            "url-secret",
            "192.0.2.10",
            "certificate-secret",
        )

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
        self.assertEqual(REDACTED, object_result["peer_address"])
        self.assert_json_safe_and_no_leak(
            {"dataclass": dataclass_result, "object": object_result},
            "dataclass-token",
            "dataclass-payload",
            "dataclass-capability",
            "198.51.100.8",
        )

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
        self.assert_json_safe_and_no_leak(
            result,
            "message-secret",
            "details-token",
            "details-payload",
        )

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
        self.assert_json_safe_and_no_leak(
            result,
            "user",
            "password",
            "query-secret",
            "signature-secret",
            "fragment-secret",
        )

    def test_authorization_headers_redact_complete_values(self) -> None:
        result = Sanitizer().sanitize_text(
            "Authorization: Basic basic-secret trailing-basic-secret\r\n"
            "Authorization: Digest username=alice, response=digest-secret\n"
            "Authorization: ApiKey api-key-header-secret with-spaces\n"
            "Proxy-Authorization: Basic proxy-secret more-proxy-secret\n"
            "Safe-Header: visible"
        )

        self.assertEqual(4, result.count(REDACTED))
        self.assertIn("Safe-Header: visible", result)
        self.assert_json_safe_and_no_leak(
            result,
            "basic-secret",
            "trailing-basic-secret",
            "alice",
            "digest-secret",
            "api-key-header-secret",
            "with-spaces",
            "proxy-secret",
            "more-proxy-secret",
        )

    def test_cookie_headers_redact_all_segments(self) -> None:
        result = Sanitizer().sanitize_text(
            "Cookie: a=cookie-a-secret; b=cookie-b-secret; c=cookie-c-secret\n"
            "Set-Cookie: session=set-cookie-secret; Path=/; HttpOnly; Secure\n"
            "ordinary=visible"
        )

        self.assertEqual(2, result.count(REDACTED))
        self.assertIn("ordinary=visible", result)
        self.assert_json_safe_and_no_leak(
            result,
            "cookie-a-secret",
            "cookie-b-secret",
            "cookie-c-secret",
            "set-cookie-secret",
            "HttpOnly",
            "Secure",
        )

    def test_free_text_keeps_bearer_assignments_and_urls_compatible(self) -> None:
        result = Sanitizer().sanitize_text(
            "Bearer bearer-secret; token=plain-secret; signature=sig-secret; "
            "fetch=https://example.test/item?signature=url-secret&part=1"
        )

        self.assertIn(REDACTED, result)
        self.assertIn("part=1", result)
        self.assert_json_safe_and_no_leak(
            result,
            "bearer-secret",
            "plain-secret",
            "sig-secret",
            "url-secret",
        )

    def test_mapping_keys_are_sanitized_and_non_strings_are_safe(self) -> None:
        source = {
            "token=key-token-secret": "safe-one",
            "https://example.test/?signature=url-key-secret": "safe-two",
            "Authorization: Basic key-auth-secret": "safe-three",
            SecretObjectKey(): "safe-four",
            42: "safe-five",
        }

        result = Sanitizer().sanitize(source)

        self.assertTrue(all(isinstance(key, str) for key in result))
        self.assertIn("<SecretObjectKey>", result)
        self.assertIn("<int>", result)
        self.assert_json_safe_and_no_leak(
            result,
            "key-token-secret",
            "url-key-secret",
            "key-auth-secret",
            "object-key-secret",
        )

    def test_mapping_key_redaction_collisions_do_not_overwrite(self) -> None:
        source = {
            "token=first-key-secret": "first-value",
            "token=second-key-secret": "second-value",
            "signature=third-key-secret": "third-value",
            "signature=fourth-key-secret": "fourth-value",
        }

        result = Sanitizer().sanitize(source)

        self.assertEqual(4, len(result))
        self.assertEqual("first-value", result["token=[REDACTED]"])
        self.assertEqual("second-value", result["token=[REDACTED]#2"])
        self.assertEqual("third-value", result["signature=[REDACTED]"])
        self.assertEqual("fourth-value", result["signature=[REDACTED]#2"])
        self.assert_json_safe_and_no_leak(
            result,
            "first-key-secret",
            "second-key-secret",
            "third-key-secret",
            "fourth-key-secret",
        )

    def test_non_finite_numbers_are_strict_json_safe(self) -> None:
        source = {
            "nan": float("nan"),
            "positive": float("inf"),
            "negative": float("-inf"),
            "nested": [float("nan"), float("inf"), float("-inf")],
            float("inf"): "non-finite-key-value",
            "token": "non-finite-token-secret",
        }

        result = Sanitizer().sanitize(source)

        self.assertEqual("[NON_FINITE_NUMBER]", result["nan"])
        self.assertEqual("[NON_FINITE_NUMBER]", result["positive"])
        self.assertEqual("[NON_FINITE_NUMBER]", result["negative"])
        self.assertEqual(
            ["[NON_FINITE_NUMBER]"] * 3,
            result["nested"],
        )
        self.assertIn("<float>", result)
        self.assert_json_safe_and_no_leak(
            result,
            "non-finite-token-secret",
        )

    def test_exception_str_failure_is_fail_closed(self) -> None:
        error = ExplodingStringError("exception-business-secret")

        result = Sanitizer().sanitize(error)

        self.assertEqual("ExplodingStringError", result["type"])
        self.assertEqual("[SANITIZATION_FAILED]", result["message"])
        self.assert_json_safe_and_no_leak(
            result,
            "exception-business-secret",
            "exception-str-secret",
        )

    def test_exception_attribute_failures_are_fail_closed(self) -> None:
        error = ExplodingAttributeError("attribute-business-secret")

        result = Sanitizer().sanitize(error)

        self.assertEqual("[SANITIZATION_FAILED]", result["message"])
        self.assertEqual("[SANITIZATION_FAILED]", result["code"])
        self.assertEqual("[SANITIZATION_FAILED]", result["numeric_code"])
        self.assertEqual("[SANITIZATION_FAILED]", result["details"])
        self.assert_json_safe_and_no_leak(
            result,
            "attribute-business-secret",
            "exception-message-secret",
            "exception-code-secret",
            "exception-numeric_code-secret",
            "exception-details-secret",
        )

    def test_mapping_items_failure_is_fail_closed(self) -> None:
        result = Sanitizer().sanitize(ExplodingItemsMapping())

        self.assertEqual("[SANITIZATION_FAILED]", result)
        self.assert_json_safe_and_no_leak(result, "mapping-items-secret")

    def test_vars_and_dataclass_attribute_failures_are_fail_closed(self) -> None:
        vars_result = Sanitizer().sanitize(ExplodingVarsObject())
        dataclass_result = Sanitizer().sanitize(
            ExplodingFieldRecord("attribute-business-secret")
        )

        self.assertEqual("[SANITIZATION_FAILED]", vars_result)
        self.assertEqual(
            "[SANITIZATION_FAILED]",
            dataclass_result["message"],
        )
        self.assert_json_safe_and_no_leak(
            {"vars": vars_result, "dataclass": dataclass_result},
            "vars-business-secret",
            "vars-access-secret",
            "attribute-business-secret",
            "attribute-access-secret",
        )

    def test_digest_callback_failure_is_fail_closed(self) -> None:
        with mock.patch.object(
            Sanitizer,
            "_normalize_digest_value",
            side_effect=RuntimeError("digest-callback-secret"),
        ):
            result = Sanitizer().sanitize(
                DigestObject(),
                field_name="capabilities",
            )

        self.assertEqual(REDACTED, result)
        self.assert_json_safe_and_no_leak(result, "digest-callback-secret")

    def test_digest_rejects_bytes_over_limit_without_leaking(self) -> None:
        sanitizer = Sanitizer(max_digest_bytes_length=8)
        boundary_secret = b"byte-sec"
        oversized_secret = b"byte-limit-secret"

        boundary_result = sanitizer.sanitize(
            boundary_secret,
            field_name="capabilities",
        )
        oversized_result = sanitizer.sanitize(
            oversized_secret,
            field_name="capabilities",
        )

        self.assertEqual(
            "[REDACTED sha256:"
            f"{hashlib.sha256(boundary_secret).hexdigest()[:16]}]",
            boundary_result,
        )
        self.assertEqual(REDACTED, oversized_result)
        self.assert_json_safe_and_no_leak(
            {"boundary": boundary_result, "oversized": oversized_result},
            boundary_secret.decode("ascii"),
            oversized_secret.decode("ascii"),
            oversized_secret.hex(),
        )

    def test_digest_string_and_normalized_byte_limits_have_boundaries(self) -> None:
        string_limited = Sanitizer(max_digest_string_length=8)
        string_boundary = string_limited.sanitize(
            "strsec01",
            field_name="capabilities",
        )
        string_oversized = string_limited.sanitize(
            "strsec012",
            field_name="capabilities",
        )
        normalized_boundary = Sanitizer(
            max_digest_normalized_bytes=11,
        ).sanitize("normsec1", field_name="capabilities")
        normalized_oversized = Sanitizer(
            max_digest_normalized_bytes=10,
        ).sanitize("normsec1", field_name="capabilities")

        self.assertRegex(
            string_boundary,
            r"^\[REDACTED sha256:[0-9a-f]{16}\]$",
        )
        self.assertEqual(REDACTED, string_oversized)
        self.assertRegex(
            normalized_boundary,
            r"^\[REDACTED sha256:[0-9a-f]{16}\]$",
        )
        self.assertEqual(REDACTED, normalized_oversized)
        self.assert_json_safe_and_no_leak(
            {
                "string_boundary": string_boundary,
                "string_oversized": string_oversized,
                "normalized_boundary": normalized_boundary,
                "normalized_oversized": normalized_oversized,
            },
            "strsec01",
            "strsec012",
            "normsec1",
        )

    def test_digest_rejects_wide_capabilities_and_mapping(self) -> None:
        sanitizer = Sanitizer(max_digest_container_items=3)
        capabilities = [
            "wide-capability-secret-a",
            "wide-capability-secret-b",
            "wide-capability-secret-c",
            "wide-capability-secret-d",
        ]
        wide_mapping = {
            f"safe-key-{index}": f"wide-mapping-secret-{index}"
            for index in range(4)
        }

        capabilities_result = sanitizer.sanitize(
            capabilities,
            field_name="capabilities",
        )
        mapping_result = sanitizer.sanitize(
            wide_mapping,
            field_name="allowed_capabilities",
        )

        self.assertEqual(REDACTED, capabilities_result)
        self.assertEqual(REDACTED, mapping_result)
        self.assert_json_safe_and_no_leak(
            {"capabilities": capabilities_result, "mapping": mapping_result},
            *capabilities,
            *wide_mapping.values(),
        )

    def test_digest_depth_and_circular_references_are_bounded(self) -> None:
        deep_secret = "deep-digest-secret"
        deep_value = [[[deep_secret]]]
        circular: dict[str, object] = {
            "value": "circular-digest-secret",
        }
        circular["self"] = circular

        deep_result = Sanitizer(max_depth=2).sanitize(
            deep_value,
            field_name="capabilities",
        )
        nested_path_result = Sanitizer(max_depth=1).sanitize({
            "outer": {"capabilities": ["path-depth-secret"]},
        })
        circular_first = Sanitizer().sanitize(
            circular,
            field_name="capabilities",
        )
        circular_second = Sanitizer().sanitize(
            circular,
            field_name="capabilities",
        )

        self.assertEqual(REDACTED, deep_result)
        self.assertEqual(REDACTED, nested_path_result["outer"]["capabilities"])
        self.assertEqual(circular_first, circular_second)
        self.assertRegex(
            circular_first,
            r"^\[REDACTED sha256:[0-9a-f]{16}\]$",
        )
        self.assert_json_safe_and_no_leak(
            {
                "deep": deep_result,
                "nested_path": nested_path_result,
                "circular": circular_first,
            },
            deep_secret,
            "path-depth-secret",
            "circular-digest-secret",
        )

    def test_digest_rejects_wide_dataclass_and_regular_object(self) -> None:
        record = WideDigestRecord(
            "dataclass-digest-secret-a",
            "dataclass-digest-secret-b",
            "dataclass-digest-secret-c",
            "dataclass-digest-secret-d",
            "dataclass-digest-secret-e",
        )

        class WideObject:
            def __init__(self) -> None:
                for index in range(5):
                    setattr(self, f"field_{index}", f"object-digest-secret-{index}")

        sanitizer = Sanitizer(max_digest_container_items=4)
        dataclass_result = sanitizer.sanitize(
            record,
            field_name="capabilities",
        )
        object_result = sanitizer.sanitize(
            WideObject(),
            field_name="capabilities",
        )

        self.assertEqual(REDACTED, dataclass_result)
        self.assertEqual(REDACTED, object_result)
        self.assert_json_safe_and_no_leak(
            {"dataclass": dataclass_result, "object": object_result},
            "dataclass-digest-secret-a",
            "dataclass-digest-secret-b",
            "dataclass-digest-secret-c",
            "dataclass-digest-secret-d",
            "dataclass-digest-secret-e",
            "object-digest-secret-0",
            "object-digest-secret-1",
            "object-digest-secret-2",
            "object-digest-secret-3",
            "object-digest-secret-4",
        )

    def test_digest_container_and_node_limits_have_boundaries(self) -> None:
        container_limited = Sanitizer(max_digest_container_items=3)
        container_boundary_values = [
            "container-secret-a",
            "container-secret-b",
            "container-secret-c",
        ]
        container_boundary = container_limited.sanitize(
            container_boundary_values,
            field_name="capabilities",
        )
        container_oversized = container_limited.sanitize(
            container_boundary_values + ["container-secret-d"],
            field_name="capabilities",
        )
        node_boundary = Sanitizer(max_digest_nodes=3).sanitize(
            ["node-secret-a", "node-secret-b"],
            field_name="capabilities",
        )
        node_oversized = Sanitizer(max_digest_nodes=2).sanitize(
            ["node-secret-a", "node-secret-b"],
            field_name="capabilities",
        )

        self.assertRegex(
            container_boundary,
            r"^\[REDACTED sha256:[0-9a-f]{16}\]$",
        )
        self.assertEqual(REDACTED, container_oversized)
        self.assertRegex(
            node_boundary,
            r"^\[REDACTED sha256:[0-9a-f]{16}\]$",
        )
        self.assertEqual(REDACTED, node_oversized)
        self.assert_json_safe_and_no_leak(
            {
                "container_boundary": container_boundary,
                "container_oversized": container_oversized,
                "node_boundary": node_boundary,
                "node_oversized": node_oversized,
            },
            *container_boundary_values,
            "container-secret-d",
            "node-secret-a",
            "node-secret-b",
        )

    def test_digest_mapping_and_sets_are_order_stable(self) -> None:
        sanitizer = Sanitizer()
        first_mapping = {
            "alpha": "mapping-order-secret-a",
            "beta": "mapping-order-secret-b",
        }
        second_mapping = {
            "beta": "mapping-order-secret-b",
            "alpha": "mapping-order-secret-a",
        }
        mapping_first = sanitizer.sanitize(
            first_mapping,
            field_name="capabilities",
        )
        mapping_second = sanitizer.sanitize(
            second_mapping,
            field_name="capabilities",
        )
        set_first = sanitizer.sanitize(
            {"set-order-secret-a", "set-order-secret-b"},
            field_name="capabilities",
        )
        set_second = sanitizer.sanitize(
            {"set-order-secret-b", "set-order-secret-a"},
            field_name="capabilities",
        )
        frozen_first = sanitizer.sanitize(
            frozenset({"frozen-order-secret-a", "frozen-order-secret-b"}),
            field_name="capabilities",
        )
        frozen_second = sanitizer.sanitize(
            frozenset({"frozen-order-secret-b", "frozen-order-secret-a"}),
            field_name="capabilities",
        )
        different = sanitizer.sanitize(
            {"alpha": "mapping-order-secret-c"},
            field_name="capabilities",
        )

        self.assertEqual(mapping_first, mapping_second)
        self.assertEqual(set_first, set_second)
        self.assertEqual(frozen_first, frozen_second)
        self.assertNotEqual(mapping_first, different)
        self.assert_json_safe_and_no_leak(
            {
                "mapping_first": mapping_first,
                "mapping_second": mapping_second,
                "set_first": set_first,
                "set_second": set_second,
                "frozen_first": frozen_first,
                "frozen_second": frozen_second,
                "different": different,
            },
            "mapping-order-secret-a",
            "mapping-order-secret-b",
            "mapping-order-secret-c",
            "set-order-secret-a",
            "set-order-secret-b",
            "frozen-order-secret-a",
            "frozen-order-secret-b",
        )

    def test_digest_process_level_exceptions_are_not_swallowed(self) -> None:
        class InterruptingDigestMapping(ExplodingItemsMapping):
            def items(self):  # type: ignore[no-untyped-def]
                raise KeyboardInterrupt("digest-interrupt-secret")

        class ExitingDigestObject:
            def __getattribute__(self, name: str) -> object:
                if name == "__dict__":
                    raise SystemExit("digest-exit-secret")
                return object.__getattribute__(self, name)

        with self.assertRaises(KeyboardInterrupt):
            Sanitizer().sanitize(
                InterruptingDigestMapping(),
                field_name="capabilities",
            )
        with self.assertRaises(SystemExit):
            Sanitizer().sanitize(
                ExitingDigestObject(),
                field_name="capabilities",
            )
        self.assert_json_safe_and_no_leak(
            {"status": "digest-process-exceptions-propagated"},
            "digest-interrupt-secret",
            "digest-exit-secret",
        )

    def test_process_level_exceptions_are_not_swallowed(self) -> None:
        class InterruptingMapping(ExplodingItemsMapping):
            def items(self):  # type: ignore[no-untyped-def]
                raise KeyboardInterrupt("interrupt-secret")

        class ExitingError(Exception):
            def __str__(self) -> str:
                raise SystemExit("exit-secret")

        with self.assertRaises(KeyboardInterrupt):
            Sanitizer().sanitize(InterruptingMapping())
        with self.assertRaises(SystemExit):
            Sanitizer().sanitize(ExitingError("business-secret"))
        self.assert_json_safe_and_no_leak(
            {"status": "process-exceptions-propagated"},
            "interrupt-secret",
            "exit-secret",
            "business-secret",
        )

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
        self.assert_json_safe_and_no_leak(
            {"first": first, "second": second, "different": different},
            "alpha-secret",
            "beta-secret",
            "other-secret",
        )

    def test_cycles_and_depth_are_bounded(self) -> None:
        circular: dict[str, object] = {}
        circular["self"] = circular
        circular["token"] = "circular-token-secret"
        circular_result = Sanitizer().sanitize(circular)
        depth_result = Sanitizer(max_depth=1).sanitize({
            "outer": {"inner": {"safe": "too-deep-secret"}},
        })

        self.assertEqual(CIRCULAR_REFERENCE, circular_result["self"])
        self.assertEqual(REDACTED, circular_result["token"])
        self.assertEqual(MAX_DEPTH_REACHED, depth_result["outer"]["inner"])
        self.assert_json_safe_and_no_leak(
            {"circular": circular_result, "depth": depth_result},
            "circular-token-secret",
            "too-deep-secret",
        )

    def test_public_helpers_and_validation_are_stable(self) -> None:
        sanitizer = Sanitizer()
        self.assertIs(NsSanitizer, Sanitizer)
        self.assertEqual(
            DEFAULT_SANITIZER_DIGEST_MAX_NODES,
            sanitizer.max_digest_nodes,
        )
        self.assertEqual(
            DEFAULT_SANITIZER_DIGEST_MAX_CONTAINER_ITEMS,
            sanitizer.max_digest_container_items,
        )
        self.assertEqual(
            DEFAULT_SANITIZER_DIGEST_MAX_STRING_LENGTH,
            sanitizer.max_digest_string_length,
        )
        self.assertEqual(
            DEFAULT_SANITIZER_DIGEST_MAX_BYTES_LENGTH,
            sanitizer.max_digest_bytes_length,
        )
        self.assertEqual(
            DEFAULT_SANITIZER_DIGEST_MAX_NORMALIZED_BYTES,
            sanitizer.max_digest_normalized_bytes,
        )
        sanitized_value = sanitize("helper-token-secret", field_name="token")
        sanitized_url = sanitize_url(
            "https://example.test/?token=helper-url-secret"
        )
        sanitized_text = sanitize_text("Bearer helper-bearer-secret")
        self.assertEqual(REDACTED, sanitized_value)

        invalid_calls = (
            lambda: Sanitizer(max_depth=0),
            lambda: Sanitizer(max_depth=True),
            lambda: Sanitizer(max_digest_nodes=0),
            lambda: Sanitizer(max_digest_container_items=True),
            lambda: Sanitizer(max_digest_string_length=0),
            lambda: Sanitizer(max_digest_bytes_length=0),
            lambda: Sanitizer(max_digest_normalized_bytes=0),
            lambda: Sanitizer().sanitize({}, field_name=""),
            lambda: Sanitizer().sanitize({}, path="not-a-path"),
            lambda: Sanitizer().sanitize_url(1),
            lambda: Sanitizer().sanitize_text(None),
        )
        for call in invalid_calls:
            with self.subTest(call=call):
                with self.assertRaises(NsValidationError):
                    call()
        self.assert_json_safe_and_no_leak(
            {
                "value": sanitized_value,
                "url": sanitized_url,
                "text": sanitized_text,
            },
            "helper-token-secret",
            "helper-url-secret",
            "helper-bearer-secret",
        )


if __name__ == "__main__":
    unittest.main()
