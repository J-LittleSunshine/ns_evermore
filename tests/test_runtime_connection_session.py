# -*- coding: utf-8 -*-
from __future__ import annotations

import dataclasses
import unittest
from datetime import datetime, timedelta, timezone

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import (
    NsRuntimeIamDeniedError,
    NsRuntimeProtocolVersionError,
    NsRuntimeTransportCapabilityUnavailableError,
)
from ns_common.time import ControlledClock
from ns_common.iam import IamPrincipalType
from ns_runtime.connection import (
    CapabilityPolicy,
    CapabilityRule,
    ConnectionHandshakeAuthenticator,
    ConnectionHelloReceiver,
    DeterministicTestIamAdapter,
    HandshakeIamAuthority,
    HandshakeSessionNegotiator,
    HelloClaimParser,
    LogicalConnectionCloseReason,
    LogicalConnectionState,
    LogicalConnectionStateMachine,
    LogicalSessionIdentity,
    NegotiatedSession,
    P05_CAPABILITY_POLICY,
    PendingHelloClaims,
    SessionContext,
    TestIamAction,
    TestIamOutcome,
)
from ns_runtime.protocol import (
    JsonV1Codec,
    ProtocolCompatibilityMatrix,
    ProtocolVersion,
    ProtocolVersionSupport,
    WIRE_CODEC_JSON_V1,
)
from ns_runtime.transport import (
    TransportCapabilities,
    TransportCapability,
    WEBSOCKET_TCP_CAPABILITIES,
)

from tests.test_runtime_connection_authentication import _hello
from tests.test_runtime_connection_handshake import _FakeTransportSession


UTC_START = datetime(2026, 7, 21, tzinfo=timezone.utc)
CONNECTION_ID = "connection_123e4567e89b42d3a456426614174000"
SESSION_ID = "session_123e4567e89b42d3a456426614174001"


class SessionNegotiationTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.clock = ControlledClock(utc_start=UTC_START)
        self.supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        self.transport = _FakeTransportSession(
            capabilities=WEBSOCKET_TCP_CAPABILITIES,
        )
        self.machine = LogicalConnectionStateMachine()

    async def asyncTearDown(self) -> None:
        await self.supervisor.shutdown(timeout_seconds=1)

    async def test_handshake_negotiates_sc1_before_active(self) -> None:
        authority = _authority()
        authenticator = self._authenticator(authority)
        await self.transport.messages.put(_hello())

        result = await authenticator.authenticate()

        self.assertIsInstance(result, NegotiatedSession)
        assert isinstance(result, NegotiatedSession)
        context = result.context
        self.assertIs(LogicalConnectionState.AUTHENTICATED, self.machine.state)
        self.assertIs(LogicalConnectionState.AUTHENTICATED, context.established_state)
        self.assertEqual(ProtocolVersion(1, 0, 0), context.protocol_version)
        self.assertEqual("json.v1/protocol-1.0", context.protocol_schema_key)
        self.assertEqual(WIRE_CODEC_JSON_V1, context.wire_codec)
        self.assertEqual(
            frozenset({"runtime.connection", "runtime.management"}),
            context.capabilities,
        )
        self.assertEqual(result.protocol.selected, context.protocol_version)
        self.assertFalse(result.protocol.downgraded)
        self.assertEqual((), self.supervisor.pending_task_names)

    async def test_requested_capability_cannot_exceed_iam_authority(self) -> None:
        authenticator = self._authenticator(
            _authority(capabilities=frozenset({"runtime.connection"})),
        )
        await self.transport.messages.put(_hello())

        with self.assertRaises(NsRuntimeIamDeniedError) as context:
            await authenticator.authenticate()

        self.assertEqual(
            "requested_capability_not_authorized",
            context.exception.details["reason"],
        )
        self.assertIs(LogicalConnectionCloseReason.PROTOCOL_FAILED, self.machine.close_reason)

    async def test_adapter_transport_capabilities_are_authoritative(self) -> None:
        self.transport = _FakeTransportSession(capabilities=TransportCapabilities())
        authenticator = self._authenticator(_authority())
        await self.transport.messages.put(_hello())

        with self.assertRaises(NsRuntimeTransportCapabilityUnavailableError):
            await authenticator.authenticate()

        self.assertIs(LogicalConnectionCloseReason.PROTOCOL_FAILED, self.machine.close_reason)

    async def test_protocol_matrix_is_authoritative(self) -> None:
        matrix = ProtocolCompatibilityMatrix((
            ProtocolVersionSupport(
                ProtocolVersion(2, 0, 0),
                "json.v1/protocol-2.0",
            ),
        ))
        authenticator = self._authenticator(_authority(), protocol_matrix=matrix)
        await self.transport.messages.put(_hello())

        with self.assertRaises(NsRuntimeProtocolVersionError) as context:
            await authenticator.authenticate()

        self.assertEqual("major_not_supported", context.exception.details["reason"])
        self.assertIs(LogicalConnectionCloseReason.PROTOCOL_FAILED, self.machine.close_reason)

    def test_unknown_capability_fails_instead_of_becoming_authority(self) -> None:
        negotiator = self._negotiator()
        claims = _claims(frozenset({"runtime.unregistered"}))
        authority = _authority(capabilities=frozenset({"runtime.unregistered"}))

        with self.assertRaises(NsRuntimeProtocolVersionError) as context:
            negotiator.negotiate(claims=claims, authority=authority)

        self.assertEqual("capability_not_registered", context.exception.details["reason"])

    def test_capability_protocol_binding_is_strict(self) -> None:
        policy = CapabilityPolicy((
            CapabilityRule(
                name="runtime.connection",
                schema_keys=frozenset({"json.v1/protocol-2.0"}),
                required_transport_capabilities=frozenset({
                    TransportCapability.RELIABLE_ORDERED_MESSAGES,
                }),
            ),
        ))
        negotiator = self._negotiator(capability_policy=policy)

        with self.assertRaises(NsRuntimeProtocolVersionError) as context:
            negotiator.negotiate(
                claims=_claims(frozenset({"runtime.connection"})),
                authority=_authority(
                    capabilities=frozenset({"runtime.connection"}),
                ),
            )

        self.assertEqual(
            "capability_protocol_incompatible",
            context.exception.details["reason"],
        )

    def test_sc1_is_exactly_typed_frozen_slotted_and_deeply_immutable(self) -> None:
        authority = _authority()
        result = self._negotiator().negotiate(
            claims=_claims(),
            authority=authority,
        )
        context = result.context

        self.assertEqual(
            {
                "connection_id", "session_id", "connection_epoch", "identity",
                "tenant_id", "component_type", "protocol_version",
                "protocol_schema_key", "wire_codec", "capabilities",
                "permission_snapshot_ref", "permission_digest",
                "permission_version", "iam_mode", "authorization_issued_at",
                "session_expires_at", "resume_eligible", "established_state",
                "created_at",
            },
            {item.name for item in dataclasses.fields(SessionContext)},
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            context.connection_epoch = 9  # type: ignore[misc]
        with self.assertRaises((AttributeError, TypeError)):
            context.transport = self.transport  # type: ignore[attr-defined]
        self.assertIsInstance(context.capabilities, frozenset)
        self.assertNotIn("permissions", {item.name for item in dataclasses.fields(context)})
        combined = repr(context) + repr(result) + repr(authority)
        for secret in (
            CONNECTION_ID,
            SESSION_ID,
            "identity:test-user",
            "tenant:test",
            "permission:snapshot-test",
            "sha256:permission-test",
        ):
            self.assertNotIn(secret, combined)

    def test_sc1_detaches_from_full_permission_snapshot(self) -> None:
        mutable_permissions = {"runtime.connection": True}
        authority = _authority(permissions=mutable_permissions)
        result = self._negotiator().negotiate(
            claims=_claims(frozenset({"runtime.connection"})),
            authority=authority,
        )
        mutable_permissions["runtime.connection"] = False

        self.assertEqual(
            frozenset({"runtime.connection"}),
            result.context.capabilities,
        )
        self.assertFalse(hasattr(result.context, "permissions"))

    def test_logical_identity_is_separate_from_transport_identity(self) -> None:
        result = self._negotiator().negotiate(
            claims=_claims(),
            authority=_authority(),
        )
        context = result.context

        self.assertNotEqual(context.connection_id, self.transport.identity.transport_connection_id)
        self.assertNotEqual(context.session_id, self.transport.identity.transport_session_id)
        field_names = {item.name for item in dataclasses.fields(context)}
        self.assertFalse(any(name.startswith("transport_") for name in field_names))
        self.assertNotIn("path", field_names)

    def test_capability_policy_is_immutable_and_websocket_contract_suffices(self) -> None:
        self.assertEqual(
            {
                "runtime.connection", "runtime.heartbeat", "runtime.resume",
                "runtime.management",
            },
            {rule.name for rule in P05_CAPABILITY_POLICY.rules},
        )
        self.assertTrue(
            WEBSOCKET_TCP_CAPABILITIES.supports(
                TransportCapability.RELIABLE_ORDERED_MESSAGES,
            ),
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            P05_CAPABILITY_POLICY._rules = ()  # type: ignore[misc]

    def _authenticator(
        self,
        authority: HandshakeIamAuthority,
        *,
        protocol_matrix=None,
    ) -> ConnectionHandshakeAuthenticator:
        receiver = ConnectionHelloReceiver(
            transport_session=self.transport,
            state_machine=self.machine,
            clock=self.clock,
            task_supervisor=self.supervisor,
            task_sequence=41,
            timeout_seconds=10,
            codec=JsonV1Codec(),
        )
        negotiator = self._negotiator(protocol_matrix=protocol_matrix)
        adapter = DeterministicTestIamAdapter(
            (TestIamOutcome(action=TestIamAction.ALLOW, authority=authority),),
            clock=self.clock,
        )
        return ConnectionHandshakeAuthenticator(
            hello_receiver=receiver,
            claim_parser=HelloClaimParser(),
            iam_adapter=adapter,
            clock=self.clock,
            task_supervisor=self.supervisor,
            task_sequence=41,
            timeout_seconds=10,
            session_negotiator=negotiator,
        )

    def _negotiator(
        self,
        *,
        protocol_matrix=None,
        capability_policy: CapabilityPolicy = P05_CAPABILITY_POLICY,
    ) -> HandshakeSessionNegotiator:
        kwargs = {}
        if protocol_matrix is not None:
            kwargs["protocol_matrix"] = protocol_matrix
        return HandshakeSessionNegotiator(
            transport_session=self.transport,
            logical_identity=LogicalSessionIdentity(
                connection_id=CONNECTION_ID,
                session_id=SESSION_ID,
                connection_epoch=0,
            ),
            clock=self.clock,
            capability_policy=capability_policy,
            **kwargs,
        )


def _claims(
    capabilities: frozenset[str] = frozenset({
        "runtime.connection",
        "runtime.management",
    }),
) -> PendingHelloClaims:
    return PendingHelloClaims(
        component_type="client",
        requested_version=ProtocolVersion(1, 0, 0),
        minimum_version=ProtocolVersion(1, 0, 0),
        requested_capabilities=capabilities,
    )


def _authority(
    *,
    capabilities: frozenset[str] = frozenset({
        "runtime.connection",
        "runtime.management",
    }),
    permissions=None,
) -> HandshakeIamAuthority:
    return HandshakeIamAuthority(
        identity="identity:test-user",
        tenant_id="tenant:test",
        component_type="client",
        principal_type=IamPrincipalType.CLIENT,
        capabilities=capabilities,
        permissions=(
            {capability: True for capability in capabilities}
            if permissions is None
            else permissions
        ),
        permission_snapshot_ref="permission:snapshot-test",
        permission_digest="sha256:permission-test",
        permission_version="version:1",
        issued_at=UTC_START,
        expires_at=UTC_START + timedelta(minutes=5),
        resume_eligible=True,
        iam_mode="test",
    )


if __name__ == "__main__":
    unittest.main()
