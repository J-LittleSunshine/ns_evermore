# -*- coding: utf-8 -*-
from __future__ import annotations

from contextlib import redirect_stdout
import asyncio
from dataclasses import FrozenInstanceError
from io import StringIO
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from ns_common.async_runtime import NsEventLoopSelector
from ns_runtime.diagnostics import inspect_local_runtime
from ns_runtime.main import _module_main
from ns_runtime.startup import RuntimeStartupPreflight


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"


def _write_empty_config(directory: Path) -> Path:
    config_path = directory / "ns_config.json"
    config_path.write_text("{}", encoding="utf-8")
    return config_path


def _controlled_preflight(
    *,
    dependency_available: bool = True,
) -> tuple[RuntimeStartupPreflight, list[asyncio.AbstractEventLoopPolicy]]:
    installed_policies: list[asyncio.AbstractEventLoopPolicy] = []
    return (
        RuntimeStartupPreflight(
            event_loop_selector=NsEventLoopSelector(
                platform_system=lambda: "Windows",
                policy_setter=installed_policies.append,
            ),
            dependency_probe=(
                (lambda _: object())
                if dependency_available
                else (lambda _: None)
            ),
        ),
        installed_policies,
    )


class RuntimeLocalDiagnosticsTestCase(unittest.TestCase):

    def test_inspection_is_read_only_and_reports_missing_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            config_path = _write_empty_config(temporary_root)
            startup_root = temporary_root / "must-not-exist"
            preflight, installed_policies = _controlled_preflight()

            report = inspect_local_runtime(
                environment="test",
                config_path=config_path,
                startup_root=startup_root,
                preflight=preflight,
            )

            self.assertFalse(report.ready)
            self.assertTrue(report.config_valid)
            self.assertTrue(report.dependencies_available)
            self.assertEqual("asyncio", report.event_loop_implementation)
            self.assertEqual("not_ready", report.to_dict()["status"])
            self.assertEqual(
                {"missing"},
                {
                    item["state"]
                    for item in report.to_dict()["directories"]  # type: ignore[union-attr]
                },
            )
            self.assertFalse(startup_root.exists())
            self.assertEqual([], installed_policies)

            with self.assertRaises(FrozenInstanceError):
                report.ready = True  # type: ignore[misc]

    def test_inspection_reports_ready_without_installing_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            config_path = _write_empty_config(temporary_root)
            startup_root = temporary_root / "runtime-root"
            for role in ("data", "etc", "log", "tmp"):
                (startup_root / role).mkdir(parents=True, exist_ok=True)
            preflight, installed_policies = _controlled_preflight()

            report = inspect_local_runtime(
                environment="local",
                config_path=config_path,
                startup_root=startup_root,
                preflight=preflight,
            )

        self.assertTrue(report.ready)
        self.assertEqual("ready", report.to_dict()["status"])
        self.assertEqual(("websockets",), report.checked_dependencies)
        self.assertEqual([], installed_policies)

    def test_module_diagnostic_emits_one_json_object_and_exit_status(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            config_path = _write_empty_config(temporary_root)
            startup_root = temporary_root / "missing-runtime-root"
            stdout = StringIO()

            with redirect_stdout(stdout):
                status = _module_main([
                    "diagnose",
                    "--environment",
                    "test",
                    "--config",
                    str(config_path),
                    "--startup-root",
                    str(startup_root),
                ])

            payload = json.loads(stdout.getvalue())
            if importlib.util.find_spec("websockets") is None:
                self.assertEqual(2, status)
                self.assertEqual("error", payload["status"])
                self.assertEqual("NS_DEPENDENCY_ERROR", payload["error_code"])
                self.assertEqual(
                    "websockets",
                    payload["details"]["dependency"],
                )
            else:
                self.assertEqual(1, status)
                self.assertEqual("not_ready", payload["status"])
                self.assertFalse(payload["ready"])
            self.assertFalse(startup_root.exists())

    def test_module_diagnostic_error_is_sanitized(self) -> None:
        with tempfile.TemporaryDirectory(prefix="diagnostic-secret-") as directory:
            invalid_config = Path(directory) / "credential-secret.json"
            invalid_config.write_text(
                '{"credential":"credential-secret"',
                encoding="utf-8",
            )
            stdout = StringIO()

            with redirect_stdout(stdout):
                status = _module_main([
                    "diagnose",
                    "--environment",
                    "local",
                    "--config",
                    str(invalid_config),
                    "--startup-root",
                    str(Path(directory) / "runtime-secret"),
                ])

            raw_output = stdout.getvalue()
            payload = json.loads(raw_output)
            self.assertEqual(2, status)
            self.assertEqual("error", payload["status"])
            self.assertIn("error_code", payload)
            self.assertIn("numeric_code", payload)
            self.assertNotIn("credential-secret", raw_output)
            self.assertNotIn(str(invalid_config), raw_output)

    def test_process_diagnostic_runs_through_the_only_module_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            config_path = _write_empty_config(temporary_root)
            startup_root = temporary_root / "missing-runtime-root"
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(SRC_DIR)

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "ns_runtime.main",
                    "diagnose",
                    "--environment",
                    "test",
                    "--config",
                    str(config_path),
                    "--startup-root",
                    str(startup_root),
                ],
                cwd=ROOT_DIR,
                env=environment,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

            payload = json.loads(completed.stdout)
            if importlib.util.find_spec("websockets") is None:
                self.assertEqual(2, completed.returncode)
                self.assertEqual("NS_DEPENDENCY_ERROR", payload["error_code"])
            else:
                self.assertEqual(1, completed.returncode)
                self.assertEqual("not_ready", payload["status"])
            self.assertEqual("", completed.stderr)
            self.assertFalse(startup_root.exists())

    def test_cold_process_diagnostic_does_not_load_runtime_service_or_mutate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            config_path = _write_empty_config(temporary_root)
            startup_root = temporary_root / "missing-runtime-root"
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(SRC_DIR)
            script = (
                "import json,sys;"
                "from ns_runtime.main import _module_main;"
                "rc=_module_main(sys.argv[1:]);"
                "print(json.dumps({'return_code':rc,"
                "'service_loaded':'ns_runtime.service' in sys.modules,"
                "'monitor_loaded':'ns_runtime.event_loop_observability' in sys.modules,"
                "'websockets_loaded':'websockets' in sys.modules}))"
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    script,
                    "diagnose",
                    "--environment",
                    "test",
                    "--config",
                    str(config_path),
                    "--startup-root",
                    str(startup_root),
                ],
                cwd=ROOT_DIR,
                env=environment,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            lines = completed.stdout.splitlines()
            self.assertEqual(2, len(lines), completed.stdout)
            report = json.loads(lines[0])
            process_state = json.loads(lines[1])
            if importlib.util.find_spec("websockets") is None:
                self.assertEqual("error", report["status"])
                self.assertEqual("NS_DEPENDENCY_ERROR", report["error_code"])
                self.assertEqual(2, process_state["return_code"])
            else:
                self.assertEqual("not_ready", report["status"])
                self.assertEqual(1, process_state["return_code"])
            self.assertFalse(process_state["service_loaded"])
            self.assertFalse(process_state["monitor_loaded"])
            self.assertFalse(process_state["websockets_loaded"])
            self.assertFalse(startup_root.exists())


if __name__ == "__main__":
    unittest.main()
