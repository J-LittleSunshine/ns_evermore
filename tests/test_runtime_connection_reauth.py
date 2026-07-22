# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import dataclasses
import json
import unittest
from datetime import timedelta
from uuid import UUID

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import (
    NsRuntimeAuthContextForgedError,
    NsRuntimeEnvelopeSchemaError,
    NsRuntimeIamDeniedError,
    NsRuntimeIamTimeoutError,
    NsRuntimeSourceForgedError,
)
from ns_common.identifiers import IdentifierFactory
from ns_common.iam import IamPrincipalType
from ns_common.time import ControlledClock
from ns_runtime.connection import (
    ConnectionDrainService,
    ConnectionLifecycleAuditBoundary,
    ConnectionReauthCoordinator,
    ConnectionReauthEnvelopeHandler,
    ConnectionRoutingEligibility,
    DeterministicTestIamAdapter,
    DeterministicTestConnectionAuditSink,
    DrainPolicy,
    LocalConnectionIndex,
    LogicalConnectionCloseReason,
    LogicalConnectionState,
    ReauthEnvelopeBuilder,
    ReauthRejectionReason,
    SessionExpiryController,
    SessionExpiryPolicy,
    TestIamAction,
    TestIamOutcome,
)
from ns_runtime.protocol import JsonV1Codec

from tests.test_runtime_connection_accepted import _CaptureTransport
from tests.test_runtime_connection_binding import CONNECTION_ID, UTC_START, _context
from tests.test_runtime_connection_index import _authenticated_machine
from tests.test_runtime_connection_session import _authority


TOKEN = "reauth-top-secret-token"


