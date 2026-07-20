# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
import logging
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

from ns_common.async_runtime import TaskSupervisor
from ns_common.config import NsConfig
from ns_common.exceptions import NsValidationError
from ns_common.http_client import NsHttpClientOwner
from ns_common.observability import (
    InMemoryDiagnosticSnapshotSink,
    InMemoryMetricsSink,
    InMemoryTraceSink,
)
from ns_common.time import SystemClock
from ns_runtime.context import RuntimeContext, RuntimeDependencySlots
from ns_runtime.service import RuntimeService


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"


_CONTEXT_SIDE_EFFECT_PROBE_SETUP = """
import asyncio
import builtins
import logging
import os
from pathlib import Path
import sys
import threading

for forbidden_module in (
    "ns_common",
    "ns_common.config",
    "ns_common.config.model",
    "ns_common.paths",
    "ns_common.logger",
    "ns_common.http_client",
):
    assert forbidden_module not in sys.modules, forbidden_module

events = []
original_builtin_open = builtins.open
original_exists = Path.exists
original_mkdir = Path.mkdir
original_open = Path.open
original_getenv = os.getenv
environ_type = type(os.environ)
original_environ_getitem = environ_type.__getitem__
original_thread_start = threading.Thread.start
original_create_task = asyncio.create_task
original_new_event_loop = asyncio.new_event_loop
policy = asyncio.get_event_loop_policy()
policy_type = type(policy)
original_policy_new_event_loop = policy_type.new_event_loop

def watched_builtin_open(file, *args, **kwargs):
    events.append(("builtin_open", os.fspath(file)))
    return original_builtin_open(file, *args, **kwargs)

def watched_exists(path):
    events.append(("path_exists", os.fspath(path)))
    return original_exists(path)

def watched_mkdir(path, *args, **kwargs):
    events.append(("path_mkdir", os.fspath(path)))
    return original_mkdir(path, *args, **kwargs)

def watched_open(path, *args, **kwargs):
    events.append(("path_open", os.fspath(path)))
    return original_open(path, *args, **kwargs)

def watched_getenv(*args, **kwargs):
    events.append(("getenv", str(args[0]) if args else ""))
    return original_getenv(*args, **kwargs)

def watched_environ_getitem(environ, key):
    events.append(("environ_getitem", str(key)))
    return original_environ_getitem(environ, key)

def watched_thread_start(thread, *args, **kwargs):
    events.append(("thread_start", thread.name))
    return original_thread_start(thread, *args, **kwargs)

def watched_create_task(*args, **kwargs):
    events.append(("create_task", "asyncio"))
    return original_create_task(*args, **kwargs)

def watched_new_event_loop(*args, **kwargs):
    events.append(("new_event_loop", "asyncio"))
    return original_new_event_loop(*args, **kwargs)

def watched_policy_new_event_loop(policy_instance, *args, **kwargs):
    events.append(("policy_new_event_loop", type(policy_instance).__name__))
    return original_policy_new_event_loop(policy_instance, *args, **kwargs)

builtins.open = watched_builtin_open
Path.exists = watched_exists
Path.mkdir = watched_mkdir
Path.open = watched_open
os.getenv = watched_getenv
environ_type.__getitem__ = watched_environ_getitem
threading.Thread.start = watched_thread_start
asyncio.create_task = watched_create_task
asyncio.new_event_loop = watched_new_event_loop
policy_type.new_event_loop = watched_policy_new_event_loop

before_threads = tuple(threading.enumerate())
before_root_handlers = tuple(logging.getLogger().handlers)
before_handler_refs = tuple(logging._handlerList)
before_loggers = tuple(logging.Logger.manager.loggerDict)
"""


