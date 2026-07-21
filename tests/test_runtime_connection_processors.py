# -*- coding: utf-8 -*-
from __future__ import annotations

import unittest

from ns_common.exceptions import NsValidationError
from ns_runtime.connection import (
    ConnectionLifecycleProcessor,
    ConnectionLifecycleProcessorRegistry,
    P05_EXECUTABLE_PROCESSOR_KEYS,
)
from ns_runtime.protocol import (
    BUILTIN_MESSAGE_REGISTRY,
    Envelope,
    MessageDirection,
    MessageGroup,
    ProtocolGroup,
)


class _RecordingProcessor(ConnectionLifecycleProcessor):
    def __init__(self, message_type: str) -> None:
        super().__init__(
            contract=BUILTIN_MESSAGE_REGISTRY.require(message_type),
        )
        self.calls: list[Envelope] = []

    async def process(self, envelope: Envelope) -> object:
        self._validate_contract(envelope)
        self.calls.append(envelope)
        return envelope.message.type


class ConnectionLifecycleProcessorRegistryTestCase(unittest.IsolatedAsyncioTestCase):
    def _processors(self) -> tuple[_RecordingProcessor, ...]:
        return tuple(
            _RecordingProcessor(message_type)
            for message_type in sorted(P05_EXECUTABLE_PROCESSOR_KEYS)
        )

    async def test_canonical_processor_keys_are_exact_and_dispatch_once(self) -> None:
        processors = self._processors()
        registry = ConnectionLifecycleProcessorRegistry(processors)
        enabled_executable = {
            contract.processor_key
            for contract in BUILTIN_MESSAGE_REGISTRY.contracts
            if contract.feature_enabled
            and contract.direction is MessageDirection.INBOUND
            and contract.message_type != "connection.hello"
        }
        self.assertEqual(P05_EXECUTABLE_PROCESSOR_KEYS, enabled_executable)
        self.assertEqual(P05_EXECUTABLE_PROCESSOR_KEYS, registry.processor_keys)
        envelope = Envelope(
            protocol=ProtocolGroup(major=1, minor=0, patch=0),
            message=MessageGroup(
                message_id="message_1",
                type="connection.drain",
                category="connection",
                priority=0,
                created_at="2026-07-21T00:00:00Z",
                reliability="best_effort",
            ),
        )
        self.assertEqual("connection.drain", await registry.dispatch(envelope))
        by_type = {processor.contract.message_type: processor for processor in processors}
        self.assertEqual([envelope], by_type["connection.drain"].calls)
        self.assertEqual([], by_type["connection.heartbeat"].calls)
        self.assertEqual([], by_type["connection.reauth"].calls)

    def test_missing_duplicate_outbound_and_disabled_contracts_fail_closed(self) -> None:
        processors = self._processors()
        with self.assertRaises(NsValidationError):
            ConnectionLifecycleProcessorRegistry(processors[:-1])
        with self.assertRaises(NsValidationError):
            ConnectionLifecycleProcessorRegistry((*processors, processors[0]))
        for message_type in ("connection.heartbeat_ack", "task.dispatch"):
            with self.subTest(message_type=message_type):
                with self.assertRaises(NsValidationError):
                    _RecordingProcessor(message_type)


if __name__ == "__main__":
    unittest.main()
