# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import subprocess
import sys
import unittest

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import (
    NsRuntimeTransportDisabledError,
    NsValidationError,
)
from ns_common.time import SystemClock
from ns_runtime.transport import (
    TRANSPORT_ADAPTER_NAMES,
    TransportAdapterBuildContext,
    TransportAdapterRegistry,
    TransportIdentityFactory,
    WebSocketTcpAdapterOptions,
)


class TransportAdapterRegistryTestCase(unittest.IsolatedAsyncioTestCase):
    def _context(self) -> TransportAdapterBuildContext:
        supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        self.addAsyncCleanup(supervisor.shutdown)
        return TransportAdapterBuildContext(
            websocket_tcp_options=WebSocketTcpAdapterOptions(
                host="127.0.0.1",
                port=0,
                clock=SystemClock(),
                environment="test",
                allow_plaintext_non_prod=True,
            ),
            task_supervisor=supervisor,
            identity_factory=TransportIdentityFactory(),
        )

    async def test_default_registry_reserves_all_names_but_only_websocket_is_available(
        self,
    ) -> None:
        registry = TransportAdapterRegistry.default()
        self.assertEqual(TRANSPORT_ADAPTER_NAMES, tuple(registry.registrations))
        self.assertEqual(("websocket_tcp",), registry.available_adapters)
        for name in TRANSPORT_ADAPTER_NAMES[1:]:
            registration = registry.registrations[name]
            self.assertFalse(registration.available)
            self.assertIsNone(registration.factory)
            self.assertFalse(registration.capabilities.supported)
        with self.assertRaises(TypeError):
            registry.registrations["quic_native"] = registry.registrations["websocket_tcp"]  # type: ignore[index]

    async def test_create_enabled_builds_without_starting_listener(self) -> None:
        registry = TransportAdapterRegistry.default()
        adapters = registry.create_enabled(
            ("websocket_tcp",),
            context=self._context(),
        )
        self.assertEqual(1, len(adapters))
        self.assertFalse(adapters[0].accepting)
        self.assertIsNone(adapters[0].bound_port)  # type: ignore[attr-defined]
        await adapters[0].close()

    async def test_disabled_adapter_fails_without_partial_construction(self) -> None:
        registry = TransportAdapterRegistry.default()
        for name in TRANSPORT_ADAPTER_NAMES[1:]:
            with self.subTest(name=name), self.assertRaises(
                NsRuntimeTransportDisabledError,
            ) as raised:
                registry.create_enabled((name,), context=self._context())
            self.assertEqual("adapter_unavailable", raised.exception.details["reason"])
            self.assertNotIn(name, repr(raised.exception.details))

    async def test_duplicate_enabled_adapter_is_rejected(self) -> None:
        with self.assertRaises(NsValidationError):
            TransportAdapterRegistry.default().create_enabled(
                ("websocket_tcp", "websocket_tcp"),
                context=self._context(),
            )

    async def test_fresh_registry_import_and_disabled_lookup_load_no_transport_dependencies(
        self,
    ) -> None:
        environment = dict(os.environ)
        environment["PYTHONPATH"] = "src"
        script = """
import sys
from ns_runtime.transport import TransportAdapterRegistry
registry = TransportAdapterRegistry.default()
assert registry.available_adapters == ('websocket_tcp',)
for dependency in ('websockets', 'aioquic', 'webtransport'):
    assert not any(name == dependency or name.startswith(dependency + '.') for name in sys.modules)
"""
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=os.getcwd(),
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)

