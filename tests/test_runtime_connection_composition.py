# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import importlib.util
import json
import ssl
import subprocess
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from ns_common.async_runtime import TaskSupervisor
from ns_common.identifiers import IdentifierFactory, NsIdentifierKind
from ns_common.observability import InMemoryMetricsSink
from ns_common.security import Sanitizer
from ns_common.time import SystemClock
from ns_runtime.connection import (
    AcceptedHeartbeatPolicy,
    ConnectionAcceptedEnvelopeBuilder,
    ConnectionLifecycleManager,
    ConnectionLifecyclePolicy,
    ConnectionLifecycleProcessorRegistryFactory,
    DeterministicTestIamAdapter,
    FailClosedHandshakeIamAdapter,
    HandshakeIamAuthority,
    LocalConnectionIndex,
    TestIamAction,
    TestIamOutcome,
)
from ns_runtime.protocol import ErrorEnvelopeBuilder, JsonV1Codec
from ns_runtime.roles import RuntimeRole
from ns_runtime.transport import (
    TransportIdentityFactory,
    TransportManager,
    TransportMetricsRecorder,
    WebSocketTcpAdapter,
    WebSocketTcpAdapterOptions,
)


@unittest.skipUnless(
    importlib.util.find_spec("websockets") is not None,
    "runtime transport dependency isn't installed",
)
class ConnectionLifecycleCompositionLoopbackTestCase(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._certificate_directory = tempfile.TemporaryDirectory()
        directory = Path(cls._certificate_directory.name)
        cls._certificate = directory / "loopback-cert.pem"
        cls._private_key = directory / "loopback-key.pem"
        completed = subprocess.run(
            [
                "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                "-keyout", str(cls._private_key),
                "-out", str(cls._certificate),
                "-days", "1", "-subj", "/CN=localhost",
                "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise unittest.SkipTest("loopback TLS certificate generation failed")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._certificate_directory.cleanup()

    async def asyncSetUp(self) -> None:
        self.clock = SystemClock()
        self.supervisor = TaskSupervisor(shutdown_timeout_seconds=2)
        self._managers: list[ConnectionLifecycleManager] = []
        self._transport_managers: list[TransportManager] = []

    async def asyncTearDown(self) -> None:
        for manager in reversed(self._managers):
            await manager.drain()
        for transport_manager in reversed(self._transport_managers):
            await transport_manager.close()
        await self.supervisor.shutdown(timeout_seconds=2)
        # TLS transports publish their final close callback on a later loop turn.
        await asyncio.sleep(0)

    def _server_tls_context(self) -> ssl.SSLContext:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(self._certificate, self._private_key)
        return context

    @staticmethod
    def _client_tls_context() -> ssl.SSLContext:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context

    async def _start(
        self,
        iam_adapter,
        *,
        tls: bool = False,
    ) -> tuple[WebSocketTcpAdapter, ConnectionLifecycleManager]:
        ssl_context = self._server_tls_context() if tls else None
        options = WebSocketTcpAdapterOptions(
            host="127.0.0.1",
            port=0,
            clock=self.clock,
            ssl_context=ssl_context,
            environment="test",
            allow_plaintext_non_prod=not tls,
            send_timeout_seconds=1,
            ping_timeout_seconds=1,
            close_timeout_seconds=1,
            adapter_shutdown_timeout_seconds=2,
        )
        adapter = WebSocketTcpAdapter(
            options=options,
            task_supervisor=self.supervisor,
            identity_factory=TransportIdentityFactory(),
            metrics=TransportMetricsRecorder(
                clock=self.clock,
                sink=InMemoryMetricsSink(),
            ),
        )
        transport_manager = TransportManager((adapter,))
        identifier_factory = IdentifierFactory()
        runtime_id = identifier_factory.generate(NsIdentifierKind.RUNTIME_ID)
        manager = ConnectionLifecycleManager(
            transport_manager=transport_manager,
            connection_index=LocalConnectionIndex(),
            clock=self.clock,
            task_supervisor=self.supervisor,
            identifier_factory=identifier_factory,
            iam_adapter=iam_adapter,
            accepted_builder=ConnectionAcceptedEnvelopeBuilder(
                clock=self.clock,
                identifier_factory=identifier_factory,
                runtime_id=runtime_id,
                role=RuntimeRole.SINGLETON,
                heartbeat_policy=AcceptedHeartbeatPolicy(
                    interval_seconds=30,
                    timeout_seconds=120,
                ),
            ),
            error_builder=ErrorEnvelopeBuilder(sanitizer=Sanitizer()),
            logger=__import__("logging").Logger("p05-composition-test"),
            runtime_id=runtime_id,
            policy=ConnectionLifecyclePolicy(
                handshake_timeout_seconds=2,
                rejected_send_timeout_seconds=1,
                native_heartbeat_interval_seconds=60,
                envelope_heartbeat_timeout_seconds=120,
                drain_timeout_seconds=2,
                reconnect_grace_seconds=30,
                reauth_lead_seconds=30,
            ),
            codec=JsonV1Codec(),
            processor_registry_factory=ConnectionLifecycleProcessorRegistryFactory(),
        )
        await transport_manager.start()
        await manager.start()
        self._transport_managers.append(transport_manager)
        self._managers.append(manager)
        return adapter, manager

    async def test_plaintext_real_adapter_hello_heartbeat_drain_close(self) -> None:
        from websockets.asyncio.client import connect

        adapter, manager = await self._start(_test_iam(self.clock, 1))
        async with connect(
            f"ws://127.0.0.1:{adapter.bound_port}",
            proxy=None,
        ) as client:
            await client.send(_hello())
            accepted = json.loads(await asyncio.wait_for(client.recv(), timeout=2))
            self.assertEqual("connection.accepted", accepted["message"]["type"])
            context = accepted["payload"]["inline"]
            await client.send(_heartbeat(context, sequence=1))
            ack = json.loads(await asyncio.wait_for(client.recv(), timeout=2))
            self.assertEqual("connection.heartbeat_ack", ack["message"]["type"])
            self.assertEqual(1, ack["payload"]["inline"]["sequence"])
            await client.send(_disabled_task())
            disabled = json.loads(await asyncio.wait_for(client.recv(), timeout=2))
            self.assertEqual("runtime.error", disabled["message"]["type"])
            self.assertEqual(
                "RUNTIME_FEATURE_DISABLED",
                disabled["payload"]["inline"]["error_code"],
            )
            await client.send(_drain())
            await asyncio.wait_for(client.wait_closed(), timeout=2)
        await _wait_until(lambda: manager.active_connection_count == 0)
        self.assertEqual((), await manager.connection_index.active_targets())

    async def test_tls_real_adapter_reaches_active(self) -> None:
        from websockets.asyncio.client import connect

        adapter, manager = await self._start(_test_iam(self.clock, 1), tls=True)
        async with connect(
            f"wss://127.0.0.1:{adapter.bound_port}",
            ssl=self._client_tls_context(),
            proxy=None,
        ) as client:
            await client.send(_hello())
            accepted = json.loads(await asyncio.wait_for(client.recv(), timeout=2))
            self.assertEqual("connection.accepted", accepted["message"]["type"])
            self.assertEqual(1, len(await manager.connection_index.active_targets()))
            await client.send(_drain())
            await asyncio.wait_for(client.wait_closed(), timeout=2)

    async def test_protocol_incompatible_receives_rejected_then_close(self) -> None:
        from websockets.asyncio.client import connect

        adapter, manager = await self._start(_test_iam(self.clock, 1))
        async with connect(
            f"ws://127.0.0.1:{adapter.bound_port}",
            proxy=None,
        ) as client:
            await client.send(_hello(protocol_major=2, requested_version="2.0.0"))
            rejected = json.loads(await asyncio.wait_for(client.recv(), timeout=2))
            self.assertEqual("connection.rejected", rejected["message"]["type"])
            self.assertEqual(
                "protocol_incompatible",
                rejected["payload"]["inline"]["reason"],
            )
            self.assertEqual(
                {"reason", "server_time", "retryable"},
                set(rejected["payload"]["inline"]),
            )
            await asyncio.wait_for(client.wait_closed(), timeout=2)
        self.assertEqual(0, manager.active_connection_count)

    async def test_disconnect_resume_epoch_and_reauth_end_to_end(self) -> None:
        from websockets.asyncio.client import connect

        adapter, manager = await self._start(_test_iam(self.clock, 3))
        uri = f"ws://127.0.0.1:{adapter.bound_port}"
        first = await connect(uri, proxy=None)
        await first.send(_hello())
        accepted = json.loads(await asyncio.wait_for(first.recv(), timeout=2))
        old = accepted["payload"]["inline"]
        await first.close()
        await _wait_until_async(
            lambda: _target_count(manager),
            expected=0,
        )

        async with connect(uri, proxy=None) as resumed_client:
            await resumed_client.send(_hello(resume=old))
            resumed = json.loads(
                await asyncio.wait_for(resumed_client.recv(), timeout=2),
            )
            current = resumed["payload"]["inline"]
            self.assertEqual(old["connection_id"], current["connection_id"])
            entry = await manager.connection_index.lookup_connection(
                current["connection_id"],
            )
            assert entry is not None
            self.assertEqual(1, entry.session_context.connection_epoch)
            self.assertNotEqual(old["session_id"], current["session_id"])

            await resumed_client.send(_reauth())
            reauth = json.loads(
                await asyncio.wait_for(resumed_client.recv(), timeout=2),
            )
            self.assertEqual("connection.reauth_accepted", reauth["message"]["type"])
            await resumed_client.send(_heartbeat(current, sequence=2, epoch=1))
            ack = json.loads(await asyncio.wait_for(resumed_client.recv(), timeout=2))
            self.assertEqual("connection.heartbeat_ack", ack["message"]["type"])

    async def test_old_epoch_is_rejected_after_resume(self) -> None:
        from websockets.asyncio.client import connect

        adapter, manager = await self._start(_test_iam(self.clock, 2))
        uri = f"ws://127.0.0.1:{adapter.bound_port}"
        first = await connect(uri, proxy=None)
        await first.send(_hello())
        accepted = json.loads(await first.recv())
        old = accepted["payload"]["inline"]
        await first.close()
        await _wait_until_async(lambda: _target_count(manager), expected=0)
        async with connect(uri, proxy=None) as resumed_client:
            await resumed_client.send(_hello(resume=old))
            current = json.loads(await resumed_client.recv())["payload"]["inline"]
            await resumed_client.send(_heartbeat(old, sequence=3, epoch=0))
            error = json.loads(await asyncio.wait_for(resumed_client.recv(), timeout=2))
            self.assertEqual("runtime.error", error["message"]["type"])
            await asyncio.wait_for(resumed_client.wait_closed(), timeout=2)
            self.assertNotEqual(old["session_id"], current["session_id"])

    async def test_production_fail_closed_never_enters_active(self) -> None:
        from websockets.asyncio.client import connect

        prod_adapter, prod_manager = await self._start(FailClosedHandshakeIamAdapter())
        async with connect(
            f"ws://127.0.0.1:{prod_adapter.bound_port}",
            proxy=None,
        ) as client:
            await client.send(_hello())
            rejected = json.loads(await asyncio.wait_for(client.recv(), timeout=2))
            self.assertEqual("connection.rejected", rejected["message"]["type"])
            self.assertEqual("iam_denied", rejected["payload"]["inline"]["reason"])
            await asyncio.wait_for(client.wait_closed(), timeout=2)
        self.assertEqual(0, prod_manager.active_connection_count)

    async def test_reauth_rejection_is_sent_then_connection_closes(self) -> None:
        from websockets.asyncio.client import connect

        authority = _authority(self.clock)
        iam = DeterministicTestIamAdapter(
            (
                TestIamOutcome(action=TestIamAction.ALLOW, authority=authority),
                TestIamOutcome(action=TestIamAction.DENY),
            ),
            clock=self.clock,
        )
        adapter, manager = await self._start(iam)
        async with connect(
            f"ws://127.0.0.1:{adapter.bound_port}",
            proxy=None,
        ) as client:
            await client.send(_hello())
            accepted = json.loads(await asyncio.wait_for(client.recv(), timeout=2))
            self.assertEqual("connection.accepted", accepted["message"]["type"])
            await client.send(_reauth())
            rejected = json.loads(await asyncio.wait_for(client.recv(), timeout=2))
            self.assertEqual("connection.reauth_rejected", rejected["message"]["type"])
            self.assertEqual("auth_denied", rejected["payload"]["inline"]["reason"])
            await asyncio.wait_for(client.wait_closed(), timeout=2)
        await _wait_until(lambda: manager.active_connection_count == 0)


def _authority(clock: SystemClock) -> HandshakeIamAuthority:
    now = clock.utc_now()
    return HandshakeIamAuthority(
        identity="identity:test-client",
        tenant_id="tenant:test",
        component_type="client",
        capabilities=frozenset({"runtime.connection"}),
        permissions={"runtime.connection": True},
        permission_snapshot_ref="permission:test",
        permission_digest="sha256:test",
        permission_version="version:test",
        issued_at=now,
        expires_at=now + timedelta(minutes=10),
        resume_eligible=True,
        iam_mode="test",
    )


def _test_iam(clock: SystemClock, count: int) -> DeterministicTestIamAdapter:
    authority = _authority(clock)
    return DeterministicTestIamAdapter(
        tuple(
            TestIamOutcome(action=TestIamAction.ALLOW, authority=authority)
            for _ in range(count)
        ),
        clock=clock,
    )


def _message(message_type: str, *, payload: dict[str, object] | None = None) -> dict[str, object]:
    value: dict[str, object] = {
        "protocol": {"major": 1, "minor": 0, "patch": 0},
        "message": {
            "message_id": "message_00000000000000000000000000000001",
            "type": message_type,
            "category": "connection",
            "priority": 0,
            "created_at": "2026-07-21T00:00:00Z",
            "reliability": "best_effort",
        },
    }
    if payload is not None:
        value["payload"] = {"mode": "inline", "inline": payload}
    return value


def _hello(
    *,
    protocol_major: int = 1,
    requested_version: str = "1.0.0",
    resume: dict[str, object] | None = None,
) -> str:
    value = _message(
        "connection.hello",
        payload={
            "token": "opaque-test-token",
            "component_type": "client",
            "requested_version": requested_version,
            "min_version": requested_version,
            "requested_capabilities": ["runtime.connection"],
        },
    )
    value["protocol"] = {"major": protocol_major, "minor": 0, "patch": 0}
    if resume is not None:
        value["extensions"] = {
            "ns.connection_resume": {
                "connection_id": resume["connection_id"],
                "session_id": resume["session_id"],
                "connection_epoch": 0,
            },
        }
    return json.dumps(value, separators=(",", ":"))


def _heartbeat(
    context: dict[str, object],
    *,
    sequence: int,
    epoch: int = 0,
) -> str:
    return json.dumps(
        _message(
            "connection.heartbeat",
            payload={
                "connection_id": context["connection_id"],
                "session_id": context["session_id"],
                "connection_epoch": epoch,
                "sequence": sequence,
                "sent_at": "2026-07-21T00:00:00Z",
            },
        ),
        separators=(",", ":"),
    )


def _drain() -> str:
    return json.dumps(_message("connection.drain"), separators=(",", ":"))


def _reauth() -> str:
    return json.dumps(
        _message(
            "connection.reauth",
            payload={
                "token": "opaque-reauth-token",
                "requested_capabilities": ["runtime.connection"],
            },
        ),
        separators=(",", ":"),
    )


def _disabled_task() -> str:
    value = _message(
        "task.dispatch",
        payload={"operation": "not-yet-enabled"},
    )
    value["message"]["category"] = "task"  # type: ignore[index]
    value["target"] = {"kind": "runtime", "runtime_id": "runtime_target"}
    return json.dumps(value, separators=(",", ":"))


async def _target_count(manager: ConnectionLifecycleManager) -> int:
    return len(await manager.connection_index.active_targets())


async def _wait_until_async(operation, *, expected: object) -> None:
    for _ in range(200):
        if await operation() == expected:
            return
        await asyncio.sleep(0.01)
    raise AssertionError("async condition did not become true")


async def _wait_until(predicate) -> None:
    for _ in range(200):
        if predicate():
            return
        await asyncio.sleep(0.01)
    raise AssertionError("condition did not become true")


if __name__ == "__main__":
    unittest.main()
