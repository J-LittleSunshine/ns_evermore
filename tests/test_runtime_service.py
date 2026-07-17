# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import unittest

from ns_common.exceptions import NsStateError
from ns_runtime.service import RuntimeService, RuntimeServiceState


class _RecordingRuntimeService(RuntimeService):
    def __init__(
        self,
        *,
        start_error: BaseException | None = None,
        stop_error: BaseException | None = None,
    ) -> None:
        super().__init__()
        self.events: list[tuple[str, RuntimeServiceState]] = []
        self.start_error = start_error
        self.stop_error = stop_error

    async def _on_start(self) -> None:
        self.events.append(("start", self.state))
        if self.start_error is not None:
            raise self.start_error

    async def _on_stop(self) -> None:
        self.events.append(("stop", self.state))
        if self.stop_error is not None:
            raise self.stop_error


class _BlockingRuntimeService(RuntimeService):
    def __init__(self) -> None:
        super().__init__()
        self.start_calls = 0
        self.stop_calls = 0
        self.start_entered = asyncio.Event()
        self.release_start = asyncio.Event()

    async def _on_start(self) -> None:
        self.start_calls += 1
        self.start_entered.set()
        await self.release_start.wait()

    async def _on_stop(self) -> None:
        self.stop_calls += 1


class RuntimeServiceTestCase(unittest.IsolatedAsyncioTestCase):

    async def test_normal_lifecycle_exposes_every_transitional_state(self) -> None:
        service = _RecordingRuntimeService()

        self.assertIs(RuntimeServiceState.CREATED, service.state)
        await service.start()
        self.assertIs(RuntimeServiceState.RUNNING, service.state)
        await service.stop()
        self.assertIs(RuntimeServiceState.STOPPED, service.state)
        self.assertEqual(
            [
                ("start", RuntimeServiceState.STARTING),
                ("stop", RuntimeServiceState.STOPPING),
            ],
            service.events,
        )

    async def test_state_values_are_stable_and_complete(self) -> None:
        self.assertEqual(
            (
                "created",
                "starting",
                "running",
                "stopping",
                "stopped",
                "failed",
            ),
            tuple(state.value for state in RuntimeServiceState),
        )

    async def test_invalid_transition_returns_stable_state_error(self) -> None:
        service = RuntimeService()

        with self.assertRaises(NsStateError) as context:
            await service.stop()

        self.assertEqual("NS_STATE_ERROR", context.exception.code)
        self.assertEqual(
            "RuntimeService lifecycle transition is invalid.",
            context.exception.message,
        )
        self.assertEqual(
            {
                "component": "runtime_service",
                "operation": "stop",
                "current_state": "created",
                "requested_state": "stopping",
                "allowed_target_states": ["starting"],
            },
            context.exception.details,
        )
        self.assertIs(RuntimeServiceState.CREATED, service.state)

    async def test_stopped_state_is_terminal(self) -> None:
        service = RuntimeService()
        await service.start()
        await service.stop()

        for operation in (service.start, service.stop):
            with self.subTest(operation=operation.__name__):
                with self.assertRaises(NsStateError) as context:
                    await operation()
                self.assertEqual("stopped", context.exception.details["current_state"])
                self.assertEqual([], context.exception.details["allowed_target_states"])

    async def test_start_failure_is_propagated_and_marks_service_failed(self) -> None:
        failure = RuntimeError("startup failure sentinel")
        service = _RecordingRuntimeService(start_error=failure)

        with self.assertRaises(RuntimeError) as context:
            await service.start()

        self.assertIs(failure, context.exception)
        self.assertIs(RuntimeServiceState.FAILED, service.state)
        for operation in (service.start, service.stop):
            with self.subTest(operation=operation.__name__):
                with self.assertRaises(NsStateError) as transition_context:
                    await operation()
                self.assertEqual(
                    "failed",
                    transition_context.exception.details["current_state"],
                )
                self.assertEqual(
                    [],
                    transition_context.exception.details["allowed_target_states"],
                )

    async def test_stop_failure_is_propagated_and_marks_service_failed(self) -> None:
        failure = RuntimeError("shutdown failure sentinel")
        service = _RecordingRuntimeService(stop_error=failure)
        await service.start()

        with self.assertRaises(RuntimeError) as context:
            await service.stop()

        self.assertIs(failure, context.exception)
        self.assertIs(RuntimeServiceState.FAILED, service.state)

    async def test_cancelled_start_marks_service_failed_and_releases_lock(self) -> None:
        service = _BlockingRuntimeService()
        start_task = asyncio.create_task(service.start())
        await asyncio.wait_for(service.start_entered.wait(), timeout=1.0)
        self.assertIs(RuntimeServiceState.STARTING, service.state)

        start_task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await start_task

        self.assertIs(RuntimeServiceState.FAILED, service.state)
        with self.assertRaises(NsStateError):
            await asyncio.wait_for(service.start(), timeout=1.0)

    async def test_concurrent_start_calls_are_serialized(self) -> None:
        service = _BlockingRuntimeService()
        first_start = asyncio.create_task(service.start())
        await asyncio.wait_for(service.start_entered.wait(), timeout=1.0)

        second_start = asyncio.create_task(service.start())
        await asyncio.sleep(0)
        self.assertFalse(second_start.done())

        service.release_start.set()
        await asyncio.wait_for(first_start, timeout=1.0)
        with self.assertRaises(NsStateError) as context:
            await asyncio.wait_for(second_start, timeout=1.0)

        self.assertEqual(1, service.start_calls)
        self.assertEqual("running", context.exception.details["current_state"])
        self.assertEqual("starting", context.exception.details["requested_state"])

    async def test_stop_waits_for_in_progress_start(self) -> None:
        service = _BlockingRuntimeService()
        start_task = asyncio.create_task(service.start())
        await asyncio.wait_for(service.start_entered.wait(), timeout=1.0)

        stop_task = asyncio.create_task(service.stop())
        await asyncio.sleep(0)
        self.assertFalse(stop_task.done())

        service.release_start.set()
        await asyncio.wait_for(start_task, timeout=1.0)
        await asyncio.wait_for(stop_task, timeout=1.0)

        self.assertIs(RuntimeServiceState.STOPPED, service.state)
        self.assertEqual(1, service.start_calls)
        self.assertEqual(1, service.stop_calls)


class RuntimeServiceLoopBindingTestCase(unittest.TestCase):

    def test_service_cannot_cross_event_loops(self) -> None:
        service = RuntimeService()
        asyncio.run(service.start())

        with self.assertRaises(NsStateError) as context:
            asyncio.run(service.stop())

        self.assertEqual(
            {
                "component": "runtime_service",
                "operation": "stop",
                "current_state": "running",
                "reason": "event_loop_mismatch",
            },
            context.exception.details,
        )
        self.assertIs(RuntimeServiceState.RUNNING, service.state)


if __name__ == "__main__":
    unittest.main()
