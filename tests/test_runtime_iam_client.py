# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import copy
from datetime import datetime, timedelta, timezone
import json
import unittest
from unittest import mock
from typing import Mapping

from ns_common.exceptions import (
    NsConfigError,
    NsDependencyError,
    NsRuntimeIamDeniedError,
    NsRuntimeIamTimeoutError,
    NsRuntimeIamUnavailableError,
    NsValidationError,
)
from ns_common.http_client import (
    NsAsyncHttpClient,
    NsHttpClientOwner,
)
from ns_common.iam import (
    IamCredentialStatus, IamIntrospectionResult, IamPrincipalType,
    IamTargetContext, PayloadRefValidationRequest, PayloadRefValidationResult,
    PayloadRefRevalidationDecision, PayloadRefRevalidationRequest,
)
from ns_common.time import ControlledClock
from ns_common.config import NsConfig
from ns_runtime.connection import (
    HandshakeCredential,
    HandshakeIamRequest,
    PendingHelloClaims,
)
from ns_runtime.iam import (
    AuthorizationMode,
    IamClient,
    MessageAuthorizationService,
    PermissionSnapshot,
)
import ns_runtime.iam.client as iam_client_module
from ns_runtime.protocol import ProtocolVersion


NOW = datetime(2026, 7, 21, tzinfo=timezone.utc)
TOKEN = "user-access-token-must-never-leak"
SERVICE = "internal-service-credential-at-least-32-chars"


class _ContractTestIamClient(IamClient):
    """Explicit test-realm adapter; it can never satisfy production checks."""

    def __init__(
        self,
        *,
        http_client: NsAsyncHttpClient,
        clock: ControlledClock,
    ) -> None:
        self._test_http = http_client
        self._service_credential = SERVICE
        self._trace_id_factory = lambda: "operation:trace1"
        self._clock = clock
        self._iam_mode = "strict"
        self._payload_revalidation_results = {}
        self._authorization_service = None

    def _is_production_adapter(self) -> bool:
        return False

    async def _post(
        self,
        path: str,
        payload: Mapping[str, object],
    ) -> dict[str, object]:
        try:
            response = await self._test_http.post(
                path,
                json_data=dict(payload),
                bearer_token=self._service_credential,
                trace_id=self._trace_id_factory(),
                expected_statuses={200},
            )
            body = response.json()
        except NsDependencyError as error:
            if "timeout_seconds" in error.details:
                raise NsRuntimeIamTimeoutError(details={
                    "component": "runtime_iam_client",
                    "operation": "http_request",
                    "reason": "timeout",
                }) from None
            raise NsRuntimeIamUnavailableError(details={
                "component": "runtime_iam_client",
                "operation": "http_request",
                "reason": "backend_unavailable",
            }) from None
        if (
            not isinstance(body, Mapping)
            or body.get("success") is not True
            or set(body) != {
                "success", "code", "error", "message", "data", "request_id",
            }
            or not isinstance(body.get("data"), Mapping)
        ):
            raise NsRuntimeIamUnavailableError(details={
                "component": "runtime_iam_client",
                "operation": "response",
                "reason": "malformed_response",
            })
        return dict(body["data"])


class _HttpServer:
    def __init__(self, outcomes: list[object]) -> None:
        self.outcomes = outcomes
        self.calls: list[dict[str, object]] = []
        self.server: asyncio.AbstractServer | None = None

    async def start(self) -> str:
        self.server = await asyncio.start_server(
            self._handle,
            "127.0.0.1",
            0,
        )
        port = self.server.sockets[0].getsockname()[1]
        return f"http://127.0.0.1:{port}/"

    async def close(self) -> None:
        if self.server is None:
            return
        self.server.close()
        await self.server.wait_closed()

    async def _handle(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        header_bytes = await reader.readuntil(b"\r\n\r\n")
        header_text = header_bytes.decode("iso-8859-1")
        lines = header_text.split("\r\n")
        method, target, _ = lines[0].split(" ", 2)
        headers = {
            name.strip().casefold(): value.strip()
            for line in lines[1:]
            if ":" in line
            for name, value in (line.split(":", 1),)
        }
        length = int(headers.get("content-length", "0"))
        body = await reader.readexactly(length) if length else b""
        payload = json.loads(body) if body else None
        authorization = headers.get("authorization", "")
        self.calls.append({
            "url": target.lstrip("/"),
            "method": method,
            "bearer_token": authorization.removeprefix("Bearer "),
            "trace_id": headers.get("x-trace-id"),
            "json_data": payload,
        })
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, NsDependencyError) and "timeout_seconds" in outcome.details:
            await asyncio.sleep(0.2)
            writer.close()
            await writer.wait_closed()
            return
        status = 503 if isinstance(outcome, Exception) else 200
        response_body = json.dumps(
            _wrap({}) if isinstance(outcome, Exception) else _wrap(outcome),
        ).encode()
        reason = "OK" if status == 200 else "Service Unavailable"
        writer.write(
            f"HTTP/1.1 {status} {reason}\r\n".encode()
            + b"Content-Type: application/json\r\n"
            + f"Content-Length: {len(response_body)}\r\n".encode()
            + b"Connection: close\r\n\r\n"
            + response_body
        )
        await writer.drain()
        writer.close()
        await writer.wait_closed()


