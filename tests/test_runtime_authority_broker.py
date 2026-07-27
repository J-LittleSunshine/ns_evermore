# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import dataclasses
from datetime import datetime, timedelta, timezone
import os
import signal
import tempfile
import unittest
from unittest import mock

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

from ns_common.exceptions import (
    NsRuntimeIamUnavailableError,
    NsRuntimeStateStoreCapabilityUnavailableError,
    NsRuntimeStateStoreIndeterminateWriteError,
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
    StateDocument,
    StateNamespace,
    StateNamespaceKind,
    create_state_store_provider,
)
from ns_common.time import ControlledClock, SystemClock
import ns_runtime.authority_broker as broker_module
from ns_runtime.authority_broker import (
    AuthorityBrokerConfig,
    BrokerAuthorityHandle,
    BrokerInstanceCertificate,
    BrokerRepositoryRole,
    BrokerSignedIamResult,
    ProductionIamAuthorityProxy,
    start_contract_test_authority_broker,
    start_production_authority_broker,
)
from ns_runtime.authority_wire import (
    MAX_FRAME_BYTES,
    decode_frame,
    encode_frame,
    require_object,
)
from ns_runtime.authority_bootstrap import load_inherited_authority_bootstrap
from ns_runtime.iam import (
    AuthorizationMode,
    IamClient,
    MessageAuthorizationService,
    OperationRiskContext,
    PermissionSnapshot,
)

from tests.test_runtime_iam_client import _HttpServer


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


class RuntimeAuthorityBrokerTestCase(unittest.IsolatedAsyncioTestCase):
    async def _broker(self, outcomes: list[object]):
        server = _HttpServer(outcomes)
        base_url = await server.start()
        broker = start_contract_test_authority_broker(
            config=_config(base_url),
            iam_service_credential="s" * 32,
        )
        self.addAsyncCleanup(server.close)
        self.addCleanup(broker.close)
        return broker, server

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
                    "state_password_source": "none",
                },
            )
        with self.assertRaises(NsValidationError):
            broker_module._BrokerStateBackend(
                _config("https://iam.invalid/"),
                {
                    "iam_service_credential": "s" * 32,
                    "state_password_source": "none",
                },
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
                "state_password_source": "none",
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
                "state_password_source": "none",
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
            self.assertEqual(
                {"_connection", "_process", "_consumed"},
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

    def test_malformed_response_after_write_is_indeterminate(self) -> None:
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        handle = broker_module._new_handle(
            private_key=private_key,
            instance_id="broker_test",
            role=BrokerRepositoryRole.ADMISSION,
            runtime_id="runtime:test",
            generation=1,
        )

        class Process:
            def is_alive(self):
                return True

            def join(self, timeout=None):
                del timeout

            def terminate(self):
                pass

            def kill(self):
                pass

        class Connection:
            def send_bytes(self, value):
                self.sent = value

            def poll(self, timeout):
                del timeout
                return True

            def recv_bytes(self, maximum):
                del maximum
                return b'{"malformed":true}'

            def close(self):
                pass

        channel = broker_module._BrokerChannel(
            connection=Connection(),
            process=Process(),
            public_key=public_key,
            instance_id="broker_test",
            timeout_seconds=0.1,
            realm="contract-test",
        )
        with self.assertRaises(NsRuntimeStateStoreIndeterminateWriteError):
            channel.request(
                handle=handle,
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

    @unittest.skipUnless(os.name == "posix", "requires POSIX process signals")
    async def test_close_kills_broker_stuck_in_operation(self) -> None:
        broker, _ = await self._broker([])
        process = broker._channel._process
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
        self.assertEqual("contract-test", broker._channel._realm)

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
        first._channel._process.terminate()
        first._channel._process.join(timeout=5.0)
        with self.assertRaises(NsRuntimeIamUnavailableError):
            await first.iam.access_check(request)
        with self.assertRaises(NsRuntimeStateStoreIndeterminateWriteError):
            await first.repositories.admission._request(
                "transact_admission",
                object(),
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

if __name__ == "__main__":
    unittest.main()
