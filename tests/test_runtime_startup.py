# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
from dataclasses import FrozenInstanceError, replace
import logging
from pathlib import Path
import tempfile
import unittest

from ns_common.async_runtime import (
    NsEventLoopImplementation,
    NsEventLoopSelector,
    TaskSupervisor,
)
from ns_common.config import NsConfig
from ns_common.exceptions import (
    NsConfigError,
    NsDependencyError,
    NsRuntimeConfigInvalidError,
    NsRuntimeStartupSecurityError,
    NsRuntimeTransportDisabledError,
    NsValidationError,
)
from ns_common.observability import InMemoryMetricsSink, InMemoryTraceSink
from ns_common.time import SystemClock
from ns_runtime.context import RuntimeContext
from ns_runtime.startup import (
    RuntimeStartupDirectories,
    RuntimeStartupPreflight,
)


def _create_context(config: NsConfig | None = None) -> RuntimeContext:
    return RuntimeContext(
        config=config or NsConfig.from_dict({}, environment="local"),
        clock=SystemClock(),
        logger=logging.Logger("runtime-startup-test"),
        metrics=InMemoryMetricsSink(),
        traces=InMemoryTraceSink(),
        task_supervisor=TaskSupervisor(),
    )


def _replace_runtime_config(config: NsConfig, **changes: object) -> NsConfig:
    return replace(config, runtime=replace(config.runtime, **changes))


def _production_candidate_config() -> NsConfig:
    return NsConfig.from_dict(
        {
            "backend": {
                "debug": False,
                "secret_key": "s" * 32,
            },
        },
        environment="local",
    )


def _windows_selector(
    *,
    installed_policies: list[asyncio.AbstractEventLoopPolicy] | None = None,
) -> NsEventLoopSelector:
    target = installed_policies if installed_policies is not None else []
    return NsEventLoopSelector(
        platform_system=lambda: "Windows",
        policy_setter=target.append,
    )


