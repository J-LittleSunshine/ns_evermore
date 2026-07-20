# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"


_BOOTSTRAP_PROBE = r"""
import asyncio
import builtins
import importlib.util
import json
import os
from pathlib import Path
import sys

scenario, config_path, startup_root, project_root = sys.argv[1:]

assert "ns_common" not in sys.modules
assert "ns_runtime.main" not in sys.modules

ensure_runtime_dirs_calls = []
mkdir_calls = []
write_calls = []
policy_set_calls = []

original_profile = sys.getprofile()
original_path_mkdir = Path.mkdir
original_path_open = Path.open
original_builtin_open = builtins.open
original_os_mkdir = os.mkdir
original_find_spec = importlib.util.find_spec
original_set_event_loop_policy = asyncio.set_event_loop_policy
initial_policy = asyncio.get_event_loop_policy()

def profile_calls(frame, event, arg):
    if (
        event == "call"
        and frame.f_code.co_name == "ensure_runtime_dirs"
        and frame.f_globals.get("__name__") == "ns_common.paths"
    ):
        ensure_runtime_dirs_calls.append("ns_common.paths.ensure_runtime_dirs")

def watched_path_mkdir(path, *args, **kwargs):
    mkdir_calls.append(os.fspath(path))
    return original_path_mkdir(path, *args, **kwargs)

def watched_os_mkdir(path, *args, **kwargs):
    mkdir_calls.append(os.fspath(path))
    return original_os_mkdir(path, *args, **kwargs)

def watched_path_open(path, mode="r", *args, **kwargs):
    if any(flag in mode for flag in ("w", "a", "x", "+")):
        write_calls.append(os.fspath(path))
    return original_path_open(path, mode, *args, **kwargs)

def watched_builtin_open(file, mode="r", *args, **kwargs):
    if any(flag in mode for flag in ("w", "a", "x", "+")):
        write_calls.append(os.fspath(file))
    return original_builtin_open(file, mode, *args, **kwargs)

def watched_find_spec(name, *args, **kwargs):
    if name == "websockets":
        return None
    return original_find_spec(name, *args, **kwargs)

def watched_set_event_loop_policy(policy):
    policy_set_calls.append(type(policy).__name__)
    return original_set_event_loop_policy(policy)

sys.setprofile(profile_calls)
Path.mkdir = watched_path_mkdir
Path.open = watched_path_open
builtins.open = watched_builtin_open
os.mkdir = watched_os_mkdir
importlib.util.find_spec = watched_find_spec
asyncio.set_event_loop_policy = watched_set_event_loop_policy

import ns_runtime.main as main_module
main_import_loaded_ns_common = "ns_common" in sys.modules

try:
    return_code = main_module.main(
        environment="prod" if scenario == "security" else "local",
        config_path=config_path,
        startup_root=startup_root,
    )
except BaseException as error:
    error_code = getattr(error, "code", type(error).__name__)
    error_details = dict(getattr(error, "details", {}))
    return_code = None
else:
    error_code = "RETURNED"
    error_details = {"return_code": return_code}
finally:
    sys.setprofile(original_profile)

config_model = sys.modules.get("ns_common.config.model")
config_facade = sys.modules.get("ns_common.config")
common_facade = sys.modules.get("ns_common")
bootstrap_module = sys.modules.get("ns_runtime._bootstrap")
exceptions_facade = sys.modules.get("ns_common.exceptions")
global_config_initialized = any(
    module is not None and "ns_config" in vars(module)
    for module in (config_model, config_facade, common_facade)
)

repository_directories = {
    name: (Path(project_root) / name).exists()
    for name in ("data", "etc", "log", "tmp")
}
result = {
    "error_code": error_code,
    "error_details": error_details,
    "ensure_runtime_dirs_calls": ensure_runtime_dirs_calls,
    "mkdir_calls": mkdir_calls,
    "write_calls": write_calls,
    "main_import_loaded_ns_common": main_import_loaded_ns_common,
    "global_config_initialized": global_config_initialized,
    "authoritative_config_identity": (
        bootstrap_module.NsConfig is config_model.NsConfig
        is config_facade.NsConfig
    ),
    "authoritative_error_identity": (
        bootstrap_module.NsDependencyError is exceptions_facade.NsDependencyError
        and bootstrap_module.NsRuntimeStartupSecurityError
        is exceptions_facade.NsRuntimeStartupSecurityError
    ),
    "repository_directories": repository_directories,
    "startup_root_exists": Path(startup_root).exists(),
    "policy_set_calls": policy_set_calls,
    "event_loop_policy_unchanged": (
        asyncio.get_event_loop_policy() is initial_policy
    ),
    "runtime_service_module_loaded": "ns_runtime.service" in sys.modules,
}
print(json.dumps(result, sort_keys=True))
"""