def _wrap(data: object) -> dict[str, object]:
    return {
        "success": True,
        "code": 0,
        "error": "OK",
        "message": "OK",
        "data": data,
        "request_id": "request:1",
    }


def _result(**changes: object) -> IamIntrospectionResult:
    values: dict[str, object] = {
        "identity": "user:1",
        "tenant_id": "tenant:1",
        "principal_type": IamPrincipalType.CLIENT,
        "component_type": "client",
        "capabilities": frozenset({"runtime.connection"}),
        "permission_snapshot_ref": "permission:1",
        "permission_digest": "sha256:1234",
        "permission_version": "version:1",
        "issued_at": NOW,
        "expires_at": NOW + timedelta(minutes=5),
        "credential_status": IamCredentialStatus.ACTIVE,
        "resume_eligible": True,
    }
    values.update(changes)
    return IamIntrospectionResult(**values)  # type: ignore[arg-type]


def _request(
    *,
    component_type: str = "client",
    capabilities: frozenset[str] = frozenset({"runtime.connection"}),
) -> HandshakeIamRequest:
    return HandshakeIamRequest(
        claims=PendingHelloClaims(
            component_type=component_type,
            requested_version=ProtocolVersion(1, 0, 0),
            minimum_version=None,
            requested_capabilities=capabilities,
        ),
        credential=HandshakeCredential(TOKEN),
    )


