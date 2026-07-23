# -*- coding: utf-8 -*-
from __future__ import annotations

import math
import unittest

from ns_common.exceptions import NsRuntimeEnvelopeSchemaError
from ns_runtime.protocol import (
    JsonResourceLimits,
    JsonV1Codec,
    canonical_checksum,
    canonical_serialize,
    envelope_from_mapping,
)


def _envelope(payload: dict[str, object], extensions: dict[str, object]):
    return envelope_from_mapping({
        "message": {
            "type": "task.dispatch",
            "created_at": "2026-07-20T12:00:00Z",
            "priority": 1,
            "category": "task",
            "message_id": "message_1",
            "reliability": "reliable",
        },
        "protocol": {"patch": 0, "minor": 0, "major": 1},
        "target": {"runtime_id": "runtime_2", "kind": "runtime"},
        "payload": {"inline": payload, "mode": "inline"},
        "extensions": extensions,
    })


class RuntimeProtocolCanonicalTestCase(unittest.TestCase):
    def test_mapping_insertion_order_does_not_change_bytes_or_checksum(self) -> None:
        first = _envelope(
            {"z": [3, 2, 1], "a": {"y": 2, "x": "你好"}},
            {"com.example.two": {"b": 2}, "com.example.one": {"a": 1}},
        )
        second = _envelope(
            {"a": {"x": "你好", "y": 2}, "z": [3, 2, 1]},
            {"com.example.one": {"a": 1}, "com.example.two": {"b": 2}},
        )
        self.assertEqual(canonical_serialize(first), canonical_serialize(second))
        self.assertEqual(canonical_checksum(first), canonical_checksum(second))
        self.assertTrue(canonical_checksum(first).startswith("sha256:"))

    def test_canonical_form_is_compact_utf8_with_sorted_keys(self) -> None:
        encoded = canonical_serialize(_envelope({"b": 2, "a": "你好"}, {"com.example.safe": {"x": 1}}))
        self.assertIn("你好".encode("utf-8"), encoded)
        self.assertNotIn(b" ", encoded)
        self.assertLess(encoded.index(b'"a"'), encoded.index(b'"b"'))

    def test_outbound_non_finite_numbers_and_size_are_rejected(self) -> None:
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                with self.assertRaises(NsRuntimeEnvelopeSchemaError):
                    canonical_serialize(_envelope({"number": value}, {"com.example.safe": {"x": 1}}))
        with self.assertRaises(NsRuntimeEnvelopeSchemaError) as size:
            canonical_serialize(
                _envelope({"text": "bounded"}, {"com.example.safe": {"x": 1}}),
                limits=JsonResourceLimits(max_document_bytes=32),
            )
        self.assertEqual("max_document_bytes_exceeded", size.exception.details["reason"])

    def test_same_frozen_envelope_remains_stable_after_input_mutation(self) -> None:
        payload: dict[str, object] = {"items": [1, 2]}
        envelope = _envelope(payload, {"com.example.safe": {"x": 1}})
        before = canonical_serialize(envelope)
        payload["items"] = [999]
        self.assertEqual(before, canonical_serialize(envelope))

    def test_canonical_bytes_round_trip_to_the_same_canonical_form(self) -> None:
        envelope = _envelope(
            {"nested": {"b": 2, "a": 1}},
            {"com.example.safe": {"enabled": True}},
        )
        encoded = canonical_serialize(envelope)
        decoded = envelope_from_mapping(JsonV1Codec().decode_document(encoded))
        self.assertEqual(encoded, canonical_serialize(decoded))


if __name__ == "__main__":
    unittest.main()