class ConnectionReauthTestCase(unittest.IsolatedAsyncioTestCase):
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
        self.builder = _response_builder(self.clock)

    async def asyncTearDown(self) -> None:
        await self.supervisor.shutdown(timeout_seconds=1)

    def test_handler_uses_exact_p03_shape_and_redacts_token(self) -> None:
        handler = self._handler()

        parsed = handler.parse(_reauth_text())

        self.assertEqual(self.current.component_type, parsed.claims.component_type)
        self.assertEqual(
            frozenset({"runtime.connection", "runtime.management"}),
            parsed.claims.requested_capabilities,
        )
        self.assertTrue(parsed.credential.available)
        self.assertNotIn(TOKEN, repr(parsed) + repr(parsed.credential))

        for group in ("source", "auth_context"):
            with self.subTest(group=group):
                error = (
                    NsRuntimeSourceForgedError
                    if group == "source"
                    else NsRuntimeAuthContextForgedError
                )
                with self.assertRaises(error):
                    handler.parse(_reauth_text(**{group: {"forged": True}}))
        with self.assertRaises(NsRuntimeEnvelopeSchemaError):
            handler.parse(_reauth_text(extra_payload={"attacker": "value"}))
        with self.assertRaises(NsRuntimeEnvelopeSchemaError):
            handler.parse(_reauth_text(extensions={"attacker.reauth": {}}))

    async def test_success_refreshes_authority_without_changing_logical_session(self) -> None:
        authority = _renewed_authority()
        adapter = _adapter(self.clock, authority=authority)
        parsed = self._handler().parse(_reauth_text())

        result = await self._coordinator(adapter).reauthenticate(parsed)

        updated = result.context
        self.assertEqual(self.current.connection_id, updated.connection_id)
        self.assertEqual(self.current.session_id, updated.session_id)
        self.assertEqual(self.current.connection_epoch, updated.connection_epoch)
        self.assertEqual(self.current.created_at, updated.created_at)
        self.assertEqual("version:2", updated.permission_version)
        self.assertEqual(authority.expires_at, updated.session_expires_at)
        self.assertFalse(result.capabilities_changed)
        self.assertFalse(parsed.credential.available)
        self.assertEqual(1, adapter.call_count)
        self.assertEqual(1, adapter.consumed_credential_count)
        self.assertEqual(1, len(self.transport.sent))
        accepted = json.loads(self.transport.sent[0])
        self.assertEqual("connection.reauth_accepted", accepted["message"]["type"])
        self.assertEqual(
            {
                "session_id", "connection_epoch", "session_expires_at",
                "server_time", "capabilities_changed",
            },
            set(accepted["payload"]["inline"]),
        )
        self.assertNotIn(TOKEN, self.transport.sent[0] + repr(result))
        entry = await self.index.lookup_connection(CONNECTION_ID)
        assert entry is not None
        self.assertEqual(updated, entry.session_context)
        self.assertTrue(entry.active_target_eligible)
        self.assertEqual((), self.supervisor.pending_task_names)

    async def test_capability_shrink_rebuilds_index_and_preserves_drain(self) -> None:
        await self.index.transition(CONNECTION_ID, LogicalConnectionState.DRAINING)
        authority = _renewed_authority()
        parsed = self._handler().parse(
            _reauth_text(capabilities=["runtime.connection"]),
        )

        result = await self._coordinator(
            _adapter(self.clock, authority=authority),
        ).reauthenticate(parsed)

        self.assertTrue(result.capabilities_changed)
        self.assertEqual(frozenset({"runtime.connection"}), result.context.capabilities)
        snapshot = await self.index.snapshot()
        self.assertNotIn("runtime.management", snapshot.by_capability)
        entry = snapshot.by_connection_id[CONNECTION_ID]
        self.assertIs(LogicalConnectionState.DRAINING, entry.state)
        self.assertFalse(entry.active_target_eligible)

    async def test_unauthorized_capability_rejects_and_closes(self) -> None:
        authority = _renewed_authority(
            capabilities=frozenset({"runtime.connection"}),
        )
        parsed = self._handler().parse(
            _reauth_text(capabilities=["runtime.connection", "runtime.management"]),
        )

        with self.assertRaises(NsRuntimeIamDeniedError):
            await self._coordinator(
                _adapter(self.clock, authority=authority),
            ).reauthenticate(parsed)

        rejected = json.loads(self.transport.sent[0])
        self.assertEqual(
            ReauthRejectionReason.CAPABILITY_DENIED.value,
            rejected["payload"]["inline"]["reason"],
        )
        self.assertEqual(
            {"reason", "server_time", "connection_closing"},
            set(rejected["payload"]["inline"]),
        )
        self.assertIs(LogicalConnectionState.CLOSED, self.machine.state)
        self.assertIsNone(await self.index.lookup_connection(CONNECTION_ID))

    async def test_identity_tenant_component_and_expired_authority_are_fixed_rejections(self) -> None:
        cases = (
            ({"identity": "identity:attacker"}, ReauthRejectionReason.IDENTITY_MISMATCH),
            ({"tenant_id": "tenant:other"}, ReauthRejectionReason.IDENTITY_MISMATCH),
            ({"component_type": "node"}, ReauthRejectionReason.IDENTITY_MISMATCH),
            (
                {"principal_type": IamPrincipalType.BACKEND_SERVICE},
                ReauthRejectionReason.IDENTITY_MISMATCH,
            ),
            (
                {
                    "issued_at": UTC_START - timedelta(minutes=2),
                    "expires_at": UTC_START - timedelta(minutes=1),
                },
                ReauthRejectionReason.SESSION_EXPIRED,
            ),
        )
        for changes, expected_reason in cases:
            with self.subTest(reason=expected_reason.value, changes=changes):
                fixture = await _reauth_fixture()
                try:
                    authority = dataclasses.replace(
                        _renewed_authority(),
                        **changes,
                    )
                    parsed = fixture.handler.parse(_reauth_text())
                    with self.assertRaises(NsRuntimeIamDeniedError):
                        await fixture.coordinator(
                            _adapter(fixture.clock, authority=authority),
                        ).reauthenticate(parsed)
                    response = json.loads(fixture.transport.sent[0])
                    self.assertEqual(
                        expected_reason.value,
                        response["payload"]["inline"]["reason"],
                    )
                    self.assertIs(LogicalConnectionState.CLOSED, fixture.machine.state)
                finally:
                    await fixture.supervisor.shutdown(timeout_seconds=1)

    async def test_iam_denial_revokes_target_before_rejected_send(self) -> None:
        self.transport.send_release = asyncio.Event()
        adapter = DeterministicTestIamAdapter(
            (TestIamOutcome(action=TestIamAction.DENY),),
            clock=self.clock,
        )
        task = asyncio.create_task(
            self._coordinator(adapter).reauthenticate(
                self._handler().parse(_reauth_text()),
            ),
        )
        await self.transport.send_started.wait()

        entry = await self.index.lookup_connection(CONNECTION_ID)
        assert entry is not None
        self.assertIs(LogicalConnectionState.CLOSING, entry.state)
        self.assertFalse(entry.active_target_eligible)
        self.transport.send_release.set()
        with self.assertRaises(NsRuntimeIamDeniedError):
            await task
        response = json.loads(self.transport.sent[0])
        self.assertEqual("auth_denied", response["payload"]["inline"]["reason"])

    async def test_total_deadline_cancels_iam_rejects_and_clears_credential(self) -> None:
        adapter = DeterministicTestIamAdapter(
            (TestIamOutcome(action=TestIamAction.TIMEOUT),),
            clock=self.clock,
        )
        parsed = self._handler().parse(_reauth_text())
        task = asyncio.create_task(
            self._coordinator(adapter, timeout_seconds=10).reauthenticate(parsed),
        )
        await _wait_until(
            lambda: adapter.call_count == 1 and self.clock.pending_sleep_count >= 2,
        )

        self.clock.advance(10)
        with self.assertRaises(NsRuntimeIamTimeoutError) as context:
            await task

        self.assertEqual("reauth_total_deadline", context.exception.details["reason"])
        self.assertFalse(parsed.credential.available)
        self.assertEqual("auth_timeout", _response_reason(self.transport.sent[0]))
        self.assertEqual((), self.supervisor.pending_task_names)
        self.assertEqual(0, self.clock.pending_sleep_count)
        self.assertIs(LogicalConnectionCloseReason.AUTH_FAILED, self.machine.close_reason)

    async def test_cancellation_closes_shutdown_and_clears_credential(self) -> None:
        adapter = DeterministicTestIamAdapter(
            (TestIamOutcome(action=TestIamAction.CANCEL),),
            clock=self.clock,
        )
        parsed = self._handler().parse(_reauth_text())

        with self.assertRaises(asyncio.CancelledError):
            await self._coordinator(adapter).reauthenticate(parsed)

        self.assertFalse(parsed.credential.available)
        self.assertIs(LogicalConnectionCloseReason.SHUTDOWN, self.machine.close_reason)
        self.assertIsNone(await self.index.lookup_connection(CONNECTION_ID))

    async def test_accepted_send_failure_closes_without_publishing_new_authority(self) -> None:
        failure = RuntimeError("send-secret-must-not-be-rendered")
        self.transport.send_failure = failure
        parsed = self._handler().parse(_reauth_text())

        with self.assertRaises(RuntimeError) as context:
            await self._coordinator(
                _adapter(self.clock, authority=_renewed_authority()),
            ).reauthenticate(parsed)

        self.assertIs(failure, context.exception)
        self.assertIs(LogicalConnectionCloseReason.SEND_FAILED, self.machine.close_reason)
        self.assertIsNone(await self.index.lookup_connection(CONNECTION_ID))
        self.assertFalse(parsed.credential.available)

    def _handler(self) -> ConnectionReauthEnvelopeHandler:
        return ConnectionReauthEnvelopeHandler(
            session_context=self.current,
            codec=JsonV1Codec(),
        )

    def _coordinator(
        self,
        adapter: DeterministicTestIamAdapter,
        *,
        timeout_seconds: float = 30,
        expiry_controller: SessionExpiryController | None = None,
    ) -> ConnectionReauthCoordinator:
        return ConnectionReauthCoordinator(
            current_context=self.current,
            connection_index=self.index,
            transport_session=self.transport,
            iam_adapter=adapter,
            response_builder=self.builder,
            clock=self.clock,
            task_supervisor=self.supervisor,
            task_sequence=131,
            timeout_seconds=timeout_seconds,
            expected_principal_type=IamPrincipalType.CLIENT,
            expiry_controller=expiry_controller,
            audit_boundary=ConnectionLifecycleAuditBoundary(
                session_context=self.current,
                clock=self.clock,
                sink=DeterministicTestConnectionAuditSink(),
            ),
        )


