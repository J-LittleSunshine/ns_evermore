# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import logging
import queue
import threading
import unittest

from ns_common.async_runtime import TaskSupervisor
from ns_common.config import NsConfig
from ns_common.exceptions import NsStateError
from ns_common.observability import InMemoryMetricsSink, InMemoryTraceSink
from ns_common.time import SystemClock
from ns_runtime.context import RuntimeContext
from ns_runtime.service import RuntimeService, RuntimeServiceState


def _create_runtime_context() -> RuntimeContext:
    return RuntimeContext(
        config=NsConfig(),
        clock=SystemClock(),
        logger=logging.Logger("runtime-service-test"),
        metrics=InMemoryMetricsSink(),
        traces=InMemoryTraceSink(),
        task_supervisor=TaskSupervisor(),
    )


class _RecordingRuntimeService(RuntimeService):
    def __init__(
        self,
        *,
        start_error: BaseException | None = None,
        stop_error: BaseException | None = None,
    ) -> None:
        super().__init__(context=_create_runtime_context())
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
    def __init__(self, *, start_error: BaseException | None = None) -> None:
        super().__init__(context=_create_runtime_context())
        self.start_calls = 0
        self.stop_calls = 0
        self.start_error = start_error
        self.start_entered = asyncio.Event()
        self.release_start = asyncio.Event()

    async def _on_start(self) -> None:
        self.start_calls += 1
        self.start_entered.set()
        await self.release_start.wait()
        if self.start_error is not None:
            raise self.start_error

    async def _on_stop(self) -> None:
        self.stop_calls += 1


class _BlockingStopRuntimeService(RuntimeService):
    def __init__(
        self,
        *,
        first_stop_error: BaseException | None = None,
    ) -> None:
        super().__init__(context=_create_runtime_context())
        self.first_stop_error = first_stop_error
        self.stop_calls = 0
        self.active_stop_calls = 0
        self.maximum_active_stop_calls = 0
        self.first_stop_entered = asyncio.Event()
        self.second_stop_entered = asyncio.Event()
        self.release_first_stop = asyncio.Event()

    async def _on_stop(self) -> None:
        self.stop_calls += 1
        attempt = self.stop_calls
        self.active_stop_calls += 1
        self.maximum_active_stop_calls = max(
            self.maximum_active_stop_calls,
            self.active_stop_calls,
        )
        try:
            if attempt == 1:
                self.first_stop_entered.set()
                await self.release_first_stop.wait()
                if self.first_stop_error is not None:
                    raise self.first_stop_error
            elif attempt == 2:
                self.second_stop_entered.set()
        finally:
            self.active_stop_calls -= 1


