# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import dataclasses
import unittest
from uuid import UUID

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import (
    NsRuntimeIamDeniedError,
    NsRuntimeStateStoreUnavailableError,
    NsStateError,
)
from ns_common.identifiers import IdentifierFactory
from ns_common.time import ControlledClock
from ns_runtime.connection import (
    ConnectionAuditConsistency,
    ConnectionAuditKind,
    ConnectionAuditOutcome,
    ConnectionCapabilityClass,
    ConnectionHeartbeatService,
    ConnectionLifecycleAuditBoundary,
    ConnectionReauthCoordinator,
    ConnectionReauthEnvelopeHandler,
    ConnectionResumeCoordinator,
    DeterministicTestConnectionAuditSink,
    DeterministicTestIamAdapter,
    DeterministicTestSecurityAuditSink,
    HeartbeatPolicy,
    LocalConnectionIndex,
    LogicalConnectionCloseReason,
    LogicalConnectionState,
    LogicalConnectionTransportMap,
    LogicalSessionIdentityFactory,
    NonResumableCloseKind,
    NonResumableConnectionGuard,
    ReconnectGraceService,
    SafeConnectionSnapshot,
    SafeConnectionSnapshotReader,
    SessionExpiryController,
    SessionExpiryPolicy,
    TestIamAction,
    TestIamOutcome,
)
from ns_runtime.protocol import JsonV1Codec
from tests.test_runtime_connection_accepted import _CaptureTransport, _builder
from tests.test_runtime_connection_binding import (
    CONNECTION_ID,
    SESSION_ID,
    UTC_START,
    _context,
)
from tests.test_runtime_connection_drain import _service as _drain_service
from tests.test_runtime_connection_heartbeat import (
    _heartbeat,
    _service as _heartbeat_service,
)
from tests.test_runtime_connection_index import _authenticated_machine
from tests.test_runtime_connection_reauth import _reauth_text, _response_builder
from tests.test_runtime_connection_resume import (
    _ResumeTransport,
    _adapter as _resume_adapter,
    _parsed as _resume_parsed,
)


class SafeConnectionSnapshotTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.clock = ControlledClock(utc_start=UTC_START)
        self.supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        self.transport = _CaptureTransport()
        self.current = _context(self.transport, clock=self.clock)
        self.machine = await _authenticated_machine()
        self.index = LocalConnectionIndex()
        await self.index.add_authenticated(
            session_context=self.current,
            state_machine=self.machine,
        )
        await self.index.transition(CONNECTION_ID, LogicalConnectionState.ACTIVE)
        self.mapping = LogicalConnectionTransportMap(
            session_context=self.current,
            transport_session=self.transport,
        )
        self.heartbeat = _heartbeat_service(
            context=self.current,
            index=self.index,
            transport=self.transport,
            clock=self.clock,
            supervisor=self.supervisor,
        )
        self.grace = ReconnectGraceService(
            session_context=self.current,
            connection_index=self.index,
            transport_mapping=self.mapping,
            clock=self.clock,
            task_supervisor=self.supervisor,
            task_sequence=141,
        )
        self.drain = _drain_service(
            index=self.index,
            transport=self.transport,
            clock=self.clock,
            supervisor=self.supervisor,
        )
        self.expiry = SessionExpiryController(
            session_context=self.current,
            connection_index=self.index,
            transport_session=self.transport,
            clock=self.clock,
            task_supervisor=self.supervisor,
            task_sequence=142,
            policy=SessionExpiryPolicy(reauth_lead_seconds=60),
        )
        self.security = NonResumableConnectionGuard(
            session_context=self.current,
            connection_index=self.index,
            clock=self.clock,
            audit_sink=DeterministicTestSecurityAuditSink(),
            lifecycle_audit=ConnectionLifecycleAuditBoundary(
                session_context=self.current,
                clock=self.clock,
                sink=DeterministicTestConnectionAuditSink(),
            ),
            transport_session=self.transport,
        )

    async def asyncTearDown(self) -> None:
        await self.supervisor.shutdown(timeout_seconds=1)

    async def test_exact_frozen_safe_projection_and_nested_lifecycle_views(self) -> None:
        await self.heartbeat.start()
        await self.expiry.start()
        await _wait_until(lambda: self.clock.pending_sleep_count == 3)
        await self.heartbeat.handle_text(_heartbeat(sequence=1))

        snapshot = await self._reader().read()

        self.assertEqual(
            {
                "connection_summary", "session_summary", "state", "close_reason",
                "active_target_eligible", "component_type", "connection_epoch",
                "protocol_version", "capability_classes", "heartbeat", "grace",
                "drain", "reauth", "security_close", "observed_at",
                "index_mutation_sequence", "coherent", "complete",
            },
            {field.name for field in dataclasses.fields(SafeConnectionSnapshot)},
        )
        self.assertTrue(snapshot.connection_summary.startswith("sha256:"))
        self.assertTrue(snapshot.session_summary.startswith("sha256:"))
        self.assertIs(LogicalConnectionState.ACTIVE, snapshot.state)
        self.assertTrue(snapshot.active_target_eligible)
        self.assertEqual("client", snapshot.component_type)
        self.assertEqual(0, snapshot.connection_epoch)
        self.assertEqual("1.0.0", snapshot.protocol_version)
        self.assertEqual(
            frozenset({
                ConnectionCapabilityClass.LIFECYCLE,
                ConnectionCapabilityClass.MANAGEMENT,
            }),
            snapshot.capability_classes,
        )
        self.assertIsNotNone(snapshot.heartbeat)
        self.assertIsNotNone(snapshot.grace)
        self.assertIsNotNone(snapshot.drain)
        self.assertIsNotNone(snapshot.reauth)
        self.assertIsNotNone(snapshot.security_close)
        self.assertTrue(snapshot.coherent)
        self.assertTrue(snapshot.complete)
        with self.assertRaises((dataclasses.FrozenInstanceError, TypeError)):
            snapshot.state = LogicalConnectionState.CLOSED  # type: ignore[misc]

        rendered = repr(snapshot)
        for forbidden in (
            CONNECTION_ID,
            SESSION_ID,
            "identity:test-user",
            "tenant:test",
            "permission:snapshot-test",
            "sha256:permission-test",
            self.transport.identity.transport_session_id,
            self.transport.identity.path.peer_summary,
            "token",
            "credential",
            "payload",
            "WebSocket",
        ):
            self.assertNotIn(forbidden, rendered)

    async def test_drain_and_security_close_are_visible_without_raw_authority(self) -> None:
        reader = self._reader()
        await self.drain.begin()

        draining = await reader.read()

        self.assertIs(LogicalConnectionState.DRAINING, draining.state)
        self.assertFalse(draining.active_target_eligible)
        assert draining.drain is not None
        self.assertTrue(draining.drain.timeout_pending)
        await self.drain.terminate(LogicalConnectionCloseReason.SHUTDOWN)

        fixture = await _snapshot_fixture()
        try:
            await fixture.security.close(NonResumableCloseKind.SECURITY_VIOLATION)
            closed = await fixture.reader.read()
            self.assertIs(LogicalConnectionState.CLOSED, closed.state)
            assert closed.security_close is not None
            assert closed.security_close.decision is not None
            self.assertIs(
                NonResumableCloseKind.SECURITY_VIOLATION,
                closed.security_close.decision.kind,
            )
            self.assertEqual(
                closed.security_close.decision.close_reason,
                closed.close_reason,
            )
        finally:
            await fixture.supervisor.shutdown(timeout_seconds=1)

    async def test_concurrent_authority_change_retries_to_coherent_projection(self) -> None:
        heartbeat = _BlockingHeartbeatService(
            session_context=self.current,
            connection_index=self.index,
            transport_session=self.transport,
            clock=self.clock,
            task_supervisor=self.supervisor,
            task_sequence=143,
            identifier_factory=IdentifierFactory(
                uuid_factory=lambda: UUID("123e4567-e89b-42d3-a456-426614174143"),
            ),
            policy=HeartbeatPolicy(
                native_interval_seconds=2,
                envelope_timeout_seconds=5,
            ),
            codec=JsonV1Codec(),
        )
        reader = SafeConnectionSnapshotReader(
            session_context=self.current,
            connection_index=self.index,
            clock=self.clock,
            heartbeat_service=heartbeat,
        )
        task = asyncio.create_task(reader.read())
        await heartbeat.snapshot_started.wait()
        updated = dataclasses.replace(
            self.current,
            capabilities=frozenset({"runtime.heartbeat"}),
            permission_version="version:2",
        )

        await self.index.replace_authority_context(
            updated,
            expected_session_context=self.current,
            allowed_states=frozenset({LogicalConnectionState.ACTIVE}),
        )
        heartbeat.snapshot_release.set()
        snapshot = await task

        self.assertTrue(snapshot.coherent)
        self.assertGreaterEqual(heartbeat.snapshot_calls, 2)
        self.assertEqual(
            frozenset({ConnectionCapabilityClass.HEARTBEAT}),
            snapshot.capability_classes,
        )
        self.assertNotIn("version:2", repr(snapshot))

    async def test_snapshot_source_failure_is_bounded_and_never_rendered(self) -> None:
        heartbeat = _FailingHeartbeatService(
            session_context=self.current,
            connection_index=self.index,
            transport_session=self.transport,
            clock=self.clock,
            task_supervisor=self.supervisor,
            task_sequence=144,
            identifier_factory=IdentifierFactory(
                uuid_factory=lambda: UUID("123e4567-e89b-42d3-a456-426614174144"),
            ),
            policy=HeartbeatPolicy(
                native_interval_seconds=2,
                envelope_timeout_seconds=5,
            ),
            codec=JsonV1Codec(),
        )
        reader = SafeConnectionSnapshotReader(
            session_context=self.current,
            connection_index=self.index,
            clock=self.clock,
            heartbeat_service=heartbeat,
        )

        snapshot = await reader.read()

        self.assertFalse(snapshot.complete)
        self.assertIsNone(snapshot.heartbeat)
        self.assertNotIn("snapshot-source-secret", repr(snapshot))

    def _reader(self) -> SafeConnectionSnapshotReader:
        return SafeConnectionSnapshotReader(
            session_context=self.current,
            connection_index=self.index,
            clock=self.clock,
            heartbeat_service=self.heartbeat,
            grace_service=self.grace,
            drain_service=self.drain,
            expiry_controller=self.expiry,
            security_guard=self.security,
        )


class ConnectionLifecycleAuditTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_resume_audit_failure_prevents_success_and_transport_send(self) -> None:
        fixture = await _resume_audit_fixture()
        try:
            fixture.sink.failure = RuntimeError("audit-storage-secret")
            with self.assertRaises(NsRuntimeStateStoreUnavailableError):
                await fixture.coordinator.resume(_resume_parsed())

            self.assertEqual([], fixture.transport.sent)
            self.assertIs(LogicalConnectionState.CLOSED, fixture.machine.state)
            audit = await fixture.boundary.snapshot()
            self.assertEqual(1, audit.attempted_count)
            self.assertEqual(1, audit.failed_count)
            self.assertEqual((), fixture.sink.events)
        finally:
            await fixture.supervisor.shutdown(timeout_seconds=1)

    async def test_resume_reference_rejection_is_audited_without_false_close(self) -> None:
        fixture = await _resume_audit_fixture()
        try:
            with self.assertRaises(NsStateError):
                await fixture.coordinator.resume(_resume_parsed(epoch=9))

            event = fixture.sink.events[0]
            self.assertIs(ConnectionAuditKind.RESUME, event.kind)
            self.assertIs(ConnectionAuditOutcome.REJECTED, event.outcome)
            self.assertIsNone(event.close_reason)
            self.assertIs(LogicalConnectionState.ACTIVE, fixture.machine.state)
        finally:
            await fixture.supervisor.shutdown(timeout_seconds=1)

    async def test_reauth_rejection_is_audited_without_overriding_denial(self) -> None:
        fixture = await _active_audit_fixture()
        try:
            adapter = DeterministicTestIamAdapter(
                (TestIamOutcome(action=TestIamAction.DENY),),
                clock=fixture.clock,
            )
            coordinator = ConnectionReauthCoordinator(
                current_context=fixture.current,
                connection_index=fixture.index,
                transport_session=fixture.transport,
                iam_adapter=adapter,
                response_builder=_response_builder(fixture.clock),
                clock=fixture.clock,
                task_supervisor=fixture.supervisor,
                task_sequence=145,
                timeout_seconds=10,
                audit_boundary=fixture.boundary,
            )
            parsed = ConnectionReauthEnvelopeHandler(
                session_context=fixture.current,
                codec=JsonV1Codec(),
            ).parse(_reauth_text())

            with self.assertRaises(NsRuntimeIamDeniedError):
                await coordinator.reauthenticate(parsed)

            event = fixture.sink.events[0]
            self.assertEqual(
                {
                    "kind", "outcome", "required_consistency",
                    "connection_summary", "component_type", "connection_epoch",
                    "close_reason", "occurred_at",
                },
                {field.name for field in dataclasses.fields(event)},
            )
            self.assertIs(ConnectionAuditKind.REAUTH_REJECTION, event.kind)
            self.assertIs(ConnectionAuditOutcome.REJECTED, event.outcome)
            self.assertIs(
                ConnectionAuditConsistency.STRONG_REQUIRED,
                event.required_consistency,
            )
            self.assertIs(LogicalConnectionState.CLOSED, fixture.machine.state)
            rendered = repr(event)
            for forbidden in (
                CONNECTION_ID,
                SESSION_ID,
                "identity:test-user",
                "tenant:test",
                "permission:snapshot-test",
                "reauth-top-secret-token",
                "payload",
                "credential",
            ):
                self.assertNotIn(forbidden, rendered)
        finally:
            await fixture.supervisor.shutdown(timeout_seconds=1)

    async def test_reauth_audit_unavailable_preserves_enforced_close(self) -> None:
        fixture = await _active_audit_fixture()
        try:
            fixture.sink.failure = RuntimeError("strong-audit-unavailable")
            coordinator = ConnectionReauthCoordinator(
                current_context=fixture.current,
                connection_index=fixture.index,
                transport_session=fixture.transport,
                iam_adapter=DeterministicTestIamAdapter(
                    (TestIamOutcome(action=TestIamAction.DENY),),
                    clock=fixture.clock,
                ),
                response_builder=_response_builder(fixture.clock),
                clock=fixture.clock,
                task_supervisor=fixture.supervisor,
                task_sequence=149,
                timeout_seconds=10,
                audit_boundary=fixture.boundary,
            )
            parsed = ConnectionReauthEnvelopeHandler(
                session_context=fixture.current,
                codec=JsonV1Codec(),
            ).parse(_reauth_text())

            with self.assertRaises(NsRuntimeStateStoreUnavailableError):
                await coordinator.reauthenticate(parsed)

            self.assertIs(LogicalConnectionState.CLOSED, fixture.machine.state)
            self.assertIsNone(await fixture.index.lookup_connection(CONNECTION_ID))
            audit = await fixture.boundary.snapshot()
            self.assertEqual(1, audit.failed_count)
        finally:
            await fixture.supervisor.shutdown(timeout_seconds=1)

    async def test_non_resumable_kinds_map_to_explicit_lifecycle_audit(self) -> None:
        cases = (
            (NonResumableCloseKind.KICK, ConnectionAuditKind.KICK),
            (
                NonResumableCloseKind.SECURITY_VIOLATION,
                ConnectionAuditKind.SECURITY_CLOSE,
            ),
            (
                NonResumableCloseKind.POLICY_NON_RECOVERABLE,
                ConnectionAuditKind.NON_RESUMABLE_CLOSE,
            ),
        )
        for close_kind, audit_kind in cases:
            with self.subTest(close_kind=close_kind.value):
                fixture = await _active_audit_fixture()
                try:
                    guard = NonResumableConnectionGuard(
                        session_context=fixture.current,
                        connection_index=fixture.index,
                        clock=fixture.clock,
                        audit_sink=DeterministicTestSecurityAuditSink(),
                        lifecycle_audit=fixture.boundary,
                        transport_session=fixture.transport,
                    )
                    await guard.close(close_kind)
                    event = fixture.sink.events[0]
                    self.assertIs(audit_kind, event.kind)
                    self.assertIs(ConnectionAuditOutcome.ENFORCED, event.outcome)
                    self.assertNotIn(CONNECTION_ID, repr(event))
                    self.assertFalse(hasattr(event, "durable"))
                    self.assertFalse(hasattr(event, "payload"))
                finally:
                    await fixture.supervisor.shutdown(timeout_seconds=1)

    async def test_audit_failure_never_allows_security_action(self) -> None:
        fixture = await _active_audit_fixture()
        try:
            fixture.sink.failure = RuntimeError("audit-failure-secret")
            guard = NonResumableConnectionGuard(
                session_context=fixture.current,
                connection_index=fixture.index,
                clock=fixture.clock,
                audit_sink=DeterministicTestSecurityAuditSink(),
                lifecycle_audit=fixture.boundary,
                transport_session=fixture.transport,
            )

            with self.assertRaises(NsRuntimeStateStoreUnavailableError) as caught:
                await guard.close(NonResumableCloseKind.KICK)

            self.assertIs(LogicalConnectionState.CLOSED, fixture.machine.state)
            self.assertIsNone(await fixture.index.lookup_connection(CONNECTION_ID))
            self.assertEqual(
                "enforced",
                caught.exception.details["enforcement_outcome"],
            )
            audit = await fixture.boundary.snapshot()
            self.assertEqual(1, audit.failed_count)
        finally:
            await fixture.supervisor.shutdown(timeout_seconds=1)

    async def test_ordinary_heartbeat_never_enters_lifecycle_audit(self) -> None:
        fixture = await _active_audit_fixture()
        try:
            heartbeat = _heartbeat_service(
                context=fixture.current,
                index=fixture.index,
                transport=fixture.transport,
                clock=fixture.clock,
                supervisor=fixture.supervisor,
            )
            await heartbeat.start()
            await _wait_until(lambda: fixture.clock.pending_sleep_count == 2)

            await heartbeat.handle_text(_heartbeat(sequence=1))

            self.assertEqual((), fixture.sink.events)
            self.assertEqual(0, (await fixture.boundary.snapshot()).attempted_count)
        finally:
            await fixture.supervisor.shutdown(timeout_seconds=1)