class SessionExpiryControllerTestCase(unittest.IsolatedAsyncioTestCase):
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
        self.controller = SessionExpiryController(
            session_context=self.current,
            connection_index=self.index,
            transport_session=self.transport,
            clock=self.clock,
            task_supervisor=self.supervisor,
            task_sequence=132,
            policy=SessionExpiryPolicy(reauth_lead_seconds=60),
        )

    async def asyncTearDown(self) -> None:
        await self.supervisor.shutdown(timeout_seconds=1)

    async def test_lead_signal_then_expiry_closes_old_permission(self) -> None:
        await self.controller.start()
        await _wait_until(lambda: self.clock.pending_sleep_count == 1)

        self.clock.advance(240)
        await _wait_until(lambda: self.clock.pending_sleep_count == 1)
        lead = await self.controller.snapshot()
        self.assertTrue(lead.reauth_required)
        self.assertFalse(lead.expired)
        entry = await self.index.lookup_connection(CONNECTION_ID)
        assert entry is not None
        self.assertFalse(entry.active_target_eligible)
        self.assertIs(
            ConnectionRoutingEligibility.SESSION_EXPIRY_SUSPENDED,
            entry.routing_eligibility,
        )

        self.clock.advance(60)
        await _wait_until(lambda: self.machine.state is LogicalConnectionState.CLOSED)
        expired = await self.controller.snapshot()
        self.assertTrue(expired.expired)
        self.assertFalse(expired.deadline_pending)
        self.assertIs(LogicalConnectionCloseReason.AUTH_FAILED, self.machine.close_reason)
        self.assertIsNone(await self.index.lookup_connection(CONNECTION_ID))

    async def test_refresh_cancels_old_generation_and_extends_deadline(self) -> None:
        await self.controller.start()
        await _wait_until(lambda: self.clock.pending_sleep_count == 1)
        updated = dataclasses.replace(
            self.current,
            authorization_issued_at=UTC_START + timedelta(seconds=1),
            session_expires_at=UTC_START + timedelta(minutes=10),
            permission_version="version:2",
        )
        await self.index.replace_authority_context(
            updated,
            expected_session_context=self.current,
            allowed_states=frozenset({LogicalConnectionState.ACTIVE}),
        )

        await self.controller.refresh(updated)
        await _wait_until(lambda: self.clock.pending_sleep_count == 1)
        self.clock.advance(300)
        await asyncio.sleep(0)

        snapshot = await self.controller.snapshot()
        self.assertEqual(1, snapshot.generation)
        self.assertFalse(snapshot.expired)
        self.assertFalse(snapshot.reauth_required)
        self.assertIs(LogicalConnectionState.ACTIVE, self.machine.state)
        self.assertEqual(updated, (await self.index.lookup_connection(CONNECTION_ID)).session_context)  # type: ignore[union-attr]

    async def test_refresh_after_lead_atomically_restores_target(self) -> None:
        await self.controller.start()
        await _wait_until(lambda: self.clock.pending_sleep_count == 1)
        self.clock.advance(240)
        await _wait_until(lambda: self.clock.pending_sleep_count == 1)
        suspended = await self.index.lookup_connection(CONNECTION_ID)
        assert suspended is not None
        self.assertIs(
            ConnectionRoutingEligibility.SESSION_EXPIRY_SUSPENDED,
            suspended.routing_eligibility,
        )
        updated = dataclasses.replace(
            self.current,
            authorization_issued_at=UTC_START + timedelta(seconds=241),
            session_expires_at=UTC_START + timedelta(minutes=10),
            permission_version="version:restored",
        )
        await self.index.replace_authority_context(
            updated,
            expected_session_context=self.current,
            allowed_states=frozenset({LogicalConnectionState.ACTIVE}),
        )
        await self.controller.refresh(updated)
        restored = await self.index.lookup_connection(CONNECTION_ID)
        assert restored is not None
        self.assertTrue(restored.active_target_eligible)
        self.assertIs(
            ConnectionRoutingEligibility.ELIGIBLE,
            restored.routing_eligibility,
        )

    async def test_expiry_close_failure_is_non_target_and_retryable(self) -> None:
        self.transport.close_failures_remaining = 1
        await self.controller.start()
        await _wait_until(lambda: self.clock.pending_sleep_count == 1)

        self.clock.advance(300)
        await _wait_until(lambda: self.machine.state is LogicalConnectionState.CLOSING)

        entry = await self.index.lookup_connection(CONNECTION_ID)
        assert entry is not None
        self.assertFalse(entry.active_target_eligible)
        self.assertTrue((await self.controller.snapshot()).expired)
        self.assertTrue(await self.controller.retry_cleanup())
        self.assertIsNone(await self.index.lookup_connection(CONNECTION_ID))
        self.assertEqual(2, self.transport.close_calls)

    async def test_draining_expiry_converges_auth_failed_without_stale_deadline(self) -> None:
        drain = ConnectionDrainService(
            connection_id=CONNECTION_ID,
            connection_index=self.index,
            transport_session=self.transport,
            clock=self.clock,
            task_supervisor=self.supervisor,
            task_sequence=134,
            policy=DrainPolicy(timeout_seconds=600),
        )
        controller = SessionExpiryController(
            session_context=self.current,
            connection_index=self.index,
            transport_session=self.transport,
            clock=self.clock,
            task_supervisor=self.supervisor,
            task_sequence=135,
            policy=SessionExpiryPolicy(reauth_lead_seconds=60),
            drain_service=drain,
        )
        await controller.start()
        await drain.begin()
        await _wait_until(lambda: self.clock.pending_sleep_count == 2)

        self.clock.advance(240)
        await asyncio.sleep(0)
        self.clock.advance(60)
        await _wait_until(lambda: self.machine.state is LogicalConnectionState.CLOSED)
        await drain.wait_closed()

        snapshot = await drain.snapshot()
        self.assertIs(LogicalConnectionCloseReason.AUTH_FAILED, snapshot.terminal_reason)
        self.assertFalse(snapshot.timeout_pending)
        self.clock.advance(600)
        await asyncio.sleep(0)
        self.assertIs(
            LogicalConnectionCloseReason.AUTH_FAILED,
            (await drain.snapshot()).terminal_reason,
        )
        self.assertIs(LogicalConnectionCloseReason.AUTH_FAILED, self.machine.close_reason)
        self.assertFalse(any(
            name.startswith("logical-drain-")
            for name in self.supervisor.pending_task_names
        ))


