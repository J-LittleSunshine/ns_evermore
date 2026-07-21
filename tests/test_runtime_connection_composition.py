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
    HandshakeIamAdapter,
    HandshakeIamRequest,
    LocalConnectionIndex,
    LogicalConnectionCloseReason,
    LogicalConnectionState,
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
        drain_timeout_seconds: float = 2,
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
                drain_timeout_seconds=drain_timeout_seconds,
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

    async def test_plaintext_drain_remains_open_for_lifecycle_messages(self) -> None:
        from websockets.asyncio.client import connect

        adapter, manager = await self._start(_test_iam(self.clock, 1))
        async with connect(
            f"ws://127.0.0.1:{adapter.bound_port}",
            proxy=None,
        ) as client:
            await client.send(_hello())
            accepted = json.loads(await asyncio.wait_for(client.recv(), timeout=2))
            self.assertEqual("connection.accepted", accepted["message"]["type"])
            self.assertEqual(0, manager.pending_candidate_cleanup_count)
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
            connection_id = context["connection_id"]
            assert isinstance(connection_id, str)
            await _wait_until_async(
                lambda: _connection_state(manager, connection_id),
                expected=LogicalConnectionState.DRAINING,
            )
            self.assertIsNone(client.close_code)
            self.assertEqual((), await manager.connection_index.active_targets())
            owner = manager._owners[connection_id]
            assert owner.drain is not None
            first_drain = await owner.drain.snapshot()
            await client.send(_drain())
            await client.send(_heartbeat(context, sequence=2))
            draining_ack = json.loads(
                await asyncio.wait_for(client.recv(), timeout=2),
            )
            self.assertEqual(
                "connection.heartbeat_ack",
                draining_ack["message"]["type"],
            )
            duplicate_drain = await owner.drain.snapshot()
            self.assertEqual(
                first_drain.deadline_monotonic,
                duplicate_drain.deadline_monotonic,
            )
            self.assertIsNone(client.close_code)
            await manager.drain()
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
            await manager.drain()
            await asyncio.wait_for(client.wait_closed(), timeout=2)

    async def test_drain_deadline_boundedly_closes_real_transport(self) -> None:
        from websockets.asyncio.client import connect

        adapter, manager = await self._start(
            _test_iam(self.clock, 1),
            drain_timeout_seconds=0.05,
        )
        async with connect(
            f"ws://127.0.0.1:{adapter.bound_port}",
            proxy=None,
        ) as client:
            await client.send(_hello())
            accepted = json.loads(await asyncio.wait_for(client.recv(), timeout=2))
            connection_id = accepted["payload"]["inline"]["connection_id"]
            await client.send(_drain())
            await _wait_until_async(
                lambda: _connection_state(manager, connection_id),
                expected=LogicalConnectionState.DRAINING,
            )
            await asyncio.wait_for(client.wait_closed(), timeout=2)
        await _wait_until(lambda: manager.active_connection_count == 0)
        self.assertIsNone(
            await manager.connection_index.lookup_connection(connection_id),
        )

    async def test_semantic_hello_failures_close_without_composition_leaks(self) -> None:
        from websockets.asyncio.client import connect

        iam = _test_iam(self.clock, 1)
        adapter, manager = await self._start(iam)
        uri = f"ws://127.0.0.1:{adapter.bound_port}"
        for case in (
            "unsupported_component_type",
            "requested_version_mismatch",
            "minimum_version_mismatch",
            "invalid_capability",
            "duplicate_capability",
            "invalid_resume_reference",
        ):
            with self.subTest(case=case):
                async with connect(uri, proxy=None) as client:
                    await client.send(_invalid_hello(case))
                    await asyncio.wait_for(client.wait_closed(), timeout=2)
                await _wait_until(lambda: not manager._admission_tasks)
                self.assertEqual(0, manager.active_connection_count)
                self.assertEqual(0, manager.pending_candidate_cleanup_count)
                self.assertEqual({}, dict((await manager.connection_index.snapshot()).by_connection_id))
                self.assertFalse(any(
                    name.startswith(("logical-handshake-", "logical-iam-", "logical-admission-"))
                    for name in self.supervisor.pending_task_names
                ))
        self.assertEqual(0, iam.call_count)

    async def test_hostile_iam_failure_is_not_retained_by_supervisor(self) -> None:
        from websockets.asyncio.client import connect

        iam = _HostileBeforeTakeIamAdapter()
        adapter, manager = await self._start(iam)
        async with connect(
            f"ws://127.0.0.1:{adapter.bound_port}",
            proxy=None,
        ) as client:
            await client.send(_hello())
            rejected = json.loads(await asyncio.wait_for(client.recv(), timeout=2))
            self.assertEqual("connection.rejected", rejected["message"]["type"])
            self.assertEqual("iam_unavailable", rejected["payload"]["inline"]["reason"])
            await asyncio.wait_for(client.wait_closed(), timeout=2)
        await _wait_until(lambda: not manager._admission_tasks)
        self.assertIsNotNone(iam.request)
        assert iam.request is not None
        self.assertFalse(iam.request.credential.available)
        self.assertEqual((), self.supervisor.failures)
        await manager.drain()
        await self._transport_managers[-1].close()
        report = await self.supervisor.shutdown(timeout_seconds=2)
        retained = repr(report) + repr(self.supervisor.failures) + repr(iam.request)
        self.assertNotIn("opaque-test-token", retained)
        self.assertFalse(any(name.startswith("logical-iam-") for name in report.failed_tasks))

    async def test_close_failure_retains_owner_until_concurrent_shutdown_retry(self) -> None:
        from websockets.asyncio.client import connect

        adapter, manager = await self._start(_test_iam(self.clock, 1))
        async with connect(
            f"ws://127.0.0.1:{adapter.bound_port}",
            proxy=None,
        ) as client:
            await client.send(_hello())
            accepted = json.loads(await asyncio.wait_for(client.recv(), timeout=2))
            connection_id = accepted["payload"]["inline"]["connection_id"]
            owner = manager._owners[connection_id]
            assert owner.transport is not None
            original_close = owner.transport.close
            first_started = asyncio.Event()
            release_failure = asyncio.Event()
            close_attempts = 0

            async def fail_then_close():
                nonlocal close_attempts
                close_attempts += 1
                if close_attempts == 1:
                    first_started.set()
                    await release_failure.wait()
                    raise RuntimeError("close failure")
                return await original_close()

            owner.transport.close = fail_then_close  # type: ignore[method-assign]
            first = asyncio.create_task(manager._close_owner(
                owner,
                LogicalConnectionCloseReason.SHUTDOWN,
            ))
            await first_started.wait()
            concurrent_shutdown = asyncio.create_task(manager.drain())
            release_failure.set()
            self.assertFalse(await first)
            entry = await manager.connection_index.lookup_connection(connection_id)
            self.assertIsNotNone(entry)
            assert entry is not None
            self.assertIs(LogicalConnectionState.CLOSING, entry.state)
            self.assertIn(connection_id, manager._owners)
            await concurrent_shutdown
            await asyncio.wait_for(client.wait_closed(), timeout=2)
            self.assertEqual(2, close_attempts)
            self.assertIsNone(await manager.connection_index.lookup_connection(connection_id))
            self.assertNotIn(connection_id, manager._owners)

    async def test_close_cancellation_retains_retryable_cleanup_owner(self) -> None:
        from websockets.asyncio.client import connect

        adapter, manager = await self._start(_test_iam(self.clock, 1))
        async with connect(
            f"ws://127.0.0.1:{adapter.bound_port}",
            proxy=None,
        ) as client:
            await client.send(_hello())
            accepted = json.loads(await asyncio.wait_for(client.recv(), timeout=2))
            connection_id = accepted["payload"]["inline"]["connection_id"]
            owner = manager._owners[connection_id]
            assert owner.transport is not None
            original_close = owner.transport.close
            cancelled = asyncio.CancelledError("transport close cancelled")

            async def cancelled_close():
                raise cancelled

            owner.transport.close = cancelled_close  # type: ignore[method-assign]
            try:
                with self.assertRaises(asyncio.CancelledError) as raised:
                    await manager.drain()
                self.assertIs(cancelled, raised.exception)
                entry = await manager.connection_index.lookup_connection(connection_id)
                self.assertIsNotNone(entry)
                assert entry is not None
                self.assertIs(LogicalConnectionState.CLOSING, entry.state)
                self.assertIn(connection_id, manager._owners)
            finally:
                owner.transport.close = original_close  # type: ignore[method-assign]
            self.assertTrue(await manager.retry_cleanup(connection_id))
            await asyncio.wait_for(client.wait_closed(), timeout=2)
            self.assertIsNone(await manager.connection_index.lookup_connection(connection_id))
            self.assertNotIn(connection_id, manager._owners)

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
        await _wait_until(lambda: not prod_manager._admission_tasks)
        self.assertEqual(0, prod_manager.active_connection_count)
        self.assertEqual(0, prod_manager.pending_candidate_cleanup_count)
        self.assertEqual((), self.supervisor.failures)

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

    async def test_draining_reauth_denial_converges_first_reason_and_tasks(self) -> None:
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
            connection_id = accepted["payload"]["inline"]["connection_id"]
            owner = manager._owners[connection_id]
            assert owner.drain is not None
            drain = owner.drain
            await client.send(_drain())
            await _wait_until_async(
                lambda: _connection_state(manager, connection_id),
                expected=LogicalConnectionState.DRAINING,
            )
            await client.send(_reauth())
            rejected = json.loads(await asyncio.wait_for(client.recv(), timeout=2))
            self.assertEqual("connection.reauth_rejected", rejected["message"]["type"])
            await asyncio.wait_for(client.wait_closed(), timeout=2)

        await drain.wait_closed()
        await _wait_until(lambda: manager.active_connection_count == 0)
        snapshot = await drain.snapshot()
        self.assertIs(LogicalConnectionCloseReason.AUTH_FAILED, snapshot.terminal_reason)
        self.assertIs(
            LogicalConnectionCloseReason.AUTH_FAILED,
            owner.state_machine.close_reason,
        )
        self.assertFalse(snapshot.timeout_pending)
        self.assertIsNone(await manager.connection_index.lookup_connection(connection_id))
        await _wait_until(lambda: not any(
            name.startswith("logical-drain-")
            for name in self.supervisor.pending_task_names
        ))

    async def test_draining_reauth_close_failure_keeps_auth_reason_for_retry(self) -> None:
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
            connection_id = accepted["payload"]["inline"]["connection_id"]
            owner = manager._owners[connection_id]
            assert owner.transport is not None
            assert owner.drain is not None
            drain = owner.drain
            original_close = owner.transport.close
            close_calls = 0

            async def fail_once():
                nonlocal close_calls
                close_calls += 1
                if close_calls == 1:
                    raise RuntimeError("external close failure")
                return await original_close()

            owner.transport.close = fail_once  # type: ignore[method-assign]
            await client.send(_drain())
            await _wait_until_async(
                lambda: _connection_state(manager, connection_id),
                expected=LogicalConnectionState.DRAINING,
            )
            await client.send(_reauth())
            rejected = json.loads(await asyncio.wait_for(client.recv(), timeout=2))
            self.assertEqual("connection.reauth_rejected", rejected["message"]["type"])
            await _wait_until_async(
                lambda: _connection_state(manager, connection_id),
                expected=LogicalConnectionState.CLOSING,
            )
            snapshot = await drain.snapshot()
            self.assertIs(LogicalConnectionCloseReason.AUTH_FAILED, snapshot.terminal_reason)
            self.assertIs(
                LogicalConnectionCloseReason.AUTH_FAILED,
                owner.state_machine.close_reason,
            )
            self.assertFalse(snapshot.timeout_pending)
            self.assertIn(connection_id, manager._owners)
            self.assertIsNotNone(owner.drain_cleanup_task)
            assert owner.drain_cleanup_task is not None
            self.assertFalse(owner.drain_cleanup_task.done())

            self.assertTrue(await manager.retry_cleanup(connection_id))
            await asyncio.wait_for(client.wait_closed(), timeout=2)

        await drain.wait_closed()
        self.assertEqual(2, close_calls)
        self.assertIs(
            LogicalConnectionCloseReason.AUTH_FAILED,
            (await drain.snapshot()).terminal_reason,
        )
        await _wait_until(lambda: manager.active_connection_count == 0)
        await _wait_until(lambda: not any(
            name.startswith("logical-drain-")
            for name in self.supervisor.pending_task_names
        ))


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