_CONTEXT_SIDE_EFFECT_PROBE_ASSERTIONS = """
assert events == [], events
assert before_threads == tuple(threading.enumerate())
assert before_root_handlers == tuple(logging.getLogger().handlers)
assert before_handler_refs == tuple(logging._handlerList)
assert before_loggers == tuple(logging.Logger.manager.loggerDict)
assert policy is asyncio.get_event_loop_policy()
for forbidden_module in (
    "ns_common",
    "ns_common.config",
    "ns_common.config.model",
    "ns_common.paths",
    "ns_common.logger",
    "ns_common.http_client",
):
    assert forbidden_module not in sys.modules, forbidden_module
"""


def _run_context_side_effect_probe(
    body: str,
    *,
    temporary_prefix: str,
) -> tuple[subprocess.CompletedProcess[str], tuple[Path, ...]]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(SRC_DIR)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    probe = (
        _CONTEXT_SIDE_EFFECT_PROBE_SETUP
        + body
        + _CONTEXT_SIDE_EFFECT_PROBE_ASSERTIONS
    )

    with tempfile.TemporaryDirectory(prefix=temporary_prefix) as temporary_root:
        completed = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=temporary_root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        remaining_paths = tuple(Path(temporary_root).iterdir())

    return completed, remaining_paths


def _create_dependencies() -> dict[str, object]:
    return {
        "config": NsConfig(),
        "clock": SystemClock(),
        "logger": logging.Logger("runtime-context-test"),
        "metrics": InMemoryMetricsSink(),
        "traces": InMemoryTraceSink(),
        "task_supervisor": TaskSupervisor(),
    }