@dataclasses.dataclass
class _ReauthFixture:
    clock: ControlledClock
    supervisor: TaskSupervisor
    transport: _CaptureTransport
    current: object
    machine: object
    index: LocalConnectionIndex
    handler: ConnectionReauthEnvelopeHandler
    builder: ReauthEnvelopeBuilder

    def coordinator(self, adapter) -> ConnectionReauthCoordinator:
        return ConnectionReauthCoordinator(
            current_context=self.current,
            connection_index=self.index,
            transport_session=self.transport,
            iam_adapter=adapter,
            response_builder=self.builder,
            clock=self.clock,
            task_supervisor=self.supervisor,
            task_sequence=133,
            timeout_seconds=30,
            expected_principal_type=IamPrincipalType.CLIENT,
            audit_boundary=ConnectionLifecycleAuditBoundary(
                session_context=self.current,
                clock=self.clock,
                sink=DeterministicTestConnectionAuditSink(),
            ),
        )


async def _reauth_fixture() -> _ReauthFixture:
    clock = ControlledClock(utc_start=UTC_START)
    supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
    transport = _CaptureTransport()
    current = _context(transport, clock=clock)
    machine = await _authenticated_machine()
    index = LocalConnectionIndex()
    await index.add_authenticated(session_context=current, state_machine=machine)
    await index.transition(CONNECTION_ID, LogicalConnectionState.ACTIVE)
    return _ReauthFixture(
        clock=clock,
        supervisor=supervisor,
        transport=transport,
        current=current,
        machine=machine,
        index=index,
        handler=ConnectionReauthEnvelopeHandler(
            session_context=current,
            codec=JsonV1Codec(),
        ),
        builder=_response_builder(clock),
    )


