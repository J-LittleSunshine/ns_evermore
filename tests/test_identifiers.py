# -*- coding: utf-8 -*-
from __future__ import annotations

import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from uuid import (
    UUID,
    uuid1,
    uuid4,
)

from ns_common.exceptions import (
    NsStateError,
    NsValidationError,
)
from ns_common.identifiers import (
    IDENTIFIER_FORMAT,
    IDENTIFIER_KINDS,
    IDENTIFIER_PREFIXES,
    IdentifierFactory,
    NsIdentifier,
    NsIdentifierKind,
    generate_connection_id,
    generate_delivery_id,
    generate_identifier,
    generate_message_id,
    generate_operation_id,
    generate_plan_id,
    generate_runtime_id,
    generate_session_id,
    generate_stream_id,
    generate_summary_id,
    is_valid_identifier,
    parse_identifier,
    validate_identifier,
)


FIXED_UUID4 = UUID("12345678-1234-4abc-8def-1234567890ab")


class IdentifierTestCase(unittest.TestCase):

    def test_kind_registry_and_prefixes_are_stable_and_immutable(self) -> None:
        self.assertEqual(
            (
                "runtime_id",
                "connection_id",
                "session_id",
                "message_id",
                "summary_id",
                "delivery_id",
                "stream_id",
                "plan_id",
                "operation_id",
            ),
            IDENTIFIER_KINDS,
        )
        self.assertEqual("{prefix}_{uuid4_hex}", IDENTIFIER_FORMAT)
        self.assertEqual(len(IDENTIFIER_KINDS), len(set(IDENTIFIER_PREFIXES.values())))
        with self.assertRaises(TypeError):
            IDENTIFIER_PREFIXES[NsIdentifierKind.MESSAGE_ID] = "changed"  # type: ignore[index]

    def test_deterministic_factory_uses_exact_lowercase_uuid4_format(self) -> None:
        factory = IdentifierFactory(uuid_factory=lambda: FIXED_UUID4)
        value = factory.generate(NsIdentifierKind.MESSAGE_ID)

        self.assertEqual(
            "message_1234567812344abc8def1234567890ab",
            value,
        )
        parsed = factory.parse(value, expected_kind="message_id")
        self.assertIs(NsIdentifierKind.MESSAGE_ID, parsed.kind)
        self.assertEqual(FIXED_UUID4, parsed.uuid_value)
        self.assertEqual(FIXED_UUID4.hex, parsed.payload)
        self.assertEqual(value, str(parsed))
        self.assertEqual(value, factory.validate(value, expected_kind="message_id"))
        self.assertTrue(factory.is_valid(value, expected_kind="message_id"))

        with self.assertRaises(FrozenInstanceError):
            parsed.value = "changed"  # type: ignore[misc]

    def test_all_identifier_kinds_generate_and_validate(self) -> None:
        generators = {
            NsIdentifierKind.RUNTIME_ID: generate_runtime_id,
            NsIdentifierKind.CONNECTION_ID: generate_connection_id,
            NsIdentifierKind.SESSION_ID: generate_session_id,
            NsIdentifierKind.MESSAGE_ID: generate_message_id,
            NsIdentifierKind.SUMMARY_ID: generate_summary_id,
            NsIdentifierKind.DELIVERY_ID: generate_delivery_id,
            NsIdentifierKind.STREAM_ID: generate_stream_id,
            NsIdentifierKind.PLAN_ID: generate_plan_id,
            NsIdentifierKind.OPERATION_ID: generate_operation_id,
        }

        generated_values: set[str] = set()
        for kind, generator in generators.items():
            with self.subTest(kind=kind.value):
                value = generator()
                self.assertTrue(value)
                self.assertTrue(value.startswith(f"{IDENTIFIER_PREFIXES[kind]}_"))
                self.assertEqual(value, validate_identifier(value, expected_kind=kind))
                self.assertIs(kind, parse_identifier(value).kind)
                generated_values.add(value)

        self.assertEqual(len(generators), len(generated_values))

    def test_invalid_values_are_rejected_without_normalization(self) -> None:
        valid = f"message_{FIXED_UUID4.hex}"
        invalid_values: list[object] = [
            None,
            "",
            " ",
            1,
            True,
            f" {valid}",
            f"{valid} ",
            valid.upper(),
            f"message_{FIXED_UUID4}",
            f"message_{FIXED_UUID4.hex}0",
            f"unknown_{FIXED_UUID4.hex}",
            f"message_{'0' * 32}",
            f"message_{uuid1().hex}",
        ]

        for value in invalid_values:
            with self.subTest(value=value):
                with self.assertRaises(NsValidationError) as context:
                    validate_identifier(value, expected_kind="message_id")
                self.assertEqual("message_id", context.exception.details["field"])
                self.assertEqual(value, context.exception.details["value"])
                self.assertFalse(
                    is_valid_identifier(value, expected_kind="message_id")
                )

    def test_expected_kind_mismatch_is_explicit(self) -> None:
        connection_id = (
            f"connection_{FIXED_UUID4.hex}"
        )
        with self.assertRaises(NsValidationError) as context:
            parse_identifier(
                connection_id,
                expected_kind=NsIdentifierKind.MESSAGE_ID,
            )

        self.assertEqual("message_id", context.exception.details["field"])
        self.assertEqual("message_id", context.exception.details["expected_kind"])
        self.assertEqual("connection_id", context.exception.details["actual_kind"])

    def test_invalid_kind_and_uuid_factory_are_rejected(self) -> None:
        with self.assertRaises(NsValidationError) as kind_context:
            generate_identifier("unknown_id")
        self.assertEqual("identifier.kind", kind_context.exception.details["field"])
        self.assertEqual(list(IDENTIFIER_KINDS), kind_context.exception.details["allowed_values"])

        with self.assertRaises(NsValidationError):
            IdentifierFactory(uuid_factory=None)  # type: ignore[arg-type]

        for invalid_uuid in ("not-a-uuid", uuid1()):
            with self.subTest(invalid_uuid=invalid_uuid):
                factory = IdentifierFactory(
                    uuid_factory=lambda value=invalid_uuid: value,  # type: ignore[return-value]
                )
                with self.assertRaises(NsStateError):
                    factory.generate(NsIdentifierKind.RUNTIME_ID)

    def test_identifier_value_object_enforces_its_invariants(self) -> None:
        with self.assertRaises(NsValidationError):
            NsIdentifier(
                kind=NsIdentifierKind.MESSAGE_ID,
                value=f"connection_{FIXED_UUID4.hex}",
                uuid_value=FIXED_UUID4,
            )
        with self.assertRaises(NsValidationError):
            NsIdentifier(
                kind=NsIdentifierKind.MESSAGE_ID,
                value=f"message_{uuid1().hex}",
                uuid_value=uuid1(),
            )

    def test_concurrent_generation_has_no_conflicts(self) -> None:
        factory = IdentifierFactory()
        kinds = tuple(NsIdentifierKind)
        total = 9000

        def generate_one(index: int) -> str:
            return factory.generate(kinds[index % len(kinds)])

        with ThreadPoolExecutor(max_workers=16) as executor:
            values = list(executor.map(generate_one, range(total)))

        self.assertEqual(total, len(values))
        self.assertEqual(total, len(set(values)))
        for value in values:
            self.assertTrue(is_valid_identifier(value))


if __name__ == "__main__":
    unittest.main()
