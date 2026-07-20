# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from ns_common.async_runtime import NsEventLoopSelector
from ns_common.exceptions import (
    NsConfigError,
    NsDependencyError,
    NsRuntimeStartupSecurityError,
    NsRuntimeTransportDisabledError,
)
from ns_common.logger import NsLogger, close_ns_loggers
from ns_runtime.main import main
from ns_runtime.startup import (
    RuntimeStartupDirectories,
    RuntimeStartupPreflight,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"


def _write_config(
    directory: Path,
    raw_config: dict[str, object],
    *,
    filename: str = "ns_config.json",
) -> Path:
    config_path = directory / filename
    config_path.write_text(
        json.dumps(raw_config),
        encoding="utf-8",
    )
    return config_path


def _production_config(runtime: dict[str, object] | None = None) -> dict[str, object]:
    config: dict[str, object] = {
        "backend": {
            "debug": False,
            "secret_key": "s" * 32,
        },
    }
    if runtime is not None:
        config["runtime"] = runtime
    return config


def _controlled_preflight(
    *,
    dependency_available: bool = True,
    tls_available: bool = True,
) -> tuple[RuntimeStartupPreflight, list[object]]:
    installed_policies: list[object] = []
    preflight = RuntimeStartupPreflight(
        event_loop_selector=NsEventLoopSelector(
            platform_system=lambda: "Windows",
            policy_setter=installed_policies.append,
        ),
        dependency_probe=(
            (lambda _: object())
            if dependency_available
            else (lambda _: None)
        ),
        tls_capability_probe=lambda: tls_available,
    )
    return preflight, installed_policies


class NsRuntimeMainTestCase(unittest.TestCase):

    def test_main_wires_each_initial_role_to_explicit_safe_logger(self) -> None:
        captured_contexts: list[object] = []

        class CapturingService:
            def __init__(self, *, context: object) -> None:
                captured_contexts.append(context)

            async def start(self) -> None:
                return None

            async def stop(self) -> None:
                return None

        try:
            with tempfile.TemporaryDirectory() as temporary_directory:
                temporary_root = Path(temporary_directory)
                for role in (
                    "singleton",
                    "sub_node",
                    "standby_master",
                    "active_master",
                ):
                    with self.subTest(role=role):
                        cluster: dict[str, object] = {"role": role}
                        if role == "sub_node":
                            cluster["active_master_url"] = (
                                "https://master.example.test"
                            )
                        config_path = _write_config(
                            temporary_root,
                            {"runtime": {"cluster": cluster}},
                            filename=f"{role}.json",
                        )
                        startup_root = temporary_root / role
                        preflight, _ = _controlled_preflight()

                        with mock.patch(
                            "ns_runtime.service.RuntimeService",
                            CapturingService,
                        ):
                            self.assertEqual(
                                0,
                                main(
                                    environment="test",
                                    config_path=config_path,
                                    startup_root=startup_root,
                                    preflight=preflight,
                                ),
                            )

                        context = captured_contexts[-1]
                        self.assertEqual(
                            role,
                            context.config.runtime.cluster.role,  # type: ignore[attr-defined]
                        )
                        self.assertIsInstance(
                            context.logger,  # type: ignore[attr-defined]
                            NsLogger,
                        )
                        self.assertTrue((startup_root / "log").is_dir())
        finally:
            close_ns_loggers()

    def test_main_succeeds_with_runtime_dependencies_or_fails_closed(self) -> None:
        if importlib.util.find_spec("websockets") is None:
            with self.assertRaises(NsDependencyError) as context:
                main()
            self.assertEqual("websockets", context.exception.details["dependency"])
            return

        self.assertEqual(0, main())

    def test_process_entry_starts_and_exits_as_a_module(self) -> None:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(SRC_DIR)

        completed = subprocess.run(
            [sys.executable, "-m", "ns_runtime.main"],
            cwd=ROOT_DIR,
            env=environment,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        if importlib.util.find_spec("websockets") is None:
            self.assertNotEqual(0, completed.returncode)
            self.assertEqual("", completed.stdout)
            self.assertIn("NS_DEPENDENCY_ERROR", completed.stderr)
            self.assertIn("websockets", completed.stderr)
        else:
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual("", completed.stdout)
            self.assertEqual("", completed.stderr)

    def test_main_normalizes_production_plaintext_config_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            config_path = _write_config(
                temporary_root,
                _production_config(),
            )
            startup_root = temporary_root / "runtime-root"
            preflight, installed_policies = _controlled_preflight()

            with mock.patch(
                "ns_runtime.service.RuntimeService",
                side_effect=AssertionError("service must not be constructed"),
            ):
                with self.assertRaises(
                    NsRuntimeStartupSecurityError,
                ) as context:
                    main(
                        environment="prod",
                        config_path=config_path,
                        startup_directories=(
                            RuntimeStartupDirectories.for_root(startup_root)
                        ),
                        preflight=preflight,
                    )

            self.assertEqual(
                "RUNTIME_STARTUP_SECURITY_ERROR",
                context.exception.code,
            )
            self.assertEqual(
                "plaintext_transport_in_production",
                context.exception.details["reason"],
            )
            self.assertFalse(startup_root.exists())
            self.assertEqual([], installed_policies)

    def test_main_normalizes_production_sqlite_config_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            config_path = _write_config(
                temporary_root,
                _production_config({
                    "transport": {
                        "websocket_tcp": {
                            "tls_enabled": True,
                        },
                    },
                }),
            )
            startup_root = temporary_root / "runtime-root"
            preflight, installed_policies = _controlled_preflight()

            with mock.patch(
                "ns_runtime.service.RuntimeService",
                side_effect=AssertionError("service must not be constructed"),
            ):
                with self.assertRaises(
                    NsRuntimeStartupSecurityError,
                ) as context:
                    main(
                        environment="prod",
                        config_path=config_path,
                        startup_directories=(
                            RuntimeStartupDirectories.for_root(startup_root)
                        ),
                        preflight=preflight,
                    )

            self.assertEqual(
                "non_production_state_store_backend",
                context.exception.details["reason"],
            )
            self.assertFalse(startup_root.exists())
            self.assertEqual([], installed_policies)

    def test_main_normalizes_remaining_startup_security_config_errors(
        self,
    ) -> None:
        cases = (
            (
                "disabled_production_tls_requirement",
                {
                    "runtime": {
                        "security": {
                            "require_tls_in_prod": False,
                        },
                    },
                },
                "production_tls_requirement_disabled",
            ),
            (
                "disabled_non_production_plaintext",
                {
                    "runtime": {
                        "security": {
                            "allow_plaintext_non_prod": False,
                        },
                    },
                },
                "plaintext_transport_disabled",
            ),
        )
        for case_name, raw_config, expected_reason in cases:
            with self.subTest(case=case_name):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    temporary_root = Path(temporary_directory)
                    config_path = _write_config(temporary_root, raw_config)
                    startup_root = temporary_root / "runtime-root"
                    preflight, installed_policies = _controlled_preflight()

                    with mock.patch(
                        "ns_runtime.service.RuntimeService",
                        side_effect=AssertionError(
                            "service must not be constructed",
                        ),
                    ):
                        with self.assertRaises(
                            NsRuntimeStartupSecurityError,
                        ) as context:
                            main(
                                environment="local",
                                config_path=config_path,
                                startup_directories=(
                                    RuntimeStartupDirectories.for_root(
                                        startup_root,
                                    )
                                ),
                                preflight=preflight,
                            )

                    self.assertEqual(
                        expected_reason,
                        context.exception.details["reason"],
                    )
                    self.assertFalse(startup_root.exists())
                    self.assertEqual([], installed_policies)

    def test_main_preserves_ordinary_config_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            config_path = _write_config(
                temporary_root,
                {
                    "runtime": {
                        "transport": {
                            "listen_port": 0,
                        },
                    },
                },
            )
            startup_root = temporary_root / "runtime-root"
            preflight, installed_policies = _controlled_preflight()

            with mock.patch(
                "ns_runtime.service.RuntimeService",
                side_effect=AssertionError("service must not be constructed"),
            ):
                with self.assertRaises(NsConfigError) as context:
                    main(
                        environment="local",
                        config_path=config_path,
                        startup_directories=(
                            RuntimeStartupDirectories.for_root(startup_root)
                        ),
                        preflight=preflight,
                    )

            self.assertEqual("NS_CONFIG_ERROR", context.exception.code)
            self.assertEqual(
                "runtime.transport.listen_port",
                context.exception.details["field"],
            )
            self.assertNotIsInstance(
                context.exception,
                NsRuntimeStartupSecurityError,
            )
            self.assertFalse(startup_root.exists())
            self.assertEqual([], installed_policies)

    def test_main_missing_websockets_has_no_directory_or_policy_side_effect(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            config_path = _write_config(temporary_root, {})
            startup_root = temporary_root / "runtime-root"
            preflight, installed_policies = _controlled_preflight(
                dependency_available=False,
            )

            with (
                mock.patch(
                    "ns_runtime._bootstrap.get_default_config_path",
                    return_value=config_path,
                ) as default_path,
                mock.patch(
                    "ns_common.config.codec.ensure_runtime_dirs",
                    side_effect=AssertionError(
                        "explicit startup config loading must not prepare dirs",
                    ),
                ),
                mock.patch(
                    "ns_runtime.service.RuntimeService",
                    side_effect=AssertionError(
                        "service must not be constructed",
                    ),
                ),
            ):
                with self.assertRaises(NsDependencyError) as context:
                    main(
                        environment="local",
                        startup_directories=(
                            RuntimeStartupDirectories.for_root(startup_root)
                        ),
                        preflight=preflight,
                    )

            default_path.assert_called_once_with("local")
            self.assertEqual("NS_DEPENDENCY_ERROR", context.exception.code)
            self.assertEqual(
                "websockets",
                context.exception.details["dependency"],
            )
            self.assertFalse(startup_root.exists())
            self.assertEqual([], installed_policies)

    def test_main_tls_failure_has_no_directory_or_policy_side_effect(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            config_path = _write_config(
                temporary_root,
                {
                    "runtime": {
                        "transport": {
                            "websocket_tcp": {
                                "tls_enabled": True,
                            },
                        },
                    },
                },
            )
            startup_root = temporary_root / "runtime-root"
            preflight, installed_policies = _controlled_preflight(
                tls_available=False,
            )

            with mock.patch(
                "ns_runtime.service.RuntimeService",
                side_effect=AssertionError("service must not be constructed"),
            ):
                with self.assertRaises(
                    NsRuntimeStartupSecurityError,
                ) as context:
                    main(
                        environment="local",
                        config_path=config_path,
                        startup_directories=(
                            RuntimeStartupDirectories.for_root(startup_root)
                        ),
                        preflight=preflight,
                    )

            self.assertEqual(
                "server_tls_capability_unavailable",
                context.exception.details["reason"],
            )
            self.assertFalse(startup_root.exists())
            self.assertEqual([], installed_policies)

    def test_main_unavailable_transport_has_no_directory_or_policy_side_effect(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            config_path = _write_config(
                temporary_root,
                {
                    "runtime": {
                        "transport": {
                            "websocket_http3": {
                                "enabled": True,
                            },
                        },
                    },
                },
            )
            startup_root = temporary_root / "runtime-root"
            preflight, installed_policies = _controlled_preflight()

            with mock.patch(
                "ns_runtime.service.RuntimeService",
                side_effect=AssertionError("service must not be constructed"),
            ):
                with self.assertRaises(
                    NsRuntimeTransportDisabledError,
                ) as context:
                    main(
                        environment="local",
                        config_path=config_path,
                        startup_directories=(
                            RuntimeStartupDirectories.for_root(startup_root)
                        ),
                        preflight=preflight,
                    )

            self.assertEqual(
                "RUNTIME_TRANSPORT_DISABLED",
                context.exception.code,
            )
            self.assertFalse(startup_root.exists())
            self.assertEqual([], installed_policies)

    def test_importing_component_has_no_process_side_effects(self) -> None:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(SRC_DIR)

        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import asyncio, sys; "
                    "before = asyncio.get_event_loop_policy(); "
                    "import ns_runtime; "
                    "after = asyncio.get_event_loop_policy(); "
                    "forbidden = {'django', 'ns_common', 'redis', 'uvloop', "
                    "'valkey', 'websockets'}; "
                    "valid = (before is after and not forbidden.intersection("
                    "sys.modules) and 'ns_runtime.main' not in sys.modules); "
                    "raise SystemExit(0 if valid else 1)"
                ),
            ],
            cwd=ROOT_DIR,
            env=environment,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("", completed.stdout)
        self.assertEqual("", completed.stderr)

    def test_importing_entry_module_does_not_load_startup_dependencies(self) -> None:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(SRC_DIR)

        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import asyncio, sys; "
                    "before = asyncio.get_event_loop_policy(); "
                    "import ns_runtime.main; "
                    "after = asyncio.get_event_loop_policy(); "
                    "forbidden = {'ns_common', 'ns_runtime._bootstrap', "
                    "'ns_runtime.context', "
                    "'ns_runtime.service', 'ns_runtime.startup', 'uvloop', "
                    "'websockets'}; "
                    "valid = (before is after and not forbidden.intersection("
                    "sys.modules)); "
                    "raise SystemExit(0 if valid else 1)"
                ),
            ],
            cwd=ROOT_DIR,
            env=environment,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("", completed.stdout)
        self.assertEqual("", completed.stderr)


if __name__ == "__main__":
    unittest.main()