def _run_bootstrap_probe(
    *,
    scenario: str,
    raw_config: dict[str, object],
) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    with tempfile.TemporaryDirectory(
        prefix=f"ns-runtime-bootstrap-{scenario}-",
    ) as temporary_directory:
        temporary_root = Path(temporary_directory)
        isolated_project = temporary_root / "project"
        isolated_source = isolated_project / "src"
        shutil.copytree(
            SOURCE_ROOT,
            isolated_source,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        config_path = temporary_root / "runtime-config.json"
        config_path.write_text(json.dumps(raw_config), encoding="utf-8")
        startup_root = temporary_root / "explicit-startup-root"

        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(isolated_source)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                _BOOTSTRAP_PROBE,
                scenario,
                str(config_path),
                str(startup_root),
                str(isolated_project),
            ],
            cwd=temporary_root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        result = (
            json.loads(completed.stdout)
            if completed.returncode == 0 and completed.stdout
            else {}
        )
    return completed, result


class RuntimeColdBootstrapTestCase(unittest.TestCase):

    def _assert_zero_bootstrap_side_effects(
        self,
        result: dict[str, object],
    ) -> None:
        self.assertEqual([], result["ensure_runtime_dirs_calls"])
        self.assertEqual([], result["mkdir_calls"])
        self.assertEqual([], result["write_calls"])
        self.assertFalse(result["main_import_loaded_ns_common"])
        self.assertFalse(result["global_config_initialized"])
        self.assertTrue(result["authoritative_config_identity"])
        self.assertTrue(result["authoritative_error_identity"])
        self.assertEqual(
            {"data": False, "etc": False, "log": False, "tmp": False},
            result["repository_directories"],
        )
        self.assertFalse(result["startup_root_exists"])
        self.assertEqual([], result["policy_set_calls"])
        self.assertTrue(result["event_loop_policy_unchanged"])
        self.assertFalse(result["runtime_service_module_loaded"])

    def test_fresh_main_dependency_failure_has_no_bootstrap_side_effects(
        self,
    ) -> None:
        completed, result = _run_bootstrap_probe(
            scenario="dependency",
            raw_config={},
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("NS_DEPENDENCY_ERROR", result["error_code"])
        self.assertEqual(
            "websockets",
            result["error_details"]["dependency"],  # type: ignore[index]
        )
        self._assert_zero_bootstrap_side_effects(result)

    def test_fresh_main_security_failure_has_no_bootstrap_side_effects(
        self,
    ) -> None:
        completed, result = _run_bootstrap_probe(
            scenario="security",
            raw_config={
                "backend": {
                    "debug": False,
                    "secret_key": "s" * 32,
                },
            },
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual(
            "RUNTIME_STARTUP_SECURITY_ERROR",
            result["error_code"],
        )
        self.assertEqual(
            "plaintext_transport_in_production",
            result["error_details"]["reason"],  # type: ignore[index]
        )
        self._assert_zero_bootstrap_side_effects(result)


if __name__ == "__main__":
    unittest.main()
