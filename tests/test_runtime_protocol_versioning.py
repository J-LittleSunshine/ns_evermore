# -*- coding: utf-8 -*-
from __future__ import annotations

import unittest

from ns_common.exceptions import NsRuntimeProtocolVersionError
from ns_runtime.protocol import (
    JSON_V1_PROTOCOL_MATRIX,
    ProtocolCompatibilityMatrix,
    ProtocolGroup,
    ProtocolVersion,
    ProtocolVersionSupport,
)


class RuntimeProtocolVersioningTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.matrix = ProtocolCompatibilityMatrix((
            ProtocolVersionSupport(ProtocolVersion(1, 0, 0), "schema/1.0"),
            ProtocolVersionSupport(ProtocolVersion(1, 1, 5), "schema/1.1"),
            ProtocolVersionSupport(ProtocolVersion(1, 2, 3), "schema/1.2"),
        ))

    def test_major_is_strict(self) -> None:
        with self.assertRaises(NsRuntimeProtocolVersionError) as context:
            self.matrix.negotiate(ProtocolVersion(2, 0, 0))
        self.assertEqual("major_not_supported", context.exception.details["reason"])

    def test_minor_and_patch_select_highest_compatible_schema(self) -> None:
        minor = self.matrix.negotiate(
            ProtocolVersion(1, 3, 0),
            minimum=ProtocolVersion(1, 1, 0),
        )
        self.assertEqual(ProtocolVersion(1, 2, 3), minor.selected)
        self.assertEqual("schema/1.2", minor.schema_key)
        self.assertTrue(minor.downgraded)

        patch = self.matrix.negotiate(
            ProtocolVersion(1, 2, 9),
            minimum=ProtocolVersion(1, 2, 0),
        )
        self.assertEqual(ProtocolVersion(1, 2, 3), patch.selected)
        self.assertEqual("schema/1.2", patch.schema_key)

    def test_minimum_range_is_enforced(self) -> None:
        with self.assertRaises(NsRuntimeProtocolVersionError) as context:
            self.matrix.negotiate(
                ProtocolVersion(1, 3, 0),
                minimum=ProtocolVersion(1, 2, 4),
            )
        self.assertEqual("compatible_version_not_found", context.exception.details["reason"])

    def test_group_selection_centralizes_version_and_schema(self) -> None:
        negotiated = self.matrix.negotiate_group(
            ProtocolGroup(major=1, minor=2, patch=9, min_version="1.1"),
        )
        self.assertEqual(ProtocolVersion(1, 2, 3), negotiated.selected)
        self.assertEqual("schema/1.2", negotiated.schema_key)

    def test_invalid_or_attacker_controlled_version_is_not_echoed(self) -> None:
        secret = "1.secret-token"
        with self.assertRaises(NsRuntimeProtocolVersionError) as context:
            ProtocolVersion.parse(secret)
        self.assertEqual("invalid_version_format", context.exception.details["reason"])
        self.assertNotIn(secret, str(context.exception))

    def test_current_frozen_matrix_is_json_v1_protocol_1_0(self) -> None:
        selected = JSON_V1_PROTOCOL_MATRIX.negotiate_group(
            ProtocolGroup(major=1, minor=0, patch=7),
        )
        self.assertEqual(ProtocolVersion(1, 0, 0), selected.selected)
        self.assertEqual("json.v1/protocol-1.0", selected.schema_key)
        self.assertTrue(selected.downgraded)


if __name__ == "__main__":
    unittest.main()