class RuntimeStartupPreflightTestCase(unittest.TestCase):

    def test_validate_prepares_explicit_directories_without_installing_policy(
        self,
    ) -> None:
        dependency_checks: list[str] = []

        def dependency_probe(package_name: str) -> object:
            dependency_checks.append(package_name)
            return object()

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "runtime-root"
            directories = RuntimeStartupDirectories.for_root(root)
            result = RuntimeStartupPreflight(
                event_loop_selector=_windows_selector(),
                dependency_probe=dependency_probe,
            ).validate(
                _create_context(),
                environment="local",
                directories=directories,
            )

            self.assertEqual("local", result.environment)
            self.assertIs(
                NsEventLoopImplementation.ASYNCIO,
                result.event_loop.selected,
            )
            self.assertFalse(result.event_loop_policy_installed)
            self.assertEqual(("websocket_tcp",), result.enabled_transport_adapters)
            self.assertEqual((), result.tls_transport_adapters)
            self.assertEqual("sqlite", result.state_store_backend)
            self.assertEqual(("websockets",), result.checked_dependencies)
            self.assertEqual(["websockets"], dependency_checks)
            self.assertEqual(
                ("data", "etc", "log", "tmp"),
                result.prepared_directories,
            )
            for _, path in directories.required_directories():
                self.assertTrue(path.is_dir())

            with self.assertRaises(FrozenInstanceError):
                result.environment = "dev"  # type: ignore[misc]

    def test_prepare_installs_policy_only_after_all_preflight_checks(self) -> None:
        installed_policies: list[asyncio.AbstractEventLoopPolicy] = []
        with tempfile.TemporaryDirectory() as temporary_directory:
            directories = RuntimeStartupDirectories.for_root(
                Path(temporary_directory) / "runtime-root",
            )
            result = RuntimeStartupPreflight(
                event_loop_selector=_windows_selector(
                    installed_policies=installed_policies,
                ),
                dependency_probe=lambda _: object(),
            ).prepare(
                _create_context(),
                environment="test",
                directories=directories,
            )

        self.assertTrue(result.event_loop_policy_installed)
        self.assertEqual(1, len(installed_policies))
        self.assertIsInstance(
            installed_policies[0],
            asyncio.AbstractEventLoopPolicy,
        )

    def test_invalid_environment_fails_before_dependencies_directories_or_policy(
        self,
    ) -> None:
        installed_policies: list[asyncio.AbstractEventLoopPolicy] = []
        dependency_checks: list[str] = []
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "must-not-exist"
            preflight = RuntimeStartupPreflight(
                event_loop_selector=_windows_selector(
                    installed_policies=installed_policies,
                ),
                dependency_probe=lambda name: dependency_checks.append(name),
            )

            with self.assertRaises(NsRuntimeConfigInvalidError) as context:
                preflight.prepare(
                    _create_context(),
                    environment="production",
                    directories=RuntimeStartupDirectories.for_root(root),
                )

            self.assertEqual("environment", context.exception.details["field"])
            self.assertFalse(root.exists())
        self.assertEqual([], dependency_checks)
        self.assertEqual([], installed_policies)

    def test_invalid_config_fails_before_dependency_directory_and_policy(self) -> None:
        config = NsConfig.from_dict({}, environment="local")
        invalid_transport = replace(config.runtime.transport, listen_port=0)
        invalid_config = _replace_runtime_config(
            config,
            transport=invalid_transport,
        )
        installed_policies: list[asyncio.AbstractEventLoopPolicy] = []

        def unexpected_dependency(_: str) -> object:
            self.fail("dependency check must run after configuration validation")

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "must-not-exist"
            with self.assertRaises(NsConfigError) as context:
                RuntimeStartupPreflight(
                    event_loop_selector=_windows_selector(
                        installed_policies=installed_policies,
                    ),
                    dependency_probe=unexpected_dependency,
                ).prepare(
                    _create_context(invalid_config),
                    environment="local",
                    directories=RuntimeStartupDirectories.for_root(root),
                )

            self.assertEqual(
                "runtime.transport.listen_port",
                context.exception.details["field"],
            )
            self.assertFalse(root.exists())
        self.assertEqual([], installed_policies)

    def test_missing_transport_dependency_fails_without_leaking_probe_error(
        self,
    ) -> None:
        installed_policies: list[asyncio.AbstractEventLoopPolicy] = []
        secret = "dependency-probe-secret"

        def broken_probe(_: str) -> object:
            raise RuntimeError(secret)

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "must-not-exist"
            with self.assertRaises(NsDependencyError) as context:
                RuntimeStartupPreflight(
                    event_loop_selector=_windows_selector(
                        installed_policies=installed_policies,
                    ),
                    dependency_probe=broken_probe,
                ).prepare(
                    _create_context(),
                    environment="local",
                    directories=RuntimeStartupDirectories.for_root(root),
                )

            error = context.exception
            self.assertEqual("websockets", error.details["dependency"])
            self.assertNotIn(secret, str(error))
            self.assertNotIn(secret, str(error.to_dict()))
            self.assertIsNone(error.__context__)
            self.assertIsNone(error.__cause__)
            self.assertFalse(root.exists())
        self.assertEqual([], installed_policies)

    def test_unimplemented_future_transport_is_feature_gated(self) -> None:
        config = NsConfig.from_dict({}, environment="local")
        transport = replace(
            config.runtime.transport,
            websocket_http3=replace(
                config.runtime.transport.websocket_http3,
                enabled=True,
            ),
        )
        config = _replace_runtime_config(config, transport=transport)

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "must-not-exist"
            with self.assertRaises(NsRuntimeTransportDisabledError) as context:
                RuntimeStartupPreflight(
                    event_loop_selector=_windows_selector(),
                    dependency_probe=lambda _: object(),
                ).validate(
                    _create_context(config),
                    environment="local",
                    directories=RuntimeStartupDirectories.for_root(root),
                )

            self.assertEqual(
                ["websocket_http3"],
                context.exception.details["adapters"],
            )
            self.assertEqual(
                "feature_not_implemented",
                context.exception.details["reason"],
            )
            self.assertFalse(root.exists())

    def test_production_plaintext_transport_fails_security_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "must-not-exist"
            with self.assertRaises(NsRuntimeStartupSecurityError) as context:
                RuntimeStartupPreflight(
                    event_loop_selector=_windows_selector(),
                ).validate(
                    _create_context(_production_candidate_config()),
                    environment="prod",
                    directories=RuntimeStartupDirectories.for_root(root),
                )

            self.assertEqual(
                "plaintext_transport_in_production",
                context.exception.details["reason"],
            )
            self.assertFalse(root.exists())

    def test_production_sqlite_state_store_fails_security_preflight(self) -> None:
        config = _production_candidate_config()
        transport = replace(
            config.runtime.transport,
            websocket_tcp=replace(
                config.runtime.transport.websocket_tcp,
                tls_enabled=True,
            ),
        )
        config = _replace_runtime_config(config, transport=transport)

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "must-not-exist"
            with self.assertRaises(NsRuntimeStartupSecurityError) as context:
                RuntimeStartupPreflight(
                    event_loop_selector=_windows_selector(),
                ).validate(
                    _create_context(config),
                    environment="prod",
                    directories=RuntimeStartupDirectories.for_root(root),
                )

            self.assertEqual(
                "non_production_state_store_backend",
                context.exception.details["reason"],
            )
            self.assertFalse(root.exists())

    def test_production_redis_and_valkey_configuration_pass_preflight(self) -> None:
        for backend, url in (
            ("redis", "rediss://127.0.0.1:6379/0"),
            ("valkey", "valkeys://127.0.0.1:6379/0"),
        ):
            with self.subTest(backend=backend):
                config = NsConfig.from_dict(
                    {
                        "backend": {
                            "debug": False,
                            "secret_key": "s" * 32,
                        },
                        "runtime": {
                            "transport": {
                                "websocket_tcp": {
                                    "tls_enabled": True,
                                },
                            },
                            "state_store": {
                                "backend": backend,
                                "url": url,
                            },
                        },
                    },
                    environment="prod",
                )
                with tempfile.TemporaryDirectory() as temporary_directory:
                    result = RuntimeStartupPreflight(
                        event_loop_selector=_windows_selector(),
                        dependency_probe=lambda _: object(),
                    ).validate(
                        _create_context(config),
                        environment="prod",
                        directories=RuntimeStartupDirectories.for_root(
                            Path(temporary_directory) / "runtime-root",
                        ),
                    )

                self.assertEqual(backend, result.state_store_backend)
                self.assertEqual(("websocket_tcp",), result.tls_transport_adapters)
                self.assertEqual(("websockets",), result.checked_dependencies)

    def test_tls_capability_is_checked_before_directories_and_policy(self) -> None:
        config = NsConfig.from_dict({}, environment="local")
        transport = replace(
            config.runtime.transport,
            websocket_tcp=replace(
                config.runtime.transport.websocket_tcp,
                tls_enabled=True,
            ),
        )
        config = _replace_runtime_config(config, transport=transport)
        installed_policies: list[asyncio.AbstractEventLoopPolicy] = []

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "must-not-exist"
            with self.assertRaises(NsRuntimeStartupSecurityError) as context:
                RuntimeStartupPreflight(
                    event_loop_selector=_windows_selector(
                        installed_policies=installed_policies,
                    ),
                    dependency_probe=lambda _: object(),
                    tls_capability_probe=lambda: False,
                ).prepare(
                    _create_context(config),
                    environment="local",
                    directories=RuntimeStartupDirectories.for_root(root),
                )

            self.assertEqual(
                "server_tls_capability_unavailable",
                context.exception.details["reason"],
            )
            self.assertFalse(root.exists())
        self.assertEqual([], installed_policies)

    def test_non_prod_plaintext_policy_is_enforced_at_startup(self) -> None:
        config = NsConfig.from_dict({}, environment="local")
        security = replace(
            config.runtime.security,
            allow_plaintext_non_prod=False,
        )
        config = _replace_runtime_config(config, security=security)

        with self.assertRaises(NsRuntimeStartupSecurityError) as context:
            RuntimeStartupPreflight(
                event_loop_selector=_windows_selector(),
            ).validate(
                _create_context(config),
                environment="test",
                directories=RuntimeStartupDirectories.for_root(
                    Path(tempfile.gettempdir()) / "unused-runtime-root",
                ),
            )

        self.assertEqual(
            "plaintext_transport_disabled",
            context.exception.details["reason"],
        )

    def test_sqlite_parent_outside_standard_data_directory_is_prepared(self) -> None:
        config = NsConfig.from_dict({}, environment="local")
        state_store = replace(
            config.runtime.state_store,
            sqlite_path="var/runtime/state.sqlite3",
        )
        config = _replace_runtime_config(config, state_store=state_store)

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "runtime-root"
            result = RuntimeStartupPreflight(
                event_loop_selector=_windows_selector(),
                dependency_probe=lambda _: object(),
            ).validate(
                _create_context(config),
                environment="dev",
                directories=RuntimeStartupDirectories.for_root(root),
            )

            self.assertIn("state_store", result.prepared_directories)
            self.assertTrue((root / "var" / "runtime").is_dir())

    def test_directory_access_failure_is_safe_and_policy_is_not_installed(self) -> None:
        installed_policies: list[asyncio.AbstractEventLoopPolicy] = []
        with tempfile.TemporaryDirectory(prefix="runtime-path-secret-") as temporary_directory:
            root = Path(temporary_directory) / "private-runtime-root"
            with self.assertRaises(NsDependencyError) as context:
                RuntimeStartupPreflight(
                    event_loop_selector=_windows_selector(
                        installed_policies=installed_policies,
                    ),
                    dependency_probe=lambda _: object(),
                    directory_access_probe=lambda _path, _mode: False,
                ).prepare(
                    _create_context(),
                    environment="local",
                    directories=RuntimeStartupDirectories.for_root(root),
                )

            error = context.exception
            self.assertEqual("access_denied", error.details["reason"])
            self.assertNotIn(str(root), str(error))
            self.assertNotIn(str(root), str(error.to_dict()))
            self.assertIsNone(error.__context__)
            self.assertIsNone(error.__cause__)
        self.assertEqual([], installed_policies)

    def test_context_and_directory_types_are_validated_without_repr(self) -> None:
        preflight = RuntimeStartupPreflight(
            event_loop_selector=_windows_selector(),
        )
        with self.assertRaises(NsValidationError) as context_error:
            preflight.validate(object())  # type: ignore[arg-type]
        self.assertEqual("context", context_error.exception.details["dependency"])

        with self.assertRaises(NsValidationError) as directory_error:
            preflight.validate(
                _create_context(),
                directories=object(),  # type: ignore[arg-type]
            )
        self.assertEqual(
            "directories",
            directory_error.exception.details["dependency"],
        )

        with self.assertRaises(NsValidationError) as selector_error:
            RuntimeStartupPreflight(
                event_loop_selector=object(),  # type: ignore[arg-type]
            )
        self.assertEqual(
            "event_loop_selector",
            selector_error.exception.details["dependency"],
        )


if __name__ == "__main__":
    unittest.main()
