# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import copy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

from ns_common.async_runtime import NsEventLoopSelector
from ns_common.exceptions import (
    NsConfigError,
    NsDependencyError,
    NsRuntimeStartupSecurityError,
    NsRuntimeTransportDisabledError,
    NsValidationError,
)
from ns_common.logger import NsLogger, close_ns_loggers
from ns_runtime.main import main as _runtime_main
from ns_runtime.startup import (
    RuntimeStartupDirectories,
    RuntimeStartupPreflight,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"


def main(**values: object) -> int:
    values.setdefault("self_check", True)
    return _runtime_main(**values)  # type: ignore[arg-type]


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
            "iam_internal_token": "b" * 32,
        },
    }
    runtime_config: dict[str, object] = {
        "iam": {
            "base_url": "https://iam.example.test/api/iam/",
            "internal_service_credential": "r" * 32,
        },
    }
    if runtime is not None:
        runtime_config.update(runtime)
    config["runtime"] = runtime_config
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

    def test_production_iam_handle_binds_backend_and_security_configuration(
        self,
    ) -> None:
        checks: list[bool] = []
        test_case = self

        class InspectingService:
            def __init__(
                self, *, context, transport_manager, logger_close,
                event_loop_monitor, logical_connection_owner,
            ) -> None:
                from ns_runtime.shutdown import RuntimeShutdownCoordinator

                self._owner = logical_connection_owner
                self.shutdown_coordinator = RuntimeShutdownCoordinator(
                    context=context, logger_close=logger_close,
                    transport_owner=transport_manager,
                    logical_connection_owner=logical_connection_owner,
                )

            async def start(self) -> None:
                iam = self._owner._iam
                handle = iam._http_authority
                binding = handle._NsHttpClientAuthorityHandle__binding
                client = binding._client
                httpx_client = binding._httpx_client
                checks.append(handle.is_current(iam_client=iam))
                with test_case.assertRaises(NsValidationError):
                    copy.copy(handle)
                uninitialized = object.__new__(type(handle))
                checks.append(not uninitialized.is_current(iam_client=iam))
                for denied_path in (
                    "https://evil.invalid/internal/runtime_access_check/",
                    "../runtime_access_check/",
                    "internal/not-allowlisted/",
                ):
                    with test_case.assertRaises(NsValidationError):
                        await handle.post(
                            denied_path, json_data={},
                            bearer_token="r" * 32,
                            trace_id="operation:path-attack",
                            expected_statuses={200},
                        )
                mutations = (
                    (client, "base_url", "https://evil.invalid/"),
                    (client, "_request_base_url", type(client._request_base_url)(
                        "https://evil.invalid/",
                    )),
                    (httpx_client, "_base_url", type(httpx_client.base_url)(
                        "https://evil.invalid/",
                    )),
                    (httpx_client, "_mounts", dict(httpx_client._mounts)),
                    (httpx_client, "_transport", object()),
                )
                for target, name, replacement in mutations:
                    original = getattr(target, name)
                    setattr(target, name, replacement)
                    checks.append(not handle.is_current(iam_client=iam))
                    setattr(target, name, original)
                    checks.append(handle.is_current(iam_client=iam))
                original_timeout = httpx_client._timeout
                httpx_client._timeout = type(original_timeout)(1.0)
                checks.append(not handle.is_current(iam_client=iam))
                httpx_client._timeout = original_timeout
                original_headers = httpx_client._headers
                httpx_client._headers = original_headers.copy()
                httpx_client._headers["x-route-attack"] = "1"
                checks.append(not handle.is_current(iam_client=iam))
                httpx_client._headers = original_headers
                pool = binding._transport._pool
                original_proxy = pool._proxy
                pool._proxy = object()
                checks.append(not handle.is_current(iam_client=iam))
                pool._proxy = original_proxy
                ssl_context = pool._ssl_context
                original_check_hostname = ssl_context.check_hostname
                ssl_context.check_hostname = not original_check_hostname
                checks.append(not handle.is_current(iam_client=iam))
                ssl_context.check_hostname = original_check_hostname
                checks.append(handle.is_current(iam_client=iam))

            async def stop(self) -> None:
                return None

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            config_path = _write_config(root, {})
            preflight, _ = _controlled_preflight()
            with mock.patch(
                "ns_runtime.transport.TransportRuntimeService",
                InspectingService,
            ):
                self.assertEqual(0, main(
                    environment="test", config_path=config_path,
                    startup_root=root / "runtime", preflight=preflight,
                ))
        self.assertTrue(all(checks))

    def test_iam_request_uses_bound_transport_during_concurrent_replacement(
        self,
    ) -> None:
        request_started = threading.Event()
        allow_response = threading.Event()
        outcomes: list[object] = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                request_started.set()
                allow_response.wait(5)
                body = b'{"success":true,"data":{"bound":true}}'
                self.send_response(200)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args: object) -> None:
                del args

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        class RequestingService:
            def __init__(
                self, *, context, transport_manager, logger_close,
                event_loop_monitor, logical_connection_owner,
            ) -> None:
                from ns_runtime.shutdown import RuntimeShutdownCoordinator

                self._owner = logical_connection_owner
                self.shutdown_coordinator = RuntimeShutdownCoordinator(
                    context=context, logger_close=logger_close,
                    transport_owner=transport_manager,
                    logical_connection_owner=logical_connection_owner,
                )

            async def start(self) -> None:
                iam = self._owner._iam
                handle = iam._http_authority
                binding = handle._NsHttpClientAuthorityHandle__binding

                def attack() -> None:
                    if not request_started.wait(5):
                        return
                    client = binding._client
                    httpx_client = binding._httpx_client
                    originals = (
                        client.base_url, client._request_base_url,
                        httpx_client._base_url, httpx_client._transport,
                        httpx_client._mounts,
                    )
                    client.base_url = "https://evil.invalid"
                    client._request_base_url = type(client._request_base_url)(
                        "https://evil.invalid/",
                    )
                    httpx_client._base_url = type(httpx_client.base_url)(
                        "https://evil.invalid/",
                    )
                    httpx_client._transport = object()
                    httpx_client._mounts = {}
                    client.base_url, client._request_base_url = originals[:2]
                    httpx_client._base_url, httpx_client._transport, (
                        httpx_client._mounts
                    ) = originals[2:]
                    allow_response.set()

                attacker = threading.Thread(target=attack, daemon=True)
                attacker.start()
                response = await handle.post(
                    "internal/runtime_access_check/",
                    json_data={}, bearer_token="r" * 32,
                    trace_id="operation:toctou", expected_statuses={200},
                )
                attacker.join(5)
                outcomes.append(response.json()["data"])

            async def stop(self) -> None:
                return None

        try:
            with tempfile.TemporaryDirectory() as temporary_directory:
                root = Path(temporary_directory)
                base_url = (
                    f"http://127.0.0.1:{server.server_port}/api/iam/"
                )
                config_path = _write_config(
                    root,
                    _production_config({"iam": {
                        "base_url": base_url,
                        "internal_service_credential": "r" * 32,
                    }}),
                )
                preflight, _ = _controlled_preflight()
                with mock.patch(
                    "ns_runtime.transport.TransportRuntimeService",
                    RequestingService,
                ):
                    self.assertEqual(0, main(
                        environment="test", config_path=config_path,
                        startup_root=root / "runtime", preflight=preflight,
                    ))
        finally:
            allow_response.set()
            server.shutdown()
            server.server_close()
            server_thread.join(5)
        self.assertEqual([{"bound": True}], outcomes)

    def test_main_wires_each_initial_role_to_explicit_safe_logger(self) -> None:
        captured_contexts: list[object] = []
        captured_monitors: list[object] = []
        captured_logical_owners: list[object] = []

        class CapturingService:
            def __init__(
                self,
                *,
                context: object,
                transport_manager: object,
                logger_close: object,
                event_loop_monitor: object,
                logical_connection_owner: object,
            ) -> None:
                from ns_runtime.shutdown import RuntimeShutdownCoordinator

                captured_contexts.append(context)
                captured_monitors.append(event_loop_monitor)
                captured_logical_owners.append(logical_connection_owner)
                self.shutdown_coordinator = RuntimeShutdownCoordinator(
                    context=context,  # type: ignore[arg-type]
                    logger_close=logger_close,  # type: ignore[arg-type]
                    transport_owner=transport_manager,  # type: ignore[arg-type]
                    logical_connection_owner=logical_connection_owner,  # type: ignore[arg-type]
                )
                self.event_loop_monitor = event_loop_monitor

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
                            "ns_runtime.transport.TransportRuntimeService",
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
                        self.assertIs(
                            context,
                            captured_monitors[-1].context,  # type: ignore[attr-defined]
                        )
                        self.assertEqual(
                            "asyncio",
                            captured_monitors[-1].snapshot.implementation.value,  # type: ignore[attr-defined]
                        )
                        self.assertTrue((startup_root / "log").is_dir())
                        from ns_runtime.iam import IamClient

                        self.assertIsInstance(
                            captured_logical_owners[-1]._iam,  # type: ignore[attr-defined]
                            IamClient,
                        )
                        self.assertIsNotNone(context.http_client_owner)  # type: ignore[attr-defined]
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
            [sys.executable, "-m", "ns_runtime.main", "self-check"],
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
            self.assertEqual("", completed.stderr)
            summary = json.loads(completed.stdout.strip())
            self.assertEqual("runtime_shutdown_summary", summary["event"])
            self.assertEqual(
                "self_check_complete",
                summary["shutdown_reason"],
            )
            self.assertEqual(0, summary["task_unfinished_count"])
            self.assertEqual(0, summary["cleanup_failure_count"])

    def test_default_process_entry_stays_running_until_sigterm(self) -> None:
        if importlib.util.find_spec("websockets") is None:
            self.skipTest("websockets is unavailable")
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(SRC_DIR)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            config_path = _write_config(root, {
                "runtime": {
                    "transport": {
                        "listen_host": "127.0.0.1",
                        "listen_port": port,
                    },
                    "state_store": {
                        "backend": "sqlite",
                        "sqlite_path": str(root / "data" / "runtime.sqlite3"),
                    },
                },
            })
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "ns_runtime.main",
                    "--environment",
                    "test",
                    "--config",
                    str(config_path),
                    "--startup-root",
                    str(root / "runtime-root"),
                ],
                cwd=ROOT_DIR,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout = ""
            stderr = ""
            try:
                deadline = time.monotonic() + 10
                listener_ready = False
                while time.monotonic() < deadline and process.poll() is None:
                    with socket.socket(
                        socket.AF_INET,
                        socket.SOCK_STREAM,
                    ) as probe:
                        probe.settimeout(0.05)
                        if probe.connect_ex(("127.0.0.1", port)) == 0:
                            listener_ready = True
                            break
                    time.sleep(0.05)
                self.assertTrue(listener_ready)
                self.assertIsNone(
                    process.poll(),
                    "default module entry exited without a shutdown request",
                )
                process.send_signal(signal.SIGTERM)
                stdout, stderr = process.communicate(timeout=10)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate(timeout=5)

        self.assertEqual(0, process.returncode, stderr)
        summaries = []
        for line in stdout.splitlines():
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if value.get("event") == "runtime_shutdown_summary":
                summaries.append(value)
        self.assertEqual(1, len(summaries), stdout)
        self.assertEqual("sigterm", summaries[0]["shutdown_reason"])

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
