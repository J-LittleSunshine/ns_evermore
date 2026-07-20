# -*- coding: utf-8 -*-
from __future__ import annotations

import unittest

from ns_common.exceptions import NsRuntimeUnsupportedMessageTypeError
from ns_runtime.protocol import (
    BUILTIN_MESSAGE_CONTRACTS,
    BUILTIN_MESSAGE_FAMILIES,
    BUILTIN_MESSAGE_REGISTRY,
    CURRENT_PROTOCOL_SCHEMA_KEY,
)


EXPECTED_BUILTIN_TYPES = (
    "connection.hello", "connection.accepted", "connection.rejected",
    "connection.reauth", "connection.reauth_accepted", "connection.reauth_rejected",
    "connection.heartbeat", "connection.heartbeat_ack", "connection.drain",
    "task.dispatch", "task.result", "task.callback",
    "delivery.accepted", "delivery.rejected", "delivery.duplicate",
    "delivery.ack", "delivery.nack", "delivery.defer",
    "stream.start", "stream.chunk", "stream.end",
    "runtime.control.health", "runtime.control.kick_connection",
    "runtime.control.drain_node", "runtime.control.switch_master",
    "runtime.control.isolate_node", "runtime.control.recover_node",
    "cluster.event.node_joined", "cluster.event.node_left",
    "cluster.event.role_changed", "cluster.event.health_changed",
    "cluster.event.config_drift", "cluster.event.leader_changed",
    "config.update", "config.updated", "config.rejected",
    "dead_letter.query", "dead_letter.result", "dead_letter.cleanup",
    "dead_letter.cleanup_result", "replay.request", "replay.result",
    "cancel.request", "cancel.result", "hold.request", "hold.release", "hold.result",
    "status.query", "status.result", "runtime.error",
)


class RuntimeProtocolRegistryTestCase(unittest.TestCase):
    def test_builtin_registry_has_the_independently_frozen_full_type_list(self) -> None:
        self.assertEqual(
            EXPECTED_BUILTIN_TYPES,
            tuple(contract.message_type for contract in BUILTIN_MESSAGE_CONTRACTS),
        )
        self.assertEqual(len(EXPECTED_BUILTIN_TYPES), len(set(EXPECTED_BUILTIN_TYPES)))

    def test_every_required_family_and_current_schema_is_covered(self) -> None:
        self.assertEqual(
            set(BUILTIN_MESSAGE_FAMILIES),
            {contract.family for contract in BUILTIN_MESSAGE_CONTRACTS},
        )
        for contract in BUILTIN_MESSAGE_CONTRACTS:
            with self.subTest(message_type=contract.message_type):
                schema = BUILTIN_MESSAGE_REGISTRY.schema_for(
                    contract.message_type,
                    CURRENT_PROTOCOL_SCHEMA_KEY,
                )
                self.assertEqual(contract.message_type, schema.message_type)

    def test_registry_and_schema_maps_are_immutable(self) -> None:
        contract = BUILTIN_MESSAGE_REGISTRY.require("task.dispatch")
        with self.assertRaises(TypeError):
            contract.schemas["other"] = contract.schema_for(CURRENT_PROTOCOL_SCHEMA_KEY)  # type: ignore[index]
        self.assertIs(contract, BUILTIN_MESSAGE_REGISTRY.require("task.dispatch"))

    def test_unregistered_type_and_schema_fail_without_input_echo(self) -> None:
        secret_type = "private.secret_command"
        with self.assertRaises(NsRuntimeUnsupportedMessageTypeError) as unknown:
            BUILTIN_MESSAGE_REGISTRY.require(secret_type)
        self.assertEqual("message_type_not_registered", unknown.exception.details["reason"])
        self.assertNotIn(secret_type, str(unknown.exception))

        with self.assertRaises(NsRuntimeUnsupportedMessageTypeError) as schema:
            BUILTIN_MESSAGE_REGISTRY.schema_for("task.dispatch", "secret-schema")
        self.assertEqual("schema_not_registered", schema.exception.details["reason"])
        self.assertNotIn("secret-schema", str(schema.exception))


if __name__ == "__main__":
    unittest.main()
