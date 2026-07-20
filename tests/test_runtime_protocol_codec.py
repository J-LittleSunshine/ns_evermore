# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import unittest

from ns_common.exceptions import (
    NsRuntimeEnvelopeSchemaError,
    NsRuntimeProtocolParseError,
)
from ns_runtime.protocol import JsonResourceLimits, JsonV1Codec


def _document(**message_overrides: object) -> dict[str, object]:
    message = {
        "message_id": "message_123",
        "type": "task.dispatch",
        "category": "task",
        "priority": 0,
        "created_at": "2026-07-20T12:00:00Z",
        **message_overrides,
    }
    return {
        "protocol": {"major": 1, "minor": 0, "patch": 0},
        "message": message,
    }


class RuntimeProtocolCodecTestCase(unittest.TestCase):
    def test_json_v1_accepts_utf8_text_or_bytes_only(self) -> None:
        codec = JsonV1Codec()
        encoded = json.dumps(_document(), ensure_ascii=False)
        self.assertEqual("task.dispatch", codec.decode_inbound(encoded).message.type)
        self.assertEqual("task.dispatch", codec.decode_inbound(encoded.encode()).message.type)
        with self.assertRaises(NsRuntimeProtocolParseError):
            codec.decode_document(bytearray(encoded.encode()))  # type: ignore[arg-type]
        with self.assertRaises(NsRuntimeProtocolParseError):
            codec.decode_document(b"\xff")

    def test_document_byte_limit_is_utf8_accurate(self) -> None:
        codec = JsonV1Codec(limits=JsonResourceLimits(max_document_bytes=5))
        self.assertEqual("abc", codec.decode_document('"abc"'))
        with self.assertRaises(NsRuntimeEnvelopeSchemaError) as context:
            codec.decode_document('"你好"')
        self.assertEqual("max_document_bytes_exceeded", context.exception.details["reason"])

    def test_depth_is_rejected_before_recursive_json_decode(self) -> None:
        codec = JsonV1Codec(limits=JsonResourceLimits(max_depth=4))
        with self.assertRaises(NsRuntimeEnvelopeSchemaError) as context:
            codec.decode_document("[[[[[]]]]]")
        self.assertEqual("max_depth_exceeded", context.exception.details["reason"])
        self.assertEqual("[[]]", codec.decode_document("[[]]").__repr__())

    def test_string_array_object_node_and_number_limits(self) -> None:
        cases = (
            (JsonResourceLimits(max_string_chars=3), '"four"', "max_string_chars_exceeded"),
            (JsonResourceLimits(max_array_items=2), "[1,2,3]", "max_array_items_exceeded"),
            (JsonResourceLimits(max_object_items=1), '{"a":1,"b":2}', "max_object_items_exceeded"),
            (JsonResourceLimits(max_nodes=2), "[1,2]", "max_nodes_exceeded"),
            (JsonResourceLimits(max_integer_abs=10), "11", "integer_range_exceeded"),
            (JsonResourceLimits(max_float_abs=10.0), "10.1", "float_range_exceeded"),
        )
        for limits, document, reason in cases:
            with self.subTest(reason=reason):
                with self.assertRaises(NsRuntimeEnvelopeSchemaError) as context:
                    JsonV1Codec(limits=limits).decode_document(document)
                self.assertEqual(reason, context.exception.details["reason"])

    def test_non_finite_and_duplicate_keys_are_stable_parse_errors(self) -> None:
        codec = JsonV1Codec()
        for document, reason in (
            ('{"x":NaN}', "non_finite_number"),
            ('{"x":Infinity}', "non_finite_number"),
            ('{"x":1,"x":2}', "duplicate_object_key"),
        ):
            with self.subTest(reason=reason):
                with self.assertRaises(NsRuntimeProtocolParseError) as context:
                    codec.decode_document(document)
                self.assertEqual(reason, context.exception.details["reason"])
                self.assertNotIn(document, str(context.exception))

    def test_invalid_json_never_copies_parser_exception_or_payload(self) -> None:
        secret_document = '{"token":"secret",'
        with self.assertRaises(NsRuntimeProtocolParseError) as context:
            JsonV1Codec().decode_document(secret_document)
        self.assertEqual("invalid_json_document", context.exception.details["reason"])
        self.assertNotIn("secret", str(context.exception))


if __name__ == "__main__":
    unittest.main()
