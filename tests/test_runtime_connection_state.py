# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import dataclasses
import unittest

from ns_common.exceptions import NsStateError, NsValidationError
from ns_runtime.connection import (
    LogicalConnectionCloseReason,
    LogicalConnectionState,
    LogicalConnectionStateMachine,
    LogicalConnectionStateSnapshot,
)


class LogicalConnectionStateMachineTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_complete_active_drain_and_close_path(self) -> None:
        machine = LogicalConnectionStateMachine()
        expected = (
            LogicalConnectionState.HANDSHAKING,
            LogicalConnectionState.AUTHENTICATED,
            LogicalConnectionState.ACTIVE,
            LogicalConnectionState.DRAINING,
        )
        for sequence, state in enumerate(expected, start=1):
            snapshot = await machine.transition(state)
            self.assertIs(state, snapshot.state)
            self.assertEqual(sequence, snapshot.transition_sequence)
            self.assertIsNone(snapshot.close_reason)

        closing = await machine.transition(
            LogicalConnectionState.CLOSING,
            close_reason=LogicalConnectionCloseReason.NORMAL,
        )
        closed = await machine.transition(LogicalConnectionState.CLOSED)
        self.assertIs(LogicalConnectionState.CLOSING, closing.state)
        self.assertIs(LogicalConnectionState.CLOSED, closed.state)
        self.assertIs(LogicalConnectionCloseReason.NORMAL, closed.close_reason)
        self.assertTrue(machine.terminal)

    async def test_every_declared_close_reason_is_low_cardinality_and_stable(self) -> None:
        expected = {
            "normal", "rejected", "auth_failed", "protocol_failed",
            "timeout_closed", "transport_disconnected", "drain_timeout",
            "kicked", "isolated_closed", "security_closed", "send_failed",
            "shutdown", "internal_error",
        }
        self.assertEqual(expected, {item.value for item in LogicalConnectionCloseReason})
        self.assertTrue(all(" " not in item.value for item in LogicalConnectionCloseReason))

    async def test_illegal_transitions_are_rejected_without_partial_mutation(self) -> None:
        machine = LogicalConnectionStateMachine()
        initial = await machine.snapshot()
        for state in (
            LogicalConnectionState.AUTHENTICATED,
            LogicalConnectionState.ACTIVE,
            LogicalConnectionState.DRAINING,
            LogicalConnectionState.CLOSED,
        ):
            with self.subTest(state=state.value), self.assertRaises(NsStateError):
                await machine.transition(state)
            self.assertEqual(initial, await machine.snapshot())

        with self.assertRaises(NsValidationError):
            await machine.transition(LogicalConnectionState.CLOSING)
        self.assertEqual(initial, await machine.snapshot())

    async def test_draining_is_one_way_and_closed_is_terminal(self) -> None:
        machine = await _active_machine()
        await machine.transition(LogicalConnectionState.DRAINING)
        with self.assertRaises(NsStateError):
            await machine.transition(LogicalConnectionState.ACTIVE)
        await machine.transition(
            LogicalConnectionState.CLOSING,
            close_reason=LogicalConnectionCloseReason.DRAIN_TIMEOUT,
        )
        await machine.transition(LogicalConnectionState.CLOSED)
        for state in LogicalConnectionState:
            with self.subTest(state=state.value), self.assertRaises(NsStateError):
                await machine.transition(state)

    async def test_concurrent_duplicate_hello_cannot_authenticate_twice(self) -> None:
        machine = LogicalConnectionStateMachine()
        await machine.transition(LogicalConnectionState.HANDSHAKING)
        results = await asyncio.gather(
            machine.transition(LogicalConnectionState.AUTHENTICATED),
            machine.transition(LogicalConnectionState.AUTHENTICATED),
            return_exceptions=True,
        )
        self.assertEqual(1, sum(isinstance(item, LogicalConnectionStateSnapshot) for item in results))
        self.assertEqual(1, sum(isinstance(item, NsStateError) for item in results))
        self.assertIs(LogicalConnectionState.AUTHENTICATED, machine.state)
        self.assertEqual(2, machine.transition_sequence)

    async def test_concurrent_active_drain_and_close_has_one_linearized_state(self) -> None:
        machine = await _active_machine()
        results = await asyncio.gather(
            machine.transition(LogicalConnectionState.DRAINING),
            machine.transition(
                LogicalConnectionState.CLOSING,
                close_reason=LogicalConnectionCloseReason.SHUTDOWN,
            ),
            return_exceptions=True,
        )
        self.assertTrue(all(
            isinstance(item, (LogicalConnectionStateSnapshot, NsStateError))
            for item in results
        ))
        self.assertGreaterEqual(
            sum(isinstance(item, LogicalConnectionStateSnapshot) for item in results),
            1,
        )
        self.assertIs(LogicalConnectionState.CLOSING, machine.state)
        self.assertIs(LogicalConnectionCloseReason.SHUTDOWN, machine.close_reason)
        await machine.transition(LogicalConnectionState.CLOSED)

    async def test_concurrent_close_can_fence_handshake_completion(self) -> None:
        machine = LogicalConnectionStateMachine()
        await machine.transition(LogicalConnectionState.HANDSHAKING)
        results = await asyncio.gather(
            machine.transition(LogicalConnectionState.AUTHENTICATED),
            machine.transition(
                LogicalConnectionState.CLOSING,
                close_reason=LogicalConnectionCloseReason.SHUTDOWN,
            ),
            return_exceptions=True,
        )
        self.assertIn(machine.state, {
            LogicalConnectionState.AUTHENTICATED,
            LogicalConnectionState.CLOSING,
        })
        if machine.state is LogicalConnectionState.AUTHENTICATED:
            await machine.transition(
                LogicalConnectionState.CLOSING,
                close_reason=LogicalConnectionCloseReason.SHUTDOWN,
            )
        self.assertIs(LogicalConnectionState.CLOSING, machine.state)
        self.assertLessEqual(
            sum(
                isinstance(item, LogicalConnectionStateSnapshot)
                and item.state is LogicalConnectionState.AUTHENTICATED
                for item in results
            ),
            1,
        )

    async def test_snapshot_is_frozen_and_inputs_are_typed(self) -> None:
        machine = LogicalConnectionStateMachine()
        snapshot = await machine.snapshot()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            snapshot.state = LogicalConnectionState.CLOSED  # type: ignore[misc]
        with self.assertRaises(NsValidationError):
            await machine.transition("active")  # type: ignore[arg-type]
        with self.assertRaises(NsValidationError):
            await machine.transition(
                LogicalConnectionState.CLOSING,
                close_reason="token=secret",  # type: ignore[arg-type]
            )
        self.assertNotIn("secret", repr(await machine.snapshot()))

    async def test_transport_handshaking_state_is_a_separate_enum(self) -> None:
        from ns_runtime.transport import TransportSessionState

        self.assertIsNot(TransportSessionState.HANDSHAKING, LogicalConnectionState.HANDSHAKING)
        self.assertNotEqual(
            type(TransportSessionState.HANDSHAKING),
            type(LogicalConnectionState.HANDSHAKING),
        )


async def _active_machine() -> LogicalConnectionStateMachine:
    machine = LogicalConnectionStateMachine()
    await machine.transition(LogicalConnectionState.HANDSHAKING)
    await machine.transition(LogicalConnectionState.AUTHENTICATED)
    await machine.transition(LogicalConnectionState.ACTIVE)
    return machine


if __name__ == "__main__":
    unittest.main()