class RuntimeContextTestCase(unittest.TestCase):

    def test_context_is_frozen_keyword_only_and_preserves_dependency_identity(
        self,
    ) -> None:
        injected = _create_dependencies()
        context = RuntimeContext(**injected)

        self.assertTrue(is_dataclass(RuntimeContext))
        self.assertEqual(
            (
                "config",
                "clock",
                "logger",
                "metrics",
                "traces",
                "task_supervisor",
                "dependencies",
            ),
            tuple(item.name for item in fields(RuntimeContext)),
        )
        for dependency, value in injected.items():
            self.assertIs(value, getattr(context, dependency))
        self.assertIsInstance(context.config, NsConfig)
        self.assertIsInstance(context.clock, SystemClock)
        self.assertIsInstance(context.logger, logging.Logger)
        self.assertIsInstance(context.metrics, InMemoryMetricsSink)
        self.assertIsInstance(context.traces, InMemoryTraceSink)
        self.assertIsInstance(context.task_supervisor, TaskSupervisor)
        self.assertIs(context.config, context.config_snapshot)
        self.assertIs(context.metrics, context.metrics_sink)
        self.assertIs(context.traces, context.trace_sink)
        self.assertIsNone(context.diagnostic_snapshot_sink)
        self.assertIsNone(context.http_client_owner)

        with self.assertRaises(FrozenInstanceError):
            context.clock = SystemClock()  # type: ignore[misc]
        with self.assertRaises(TypeError):
            RuntimeContext(*injected.values())  # type: ignore[misc]

    def test_typed_future_slots_are_optional_frozen_and_preserve_identity(
        self,
    ) -> None:
        diagnostics = InMemoryDiagnosticSnapshotSink()
        http_owner = NsHttpClientOwner()
        slots = RuntimeDependencySlots(
            diagnostic_snapshot_sink=diagnostics,
            http_client_owner=http_owner,
        )
        context = RuntimeContext(
            **_create_dependencies(),
            dependencies=slots,
        )

        self.assertIs(diagnostics, context.diagnostic_snapshot_sink)
        self.assertIs(http_owner, context.http_client_owner)
        self.assertIs(slots, context.dependencies)
        self.assertFalse(hasattr(slots, "get"))
        self.assertFalse(hasattr(slots, "register"))
        self.assertFalse(hasattr(slots, "resolve"))
        with self.assertRaises(FrozenInstanceError):
            slots.http_client_owner = None  # type: ignore[misc]

    def test_invalid_core_dependencies_return_stable_validation_errors(self) -> None:
        valid = _create_dependencies()
        expected_types = {
            "config": "NsConfig",
            "clock": "Clock",
            "logger": "Logger",
            "metrics": "MetricsSink",
            "traces": "TraceSink",
            "task_supervisor": "TaskSupervisor",
            "dependencies": "RuntimeDependencySlots",
        }

        for dependency, expected_type in expected_types.items():
            with self.subTest(dependency=dependency):
                arguments = dict(valid)
                arguments[dependency] = object()
                with self.assertRaises(NsValidationError) as context:
                    RuntimeContext(**arguments)
                self.assertEqual("NS_VALIDATION_ERROR", context.exception.code)
                self.assertEqual(
                    "RuntimeContext dependency is invalid.",
                    context.exception.message,
                )
                self.assertEqual(
                    {
                        "component": "runtime_context",
                        "dependency": dependency,
                        "expected_type": expected_type,
                        "actual_type": "object",
                    },
                    context.exception.details,
                )

    def test_invalid_future_slots_return_stable_validation_errors(self) -> None:
        cases = (
            (
                "diagnostic_snapshot_sink",
                "DiagnosticSnapshotSink",
            ),
            ("http_client_owner", "NsHttpClientOwner"),
        )
        for dependency, expected_type in cases:
            with self.subTest(dependency=dependency):
                with self.assertRaises(NsValidationError) as context:
                    RuntimeDependencySlots(
                        **{dependency: object()},  # type: ignore[arg-type]
                    )
                self.assertEqual(
                    {
                        "component": "runtime_context",
                        "dependency": f"dependencies.{dependency}",
                        "expected_type": expected_type,
                        "actual_type": "object",
                    },
                    context.exception.details,
                )

    def test_matching_class_names_do_not_bypass_exact_type_validation(self) -> None:
        FakeNsConfig = type("NsConfig", (), {})
        arguments = _create_dependencies()
        arguments["config"] = FakeNsConfig()
        with self.assertRaises(NsValidationError):
            RuntimeContext(**arguments)

        FakeNsHttpClientOwner = type("NsHttpClientOwner", (), {})
        with self.assertRaises(NsValidationError):
            RuntimeDependencySlots(
                http_client_owner=FakeNsHttpClientOwner(),  # type: ignore[arg-type]
            )

    def test_validation_errors_do_not_copy_dependency_repr_or_secret_text(
        self,
    ) -> None:
        secret = "runtime-context-secret-0f931eb2"

        class _SecretDependency:
            def __repr__(self) -> str:
                return secret

            def __str__(self) -> str:
                return secret

        arguments = _create_dependencies()
        arguments["clock"] = _SecretDependency()
        with self.assertRaises(NsValidationError) as context:
            RuntimeContext(**arguments)

        error = context.exception
        self.assertNotIn(secret, str(error))
        self.assertNotIn(secret, repr(error.details))
        self.assertNotIn(secret, repr(error.to_dict()))

    def test_runtime_service_requires_and_exposes_the_exact_context(self) -> None:
        context = RuntimeContext(**_create_dependencies())
        service = RuntimeService(context=context)

        self.assertIs(context, service.context)
        with self.assertRaises(AttributeError):
            service.context = RuntimeContext(  # type: ignore[misc]
                **_create_dependencies(),
            )
        with self.assertRaises(NsValidationError) as error_context:
            RuntimeService(context=object())  # type: ignore[arg-type]
        self.assertEqual(
            {
                "component": "runtime_service",
                "dependency": "context",
                "expected_type": "RuntimeContext",
                "actual_type": "object",
            },
            error_context.exception.details,
        )

    def test_constructing_context_and_service_does_not_use_dependencies(self) -> None:
        dependencies = _create_dependencies()
        metrics = dependencies["metrics"]
        traces = dependencies["traces"]
        supervisor = dependencies["task_supervisor"]

        context = RuntimeContext(**dependencies)
        RuntimeService(context=context)

        self.assertEqual((), metrics.records)  # type: ignore[attr-defined]
        self.assertEqual((), traces.records)  # type: ignore[attr-defined]
        self.assertEqual((), supervisor.task_names)  # type: ignore[attr-defined]

    def test_context_module_has_no_ambient_locator_or_import_side_effects(
        self,
    ) -> None:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(SRC_DIR)
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import asyncio, threading; "
                    "policy = asyncio.get_event_loop_policy(); "
                    "threads = tuple(threading.enumerate()); "
                    "import ns_runtime.context as module; "
                    "public = tuple(module.__all__); "
                    "forbidden = ('get_runtime_context', 'set_runtime_context', "
                    "'current_runtime_context', 'register_dependency', "
                    "'resolve_dependency'); "
                    "valid = ("
                    "policy is asyncio.get_event_loop_policy() and "
                    "threads == tuple(threading.enumerate()) and "
                    "public == ('RuntimeContext', 'RuntimeDependencySlots') and "
                    "not any(hasattr(module, name) for name in forbidden) and "
                    "not any(isinstance(value, module.RuntimeContext) "
                    "for value in vars(module).values())); "
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

    def test_context_cold_import_does_not_load_config_or_touch_filesystem(
        self,
    ) -> None:
        completed, remaining_paths = _run_context_side_effect_probe(
            """
import ns_runtime.context as module
slots = module.RuntimeDependencySlots()

assert slots.diagnostic_snapshot_sink is None
assert slots.http_client_owner is None
""",
            temporary_prefix="ns-runtime-context-cold-import-",
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("", completed.stdout)
        self.assertEqual("", completed.stderr)
        self.assertEqual((), remaining_paths)

    def test_invalid_context_construction_has_no_import_side_effects(
        self,
    ) -> None:
        completed, remaining_paths = _run_context_side_effect_probe(
            """
import ns_runtime.context as module

try:
    module.RuntimeContext(
        config=object(),
        clock=object(),
        logger=object(),
        metrics=object(),
        traces=object(),
        task_supervisor=object(),
    )
except BaseException as error:
    expected_details = {
        "component": "runtime_context",
        "dependency": "config",
        "expected_type": "NsConfig",
        "actual_type": "object",
    }
    assert type(error).__module__ == "ns_common.exceptions.common"
    assert type(error).__name__ == "NsValidationError"
    assert error.code == "NS_VALIDATION_ERROR"
    assert error.message == "RuntimeContext dependency is invalid."
    assert error.details == expected_details
    assert error.to_dict() == {
        "code": "NS_VALIDATION_ERROR",
        "numeric_code": 100200,
        "message": "RuntimeContext dependency is invalid.",
        "details": expected_details,
    }
else:
    raise AssertionError("invalid config must be rejected")
""",
            temporary_prefix="ns-runtime-context-invalid-config-",
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("", completed.stdout)
        self.assertEqual("", completed.stderr)
        self.assertEqual((), remaining_paths)

    def test_invalid_http_owner_has_no_import_side_effects(self) -> None:
        completed, remaining_paths = _run_context_side_effect_probe(
            """
import ns_runtime.context as module

try:
    module.RuntimeDependencySlots(http_client_owner=object())
except BaseException as error:
    expected_details = {
        "component": "runtime_context",
        "dependency": "dependencies.http_client_owner",
        "expected_type": "NsHttpClientOwner",
        "actual_type": "object",
    }
    assert type(error).__module__ == "ns_common.exceptions.common"
    assert type(error).__name__ == "NsValidationError"
    assert error.code == "NS_VALIDATION_ERROR"
    assert error.message == "RuntimeContext dependency is invalid."
    assert error.details == expected_details
else:
    raise AssertionError("invalid HTTP owner must be rejected")
""",
            temporary_prefix="ns-runtime-context-invalid-http-owner-",
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("", completed.stdout)
        self.assertEqual("", completed.stderr)
        self.assertEqual((), remaining_paths)


if __name__ == "__main__":
    unittest.main()