class _BlockingHeartbeatService(ConnectionHeartbeatService):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.snapshot_started = asyncio.Event()
        self.snapshot_release = asyncio.Event()
        self.snapshot_calls = 0

    async def snapshot(self):
        self.snapshot_calls += 1
        if self.snapshot_calls == 1:
            self.snapshot_started.set()
            await self.snapshot_release.wait()
        return await super().snapshot()


class _HostileSnapshotError(RuntimeError):
    def __str__(self) -> str:
        return "snapshot-source-secret"

    def __repr__(self) -> str:
        return "snapshot-source-secret"


class _FailingHeartbeatService(ConnectionHeartbeatService):
    async def snapshot(self):
        raise _HostileSnapshotError()


@dataclasses.dataclass
class _ActiveAuditFixture:
    clock: ControlledClock
    supervisor: TaskSupervisor
    transport: _CaptureTransport
    current: object
    machine: object
    index: LocalConnectionIndex
    sink: DeterministicTestConnectionAuditSink
    boundary: ConnectionLifecycleAuditBoundary


async def _active_audit_fixture() -> _ActiveAuditFixture:
    clock = ControlledClock(utc_start=UTC_START)
    supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
    transport = _CaptureTransport()
    current = _context(transport, clock=clock)
    machine = await _authenticated_machine()
    index = LocalConnectionIndex()
    await index.add_authenticated(session_context=current, state_machine=machine)
    await index.transition(CONNECTION_ID, LogicalConnectionState.ACTIVE)
    sink = DeterministicTestConnectionAuditSink()
    return _ActiveAuditFixture(
        clock=clock,
        supervisor=supervisor,
        transport=transport,
        current=current,
        machine=machine,
        index=index,
        sink=sink,
        boundary=ConnectionLifecycleAuditBoundary(
            session_context=current,
            clock=clock,
            sink=sink,
        ),
    )


