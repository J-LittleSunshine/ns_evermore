# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import unittest

from ns_common.exceptions import (
    NsConfigError,
    NsDependencyError,
    NsRuntimeIamDeniedError,
    NsRuntimeIamTimeoutError,
    NsRuntimeIamUnavailableError,
)
from ns_common.http_client import NsAsyncHttpClient, NsHttpResponse
from ns_common.iam import (
    IamCredentialStatus, IamIntrospectionResult, IamPrincipalType,
    IamTargetContext, PayloadRefValidationRequest, PayloadRefValidationResult,
)
from ns_common.time import ControlledClock
from ns_common.config import NsConfig
from ns_runtime.connection import (
    HandshakeCredential,
    HandshakeIamRequest,
    PendingHelloClaims,
)
from ns_runtime.iam import IamClient, PermissionSnapshot
from ns_runtime.protocol import ProtocolVersion


NOW = datetime(2026, 7, 21, tzinfo=timezone.utc)
TOKEN = "user-access-token-must-never-leak"
SERVICE = "internal-service-credential-at-least-32-chars"


class _HttpClient(NsAsyncHttpClient):
    def __init__(self, outcomes: list[object]) -> None:
        self.outcomes = outcomes
        self.calls: list[dict[str, object]] = []

    async def post(self, url: str, **kwargs: object) -> NsHttpResponse:
        self.calls.append({"url": url, **kwargs})
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return NsHttpResponse(
            status_code=200,
            headers={"content-type": "application/json"},
            text=json.dumps(_wrap(outcome)),
            url="https://iam.test/internal",
            method="POST",
        )


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
    def _client(self, outcomes: list[object]) -> tuple[IamClient, _HttpClient]:
        http = _HttpClient(outcomes)
        client = IamClient(
            http_client=http,
            internal_service_credential=SERVICE,
            trace_id_factory=lambda: "operation:trace1",
            clock=ControlledClock(utc_start=NOW),
        )
        return client, http

    async def test_valid_token_uses_internal_credential_and_trace_without_leak(self) -> None:
        client, http = self._client([{
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
        client, http = self._client([expected.to_wire()])
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
                client, _ = self._client([outcome])
                with self.assertRaises(NsRuntimeIamDeniedError):
                    await client.authenticate(_request())

    async def test_component_impersonation_and_capability_escalation_are_denied(self) -> None:
        hostile = (
            _result(component_type="node"),
            _result(capabilities=frozenset({"runtime.connection", "runtime.management"})),
        )
        for result in hostile:
            client, _ = self._client([{
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
                client, _ = self._client([outcome])
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
