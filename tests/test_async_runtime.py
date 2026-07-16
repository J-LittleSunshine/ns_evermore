# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import sys
import types
import unittest
from dataclasses import FrozenInstanceError

from ns_common.async_runtime import (
    NsEventLoopImplementation,
    NsEventLoopSelector,
    NsTaskSupervisorState,
    TaskSupervisor,
    install_event_loop_policy,
    select_event_loop,
)
from ns_common.config import (
    NsConfig,
    NsConfigGroupMetadata,
    NsRuntimeEventLoopConfig,
)
from ns_common.exceptions import (
    NsConfigError,
    NsDependencyError,
    NsStateError,
)


def event_loop_config(
    implementation: str = "auto",
    *,
    apply_mode: str = "restart_required",
) -> NsRuntimeEventLoopConfig:
    return NsRuntimeEventLoopConfig(
        implementation=implementation,  # type: ignore[arg-type]
        metadata=NsConfigGroupMetadata(
            apply_mode=apply_mode,  # type: ignore[arg-type]
        ),
    )


class NsEventLoopSelectorTestCase(unittest.TestCase):

    @unittest.skipUnless(sys.platform == "win32", "real Windows policy check")
    def test_real_windows_auto_uses_standard_asyncio(self) -> None:
        selection = NsEventLoopSelector().select(event_loop_config())

        self.assertIs(NsEventLoopImplementation.ASYNCIO, selection.selected)
        self.assertEqual("windows", selection.platform)

    def test_windows_auto_selects_standard_asyncio_without_loading_uvloop(self) -> None:
        def unexpected_loader(_: str) -> object:
            raise AssertionError("uvloop must not be imported for Windows auto mode")

        selection = NsEventLoopSelector(
            platform_system=lambda: "Windows",
            module_loader=unexpected_loader,
        ).select(event_loop_config())

        self.assertIs(NsEventLoopImplementation.ASYNCIO, selection.selected)
        self.assertEqual("windows", selection.platform)
        self.assertEqual("auto_windows_asyncio", selection.reason)
        self.assertFalse(selection.fallback)

    def test_linux_auto_prefers_uvloop_when_available(self) -> None:
        uvloop_policy = asyncio.DefaultEventLoopPolicy()
        installed_policies: list[asyncio.AbstractEventLoopPolicy] = []
        warnings: list[str] = []
        fake_uvloop = types.SimpleNamespace(EventLoopPolicy=lambda: uvloop_policy)

        selection = NsEventLoopSelector(
            platform_system=lambda: "Linux",
            module_loader=lambda name: fake_uvloop if name == "uvloop" else None,
            policy_setter=installed_policies.append,
            warning_emitter=warnings.append,
        ).install(event_loop_config())

        self.assertIs(NsEventLoopImplementation.UVLOOP, selection.selected)
        self.assertEqual("auto_linux_uvloop", selection.reason)
        self.assertEqual([uvloop_policy], installed_policies)
        self.assertEqual([], warnings)

    def test_linux_auto_falls_back_when_uvloop_policy_initialization_fails(self) -> None:
        asyncio_policy = asyncio.DefaultEventLoopPolicy()
        installed_policies: list[asyncio.AbstractEventLoopPolicy] = []
        warnings: list[str] = []

        def broken_policy_factory() -> asyncio.AbstractEventLoopPolicy:
            raise RuntimeError("broken uvloop policy")

        fake_uvloop = types.SimpleNamespace(EventLoopPolicy=broken_policy_factory)
        selection = NsEventLoopSelector(
            platform_system=lambda: "Linux",
            module_loader=lambda _: fake_uvloop,
            asyncio_policy_factory=lambda: asyncio_policy,
            policy_setter=installed_policies.append,
            warning_emitter=warnings.append,
        ).install(event_loop_config())

        self.assertIs(NsEventLoopImplementation.ASYNCIO, selection.selected)
        self.assertTrue(selection.fallback)
        self.assertEqual("auto_uvloop_initialization_failed", selection.reason)
        self.assertEqual([asyncio_policy], installed_policies)
        self.assertEqual([selection.warning], warnings)

    def test_linux_auto_falls_back_to_asyncio_and_warns(self) -> None:
        asyncio_policy = asyncio.DefaultEventLoopPolicy()
        installed_policies: list[asyncio.AbstractEventLoopPolicy] = []
        warnings: list[str] = []

        def missing_uvloop(_: str) -> object:
            raise ModuleNotFoundError("uvloop")

        selection = NsEventLoopSelector(
            platform_system=lambda: "Linux",
            module_loader=missing_uvloop,
            asyncio_policy_factory=lambda: asyncio_policy,
            policy_setter=installed_policies.append,
            warning_emitter=warnings.append,
        ).install(event_loop_config())

        self.assertIs(NsEventLoopImplementation.ASYNCIO, selection.selected)
        self.assertTrue(selection.fallback)
        self.assertEqual("auto_uvloop_unavailable", selection.reason)
        self.assertEqual([asyncio_policy], installed_policies)
        self.assertEqual([selection.warning], warnings)

    def test_explicit_asyncio_never_probes_uvloop(self) -> None:
        def unexpected_loader(_: str) -> object:
            raise AssertionError("explicit asyncio must not import uvloop")

        selection = NsEventLoopSelector(
            platform_system=lambda: "Linux",
            module_loader=unexpected_loader,
        ).select(event_loop_config("asyncio"))

        self.assertIs(NsEventLoopImplementation.ASYNCIO, selection.selected)
        self.assertEqual("explicit_asyncio", selection.reason)

    def test_explicit_uvloop_missing_fails_without_fallback(self) -> None:
        def missing_uvloop(_: str) -> object:
            raise ModuleNotFoundError("uvloop")

        with self.assertRaises(NsDependencyError) as context:
            NsEventLoopSelector(
                platform_system=lambda: "Linux",
                module_loader=missing_uvloop,
            ).install(event_loop_config("uvloop"))

        self.assertEqual(
            "runtime.event_loop.implementation",
            context.exception.details["field"],
        )
        self.assertEqual("uvloop", context.exception.details["package"])

    def test_explicit_uvloop_policy_initialization_failure_is_standardized(self) -> None:
        def broken_policy_factory() -> asyncio.AbstractEventLoopPolicy:
            raise RuntimeError("broken uvloop policy")

        fake_uvloop = types.SimpleNamespace(EventLoopPolicy=broken_policy_factory)
        with self.assertRaises(NsDependencyError) as context:
            NsEventLoopSelector(
                platform_system=lambda: "Linux",
                module_loader=lambda _: fake_uvloop,
            ).install(event_loop_config("uvloop"))

        self.assertEqual("policy_initialization", context.exception.details["phase"])

    def test_select_also_reports_linux_auto_fallback(self) -> None:
        warnings: list[str] = []

        def missing_uvloop(_: str) -> object:
            raise ModuleNotFoundError("uvloop")

        selection = NsEventLoopSelector(
            platform_system=lambda: "Linux",
            module_loader=missing_uvloop,
            warning_emitter=warnings.append,
        ).select(event_loop_config())

        self.assertTrue(selection.fallback)
        self.assertEqual([selection.warning], warnings)

    def test_explicit_uvloop_is_rejected_on_windows(self) -> None:
        with self.assertRaises(NsDependencyError) as context:
            NsEventLoopSelector(
                platform_system=lambda: "win32",
            ).select(event_loop_config("uvloop"))

        self.assertEqual("windows", context.exception.details["platform"])

    def test_running_event_loop_rejects_policy_change_as_restart_required(self) -> None:
        async def attempt_install() -> None:
            with self.assertRaises(NsStateError) as context:
                NsEventLoopSelector(
                    platform_system=lambda: "Windows",
                    policy_setter=lambda _: self.fail("policy setter must not run"),
                ).install(event_loop_config("asyncio"))

            self.assertEqual("restart_required", context.exception.details["action"])
            self.assertEqual("restart_required", context.exception.details["apply_mode"])

        asyncio.run(attempt_install())

    def test_selector_rejects_invalid_config_and_apply_mode(self) -> None:
        selector = NsEventLoopSelector(platform_system=lambda: "Windows")

        with self.assertRaises(NsConfigError) as type_context:
            selector.select({})  # type: ignore[arg-type]
        self.assertEqual("runtime.event_loop", type_context.exception.details["field"])

        with self.assertRaises(NsConfigError) as mode_context:
            selector.select(event_loop_config(apply_mode="immediate"))
        self.assertEqual(
            "runtime.event_loop.metadata.apply_mode",
            mode_context.exception.details["field"],
        )

    def test_selection_is_immutable_and_helpers_accept_explicit_selector(self) -> None:
        selector = NsEventLoopSelector(platform_system=lambda: "Windows")
        config = event_loop_config("asyncio")
        selection = select_event_loop(config, selector=selector)

        with self.assertRaises(FrozenInstanceError):
            selection.reason = "changed"  # type: ignore[misc]

        installed: list[asyncio.AbstractEventLoopPolicy] = []
        install_selector = NsEventLoopSelector(
            platform_system=lambda: "Windows",
            policy_setter=installed.append,
        )
        installed_selection = install_event_loop_policy(
            config,
            selector=install_selector,
        )
        self.assertIs(NsEventLoopImplementation.ASYNCIO, installed_selection.selected)
        self.assertEqual(1, len(installed))

    def test_default_config_is_accepted_by_selector(self) -> None:
        config = NsConfig.from_dict({}).runtime.event_loop
        selection = select_event_loop(
            config,
            selector=NsEventLoopSelector(platform_system=lambda: "Windows"),
        )

        self.assertIs(NsEventLoopImplementation.ASYNCIO, selection.selected)
        self.assertEqual("windows", selection.platform)