class _HostileBeforeTakeIamAdapter(HandshakeIamAdapter):
    def __init__(self) -> None:
        self.request: HandshakeIamRequest | None = None

    async def authenticate(
        self,
        request: HandshakeIamRequest,
    ) -> HandshakeIamAuthority:
        self.request = request
        raise RuntimeError("opaque-test-token")


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


def _invalid_hello(case: str) -> str:
    value = json.loads(_hello())
    protocol = value["protocol"]
    payload = value["payload"]["inline"]
    if case == "unsupported_component_type":
        payload["component_type"] = "unsupported"
    elif case == "requested_version_mismatch":
        payload["requested_version"] = "1.0.1"
    elif case == "minimum_version_mismatch":
        protocol["min_version"] = "1.0.1"
    elif case == "invalid_capability":
        payload["requested_capabilities"] = ["runtime.connection", "INVALID"]
    elif case == "duplicate_capability":
        payload["requested_capabilities"] = ["runtime.connection", "runtime.connection"]
    elif case == "invalid_resume_reference":
        value["extensions"] = {
            "ns.connection_resume": {
                "connection_id": "invalid",
                "session_id": "invalid",
                "connection_epoch": 0,
            },
        }
    else:
        raise AssertionError("unknown invalid hello case")
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


async def _connection_state(
    manager: ConnectionLifecycleManager,
    connection_id: str,
) -> LogicalConnectionState | None:
    entry = await manager.connection_index.lookup_connection(connection_id)
    return entry.state if entry is not None else None


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