@dataclasses.dataclass
class _ResumeAuditFixture:
    supervisor: TaskSupervisor
    machine: object
    transport: _ResumeTransport
    sink: DeterministicTestConnectionAuditSink
    boundary: ConnectionLifecycleAuditBoundary
    coordinator: ConnectionResumeCoordinator


async def _resume_audit_fixture() -> _ResumeAuditFixture:
    clock = ControlledClock(utc_start=UTC_START)
    supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
    old_transport = _CaptureTransport()
    current = _context(old_transport, clock=clock)
    machine = await _authenticated_machine()
    index = LocalConnectionIndex()
    await index.add_authenticated(session_context=current, state_machine=machine)
    await index.transition(CONNECTION_ID, LogicalConnectionState.ACTIVE)
    mapping = LogicalConnectionTransportMap(
        session_context=current,
        transport_session=old_transport,
    )
    grace = ReconnectGraceService(
        session_context=current,
        connection_index=index,
        transport_mapping=mapping,
        clock=clock,
        task_supervisor=supervisor,
        task_sequence=146,
    )
    await grace.enter(
        transport_session_id=old_transport.identity.transport_session_id,
    )
    sink = DeterministicTestConnectionAuditSink()
    boundary = ConnectionLifecycleAuditBoundary(
        session_context=current,
        clock=clock,
        sink=sink,
    )
    new_transport = _ResumeTransport()
    coordinator = ConnectionResumeCoordinator(
        current_context=current,
        grace_service=grace,
        connection_index=index,
        transport_mapping=mapping,
        new_transport_session=new_transport,
        iam_adapter=_resume_adapter(clock),
        logical_identity_factory=LogicalSessionIdentityFactory(
            IdentifierFactory(
                uuid_factory=lambda: UUID(
                    "123e4567-e89b-42d3-a456-426614174111"
                ),
            ),
        ),
        accepted_builder=_builder(clock),
        clock=clock,
        task_supervisor=supervisor,
        task_sequence=147,
        timeout_seconds=10,
        audit_boundary=boundary,
    )
    return _ResumeAuditFixture(
        supervisor=supervisor,
        machine=machine,
        transport=new_transport,
        sink=sink,
        boundary=boundary,
        coordinator=coordinator,
    )


@dataclasses.dataclass
class _SnapshotFixture:
    supervisor: TaskSupervisor
    security: NonResumableConnectionGuard
    reader: SafeConnectionSnapshotReader


async def _snapshot_fixture() -> _SnapshotFixture:
    fixture = await _active_audit_fixture()
    security = NonResumableConnectionGuard(
        session_context=fixture.current,
        connection_index=fixture.index,
        clock=fixture.clock,
        audit_sink=DeterministicTestSecurityAuditSink(),
        lifecycle_audit=fixture.boundary,
        transport_session=fixture.transport,
    )
    return _SnapshotFixture(
        supervisor=fixture.supervisor,
        security=security,
        reader=SafeConnectionSnapshotReader(
            session_context=fixture.current,
            connection_index=fixture.index,
            clock=fixture.clock,
            security_guard=security,
        ),
    )


async def _wait_until(predicate) -> None:
    for _ in range(100):
        if predicate():
            return
        await asyncio.sleep(0)
    raise AssertionError("condition was not reached")


if __name__ == "__main__":
    unittest.main()