class TaskSupervisorTestCase(unittest.IsolatedAsyncioTestCase):

    async def test_named_task_completion_is_reported(self) -> None:
        supervisor = TaskSupervisor()

        async def return_value() -> int:
            return 42

        task = supervisor.create_task(return_value(), name="answer")
        self.assertEqual("answer", task.get_name())
        self.assertEqual(42, await task)
        await asyncio.sleep(0)

        report = await supervisor.shutdown()
        self.assertEqual(("answer",), report.completed_tasks)
        self.assertEqual((), report.cancelled_tasks)
        self.assertEqual((), report.unfinished_tasks)
        self.assertEqual((), supervisor.pending_task_names)
        self.assertTrue(report.clean)
        self.assertIs(NsTaskSupervisorState.CLOSED, supervisor.state)

    async def test_task_failure_is_collected_and_forwarded_once(self) -> None:
        handled = []
        supervisor = TaskSupervisor(failure_handler=handled.append)

        async def fail() -> None:
            raise ValueError("boom")

        task = supervisor.create_task(fail(), name="failing-task")
        with self.assertRaisesRegex(ValueError, "boom"):
            await task
        await asyncio.sleep(0)

        self.assertEqual(1, len(supervisor.failures))
        self.assertEqual("failing-task", supervisor.failures[0].name)
        self.assertEqual("ValueError", supervisor.failures[0].exception_type)
        self.assertEqual("boom", supervisor.failures[0].message)
        self.assertEqual(list(supervisor.failures), handled)

        report = await supervisor.shutdown()
        self.assertEqual(("failing-task",), report.failed_tasks)
        self.assertEqual(1, len(report.failures))
        self.assertFalse(report.clean)

    async def test_shutdown_cancels_by_order_then_creation_without_hanging(self) -> None:
        cancellation_events: list[str] = []
        blocker = asyncio.Event()
        supervisor = TaskSupervisor()

        async def worker(name: str) -> None:
            try:
                await blocker.wait()
            except asyncio.CancelledError:
                cancellation_events.append(name)
                raise

        supervisor.create_task(worker("late"), name="late", cancel_order=20)
        supervisor.create_task(worker("first"), name="first", cancel_order=10)
        supervisor.create_task(worker("second"), name="second", cancel_order=10)
        await asyncio.sleep(0)

        report = await supervisor.shutdown(timeout_seconds=1.0)

        self.assertEqual(("first", "second", "late"), report.cancellation_order)
        self.assertEqual(["first", "second", "late"], cancellation_events)
        self.assertEqual(("late", "first", "second"), report.cancelled_tasks)
        self.assertEqual((), report.unfinished_tasks)
        self.assertEqual((), supervisor.pending_task_names)
        self.assertTrue(report.clean)

    async def test_exception_during_cancellation_is_a_failure(self) -> None:
        supervisor = TaskSupervisor()
        started = asyncio.Event()

        async def fail_during_cleanup() -> None:
            started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                raise RuntimeError("cleanup failed")

        supervisor.create_task(
            fail_during_cleanup(),
            name="cleanup-failure",
        )
        await started.wait()

        report = await supervisor.shutdown(timeout_seconds=1.0)
        self.assertEqual(("cleanup-failure",), report.failed_tasks)
        self.assertEqual((), report.cancelled_tasks)
        self.assertEqual("cleanup failed", report.failures[0].message)

    async def test_shutdown_timeout_returns_unfinished_task_report(self) -> None:
        supervisor = TaskSupervisor(shutdown_timeout_seconds=0.01)
        started = asyncio.Event()
        release = asyncio.Event()

        async def ignore_first_cancel() -> None:
            started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                await release.wait()

        task = supervisor.create_task(
            ignore_first_cancel(),
            name="stubborn",
            cancel_order=5,
        )
        await started.wait()

        report = await supervisor.shutdown()
        self.assertTrue(report.timed_out)
        self.assertFalse(report.clean)
        self.assertEqual(("stubborn",), report.cancellation_order)
        self.assertEqual("stubborn", report.unfinished_tasks[0].name)
        self.assertEqual(5, report.unfinished_tasks[0].cancel_order)
        self.assertGreaterEqual(report.unfinished_tasks[0].cancelling_count, 1)
        self.assertEqual(("stubborn",), supervisor.pending_task_names)

        release.set()
        await asyncio.wait_for(task, timeout=1.0)
        await asyncio.sleep(0)
        self.assertEqual((), supervisor.pending_task_names)

    async def test_duplicate_and_closed_registration_close_rejected_coroutines(self) -> None:
        supervisor = TaskSupervisor()

        async def no_op() -> None:
            return None

        first = supervisor.create_task(no_op(), name="unique")
        await first
        duplicate = no_op()
        with self.assertRaises(NsConfigError):
            supervisor.create_task(duplicate, name="unique")
        self.assertIsNone(duplicate.cr_frame)

        report = await supervisor.shutdown()
        closed = no_op()
        with self.assertRaises(NsStateError):
            supervisor.create_task(closed, name="after-close")
        self.assertIsNone(closed.cr_frame)
        self.assertIs(report, await supervisor.shutdown())

    async def test_registration_and_timeout_validation_are_strict(self) -> None:
        with self.assertRaises(NsConfigError):
            TaskSupervisor(shutdown_timeout_seconds=0)
        with self.assertRaises(NsConfigError):
            TaskSupervisor(shutdown_timeout_seconds=float("inf"))

        supervisor = TaskSupervisor()

        async def no_op() -> None:
            return None

        invalid_name = no_op()
        with self.assertRaises(NsConfigError):
            supervisor.create_task(invalid_name, name=" ")
        self.assertIsNone(invalid_name.cr_frame)

        invalid_order = no_op()
        with self.assertRaises(NsConfigError):
            supervisor.create_task(
                invalid_order,
                name="invalid-order",
                cancel_order=True,
            )
        self.assertIsNone(invalid_order.cr_frame)

        with self.assertRaises(NsStateError):
            supervisor.get_task("missing")

        with self.assertRaises(NsConfigError):
            await supervisor.shutdown(timeout_seconds="invalid")  # type: ignore[arg-type]

        clean_report = await supervisor.shutdown()
        self.assertEqual(0, clean_report.total_tasks)

    async def test_supervised_task_cannot_shutdown_its_own_supervisor(self) -> None:
        supervisor = TaskSupervisor()

        async def self_shutdown() -> None:
            await supervisor.shutdown()

        task = supervisor.create_task(self_shutdown(), name="self-shutdown")
        with self.assertRaises(NsStateError):
            await task
        await asyncio.sleep(0)

        report = await supervisor.shutdown()
        self.assertEqual(("self-shutdown",), report.failed_tasks)


class TaskSupervisorLoopBindingTestCase(unittest.TestCase):

    def test_supervisor_cannot_cross_event_loops(self) -> None:
        supervisor = TaskSupervisor()

        async def create_on_first_loop() -> None:
            task = supervisor.create_task(asyncio.sleep(0), name="first-loop")
            await task

        asyncio.run(create_on_first_loop())

        async def shutdown_on_second_loop() -> None:
            with self.assertRaises(NsStateError):
                await supervisor.shutdown()

        asyncio.run(shutdown_on_second_loop())


if __name__ == "__main__":
    unittest.main()