class RuntimeIamClientTestCase(unittest.IsolatedAsyncioTestCase):
    async def _client(
        self,
        outcomes: list[object],
    ) -> tuple[_ContractTestIamClient, _HttpServer]:
        captured = _HttpServer(outcomes)
        base_url = await captured.start()
        owner = NsHttpClientOwner()
        http = owner.create(
            name="runtime-iam-test",
            base_url=base_url,
            timeout_seconds=0.05,
        )
        self.addAsyncCleanup(captured.close)
        self.addAsyncCleanup(owner.aclose)
        client = _ContractTestIamClient(
            http_client=http,
            clock=ControlledClock(utc_start=NOW),
        )
        return client, captured

    def test_production_iam_adapter_cannot_be_directly_built_or_impersonated(
        self,
    ) -> None:
        with self.assertRaises(ImportError):
            from ns_runtime.iam.client import (  # type: ignore[attr-defined]  # noqa: F401
                _create_production_iam_client,
            )
        self.assertFalse(hasattr(
            iam_client_module,
            "_create_production_iam_client",
        ))
        with self.assertRaises(ImportError):
            from ns_runtime.iam.client import IamClientFactory  # type: ignore[attr-defined]  # noqa: F401
        self.assertFalse(hasattr(iam_client_module, "IamClientFactory"))
        http = NsAsyncHttpClient(
            name="runtime-iam-negative",
            base_url="https://iam.test/",
        )
        self.addAsyncCleanup(http.aclose)
        values = {
            "http_client": http,
            "internal_service_credential": SERVICE,
            "trace_id_factory": lambda: "operation:negative",
            "clock": ControlledClock(utc_start=NOW),
        }
        with self.assertRaises(NsValidationError):
            IamClient(**values)

        class ForgedIamClient(IamClient):
            async def access_check(self, request):
                return object()

        invalid_clients = (
            object.__new__(IamClient),
            object.__new__(ForgedIamClient),
            object(),
            {},
            "iam-client",
        )
        for value in invalid_clients:
            with self.subTest(client_type=type(value).__name__):
                with self.assertRaises(NsValidationError):
                    MessageAuthorizationService(
                        iam_client=value,  # type: ignore[arg-type]
                        clock=ControlledClock(utc_start=NOW),
                        mode=AuthorizationMode.STRICT,
                        cache_ttl_seconds=60,
                    )

    async def test_owner_provenance_rejects_http_method_substitution_and_copy(
        self,
    ) -> None:
        owner = NsHttpClientOwner()
        http = owner.create(
            name="runtime-iam-provenance",
            base_url="https://iam.example.test/api/",
        )
        self.addAsyncCleanup(owner.aclose)
        self.assertFalse(hasattr(owner, "_create_authority_handle"))
        self.assertFalse(hasattr(
            iam_client_module, "_ProductionIamCompositionProof",
        ))
        forged = object.__new__(IamClient)
        self.assertFalse(forged._is_production_adapter())
        with self.assertRaises(NsValidationError):
            copy.copy(owner)
        with self.assertRaises(NsValidationError):
            IamClient(
                http_client=copy.copy(http),
                internal_service_credential=SERVICE,
                trace_id_factory=lambda: "operation:forged",
                clock=ControlledClock(utc_start=NOW),
            )

        async def fake_post(*args, **kwargs):
            del args, kwargs
            return object()

        http.post = fake_post
        del http.post
        compiled = compile(
            "def main():\n"
            "  from ns_runtime.iam.client import IamClient\n"
            "  return object.__new__(IamClient)._is_production_adapter()\n",
            "/tmp/ns_runtime/main.py",
            "exec",
        )
        namespace: dict[str, object] = {}
        exec(compiled, namespace)
        self.assertFalse(namespace["main"]())
        with mock.patch("sys._getframe", side_effect=AssertionError("used")):
            self.assertFalse(object.__new__(IamClient)._is_production_adapter())

        await owner.aclose()
        self.assertTrue(http.is_closed)
        self.assertFalse(object.__new__(IamClient)._is_production_adapter())

    async def test_valid_token_uses_internal_credential_and_trace_without_leak(self) -> None:
        client, http = await self._client([{
            "active": True,
            "reason": "TOKEN_ACTIVE",
            "authority": _result().to_wire(),
        }])
        request = _request()
        authority = await client.authenticate(request)
        self.assertEqual("user:1", authority.identity)
        self.assertFalse(request.credential.available)
        self.assertEqual(SERVICE, http.calls[0]["bearer_token"])
        self.assertEqual("operation:trace1", http.calls[0]["trace_id"])
        self.assertEqual(TOKEN, http.calls[0]["json_data"]["token"])  # type: ignore[index]
        combined = repr(client) + repr(request) + repr(authority)
        self.assertNotIn(TOKEN, combined)
        self.assertNotIn(SERVICE, combined)

    async def test_payload_ref_validation_is_live_typed_and_integrity_bound(self) -> None:
        expected = PayloadRefValidationResult(
            valid=True, reason="valid", revoked=False,
            expires_at=NOW + timedelta(minutes=2), object_id="object:1",
            version="version:1", checksum="sha256:abcd",
            tenant_id="tenant:1", size_bytes=123,
        )
        client, http = await self._client([expected.to_wire()])
        request = PayloadRefValidationRequest(
            object_id="object:1", version="version:1", checksum="sha256:abcd",
            tenant_id="tenant:1", owner_identity="user:1",
            source_identity="user:1",
            target=IamTargetContext(
                kind="connection", tenant_id="tenant:1", reference="connection:1",
            ),
        )
        self.assertEqual(expected, await client.validate_payload_ref(request))
        self.assertEqual("internal/payload_ref/validate/", http.calls[0]["url"])
        self.assertEqual(request.to_wire(), http.calls[0]["json_data"])

    async def test_payload_ref_revalidation_preserves_backend_decision_reference(
        self,
    ) -> None:
        request = PayloadRefRevalidationRequest(
            object_id="object:1",
            version="version:1",
            checksum="sha256:abcd",
            size_bytes=123,
            tenant_id="tenant:1",
            target_principal="user:1",
            target_tenant_id="tenant:1",
            target_fingerprint="sha256:target",
            permission_snapshot_ref="permission:1",
            permission_version="version:1",
            admission_authority_reference="admission:opaque",
        )
        expected = PayloadRefRevalidationDecision(
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
            decision_reference="iam-payload:backend-issued",
            decided_at=NOW,
            expires_at=NOW + timedelta(minutes=2),
        )
        client, http = await self._client([expected.to_wire()])
        self.assertEqual(
            expected,
            await client.revalidate_payload_ref(request),
        )
        self.assertEqual(
            "internal/payload_ref/revalidate/",
            http.calls[0]["url"],
        )

    async def test_invalid_expired_and_revoked_credentials_are_denied(self) -> None:
        cases = (
            {"active": False, "reason": "TOKEN_INVALID", "authority": None},
            {
                "active": True,
                "reason": "TOKEN_EXPIRED",
                "authority": _result(
                    issued_at=NOW - timedelta(minutes=10),
                    expires_at=NOW - timedelta(minutes=1),
                    credential_status=IamCredentialStatus.EXPIRED,
                ).to_wire(),
            },
            {
                "active": True,
                "reason": "TOKEN_REVOKED",
                "authority": _result(
                    credential_status=IamCredentialStatus.REVOKED,
                ).to_wire(),
            },
        )
        for outcome in cases:
            with self.subTest(reason=outcome["reason"]):
                client, _ = await self._client([outcome])
                with self.assertRaises(NsRuntimeIamDeniedError):
                    await client.authenticate(_request())

    async def test_component_impersonation_and_capability_escalation_are_denied(self) -> None:
        hostile = (
            _result(component_type="node"),
            _result(capabilities=frozenset({"runtime.connection", "runtime.management"})),
        )
        for result in hostile:
            client, _ = await self._client([{
                "active": True,
                "reason": "TOKEN_ACTIVE",
                "authority": result.to_wire(),
            }])
            with self.assertRaises(NsRuntimeIamDeniedError):
                await client.authenticate(_request())

    async def test_timeout_5xx_and_malformed_response_are_normalized(self) -> None:
        timeout = NsDependencyError("timeout", details={"timeout_seconds": 5})
        failure = NsDependencyError("status", details={"status_code": 503})
        cases = (
            (timeout, NsRuntimeIamTimeoutError),
            (failure, NsRuntimeIamUnavailableError),
            ({"active": True}, NsRuntimeIamUnavailableError),
        )
        for outcome, expected in cases:
            with self.subTest(expected=expected.__name__):
                client, _ = await self._client([outcome])
                request = _request()
                with self.assertRaises(expected):
                    await client.authenticate(request)
                self.assertFalse(request.credential.available)

    def test_permission_snapshot_has_only_minimal_authority_and_auth_context(self) -> None:
        snapshot = PermissionSnapshot.from_introspection(
            _result(),
            iam_mode="strict",
        )
        self.assertEqual(
            {
                "identity", "tenant_id", "principal_type", "component_type",
                "capabilities", "permission_snapshot_ref", "permission_digest",
                "permission_version", "iam_mode", "issued_at", "expires_at",
                "resume_eligible",
            },
            set(snapshot.__dataclass_fields__),
        )
        auth_context = snapshot.auth_context()
        self.assertEqual(
            {
                "permission_snapshot_ref", "permission_digest", "iam_mode",
                "issued_at", "expires_at",
            },
            set(auth_context.to_dict()),
        )
        leak_probe = repr(snapshot) + repr(auth_context)
        for forbidden in ("token", "credential", "raw_response", TOKEN, SERVICE):
            self.assertNotIn(forbidden, leak_probe)

    def test_iam_config_mode_and_service_credential_are_strict(self) -> None:
        with self.assertRaises(NsConfigError):
            NsConfig.from_dict({
                "runtime": {"iam": {"authorization_mode": "permissive"}},
            })
        with self.assertRaises(NsConfigError):
            NsConfig.from_dict({
                "runtime": {"iam": {"internal_service_credential": "short"}},
            })

        def prod_config(
            iam: dict[str, object],
            *,
            backend_token: str = "b" * 32,
        ) -> dict[str, object]:
            return {
                "backend": {
                    "debug": False,
                    "secret_key": "s" * 32,
                    "iam_internal_token": backend_token,
                },
                "runtime": {
                    "iam": {
                        "base_url": "https://iam.example.test/api/iam/",
                        "internal_service_credential": "r" * 32,
                        **iam,
                    },
                    "transport": {"websocket_tcp": {"tls_enabled": True}},
                    "state_store": {
                        "backend": "redis",
                        "url": "rediss://127.0.0.1:6379/0",
                    },
                },
            }

        for iam, expected_field in (
            ({"base_url": "http://iam.example.test/api/iam/"}, "runtime.iam.base_url"),
            (
                {"internal_service_credential": "change-me-iam-internal-token-at-least-32-chars"},
                "runtime.iam.internal_service_credential",
            ),
            ({"fail_closed": False}, "runtime.iam.fail_closed"),
        ):
            with self.subTest(field=expected_field):
                with self.assertRaises(NsConfigError) as context:
                    NsConfig.from_dict(prod_config(iam), environment="prod")
                self.assertEqual(expected_field, context.exception.details["field"])
        with self.assertRaises(NsConfigError) as context:
            NsConfig.from_dict(prod_config(
                {},
                backend_token="change-me-iam-internal-token-at-least-32-chars",
            ), environment="prod")
        self.assertEqual(
            "backend.iam_internal_token",
            context.exception.details["field"],
        )


if __name__ == "__main__":
    unittest.main()