def _renewed_authority(
    *,
    capabilities: frozenset[str] = frozenset({
        "runtime.connection",
        "runtime.management",
    }),
):
    return dataclasses.replace(
        _authority(capabilities=capabilities),
        permissions={capability: True for capability in capabilities},
        permission_snapshot_ref="permission:snapshot-renewed",
        permission_digest="sha256:permission-renewed",
        permission_version="version:2",
        issued_at=UTC_START + timedelta(seconds=1),
        expires_at=UTC_START + timedelta(minutes=10),
    )


def _adapter(clock: ControlledClock, *, authority):
    return DeterministicTestIamAdapter(
        (TestIamOutcome(action=TestIamAction.ALLOW, authority=authority),),
        clock=clock,
    )


def _response_builder(clock: ControlledClock) -> ReauthEnvelopeBuilder:
    return ReauthEnvelopeBuilder(
        clock=clock,
        identifier_factory=IdentifierFactory(
            uuid_factory=lambda: UUID("123e4567-e89b-42d3-a456-426614174099"),
        ),
    )


def _reauth_text(
    *,
    capabilities=None,
    extra_payload=None,
    extensions=None,
    source=None,
    auth_context=None,
) -> str:
    payload = {"token": TOKEN}
    if capabilities is not None:
        payload["requested_capabilities"] = capabilities
    if extra_payload is not None:
        payload.update(extra_payload)
    value = {
        "protocol": {"major": 1, "minor": 0, "patch": 0},
        "message": {
            "message_id": "message_00000000000000000000000000000001",
            "type": "connection.reauth",
            "category": "connection",
            "priority": 0,
            "created_at": "2026-07-21T00:00:00Z",
            "reliability": "best_effort",
        },
        "payload": {"mode": "inline", "inline": payload},
    }
    for key, item in (
        ("extensions", extensions),
        ("source", source),
        ("auth_context", auth_context),
    ):
        if item is not None:
            value[key] = item
    return json.dumps(value, separators=(",", ":"))


def _response_reason(text: str) -> str:
    return json.loads(text)["payload"]["inline"]["reason"]


async def _wait_until(predicate) -> None:
    for _ in range(80):
        if predicate():
            return
        await asyncio.sleep(0)
    raise AssertionError("condition was not reached")


if __name__ == "__main__":
    unittest.main()