class _ThreadRaceRuntimeService(RuntimeService):
    def __init__(self) -> None:
        super().__init__(context=_create_runtime_context())
        self.start_calls = 0
        self.start_calls_lock = threading.Lock()
        self.start_entered = threading.Event()
        self.release_start = threading.Event()

    async def _on_start(self) -> None:
        with self.start_calls_lock:
            self.start_calls += 1
        self.start_entered.set()
        while not self.release_start.is_set():
            await asyncio.sleep(0.001)


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
        service = RuntimeService(context=_create_runtime_context())

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

    async def test_stopped_rejects_restart_and_stop_is_idempotent(self) -> None:
        service = _RecordingRuntimeService()
        await service.start()
        await service.stop()

        with self.assertRaises(NsStateError) as context:
            await service.start()
        self.assertEqual("stopped", context.exception.details["current_state"])
        self.assertEqual([], context.exception.details["allowed_target_states"])

        for _ in range(3):
            await service.stop()

        self.assertIs(RuntimeServiceState.STOPPED, service.state)
        self.assertEqual(1, sum(event[0] == "stop" for event in service.events))

    async def test_start_failure_is_propagated_and_marks_service_failed(self) -> None:
        failure = RuntimeError("startup failure sentinel")
        service = _RecordingRuntimeService(start_error=failure)

        with self.assertRaises(RuntimeError) as context:
            await service.start()

        self.assertIs(failure, context.exception)
        self.assertIs(RuntimeServiceState.FAILED, service.state)

        with self.assertRaises(NsStateError) as transition_context:
            await service.start()
        self.assertEqual(
            "failed",
            transition_context.exception.details["current_state"],
        )
        self.assertEqual(
            ["stopping"],
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
        service.stop_error = None

        await service.stop()
        await service.stop()

        self.assertIs(RuntimeServiceState.STOPPED, service.state)
        self.assertEqual(2, sum(event[0] == "stop" for event in service.events))

    async def test_start_failure_can_be_cleaned_up_without_storing_error(self) -> None:
        failure = RuntimeError("partial startup failure sentinel")

        class _PartiallyStartedRuntimeService(RuntimeService):
            def __init__(self) -> None:
                super().__init__(context=_create_runtime_context())
                self.resource_acquired = False
                self.stop_calls = 0

            async def _on_start(self) -> None:
                self.resource_acquired = True
                raise failure

            async def _on_stop(self) -> None:
                self.stop_calls += 1
                self.resource_acquired = False

        service = _PartiallyStartedRuntimeService()
        with self.assertRaises(RuntimeError) as context:
            await service.start()

        self.assertIs(failure, context.exception)
        self.assertIs(RuntimeServiceState.FAILED, service.state)
        self.assertTrue(service.resource_acquired)
        self.assertNotIn(failure, vars(service).values())

        await service.stop()
        await service.stop()

        self.assertIs(RuntimeServiceState.STOPPED, service.state)
        self.assertFalse(service.resource_acquired)
        self.assertEqual(1, service.stop_calls)

    async def test_failed_start_cleanup_failure_can_be_retried(self) -> None:
        start_failure = RuntimeError("startup failure before cleanup sentinel")
        stop_failure = RuntimeError("cleanup failure sentinel")
        service = _RecordingRuntimeService(
            start_error=start_failure,
            stop_error=stop_failure,
        )

        with self.assertRaises(RuntimeError) as start_context:
            await service.start()
        with self.assertRaises(RuntimeError) as stop_context:
            await service.stop()

        self.assertIs(start_failure, start_context.exception)
        self.assertIs(stop_failure, stop_context.exception)
        self.assertIs(RuntimeServiceState.FAILED, service.state)
        service.stop_error = None

        await service.stop()
        self.assertIs(RuntimeServiceState.STOPPED, service.state)
        self.assertEqual(2, sum(event[0] == "stop" for event in service.events))

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

        await asyncio.wait_for(service.stop(), timeout=1.0)
        await asyncio.wait_for(service.stop(), timeout=1.0)
        self.assertIs(RuntimeServiceState.STOPPED, service.state)
        self.assertEqual(1, service.stop_calls)

    async def test_cancelled_stop_can_be_retried(self) -> None:
        service = _BlockingStopRuntimeService()
        await service.start()
        stop_task = asyncio.create_task(service.stop())
        await asyncio.wait_for(service.first_stop_entered.wait(), timeout=1.0)
        self.assertIs(RuntimeServiceState.STOPPING, service.state)

        stop_task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await stop_task

        self.assertIs(RuntimeServiceState.FAILED, service.state)
        await asyncio.wait_for(service.stop(), timeout=1.0)
        self.assertIs(RuntimeServiceState.STOPPED, service.state)
        self.assertEqual(2, service.stop_calls)
        self.assertEqual(1, service.maximum_active_stop_calls)

    async def test_process_level_stop_errors_preserve_identity_and_allow_retry(
        self,
    ) -> None:
        for failure in (
            KeyboardInterrupt("keyboard interrupt sentinel"),
            SystemExit("system exit sentinel"),
        ):
            with self.subTest(error_type=type(failure).__name__):
                service = _RecordingRuntimeService(stop_error=failure)
                await service.start()

                with self.assertRaises(type(failure)) as context:
                    await service.stop()

                self.assertIs(failure, context.exception)
                self.assertIs(RuntimeServiceState.FAILED, service.state)
                service.stop_error = None
                await service.stop()
                self.assertIs(RuntimeServiceState.STOPPED, service.state)

    async def test_process_level_start_errors_preserve_identity_and_allow_cleanup(
        self,
    ) -> None:
        for failure in (
            KeyboardInterrupt("startup keyboard interrupt sentinel"),
            SystemExit("startup system exit sentinel"),
        ):
            with self.subTest(error_type=type(failure).__name__):
                service = _RecordingRuntimeService(start_error=failure)

                with self.assertRaises(type(failure)) as context:
                    await service.start()

                self.assertIs(failure, context.exception)
                self.assertIs(RuntimeServiceState.FAILED, service.state)
                await service.stop()
                self.assertIs(RuntimeServiceState.STOPPED, service.state)

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

    async def test_concurrent_start_failure_does_not_retry_start_hook(self) -> None:
        failure = RuntimeError("concurrent startup failure sentinel")
        service = _BlockingRuntimeService(start_error=failure)
        first_start = asyncio.create_task(service.start())
        await asyncio.wait_for(service.start_entered.wait(), timeout=1.0)

        second_start = asyncio.create_task(service.start())
        await asyncio.sleep(0)
        self.assertFalse(second_start.done())
        service.release_start.set()

        with self.assertRaises(RuntimeError) as first_context:
            await asyncio.wait_for(first_start, timeout=1.0)
        with self.assertRaises(NsStateError) as second_context:
            await asyncio.wait_for(second_start, timeout=1.0)

        self.assertIs(failure, first_context.exception)
        self.assertEqual(1, service.start_calls)
        self.assertEqual("failed", second_context.exception.details["current_state"])
        self.assertEqual(
            ["stopping"],
            second_context.exception.details["allowed_target_states"],
        )

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

    async def test_stop_waits_for_failed_start_then_cleans_up(self) -> None:
        failure = RuntimeError("blocked startup failure sentinel")
        service = _BlockingRuntimeService(start_error=failure)
        start_task = asyncio.create_task(service.start())
        await asyncio.wait_for(service.start_entered.wait(), timeout=1.0)

        stop_task = asyncio.create_task(service.stop())
        await asyncio.sleep(0)
        self.assertFalse(stop_task.done())
        service.release_start.set()

        with self.assertRaises(RuntimeError) as context:
            await asyncio.wait_for(start_task, timeout=1.0)
        await asyncio.wait_for(stop_task, timeout=1.0)

        self.assertIs(failure, context.exception)
        self.assertIs(RuntimeServiceState.STOPPED, service.state)
        self.assertEqual(1, service.start_calls)
        self.assertEqual(1, service.stop_calls)

    async def test_concurrent_stop_calls_share_one_successful_attempt(self) -> None:
        service = _BlockingStopRuntimeService()
        await service.start()
        first_stop = asyncio.create_task(service.stop())
        await asyncio.wait_for(service.first_stop_entered.wait(), timeout=1.0)

        waiting_stops = [asyncio.create_task(service.stop()) for _ in range(3)]
        await asyncio.sleep(0)
        self.assertTrue(all(not task.done() for task in waiting_stops))
        service.release_first_stop.set()

        await asyncio.wait_for(
            asyncio.gather(first_stop, *waiting_stops),
            timeout=1.0,
        )
        self.assertIs(RuntimeServiceState.STOPPED, service.state)
        self.assertEqual(1, service.stop_calls)
        self.assertEqual(1, service.maximum_active_stop_calls)

    async def test_waiting_stop_takes_over_after_first_attempt_fails(self) -> None:
        failure = RuntimeError("first shutdown attempt sentinel")
        service = _BlockingStopRuntimeService(first_stop_error=failure)
        await service.start()
        first_stop = asyncio.create_task(service.stop())
        await asyncio.wait_for(service.first_stop_entered.wait(), timeout=1.0)

        waiting_stops = [asyncio.create_task(service.stop()) for _ in range(3)]
        await asyncio.sleep(0)
        self.assertTrue(all(not task.done() for task in waiting_stops))
        service.release_first_stop.set()

        with self.assertRaises(RuntimeError) as context:
            await asyncio.wait_for(first_stop, timeout=1.0)
        await asyncio.wait_for(
            asyncio.gather(*waiting_stops),
            timeout=1.0,
        )

        self.assertIs(failure, context.exception)
        self.assertTrue(service.second_stop_entered.is_set())
        self.assertIs(RuntimeServiceState.STOPPED, service.state)
        self.assertEqual(2, service.stop_calls)
        self.assertEqual(1, service.maximum_active_stop_calls)

    async def test_hook_error_text_is_not_copied_to_lifecycle_error(self) -> None:
        secret = "runtime-hook-secret-57f2"
        failure = RuntimeError(secret)

        class _SensitiveFailureRuntimeService(RuntimeService):
            async def _on_start(self) -> None:
                raise failure

        service = _SensitiveFailureRuntimeService(
            context=_create_runtime_context(),
        )
        with self.assertRaises(RuntimeError) as context:
            await service.start()
        self.assertIs(failure, context.exception)
        self.assertNotIn(failure, vars(service).values())

        with self.assertRaises(NsStateError) as transition_context:
            await service.start()

        lifecycle_error = transition_context.exception
        self.assertNotIn(secret, str(lifecycle_error))
        self.assertNotIn(secret, repr(lifecycle_error.details))
        self.assertNotIn(secret, repr(lifecycle_error.to_dict()))


class RuntimeServiceLoopBindingTestCase(unittest.TestCase):

    def test_service_cannot_cross_event_loops(self) -> None:
        service = RuntimeService(context=_create_runtime_context())
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

    def test_first_loop_binding_is_atomic_across_threads(self) -> None:
        service = _ThreadRaceRuntimeService()
        start_barrier = threading.Barrier(3)
        results: queue.Queue[tuple[str, BaseException | None]] = queue.Queue()
        loops: list[asyncio.AbstractEventLoop] = []
        loops_lock = threading.Lock()

        def run_start() -> None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                with loops_lock:
                    loops.append(loop)
                start_barrier.wait(timeout=5.0)
                try:
                    loop.run_until_complete(service.start())
                except BaseException as error:
                    results.put(("error", error))
                else:
                    results.put(("success", None))
            except BaseException as error:
                results.put(("thread_failure", error))
            finally:
                asyncio.set_event_loop(None)
                loop.close()

        threads = [
            threading.Thread(target=run_start, name=f"runtime-loop-{index}")
            for index in range(2)
        ]
        first_result: tuple[str, BaseException | None] | None = None
        try:
            for thread in threads:
                thread.start()
            start_barrier.wait(timeout=5.0)
            self.assertTrue(service.start_entered.wait(timeout=5.0))
            first_result = results.get(timeout=5.0)
        finally:
            service.release_start.set()
            for thread in threads:
                thread.join(timeout=5.0)

        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(2, len(loops))
        self.assertIsNot(loops[0], loops[1])
        self.assertIsNotNone(first_result)
        all_results = [first_result, results.get(timeout=5.0)]
        self.assertEqual(
            ["error", "success"],
            sorted(result[0] for result in all_results if result is not None),
        )

        errors = [
            result[1]
            for result in all_results
            if result is not None and result[0] == "error"
        ]
        self.assertEqual(1, len(errors))
        error = errors[0]
        self.assertIsInstance(error, NsStateError)
        assert isinstance(error, NsStateError)
        self.assertEqual("NS_STATE_ERROR", error.code)
        self.assertEqual(
            "RuntimeService cannot be shared across event loops.",
            error.message,
        )
        self.assertEqual(
            {"component", "operation", "current_state", "reason"},
            set(error.details),
        )
        self.assertEqual("runtime_service", error.details["component"])
        self.assertEqual("start", error.details["operation"])
        self.assertIn(error.details["current_state"], {"created", "starting"})
        self.assertEqual("event_loop_mismatch", error.details["reason"])
        self.assertNotIsInstance(error, RuntimeError)
        self.assertNotIn("attached to a different loop", str(error).lower())
        self.assertNotIn("bound to a different event loop", str(error).lower())
        self.assertIsNone(error.__cause__)
        self.assertIsNone(error.__context__)
        self.assertEqual(1, service.start_calls)
        self.assertIs(RuntimeServiceState.RUNNING, service.state)


if __name__ == "__main__":
    unittest.main()
