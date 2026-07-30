# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import dataclasses
import asyncio
from datetime import datetime, timedelta, timezone
import os
import signal
import tempfile
import threading
import time
import unittest
from unittest import mock

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import (
    NsRuntimeIamUnavailableError,
    NsRuntimeStateStoreCapabilityUnavailableError,
    NsRuntimeStateStoreIndeterminateWriteError,
    NsRuntimeStateStoreUnavailableError,
    NsValidationError,
)
from ns_common.config import NsRuntimeStateStoreConfig
from ns_common.http_client import NsAsyncHttpClient, NsHttpClientOwner
from ns_common.iam import (
    IamAccessCheckRequest,
    IamAccessDecision,
    IamCredentialStatus,
    IamIntrospectionResult,
    IamPrincipalType,
    IamTargetContext,
    PayloadRefRevalidationDecision,
    PayloadRefRevalidationRequest,
)
from ns_common.state_store import (
    StateAssertion,
    StateDocument,
    StateKey,
    StateMutation,
    StateMutationKind,
    StateNamespace,
    StateNamespaceKind,
    StateRecord,
    StateRecordReadAssertion,
    StateRevision,
    create_state_store_provider,
)
from ns_common.time import ControlledClock, SystemClock
import ns_runtime.authority_broker as broker_module
from ns_runtime.authority_broker import (
    AuthorityBrokerConfig,
    BrokerAuthorityHandle,
    BrokerDelegationCertificate,
    BrokerIamVerificationReceipt,
    BrokerInstanceCertificate,
    BrokerRepositoryRole,
    BrokerSignedIamResult,
    AdmissionRepositoryProxy,
    ProductionIamAuthorityProxy,
    start_contract_test_authority_broker,
    start_production_authority_broker,
)
from ns_runtime.delivery.scheduling import (
    LocalDeliveryTarget,
    PayloadAccessDecisionEvidence,
    _PayloadAccessEvidenceIssuer,
)
from ns_runtime.delivery.models import DeliveryRecord, PayloadEvidence, PayloadKind
from ns_runtime.delivery.payload_authority import (
    IamDeliveryPayloadReferenceValidator,
)
from ns_runtime.authority_attestor import (
    AuthorityAttestationError,
    start_authority_attestor,
)
import ns_runtime.authority_attestor as attestor_module
import ns_runtime.processor.integration as processor_integration_module
from ns_runtime.authority_wire import (
    MAX_FRAME_BYTES,
    decode_frame,
    encode_frame,
    require_object,
)
from ns_runtime.authority_bootstrap import load_inherited_authority_bootstrap
from ns_runtime.context import RuntimeDependencySlots
from ns_runtime.delivery_persistence import (
    DeliveryPersistencePartition,
    DeliveryPersistenceTransaction,
    DeliveryPersistenceTransactionResult,
)
from ns_runtime.iam import (
    AuthorizationMode,
    IamClient,
    MessageAuthorizationService,
    OperationRiskContext,
    PermissionSnapshot,
)
from ns_runtime.iam.authorization import MessageAuthorizationResult
from ns_runtime.processor import (
    AuthorizationDecisionEvidence,
    DefaultProcessorErrorMapper,
    DeterministicTestAuditSink,
    EventBus,
    InterfaceOnlyIdempotencyPrecheck,
    InterfaceOnlyRateLimitEntry,
    InterfaceOnlyRoutingPreparation,
    PassthroughResponseFinalizer,
    ProcessorContext,
    ProcessorDependencies,
    ProcessorTraceReference,
)
from ns_runtime.processor.contracts import (
    AuthorizationDecisionOutcome,
    _ProductionAuthorizationEvidenceIssuer,
)
from ns_runtime.processor.integration import IamProcessorAuthorization

from tests.test_runtime_iam_client import _HttpServer
from tests.test_runtime_processor_pipeline import (
    NOW as PROCESSOR_NOW,
    _envelope as _processor_envelope,
    _session as _processor_session,
)


def _config(base_url: str, *, runtime_id: str = "runtime:broker-test"):
    return AuthorityBrokerConfig(
        iam_base_url=base_url,
        iam_timeout_seconds=1.0,
        iam_mode="strict",
        permission_snapshot_ttl_seconds=60.0,
        state_backend="sqlite",
        state_endpoint="",
        state_username="",
        state_namespace="broker-unit-test",
        state_operation_timeout_seconds=1.0,
        runtime_id=runtime_id,
    )


def _access_request(*, message_type: str = "connection.heartbeat"):
    return IamAccessCheckRequest(
        identity="identity:1",
        tenant_id="tenant:1",
        permission_snapshot_ref="permission:1",
        permission_version="version:1",
        message_type=message_type,
        target=IamTargetContext(kind="identity", tenant_id="tenant:1"),
    )


def _decision(request: IamAccessCheckRequest) -> IamAccessDecision:
    now = datetime.now(timezone.utc)
    return IamAccessDecision(
        allowed=True,
        reason="backend_allow",
        permission_version=request.permission_version,
        decided_at=now,
    )


def _authorization_snapshot(
    *,
    now: datetime | None = None,
) -> PermissionSnapshot:
    issued = now or datetime.now(timezone.utc)
    return PermissionSnapshot.from_introspection(
        IamIntrospectionResult(
            identity="identity:1",
            tenant_id="tenant:1",
            principal_type=IamPrincipalType.CLIENT,
            component_type="client",
            capabilities=frozenset({"runtime.connection"}),
            permission_snapshot_ref="permission:1",
            permission_digest="sha256:broker-snapshot",
            permission_version="version:1",
            issued_at=issued - timedelta(seconds=1),
            expires_at=issued + timedelta(minutes=5),
            credential_status=IamCredentialStatus.ACTIVE,
            resume_eligible=True,
        ),
        iam_mode="cache",
    )


def _test_certificate(
    signer_private_key: Ed25519PrivateKey,
    session_public_key: bytes,
    *,
    instance_id: str = "broker_test",
    runtime_id: str = "runtime:test",
    issued_at: datetime | None = None,
    expires_at: datetime | None = None,
    delegation_fingerprint: str = "sha256:" + "0" * 64,
) -> BrokerInstanceCertificate:
    issued = issued_at or datetime.now(timezone.utc)
    expires = expires_at or issued + timedelta(minutes=4)
    values = {
        "trust_realm": "contract-test",
        "broker_instance_id": instance_id,
        "session_public_key": broker_module.encode_bytes(
            session_public_key,
        ),
        "runtime_id": runtime_id,
        "lifecycle_generation": 1,
        "delegation_fingerprint": delegation_fingerprint,
        "issued_at": broker_module.encode_time(issued),
        "expires_at": broker_module.encode_time(expires),
        "nonce": "certificate-nonce",
    }
    return BrokerInstanceCertificate(
        trust_realm="contract-test",
        broker_instance_id=instance_id,
        session_public_key=session_public_key,
        runtime_id=runtime_id,
        lifecycle_generation=1,
        delegation_fingerprint=delegation_fingerprint,
        issued_at=issued,
        expires_at=expires,
        nonce="certificate-nonce",
        signature=signer_private_key.sign(broker_module._canonical(values)),
    )


class _FakeProcess:
    def __init__(self) -> None:
        self.running = True
        self.terminated = False
        self.killed = False

    def is_alive(self) -> bool:
        return self.running

    def join(self, timeout=None) -> None:
        del timeout

    def terminate(self) -> None:
        self.terminated = True
        self.running = False

    def kill(self) -> None:
        self.killed = True
        self.running = False


class _FakeConnection:
    def __init__(self, response) -> None:
        self.response = response
        self.sent: bytes | None = None
        self.closed = False

    def send_bytes(self, value: bytes) -> None:
        self.sent = value

    def poll(self, timeout: float) -> bool:
        del timeout
        return True

    def recv_bytes(self, maximum: int) -> bytes:
        del maximum
        return self.response(self.sent)

    def close(self) -> None:
        self.closed = True


class _RotationResponseMutator:
    def __init__(self, connection, mutate) -> None:
        self._connection = connection
        self._mutate = mutate
        self._rotation_pending = False
        self.sent_kinds: list[str] = []
        self.saw_rotation_response = False

    @property
    def closed(self) -> bool:
        return self._connection.closed

    def send_bytes(self, value: bytes) -> None:
        message = decode_frame(value)
        kind = message.get("kind") if type(message) is dict else ""
        self.sent_kinds.append(str(kind))
        self._rotation_pending = kind == "rotate_session"
        self._connection.send_bytes(value)

    def poll(self, timeout: float) -> bool:
        return self._connection.poll(timeout)

    def recv_bytes(self, maximum: int) -> bytes:
        raw = self._connection.recv_bytes(maximum)
        if not self._rotation_pending:
            return raw
        self._rotation_pending = False
        self.saw_rotation_response = True
        message = decode_frame(raw)
        assert type(message) is dict
        return encode_frame(self._mutate(message))

    def close(self) -> None:
        self._connection.close()


def _test_channel(
    response,
    *,
    role: BrokerRepositoryRole = BrokerRepositoryRole.LIFECYCLE,
    diagnostics_enabled: bool = False,
):
    root = Ed25519PrivateKey.generate()
    root_public_key = root.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    attestor = start_authority_attestor(
        realm="contract-test",
        expected_test_root_public_key=root_public_key,
        diagnostics_enabled=diagnostics_enabled,
    )
    delegation_signer = Ed25519PrivateKey.generate()
    delegation_public_key = delegation_signer.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    session = Ed25519PrivateKey.generate()
    public_key = session.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    now = datetime.now(timezone.utc)
    delegation_values = {
        "trust_realm": "contract-test",
        "broker_instance_id": "broker_test",
        "runtime_id": "runtime:test",
        "delegation_public_key": broker_module.encode_bytes(
            delegation_public_key,
        ),
        "attestor_instance_id": attestor.instance_id,
        "attestor_public_key": broker_module.encode_bytes(
            attestor.public_key,
        ),
        "allowed_usages": list(broker_module._DELEGATION_USAGES),
        "issued_at": broker_module.encode_time(now),
        "expires_at": broker_module.encode_time(
            now + timedelta(hours=1),
        ),
        "nonce": "delegation-nonce",
    }
    delegation = BrokerDelegationCertificate(
        trust_realm="contract-test",
        broker_instance_id="broker_test",
        runtime_id="runtime:test",
        delegation_public_key=delegation_public_key,
        attestor_instance_id=attestor.instance_id,
        attestor_public_key=attestor.public_key,
        allowed_usages=broker_module._DELEGATION_USAGES,
        issued_at=now,
        expires_at=now + timedelta(hours=1),
        nonce="delegation-nonce",
        signature=root.sign(broker_module._canonical(delegation_values)),
    )
    certificate = _test_certificate(
        delegation_signer,
        public_key,
        delegation_fingerprint=delegation.fingerprint,
    )
    endpoints = {
        item.value: "endpoint_" + item.value
        for item in BrokerRepositoryRole
    }
    handles = {
        role.value: broker_module._new_handle(
            private_key=session,
            instance_id=certificate.broker_instance_id,
            endpoint_id=endpoints[role.value],
            role=role,
            runtime_id=certificate.runtime_id,
            generation=certificate.lifecycle_generation,
        )
        for role in BrokerRepositoryRole
    }
    approved = attestor.approve_identity(
        realm="contract-test",
        runtime_id=certificate.runtime_id,
        delegation_certificate=(
            broker_module._encode_delegation_certificate(delegation)
        ),
        session_certificate=broker_module._encode_certificate(certificate),
        handles={
            name: broker_module._encode_handle(handle)
            for name, handle in handles.items()
        },
        endpoints=endpoints,
    )
    process = _FakeProcess()
    custodian = broker_module._BrokerProcessCustodian(
        process=process,
        attestor=attestor,
    )
    connection = _FakeConnection(response)
    channel = broker_module._ContractTestRoleBrokerChannel(
        connection=connection,
        custodian=custodian,
        public_key=public_key,
        instance_id=certificate.broker_instance_id,
        runtime_id=certificate.runtime_id,
        lifecycle_generation=certificate.lifecycle_generation,
        certificate=certificate,
        delegation_certificate=delegation,
        attestor=attestor,
        identity_id=approved["identity_id"],
        endpoint_id=endpoints[role.value],
        role=role,
        handle=handles[role.value],
        timeout_seconds=0.1,
        diagnostics_enabled=diagnostics_enabled,
    )
    return channel, process, connection, session, certificate


def _signed_response_bytes(
    sent: bytes | None,
    *,
    session: Ed25519PrivateKey,
    certificate: BrokerInstanceCertificate,
    response_sequence: int,
    operation: str | None = None,
    response_handle: BrokerAuthorityHandle | None = None,
    result: object = None,
    error: object = None,
) -> bytes:
    assert sent is not None
    request = decode_frame(sent)
    assert type(request) is dict
    ticket = request["attestation"]
    assert type(ticket) is dict
    request_handle = BrokerAuthorityHandle(
        broker_instance_id=certificate.broker_instance_id,
        endpoint_id=ticket["endpoint_id"],
        handle_id=ticket["handle_id"],
        role=BrokerRepositoryRole(ticket["role"]),
        runtime_id=certificate.runtime_id,
        lifecycle_generation=certificate.lifecycle_generation,
        signature=b"response-helper",
    )
    signed = broker_module._sign_state_response(
        private_key=session,
        certificate=certificate,
        request_id=request["request_id"],
        request_sequence=request["request_sequence"],
        operation=operation or request["operation"],
        handle=response_handle or request_handle,
        request_fingerprint=broker_module._state_request_fingerprint(
            operation=request["operation"],
            handle=request_handle,
            payload=request["payload"],
        ),
        response_sequence=response_sequence,
        result=({"status": "ok"} if result is None and error is None else result),
        error=error,
        now=datetime.now(timezone.utc),
    )
    return encode_frame(broker_module._signed_response_envelope(signed))


class RuntimeAuthorityBrokerTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_state_store_proxy_close_retries_before_marking_closed(
        self,
    ) -> None:
        failure = RuntimeError("channel close failed once")

        class Channel:
            def __init__(self) -> None:
                self.close_calls = 0

            def close(self) -> None:
                self.close_calls += 1
                if self.close_calls == 1:
                    raise failure

        channel = Channel()
        proxy = object.__new__(
            broker_module.AuthorityBrokerStateStoreProxy,
        )
        proxy._channel = channel
        proxy._handle = None
        proxy._state = "open"

        with self.assertRaises(RuntimeError) as raised:
            await proxy.close()

        self.assertIs(failure, raised.exception)
        self.assertEqual("open", proxy._state)
        self.assertEqual(1, channel.close_calls)
        await proxy.close()
        self.assertEqual("closed", proxy._state)
        self.assertEqual(2, channel.close_calls)

    async def _broker(
        self,
        outcomes: list[object],
        *,
        session_ttl_seconds: float = 300.0,
    ):
        server = _HttpServer(outcomes)
        base_url = await server.start()
        broker = start_contract_test_authority_broker(
            config=_config(base_url),
            iam_service_credential="s" * 32,
            startup_timeout_seconds=30.0,
            session_ttl_seconds=session_ttl_seconds,
            delegation_ttl_seconds=max(
                30.0, session_ttl_seconds * 10,
            ),
            broker_operation_timeout_seconds=30.0,
        )
        self.addAsyncCleanup(server.close)
        self.addCleanup(broker.close)
        return broker, server

    def _close_broker_and_assert_reaped(self, broker) -> None:
        channels = tuple(
            proxy._channel
            for proxy in (
                broker.iam,
                broker.repositories.admission,
                broker.repositories.scheduler,
                broker.repositories.payload,
                broker.repositories.registry,
                broker.repositories.audit,
                broker.state_store,
            )
        )
        custodian = broker._channel._custodian
        attestor = custodian.attestor
        broker_process = custodian.process
        attestor_process = attestor._process
        broker.close()
        self.assertFalse(broker_process.is_alive())
        self.assertIsNotNone(broker_process.exitcode)
        self.assertFalse(attestor_process.is_alive())
        self.assertIsNotNone(attestor_process.exitcode)
        self.assertFalse(attestor.alive)
        self.assertTrue(custodian._reaped)
        self.assertTrue(custodian._process_reaped)
        self.assertTrue(custodian._attestor_closed)
        self.assertEqual((), custodian._endpoint_close_resources)
        self.assertTrue(attestor._connection_closed)
        self.assertTrue(attestor._process_reaped)
        self.assertTrue(attestor._reaped)
        self.assertTrue(all(channel._connection.closed for channel in channels))

    @staticmethod
    def _admission_transaction(
        broker,
        *,
        suffix: str,
    ) -> DeliveryPersistenceTransaction:
        partition = broker.repositories.admission.delivery_scope(
            tenant_id="tenant:lag",
            bucket_id=0,
            layout_generation=1,
        )
        return DeliveryPersistenceTransaction(
            partition=partition,
            mutations=(StateMutation(
                key=StateKey(
                    namespace=partition.namespace,
                    object_type="delivery",
                    object_id="delivery:" + suffix,
                ),
                assertion=StateAssertion.absent(),
                kind=StateMutationKind.CREATE,
                document=StateDocument(
                    schema_name="delivery_delivery",
                    schema_version=1,
                    state_version=1,
                    payload=b'{"status":"prepared"}',
                ),
            ),),
        )

    async def _assert_ticker_progress(
        self,
        *,
        channel,
        operation,
        expected_exception: type[BaseException] | None = None,
    ) -> object:
        original = (
            broker_module.AuthorityAttestorClient
            .current_endpoint_identity
        )
        worker_entered = threading.Event()
        release_worker = threading.Event()
        worker_entered_async = asyncio.Event()
        loop = asyncio.get_running_loop()

        def blocked_identity(client, **kwargs):
            if (
                not worker_entered.is_set()
                and kwargs.get("endpoint_id") == channel.endpoint_id
            ):
                worker_entered.set()
                loop.call_soon_threadsafe(worker_entered_async.set)
                if not release_worker.wait(timeout=30.0):
                    raise RuntimeError("test authority barrier was not released")
            return original(client, **kwargs)

        ticks = 0
        ticker_gate = asyncio.Event()

        async def ticker() -> None:
            nonlocal ticks
            await ticker_gate.wait()
            for _ in range(3):
                ticks += 1
                await asyncio.sleep(0)

        ticker_task = asyncio.create_task(ticker())
        operation_task = None
        worker_entry_task = asyncio.create_task(worker_entered_async.wait())
        result: object = None
        try:
            with mock.patch.object(
                broker_module.AuthorityAttestorClient,
                "current_endpoint_identity",
                blocked_identity,
            ):
                operation_task = asyncio.create_task(operation())
                completed, _ = await asyncio.wait(
                    {worker_entry_task, operation_task},
                    timeout=10.0,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if not completed:
                    self.fail("authority worker did not reach test barrier")
                if (
                    operation_task in completed
                    and not worker_entered.is_set()
                ):
                    await operation_task
                    self.fail(
                        "authority operation completed before test barrier",
                    )
                await worker_entry_task
                ticks_at_barrier = ticks
                ticker_gate.set()
                await asyncio.wait_for(ticker_task, timeout=10.0)
                release_worker.set()
                if expected_exception is None:
                    result = await operation_task
                else:
                    with self.assertRaises(expected_exception):
                        await operation_task
        finally:
            release_worker.set()
            if operation_task is not None and not operation_task.done():
                operation_task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await operation_task
            if not worker_entry_task.done():
                worker_entry_task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await worker_entry_task
            ticker_gate.set()
            if not ticker_task.done():
                await ticker_task
        self.assertTrue(worker_entered.is_set())
        self.assertGreaterEqual(ticks, ticks_at_barrier + 3)
        self.assertTrue(channel._custodian.process.is_alive())
        self.assertTrue(channel._custodian.attestor.alive)
        return result

    @staticmethod
    async def _wait_for_current_certificate_rotation_window(
        channel,
        *,
        clock,
    ) -> None:
        certificate = channel.certificate
        lifetime = (
            certificate.expires_at - certificate.issued_at
        ).total_seconds()
        rotation_at = certificate.expires_at - timedelta(
            seconds=lifetime / 3.0,
        )
        while True:
            delay = (rotation_at - clock.utc_now()).total_seconds()
            if delay <= 0:
                return
            await asyncio.sleep(delay)

    def test_custodian_continues_after_endpoint_keyboard_interrupt_and_retries(
        self,
    ) -> None:
        class Endpoint:
            def __init__(self, failure: BaseException | None = None) -> None:
                self.failure = failure
                self.close_calls = 0

            def close(self) -> None:
                self.close_calls += 1
                if self.failure is not None and self.close_calls == 1:
                    raise self.failure

        class Attestor:
            def __init__(self) -> None:
                self.close_calls = 0

            def close(self) -> None:
                self.close_calls += 1

        interrupt = KeyboardInterrupt("endpoint interrupt")
        failing = Endpoint(interrupt)
        remaining = Endpoint()
        process = _FakeProcess()
        attestor = Attestor()
        custodian = broker_module._BrokerProcessCustodian(
            process=process,
            attestor=attestor,
            endpoint_close_resources=(
                broker_module._ParentEndpointCloseResource(failing),
                broker_module._ParentEndpointCloseResource(remaining),
            ),
        )

        with self.assertRaises(KeyboardInterrupt) as raised:
            custodian.reap()
        self.assertIs(interrupt, raised.exception)
        self.assertEqual(1, failing.close_calls)
        self.assertEqual(1, remaining.close_calls)
        self.assertFalse(process.is_alive())
        self.assertEqual(1, process.terminated)
        self.assertEqual(1, attestor.close_calls)

        custodian.reap()
        self.assertEqual(2, failing.close_calls)
        self.assertEqual(1, remaining.close_calls)
        self.assertEqual(1, attestor.close_calls)
        self.assertTrue(custodian._reaped)

    def test_custodian_reports_process_that_survives_terminate_and_kill(
        self,
    ) -> None:
        class StubbornProcess(_FakeProcess):
            def terminate(self) -> None:
                self.terminated = True

            def kill(self) -> None:
                self.killed = True

        class Attestor:
            def __init__(self) -> None:
                self.close_calls = 0

            def close(self) -> None:
                self.close_calls += 1

        process = StubbornProcess()
        attestor = Attestor()
        custodian = broker_module._BrokerProcessCustodian(
            process=process,
            attestor=attestor,
        )

        with self.assertRaises(
            NsRuntimeIamUnavailableError,
        ) as raised:
            custodian.reap()
        self.assertEqual(
            "broker_process_did_not_exit",
            raised.exception.details["reason"],
        )
        self.assertTrue(process.is_alive())
        self.assertTrue(process.terminated)
        self.assertTrue(process.killed)
        self.assertEqual(1, attestor.close_calls)
        self.assertFalse(custodian._reaped)

    def test_channel_close_reaps_custody_after_connection_keyboard_interrupt(
        self,
    ) -> None:
        channel, process, connection, _, _ = _test_channel(
            lambda sent: b"",
        )

        class FailOnceCloseConnection:
            def __init__(self) -> None:
                self.close_calls = 0

            def close(self) -> None:
                self.close_calls += 1
                if self.close_calls == 1:
                    raise KeyboardInterrupt("connection close")
                connection.close()

        failing_connection = FailOnceCloseConnection()
        object.__setattr__(channel, "_connection", failing_connection)
        attestor = channel._custodian.attestor

        with self.assertRaises(KeyboardInterrupt):
            channel.close(terminate=True)

        self.assertFalse(process.is_alive())
        self.assertFalse(attestor.alive)
        self.assertTrue(channel._custodian._reaped)
        channel.close(terminate=True)
        self.assertEqual(2, failing_connection.close_calls)

    def test_old_pending_token_binding_and_direct_client_assembly_fail_closed(
        self,
    ) -> None:
        owner = NsHttpClientOwner()
        http = owner.create(
            name="ordinary-owner",
            base_url="https://iam.invalid/",
        )
        self.addAsyncCleanup(owner.aclose)
        self.assertFalse(hasattr(owner, "_pending_authority_token"))
        self.assertFalse(hasattr(owner, "_create_authority_handle"))
        with self.assertRaises(NsValidationError):
            IamClient(
                http_client=http,
                internal_service_credential="s" * 32,
                composition=object(),
            )
        forged = object.__new__(ProductionIamAuthorityProxy)
        for name, value in {
            "_channel": object(),
            "_handle": object(),
            "_clock": object(),
            "_iam_mode": "strict",
            "_authorization_service": None,
        }.items():
            object.__setattr__(forged, name, value)
        self.assertFalse(forged._is_production_adapter())
        self.assertFalse(BrokerAuthorityHandle(
            broker_instance_id="forged",
            endpoint_id="forged",
            handle_id="forged",
            role=BrokerRepositoryRole.IAM,
            runtime_id="forged",
            lifecycle_generation=1,
            signature=b"forged",
        ).verify(b"\0" * 32, instance_id="forged"))

        with self.assertRaises(NsValidationError):
            broker_module._BrokerIamBackend(
                _config("https://iam.invalid/"),
                {
                    "iam_service_credential": "s" * 32,
                    "state_password_base64": None,
                },
                clock=ControlledClock(),
            )
        with self.assertRaises(NsValidationError):
            broker_module._BrokerStateBackend(
                _config("https://iam.invalid/"),
                {
                    "iam_service_credential": "s" * 32,
                    "state_password_base64": None,
                },
                clock=ControlledClock(),
            )

        raw_provider = create_state_store_provider(
            config=NsRuntimeStateStoreConfig(
                backend="redis",
                endpoint="redis://127.0.0.1:6379/0",
                namespace="provider-without-authority",
            ),
            clock=ControlledClock(),
        )
        assert raw_provider is not None
        self.assertIsNone(vars(raw_provider).get(
            "_StateStore__production_scope_validator",
        ))
        with self.assertRaises(NsValidationError):
            raw_provider._install_repositories(())

    def test_public_starter_and_wrong_deployment_root_fail_closed(self) -> None:
        with self.assertRaises(NsValidationError):
            start_production_authority_broker(config=_config(
                "https://attacker.invalid/",
            ))
        root = Ed25519PrivateKey.generate()
        root_bytes = root.private_bytes(
            serialization.Encoding.Raw,
            serialization.PrivateFormat.Raw,
            serialization.NoEncryption(),
        )
        key_read, key_write = os.pipe()
        secrets_read, secrets_write = os.pipe()
        try:
            os.write(key_write, root_bytes)
            os.write(secrets_write, encode_frame({
                "iam_service_credential": "s" * 32,
                "state_password_base64": None,
            }))
        finally:
            os.close(key_write)
            os.close(secrets_write)
        attacker_public = root.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        with mock.patch.object(
            broker_module,
            "_PRODUCTION_ROOT_PUBLIC_KEY",
            attacker_public,
        ):
            with self.assertRaises(NsRuntimeIamUnavailableError):
                broker_module._start_production_authority_broker_from_inherited_fds(
                    config=_config("https://attacker.invalid/"),
                    root_key_fd=key_read,
                    secrets_fd=secrets_read,
                )

    def test_outer_bootstrap_moves_secret_fds_out_of_parent_immediately(
        self,
    ) -> None:
        key_read, key_write = os.pipe()
        secrets_read, secrets_write = os.pipe()
        secret_marker = "broker-secret-must-not-remain-in-parent"
        previous_key = os.environ.get("NS_RUNTIME_AUTHORITY_KEY_FD")
        previous_secrets = os.environ.get("NS_RUNTIME_AUTHORITY_SECRETS_FD")
        try:
            os.write(key_write, os.urandom(32))
            os.write(secrets_write, encode_frame({
                "iam_service_credential": secret_marker,
                "state_password_base64": broker_module.encode_bytes(
                    secret_marker.encode("utf-8"),
                ),
            }))
        finally:
            os.close(key_write)
            os.close(secrets_write)
        os.environ["NS_RUNTIME_AUTHORITY_KEY_FD"] = str(key_read)
        os.environ["NS_RUNTIME_AUTHORITY_SECRETS_FD"] = str(secrets_read)
        bootstrap = None
        try:
            bootstrap = load_inherited_authority_bootstrap()
            self.assertNotIn("NS_RUNTIME_AUTHORITY_KEY_FD", os.environ)
            self.assertNotIn("NS_RUNTIME_AUTHORITY_SECRETS_FD", os.environ)
            self.assertFalse(any(
                secret_marker in value
                for value in os.environ.values()
            ))
            self.assertEqual(
                {"_connections", "_process", "_attestor", "_consumed"},
                set(type(bootstrap).__slots__),
            )
            for slot in type(bootstrap).__slots__:
                value = getattr(bootstrap, slot)
                self.assertNotEqual(secret_marker, value)
                self.assertNotIsInstance(value, Ed25519PrivateKey)
            with self.assertRaises(OSError):
                os.fstat(key_read)
            with self.assertRaises(OSError):
                os.fstat(secrets_read)
        finally:
            if bootstrap is not None:
                bootstrap.close()
            for name, previous in (
                ("NS_RUNTIME_AUTHORITY_KEY_FD", previous_key),
                ("NS_RUNTIME_AUTHORITY_SECRETS_FD", previous_secrets),
            ):
                if previous is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = previous

    def test_root_certificate_rejects_self_reported_public_key(self) -> None:
        signer = Ed25519PrivateKey.generate()
        wrong_root = Ed25519PrivateKey.generate().public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        session_public = Ed25519PrivateKey.generate().public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        now = datetime.now(timezone.utc)
        values = {
            "trust_realm": "contract-test",
            "broker_instance_id": "broker_test",
            "session_public_key": broker_module.encode_bytes(session_public),
            "runtime_id": "runtime:test",
            "lifecycle_generation": 1,
            "delegation_fingerprint": "sha256:" + "0" * 64,
            "issued_at": broker_module.encode_time(now),
            "expires_at": broker_module.encode_time(now + timedelta(minutes=1)),
            "nonce": "nonce",
        }
        certificate = BrokerInstanceCertificate(
            trust_realm="contract-test",
            broker_instance_id="broker_test",
            session_public_key=session_public,
            runtime_id="runtime:test",
            lifecycle_generation=1,
            delegation_fingerprint="sha256:" + "0" * 64,
            issued_at=now,
            expires_at=now + timedelta(minutes=1),
            nonce="nonce",
            signature=signer.sign(broker_module._canonical(values)),
        )
        self.assertFalse(certificate.verify(
            wrong_root,
            expected_realm="contract-test",
            expected_runtime_id="runtime:test",
            now=now,
        ))

    def test_controlled_clock_drives_proxy_certificate_and_rotation_boundaries(
        self,
    ) -> None:
        clock = ControlledClock(
            utc_start=datetime(2001, 2, 3, tzinfo=timezone.utc),
        )
        self.assertGreater(
            abs(
                (datetime.now(timezone.utc) - clock.utc_now()).total_seconds()
            ),
            24 * 60 * 60,
        )

        channel = object.__new__(
            broker_module._ProductionRoleBrokerChannel,
        )
        handle = BrokerAuthorityHandle(
            broker_instance_id="broker:clock",
            endpoint_id="endpoint:iam",
            handle_id="handle:iam",
            role=BrokerRepositoryRole.IAM,
            runtime_id="runtime:clock",
            lifecycle_generation=1,
            signature=b"test-signature",
        )
        object.__setattr__(channel, "_role", BrokerRepositoryRole.IAM)
        object.__setattr__(channel, "_handle", handle)
        proxy = object.__new__(ProductionIamAuthorityProxy)
        for name, value in (
            ("_channel", channel),
            ("_handle", handle),
            ("_clock", clock),
            ("_iam_mode", "strict"),
            ("_authorization_service", None),
            ("_composition_binding", None),
        ):
            object.__setattr__(proxy, name, value)
        observed: list[datetime] = []

        def verify_chain(
            value: ProductionIamAuthorityProxy,
            now: datetime,
        ) -> bool:
            self.assertIs(value, proxy)
            observed.append(now)
            return True

        with (
            mock.patch.object(
                broker_module._ProductionRoleBrokerChannel,
                "alive",
                new_callable=mock.PropertyMock,
                return_value=True,
            ),
            mock.patch.object(
                broker_module._ProductionRoleBrokerChannel,
                "_identity_is_current",
                return_value=True,
            ),
            mock.patch.object(
                ProductionIamAuthorityProxy,
                "_verify_production_chain",
                autospec=True,
                side_effect=verify_chain,
            ),
        ):
            self.assertTrue(proxy._is_broker_adapter())
            self.assertTrue(proxy._is_production_adapter())
        self.assertEqual(
            [clock.utc_now(), clock.utc_now(), clock.utc_now()],
            observed,
        )

        root = Ed25519PrivateKey.generate()
        root_public = root.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        session_public = (
            Ed25519PrivateKey.generate().public_key().public_bytes(
                serialization.Encoding.Raw,
                serialization.PublicFormat.Raw,
            )
        )
        issued_at = clock.utc_now()
        expires_at = issued_at + timedelta(seconds=60)
        certificate = _test_certificate(
            root,
            session_public,
            issued_at=issued_at,
            expires_at=expires_at,
        )
        verify_values = {
            "expected_realm": "contract-test",
            "expected_runtime_id": certificate.runtime_id,
            "expected_instance_id": certificate.broker_instance_id,
            "expected_session_public_key": certificate.session_public_key,
            "expected_generation": certificate.lifecycle_generation,
        }
        self.assertTrue(certificate.verify(
            root_public,
            now=clock.utc_now(),
            **verify_values,
        ))
        clock.advance(59.999)
        self.assertTrue(certificate.verify(
            root_public,
            now=clock.utc_now(),
            **verify_values,
        ))
        clock.advance(0.001)
        self.assertFalse(certificate.verify(
            root_public,
            now=clock.utc_now(),
            **verify_values,
        ))

        rotation_clock = ControlledClock(utc_start=issued_at)
        approved = {
            "session_issued_at": issued_at,
            "session_expires_at": expires_at,
        }
        rotation_clock.advance(39.999)
        self.assertFalse(attestor_module._rotation_required(
            approved,
            rotation_clock.utc_now(),
        ))
        rotation_clock.advance(0.001)
        self.assertTrue(attestor_module._rotation_required(
            approved,
            rotation_clock.utc_now(),
        ))

    def test_wire_never_invokes_reduce_and_rejects_malformed_frames(self) -> None:
        invoked: list[bool] = []

        class Hostile:
            def __reduce__(self):
                invoked.append(True)
                return (eval, ("1 + 1",))

        with self.assertRaises(NsValidationError):
            encode_frame({"payload": Hostile()})  # type: ignore[dict-item]
        self.assertEqual([], invoked)
        with self.assertRaises(NsValidationError):
            decode_frame(b'{"a":1,"a":2}')
        with self.assertRaises(NsValidationError):
            decode_frame(b'{"value":NaN}')
        with self.assertRaises(NsValidationError):
            decode_frame(b"x" * (MAX_FRAME_BYTES + 1))
        with self.assertRaises(NsValidationError):
            require_object(
                {"known": True, "unknown": False},
                fields={"known"},
                field="attack.unknown",
            )
        with self.assertRaises(NsValidationError):
            start_contract_test_authority_broker(
                config=dataclasses.replace(
                    _config("https://iam.invalid/"),
                    state_backend="redis",
                    state_endpoint="redis://127.0.0.1:6379/0",
                ),
                iam_service_credential="s" * 32,
            )
        with self.assertRaises(ValueError):
            attestor_module._encode_frame({"payload": Hostile()})
        self.assertEqual([], invoked)
        with self.assertRaises(ValueError):
            attestor_module._decode_frame(b'{"a":1,"a":2}')
        with self.assertRaises(ValueError):
            attestor_module._decode_frame(b'{"value":Infinity}')
        with self.assertRaises(ValueError):
            attestor_module._decode_frame(
                b"x" * (attestor_module.ATTESTOR_MAX_FRAME_BYTES + 1),
            )

    def test_production_attestor_rejects_attacker_root_and_main_globals(
        self,
    ) -> None:
        attacker = Ed25519PrivateKey.generate()
        delegation_key = Ed25519PrivateKey.generate()
        session = Ed25519PrivateKey.generate()
        now = datetime.now(timezone.utc)
        delegation_public = delegation_key.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        delegation_values = {
            "trust_realm": "production",
            "broker_instance_id": "attacker-broker",
            "runtime_id": "runtime:attacker",
            "delegation_public_key": broker_module.encode_bytes(
                delegation_public,
            ),
            "attestor_instance_id": "attacker-attestor",
            "attestor_public_key": broker_module.encode_bytes(
                b"a" * 32,
            ),
            "allowed_usages": list(broker_module._DELEGATION_USAGES),
            "issued_at": broker_module.encode_time(now),
            "expires_at": broker_module.encode_time(
                now + timedelta(hours=1),
            ),
            "nonce": "attacker-delegation",
        }
        delegation = BrokerDelegationCertificate(
            trust_realm="production",
            broker_instance_id="attacker-broker",
            runtime_id="runtime:attacker",
            delegation_public_key=delegation_public,
            attestor_instance_id="attacker-attestor",
            attestor_public_key=b"a" * 32,
            allowed_usages=broker_module._DELEGATION_USAGES,
            issued_at=now,
            expires_at=now + timedelta(hours=1),
            nonce="attacker-delegation",
            signature=attacker.sign(
                broker_module._canonical(delegation_values),
            ),
        )
        session_public = session.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        certificate = _test_certificate(
            delegation_key,
            session_public,
            instance_id="attacker-broker",
            runtime_id="runtime:attacker",
            delegation_fingerprint=delegation.fingerprint,
        )
        endpoints = {
            role.value: "attacker-endpoint-" + role.value
            for role in BrokerRepositoryRole
        }
        handles = {
            role.value: broker_module._new_handle(
                private_key=session,
                instance_id="attacker-broker",
                endpoint_id=endpoints[role.value],
                role=role,
                runtime_id="runtime:attacker",
                generation=1,
            )
            for role in BrokerRepositoryRole
        }
        with mock.patch.object(
            broker_module,
            "_PRODUCTION_ROOT_PUBLIC_KEY",
            attacker.public_key().public_bytes(
                serialization.Encoding.Raw,
                serialization.PublicFormat.Raw,
            ),
        ), mock.patch.object(
            attestor_module,
            "_PRODUCTION_ROOT_PUBLIC_KEY",
            attacker.public_key().public_bytes(
                serialization.Encoding.Raw,
                serialization.PublicFormat.Raw,
            ),
        ):
            attestor = start_authority_attestor(realm="production")
            try:
                with self.assertRaises(
                    attestor_module.AuthorityAttestationError,
                ):
                    attestor.approve_identity(
                        realm="production",
                        runtime_id="runtime:attacker",
                        delegation_certificate=(
                            broker_module._encode_delegation_certificate(
                                delegation,
                            )
                        ),
                        session_certificate=(
                            broker_module._encode_certificate(certificate)
                        ),
                        handles={
                            name: broker_module._encode_handle(handle)
                            for name, handle in handles.items()
                        },
                        endpoints=endpoints,
                    )
            finally:
                attestor.close()

    def test_root_delegation_binds_exact_attestor_and_ticket_signer(
        self,
    ) -> None:
        root = Ed25519PrivateKey.generate()
        root_public = root.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        approved_attestor = start_authority_attestor(
            realm="contract-test",
            expected_test_root_public_key=root_public,
        )
        attacker_attestor = start_authority_attestor(
            realm="contract-test",
            expected_test_root_public_key=root_public,
        )
        tamper_attestor = start_authority_attestor(
            realm="contract-test",
            expected_test_root_public_key=root_public,
        )
        ticket_attestor = start_authority_attestor(
            realm="contract-test",
            expected_test_root_public_key=root_public,
        )

        def bundle(attestor, suffix):
            delegation_key = Ed25519PrivateKey.generate()
            delegation_public = (
                delegation_key.public_key().public_bytes(
                    serialization.Encoding.Raw,
                    serialization.PublicFormat.Raw,
                )
            )
            session_key = Ed25519PrivateKey.generate()
            session_public = session_key.public_key().public_bytes(
                serialization.Encoding.Raw,
                serialization.PublicFormat.Raw,
            )
            now = datetime.now(timezone.utc)
            delegation_values = {
                "trust_realm": "contract-test",
                "broker_instance_id": "broker-" + suffix,
                "runtime_id": "runtime:" + suffix,
                "delegation_public_key": broker_module.encode_bytes(
                    delegation_public,
                ),
                "attestor_instance_id": attestor.instance_id,
                "attestor_public_key": broker_module.encode_bytes(
                    attestor.public_key,
                ),
                "allowed_usages": list(
                    broker_module._DELEGATION_USAGES,
                ),
                "issued_at": broker_module.encode_time(now),
                "expires_at": broker_module.encode_time(
                    now + timedelta(hours=1),
                ),
                "nonce": "delegation-" + suffix,
            }
            delegation = BrokerDelegationCertificate(
                trust_realm="contract-test",
                broker_instance_id="broker-" + suffix,
                runtime_id="runtime:" + suffix,
                delegation_public_key=delegation_public,
                attestor_instance_id=attestor.instance_id,
                attestor_public_key=attestor.public_key,
                allowed_usages=broker_module._DELEGATION_USAGES,
                issued_at=now,
                expires_at=now + timedelta(hours=1),
                nonce="delegation-" + suffix,
                signature=root.sign(
                    broker_module._canonical(delegation_values),
                ),
            )
            certificate = _test_certificate(
                delegation_key,
                session_public,
                instance_id="broker-" + suffix,
                runtime_id="runtime:" + suffix,
                delegation_fingerprint=delegation.fingerprint,
            )
            endpoints = {
                role.value: f"endpoint-{suffix}-{role.value}"
                for role in BrokerRepositoryRole
            }
            handles = {
                role.value: broker_module._new_handle(
                    private_key=session_key,
                    instance_id=certificate.broker_instance_id,
                    endpoint_id=endpoints[role.value],
                    role=role,
                    runtime_id=certificate.runtime_id,
                    generation=1,
                )
                for role in BrokerRepositoryRole
            }
            return delegation, certificate, endpoints, handles, session_public

        try:
            (
                delegation,
                certificate,
                endpoints,
                handles,
                session_public,
            ) = bundle(approved_attestor, "approved")
            approved = approved_attestor.approve_identity(
                realm="contract-test",
                runtime_id=certificate.runtime_id,
                delegation_certificate=(
                    broker_module._encode_delegation_certificate(
                        delegation,
                    )
                ),
                session_certificate=broker_module._encode_certificate(
                    certificate,
                ),
                handles={
                    role: broker_module._encode_handle(handle)
                    for role, handle in handles.items()
                },
                endpoints=endpoints,
            )
            with self.assertRaises(AuthorityAttestationError):
                attacker_attestor.approve_identity(
                    realm="contract-test",
                    runtime_id=certificate.runtime_id,
                    delegation_certificate=(
                        broker_module._encode_delegation_certificate(
                            delegation,
                        )
                    ),
                    session_certificate=broker_module._encode_certificate(
                        certificate,
                    ),
                    handles={
                        role: broker_module._encode_handle(handle)
                        for role, handle in handles.items()
                    },
                    endpoints=endpoints,
                )
            tampered = dataclasses.replace(
                delegation,
                attestor_instance_id=tamper_attestor.instance_id,
                attestor_public_key=tamper_attestor.public_key,
            )
            with self.assertRaises(AuthorityAttestationError):
                tamper_attestor.approve_identity(
                    realm="contract-test",
                    runtime_id=certificate.runtime_id,
                    delegation_certificate=(
                        broker_module._encode_delegation_certificate(
                            tampered,
                        )
                    ),
                    session_certificate=broker_module._encode_certificate(
                        certificate,
                    ),
                    handles={
                        role: broker_module._encode_handle(handle)
                        for role, handle in handles.items()
                    },
                    endpoints=endpoints,
                )

            (
                attacker_delegation,
                attacker_certificate,
                attacker_endpoints,
                attacker_handles,
                _,
            ) = bundle(ticket_attestor, "attacker")
            attacker_approved = ticket_attestor.approve_identity(
                realm="contract-test",
                runtime_id=attacker_certificate.runtime_id,
                delegation_certificate=(
                    broker_module._encode_delegation_certificate(
                        attacker_delegation,
                    )
                ),
                session_certificate=broker_module._encode_certificate(
                    attacker_certificate,
                ),
                handles={
                    role: broker_module._encode_handle(handle)
                    for role, handle in attacker_handles.items()
                },
                endpoints=attacker_endpoints,
            )
            fake_ticket = ticket_attestor.prepare_request(
                identity_id=attacker_approved["identity_id"],
                connection_generation=1,
                endpoint_id=attacker_endpoints["payload"],
                role="payload",
                operation="read_payload_body",
                request_id="ipc-attacker",
                request_sequence=1,
                request_fingerprint="sha256:" + "a" * 64,
            )["ticket"]
            with self.assertRaises(NsValidationError):
                broker_module._verify_attestor_ticket(
                    fake_ticket,
                    delegation_certificate=delegation,
                    identity_id=approved["identity_id"],
                    instance_id=certificate.broker_instance_id,
                    runtime_id=certificate.runtime_id,
                    generation=1,
                    session_public_key=session_public,
                    endpoint_id=endpoints["payload"],
                    endpoint_role=BrokerRepositoryRole.PAYLOAD,
                    handle=handles["payload"],
                    operation="read_payload_body",
                    request_id="ipc-attacker",
                    request_sequence=1,
                    request_fingerprint="sha256:" + "a" * 64,
                    now=datetime.now(timezone.utc),
                )
        finally:
            approved_attestor.close()
            attacker_attestor.close()
            tamper_attestor.close()
            ticket_attestor.close()

    def test_request_snapshot_rejects_connection_certificate_swap(
        self,
    ) -> None:
        holder: dict[str, object] = {}

        def response(sent):
            channel = holder["channel"]
            certificate = holder["certificate"]
            session = holder["session"]
            assert isinstance(
                channel, broker_module._ContractTestRoleBrokerChannel,
            )
            assert isinstance(certificate, BrokerInstanceCertificate)
            assert isinstance(session, Ed25519PrivateKey)
            object.__setattr__(channel, "_connection", object())
            object.__setattr__(
                channel,
                "_certificate",
                dataclasses.replace(
                    certificate,
                    nonce="swapped-during-request",
                ),
            )
            return _signed_response_bytes(
                sent,
                session=session,
                certificate=certificate,
                response_sequence=1,
            )

        channel, process, _, session, certificate = _test_channel(
            response,
        )
        holder.update({
            "channel": channel,
            "session": session,
            "certificate": certificate,
        })
        with self.assertRaises(NsRuntimeStateStoreUnavailableError):
            channel.request(
                operation="state_health",
                payload={},
            )
        self.assertFalse(process.is_alive())

    def test_send_bytes_started_failure_is_indeterminate_and_reaped(
        self,
    ) -> None:
        channel, process, connection, _, _ = _test_channel(
            lambda sent: b"",
            role=BrokerRepositoryRole.ADMISSION,
        )

        class FailsAfterStart:
            def send_bytes(self, value):
                connection.sent = value
                raise OSError("partial write")

            def close(self):
                connection.close()

        object.__setattr__(channel, "_connection", FailsAfterStart())
        with self.assertRaises(NsRuntimeStateStoreIndeterminateWriteError):
            channel.request(
                operation="transact_admission",
                payload={},
            )
        self.assertIsNotNone(connection.sent)
        self.assertFalse(process.is_alive())

    def test_malformed_response_after_write_is_indeterminate(self) -> None:
        channel, process, connection, private_key, _ = _test_channel(
            lambda sent: b'{"malformed":true}',
            role=BrokerRepositoryRole.ADMISSION,
        )
        del private_key
        with self.assertRaises(NsRuntimeStateStoreIndeterminateWriteError):
            channel.request(
                operation="transact_admission",
                payload={
                    "tenant_id": "tenant:1",
                    "bucket_id": 0,
                    "layout_generation": 1,
                    "mutations": [],
                    "record_assertions": [],
                    "ordered_index_mutations": [],
                    "ordered_index_assertions": [],
                    "log_appends": [],
                },
            )
        self.assertFalse(process.is_alive())
        self.assertTrue(connection.closed)
        channel.close()
        self.assertFalse(process.is_alive())

    async def test_async_authority_operations_do_not_block_event_loop(
        self,
    ) -> None:
        request = _access_request()
        broker, _ = await self._broker([
            _decision(request).to_wire() for _ in range(20)
        ])
        transaction = self._admission_transaction(
            broker,
            suffix="event-loop",
        )
        partition = transaction.partition
        operations = (
            (
                broker.repositories.admission._channel,
                lambda: broker.repositories.admission.transact_admission(
                    tenant_id=partition.tenant_id,
                    bucket_id=partition.bucket_id,
                    layout_generation=partition.layout_generation,
                    transaction=transaction,
                ),
                NsRuntimeStateStoreUnavailableError,
            ),
            (
                broker.repositories.scheduler._channel,
                lambda: broker.repositories.scheduler.read_scheduler_index(
                    tenant_id=partition.tenant_id,
                    bucket_id=partition.bucket_id,
                    layout_generation=partition.layout_generation,
                    index_name="delivery.prepared",
                    limit=10,
                ),
                NsRuntimeStateStoreUnavailableError,
            ),
            (
                broker.state_store._channel,
                broker.state_store.health,
                None,
            ),
            (
                broker.iam._channel,
                lambda: broker.iam.access_check(request),
                None,
            ),
        )
        try:
            for iteration in range(20):
                for channel, operation, expected_exception in operations:
                    with self.subTest(
                        iteration=iteration,
                        role=channel.role.value,
                    ):
                        await self._assert_ticker_progress(
                            channel=channel,
                            operation=operation,
                            expected_exception=expected_exception,
                        )
            self.assertTrue(broker._channel._custodian.process.is_alive())
            self.assertTrue(broker._channel._custodian.attestor.alive)
        finally:
            self._close_broker_and_assert_reaped(broker)

    async def test_test_only_diagnostics_distinguish_child_exit_roles(
        self,
    ) -> None:
        for failed_child in ("broker", "attestor"):
            with self.subTest(failed_child=failed_child):
                broker, _ = await self._broker([])
                channel = broker._channel
                custodian = channel._custodian
                failed_process = (
                    custodian.process
                    if failed_child == "broker"
                    else custodian.attestor._process
                )
                try:
                    failed_process.terminate()
                    failed_process.join(timeout=5.0)
                    with self.assertRaises(
                        NsRuntimeStateStoreUnavailableError,
                    ) as raised:
                        await asyncio.to_thread(
                            channel.request,
                            operation="state_health",
                            payload={},
                        )
                    details = raised.exception.details
                    self.assertEqual("state_health", details["operation"])
                    self.assertEqual("lifecycle", details["endpoint_role"])
                    self.assertIs(
                        int,
                        type(details["rotation_generation"]),
                    )
                    self.assertEqual("none", details["timeout_stage"])
                    self.assertEqual(
                        failed_child != "broker",
                        details["broker_process_alive"],
                    )
                    self.assertEqual(
                        failed_child != "attestor",
                        details["attestor_process_alive"],
                    )
                    self.assertIsNotNone(
                        details[
                            f"{failed_child}_exitcode"
                        ],
                    )
                    forbidden_fragments = (
                        "credential", "payload", "fd", "handle",
                        "certificate", "endpoint_id",
                    )
                    self.assertFalse(any(
                        fragment in key
                        for key in details
                        for fragment in forbidden_fragments
                    ))
                finally:
                    self._close_broker_and_assert_reaped(broker)

    def test_test_only_diagnostics_identify_broker_timeout_stage(self) -> None:
        channel, process, connection, _, _ = _test_channel(
            lambda sent: b"",
            diagnostics_enabled=True,
        )

        class NeverResponds:
            def send_bytes(self, value):
                connection.sent = value

            def poll(self, timeout):
                del timeout
                return False

            def close(self):
                connection.close()

        object.__setattr__(channel, "_connection", NeverResponds())
        with self.assertRaises(
            NsRuntimeStateStoreUnavailableError,
        ) as raised:
            channel.request(operation="state_health", payload={})

        details = raised.exception.details
        self.assertEqual("ipc_timeout", details["reason"])
        self.assertEqual("state_health", details["operation"])
        self.assertEqual("lifecycle", details["endpoint_role"])
        self.assertEqual("broker_ipc_wait", details["request_stage"])
        self.assertEqual("broker_response", details["timeout_stage"])
        self.assertTrue(details["broker_process_alive"])
        self.assertTrue(details["attestor_process_alive"])
        self.assertFalse(process.is_alive())
        self.assertTrue(connection.closed)

    async def test_verified_iam_receipt_is_worker_created_and_local_only(
        self,
    ) -> None:
        request = _access_request()
        broker, _ = await self._broker([_decision(request).to_wire()])
        verified = await broker.iam.access_check_signed(request)
        receipt = verified.verification
        identity = (
            broker.iam._broker_session_identity_snapshot_local()
        )
        assert identity is not None
        self.assertIs(BrokerIamVerificationReceipt, type(receipt))
        self.assertEqual("iam_verification_receipt", receipt.kind)
        self.assertEqual("iam", receipt.role)
        self.assertEqual(64, len(receipt.signature))
        self.assertEqual(
            identity.attestor_identity_id,
            receipt.attestor_identity_id,
        )
        self.assertEqual(
            identity.lifecycle_generation,
            receipt.lifecycle_generation,
        )
        self.assertEqual(
            identity.session_key_fingerprint,
            receipt.session_key_fingerprint,
        )
        with self.assertRaises(TypeError):
            BrokerIamVerificationReceipt(  # type: ignore[call-arg]
                attestor_identity_id=receipt.attestor_identity_id,
                broker_instance_id=receipt.broker_instance_id,
                lifecycle_generation=receipt.lifecycle_generation,
                session_key_fingerprint=receipt.session_key_fingerprint,
                operation=receipt.operation,
                request_fingerprint=receipt.request_fingerprint,
                signed_result_fingerprint=receipt.signed_result_fingerprint,
                result_fingerprint=receipt.result_fingerprint,
                verified_at=receipt.verified_at,
                authority_expires_at=receipt.authority_expires_at,
            )
        with self.assertRaises((TypeError, NsValidationError)):
            dataclasses.replace(
                receipt,
                lifecycle_generation=receipt.lifecycle_generation + 1,
            )
        tampered = object.__new__(BrokerIamVerificationReceipt)
        for field in receipt.__dataclass_fields__:
            object.__setattr__(tampered, field, getattr(receipt, field))
        object.__setattr__(
            tampered,
            "signed_result_fingerprint",
            "sha256:" + "0" * 64,
        )
        forged = object.__new__(broker_module.VerifiedBrokerIamResult)
        object.__setattr__(forged, "result", verified.result)
        object.__setattr__(forged, "authority", verified.authority)
        object.__setattr__(forged, "verification", tampered)
        self.assertFalse(
            broker.iam._verified_broker_iam_result_is_current_local(
                forged,
                operation="runtime_access_check",
                request_fingerprint=verified.authority.request_fingerprint,
                now=datetime.now(timezone.utc),
            ),
        )
        wrong_identity = object.__new__(BrokerIamVerificationReceipt)
        for field in receipt.__dataclass_fields__:
            object.__setattr__(
                wrong_identity,
                field,
                getattr(receipt, field),
            )
        object.__setattr__(
            wrong_identity,
            "attestor_identity_id",
            "attestor_wrong",
        )
        object.__setattr__(forged, "verification", wrong_identity)
        self.assertFalse(
            broker.iam._verified_broker_iam_result_is_current_local(
                forged,
                operation="runtime_access_check",
                request_fingerprint=verified.authority.request_fingerprint,
                now=datetime.now(timezone.utc),
            ),
        )
        with mock.patch.object(
            broker_module.AuthorityAttestorClient,
            "_rpc",
            side_effect=AssertionError("synchronous attestor IPC"),
        ):
            self.assertTrue(
                broker.iam
                ._verified_broker_iam_result_is_current_local(
                    verified,
                    operation="runtime_access_check",
                    request_fingerprint=(
                        verified.authority.request_fingerprint
                    ),
                    now=datetime.now(timezone.utc),
                ),
            )

    async def test_signed_iam_receipt_rejects_complete_forgery_and_replay(
        self,
    ) -> None:
        request = _access_request()
        broker, _ = await self._broker(
            [_decision(request).to_wire() for _ in range(2)],
        )
        other, _ = await self._broker([_decision(request).to_wire()])
        verified = await broker.iam.access_check_signed(request)
        receipt = verified.verification
        identity = broker.iam._broker_session_identity_snapshot_local()
        assert identity is not None
        attestor_key = broker.iam._channel._attestor.public_key
        self.assertTrue(receipt.verify(
            attestor_public_key=attestor_key,
            authority=verified.authority,
            result=verified.result,
            expected_identity=identity,
            operation="runtime_access_check",
            request_fingerprint=verified.authority.request_fingerprint,
            now=datetime.now(timezone.utc),
        ))

        def clone(value, **changes):
            copied = object.__new__(type(value))
            for field in value.__dataclass_fields__:
                object.__setattr__(
                    copied,
                    field,
                    changes.get(field, getattr(value, field)),
                )
            return copied

        mutations = (
            {"signature": b"\x00" * 64},
            {"broker_instance_id": "broker_forged"},
            {"runtime_id": "runtime:forged"},
            {"endpoint_id": "endpoint_forged"},
            {"role": "scheduler"},
            {"operation": "payload_revalidate"},
            {"request_fingerprint": "sha256:" + "1" * 64},
            {"result_fingerprint": "sha256:" + "2" * 64},
            {"request_json_fingerprint": "sha256:" + "3" * 64},
            {
                "verified_at":
                    receipt.verified_at + timedelta(seconds=1),
            },
            {
                "authority_expires_at":
                    receipt.authority_expires_at + timedelta(seconds=1),
            },
            {"lifecycle_generation": receipt.lifecycle_generation + 1},
        )
        for changes in mutations:
            with self.subTest(changes=tuple(changes)):
                forged_receipt = clone(receipt, **changes)
                forged = object.__new__(
                    broker_module.VerifiedBrokerIamResult,
                )
                object.__setattr__(forged, "result", verified.result)
                object.__setattr__(
                    forged, "authority", verified.authority,
                )
                object.__setattr__(
                    forged, "verification", forged_receipt,
                )
                self.assertFalse(
                    broker.iam
                    ._verified_broker_iam_result_is_authentic_local(
                        forged,
                        operation="runtime_access_check",
                        request_fingerprint=(
                            verified.authority.request_fingerprint
                        ),
                        now=datetime.now(timezone.utc),
                    ),
                )

        attacker_key = Ed25519PrivateKey.generate()
        other_key_receipt = clone(receipt, signature=b"")
        object.__setattr__(
            other_key_receipt,
            "signature",
            attacker_key.sign(
                broker_module._canonical(
                    other_key_receipt.signed_values(),
                ),
            ),
        )
        attacker_verified = object.__new__(
            broker_module.VerifiedBrokerIamResult,
        )
        object.__setattr__(
            attacker_verified, "result", verified.result,
        )
        object.__setattr__(
            attacker_verified, "authority", verified.authority,
        )
        object.__setattr__(
            attacker_verified, "verification", other_key_receipt,
        )
        self.assertFalse(
            broker.iam._verified_broker_iam_result_is_authentic_local(
                attacker_verified,
                operation="runtime_access_check",
                request_fingerprint=verified.authority.request_fingerprint,
                now=datetime.now(timezone.utc),
            ),
        )
        self.assertFalse(
            other.iam._verified_broker_iam_result_is_authentic_local(
                verified,
                operation="runtime_access_check",
                request_fingerprint=verified.authority.request_fingerprint,
                now=datetime.now(timezone.utc),
            ),
        )

        forged_authority = clone(
            verified.authority,
            signature=b"\x00" * 64,
            result_json=broker_module._canonical_json({
                **verified.result.to_wire(),
                "reason": "forged_allow",
            }),
        )
        forged_receipt = clone(
            receipt,
            signed_result_fingerprint=(
                broker_module._signed_iam_result_fingerprint(
                    forged_authority,
                )
            ),
            result_fingerprint=broker_module._iam_result_fingerprint(
                forged_authority.result_mapping(),
            ),
            signature=b"\x00" * 64,
        )
        forged_verified = object.__new__(
            broker_module.VerifiedBrokerIamResult,
        )
        object.__setattr__(
            forged_verified, "result",
            IamAccessDecision.from_wire(forged_authority.result_mapping()),
        )
        object.__setattr__(
            forged_verified, "authority", forged_authority,
        )
        object.__setattr__(
            forged_verified, "verification", forged_receipt,
        )
        self.assertFalse(
            broker.iam._verified_broker_iam_result_is_authentic_local(
                forged_verified,
                operation="runtime_access_check",
                request_fingerprint=forged_authority.request_fingerprint,
                now=datetime.now(timezone.utc),
            ),
        )

        service = MessageAuthorizationService.for_broker_contract_tests(
            iam_client=broker.iam,
            clock=SystemClock(),
            mode=AuthorizationMode.STRICT,
            cache_ttl_seconds=30,
        )
        issued = await service.authorize(
            snapshot=_authorization_snapshot(),
            request=request,
            risk=OperationRiskContext(),
        )
        forged_result = clone(
            issued,
            _broker_authority=forged_authority,
            _broker_verification=forged_receipt,
        )
        self.assertIs(MessageAuthorizationResult, type(forged_result))
        self.assertFalse(forged_result.is_issued_by(service))
        with mock.patch.object(
            broker_module.AuthorityAttestorClient,
            "_rpc",
            side_effect=AssertionError("synchronous attestor IPC"),
        ):
            self.assertTrue(issued.is_issued_by(service))

        contract_evidence = (
            AuthorizationDecisionEvidence._issued_for_contract_test(
                decision_version="authorization-decision.v1",
                decision_outcome=AuthorizationDecisionOutcome.ALLOW,
                decision_reason="allow",
                semantic_access_check_reference="sha256:" + "1" * 64,
                message_reference="sha256:" + "2" * 16,
                message_type="connection.heartbeat",
                config_version="config-v1",
                policy_version="policy-v1",
                principal_tenant_id="tenant:1",
                effective_tenant_id="tenant:1",
                cross_tenant_authorized=False,
                authorized_target_reference="sha256:" + "3" * 16,
                session_permission_snapshot_ref="permission:1",
                session_permission_snapshot_version="version:1",
                effective_permission_snapshot_ref="permission:1",
                effective_permission_snapshot_version="version:1",
            )
        )
        production_issuer = object.__new__(
            _ProductionAuthorizationEvidenceIssuer,
        )
        object.__setattr__(production_issuer, "_service", service)
        forged_evidence = clone(
            contract_evidence,
            _issuer=production_issuer,
            _broker_authority=forged_authority,
            _broker_verification=forged_receipt,
        )
        self.assertFalse(forged_evidence.is_production_authority())

        payload_issuer = object.__new__(_PayloadAccessEvidenceIssuer)
        object.__setattr__(payload_issuer, "_iam", broker.iam)
        object.__setattr__(payload_issuer, "_clock", SystemClock())
        forged_payload = object.__new__(PayloadAccessDecisionEvidence)
        object.__setattr__(
            forged_payload, "_authority_seal", payload_issuer,
        )
        object.__setattr__(
            forged_payload, "_broker_authority", forged_authority,
        )
        object.__setattr__(
            forged_payload, "_broker_verification", forged_receipt,
        )
        self.assertFalse(forged_payload.is_production_authority())
        self.assertTrue(broker._channel._custodian.process.is_alive())

    async def test_cache_and_backend_rotation_barriers_refetch_current(
        self,
    ) -> None:
        request = _access_request()
        for mode, warm_cache in (
            (AuthorizationMode.STRICT, False),
            (AuthorizationMode.CACHE, True),
        ):
            with self.subTest(mode=mode.value):
                broker, server = await self._broker(
                    [_decision(request).to_wire() for _ in range(5)],
                    session_ttl_seconds=5.0,
                )
                service = (
                    MessageAuthorizationService
                    .for_broker_contract_tests(
                        iam_client=broker.iam,
                        clock=SystemClock(),
                        mode=mode,
                        cache_ttl_seconds=60,
                    )
                )
                snapshot = _authorization_snapshot()
                if warm_cache:
                    await service.authorize(
                        snapshot=snapshot,
                        request=request,
                        risk=OperationRiskContext(),
                    )
                    old_item = next(iter(service._decisions.values()))
                else:
                    old_verified = (
                        await broker.iam.access_check_signed(request)
                    )
                initial_generation = (
                    broker.iam._channel.certificate.lifecycle_generation
                )
                while (
                    broker.iam._channel.certificate.lifecycle_generation
                    == initial_generation
                ):
                    await self._wait_for_current_certificate_rotation_window(
                        broker.iam._channel,
                        clock=broker.iam._clock,
                    )
                    await broker.iam.access_check_signed(request)
                original_backend = service._current_backend_result
                if warm_cache:
                    cached_calls = 0

                    async def stale_cache_then_miss(*args, **kwargs):
                        nonlocal cached_calls
                        del args, kwargs
                        cached_calls += 1
                        return old_item if cached_calls == 1 else None

                    patcher = mock.patch.object(
                        service,
                        "_current_cached",
                        side_effect=stale_cache_then_miss,
                    )
                else:
                    backend_calls = 0

                    async def stale_backend_then_current(_request):
                        nonlocal backend_calls
                        backend_calls += 1
                        if backend_calls == 1:
                            return old_verified
                        return await original_backend(_request)

                    patcher = mock.patch.object(
                        service,
                        "_current_backend_result",
                        side_effect=stale_backend_then_current,
                    )
                with patcher:
                    result = await service.authorize(
                        snapshot=snapshot,
                        request=request,
                        risk=OperationRiskContext(),
                    )
                identity = (
                    broker.iam._broker_session_identity_snapshot_local()
                )
                assert identity is not None
                self.assertEqual(
                    identity.lifecycle_generation,
                    result._broker_verification.lifecycle_generation,
                )
                self.assertEqual(
                    identity.session_key_fingerprint,
                    result._broker_verification.session_key_fingerprint,
                )
                self.assertTrue(result.is_issued_by(service))
                self.assertTrue(
                    broker._channel._custodian.process.is_alive(),
                )
                if warm_cache:
                    self.assertEqual(2, cached_calls)
                    cached = next(iter(service._decisions.values()))
                    self.assertEqual(
                        identity.lifecycle_generation,
                        cached.lifecycle_generation,
                    )
                else:
                    self.assertEqual(2, backend_calls)
                self.assertGreaterEqual(len(server.calls), 2)

    async def test_unsigned_attestor_receipt_reaps_broker_graph(
        self,
    ) -> None:
        request = _access_request()
        broker, _ = await self._broker([_decision(request).to_wire()])
        original = (
            broker_module.AuthorityAttestorClient.verify_iam_result
        )

        def remove_receipt_signature(client, **kwargs):
            receipt = original(client, **kwargs)
            receipt.pop("signature")
            return receipt

        with mock.patch.object(
            broker_module.AuthorityAttestorClient,
            "verify_iam_result",
            remove_receipt_signature,
        ):
            with self.assertRaises(NsRuntimeIamUnavailableError):
                await broker.iam.access_check_signed(request)
        self.assertFalse(broker._channel._custodian.process.is_alive())
        self.assertFalse(broker._channel._custodian.attestor.alive)

    async def test_full_message_authorization_keeps_event_loop_running(
        self,
    ) -> None:
        request = _access_request()
        broker, _ = await self._broker([
            _decision(request).to_wire() for _ in range(20)
        ])
        try:
            for iteration in range(20):
                service = (
                    MessageAuthorizationService.for_broker_contract_tests(
                        iam_client=broker.iam,
                        clock=SystemClock(),
                        mode=AuthorizationMode.STRICT,
                        cache_ttl_seconds=30,
                    )
                )
                result = await self._assert_ticker_progress(
                    channel=broker.iam._channel,
                    operation=lambda: service.authorize(
                        snapshot=_authorization_snapshot(),
                        request=request,
                        risk=OperationRiskContext(),
                    ),
                )
                with self.subTest(iteration=iteration):
                    self.assertTrue(result.is_issued_by(service))
                    self.assertIs(
                        BrokerIamVerificationReceipt,
                        type(result._broker_verification),
                    )
            self.assertTrue(broker._channel._custodian.process.is_alive())
            self.assertTrue(broker._channel._custodian.attestor.alive)
        finally:
            self._close_broker_and_assert_reaped(broker)

    async def test_processor_authorization_keeps_event_loop_running(
        self,
    ) -> None:
        decision = IamAccessDecision(
            allowed=True,
            reason="backend_allow",
            permission_version="version:test",
            decided_at=datetime.now(timezone.utc),
        )
        broker, _ = await self._broker([decision.to_wire()])
        clock = ControlledClock(utc_start=PROCESSOR_NOW)
        service = MessageAuthorizationService.for_broker_contract_tests(
            iam_client=broker.iam,
            clock=clock,
            mode=AuthorizationMode.STRICT,
            cache_ttl_seconds=30,
        )
        authorization = IamProcessorAuthorization.for_contract_tests(
            service=service,
        )
        supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        self.addAsyncCleanup(supervisor.shutdown, timeout_seconds=1)
        session = _processor_session()
        envelope = _processor_envelope()
        envelope = dataclasses.replace(
            envelope,
            source=dataclasses.replace(
                envelope.source,
                connection_id=session.connection_id,
                tenant_id=session.tenant_id,
            ),
            auth_context=dataclasses.replace(
                envelope.auth_context,
                permission_snapshot_ref=session.permission_snapshot_ref,
            ),
        )
        context = ProcessorContext(
            normalized_envelope=envelope,
            session=session,
            trace=ProcessorTraceReference(value="trace:p11-fix-16"),
            config_version="config-v1",
            policy_version="policy-v1",
            clock=clock,
            dependencies=ProcessorDependencies(
                authorization=authorization,
                rate_limit=InterfaceOnlyRateLimitEntry(),
                idempotency=InterfaceOnlyIdempotencyPrecheck(),
                routing=InterfaceOnlyRoutingPreparation(),
                response_finalizer=PassthroughResponseFinalizer(),
                error_mapper=DefaultProcessorErrorMapper(),
                principal_type=IamPrincipalType.CLIENT,
                audit_sink=DeterministicTestAuditSink(),
                event_bus=EventBus(
                    task_supervisor=supervisor,
                    default_timeout_seconds=1,
                ),
                task_supervisor=supervisor,
            ),
        )
        original = (
            broker_module.AuthorityAttestorClient.verify_iam_result
        )
        delayed = False

        def delayed_verification(client, **kwargs):
            nonlocal delayed
            if not delayed:
                delayed = True
                time.sleep(0.25)
            return original(client, **kwargs)

        ticks = 0
        running = True

        async def ticker() -> None:
            nonlocal ticks
            while running:
                ticks += 1
                await asyncio.sleep(0.01)

        ticker_task = asyncio.create_task(ticker())
        try:
            with mock.patch.object(
                broker_module.AuthorityAttestorClient,
                "verify_iam_result",
                delayed_verification,
            ):
                evidence = await authorization.authorize(context)
        finally:
            running = False
            await ticker_task
        self.assertTrue(delayed)
        self.assertGreaterEqual(ticks, 8)
        self.assertTrue(evidence.is_contract_test_authority())
        self.assertFalse(evidence.is_production_authority())

    async def test_controlled_clock_offset_honors_receipt_expiry_boundary(
        self,
    ) -> None:
        request = _access_request()
        broker, _ = await self._broker([_decision(request).to_wire()])
        clock = ControlledClock(utc_start=PROCESSOR_NOW)
        service = MessageAuthorizationService.for_broker_contract_tests(
            iam_client=broker.iam,
            clock=clock,
            mode=AuthorizationMode.STRICT,
            cache_ttl_seconds=60,
        )

        result = await service.authorize(
            snapshot=_authorization_snapshot(now=PROCESSOR_NOW),
            request=request,
            risk=OperationRiskContext(),
        )
        receipt = result._broker_verification
        assert receipt is not None
        self.assertGreater(
            abs((datetime.now(timezone.utc) - clock.utc_now()).total_seconds()),
            24 * 60 * 60,
        )
        lifetime = receipt.authority_expires_at - receipt.verified_at
        clock.advance(lifetime.total_seconds() - 0.001)
        self.assertTrue(result.is_issued_by(service))
        clock.advance(0.001)
        self.assertFalse(result.is_issued_by(service))

    async def test_processor_evidence_stale_receipt_retries_authorization(
        self,
    ) -> None:
        from ns_runtime.iam.authorization import _StaleIamSessionReceipt

        decision = IamAccessDecision(
            allowed=True,
            reason="backend_allow",
            permission_version="version:test",
            decided_at=datetime.now(timezone.utc),
        )
        broker, server = await self._broker(
            [decision.to_wire(), decision.to_wire()],
        )
        clock = ControlledClock(utc_start=PROCESSOR_NOW)
        service = MessageAuthorizationService.for_broker_contract_tests(
            iam_client=broker.iam,
            clock=clock,
            mode=AuthorizationMode.STRICT,
            cache_ttl_seconds=30,
        )
        authorization = IamProcessorAuthorization.for_contract_tests(
            service=service,
        )
        supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        self.addAsyncCleanup(supervisor.shutdown, timeout_seconds=1)
        session = _processor_session()
        envelope = _processor_envelope()
        envelope = dataclasses.replace(
            envelope,
            source=dataclasses.replace(
                envelope.source,
                connection_id=session.connection_id,
                tenant_id=session.tenant_id,
            ),
            auth_context=dataclasses.replace(
                envelope.auth_context,
                permission_snapshot_ref=session.permission_snapshot_ref,
            ),
        )
        context = ProcessorContext(
            normalized_envelope=envelope,
            session=session,
            trace=ProcessorTraceReference(value="trace:p11-fix-17"),
            config_version="config-v1",
            policy_version="policy-v1",
            clock=clock,
            dependencies=ProcessorDependencies(
                authorization=authorization,
                rate_limit=InterfaceOnlyRateLimitEntry(),
                idempotency=InterfaceOnlyIdempotencyPrecheck(),
                routing=InterfaceOnlyRoutingPreparation(),
                response_finalizer=PassthroughResponseFinalizer(),
                error_mapper=DefaultProcessorErrorMapper(),
                principal_type=IamPrincipalType.CLIENT,
                audit_sink=DeterministicTestAuditSink(),
                event_bus=EventBus(
                    task_supervisor=supervisor,
                    default_timeout_seconds=1,
                ),
                task_supervisor=supervisor,
            ),
        )
        original = processor_integration_module._authorization_evidence
        attempts = 0

        def stale_once(**kwargs):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise _StaleIamSessionReceipt
            return original(**kwargs)

        with mock.patch.object(
            processor_integration_module,
            "_authorization_evidence",
            side_effect=stale_once,
        ):
            evidence = await authorization.authorize(context)
        self.assertEqual(2, attempts)
        self.assertEqual(2, len(server.calls))
        self.assertTrue(evidence.is_contract_test_authority())
        self.assertTrue(broker._channel._custodian.process.is_alive())

    async def test_payload_evidence_stale_receipt_retries_revalidation(
        self,
    ) -> None:
        from ns_runtime.iam.authorization import _StaleIamSessionReceipt

        now = datetime.now(timezone.utc)
        decision = PayloadRefRevalidationDecision(
            valid=True,
            allowed=True,
            reason="backend_allow",
            object_id="payload:rotation",
            version="version:1",
            checksum="sha256:" + "1" * 64,
            size_bytes=32,
            tenant_id="tenant:1",
            target_principal="identity:1",
            target_fingerprint="sha256:" + "2" * 64,
            permission_snapshot_ref="permission:1",
            permission_version="version:1",
            decision_reference="decision:rotation",
            decided_at=now,
            expires_at=now + timedelta(minutes=5),
        )

        class RetryBoundaryIam:
            def __init__(self) -> None:
                self.calls = 0

            def _is_production_composition_bound_local(self) -> bool:
                return True

            async def revalidate_payload_ref_signed(self, request):
                del request
                self.calls += 1
                return mock.Mock(result=decision)

        iam = RetryBoundaryIam()
        issuer = mock.Mock()
        issuer.issue.side_effect = (_StaleIamSessionReceipt(), None)
        validator = object.__new__(IamDeliveryPayloadReferenceValidator)
        object.__setattr__(validator, "_iam", iam)
        object.__setattr__(validator, "_clock", SystemClock())
        object.__setattr__(validator, "_evidence_issuer", issuer)

        evidence = object.__new__(PayloadEvidence)
        for name, value in {
            "kind": PayloadKind.REFERENCE,
            "object_id": decision.object_id,
            "object_version": decision.version,
            "checksum": decision.checksum,
            "size_bytes": decision.size_bytes,
            "evidence_fingerprint": "sha256:" + "3" * 64,
        }.items():
            object.__setattr__(evidence, name, value)
        delivery = object.__new__(DeliveryRecord)
        for name, value in {
            "payload_evidence": evidence,
            "tenant_id": decision.tenant_id,
            "target_fingerprint": decision.target_fingerprint,
            "policy_decision": mock.Mock(
                request_fingerprint="sha256:" + "4" * 64,
            ),
        }.items():
            object.__setattr__(delivery, name, value)
        target = object.__new__(LocalDeliveryTarget)
        for name, value in {
            "identity": decision.target_principal,
            "tenant_id": decision.tenant_id,
            "permission_snapshot_reference": (
                decision.permission_snapshot_ref
            ),
            "permission_version": decision.permission_version,
            "access_decision_reference": "sha256:" + "5" * 64,
        }.items():
            object.__setattr__(target, name, value)

        result = await validator.validate(delivery, target=target)
        self.assertFalse(result.valid)
        self.assertEqual(2, iam.calls)
        self.assertEqual(2, issuer.issue.call_count)

    async def test_cache_tracks_session_generation_and_expires_authority(
        self,
    ) -> None:
        request = _access_request()
        broker, server = await self._broker(
            [_decision(request).to_wire() for _ in range(8)],
            session_ttl_seconds=3.0,
        )
        try:
            service = MessageAuthorizationService.for_broker_contract_tests(
                iam_client=broker.iam,
                clock=SystemClock(),
                mode=AuthorizationMode.CACHE,
                cache_ttl_seconds=60,
            )
            snapshot = _authorization_snapshot()
            first = await service.authorize(
                snapshot=snapshot,
                request=request,
                risk=OperationRiskContext(),
            )
            old_verified = object.__new__(
                broker_module.VerifiedBrokerIamResult,
            )
            object.__setattr__(old_verified, "result", first.decision)
            object.__setattr__(
                old_verified, "authority", first._broker_authority,
            )
            object.__setattr__(
                old_verified, "verification", first._broker_verification,
            )
            await service.authorize(
                snapshot=snapshot,
                request=request,
                risk=OperationRiskContext(),
            )
            self.assertEqual(1, len(server.calls))

            latest = first
            generation_history = [
                first._broker_verification.lifecycle_generation,
            ]
            for rotation_index in range(3):
                previous_generation = generation_history[-1]
                await self._wait_for_current_certificate_rotation_window(
                    broker.iam._channel,
                    clock=broker.iam._clock,
                )
                rotated = await broker.iam.access_check_signed(request)
                actual_generation = (
                    rotated.verification.lifecycle_generation
                )
                self.assertGreater(
                    actual_generation,
                    previous_generation,
                    msg=f"rotation barrier {rotation_index} did not advance",
                )
                latest = await service.authorize(
                    snapshot=snapshot,
                    request=request,
                    risk=OperationRiskContext(),
                )
                self.assertEqual(
                    actual_generation,
                    latest._broker_verification.lifecycle_generation,
                )
                generation_history.append(actual_generation)
                calls_after_source = len(server.calls)
                cached_results = await asyncio.gather(*(
                    service.authorize(
                        snapshot=snapshot,
                        request=request,
                        risk=OperationRiskContext(),
                    )
                    for _ in range(20)
                ))
                self.assertTrue(all(
                    result._broker_verification.lifecycle_generation
                    == actual_generation
                    for result in cached_results
                ))
                self.assertEqual(calls_after_source, len(server.calls))
            self.assertEqual(4, len(set(generation_history)))
            self.assertEqual(7, len(server.calls))
            self.assertFalse(
                broker.iam._verified_broker_iam_result_is_current_local(
                    old_verified,
                    operation="runtime_access_check",
                    request_fingerprint=(
                        old_verified.authority.request_fingerprint
                    ),
                    now=datetime.now(timezone.utc),
                ),
            )
            self.assertFalse(first.is_issued_by(service))
            latest_verified = object.__new__(
                broker_module.VerifiedBrokerIamResult,
            )
            object.__setattr__(latest_verified, "result", latest.decision)
            object.__setattr__(
                latest_verified, "authority", latest._broker_authority,
            )
            object.__setattr__(
                latest_verified, "verification",
                latest._broker_verification,
            )
            self.assertTrue(
                broker.iam._verified_broker_iam_result_is_current_local(
                    latest_verified,
                    operation="runtime_access_check",
                    request_fingerprint=(
                        latest_verified.authority.request_fingerprint
                    ),
                    now=datetime.now(timezone.utc),
                ),
            )
            cache_key = next(iter(service._decisions))
            service._decisions[cache_key] = dataclasses.replace(
                service._decisions[cache_key],
                authority_expires_at=(
                    datetime.now(timezone.utc) - timedelta(seconds=1)
                ),
            )
            refreshed = await service.authorize(
                snapshot=snapshot,
                request=request,
                risk=OperationRiskContext(),
            )
            self.assertEqual(8, len(server.calls))
            self.assertEqual(
                generation_history[-1],
                refreshed._broker_verification.lifecycle_generation,
            )
            self.assertTrue(broker._channel._custodian.process.is_alive())
            self.assertTrue(broker._channel._custodian.attestor.alive)
        finally:
            self._close_broker_and_assert_reaped(broker)

    async def test_endpoint_identity_provenance_failure_reaps_graph(
        self,
    ) -> None:
        broker, _ = await self._broker([])
        proxies = (
            broker.iam,
            broker.repositories.admission,
            broker.repositories.scheduler,
            broker.repositories.payload,
            broker.repositories.registry,
            broker.repositories.audit,
            broker.state_store,
        )
        connections = tuple(proxy._channel._connection for proxy in proxies)
        channel = broker.state_store._channel
        process = channel._custodian.process
        attestor = channel._attestor
        original = (
            broker_module.AuthorityAttestorClient
            .current_endpoint_identity
        )

        def wrong_endpoint(client, **kwargs):
            result = original(client, **kwargs)
            if kwargs.get("endpoint_id") == channel.endpoint_id:
                result["endpoint_id"] = "endpoint_wrong"
            return result

        with mock.patch.object(
            broker_module.AuthorityAttestorClient,
            "current_endpoint_identity",
            wrong_endpoint,
        ):
            with self.assertRaises(NsRuntimeStateStoreUnavailableError):
                await broker.state_store.health()
        self.assertFalse(process.is_alive())
        self.assertFalse(attestor.alive)
        self.assertTrue(all(connection.closed for connection in connections))

    async def test_rotation_decode_failure_is_presend_unavailable_and_reaps(
        self,
    ) -> None:
        for attack in ("missing_certificate", "wrong_generation"):
            with self.subTest(attack=attack):
                broker, _ = await self._broker(
                    [],
                    session_ttl_seconds=5.0,
                )
                transaction = self._admission_transaction(
                    broker,
                    suffix=attack,
                )
                channel = broker.repositories.admission._channel
                process = channel._custodian.process
                attestor = channel._attestor
                connections = tuple(
                    proxy._channel._connection
                    for proxy in (
                        broker.iam,
                        broker.repositories.admission,
                        broker.repositories.scheduler,
                        broker.repositories.payload,
                        broker.repositories.registry,
                        broker.repositories.audit,
                        broker.state_store,
                    )
                )

                def mutate(message):
                    certificate = message.get("session_certificate")
                    if attack == "missing_certificate":
                        message.pop("session_certificate", None)
                    else:
                        assert type(certificate) is dict
                        certificate["lifecycle_generation"] = (
                            int(certificate["lifecycle_generation"]) + 1
                        )
                    return message

                wrapper = _RotationResponseMutator(
                    channel._connection,
                    mutate,
                )
                object.__setattr__(channel, "_connection", wrapper)
                await self._wait_for_current_certificate_rotation_window(
                    channel,
                    clock=broker.iam._clock,
                )
                with self.assertRaises(
                    NsRuntimeStateStoreUnavailableError,
                ):
                    await broker.repositories.admission.transact(
                        transaction,
                    )
                self.assertTrue(wrapper.saw_rotation_response)
                self.assertNotIn("request", wrapper.sent_kinds)
                self.assertFalse(process.is_alive())
                self.assertFalse(attestor.alive)
                self.assertTrue(
                    all(connection.closed for connection in connections),
                )

    async def test_local_validation_does_not_reap_broker(self) -> None:
        broker, _ = await self._broker([])
        process = broker._channel._custodian.process
        with self.assertRaises(
            NsRuntimeStateStoreCapabilityUnavailableError,
        ):
            await broker.repositories.admission._request(
                "read_payload_body",
                {},
            )
        with self.assertRaises(NsValidationError):
            await broker.repositories.admission._request(
                "transact_admission",
                object(),
            )
        with self.assertRaises(
            NsRuntimeStateStoreCapabilityUnavailableError,
        ):
            await broker.repositories.audit._request(
                "read_delivery",
                {},
            )
        with self.assertRaises(
            NsRuntimeStateStoreCapabilityUnavailableError,
        ):
            await broker.repositories.admission._request(
                "append_processor_audit",
                {},
            )
        with self.assertRaises(
            NsRuntimeStateStoreCapabilityUnavailableError,
        ):
            await broker.repositories.audit.append_processor_audit(
                document=StateDocument(
                    schema_name="runtime.connection_lifecycle_audit",
                    schema_version=1,
                    state_version=1,
                    payload=b"{}",
                ),
            )
        self.assertTrue(process.is_alive())
        health = await broker.state_store.health()
        self.assertEqual("ready", health.status.value)

    async def test_close_closes_all_parent_endpoints_and_is_idempotent(
        self,
    ) -> None:
        broker, _ = await self._broker([])
        proxies = (
            broker.iam,
            broker.repositories.admission,
            broker.repositories.scheduler,
            broker.repositories.payload,
            broker.repositories.registry,
            broker.repositories.audit,
            broker.state_store,
        )
        connections = tuple(proxy._channel._connection for proxy in proxies)
        process = broker._channel._custodian.process
        attestor_process = broker._channel._attestor._process
        self.assertEqual(7, len({id(value) for value in connections}))
        broker.close()
        self.assertTrue(all(value.closed for value in connections))
        self.assertFalse(process.is_alive())
        self.assertFalse(attestor_process.is_alive())
        broker.close()

    @unittest.skipUnless(os.name == "posix", "requires POSIX process signals")
    async def test_close_kills_broker_stuck_in_operation(self) -> None:
        broker, _ = await self._broker([])
        process = broker._channel._custodian.process
        os.kill(process.pid, signal.SIGSTOP)
        broker.close()
        self.assertFalse(process.is_alive())

    async def test_signed_result_rejects_cross_request_operation_and_broker(
        self,
    ) -> None:
        request = _access_request()
        first, _ = await self._broker([_decision(request).to_wire()])
        second, _ = await self._broker([])
        verified = await first.iam.access_check_signed(request)
        authority = verified.authority
        now = datetime.now(timezone.utc)
        self.assertTrue(authority.verify(
            public_key=first.public_key,
            broker_instance_id=first.broker_instance_id,
            operation=authority.operation,
            request_fingerprint=authority.request_fingerprint,
            now=now,
        ))
        self.assertFalse(authority.verify(
            public_key=second.public_key,
            broker_instance_id=second.broker_instance_id,
            operation=authority.operation,
            request_fingerprint=authority.request_fingerprint,
            now=now,
        ))
        self.assertFalse(authority.verify(
            public_key=first.public_key,
            broker_instance_id=first.broker_instance_id,
            operation="payload_revalidate",
            request_fingerprint=authority.request_fingerprint,
            now=now,
        ))
        self.assertFalse(authority.verify(
            public_key=first.public_key,
            broker_instance_id=first.broker_instance_id,
            operation=authority.operation,
            request_fingerprint="sha256:" + "0" * 64,
            now=now,
        ))
        with self.assertRaises(NsValidationError):
            copy.copy(authority)
        tampered = dataclasses.replace(
            authority,
            broker_instance_id=second.broker_instance_id,
        )
        self.assertFalse(tampered.verify(
            public_key=second.public_key,
            broker_instance_id=second.broker_instance_id,
            operation=tampered.operation,
            request_fingerprint=tampered.request_fingerprint,
            now=now,
        ))

    async def test_contract_broker_cannot_impersonate_production_authorization(
        self,
    ) -> None:
        request = _access_request()
        broker, _ = await self._broker([_decision(request).to_wire()])
        now = datetime.now(timezone.utc)
        clock = SystemClock()
        snapshot = PermissionSnapshot.from_introspection(
            IamIntrospectionResult(
                identity=request.identity,
                tenant_id=request.tenant_id,
                principal_type=IamPrincipalType.CLIENT,
                component_type="client",
                capabilities=frozenset({"runtime.connection"}),
                permission_snapshot_ref=request.permission_snapshot_ref,
                permission_digest="sha256:broker-snapshot",
                permission_version=request.permission_version,
                issued_at=now - timedelta(seconds=1),
                expires_at=now + timedelta(minutes=5),
                credential_status=IamCredentialStatus.ACTIVE,
                resume_eligible=True,
            ),
            iam_mode="strict",
        )
        del snapshot, clock
        with self.assertRaises(NsValidationError):
            MessageAuthorizationService(
                iam_client=broker.iam,
                clock=SystemClock(),
                mode=AuthorizationMode.STRICT,
                cache_ttl_seconds=30,
            )
        verified = await broker.iam.access_check_signed(request)
        self.assertTrue(verified.result.allowed)
        self.assertEqual(request.permission_version, verified.result.permission_version)
        self.assertEqual("backend_allow", verified.result.reason)
        self.assertEqual(
            "contract-test",
            broker._channel.certificate.trust_realm,
        )

    async def test_exact_realm_types_and_certificate_chain_reject_forgery(
        self,
    ) -> None:
        broker, _ = await self._broker([])
        channel = broker._channel
        self.assertIs(
            broker_module._ContractTestRoleBrokerChannel,
            type(channel),
        )
        with self.assertRaises(AttributeError):
            object.__setattr__(channel, "_realm", "production")

        forged_iam = object.__new__(ProductionIamAuthorityProxy)
        for name, value in (
            ("_channel", channel),
            ("_handle", broker.iam._handle),
            ("_clock", SystemClock()),
            ("_iam_mode", "strict"),
            ("_authorization_service", None),
        ):
            object.__setattr__(forged_iam, name, value)
        self.assertFalse(forged_iam._is_production_adapter())

        contract_admission = broker.repositories.admission
        self.assertIs(
            broker_module._ContractTestAdmissionRepositoryProxy,
            type(contract_admission),
        )
        original_role = (
            broker_module._ContractTestAdmissionRepositoryProxy._ROLE
        )
        broker_module._ContractTestAdmissionRepositoryProxy._ROLE = (
            BrokerRepositoryRole.SCHEDULER
        )
        try:
            self.assertIs(
                BrokerRepositoryRole.ADMISSION,
                contract_admission.role,
            )
        finally:
            broker_module._ContractTestAdmissionRepositoryProxy._ROLE = (
                original_role
            )
        forged_repository = object.__new__(AdmissionRepositoryProxy)
        object.__setattr__(
            forged_repository, "_channel", channel,
        )
        object.__setattr__(
            forged_repository, "_handle", contract_admission._handle,
        )
        self.assertFalse(forged_repository._binding_is_current())
        with self.assertRaises(NsValidationError):
            RuntimeDependencySlots(
                delivery_admission_persistence=forged_repository,
            )
        with self.assertRaises(
            NsRuntimeStateStoreCapabilityUnavailableError,
        ):
            await forged_repository._request("read_delivery", {})

        empty_channel = object.__new__(
            broker_module._ProductionRoleBrokerChannel,
        )
        self.assertFalse(empty_channel._identity_is_current(
            datetime.now(timezone.utc),
        ))
        empty_proxy = object.__new__(ProductionIamAuthorityProxy)
        object.__setattr__(empty_proxy, "_channel", empty_channel)
        object.__setattr__(empty_proxy, "_handle", object())
        self.assertFalse(empty_proxy._is_production_adapter())

    async def test_proxy_metadata_changes_do_not_change_endpoint_role(
        self,
    ) -> None:
        broker, _ = await self._broker([])
        admission = broker.repositories.admission
        original_binding = broker_module._repository_proxy_binding
        try:
            broker_module._repository_proxy_binding = (
                lambda proxy_type: (
                    BrokerRepositoryRole.SCHEDULER,
                    broker_module._ProductionRoleBrokerChannel,
                )
            )
            self.assertFalse(broker.iam._is_production_adapter())
            self.assertFalse(admission._binding_is_current())
            with self.assertRaises(
                NsRuntimeStateStoreCapabilityUnavailableError,
            ):
                await admission._request("read_payload_body", {})
        finally:
            broker_module._repository_proxy_binding = original_binding

    async def test_main_session_metadata_is_refreshed_from_attestor(
        self,
    ) -> None:
        broker, _ = await self._broker([])
        channel = broker._channel
        certificate = channel._certificate
        public_key = channel._public_key

        object.__setattr__(
            channel,
            "_certificate",
            dataclasses.replace(
                certificate,
                broker_instance_id="broker_tampered",
            ),
        )
        self.assertTrue(channel._identity_is_current(
            datetime.now(timezone.utc),
        ))
        self.assertEqual(certificate, channel._certificate)

        object.__setattr__(channel, "_public_key", os.urandom(32))
        self.assertTrue(channel._identity_is_current(
            datetime.now(timezone.utc),
        ))
        self.assertEqual(public_key, channel._public_key)

        object.__setattr__(
            channel,
            "_certificate",
            dataclasses.replace(
                certificate,
                issued_at=datetime.now(timezone.utc) - timedelta(minutes=2),
                expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            ),
        )
        self.assertTrue(channel._identity_is_current(
            datetime.now(timezone.utc),
        ))
        self.assertEqual(certificate, channel._certificate)
        root = Ed25519PrivateKey.generate()
        session_public = Ed25519PrivateKey.generate().public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        expired = _test_certificate(
            root,
            session_public,
            issued_at=datetime.now(timezone.utc) - timedelta(minutes=2),
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        self.assertFalse(expired.verify(
            root.public_key().public_bytes(
                serialization.Encoding.Raw,
                serialization.PublicFormat.Raw,
            ),
            expected_realm="contract-test",
            expected_runtime_id=expired.runtime_id,
            expected_instance_id=expired.broker_instance_id,
            expected_session_public_key=expired.session_public_key,
            expected_generation=expired.lifecycle_generation,
            now=datetime.now(timezone.utc),
        ))

    def test_unsigned_state_response_is_rejected_and_process_reaped(
        self,
    ) -> None:
        channel, process, _, session, certificate = _test_channel(
            lambda sent: encode_frame({
                "version": 1,
                "kind": "response",
                "request_id": "unsigned",
                "result": {},
            }),
        )
        del session, certificate
        with self.assertRaises(NsRuntimeStateStoreUnavailableError):
            channel.request(
                operation="state_health",
                payload={},
            )
        self.assertFalse(process.is_alive())
        channel.close()
        self.assertFalse(process.is_alive())

    def test_signed_state_response_replay_bindings_fail_closed(self) -> None:
        attacks = (
            "operation", "handle", "broker", "request_id",
            "fingerprint", "sequence", "result", "error",
        )
        for attack in attacks:
            with self.subTest(attack=attack):
                holder: dict[str, object] = {}

                def response(sent):
                    session = holder["session"]
                    certificate = holder["certificate"]
                    handle = holder["handle"]
                    assert isinstance(session, Ed25519PrivateKey)
                    assert isinstance(
                        certificate, BrokerInstanceCertificate,
                    )
                    assert isinstance(handle, BrokerAuthorityHandle)
                    response_session = session
                    response_handle = None
                    operation = None
                    if attack == "operation":
                        operation = "read_delivery"
                    elif attack == "handle":
                        response_handle = broker_module._new_handle(
                            private_key=session,
                            instance_id=certificate.broker_instance_id,
                            endpoint_id="endpoint_admission",
                            role=BrokerRepositoryRole.ADMISSION,
                            runtime_id=certificate.runtime_id,
                            generation=1,
                        )
                    elif attack == "broker":
                        response_session = Ed25519PrivateKey.generate()
                    raw = _signed_response_bytes(
                        sent,
                        session=response_session,
                        certificate=certificate,
                        response_sequence=(2 if attack == "sequence" else 1),
                        operation=operation,
                        response_handle=response_handle,
                        error=(
                            {
                                "kind": "state_unavailable",
                                "reason": "signed_error",
                                "details": {
                                    "component": "authority_broker",
                                },
                            }
                            if attack == "error" else None
                        ),
                    )
                    if attack in {
                        "request_id", "fingerprint", "result", "error",
                    }:
                        envelope = decode_frame(raw)
                        assert type(envelope) is dict
                        signed_values = envelope["signed_response"]
                        assert type(signed_values) is dict
                        if attack == "request_id":
                            signed_values["request_id"] = "ipc_replayed"
                        elif attack == "fingerprint":
                            signed_values["request_fingerprint"] = (
                                "sha256:" + "0" * 64
                            )
                        elif attack == "result":
                            signed_values["result_json"] = (
                                '{"tampered":true}'
                            )
                        else:
                            signed_values["error_json"] = (
                                '{"kind":"state_denied"}'
                            )
                        return encode_frame(envelope)
                    return raw

                channel, process, _, session, certificate = _test_channel(
                    response,
                )
                handle = channel.handle
                holder.update({
                    "session": session,
                    "certificate": certificate,
                    "handle": handle,
                })
                with self.assertRaises(NsRuntimeStateStoreUnavailableError):
                    channel.request(
                        operation="state_health",
                        payload={},
                    )
                self.assertFalse(process.is_alive())

    def test_response_sequence_replay_and_write_signature_failure(
        self,
    ) -> None:
        holder: dict[str, object] = {"calls": 0}

        def replay(sent):
            holder["calls"] = int(holder["calls"]) + 1
            return _signed_response_bytes(
                sent,
                session=holder["session"],  # type: ignore[arg-type]
                certificate=holder["certificate"],  # type: ignore[arg-type]
                response_sequence=1,
            )

        channel, process, _, session, certificate = _test_channel(replay)
        holder.update({
            "session": session,
            "certificate": certificate,
        })
        self.assertEqual(
            {"status": "ok"},
            channel.request(
                operation="state_health",
                payload={},
            ),
        )
        with self.assertRaises(NsRuntimeStateStoreUnavailableError):
            channel.request(
                operation="state_health",
                payload={},
            )
        self.assertFalse(process.is_alive())

        write_holder: dict[str, object] = {}

        def wrong_write_signature(sent):
            return _signed_response_bytes(
                sent,
                session=Ed25519PrivateKey.generate(),
                certificate=write_holder["certificate"],  # type: ignore[arg-type]
                response_sequence=1,
                result={"records": [], "log_positions": []},
            )

        write_channel, write_process, _, write_session, write_cert = (
            _test_channel(
                wrong_write_signature,
                role=BrokerRepositoryRole.ADMISSION,
            )
        )
        write_holder["certificate"] = write_cert
        del write_session
        with self.assertRaises(NsRuntimeStateStoreIndeterminateWriteError):
            write_channel.request(
                operation="transact_admission",
                payload={},
            )
        self.assertFalse(write_process.is_alive())

    async def test_payload_revalidation_is_broker_signed_and_request_bound(
        self,
    ) -> None:
        request = PayloadRefRevalidationRequest(
            object_id="object:1",
            version="version:1",
            checksum="sha256:payload",
            size_bytes=32,
            tenant_id="tenant:1",
            target_principal="identity:1",
            target_tenant_id="tenant:1",
            target_fingerprint="sha256:target",
            permission_snapshot_ref="permission:1",
            permission_version="version:1",
            admission_authority_reference="admission:1",
        )
        now = datetime.now(timezone.utc)
        decision = PayloadRefRevalidationDecision(
            valid=True,
            allowed=True,
            reason="acl_allow",
            object_id=request.object_id,
            version=request.version,
            checksum=request.checksum,
            size_bytes=request.size_bytes,
            tenant_id=request.tenant_id,
            target_principal=request.target_principal,
            target_fingerprint=request.target_fingerprint,
            permission_snapshot_ref=request.permission_snapshot_ref,
            permission_version=request.permission_version,
            decision_reference="iam-payload:broker",
            decided_at=now,
            expires_at=now + timedelta(minutes=5),
        )
        broker, _ = await self._broker([decision.to_wire()])
        verified = await broker.iam.revalidate_payload_ref_signed(request)
        self.assertEqual(decision, verified.result)
        self.assertEqual(
            request.to_wire(),
            verified.authority.request_mapping(),
        )
        with mock.patch.object(
            broker_module.AuthorityAttestorClient,
            "verify_iam_result",
            side_effect=AssertionError("synchronous attestor IPC"),
        ), mock.patch.object(
            broker_module.AuthorityAttestorClient,
            "current_endpoint_identity",
            side_effect=AssertionError("synchronous identity IPC"),
        ):
            self.assertTrue(
                broker.iam
                ._verified_broker_iam_result_is_current_local(
                    verified,
                    operation="payload_revalidate",
                    request_fingerprint=(
                        verified.authority.request_fingerprint
                    ),
                    now=datetime.now(timezone.utc),
                ),
            )
        replay_request = dataclasses.replace(
            request,
            object_id="object:2",
        )
        from ns_runtime.authority_broker import broker_request_fingerprint

        self.assertFalse(verified.authority.verify(
            public_key=broker.public_key,
            broker_instance_id=broker.broker_instance_id,
            operation="payload_revalidate",
            request_fingerprint=broker_request_fingerprint(
                "payload_revalidate",
                replay_request,
            ),
            now=datetime.now(timezone.utc),
        ))

    async def test_short_ttl_rotates_three_sessions_without_downtime(
        self,
    ) -> None:
        request = _access_request()
        broker, _ = await self._broker(
            [_decision(request).to_wire() for _ in range(12)],
            # Keep the real child-process certificate alive longer than one
            # broker/attestor/HTTP round trip under full-suite load. Exact
            # rotation and exclusive-expiry boundaries use ControlledClock.
            session_ttl_seconds=5.0,
        )
        old_handle = broker.repositories.admission._handle
        old_verified = None
        previous_generation = broker.current_session_identity()[
            "lifecycle_generation"
        ]
        for _ in range(3):
            deadline = asyncio.get_running_loop().time() + 20.0
            current_generation = previous_generation
            while current_generation <= previous_generation:
                if asyncio.get_running_loop().time() >= deadline:
                    self.fail("session generation did not advance before deadline")
                certificate = broker.iam._channel.certificate
                lifetime = (
                    certificate.expires_at - certificate.issued_at
                ).total_seconds()
                trigger_at = certificate.issued_at + timedelta(
                    seconds=lifetime * 0.75,
                )
                delay = (
                    trigger_at - broker.iam._clock.utc_now()
                ).total_seconds()
                if delay > 0:
                    await asyncio.sleep(delay)
                signed = await broker.iam.access_check_signed(request)
                current_generation = broker.current_session_identity()[
                    "lifecycle_generation"
                ]
            if old_verified is None:
                old_verified = signed
            self.assertGreater(current_generation, previous_generation)
            previous_generation = current_generation
            identity = broker.current_session_identity()
            self.assertEqual(
                identity["session_public_key"], broker.public_key,
            )
            self.assertEqual(
                identity["session_key_fingerprint"],
                broker_module._session_key_fingerprint(
                    broker.public_key,
                ),
            )
            await broker.state_store.health()
        self.assertFalse(old_handle.verify(
            broker._channel.public_key,
            instance_id=broker._channel.instance_id,
        ))
        assert old_verified is not None
        self.assertFalse(
            broker.iam._verified_broker_iam_result_is_current_local(
                old_verified,
                operation="runtime_access_check",
                request_fingerprint=(
                    old_verified.authority.request_fingerprint
                ),
                now=datetime.now(timezone.utc),
            ),
        )

    async def test_rotation_serializes_concurrent_iam_and_state_requests(
        self,
    ) -> None:
        request = _access_request()
        broker, _ = await self._broker(
            [_decision(request).to_wire() for _ in range(4)],
            session_ttl_seconds=5.0,
        )
        await self._wait_for_current_certificate_rotation_window(
            broker.iam._channel,
            clock=broker.iam._clock,
        )
        results = await asyncio.gather(
            *(broker.iam.access_check(request) for _ in range(4)),
            broker.state_store.health(),
        )
        self.assertTrue(all(result.allowed for result in results[:4]))
        self.assertGreaterEqual(
            broker.current_session_identity()["lifecycle_generation"], 2,
        )
        self.assertTrue(broker._channel._identity_is_current())

    async def test_repository_handles_are_fixed_and_cross_role_denied(
        self,
    ) -> None:
        broker, _ = await self._broker([])
        admission = broker.repositories.admission
        scheduler = broker.repositories.scheduler
        payload = broker.repositories.payload
        registry = broker.repositories.registry
        with self.assertRaises(NsRuntimeStateStoreCapabilityUnavailableError):
            await admission._request("transact_scheduler", object())
        with self.assertRaises(NsRuntimeStateStoreCapabilityUnavailableError):
            await scheduler._request("read_payload_body", object())
        with self.assertRaises(NsRuntimeStateStoreCapabilityUnavailableError):
            await payload._request("read_delivery", object())
        with self.assertRaises(NsRuntimeStateStoreCapabilityUnavailableError):
            await registry._request("read_scheduler_index", object())
        with self.assertRaises(AttributeError):
            scheduler.read_payload_body  # type: ignore[attr-defined]
        with self.assertRaises(AttributeError):
            payload.read_delivery  # type: ignore[attr-defined]
        original = admission._handle
        forged = dataclasses.replace(
            original,
            role=BrokerRepositoryRole.SCHEDULER,
        )
        object.__setattr__(admission, "_handle", forged)
        with self.assertRaises(NsRuntimeStateStoreCapabilityUnavailableError):
            await admission.read_delivery(
                tenant_id="tenant:1",
                bucket_id=0,
                layout_generation=1,
                delivery_id="delivery:1",
            )
        object.__setattr__(admission, "_handle", original)

    async def test_each_proxy_owns_one_role_endpoint_without_handle_table(
        self,
    ) -> None:
        broker, _ = await self._broker([])
        proxies = (
            broker.iam,
            broker.repositories.admission,
            broker.repositories.scheduler,
            broker.repositories.payload,
            broker.repositories.registry,
            broker.repositories.audit,
            broker.state_store,
        )
        channels = tuple(proxy._channel for proxy in proxies)
        self.assertEqual(7, len({id(channel) for channel in channels}))
        self.assertEqual(
            {role for role in BrokerRepositoryRole},
            {channel.role for channel in channels},
        )
        self.assertEqual(
            7, len({channel.endpoint_id for channel in channels}),
        )
        self.assertIs(
            BrokerRepositoryRole.PAYLOAD,
            broker.repositories.payload._channel.role,
        )
        self.assertIs(
            BrokerRepositoryRole.SCHEDULER,
            broker.repositories.scheduler._channel.role,
        )
        self.assertIsNot(
            broker.repositories.payload._channel,
            broker.repositories.scheduler._channel,
        )
        for channel in channels:
            self.assertFalse(hasattr(channel, "_handles"))
            self.assertFalse(hasattr(channel, "current_handle"))
            for slot in broker_module._RoleBrokerChannel.__slots__:
                if not hasattr(channel, slot):
                    continue
                value = getattr(channel, slot)
                self.assertFalse(
                    type(value) is dict
                    and set(value) == {
                        role.value for role in BrokerRepositoryRole
                    },
                )
        custodian = broker._channel._custodian
        self.assertEqual(
            7,
            len(custodian._endpoint_close_resources),
        )
        for resource in custodian._endpoint_close_resources:
            self.assertFalse(hasattr(resource, "role"))
            self.assertFalse(hasattr(resource, "handle"))
            self.assertFalse(hasattr(resource, "request"))
        for slot in type(custodian).__slots__:
            value = getattr(custodian, slot)
            if type(value) is dict:
                self.assertFalse(
                    all(
                        isinstance(
                            item, broker_module._RoleBrokerChannel,
                        )
                        for item in value.values()
                    ),
                )

    async def test_raw_role_endpoints_reject_cross_role_operations(
        self,
    ) -> None:
        for source_role, operation in (
            (BrokerRepositoryRole.PAYLOAD, "transact_scheduler"),
            (BrokerRepositoryRole.ADMISSION, "read_payload_body"),
        ):
            with self.subTest(source_role=source_role.value):
                broker, _ = await self._broker([])
                channel = {
                    BrokerRepositoryRole.PAYLOAD:
                        broker.repositories.payload._channel,
                    BrokerRepositoryRole.ADMISSION:
                        broker.repositories.admission._channel,
                }[source_role]
                process = channel._custodian.process
                channel._connection.send_bytes(encode_frame({
                    "version": 1,
                    "kind": "request",
                    "request_id": "raw-cross-role",
                    "request_sequence": 1,
                    "operation": operation,
                    "payload": {},
                    "attestation": {},
                }))
                for _ in range(100):
                    if not process.is_alive():
                        break
                    await asyncio.sleep(0.01)
                self.assertFalse(process.is_alive())
                broker.close()

    async def test_attestor_death_reaps_broker_for_write_and_health(
        self,
    ) -> None:
        for operation in ("write", "health"):
            with self.subTest(operation=operation):
                broker, _ = await self._broker([])
                channel = (
                    broker.repositories.admission._channel
                    if operation == "write"
                    else broker.state_store._channel
                )
                process = channel._custodian.process
                attestor_process = channel._attestor._process
                attestor_process.terminate()
                attestor_process.join(timeout=5.0)
                with self.assertRaises(
                    NsRuntimeStateStoreUnavailableError,
                ):
                    if operation == "write":
                        await broker.repositories.admission._request(
                            "transact_admission", {},
                        )
                    else:
                        await broker.state_store.health()
                self.assertFalse(process.is_alive())
                self.assertFalse(channel._attestor.alive)

    async def test_main_http_monkey_patch_cannot_change_broker_transport(
        self,
    ) -> None:
        request = _access_request()
        broker, server = await self._broker([_decision(request).to_wire()])

        async def hostile(*args, **kwargs):
            del args, kwargs
            raise AssertionError("main-process HTTP method executed")

        with mock.patch.object(NsAsyncHttpClient, "post", hostile), \
                mock.patch.object(NsAsyncHttpClient, "request", hostile):
            result = await broker.iam.access_check(request)
        self.assertTrue(result.allowed)
        self.assertEqual(1, len(server.calls))

    async def test_broker_crash_and_restart_fail_closed(self) -> None:
        request = _access_request()
        first, _ = await self._broker([_decision(request).to_wire()])
        signed = await first.iam.access_check_signed(request)
        old_handle = first.repositories.admission._handle
        first._channel._custodian.process.terminate()
        first._channel._custodian.process.join(timeout=5.0)
        with self.assertRaises(NsRuntimeIamUnavailableError):
            await first.iam.access_check(request)
        with self.assertRaises(NsRuntimeStateStoreUnavailableError):
            await first.repositories.admission._request(
                "transact_admission",
                {},
            )

        second, _ = await self._broker([])
        self.assertFalse(old_handle.verify(
            second.public_key,
            instance_id=second.broker_instance_id,
        ))
        self.assertFalse(signed.authority.verify(
            public_key=second.public_key,
            broker_instance_id=second.broker_instance_id,
            operation=signed.authority.operation,
            request_fingerprint=signed.authority.request_fingerprint,
            now=datetime.now(timezone.utc),
        ))

    async def test_main_object_graph_contains_no_private_authority_material(
        self,
    ) -> None:
        broker, _ = await self._broker([])
        forbidden_type_names = {
            "NsAsyncHttpClient", "AsyncClient", "RedisValkeyStateStore",
            "_ProductionStateScopeValidator", "_StateScopeIssuer",
        }
        pending = [broker, broker.iam, broker.repositories, broker.state_store]
        seen: set[int] = set()
        while pending:
            value = pending.pop()
            if id(value) in seen:
                continue
            seen.add(id(value))
            self.assertNotIsInstance(value, Ed25519PrivateKey)
            self.assertNotIn(type(value).__name__, forbidden_type_names)
            for name in getattr(type(value), "__slots__", ()):
                if name in {"__weakref__"} or not hasattr(value, name):
                    continue
                child = getattr(value, name)
                if type(child).__module__.startswith(("ns_runtime", "ns_common")):
                    pending.append(child)
                elif isinstance(child, (tuple, list, dict)):
                    pending.extend(
                        child.values() if isinstance(child, dict) else child
                    )

    def test_transaction_fingerprint_binds_payload_and_result_items(
        self,
    ) -> None:
        partition = DeliveryPersistencePartition(
            tenant_id="tenant:1",
            bucket_id=0,
            layout_generation=1,
            namespace=StateNamespace.tenant(
                tenant_id="tenant:1",
                domain="delivery",
            ),
        )
        key = StateKey(
            namespace=partition.namespace,
            object_type="delivery",
            object_id="delivery:1",
        )

        def transaction(payload: bytes) -> DeliveryPersistenceTransaction:
            return DeliveryPersistenceTransaction(
                partition=partition,
                mutations=(StateMutation(
                    key=key,
                    assertion=StateAssertion.absent(),
                    kind=StateMutationKind.CREATE,
                    document=StateDocument(
                        schema_name="delivery_delivery",
                        schema_version=1,
                        state_version=1,
                        payload=payload,
                    ),
                ),),
                record_assertions=(
                    StateRecordReadAssertion.absent(StateKey(
                        namespace=partition.namespace,
                        object_type="payload_body",
                        object_id="payload:1",
                    )),
                ),
            )

        first = transaction(b'{"payload":"first"}')
        second = transaction(b'{"payload":"second"}')
        self.assertNotEqual(first.fingerprint, second.fingerprint)
        assert first.mutations[0].document is not None
        record = StateRecord(
            key=key,
            document=first.mutations[0].document,
            revision=StateRevision._issue("revision:1"),
            committed_at=datetime.now(timezone.utc),
        )
        result = DeliveryPersistenceTransactionResult.for_transaction(
            first,
            records=(record,),
            log_positions=(),
        )
        self.assertTrue(result.is_for_transaction(first))
        self.assertFalse(result.is_for_transaction(second))
        self.assertFalse(result.is_for_transaction(transaction(
            b'{"payload":"first"}',
        )))
        with self.assertRaises(NsValidationError):
            copy.copy(result)
        with self.assertRaises(NsValidationError):
            dataclasses.replace(result)
        with self.assertRaises(NsValidationError):
            DeliveryPersistenceTransactionResult(
                records=(record,),
                log_positions=(),
                request_fingerprint=first.fingerprint,
            )
        wrong_record = StateRecord(
            key=StateKey(
                namespace=partition.namespace,
                object_type="delivery",
                object_id="delivery:other",
            ),
            document=first.mutations[0].document,
            revision=StateRevision._issue("revision:2"),
            committed_at=datetime.now(timezone.utc),
        )
        with self.assertRaises(NsValidationError):
            DeliveryPersistenceTransactionResult.for_transaction(
                first,
                records=(wrong_record,),
                log_positions=(),
            )
        object.__setattr__(result, "records", (wrong_record,))
        self.assertFalse(result.is_for_transaction(first))

        second_key = StateKey(
            namespace=partition.namespace,
            object_type="delivery",
            object_id="delivery:2",
        )
        second_document = StateDocument(
            schema_name="delivery_delivery",
            schema_version=1,
            state_version=1,
            payload=b'{"payload":"second-record"}',
        )
        multi = DeliveryPersistenceTransaction(
            partition=partition,
            mutations=(
                first.mutations[0],
                StateMutation(
                    key=second_key,
                    assertion=StateAssertion.absent(),
                    kind=StateMutationKind.CREATE,
                    document=second_document,
                ),
            ),
        )
        first_record = StateRecord(
            key=key,
            document=first.mutations[0].document,
            revision=StateRevision._issue("revision:multi-1"),
            committed_at=datetime.now(timezone.utc),
        )
        second_record = StateRecord(
            key=second_key,
            document=second_document,
            revision=StateRevision._issue("revision:multi-2"),
            committed_at=datetime.now(timezone.utc),
        )
        with self.assertRaises(NsValidationError):
            DeliveryPersistenceTransactionResult.for_transaction(
                multi,
                records=(second_record, first_record),
                log_positions=(),
            )

if __name__ == "__main__":
    unittest.main()
