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


if __name__ == "__main__":
    unittest.main()
