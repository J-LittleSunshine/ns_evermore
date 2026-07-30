# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
from contextlib import nullcontext
import importlib.util
import copy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
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

from ns_common.async_runtime import NsEventLoopSelector, TaskSupervisor
from ns_common.exceptions import (
    NsConfigError,
    NsDependencyError,
    NsRuntimeStartupSecurityError,
    NsRuntimeTransportDisabledError,
    NsStateError,
    NsValidationError,
)
from ns_common.logger import NsLogger, close_ns_loggers
from ns_runtime.main import (
    _MainCompositionResources,
    _run_composed_service,
    _run_composed_service_sync,
    main as _runtime_main,
)
from ns_runtime.service import RuntimeServiceState
from ns_runtime.startup import (
    RuntimeStartupDirectories,
    RuntimeStartupPreflight,
)

runtime_main_module = importlib.import_module("ns_runtime.main")


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"


def main(**values: object) -> int:
    values.setdefault("self_check", True)
    key_read, key_write = os.pipe()
    secrets_read, secrets_write = os.pipe()
    previous_key = os.environ.get("NS_RUNTIME_AUTHORITY_KEY_FD")
    previous_secrets = os.environ.get("NS_RUNTIME_AUTHORITY_SECRETS_FD")
    try:
        os.write(key_write, os.urandom(32))
        os.write(secrets_write, json.dumps({
            "iam_service_credential": "test-only-untrusted",
            "state_password_base64": None,
        }).encode())
    finally:
        os.close(key_write)
        os.close(secrets_write)
    os.environ["NS_RUNTIME_AUTHORITY_KEY_FD"] = str(key_read)
    os.environ["NS_RUNTIME_AUTHORITY_SECRETS_FD"] = str(secrets_read)
    try:
        return _runtime_main(**values)  # type: ignore[arg-type]
    finally:
        for fd in (key_read, secrets_read):
            try:
                os.close(fd)
            except OSError:
                pass
        if previous_key is None:
            os.environ.pop("NS_RUNTIME_AUTHORITY_KEY_FD", None)
        else:
            os.environ["NS_RUNTIME_AUTHORITY_KEY_FD"] = previous_key
        if previous_secrets is None:
            os.environ.pop("NS_RUNTIME_AUTHORITY_SECRETS_FD", None)
        else:
            os.environ["NS_RUNTIME_AUTHORITY_SECRETS_FD"] = previous_secrets


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

    def test_composed_service_retries_cleanup_in_same_event_loop(self) -> None:
        events: list[str] = []

        class Store:
            async def open(self) -> None:
                events.append("store:open")

            async def close(self) -> None:
                events.append("store:close")

        store = Store()

        class Coordinator:
            def __init__(self) -> None:
                self.cleanup_pending = False
                self.cleanup_progress: object = ("initial",)
                self.context = type(
                    "Context",
                    (),
                    {"state_store": store},
                )()

            def install_signal_handlers(self):
                return nullcontext()

            def request_shutdown(self, _reason: object) -> None:
                events.append("shutdown:request")

            async def wait_requested(self) -> None:
                events.append("shutdown:wait")

        class Service:
            def __init__(self) -> None:
                self.shutdown_coordinator = Coordinator()
                self.stop_calls = 0
                self.state = RuntimeServiceState.CREATED

            async def start(self) -> None:
                events.append("service:start")
                self.state = RuntimeServiceState.RUNNING

            async def stop(self) -> None:
                self.stop_calls += 1
                events.append("service:stop")
                if self.stop_calls == 1:
                    self.shutdown_coordinator.cleanup_pending = True
                    raise RuntimeError("close failed once")
                await store.close()
                self.shutdown_coordinator.cleanup_progress = ("complete",)
                self.shutdown_coordinator.cleanup_pending = False
                self.state = RuntimeServiceState.STOPPED

        resources = _MainCompositionResources()
        resources.transport_manager = object()
        resources.adapters = (object(),)
        resources.task_supervisor = object()
        resources.logger = object()
        service = Service()

        asyncio.run(_run_composed_service(
            resources,
            service,  # type: ignore[arg-type]
            state_store=store,
            self_check=True,
        ))

        self.assertEqual(2, service.stop_calls)
        self.assertEqual(1, events.count("store:close"))
        self.assertIsNone(resources.service_lifecycle_owner)
        self.assertIsNone(resources.transport_manager)
        self.assertEqual((), resources.adapters)
        self.assertIsNone(resources.task_supervisor)
        self.assertIsNone(resources.logger)

    def test_composed_service_bounds_cleanup_without_progress(self) -> None:
        operation_failure = RuntimeError("runtime-operation-identity")

        class Store:
            def __init__(self) -> None:
                self.close_calls = 0

            async def open(self) -> None:
                return None

            async def close(self) -> None:
                self.close_calls += 1

        class Coordinator:
            cleanup_pending = True
            cleanup_progress = ("unchanged-owner",)

            def __init__(self, state_store: object) -> None:
                self.context = type(
                    "Context",
                    (),
                    {"state_store": state_store},
                )()

            def install_signal_handlers(self):
                return nullcontext()

            async def wait_requested(self) -> None:
                raise operation_failure

        class Service:
            def __init__(self, state_store: object) -> None:
                self.shutdown_coordinator = Coordinator(state_store)
                self.stop_calls = 0
                self.state = RuntimeServiceState.CREATED
                self.block_cleanup = True

            async def start(self) -> None:
                self.state = RuntimeServiceState.RUNNING
                return None

            async def stop(self) -> None:
                self.stop_calls += 1
                if not self.block_cleanup:
                    await store.close()
                    self.shutdown_coordinator.cleanup_pending = False
                    self.shutdown_coordinator.cleanup_progress = ("complete",)
                    self.state = RuntimeServiceState.STOPPED
                    return
                self.state = RuntimeServiceState.FAILED
                raise RuntimeError("persistent cleanup failure")

        resources = _MainCompositionResources()
        resources.transport_manager = object()
        store = Store()
        service = Service(store)
        with self.assertRaises(NsStateError) as raised:
            _run_composed_service_sync(
                resources,
                service,  # type: ignore[arg-type]
                state_store=store,
                self_check=False,
            )

        self.assertEqual(
            "cleanup_pending_no_progress",
            raised.exception.details["reason"],
        )
        self.assertIs(operation_failure, raised.exception.__cause__)
        self.assertEqual(3, service.stop_calls)
        self.assertEqual(0, store.close_calls)
        self.assertIsNotNone(resources.service_lifecycle_owner)
        self.assertIs(
            resources.service_lifecycle_owner,
            raised.exception.cleanup_owner,
        )
        self.assertTrue(raised.exception.details["cleanup_pending"])
        self.assertFalse(raised.exception.details["service_stopped"])
        self.assertTrue(
            raised.exception.details["service_lifecycle_owner_active"],
        )
        owner = raised.exception.cleanup_owner
        self.assertIs(raised.exception, owner.run_failure)
        self.assertFalse(owner.original_loop.is_closed())
        self.assertIsNotNone(owner.service_cleanup_lease)
        service.block_cleanup = False
        owner.close()
        self.assertEqual(4, service.stop_calls)
        self.assertEqual(1, store.close_calls)
        self.assertTrue(owner.original_loop.is_closed())
        self.assertIsNone(owner.service_cleanup_lease)
        self.assertIsNone(resources.service_lifecycle_owner)

    def test_cleanup_owner_resumes_only_pending_phase_on_same_loop(self) -> None:
        events: list[str] = []

        class Store:
            def __init__(self) -> None:
                self.closed = False

            async def open(self) -> None:
                events.append("store:open")

            async def close(self) -> None:
                if not self.closed:
                    self.closed = True
                    events.append("store:close")
                    events.append("broker-graph:close")

        store = Store()

        class Manager:
            def __init__(self) -> None:
                self.closed = False

            async def close(self) -> None:
                if not self.closed:
                    self.closed = True
                    events.append("transport:close")

        class Supervisor:
            def __init__(self) -> None:
                self.closed = False

            async def shutdown(self) -> None:
                if not self.closed:
                    self.closed = True
                    events.append("tasks:close")

        class Logger:
            def __init__(self) -> None:
                self.closed = False

            def close(self) -> None:
                if not self.closed:
                    self.closed = True
                    events.append("logger:close")

        class Broker:
            def close(self) -> None:
                events.append("broker-outer:close")

        manager = Manager()
        supervisor = Supervisor()
        logger = Logger()

        class Coordinator:
            def __init__(self) -> None:
                self.cleanup_pending = False
                self.cleanup_progress: object = ("not-started",)
                self.context = type(
                    "Context",
                    (),
                    {"state_store": store},
                )()

            def install_signal_handlers(self):
                return nullcontext()

            def request_shutdown(self, _reason: object) -> None:
                return None

            async def wait_requested(self) -> None:
                return None

        class Service:
            def __init__(self) -> None:
                self.shutdown_coordinator = Coordinator()
                self.state = RuntimeServiceState.CREATED
                self.block_transport_close = True
                self.tasks_closed = False
                self.store_closed = False
                self.logger_closed = False
                self.stop_calls = 0

            async def start(self) -> None:
                self.state = RuntimeServiceState.RUNNING

            async def stop(self) -> None:
                self.stop_calls += 1
                if not self.tasks_closed:
                    await supervisor.shutdown()
                    self.tasks_closed = True
                if not self.store_closed:
                    await store.close()
                    self.store_closed = True
                if not self.logger_closed:
                    logger.close()
                    self.logger_closed = True
                if self.block_transport_close:
                    self.state = RuntimeServiceState.FAILED
                    self.shutdown_coordinator.cleanup_pending = True
                    self.shutdown_coordinator.cleanup_progress = (
                        "tasks-closed",
                        "transport-pending",
                    )
                    raise RuntimeError("transport close remains blocked")
                await manager.close()
                self.shutdown_coordinator.cleanup_progress = ("complete",)
                self.shutdown_coordinator.cleanup_pending = False
                self.state = RuntimeServiceState.STOPPED

        resources = _MainCompositionResources()
        resources.transport_manager = manager
        resources.task_supervisor = supervisor
        resources.logger = logger
        resources.authority_broker = Broker()
        service = Service()

        with self.assertRaises(NsStateError) as raised:
            _run_composed_service_sync(
                resources,
                service,  # type: ignore[arg-type]
                state_store=store,
                self_check=True,
            )
        owner = raised.exception.cleanup_owner
        self.assertIs(owner, resources.service_lifecycle_owner)
        original_loop = owner.original_loop
        lease = owner.service_cleanup_lease
        self.assertFalse(original_loop.is_closed())
        self.assertIsNotNone(lease)
        self.assertIs(raised.exception, owner.run_failure)

        with self.assertRaises(NsStateError) as wrong_loop:
            asyncio.run(lease.close())
        self.assertEqual(
            "service_cleanup_loop_mismatch",
            wrong_loop.exception.details["reason"],
        )
        self.assertFalse(original_loop.is_closed())
        self.assertEqual(4, service.stop_calls)

        service.block_transport_close = False
        owner.close()
        resources.close()
        resources.close()

        self.assertEqual(1, events.count("tasks:close"))
        self.assertEqual(1, events.count("transport:close"))
        self.assertEqual(1, events.count("store:close"))
        self.assertEqual(1, events.count("broker-graph:close"))
        self.assertEqual(1, events.count("logger:close"))
        self.assertEqual(0, events.count("broker-outer:close"))
        self.assertEqual(5, service.stop_calls)
        self.assertEqual(RuntimeServiceState.STOPPED, service.state)
        self.assertTrue(original_loop.is_closed())
        self.assertIsNone(owner.service_cleanup_lease)
        self.assertIsNone(resources.service_lifecycle_owner)

    def test_process_cleanup_failure_keeps_service_incomplete_cause_chain(
        self,
    ) -> None:
        for exception_type in (KeyboardInterrupt, SystemExit):
            with self.subTest(exception_type=exception_type.__name__):
                operation_failure = RuntimeError("operation-identity")
                process_failure = exception_type()

                class Store:
                    async def open(self) -> None:
                        return None

                    async def close(self) -> None:
                        return None

                store = Store()

                class Coordinator:
                    cleanup_pending = True
                    cleanup_progress = ("cleanup-pending",)

                    def __init__(self) -> None:
                        self.context = type(
                            "Context",
                            (),
                            {"state_store": store},
                        )()

                    def install_signal_handlers(self):
                        return nullcontext()

                    async def wait_requested(self) -> None:
                        raise operation_failure

                class Service:
                    def __init__(self) -> None:
                        self.shutdown_coordinator = Coordinator()
                        self.state = RuntimeServiceState.CREATED
                        self.block_cleanup = True
                        self.stop_calls = 0

                    async def start(self) -> None:
                        self.state = RuntimeServiceState.RUNNING

                    async def stop(self) -> None:
                        self.stop_calls += 1
                        if self.block_cleanup:
                            self.state = RuntimeServiceState.FAILED
                            raise process_failure
                        self.shutdown_coordinator.cleanup_pending = False
                        self.shutdown_coordinator.cleanup_progress = (
                            "complete",
                        )
                        self.state = RuntimeServiceState.STOPPED

                resources = _MainCompositionResources()
                resources.transport_manager = object()
                service = Service()
                with self.assertRaises(exception_type) as raised:
                    _run_composed_service_sync(
                        resources,
                        service,  # type: ignore[arg-type]
                        state_store=store,
                        self_check=False,
                    )

                self.assertIs(process_failure, raised.exception)
                incomplete = raised.exception.__cause__
                self.assertIsInstance(incomplete, NsStateError)
                self.assertEqual(
                    "cleanup_pending_no_progress",
                    incomplete.details["reason"],
                )
                self.assertIs(operation_failure, incomplete.__cause__)
                owner = incomplete.cleanup_owner
                self.assertIs(owner, resources.service_lifecycle_owner)
                self.assertIs(process_failure, owner.run_failure)
                self.assertFalse(owner.original_loop.is_closed())
                self.assertIsNotNone(owner.service_cleanup_lease)
                self.assertNotIn(
                    "operation-identity",
                    repr(incomplete),
                )

                service.block_cleanup = False
                owner.close()
                self.assertEqual(4, service.stop_calls)
                self.assertEqual(RuntimeServiceState.STOPPED, service.state)
                self.assertTrue(owner.original_loop.is_closed())
                self.assertIsNone(owner.service_cleanup_lease)
                self.assertIsNone(resources.service_lifecycle_owner)

    def test_start_failure_does_not_duplicate_service_owned_cleanup(self) -> None:
        start_failure = RuntimeError("service start identity")
        events: list[str] = []

        class Store:
            async def open(self) -> None:
                events.append("store:open")

            async def close(self) -> None:
                events.append("store:close")
                events.append("broker-graph:close")

        store = Store()

        class Manager:
            async def close(self) -> None:
                events.append("manager:close")

        class Supervisor:
            async def shutdown(self) -> None:
                events.append("supervisor:shutdown")

        class Logger:
            def close(self) -> None:
                events.append("logger:close")

        class Broker:
            def close(self) -> None:
                events.append("broker-outer:close")

        manager = Manager()
        supervisor = Supervisor()
        logger = Logger()

        class Coordinator:
            def __init__(self) -> None:
                self.cleanup_pending = False
                self.cleanup_progress: object = ("not-started",)
                self.context = type(
                    "Context",
                    (),
                    {"state_store": store},
                )()

            def install_signal_handlers(self):
                return nullcontext()

        class Service:
            def __init__(self) -> None:
                self.shutdown_coordinator = Coordinator()
                self.state = RuntimeServiceState.CREATED

            async def start(self) -> None:
                self.state = RuntimeServiceState.FAILED
                raise start_failure

            async def stop(self) -> None:
                await manager.close()
                await supervisor.shutdown()
                await store.close()
                logger.close()
                self.shutdown_coordinator.cleanup_progress = ("complete",)
                self.state = RuntimeServiceState.STOPPED

        resources = _MainCompositionResources()
        resources.transport_manager = manager
        resources.task_supervisor = supervisor
        resources.logger = logger
        resources.authority_broker = Broker()
        service = Service()

        with self.assertRaises(RuntimeError) as raised:
            asyncio.run(_run_composed_service(
                resources,
                service,  # type: ignore[arg-type]
                state_store=store,
                self_check=False,
            ))

        self.assertIs(start_failure, raised.exception)
        resources.close()
        self.assertEqual(1, events.count("manager:close"))
        self.assertEqual(1, events.count("supervisor:shutdown"))
        self.assertEqual(1, events.count("store:close"))
        self.assertEqual(1, events.count("broker-graph:close"))
        self.assertEqual(0, events.count("broker-outer:close"))
        self.assertEqual(1, events.count("logger:close"))
        self.assertIsNone(resources.service_lifecycle_owner)

    def test_composed_store_open_failure_closes_every_untransferred_resource(
        self,
    ) -> None:
        open_failure = RuntimeError("state store open failed")
        events: list[str] = []

        class Store:
            async def open(self) -> None:
                events.append("store:open")
                raise open_failure

            async def close(self) -> None:
                events.append("store:close")

        class Manager:
            async def close(self) -> None:
                events.append("manager:close")

        class Supervisor:
            async def shutdown(self) -> None:
                events.append("supervisor:shutdown")

        class Logger:
            def close(self) -> None:
                events.append("logger:close")

        class Broker:
            def close(self) -> None:
                events.append("broker:close")

        class Coordinator:
            def install_signal_handlers(self):
                return nullcontext()

        class CreatedService:
            shutdown_coordinator = Coordinator()

            async def start(self) -> None:
                events.append("service:start")

            async def stop(self) -> None:
                events.append("service:stop")
                raise AssertionError("CREATED.stop must not be called")

        resources = _MainCompositionResources()
        resources.transport_manager = Manager()
        resources.task_supervisor = Supervisor()
        resources.logger = Logger()
        resources.authority_broker = Broker()
        with self.assertRaises(RuntimeError) as raised:
            asyncio.run(_run_composed_service(
                resources,
                CreatedService(),  # type: ignore[arg-type]
                state_store=Store(),
                self_check=True,
            ))
        self.assertIs(open_failure, raised.exception)
        resources.close()
        resources.close()
        self.assertEqual(
            [
                "store:open",
                "store:close",
                "manager:close",
                "supervisor:shutdown",
                "broker:close",
                "logger:close",
            ],
            events,
        )

    @unittest.skip(
        "requires the deployment production authority private key",
    )
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
                from dataclasses import replace
                from ns_common.http_client import (
                    NsAsyncHttpClient,
                    NsHttpClientOwner,
                )
                from ns_runtime.authority_broker import (
                    BrokerRepositoryRole,
                    ProductionIamAuthorityProxy,
                )

                self.assert_no_http = all(
                    not hasattr(iam, name)
                    for name in (
                        "_http_authority", "_client", "_httpx_client",
                        "_transport", "_mounts", "_service_credential",
                    )
                )
                checks.append(self.assert_no_http)
                checks.append(type(iam) is ProductionIamAuthorityProxy)
                handle = iam._handle
                checks.append(handle.role is BrokerRepositoryRole.IAM)
                checks.append(handle.verify(
                    iam._channel.public_key,
                    instance_id=iam._channel.instance_id,
                ))
                with test_case.assertRaises(NsValidationError):
                    copy.copy(handle)
                checks.append(not replace(
                    handle,
                    role=BrokerRepositoryRole.SCHEDULER,
                ).verify(
                    iam._channel.public_key,
                    instance_id=iam._channel.instance_id,
                ))
                with test_case.assertRaises(NsValidationError):
                    ProductionIamAuthorityProxy()
                forged = object.__new__(ProductionIamAuthorityProxy)
                checks.append(not forged._is_production_adapter())
                owner = NsHttpClientOwner()
                client = owner.create(
                    name="ordinary",
                    base_url="https://evil.invalid/",
                )
                try:
                    checks.append(not hasattr(owner, "_create_authority_handle"))
                    checks.append(not hasattr(client, "_authority_handle"))
                    original = NsAsyncHttpClient.post
                    NsAsyncHttpClient.post = mock.AsyncMock()  # type: ignore[method-assign]
                    checks.append(iam._is_production_adapter())
                    NsAsyncHttpClient.post = original
                finally:
                    await owner.aclose()

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

    @unittest.skip(
        "requires the deployment production authority private key",
    )
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
                from datetime import datetime, timezone

                data = {
                    "allowed": True,
                    "reason": "broker_transport_bound",
                    "permission_version": "version-1",
                    "decided_at": datetime.now(timezone.utc).isoformat().replace(
                        "+00:00", "Z",
                    ),
                    "refresh_required": False,
                }
                body = json.dumps({
                    "success": True,
                    "code": "OK",
                    "error": None,
                    "message": "ok",
                    "data": data,
                    "request_id": "request-broker",
                }).encode()
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
                from ns_common.http_client import NsAsyncHttpClient
                from ns_common.iam import IamAccessCheckRequest, IamTargetContext

                def attack() -> None:
                    if not request_started.wait(5):
                        return
                    originals = (
                        NsAsyncHttpClient.request,
                        NsAsyncHttpClient.post,
                    )
                    NsAsyncHttpClient.request = mock.AsyncMock()  # type: ignore[method-assign]
                    NsAsyncHttpClient.post = mock.AsyncMock()  # type: ignore[method-assign]
                    NsAsyncHttpClient.request, NsAsyncHttpClient.post = originals
                    allow_response.set()

                attacker = threading.Thread(target=attack, daemon=True)
                attacker.start()
                response = await iam.access_check_signed(
                    IamAccessCheckRequest(
                        identity="identity-1",
                        tenant_id="tenant-1",
                        permission_snapshot_ref="snapshot-1",
                        permission_version="version-1",
                        message_type="message.test",
                        target=IamTargetContext(
                            kind="session",
                            tenant_id="tenant-1",
                        ),
                    ),
                )
                attacker.join(5)
                outcomes.append((
                    response.result.reason,
                    response.authority.verify(
                        public_key=iam._channel.public_key,
                        broker_instance_id=iam._channel.instance_id,
                        operation="runtime_access_check",
                        request_fingerprint=response.authority.request_fingerprint,
                        now=iam._clock.utc_now(),
                    ),
                ))

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
        self.assertEqual([("broker_transport_bound", True)], outcomes)

    @unittest.skip(
        "requires the deployment production authority private key",
    )
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
                        self.assertIsNone(context.http_client_owner)  # type: ignore[attr-defined]
                        self.assertIsNotNone(context.state_store)  # type: ignore[attr-defined]
        finally:
            close_ns_loggers()

    @unittest.skip(
        "requires the deployment production authority private key",
    )
    def test_main_succeeds_with_runtime_dependencies_or_fails_closed(self) -> None:
        if importlib.util.find_spec("websockets") is None:
            with self.assertRaises(NsDependencyError) as context:
                main()
            self.assertEqual("websockets", context.exception.details["dependency"])
            return

        self.assertEqual(0, main())

    @unittest.skip(
        "requires the deployment production authority private key",
    )
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

    @unittest.skip(
        "requires the deployment production authority private key",
    )
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

    def test_every_prelaunch_failure_closes_pending_bootstrap_and_resources(
        self,
    ) -> None:
        phases = (
            "config",
            "preflight",
            "tls",
            "logger",
            "adapter_registry",
            "transport_manager",
            "broker_launch",
        )
        for phase in phases:
            with self.subTest(phase=phase):
                bootstrap_close_calls = 0
                bootstrap_launch_calls = 0
                supervisors: list[TaskSupervisor] = []
                loggers: list[logging.Logger] = []
                managers: list[object] = []
                failure = RuntimeError(f"{phase} failure")

                class FakeBootstrap:
                    def launch(self, *, config, clock):
                        nonlocal bootstrap_launch_calls
                        del config, clock
                        bootstrap_launch_calls += 1
                        raise failure

                    def close(self) -> None:
                        nonlocal bootstrap_close_calls
                        bootstrap_close_calls += 1

                class TrackingSupervisor(TaskSupervisor):
                    def __init__(self, **values):
                        super().__init__(**values)
                        supervisors.append(self)

                class TrackingLogger(logging.Logger):
                    def __init__(self) -> None:
                        super().__init__("runtime-test-tracking")
                        self.close_calls = 0
                        loggers.append(self)

                    def close(self) -> None:
                        self.close_calls += 1

                class TrackingManager:
                    def __init__(self) -> None:
                        self.close_calls = 0
                        managers.append(self)

                    async def close(self) -> None:
                        self.close_calls += 1

                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    raw_config: dict[str, object] = {}
                    if phase == "tls":
                        raw_config = {
                            "runtime": {
                                "transport": {
                                    "websocket_tcp": {
                                        "tls_enabled": True,
                                    },
                                },
                            },
                        }
                    config_path = _write_config(root, raw_config)
                    startup_directories = RuntimeStartupDirectories.for_root(
                        root / "runtime-root",
                    )
                    controlled, _ = _controlled_preflight()
                    if phase == "config":
                        controlled = mock.Mock()
                        controlled.resolve_environment.return_value = "local"
                        controlled.load_config_snapshot.side_effect = failure
                    elif phase == "preflight":
                        controlled.prepare = mock.Mock(side_effect=failure)

                    fake_logger = TrackingLogger()
                    fake_manager = TrackingManager()
                    logger_patch = (
                        mock.patch(
                            "ns_common.logger.NsLogger",
                            side_effect=failure,
                        )
                        if phase == "logger"
                        else mock.patch(
                            "ns_common.logger.NsLogger",
                            return_value=fake_logger,
                        )
                    )
                    registry_patch = (
                        mock.patch(
                            "ns_runtime.transport.TransportAdapterRegistry.default",
                            side_effect=failure,
                        )
                        if phase == "adapter_registry"
                        else mock.patch(
                            "ns_runtime.transport.TransportAdapterRegistry.default",
                            wraps=__import__(
                                "ns_runtime.transport",
                                fromlist=["TransportAdapterRegistry"],
                            ).TransportAdapterRegistry.default,
                        )
                    )
                    manager_patch = (
                        mock.patch(
                            "ns_runtime.transport.TransportManager",
                            side_effect=failure,
                        )
                        if phase == "transport_manager"
                        else mock.patch(
                            "ns_runtime.transport.TransportManager",
                            return_value=fake_manager,
                        )
                    )
                    with (
                        mock.patch(
                            "ns_runtime.authority_bootstrap."
                            "load_inherited_authority_bootstrap",
                            return_value=FakeBootstrap(),
                        ),
                        mock.patch(
                            "ns_common.async_runtime.TaskSupervisor",
                            TrackingSupervisor,
                        ),
                        logger_patch,
                        registry_patch,
                        manager_patch,
                    ):
                        with self.assertRaises(BaseException) as raised:
                            _runtime_main(
                                environment="local",
                                config_path=config_path,
                                startup_directories=startup_directories,
                                preflight=controlled,
                                self_check=True,
                            )

                if phase != "tls":
                    self.assertIs(failure, raised.exception)
                else:
                    self.assertIsInstance(
                        raised.exception,
                        NsRuntimeStartupSecurityError,
                    )
                self.assertEqual(1, bootstrap_close_calls)
                self.assertEqual(
                    1 if phase == "broker_launch" else 0,
                    bootstrap_launch_calls,
                )
                if phase not in {"config"}:
                    self.assertEqual(1, len(supervisors))
                    self.assertEqual("closed", supervisors[0].state.value)
                if phase in {
                    "adapter_registry",
                    "transport_manager",
                    "broker_launch",
                }:
                    self.assertEqual(1, fake_logger.close_calls)
                if phase == "broker_launch":
                    self.assertEqual(1, fake_manager.close_calls)

    def test_composition_close_retries_only_resources_that_failed(self) -> None:
        class AsyncResource:
            def __init__(self, *, fail_once: bool) -> None:
                self.fail_once = fail_once
                self.calls = 0

            async def close(self) -> None:
                self.calls += 1
                if self.fail_once and self.calls == 1:
                    raise RuntimeError("async close failed once")

            async def shutdown(self) -> None:
                await self.close()

        class SyncResource:
            def __init__(self, *, fail_once: bool) -> None:
                self.fail_once = fail_once
                self.calls = 0

            def close(self) -> None:
                self.calls += 1
                if self.fail_once and self.calls == 1:
                    raise RuntimeError("sync close failed once")

        manager = AsyncResource(fail_once=True)
        supervisor = AsyncResource(fail_once=False)
        broker = SyncResource(fail_once=False)
        logger = SyncResource(fail_once=True)
        resources = _MainCompositionResources()
        resources.transport_manager = manager
        resources.adapters = (object(),)
        resources.task_supervisor = supervisor
        resources.authority_broker = broker
        resources.logger = logger

        with self.assertRaises(RuntimeError):
            resources.close()
        self.assertEqual(1, manager.calls)
        self.assertEqual(1, supervisor.calls)
        self.assertEqual(1, broker.calls)
        self.assertEqual(1, logger.calls)
        self.assertIs(resources.transport_manager, manager)
        self.assertEqual((object,), tuple(type(item) for item in resources.adapters))
        self.assertIsNone(resources.task_supervisor)
        self.assertIsNone(resources.authority_broker)
        self.assertIs(resources.logger, logger)

        resources.close()
        self.assertEqual(2, manager.calls)
        self.assertEqual(1, supervisor.calls)
        self.assertEqual(1, broker.calls)
        self.assertEqual(2, logger.calls)
        self.assertIsNone(resources.transport_manager)
        self.assertEqual((), resources.adapters)
        self.assertIsNone(resources.logger)

    def test_main_retries_only_incomplete_composition_resources(
        self,
    ) -> None:
        operation_failure = RuntimeError("runtime operation failed")
        resources_seen: list[_MainCompositionResources] = []

        class AsyncResource:
            def __init__(self, *, fail_once: bool) -> None:
                self.fail_once = fail_once
                self.calls = 0

            async def close(self) -> None:
                self.calls += 1
                if self.fail_once and self.calls == 1:
                    raise RuntimeError("async cleanup failed")

            async def shutdown(self) -> None:
                await self.close()

        class SyncResource:
            def __init__(self, *, fail_once: bool) -> None:
                self.fail_once = fail_once
                self.calls = 0

            def close(self) -> None:
                self.calls += 1
                if self.fail_once and self.calls == 1:
                    raise RuntimeError("sync cleanup failed")

        manager = AsyncResource(fail_once=True)
        supervisor = AsyncResource(fail_once=False)
        broker = SyncResource(fail_once=True)
        logger = SyncResource(fail_once=True)

        def fail_after_composition(**values: object) -> int:
            resources = values["resources"]
            self.assertIsInstance(resources, _MainCompositionResources)
            resources_seen.append(resources)
            resources.transport_manager = manager
            resources.adapters = (object(),)
            resources.task_supervisor = supervisor
            resources.authority_broker = broker
            resources.logger = logger
            raise operation_failure

        with mock.patch(
            "ns_runtime.main._compose_runtime_main",
            side_effect=fail_after_composition,
        ):
            with self.assertRaises(RuntimeError) as raised:
                self._main_after_bootstrap_for_test()

        self.assertIs(operation_failure, raised.exception)
        self.assertEqual(2, manager.calls)
        self.assertEqual(1, supervisor.calls)
        self.assertEqual(2, broker.calls)
        self.assertEqual(2, logger.calls)
        self.assertEqual(1, len(resources_seen))
        self.assertFalse(resources_seen[0].incomplete)

    def test_main_composition_no_progress_overrides_operation_failure(
        self,
    ) -> None:
        operation_failure = RuntimeError("operation identity")
        resources_seen: list[_MainCompositionResources] = []

        class StubbornManager:
            def __init__(self) -> None:
                self.calls = 0

            async def close(self) -> None:
                self.calls += 1
                raise RuntimeError("sensitive manager cleanup text")

        class SyncResource:
            def __init__(self) -> None:
                self.calls = 0

            def close(self) -> None:
                self.calls += 1

        manager = StubbornManager()
        broker = SyncResource()
        logger = SyncResource()

        def fail_after_composition(**values: object) -> int:
            resources = values["resources"]
            self.assertIsInstance(resources, _MainCompositionResources)
            resources_seen.append(resources)
            resources.transport_manager = manager
            resources.authority_broker = broker
            resources.logger = logger
            raise operation_failure

        with mock.patch(
            "ns_runtime.main._compose_runtime_main",
            side_effect=fail_after_composition,
        ):
            with self.assertRaises(NsStateError) as raised:
                self._main_after_bootstrap_for_test()

        failure = raised.exception
        self.assertEqual(
            "runtime_composition_cleanup_incomplete",
            failure.details["reason"],
        )
        self.assertIs(operation_failure, failure.__cause__)
        self.assertIs(resources_seen[0], failure.cleanup_owner)
        self.assertEqual(4, manager.calls)
        self.assertEqual(1, broker.calls)
        self.assertEqual(1, logger.calls)
        self.assertNotIn("sensitive manager cleanup text", repr(failure))
        self.assertEqual(
            {
                "pending_adapters": 0,
                "transport_manager_owned": True,
                "task_supervisor_owned": False,
                "logger_owned": False,
                "authority_broker_owned": False,
                "service_lifecycle_owner_active": False,
            },
            failure.cleanup_owner.pending_facts(),
        )

    def test_composition_close_continues_after_process_level_failure(self) -> None:
        calls: list[str] = []
        interrupt = KeyboardInterrupt("manager close interrupted")

        class Manager:
            async def close(self) -> None:
                calls.append("manager")
                raise interrupt

        class Supervisor:
            async def shutdown(self) -> None:
                calls.append("supervisor")

        class Broker:
            def close(self) -> None:
                calls.append("broker")

        class Logger:
            def close(self) -> None:
                calls.append("logger")

        resources = _MainCompositionResources()
        resources.transport_manager = Manager()
        resources.task_supervisor = Supervisor()
        resources.authority_broker = Broker()
        resources.logger = Logger()

        with self.assertRaises(KeyboardInterrupt) as raised:
            resources.close()
        self.assertIs(interrupt, raised.exception)
        self.assertEqual(
            ["manager", "supervisor", "broker", "logger"],
            calls,
        )
        self.assertIsNotNone(resources.transport_manager)
        self.assertIsNone(resources.task_supervisor)
        self.assertIsNone(resources.authority_broker)
        self.assertIsNone(resources.logger)

    def test_main_retries_authority_bootstrap_after_first_close_failure(
        self,
    ) -> None:
        operation_failure = RuntimeError("ordinary operation")

        class FakeBootstrap:
            def __init__(self) -> None:
                self.close_calls = 0
                self.incomplete = True

            @property
            def cleanup_progress(self) -> tuple[bool]:
                return (self.incomplete,)

            def pending_facts(self) -> dict[str, object]:
                return {"process_owned": self.incomplete}

            def close(self) -> None:
                self.close_calls += 1
                if self.close_calls == 1:
                    raise RuntimeError("stubborn process")
                self.incomplete = False

        bootstrap = FakeBootstrap()
        preflight = mock.Mock()
        preflight.resolve_environment.return_value = "local"
        preflight.load_config_snapshot.side_effect = operation_failure
        with mock.patch(
            "ns_runtime.authority_bootstrap."
            "load_inherited_authority_bootstrap",
            return_value=bootstrap,
        ):
            with self.assertRaises(RuntimeError) as raised:
                _runtime_main(
                    environment="local",
                    config_path="unused.json",
                    preflight=preflight,
                )

        self.assertIs(operation_failure, raised.exception)
        self.assertEqual(2, bootstrap.close_calls)
        self.assertFalse(bootstrap.incomplete)

    def test_prelaunch_baseexceptions_preserve_identity_and_close_bootstrap(
        self,
    ) -> None:
        failures = (
            RuntimeError("ordinary"),
            asyncio.CancelledError("cancelled"),
            KeyboardInterrupt("interrupt"),
            SystemExit(19),
        )
        for failure in failures:
            with self.subTest(failure_type=type(failure).__name__):
                close_calls = 0

                class FakeBootstrap:
                    def close(self) -> None:
                        nonlocal close_calls
                        close_calls += 1

                preflight = mock.Mock()
                preflight.resolve_environment.return_value = "local"
                preflight.load_config_snapshot.side_effect = failure
                with mock.patch(
                    "ns_runtime.authority_bootstrap."
                    "load_inherited_authority_bootstrap",
                    return_value=FakeBootstrap(),
                ):
                    with self.assertRaises(BaseException) as raised:
                        _runtime_main(
                            environment="local",
                            config_path="unused.json",
                            preflight=preflight,
                        )
                self.assertIs(failure, raised.exception)
                self.assertEqual(1, close_calls)

    def test_process_level_cleanup_preserves_incomplete_and_operation_chain(
        self,
    ) -> None:
        for exception_type in (KeyboardInterrupt, SystemExit):
            with self.subTest(exception_type=exception_type.__name__):
                operation_failure = RuntimeError("ordinary-operation-identity")
                cleanup_failure = exception_type()
                close_calls = 0

                class FakeBootstrap:
                    incomplete = True
                    cleanup_progress = ("cleanup-pending",)

                    def pending_facts(self) -> dict[str, object]:
                        return {
                            "process_owned": True,
                            "process_alive": True,
                            "credential": "private-owner-diagnostic",
                        }

                    def close(self) -> None:
                        nonlocal close_calls
                        close_calls += 1
                        raise cleanup_failure

                bootstrap = FakeBootstrap()
                preflight = mock.Mock()
                preflight.resolve_environment.return_value = "local"
                preflight.load_config_snapshot.side_effect = operation_failure
                with mock.patch(
                    "ns_runtime.authority_bootstrap."
                    "load_inherited_authority_bootstrap",
                    return_value=bootstrap,
                ):
                    with self.assertRaises(exception_type) as raised:
                        _runtime_main(
                            environment="local",
                            config_path="unused.json",
                            preflight=preflight,
                        )
                self.assertIs(cleanup_failure, raised.exception)
                self.assertEqual(3, close_calls)
                incomplete = raised.exception.__cause__
                self.assertIsInstance(incomplete, NsStateError)
                self.assertEqual(
                    "authority_bootstrap_cleanup_incomplete",
                    incomplete.details["reason"],
                )
                self.assertIs(operation_failure, incomplete.__cause__)
                self.assertIs(bootstrap, incomplete.cleanup_owner)
                self.assertTrue(incomplete.details["process_owned"])
                self.assertTrue(incomplete.details["process_alive"])
                self.assertNotIn(
                    "private-owner-diagnostic",
                    repr(incomplete),
                )

    def test_authority_cleanup_no_progress_overrides_operation_failure(
        self,
    ) -> None:
        operation_failure = RuntimeError("ordinary operation")

        class FakeBootstrap:
            incomplete = True
            cleanup_progress = ("stubborn-process",)

            def __init__(self) -> None:
                self.close_calls = 0

            def pending_facts(self) -> dict[str, object]:
                return {
                    "process_owned": True,
                    "process_alive": True,
                }

            def close(self) -> None:
                self.close_calls += 1
                raise RuntimeError("private process cleanup failure")

        bootstrap = FakeBootstrap()
        preflight = mock.Mock()
        preflight.resolve_environment.return_value = "local"
        preflight.load_config_snapshot.side_effect = operation_failure
        with mock.patch(
            "ns_runtime.authority_bootstrap."
            "load_inherited_authority_bootstrap",
            return_value=bootstrap,
        ):
            with self.assertRaises(NsStateError) as raised:
                _runtime_main(
                    environment="local",
                    config_path="unused.json",
                    preflight=preflight,
                )

        failure = raised.exception
        self.assertEqual(
            "authority_bootstrap_cleanup_incomplete",
            failure.details["reason"],
        )
        self.assertIs(operation_failure, failure.__cause__)
        self.assertIs(bootstrap, failure.cleanup_owner)
        self.assertEqual(3, bootstrap.close_calls)
        self.assertEqual(True, failure.details["process_owned"])
        self.assertEqual(True, failure.details["process_alive"])
        self.assertNotIn("private process cleanup failure", repr(failure))

    def test_post_launch_composition_failure_closes_all_authority_resources(
        self,
    ) -> None:
        resource_closed = {
            "broker": False,
            "attestor": False,
            "pipe": False,
            "physical_domain_lease": False,
        }

        class FakeRepositories:
            admission = object()
            scheduler = object()
            payload = object()
            registry = object()
            audit = object()

        class FakeBroker:
            state_store = object()
            iam = object()
            repositories = FakeRepositories()

            def close(self) -> None:
                for resource in resource_closed:
                    resource_closed[resource] = True

        broker = FakeBroker()

        class FakeBootstrap:
            launch_calls = 0
            close_calls = 0

            def launch(self, *, config, clock) -> FakeBroker:
                del config, clock
                self.launch_calls += 1
                return broker

            def close(self) -> None:
                self.close_calls += 1

        bootstrap = FakeBootstrap()
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            config_path = _write_config(temporary_root, {})
            startup_root = temporary_root / "runtime-root"
            preflight, _ = _controlled_preflight()

            with mock.patch(
                "ns_runtime.authority_bootstrap."
                "load_inherited_authority_bootstrap",
                return_value=bootstrap,
            ):
                with self.assertRaises(NsValidationError):
                    main(
                        environment="local",
                        config_path=config_path,
                        startup_directories=(
                            RuntimeStartupDirectories.for_root(startup_root)
                        ),
                        preflight=preflight,
                    )

        self.assertEqual(1, bootstrap.launch_calls)
        self.assertEqual(1, bootstrap.close_calls)
        self.assertEqual(
            {
                "broker": True,
                "attestor": True,
                "pipe": True,
                "physical_domain_lease": True,
            },
            resource_closed,
        )

    def _main_after_bootstrap_for_test(self) -> int:
        return runtime_main_module._main_after_authority_bootstrap(
            authority_bootstrap=object(),
            environment=None,
            config_path=None,
            startup_root=None,
            startup_directories=None,
            preflight=None,
            transport_ssl_context=None,
            self_check=False,
        )

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
