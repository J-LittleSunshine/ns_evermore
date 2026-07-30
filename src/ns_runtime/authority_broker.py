# -*- coding: utf-8 -*-
"""Spawn-isolated production IAM and StateStore authority broker.

The runtime process deliberately receives no production HTTP client, raw
StateStore, scope issuer, repository validator, signing key, or resource-policy
table.  It owns only a duplex IPC endpoint, broker public key, instance
identity, and signed least-privilege handles.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import math
import multiprocessing
import os
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from multiprocessing.connection import Connection, wait as wait_connections
from multiprocessing.reduction import DupFd
from pathlib import Path
from typing import Mapping
from urllib.parse import unquote, urlsplit

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from ns_common.exceptions import (
    NsRuntimeIamDeniedError,
    NsRuntimeIamTimeoutError,
    NsRuntimeIamUnavailableError,
    NsRuntimeStateStoreCapabilityUnavailableError,
    NsRuntimeStateStoreConflictError,
    NsRuntimeStateStoreIndeterminateWriteError,
    NsRuntimeStateStoreNamespaceViolationError,
    NsRuntimeStateStoreTimeoutError,
    NsRuntimeStateStoreUnavailableError,
    NsRuntimeStateStoreVersionMismatchError,
    NsValidationError,
)
from ns_common.iam import (
    IamAccessCheckRequest,
    IamAccessDecision,
    IamCredentialStatus,
    IamIntrospectionRequest,
    IamIntrospectionResult,
    IamTargetContext,
    PayloadRefRevalidationDecision,
    PayloadRefRevalidationRequest,
    PayloadRefValidationRequest,
    PayloadRefValidationResult,
)
from ns_common.state_store import (
    StateConsistency,
    StateDocument,
    StateKey,
    StateNamespace,
    StateNamespaceKind,
    StateOrderedIndexKey,
    StateReadResult,
    StateRecord,
    StateStoreHealth,
    StateTransaction,
    StateTransactionResult,
)
from ns_common.time import Clock, SystemClock
from ns_runtime.connection.iam import (
    HandshakeIamAdapter,
    HandshakeIamAuthority,
    HandshakeIamRequest,
)
from ns_runtime.delivery_persistence import (
    DeliveryPersistencePartition,
    DeliveryPersistenceTransaction,
    DeliveryPersistenceTransactionResult,
)
from ns_runtime.authority_wire import (
    MAX_FRAME_BYTES,
    WIRE_VERSION,
    decode_append_result,
    decode_bytes,
    decode_cursor,
    decode_document,
    decode_frame,
    decode_health,
    decode_index_result,
    decode_read_result,
    decode_time,
    decode_transaction_request,
    decode_transaction_result,
    encode_append_result,
    encode_bytes,
    encode_cursor,
    encode_document,
    encode_frame,
    encode_health,
    encode_index_result,
    encode_read_result,
    encode_time,
    encode_transaction_request,
    encode_transaction_result,
    require_object,
)
from ns_runtime.authority_attestor import (
    AuthorityAttestationError,
    AuthorityAttestorClient,
    IAM_VERIFICATION_RECEIPT_KIND,
    IAM_VERIFICATION_RECEIPT_WIRE_VERSION,
    start_authority_attestor,
)


_IAM_OPERATIONS = frozenset({
    "introspect",
    "runtime_access_check",
    "permission_snapshot",
    "payload_validate",
    "payload_revalidate",
})
_ROLE_OPERATIONS: Mapping[str, frozenset[str]] = {
    "admission": frozenset({
        "read_delivery", "read_admission_dedup", "read_admission_summary",
        "transact_admission",
    }),
    "scheduler": frozenset({
        "read_delivery", "read_attempt", "read_summary",
        "read_delivery_owner", "read_scheduler_cursor",
        "read_scheduler_index", "transact_scheduler",
    }),
    "payload": frozenset({"read_payload_body"}),
    "registry": frozenset({
        "read_registry_layout", "read_registry_tenant",
        "transact_registry", "read_registry_index",
    }),
    "audit": frozenset({"append_audit"}),
    "lifecycle": frozenset({"state_health"}),
}
_IAM_PATHS: Mapping[str, str] = {
    "introspect": "internal/introspect_token/",
    "runtime_access_check": "internal/runtime_access_check/",
    "permission_snapshot": "internal/permission_snapshot/",
    "payload_validate": "internal/payload_ref/validate/",
    "payload_revalidate": "internal/payload_ref/revalidate/",
}
_WRITE_OPERATIONS = frozenset({
    "transact_admission", "transact_scheduler", "transact_registry",
    "append_audit",
})
_SESSION_CERTIFICATE_TTL_SECONDS = 300.0
_DELEGATION_CERTIFICATE_TTL_SECONDS = 30 * 24 * 60 * 60.0
_DELEGATION_USAGES = (
    "role-endpoints", "iam-results", "rotation", "state-responses",
)
_BROKER_REALMS = frozenset({
    "production", "contract-test", "integration-test",
})
# Deployment trust root compiled into the broker executable/package.  The
# corresponding private key is intentionally absent from Python source and is
# supplied only through NS_RUNTIME_AUTHORITY_KEY_FD by the process launcher.
_PRODUCTION_ROOT_PUBLIC_KEY = bytes.fromhex(
    "bb664a4f556a411abe3f91fbde867461"
    "0338069f874a2281413c52332cdacfdf"
)


class BrokerRepositoryRole(str, Enum):
    IAM = "iam"
    ADMISSION = "admission"
    SCHEDULER = "scheduler"
    PAYLOAD = "payload"
    REGISTRY = "registry"
    AUDIT = "audit"
    LIFECYCLE = "lifecycle"


class _AuthorityProvenanceFailure(RuntimeError):
    """Internal failure of broker or attestor identity provenance."""


class _VerifiedRemoteBrokerError(RuntimeError):
    """Carry an attested broker error outside provenance error handling."""

    def __init__(self, value: object) -> None:
        super().__init__("verified_remote_broker_error")
        self.value = value


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerDelegationCertificate:
    trust_realm: str
    broker_instance_id: str
    runtime_id: str
    delegation_public_key: bytes
    attestor_instance_id: str
    attestor_public_key: bytes
    allowed_usages: tuple[str, ...]
    issued_at: datetime
    expires_at: datetime
    nonce: str
    signature: bytes

    def signed_values(self) -> Mapping[str, object]:
        return {
            "trust_realm": self.trust_realm,
            "broker_instance_id": self.broker_instance_id,
            "runtime_id": self.runtime_id,
            "delegation_public_key": encode_bytes(
                self.delegation_public_key,
            ),
            "attestor_instance_id": self.attestor_instance_id,
            "attestor_public_key": encode_bytes(
                self.attestor_public_key,
            ),
            "allowed_usages": list(self.allowed_usages),
            "issued_at": encode_time(self.issued_at),
            "expires_at": encode_time(self.expires_at),
            "nonce": self.nonce,
        }

    @property
    def fingerprint(self) -> str:
        return "sha256:" + hashlib.sha256(
            encode_frame(_encode_delegation_certificate(self)),
        ).hexdigest()


@dataclass(frozen=True, slots=True, kw_only=True)
class AuthorityBrokerConfig:
    iam_base_url: str
    iam_timeout_seconds: float
    iam_mode: str
    permission_snapshot_ttl_seconds: float
    state_backend: str
    state_endpoint: str
    state_username: str
    state_namespace: str
    state_operation_timeout_seconds: float
    runtime_id: str

    def __post_init__(self) -> None:
        for name in (
            "iam_base_url",
            "iam_mode",
            "state_backend",
            "state_endpoint",
            "state_username",
            "state_namespace",
            "runtime_id",
        ):
            if type(getattr(self, name)) is not str:
                _invalid(f"config.{name}")
        _normalize_backend_url(self.iam_base_url)
        if self.state_backend not in {"sqlite", "redis", "valkey"}:
            _invalid("config.state_backend")
        if self.state_backend in {"redis", "valkey"}:
            _physical_state_domain(self)
        for name in (
            "iam_mode", "state_namespace",
            "runtime_id",
        ):
            if not getattr(self, name):
                _invalid(f"config.{name}")
        for name in (
            "iam_timeout_seconds", "permission_snapshot_ttl_seconds",
            "state_operation_timeout_seconds",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
                _invalid(f"config.{name}")


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerInstanceCertificate:
    trust_realm: str
    broker_instance_id: str
    session_public_key: bytes
    runtime_id: str
    lifecycle_generation: int
    delegation_fingerprint: str
    issued_at: datetime
    expires_at: datetime
    nonce: str
    signature: bytes

    def signed_values(self) -> Mapping[str, object]:
        return {
            "trust_realm": self.trust_realm,
            "broker_instance_id": self.broker_instance_id,
            "session_public_key": encode_bytes(self.session_public_key),
            "runtime_id": self.runtime_id,
            "lifecycle_generation": self.lifecycle_generation,
            "delegation_fingerprint": self.delegation_fingerprint,
            "issued_at": encode_time(self.issued_at),
            "expires_at": encode_time(self.expires_at),
            "nonce": self.nonce,
        }

    def verify(
        self,
        root_public_key: bytes,
        *,
        expected_realm: str,
        expected_runtime_id: str,
        expected_instance_id: str | None = None,
        expected_session_public_key: bytes | None = None,
        expected_generation: int | None = None,
        now: datetime,
    ) -> bool:
        if (
            type(self) is not BrokerInstanceCertificate
            or expected_realm not in _BROKER_REALMS
            or self.trust_realm != expected_realm
            or self.runtime_id != expected_runtime_id
            or self.lifecycle_generation <= 0
            or self.issued_at > now
            or self.expires_at <= now
            or self.expires_at - self.issued_at
            > timedelta(seconds=_SESSION_CERTIFICATE_TTL_SECONDS)
            or len(self.session_public_key) != 32
            or len(root_public_key) != 32
            or (
                expected_instance_id is not None
                and self.broker_instance_id != expected_instance_id
            )
            or (
                expected_session_public_key is not None
                and self.session_public_key != expected_session_public_key
            )
            or (
                expected_generation is not None
                and self.lifecycle_generation != expected_generation
            )
        ):
            return False
        try:
            Ed25519PublicKey.from_public_bytes(root_public_key).verify(
                self.signature,
                _canonical(self.signed_values()),
            )
        except (InvalidSignature, ValueError, TypeError):
            return False
        return True


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerAuthorityHandle:
    broker_instance_id: str
    endpoint_id: str
    handle_id: str
    role: BrokerRepositoryRole
    runtime_id: str
    lifecycle_generation: int
    signature: bytes

    def signed_values(self) -> Mapping[str, object]:
        return {
            "broker_instance_id": self.broker_instance_id,
            "endpoint_id": self.endpoint_id,
            "handle_id": self.handle_id,
            "role": self.role.value,
            "runtime_id": self.runtime_id,
            "lifecycle_generation": self.lifecycle_generation,
        }

    def verify(self, public_key: bytes, *, instance_id: str) -> bool:
        if (
            type(self) is not BrokerAuthorityHandle
            or self.broker_instance_id != instance_id
            or type(self.endpoint_id) is not str
            or not self.endpoint_id
            or type(self.handle_id) is not str
            or not self.handle_id
            or not isinstance(self.role, BrokerRepositoryRole)
            or type(self.lifecycle_generation) is not int
            or self.lifecycle_generation <= 0
            or type(self.signature) is not bytes
        ):
            return False
        return _verify(public_key, _canonical(self.signed_values()), self.signature)

    def __copy__(self) -> "BrokerAuthorityHandle":
        _invalid("handle.copy")

    def __deepcopy__(self, memo: dict[int, object]) -> "BrokerAuthorityHandle":
        del memo
        _invalid("handle.copy")


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerSignedIamResult:
    broker_instance_id: str
    lifecycle_generation: int
    session_key_fingerprint: str
    operation: str
    request_fingerprint: str
    request_json: str
    result_json: str
    backend_decision: str
    permission_snapshot_ref: str
    permission_version: str
    tenant_id: str
    target: str
    message_type: str
    issued_at: datetime
    expires_at: datetime
    sequence: int
    nonce: str
    signature: bytes

    def signed_values(self) -> Mapping[str, object]:
        return {
            "broker_instance_id": self.broker_instance_id,
            "lifecycle_generation": self.lifecycle_generation,
            "session_key_fingerprint": self.session_key_fingerprint,
            "operation": self.operation,
            "request_fingerprint": self.request_fingerprint,
            "request_json": self.request_json,
            "result_json": self.result_json,
            "backend_decision": self.backend_decision,
            "permission_snapshot_ref": self.permission_snapshot_ref,
            "permission_version": self.permission_version,
            "tenant_id": self.tenant_id,
            "target": self.target,
            "message_type": self.message_type,
            "issued_at": _iso(self.issued_at),
            "expires_at": _iso(self.expires_at),
            "sequence": self.sequence,
            "nonce": self.nonce,
        }

    def verify(
        self,
        *,
        public_key: bytes,
        broker_instance_id: str,
        operation: str,
        request_fingerprint: str,
        now: datetime,
        lifecycle_generation: int | None = None,
        session_key_fingerprint: str | None = None,
    ) -> bool:
        try:
            request_values = self.request_mapping()
            bound_fingerprint = _claims_fingerprint(
                self.operation,
                request_values,
            )
        except (NsValidationError, TypeError, ValueError):
            return False
        return bool(
            type(self) is BrokerSignedIamResult
            and self.broker_instance_id == broker_instance_id
            and (
                lifecycle_generation is None
                or self.lifecycle_generation == lifecycle_generation
            )
            and (
                session_key_fingerprint is None
                or self.session_key_fingerprint
                == session_key_fingerprint
            )
            and self.operation == operation
            and self.request_fingerprint == request_fingerprint
            and self.request_fingerprint == bound_fingerprint
            and self.issued_at <= now < self.expires_at
            and type(self.sequence) is int
            and self.sequence > 0
            and type(self.nonce) is str
            and bool(self.nonce)
            and type(self.signature) is bytes
            and _verify(
                public_key,
                _canonical(self.signed_values()),
                self.signature,
            )
        )

    def result_mapping(self) -> dict[str, object]:
        try:
            value = json.loads(self.result_json)
        except (TypeError, ValueError, json.JSONDecodeError):
            _invalid("signed_result.result_json")
        if type(value) is not dict:
            _invalid("signed_result.result_json")
        return value

    def request_mapping(self) -> dict[str, object]:
        try:
            value = json.loads(self.request_json)
        except (TypeError, ValueError, json.JSONDecodeError):
            _invalid("signed_result.request_json")
        if type(value) is not dict:
            _invalid("signed_result.request_json")
        return value

    def __copy__(self) -> "BrokerSignedIamResult":
        _invalid("signed_result.copy")

    def __deepcopy__(self, memo: dict[int, object]) -> "BrokerSignedIamResult":
        del memo
        _invalid("signed_result.copy")


@dataclass(frozen=True, slots=True, kw_only=True, init=False)
class BrokerIamVerificationReceipt:
    """Local receipt for one attestor-verified broker IAM result.

    The receipt is not an authority on its own.  It is useful only together
    with the exact broker-signed result whose canonical fingerprints it binds.
    Its security boundary is the attestor Ed25519 signature; unavailable
    normal construction is only a misuse guard.
    """

    wire_version: int
    kind: str
    attestor_instance_id: str
    attestor_identity_id: str
    broker_instance_id: str
    runtime_id: str
    lifecycle_generation: int
    session_key_fingerprint: str
    endpoint_id: str
    role: str
    operation: str
    request_fingerprint: str
    signed_result_fingerprint: str
    result_fingerprint: str
    request_json_fingerprint: str
    verified_at: datetime
    authority_expires_at: datetime
    nonce: str
    signature: bytes

    def signed_values(self) -> Mapping[str, object]:
        return {
            "version": self.wire_version,
            "kind": self.kind,
            "attestor_instance_id": self.attestor_instance_id,
            "attestor_identity_id": self.attestor_identity_id,
            "broker_instance_id": self.broker_instance_id,
            "runtime_id": self.runtime_id,
            "lifecycle_generation": self.lifecycle_generation,
            "session_key_fingerprint": self.session_key_fingerprint,
            "endpoint_id": self.endpoint_id,
            "role": self.role,
            "operation": self.operation,
            "request_fingerprint": self.request_fingerprint,
            "signed_result_fingerprint": self.signed_result_fingerprint,
            "result_fingerprint": self.result_fingerprint,
            "request_json_fingerprint": self.request_json_fingerprint,
            "verified_at": encode_time(self.verified_at),
            "authority_expires_at": encode_time(
                self.authority_expires_at,
            ),
            "nonce": self.nonce,
        }

    def verify(
        self,
        *,
        attestor_public_key: bytes,
        authority: BrokerSignedIamResult,
        result: object,
        expected_identity: "_LocalIamSessionIdentity",
        operation: str,
        request_fingerprint: str,
        now: datetime,
    ) -> bool:
        if (
            type(self) is not BrokerIamVerificationReceipt
            or type(authority) is not BrokerSignedIamResult
            or type(expected_identity) is not _LocalIamSessionIdentity
            or type(attestor_public_key) is not bytes
            or len(attestor_public_key) != 32
            or type(now) is not datetime
            or now.tzinfo is None
            or now.utcoffset() is None
        ):
            return False
        try:
            result_values = _encode_iam_result(operation, result)
            authority_result = authority.result_mapping()
        except (NsValidationError, KeyError, TypeError, ValueError):
            return False
        return bool(
            self.wire_version == IAM_VERIFICATION_RECEIPT_WIRE_VERSION
            and self.kind == IAM_VERIFICATION_RECEIPT_KIND
            and self.attestor_instance_id
            == expected_identity.attestor_instance_id
            and self.attestor_identity_id
            == expected_identity.attestor_identity_id
            and self.broker_instance_id
            == expected_identity.broker_instance_id
            and self.broker_instance_id == authority.broker_instance_id
            and self.runtime_id == expected_identity.runtime_id
            and self.lifecycle_generation
            == expected_identity.lifecycle_generation
            and self.lifecycle_generation == authority.lifecycle_generation
            and self.session_key_fingerprint
            == expected_identity.session_key_fingerprint
            and self.session_key_fingerprint
            == authority.session_key_fingerprint
            and self.endpoint_id == expected_identity.endpoint_id
            and self.role == expected_identity.role == "iam"
            and self.operation == operation
            and self.operation == authority.operation
            and self.request_fingerprint == request_fingerprint
            and self.request_fingerprint == authority.request_fingerprint
            and self.signed_result_fingerprint
            == _signed_iam_result_fingerprint(authority)
            and authority_result == result_values
            and self.result_fingerprint
            == _iam_result_fingerprint(result_values)
            and self.request_json_fingerprint
            == _iam_result_fingerprint(authority.request_mapping())
            and self.verified_at <= now < self.authority_expires_at
            and self.authority_expires_at == authority.expires_at
            and authority.issued_at <= self.verified_at
            and type(self.nonce) is str
            and bool(self.nonce)
            and type(self.signature) is bytes
            and _verify(
                attestor_public_key,
                _canonical(self.signed_values()),
                self.signature,
            )
        )

    def __copy__(self) -> "BrokerIamVerificationReceipt":
        _invalid("iam_verification_receipt.copy")

    def __deepcopy__(
        self,
        memo: dict[int, object],
    ) -> "BrokerIamVerificationReceipt":
        del memo
        _invalid("iam_verification_receipt.copy")


@dataclass(frozen=True, slots=True, kw_only=True, init=False)
class VerifiedBrokerIamResult:
    result: object
    authority: BrokerSignedIamResult
    verification: BrokerIamVerificationReceipt

    def __copy__(self) -> "VerifiedBrokerIamResult":
        _invalid("verified_iam_result.copy")

    def __deepcopy__(
        self,
        memo: dict[int, object],
    ) -> "VerifiedBrokerIamResult":
        del memo
        _invalid("verified_iam_result.copy")


@dataclass(frozen=True, slots=True, kw_only=True)
class _AttestedIamChannelResponse:
    raw_result: object
    verification: Mapping[str, object]
    identity: "_LocalIamSessionIdentity"


@dataclass(frozen=True, slots=True, kw_only=True)
class _LocalIamSessionIdentity:
    attestor_instance_id: str
    attestor_identity_id: str
    broker_instance_id: str
    runtime_id: str
    lifecycle_generation: int
    session_key_fingerprint: str
    endpoint_id: str
    role: str
    connection_generation: int


@dataclass(frozen=True, slots=True, kw_only=True, init=False)
class _ProductionIamCompositionBinding:
    channel: object
    attestor_instance_id: str
    attestor_public_key: bytes
    attestor_identity_id: str
    broker_instance_id: str
    runtime_id: str
    endpoint_id: str


def _verified_iam_result_from_attestation(
    *,
    operation: str,
    result: object,
    authority: BrokerSignedIamResult,
    verification: Mapping[str, object],
    attestor_public_key: bytes,
    expected_identity: _LocalIamSessionIdentity,
) -> VerifiedBrokerIamResult:
    try:
        fields = require_object(
            verification,
            fields={
                "version", "kind", "attestor_instance_id",
                "attestor_identity_id", "broker_instance_id", "runtime_id",
                "lifecycle_generation", "session_key_fingerprint",
                "endpoint_id", "role",
                "operation", "request_fingerprint",
                "signed_result_fingerprint", "result_fingerprint",
                "request_json_fingerprint",
                "verified_at", "authority_expires_at",
                "nonce", "signature",
            },
            field="iam_verification_receipt",
        )
        receipt_values = {
            "wire_version": _exact_int(
                fields["version"],
                "iam_verification_receipt.version",
                minimum=1,
            ),
            "kind": _exact_string(
                fields["kind"],
                "iam_verification_receipt.kind",
            ),
            "attestor_instance_id": _exact_string(
                fields["attestor_instance_id"],
                "iam_verification_receipt.attestor_instance_id",
            ),
            "attestor_identity_id": _exact_string(
                fields["attestor_identity_id"],
                "iam_verification_receipt.attestor_identity_id",
            ),
            "broker_instance_id": _exact_string(
                fields["broker_instance_id"],
                "iam_verification_receipt.broker_instance_id",
            ),
            "runtime_id": _exact_string(
                fields["runtime_id"],
                "iam_verification_receipt.runtime_id",
            ),
            "lifecycle_generation": _exact_int(
                fields["lifecycle_generation"],
                "iam_verification_receipt.lifecycle_generation",
                minimum=1,
            ),
            "session_key_fingerprint": _exact_string(
                fields["session_key_fingerprint"],
                "iam_verification_receipt.session_key_fingerprint",
            ),
            "endpoint_id": _exact_string(
                fields["endpoint_id"],
                "iam_verification_receipt.endpoint_id",
            ),
            "role": _exact_string(
                fields["role"],
                "iam_verification_receipt.role",
            ),
            "operation": _exact_string(
                fields["operation"],
                "iam_verification_receipt.operation",
            ),
            "request_fingerprint": _exact_string(
                fields["request_fingerprint"],
                "iam_verification_receipt.request_fingerprint",
            ),
            "signed_result_fingerprint": _exact_string(
                fields["signed_result_fingerprint"],
                "iam_verification_receipt.signed_result_fingerprint",
            ),
            "result_fingerprint": _exact_string(
                fields["result_fingerprint"],
                "iam_verification_receipt.result_fingerprint",
            ),
            "request_json_fingerprint": _exact_string(
                fields["request_json_fingerprint"],
                "iam_verification_receipt.request_json_fingerprint",
            ),
            "verified_at": _parse_time(fields["verified_at"]),
            "authority_expires_at": _parse_time(
                fields["authority_expires_at"],
            ),
            "nonce": _exact_string(
                fields["nonce"], "iam_verification_receipt.nonce",
            ),
            "signature": decode_bytes(
                fields["signature"],
                field="iam_verification_receipt.signature",
            ),
        }
        receipt = object.__new__(BrokerIamVerificationReceipt)
        for name, value in receipt_values.items():
            object.__setattr__(receipt, name, value)
        if not receipt.verify(
            attestor_public_key=attestor_public_key,
            authority=authority,
            result=result,
            expected_identity=expected_identity,
            operation=operation,
            request_fingerprint=authority.request_fingerprint,
            now=datetime.now(timezone.utc),
        ):
            _invalid("iam_verification_receipt.binding")
        verified = object.__new__(VerifiedBrokerIamResult)
        object.__setattr__(verified, "result", result)
        object.__setattr__(verified, "authority", authority)
        object.__setattr__(verified, "verification", receipt)
        return verified
    except (
        NsValidationError, KeyError, TypeError, ValueError,
    ):
        raise


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerSignedStateResponse:
    broker_instance_id: str
    lifecycle_generation: int
    session_key_fingerprint: str
    request_id: str
    request_sequence: int
    operation: str
    handle_id: str
    role: str
    request_fingerprint: str
    ok: bool
    result_json: str
    error_json: str
    response_sequence: int
    issued_at: datetime
    nonce: str
    signature: bytes

    def signed_values(self) -> Mapping[str, object]:
        return {
            "broker_instance_id": self.broker_instance_id,
            "lifecycle_generation": self.lifecycle_generation,
            "session_key_fingerprint": self.session_key_fingerprint,
            "request_id": self.request_id,
            "request_sequence": self.request_sequence,
            "operation": self.operation,
            "handle_id": self.handle_id,
            "role": self.role,
            "request_fingerprint": self.request_fingerprint,
            "ok": self.ok,
            "result_json": self.result_json,
            "error_json": self.error_json,
            "response_sequence": self.response_sequence,
            "issued_at": encode_time(self.issued_at),
            "nonce": self.nonce,
        }

    def verify(
        self,
        *,
        certificate: BrokerInstanceCertificate,
        request_id: str,
        request_sequence: int,
        operation: str,
        handle: BrokerAuthorityHandle,
        request_fingerprint: str,
        expected_response_sequence: int,
        now: datetime,
    ) -> bool:
        if (
            type(self) is not BrokerSignedStateResponse
            or type(certificate) is not BrokerInstanceCertificate
            or self.broker_instance_id != certificate.broker_instance_id
            or self.lifecycle_generation
            != certificate.lifecycle_generation
            or self.session_key_fingerprint
            != _session_key_fingerprint(certificate.session_public_key)
            or self.request_id != request_id
            or self.request_sequence != request_sequence
            or self.operation != operation
            or self.handle_id != handle.handle_id
            or self.role != handle.role.value
            or self.request_fingerprint != request_fingerprint
            or self.response_sequence != expected_response_sequence
            or type(self.ok) is not bool
            or type(self.result_json) is not str
            or type(self.error_json) is not str
            or type(self.nonce) is not str
            or not self.nonce
            or type(self.signature) is not bytes
            or self.issued_at < certificate.issued_at
            or self.issued_at > now
            or now >= certificate.expires_at
            or (self.ok and self.error_json != "null")
            or (not self.ok and self.result_json != "null")
        ):
            return False
        return _verify(
            certificate.session_public_key,
            _canonical(self.signed_values()),
            self.signature,
        )

    def result_value(self) -> object:
        return _decode_canonical_json(self.result_json, "state_response.result")

    def error_value(self) -> object:
        return _decode_canonical_json(self.error_json, "state_response.error")

    def __copy__(self) -> "BrokerSignedStateResponse":
        _invalid("state_response.copy")

    def __deepcopy__(
        self, memo: dict[int, object],
    ) -> "BrokerSignedStateResponse":
        del memo
        _invalid("state_response.copy")


class _ParentEndpointCloseResource:
    """Close-only parent resource without role, handle, or request authority."""

    __slots__ = ("_connection",)

    def __init__(self, connection: object) -> None:
        if not callable(getattr(connection, "close", None)):
            raise TypeError("endpoint close resource requires close()")
        self._connection = connection

    def close(self) -> None:
        try:
            self._connection.close()
        except OSError:
            pass


class _BrokerProcessCustodian:
    """Shared process lifecycle with only close-only endpoint resources."""

    __slots__ = (
        "process", "attestor", "_lock", "_request_lock",
        "_endpoint_close_resources", "_reaped",
    )

    def __init__(
        self,
        *,
        process: multiprocessing.Process,
        attestor: AuthorityAttestorClient,
        endpoint_close_resources: tuple[
            _ParentEndpointCloseResource, ...
        ] = (),
    ) -> None:
        if (
            type(endpoint_close_resources) is not tuple
            or any(
                type(resource) is not _ParentEndpointCloseResource
                for resource in endpoint_close_resources
            )
        ):
            raise TypeError("invalid endpoint close resources")
        self.process = process
        self.attestor = attestor
        self._lock = threading.Lock()
        # The broker executes one request at a time.  Matching that boundary
        # here prevents a session rotation on one role endpoint from advancing
        # the attestor generation while another endpoint's signed response is
        # still awaiting verification.  This lock carries no role, handle, or
        # authority material.
        self._request_lock = threading.Lock()
        self._endpoint_close_resources = endpoint_close_resources
        self._reaped = False

    @property
    def alive(self) -> bool:
        return bool(not self._reaped and self.process.is_alive())

    def reap(self) -> None:
        with self._lock:
            if self._reaped:
                return
            for resource in self._endpoint_close_resources:
                resource.close()
            process = self.process
            process.join(timeout=0.2)
            if process.is_alive():
                process.terminate()
                process.join(timeout=5.0)
            if process.is_alive():
                process.kill()
                process.join(timeout=5.0)
            if process.is_alive():
                raise _broker_unavailable("broker_process_did_not_exit")
            try:
                self.attestor.close()
            except AuthorityAttestationError:
                pass
            self._reaped = True


class _RoleBrokerChannel:
    """One OS endpoint permanently bound to one broker-side role."""

    __slots__ = (
        "_connection", "_custodian", "_public_key", "_instance_id",
        "_runtime_id", "_lifecycle_generation", "_certificate",
        "_delegation_certificate", "_certificate_fingerprint",
        "_attestor", "_identity_id", "_endpoint_id", "_role", "_handle",
        "_connection_generation", "_lock", "_closed",
        "_timeout_seconds", "_request_sequence", "_response_sequence",
    )

    def __init__(
        self,
        *,
        connection: Connection,
        custodian: _BrokerProcessCustodian,
        public_key: bytes,
        instance_id: str,
        runtime_id: str,
        lifecycle_generation: int,
        certificate: BrokerInstanceCertificate,
        delegation_certificate: BrokerDelegationCertificate,
        attestor: AuthorityAttestorClient,
        identity_id: str,
        endpoint_id: str,
        role: BrokerRepositoryRole,
        handle: BrokerAuthorityHandle,
        timeout_seconds: float,
    ) -> None:
        self._connection = connection
        self._custodian = custodian
        self._public_key = public_key
        self._instance_id = instance_id
        self._runtime_id = runtime_id
        self._lifecycle_generation = lifecycle_generation
        self._certificate = certificate
        self._delegation_certificate = delegation_certificate
        self._certificate_fingerprint = _certificate_fingerprint(
            certificate,
        )
        self._attestor = attestor
        self._identity_id = identity_id
        self._endpoint_id = endpoint_id
        self._role = role
        self._handle = handle
        self._connection_generation = 1
        self._lock = threading.Lock()
        self._closed = False
        self._timeout_seconds = float(timeout_seconds)
        self._request_sequence = 0
        self._response_sequence = 0
        if not self._identity_is_current():
            self._closed = True
            self._fail_and_reap()
            _invalid("broker_channel.certificate")

    @property
    def public_key(self) -> bytes:
        try:
            with self._lock:
                self._sync_endpoint_identity_locked()
                return bytes(self._public_key)
        except _AuthorityProvenanceFailure:
            self._fail_and_reap()
            raise _broker_unavailable("broker_provenance_invalid") from None

    @property
    def instance_id(self) -> str:
        return self._instance_id

    @property
    def alive(self) -> bool:
        if self._closed or not self._custodian.alive:
            return False
        return self._identity_is_current()

    @property
    def certificate(self) -> BrokerInstanceCertificate:
        try:
            with self._lock:
                self._sync_endpoint_identity_locked()
                return self._certificate
        except _AuthorityProvenanceFailure:
            self._fail_and_reap()
            raise _broker_unavailable("broker_provenance_invalid") from None

    @property
    def role(self) -> BrokerRepositoryRole:
        return self._role

    @property
    def endpoint_id(self) -> str:
        return self._endpoint_id

    @property
    def handle(self) -> BrokerAuthorityHandle:
        return self._handle

    def current_session_identity(self) -> Mapping[str, object]:
        try:
            with self._lock:
                self._sync_endpoint_identity_locked()
                return {
                    "broker_instance_id": self._instance_id,
                    "runtime_id": self._runtime_id,
                    "lifecycle_generation": self._lifecycle_generation,
                    "session_public_key": bytes(self._public_key),
                    "session_key_fingerprint": _session_key_fingerprint(
                        self._public_key,
                    ),
                    "certificate_fingerprint": self._certificate_fingerprint,
                    "endpoint_id": self._endpoint_id,
                    "role": self._role.value,
                }
        except _AuthorityProvenanceFailure:
            self._fail_and_reap()
            raise _broker_unavailable("broker_provenance_invalid") from None

    def _identity_is_current(
        self, now: datetime | None = None,
    ) -> bool:
        del now
        return self._attested_identity() is not None

    def _attested_identity(self) -> dict[str, object] | None:
        attestor = getattr(self, "_attestor", None)
        if type(attestor) is not AuthorityAttestorClient:
            self._fail_and_reap()
            return None
        try:
            with self._lock:
                result = self._sync_endpoint_identity_locked()
        except _AuthorityProvenanceFailure:
            self._fail_and_reap()
            return None
        if not (
            result.get("identity_id") == self._identity_id
            and result.get("broker_instance_id") == self._instance_id
            and result.get("runtime_id") == self._runtime_id
            and result.get("lifecycle_generation")
            == self._lifecycle_generation
            and result.get("session_key_fingerprint")
            == _session_key_fingerprint(self._public_key)
            and result.get("certificate_fingerprint")
            == self._certificate_fingerprint
        ):
            self._fail_and_reap()
            return None
        return result

    def _sync_endpoint_identity_locked(self) -> dict[str, object]:
        try:
            result = self._attestor.current_endpoint_identity(
                identity_id=self._identity_id,
                endpoint_id=self._endpoint_id,
                role=self._role.value,
            )
            certificate = _decode_certificate(
                result.get("session_certificate"),
            )
            handle = _decode_handle(result.get("handle"))
            certificate_fingerprint = _certificate_fingerprint(certificate)
            session_key_fingerprint = _session_key_fingerprint(
                certificate.session_public_key,
            )
            if (
                result.get("identity_id") != self._identity_id
                or result.get("broker_instance_id") != self._instance_id
                or result.get("runtime_id") != self._runtime_id
                or result.get("endpoint_id") != self._endpoint_id
                or result.get("role") != self._role.value
                or result.get("lifecycle_generation")
                != certificate.lifecycle_generation
                or result.get("session_key_fingerprint")
                != session_key_fingerprint
                or result.get("certificate_fingerprint")
                != certificate_fingerprint
                or certificate.broker_instance_id != self._instance_id
                or certificate.runtime_id != self._runtime_id
                or handle.broker_instance_id != self._instance_id
                or handle.runtime_id != self._runtime_id
                or handle.endpoint_id != self._endpoint_id
                or handle.role is not self._role
                or handle.lifecycle_generation
                != certificate.lifecycle_generation
                or not handle.verify(
                    certificate.session_public_key,
                    instance_id=self._instance_id,
                )
            ):
                raise _AuthorityProvenanceFailure(
                    "endpoint_identity_invalid",
                )
        except _AuthorityProvenanceFailure:
            raise
        except (
            AuthorityAttestationError, NsValidationError, AttributeError,
            KeyError, TypeError, ValueError,
        ) as error:
            raise _AuthorityProvenanceFailure(
                "endpoint_identity_invalid",
            ) from error
        generation_changed = (
            certificate.lifecycle_generation
            != self._lifecycle_generation
        )
        self._certificate = certificate
        self._public_key = certificate.session_public_key
        self._lifecycle_generation = certificate.lifecycle_generation
        self._certificate_fingerprint = certificate_fingerprint
        self._handle = handle
        if generation_changed:
            self._connection_generation += 1
            self._request_sequence = 0
            self._response_sequence = 0
        return dict(result)

    def _is_production_certificate_chain_current(
        self, now: datetime,
    ) -> bool:
        del now
        identity = self._attested_identity()
        return bool(
            type(self) is _ProductionRoleBrokerChannel
            and identity is not None
            and identity.get("realm") == "production"
        )

    def request(
        self,
        *,
        operation: str,
        payload: dict[str, object] | list[object] | str | int | float | bool | None,
    ) -> object:
        if (
            type(operation) is not str
            or not _role_allows(self._role, operation)
        ):
            raise _state_denied("role_endpoint_operation_denied")
        # This is the pure local request boundary.  Past this point, malformed
        # identity, rotation, ticket, or response data is provenance failure.
        encode_frame(payload)
        with self._custodian._request_lock:
            return self._request_serialized(
                operation=operation,
                payload=payload,
            )

    def _request_serialized(
        self,
        *,
        operation: str,
        payload: dict[str, object] | list[object] | str | int | float | bool | None,
    ) -> object:
        if self._closed or not self._custodian.alive:
            self._fail_and_reap()
            raise _operation_unavailable(operation, "broker_unavailable")
        send_attempted = False
        connection = self._connection
        try:
            with self._lock:
                if self._closed or not self._custodian.alive:
                    self._fail_and_reap()
                    raise _operation_unavailable(
                        operation, "broker_unavailable",
                    )
                connection = self._connection
                attestor = self._attestor
                self._sync_endpoint_identity_locked()
                self._rotate_if_required_locked(
                    attestor=attestor,
                    operation=operation,
                )
                self._sync_endpoint_identity_locked()
                handle = self._handle
                request_id = "ipc_" + uuid.uuid4().hex
                request_sequence = self._request_sequence + 1
                request_fingerprint = _state_request_fingerprint(
                    operation=operation,
                    handle=handle,
                    payload=payload,
                )
                prepared = attestor.prepare_request(
                    identity_id=self._identity_id,
                    connection_generation=self._connection_generation,
                    endpoint_id=self._endpoint_id,
                    role=self._role.value,
                    operation=operation,
                    request_id=request_id,
                    request_sequence=request_sequence,
                    request_fingerprint=request_fingerprint,
                )
                if prepared.get("status") != "ready":
                    _invalid("attestor.request_ticket")
                ticket = prepared.get("ticket")
                if type(ticket) is not dict:
                    _invalid("attestor.request_ticket")
                connection_generation = self._connection_generation
                expected_response_sequence = self._response_sequence + 1
                snapshot = {
                    "identity_id": self._identity_id,
                    "connection_generation": connection_generation,
                    "broker_instance_id": self._instance_id,
                    "runtime_id": self._runtime_id,
                    "lifecycle_generation": self._lifecycle_generation,
                    "session_key_fingerprint": _session_key_fingerprint(
                        self._public_key,
                    ),
                    "certificate_fingerprint": (
                        self._certificate_fingerprint
                    ),
                    "endpoint_id": self._endpoint_id,
                    "handle_id": handle.handle_id,
                    "role": self._role.value,
                    "operation": operation,
                    "request_id": request_id,
                    "request_sequence": request_sequence,
                    "request_fingerprint": request_fingerprint,
                    "expected_response_sequence": (
                        expected_response_sequence
                    ),
                }
                raw_request = encode_frame({
                    "version": WIRE_VERSION,
                    "kind": "request",
                    "request_id": request_id,
                    "request_sequence": request_sequence,
                    "operation": operation,
                    "payload": payload,
                    "attestation": ticket,
                })
                self._request_sequence = request_sequence
                send_attempted = True
                connection.send_bytes(raw_request)
                if not connection.poll(self._timeout_seconds):
                    self._fail_and_reap(connection=connection)
                    if operation in _WRITE_OPERATIONS:
                        raise _indeterminate(operation, "ipc_timeout")
                    raise _operation_unavailable(operation, "ipc_timeout")
                envelope = decode_frame(
                    connection.recv_bytes(MAX_FRAME_BYTES),
                )
                values = require_object(
                    envelope,
                    fields={"version", "kind", "signed_response"},
                    field="response_envelope",
                )
                if (
                    values["version"] != WIRE_VERSION
                    or values["kind"] != "signed_response"
                    or type(values["signed_response"]) is not dict
                ):
                    _invalid("response_envelope.binding")
                verified = attestor.verify_state_response(
                    snapshot=snapshot,
                    signed_response=values["signed_response"],
                )
                if (
                    connection is not self._connection
                    or attestor is not self._attestor
                    or connection_generation
                    != self._connection_generation
                    or snapshot["certificate_fingerprint"]
                    != self._certificate_fingerprint
                    or snapshot["session_key_fingerprint"]
                    != _session_key_fingerprint(self._public_key)
                    or snapshot["broker_instance_id"]
                    != self._instance_id
                    or snapshot["runtime_id"] != self._runtime_id
                    or snapshot["lifecycle_generation"]
                    != self._lifecycle_generation
                ):
                    _invalid("response.connection_generation")
                self._response_sequence = expected_response_sequence
                if verified.get("ok") is True:
                    decoded_result = _decode_canonical_json(
                        _exact_string(
                            verified.get("result_json"),
                            "attestor.result_json",
                        ),
                        "attestor.result_json",
                    )
                    if self._role is BrokerRepositoryRole.IAM:
                        signed_iam = _decode_signed_iam_result(
                            decoded_result,
                        )
                        typed_request = _decode_iam_request(
                            operation, payload,
                        )
                        inner_verified = attestor.verify_iam_result(
                            identity_id=self._identity_id,
                            operation=operation,
                            request_fingerprint=_request_fingerprint(
                                operation, typed_request,
                            ),
                            signed_result=_encode_signed_iam_result(
                                signed_iam,
                            ),
                        )
                        if (
                            inner_verified.get("version")
                            != IAM_VERIFICATION_RECEIPT_WIRE_VERSION
                            or inner_verified.get("kind")
                            != IAM_VERIFICATION_RECEIPT_KIND
                            or inner_verified.get("attestor_instance_id")
                            != attestor.instance_id
                            or inner_verified.get("attestor_identity_id")
                            != snapshot["identity_id"]
                            or inner_verified.get("broker_instance_id")
                            != snapshot["broker_instance_id"]
                            or inner_verified.get("runtime_id")
                            != snapshot["runtime_id"]
                            or inner_verified.get(
                                "lifecycle_generation",
                            ) != snapshot["lifecycle_generation"]
                            or inner_verified.get(
                                "session_key_fingerprint",
                            ) != snapshot["session_key_fingerprint"]
                            or inner_verified.get("endpoint_id")
                            != snapshot["endpoint_id"]
                            or inner_verified.get("role") != "iam"
                            or inner_verified.get("operation") != operation
                            or inner_verified.get("request_fingerprint")
                            != signed_iam.request_fingerprint
                            or inner_verified.get(
                                "signed_result_fingerprint",
                            ) != _signed_iam_result_fingerprint(signed_iam)
                            or inner_verified.get("result_fingerprint")
                            != _iam_result_fingerprint(
                                signed_iam.result_mapping(),
                            )
                            or inner_verified.get(
                                "request_json_fingerprint",
                            ) != _iam_result_fingerprint(
                                signed_iam.request_mapping(),
                            )
                            or type(inner_verified.get("signature"))
                            is not str
                        ):
                            _invalid("response.iam_authority")
                        return _AttestedIamChannelResponse(
                            raw_result=decoded_result,
                            verification=dict(inner_verified),
                            identity=_LocalIamSessionIdentity(
                                attestor_instance_id=attestor.instance_id,
                                attestor_identity_id=snapshot["identity_id"],
                                broker_instance_id=snapshot[
                                    "broker_instance_id"
                                ],
                                runtime_id=snapshot["runtime_id"],
                                lifecycle_generation=snapshot[
                                    "lifecycle_generation"
                                ],
                                session_key_fingerprint=snapshot[
                                    "session_key_fingerprint"
                                ],
                                endpoint_id=snapshot["endpoint_id"],
                                role=snapshot["role"],
                                connection_generation=snapshot[
                                    "connection_generation"
                                ],
                            ),
                        )
                    return decoded_result
                error_value = _decode_canonical_json(
                    _exact_string(
                        verified.get("error_json"),
                        "attestor.error_json",
                    ),
                    "attestor.error_json",
                )
                _validate_remote_error(error_value)
                raise _VerifiedRemoteBrokerError(error_value)
        except NsRuntimeStateStoreIndeterminateWriteError:
            raise
        except _VerifiedRemoteBrokerError as error:
            _raise_remote_error(error.value)
        except (
            _AuthorityProvenanceFailure, AuthorityAttestationError,
            NsValidationError, AttributeError, KeyError, TypeError,
            ValueError,
        ):
            self._fail_and_reap(connection=connection)
            if operation in _WRITE_OPERATIONS and send_attempted:
                raise _indeterminate(
                    operation, "attestor_verification_failed",
                ) from None
            raise _operation_unavailable(
                operation, "attestor_unavailable",
            ) from None
        except (BrokenPipeError, EOFError, OSError):
            self._fail_and_reap(
                connection=connection,
            )
            if operation in _WRITE_OPERATIONS and send_attempted:
                raise _indeterminate(operation, "ipc_invalid_response") from None
            raise _operation_unavailable(operation, "ipc_closed") from None

    def _rotate_if_required_locked(
        self,
        *,
        attestor: AuthorityAttestorClient,
        operation: str,
    ) -> None:
        try:
            self._rotate_if_required_unchecked_locked(
                attestor=attestor,
                operation=operation,
            )
        except _AuthorityProvenanceFailure:
            raise
        except (
            AuthorityAttestationError, NsValidationError,
            BrokenPipeError, EOFError, OSError, AttributeError,
            KeyError, TypeError, ValueError,
        ) as error:
            raise _AuthorityProvenanceFailure(
                "rotation_provenance_invalid",
            ) from error

    def _rotate_if_required_unchecked_locked(
        self,
        *,
        attestor: AuthorityAttestorClient,
        operation: str,
    ) -> None:
        probe_id = "rotation_probe_" + uuid.uuid4().hex
        probe_fingerprint = "sha256:" + hashlib.sha256(
            probe_id.encode("utf-8"),
        ).hexdigest()
        prepared = attestor.prepare_request(
            identity_id=self._identity_id,
            connection_generation=self._connection_generation,
            endpoint_id=self._endpoint_id,
            role=self._role.value,
            operation=operation,
            request_id=probe_id,
            request_sequence=self._request_sequence + 1,
            request_fingerprint=probe_fingerprint,
        )
        if prepared.get("status") == "ready":
            return
        if prepared.get("status") == "rotation_in_progress":
            previous_generation = self._lifecycle_generation
            deadline = time.monotonic() + self._timeout_seconds
            while time.monotonic() < deadline:
                self._sync_endpoint_identity_locked()
                if self._lifecycle_generation > previous_generation:
                    return
                time.sleep(0.005)
            raise AuthorityAttestationError("rotation_wait_timeout")
        if prepared.get("status") != "rotation_required":
            _invalid("attestor.rotation_status")
        ticket = prepared.get("rotation_ticket")
        if type(ticket) is not dict:
            _invalid("attestor.rotation_ticket")
        connection = self._connection
        generation = self._connection_generation
        connection.send_bytes(encode_frame({
            "version": WIRE_VERSION,
            "kind": "rotate_session",
            "ticket": ticket,
        }))
        if not connection.poll(self._timeout_seconds):
            raise AuthorityAttestationError("rotation_timeout")
        rotation = decode_frame(
            connection.recv_bytes(MAX_FRAME_BYTES),
        )
        if type(rotation) is not dict:
            _invalid("rotation.response")
        rotation_attestation = {
            key: value for key, value in rotation.items()
            if key != "version"
        }
        approved = attestor.approve_rotation(
            identity_id=self._identity_id,
            rotation=rotation_attestation,
        )
        if (
            connection is not self._connection
            or generation != self._connection_generation
        ):
            _invalid("rotation.connection_generation")
        certificate = _decode_certificate(
            rotation.get("session_certificate"),
        )
        if (
            approved.get("broker_instance_id") != self._instance_id
            or approved.get("runtime_id") != self._runtime_id
            or approved.get("lifecycle_generation")
            != certificate.lifecycle_generation
            or approved.get("session_key_fingerprint")
            != _session_key_fingerprint(certificate.session_public_key)
            or approved.get("certificate_fingerprint")
            != _certificate_fingerprint(certificate)
        ):
            _invalid("rotation.approval")
        self._certificate = certificate
        self._public_key = certificate.session_public_key
        self._lifecycle_generation = certificate.lifecycle_generation
        self._certificate_fingerprint = _certificate_fingerprint(
            certificate,
        )
        self._connection_generation += 1
        self._request_sequence = 0
        self._response_sequence = 0
        self._sync_endpoint_identity_locked()

    def close(self, *, terminate: bool = False) -> None:
        try:
            with self._lock:
                if (
                    not self._closed
                    and self._custodian.alive
                    and not terminate
                    and self._role is BrokerRepositoryRole.LIFECYCLE
                ):
                    self._connection.send_bytes(encode_frame({
                        "version": WIRE_VERSION,
                        "kind": "shutdown",
                    }))
                    if self._connection.poll(5.0):
                        decode_frame(
                            self._connection.recv_bytes(MAX_FRAME_BYTES),
                        )
        except (
            BrokenPipeError, EOFError, OSError, NsValidationError,
            _AuthorityProvenanceFailure,
        ):
            pass
        finally:
            self._closed = True
            try:
                self._connection.close()
            except OSError:
                pass
            self._custodian.reap()

    def _fail_and_reap(
        self,
        *,
        connection: object | None = None,
    ) -> None:
        try:
            self._closed = True
        except AttributeError:
            return
        try:
            (
                getattr(self, "_connection", None)
                if connection is None else connection
            ).close()
        except (AttributeError, OSError):
            pass
        custodian = getattr(self, "_custodian", None)
        if type(custodian) is _BrokerProcessCustodian:
            custodian.reap()


class _ProductionRoleBrokerChannel(_RoleBrokerChannel):
    """Exact production channel bound to the compiled deployment root."""
    __slots__ = ()


class _ContractTestRoleBrokerChannel(_RoleBrokerChannel):
    """Exact deterministic contract-test channel."""
    __slots__ = ()


class _IntegrationTestRoleBrokerChannel(_RoleBrokerChannel):
    """Exact real-provider integration-test channel."""
    __slots__ = ()


def _refreshed_fixed_handle(
    stored_handle: object,
    channel: _RoleBrokerChannel,
    role: BrokerRepositoryRole,
) -> BrokerAuthorityHandle | None:
    """Refresh only an already fixed role binding without authority IPC."""

    current_handle = channel.handle
    if (
        type(stored_handle) is not BrokerAuthorityHandle
        or type(current_handle) is not BrokerAuthorityHandle
        or stored_handle.role is not role
        or current_handle.role is not role
    ):
        return None
    if stored_handle == current_handle:
        return current_handle
    if (
        stored_handle.broker_instance_id
        == current_handle.broker_instance_id
        and stored_handle.runtime_id == current_handle.runtime_id
        and stored_handle.endpoint_id == current_handle.endpoint_id
        and stored_handle.lifecycle_generation
        < current_handle.lifecycle_generation
    ):
        return current_handle
    return None


class ProductionIamAuthorityProxy(HandshakeIamAdapter):
    """Fixed-operation IAM proxy; all backend decisions originate in broker."""

    __slots__ = (
        "_channel", "_handle", "_clock", "_iam_mode",
        "_authorization_service", "_composition_binding",
    )

    def __init__(self, *args: object, **kwargs: object) -> None:
        del self, args, kwargs
        _invalid("iam_proxy.broker_authority")

    def _is_production_adapter(self) -> bool:
        return bool(
            type(self) is ProductionIamAuthorityProxy
            and self._is_broker_adapter()
            and self._verify_production_chain(SystemClock().utc_now())
        )

    def _broker_session_identity_snapshot_local(
        self,
    ) -> _LocalIamSessionIdentity | None:
        """Return one lock-free local snapshot without authority IPC."""

        channel = getattr(self, "_channel", None)
        expected_channel_type = {
            ProductionIamAuthorityProxy: _ProductionRoleBrokerChannel,
            ContractTestIamAuthorityProxy: _ContractTestRoleBrokerChannel,
            IntegrationTestIamAuthorityProxy:
                _IntegrationTestRoleBrokerChannel,
        }.get(type(self))
        if expected_channel_type is None or type(channel) is not expected_channel_type:
            return None
        try:
            generation_before = channel._lifecycle_generation
            connection_generation_before = channel._connection_generation
            public_key = channel._public_key
            handle = channel._handle
            attestor = channel._attestor
            identity = _LocalIamSessionIdentity(
                attestor_instance_id=attestor.instance_id,
                attestor_identity_id=channel._identity_id,
                broker_instance_id=channel._instance_id,
                runtime_id=channel._runtime_id,
                lifecycle_generation=generation_before,
                session_key_fingerprint=_session_key_fingerprint(public_key),
                endpoint_id=channel._endpoint_id,
                role=channel._role.value,
                connection_generation=connection_generation_before,
            )
            if (
                channel._closed
                or channel._role is not BrokerRepositoryRole.IAM
                or channel._attestor is not attestor
                or type(handle) is not BrokerAuthorityHandle
                or handle.role is not BrokerRepositoryRole.IAM
                or handle.broker_instance_id != identity.broker_instance_id
                or handle.endpoint_id != identity.endpoint_id
                or handle.lifecycle_generation
                != identity.lifecycle_generation
                or channel._lifecycle_generation != generation_before
                or channel._connection_generation
                != connection_generation_before
                or channel._public_key != public_key
                or channel._handle is not handle
            ):
                return None
            return identity
        except (AttributeError, NsValidationError, TypeError, ValueError):
            return None

    def _local_session_identity_snapshot(
        self,
    ) -> _LocalIamSessionIdentity | None:
        if type(self) is not ProductionIamAuthorityProxy:
            return None
        return self._broker_session_identity_snapshot_local()

    def _is_production_composition_bound_local(self) -> bool:
        """Pure-local composition check for async hot paths."""

        identity = self._local_session_identity_snapshot()
        channel = getattr(self, "_channel", None)
        stored_handle = getattr(self, "_handle", None)
        binding = getattr(self, "_composition_binding", None)
        substituted = {
            "authenticate", "access_check", "access_check_signed",
            "refresh_permission_snapshot", "validate_payload_ref",
            "revalidate_payload_ref", "revalidate_payload_ref_signed",
        }.intersection(getattr(self, "__dict__", {}))
        return bool(
            identity is not None
            and type(channel) is _ProductionRoleBrokerChannel
            and type(binding) is _ProductionIamCompositionBinding
            and binding.channel is channel
            and binding.attestor_instance_id
            == identity.attestor_instance_id
            and binding.attestor_public_key
            == channel._attestor.public_key
            and binding.attestor_identity_id
            == identity.attestor_identity_id
            and binding.broker_instance_id == identity.broker_instance_id
            and binding.runtime_id == identity.runtime_id
            and binding.endpoint_id == identity.endpoint_id
            and type(stored_handle) is BrokerAuthorityHandle
            and stored_handle.broker_instance_id
            == identity.broker_instance_id
            and stored_handle.endpoint_id == identity.endpoint_id
            and stored_handle.role is BrokerRepositoryRole.IAM
            and stored_handle.runtime_id == channel._runtime_id
            and stored_handle.lifecycle_generation
            <= identity.lifecycle_generation
            and not substituted
        )

    def _verified_iam_result_is_current_local(
        self,
        verified: object,
        *,
        operation: str,
        request_fingerprint: str,
        now: datetime,
    ) -> bool:
        """Validate one worker-produced receipt without locks or IPC."""

        if (
            type(verified) is not VerifiedBrokerIamResult
            or not self._is_production_composition_bound_local()
        ):
            return False
        return self._verified_broker_iam_result_is_current_local(
            verified,
            operation=operation,
            request_fingerprint=request_fingerprint,
            now=now,
        )

    def _verified_broker_iam_result_is_current_local(
        self,
        verified: object,
        *,
        operation: str,
        request_fingerprint: str,
        now: datetime,
    ) -> bool:
        if type(verified) is not VerifiedBrokerIamResult:
            return False
        before = self._broker_session_identity_snapshot_local()
        if before is None:
            return False
        authority = verified.authority
        receipt = verified.verification
        material = self._iam_receipt_verification_material_local()
        if material is None:
            return False
        attestor_public_key, attestor_instance_id = material
        if (
            before.attestor_instance_id != attestor_instance_id
            or not receipt.verify(
                attestor_public_key=attestor_public_key,
                authority=authority,
                result=verified.result,
                expected_identity=before,
                operation=operation,
                request_fingerprint=request_fingerprint,
                now=now,
            )
        ):
            return False
        after = self._broker_session_identity_snapshot_local()
        return before == after

    def _iam_receipt_verification_material_local(
        self,
    ) -> tuple[bytes, str] | None:
        channel = getattr(self, "_channel", None)
        if type(self) is ProductionIamAuthorityProxy:
            binding = getattr(self, "_composition_binding", None)
            if (
                type(binding) is not _ProductionIamCompositionBinding
                or binding.channel is not channel
            ):
                return None
            return (
                bytes(binding.attestor_public_key),
                binding.attestor_instance_id,
            )
        if type(self) in {
            ContractTestIamAuthorityProxy,
            IntegrationTestIamAuthorityProxy,
        }:
            try:
                return (
                    channel._attestor.public_key,
                    channel._attestor.instance_id,
                )
            except AttributeError:
                return None
        return None

    def _verified_broker_iam_result_is_authentic_local(
        self,
        verified: object,
        *,
        operation: str,
        request_fingerprint: str,
        now: datetime,
    ) -> bool:
        """Verify the sealed receipt while allowing an older session generation."""

        if type(verified) is not VerifiedBrokerIamResult:
            return False
        current = self._broker_session_identity_snapshot_local()
        material = self._iam_receipt_verification_material_local()
        if current is None or material is None:
            return False
        receipt = verified.verification
        authority = verified.authority
        attestor_public_key, attestor_instance_id = material
        if (
            receipt.attestor_instance_id != attestor_instance_id
            or receipt.attestor_identity_id != current.attestor_identity_id
            or receipt.broker_instance_id != current.broker_instance_id
            or receipt.runtime_id != current.runtime_id
            or receipt.endpoint_id != current.endpoint_id
            or receipt.role != current.role
        ):
            return False
        receipt_identity = _LocalIamSessionIdentity(
            attestor_instance_id=attestor_instance_id,
            attestor_identity_id=current.attestor_identity_id,
            broker_instance_id=current.broker_instance_id,
            runtime_id=current.runtime_id,
            lifecycle_generation=receipt.lifecycle_generation,
            session_key_fingerprint=receipt.session_key_fingerprint,
            endpoint_id=current.endpoint_id,
            role=current.role,
            connection_generation=current.connection_generation,
        )
        return receipt.verify(
            attestor_public_key=attestor_public_key,
            authority=authority,
            result=verified.result,
            expected_identity=receipt_identity,
            operation=operation,
            request_fingerprint=request_fingerprint,
            # This helper classifies an already verified receipt as stale; it
            # never grants current authority.  Validate the sealed receipt at
            # its attested verification instant so a rotated/expired session
            # remains distinguishable from a forged receipt.
            now=receipt.verified_at,
        )

    def _verify_production_chain(self, now: datetime) -> bool:
        channel = getattr(self, "_channel", None)
        del now
        if (
            type(channel) is not _ProductionRoleBrokerChannel
            or channel.role is not BrokerRepositoryRole.IAM
        ):
            return False
        try:
            if not channel._identity_is_current():
                return False
            handle = channel.handle
        except (NsRuntimeIamUnavailableError, AttributeError):
            return False
        stored_handle = getattr(self, "_handle", None)
        if (
            type(stored_handle) is BrokerAuthorityHandle
            and stored_handle != handle
            and stored_handle.role is BrokerRepositoryRole.IAM
            and stored_handle.broker_instance_id == channel.instance_id
            and stored_handle.runtime_id == channel._runtime_id
            and stored_handle.lifecycle_generation
            < handle.lifecycle_generation
        ):
            self._handle = handle
        return bool(
            type(self) is ProductionIamAuthorityProxy
            and type(handle) is BrokerAuthorityHandle
            and getattr(self, "_handle", None) == handle
            and channel._is_production_certificate_chain_current(
                datetime.now(timezone.utc),
            )
            and handle.role is BrokerRepositoryRole.IAM
            and handle.runtime_id == channel._runtime_id
            and handle.lifecycle_generation
            == channel._lifecycle_generation
            and handle.verify(
                channel.public_key,
                instance_id=channel.instance_id,
            )
        )

    def _is_broker_adapter(self) -> bool:
        substituted = {
            "authenticate", "access_check", "access_check_signed",
            "refresh_permission_snapshot", "validate_payload_ref",
            "revalidate_payload_ref",
        }.intersection(getattr(self, "__dict__", {}))
        expected_channel_type = {
            ProductionIamAuthorityProxy: _ProductionRoleBrokerChannel,
            ContractTestIamAuthorityProxy: _ContractTestRoleBrokerChannel,
            IntegrationTestIamAuthorityProxy: _IntegrationTestRoleBrokerChannel,
        }.get(type(self))
        channel = getattr(self, "_channel", None)
        try:
            handle = (
                channel.handle
                if (
                    type(channel) is expected_channel_type
                    and channel.role is BrokerRepositoryRole.IAM
                    and channel._identity_is_current()
                )
                else None
            )
        except (AttributeError, NsRuntimeIamUnavailableError):
            handle = None
        stored_handle = getattr(self, "_handle", None)
        if (
            type(handle) is BrokerAuthorityHandle
            and type(stored_handle) is BrokerAuthorityHandle
            and stored_handle != handle
            and stored_handle.role is BrokerRepositoryRole.IAM
            and stored_handle.broker_instance_id == channel.instance_id
            and stored_handle.runtime_id == channel._runtime_id
            and stored_handle.lifecycle_generation
            < handle.lifecycle_generation
        ):
            self._handle = handle
        return bool(
            type(self) in {
                ProductionIamAuthorityProxy,
                ContractTestIamAuthorityProxy,
                IntegrationTestIamAuthorityProxy,
            }
            and type(channel) is expected_channel_type
            and type(handle) is BrokerAuthorityHandle
            and handle.role is BrokerRepositoryRole.IAM
            and channel.alive
            and (
                (
                    type(self) is ProductionIamAuthorityProxy
                    and self._verify_production_chain(
                        SystemClock().utc_now(),
                    )
                )
                or (
                    type(self) is ContractTestIamAuthorityProxy
                    and channel._attested_identity().get("realm")
                    == "contract-test"
                )
                or (
                    type(self) is IntegrationTestIamAuthorityProxy
                    and channel._attested_identity().get("realm")
                    == "integration-test"
                )
            )
            and not substituted
        )

    async def authenticate(
        self,
        request: HandshakeIamRequest,
    ) -> HandshakeIamAuthority:
        if type(request) is not HandshakeIamRequest:
            _invalid("iam_proxy.request")
        token = request.credential.take()
        try:
            payload = {
                "token": token,
                "claims": request.claims,
            }
            verified = await self._signed_request("introspect", payload)
        finally:
            del token
        result = verified.result
        if type(result) is not HandshakeIamAuthority:
            raise _broker_unavailable("malformed_introspection_result")
        return result

    async def access_check_signed(
        self,
        request: IamAccessCheckRequest,
    ) -> VerifiedBrokerIamResult:
        if type(request) is not IamAccessCheckRequest:
            _invalid("iam_proxy.request")
        return await self._signed_request("runtime_access_check", request)

    async def access_check(
        self,
        request: IamAccessCheckRequest,
    ) -> IamAccessDecision:
        result = (await self.access_check_signed(request)).result
        if type(result) is not IamAccessDecision:
            raise _broker_unavailable("malformed_access_result")
        return result

    async def refresh_permission_snapshot(
        self,
        snapshot: "PermissionSnapshot",
    ) -> "PermissionSnapshot":
        from ns_runtime.iam.models import PermissionSnapshot

        if type(snapshot) is not PermissionSnapshot:
            _invalid("iam_proxy.snapshot")
        result = (await self._signed_request(
            "permission_snapshot", snapshot,
        )).result
        if type(result) is not PermissionSnapshot:
            raise _broker_unavailable("malformed_snapshot_result")
        return result

    async def validate_payload_ref(
        self,
        request: PayloadRefValidationRequest,
    ) -> PayloadRefValidationResult:
        if type(request) is not PayloadRefValidationRequest:
            _invalid("iam_proxy.payload_request")
        result = (await self._signed_request(
            "payload_validate", request,
        )).result
        if type(result) is not PayloadRefValidationResult:
            raise _broker_unavailable("malformed_payload_result")
        return result

    async def revalidate_payload_ref(
        self,
        request: PayloadRefRevalidationRequest,
    ) -> PayloadRefRevalidationDecision:
        result = (await self.revalidate_payload_ref_signed(request)).result
        if type(result) is not PayloadRefRevalidationDecision:
            raise _broker_unavailable("malformed_payload_result")
        return result

    async def revalidate_payload_ref_signed(
        self,
        request: PayloadRefRevalidationRequest,
    ) -> VerifiedBrokerIamResult:
        if type(request) is not PayloadRefRevalidationRequest:
            _invalid("iam_proxy.payload_request")
        verified = await self._signed_request("payload_revalidate", request)
        result = verified.result
        if type(result) is not PayloadRefRevalidationDecision:
            raise _broker_unavailable("malformed_payload_result")
        return verified

    async def _signed_request(
        self,
        operation: str,
        payload: object,
    ) -> VerifiedBrokerIamResult:
        if operation not in _IAM_OPERATIONS:
            _invalid("iam_proxy.provenance")
        expected_channel_type = {
            ProductionIamAuthorityProxy: _ProductionRoleBrokerChannel,
            ContractTestIamAuthorityProxy: _ContractTestRoleBrokerChannel,
            IntegrationTestIamAuthorityProxy:
                _IntegrationTestRoleBrokerChannel,
        }.get(type(self))
        channel = getattr(self, "_channel", None)
        if (
            expected_channel_type is None
            or type(channel) is not expected_channel_type
            or channel.role is not BrokerRepositoryRole.IAM
        ):
            _invalid("iam_proxy.provenance")
        encoded_payload = _encode_iam_request(operation, payload)
        return await asyncio.to_thread(
            self._signed_request_sync,
            operation,
            encoded_payload,
        )

    def _signed_request_sync(
        self,
        operation: str,
        encoded_payload: object,
    ) -> VerifiedBrokerIamResult:
        channel = self._channel
        handle = _refreshed_fixed_handle(
            getattr(self, "_handle", None),
            channel,
            BrokerRepositoryRole.IAM,
        )
        if handle is None:
            _invalid("iam_proxy.provenance")
        self._handle = handle
        channel_result = channel.request(
            operation=operation,
            payload=encoded_payload,  # type: ignore[arg-type]
        )
        self._handle = channel.handle
        try:
            if type(channel_result) is not _AttestedIamChannelResponse:
                _invalid("iam_proxy.attested_result")
            result = _decode_signed_iam_result(channel_result.raw_result)
            typed = _decode_iam_result(
                operation, result.result_mapping(),
            )
            material = self._iam_receipt_verification_material_local()
            if (
                material is None
                or channel_result.identity.attestor_instance_id
                != material[1]
            ):
                _invalid("iam_proxy.attestor_binding")
            verified = _verified_iam_result_from_attestation(
                operation=operation,
                result=typed,
                authority=result,
                verification=channel_result.verification,
                attestor_public_key=material[0],
                expected_identity=channel_result.identity,
            )
        except (NsValidationError, KeyError, TypeError, ValueError):
            channel._fail_and_reap()
            raise _broker_unavailable("signature_invalid") from None
        return verified

    def _verify_signed_iam_authority(
        self,
        authority: BrokerSignedIamResult,
        *,
        operation: str,
        request_fingerprint: str,
        verification: BrokerIamVerificationReceipt | None = None,
        result: object | None = None,
    ) -> bool:
        if type(verification) is not BrokerIamVerificationReceipt:
            return False
        verified = object.__new__(VerifiedBrokerIamResult)
        object.__setattr__(verified, "result", result)
        object.__setattr__(verified, "authority", authority)
        object.__setattr__(verified, "verification", verification)
        return self._verified_iam_result_is_current_local(
            verified,
            operation=operation,
            request_fingerprint=request_fingerprint,
            now=datetime.now(timezone.utc),
        )

    def _bind_authorization_service(self, service: object) -> None:
        if (
            not self._is_production_adapter()
            or service is None
            or self._authorization_service is not None
        ):
            _invalid("iam_proxy.authorization_service")
        self._authorization_service = service

    def _owns_authorization_service_local(self, service: object) -> bool:
        return bool(
            self._is_production_composition_bound_local()
            and self._authorization_service is service
        )

    def _owns_authorization_service(self, service: object) -> bool:
        """Compatibility alias; ownership checks are intentionally local."""

        if type(self) is not ProductionIamAuthorityProxy:
            return False
        return self._owns_authorization_service_local(service)

    def __copy__(self) -> "ProductionIamAuthorityProxy":
        _invalid("iam_proxy.copy")

    def __deepcopy__(self, memo: dict[int, object]) -> "ProductionIamAuthorityProxy":
        del memo
        _invalid("iam_proxy.copy")


class ContractTestIamAuthorityProxy(ProductionIamAuthorityProxy):
    """Explicit non-production broker adapter bound to a test trust root."""
    __slots__ = ()


class IntegrationTestIamAuthorityProxy(ProductionIamAuthorityProxy):
    """Explicit real-provider adapter under a non-production trust root."""
    __slots__ = ()


class _RepositoryProxy:
    __slots__ = ("_channel", "_handle")
    _ROLE: BrokerRepositoryRole

    def __init__(self, *args: object, **kwargs: object) -> None:
        del self, args, kwargs
        _invalid("repository_proxy.broker_authority")

    @property
    def role(self) -> BrokerRepositoryRole:
        channel = getattr(self, "_channel", None)
        role = getattr(channel, "role", None)
        if type(role) is not BrokerRepositoryRole:
            raise _state_denied("repository_provenance_denied")
        return role

    def _binding_is_current(self) -> bool:
        binding = _repository_proxy_binding(type(self))
        channel = getattr(self, "_channel", None)
        role = getattr(channel, "role", None)
        try:
            handle = (
                channel.handle
                if (
                    binding is not None
                    and type(channel) is binding[1]
                    and type(role) is BrokerRepositoryRole
                    and channel._identity_is_current()
                )
                else None
            )
        except (AttributeError, NsRuntimeIamUnavailableError):
            handle = None
        stored_handle = getattr(self, "_handle", None)
        if (
            type(handle) is BrokerAuthorityHandle
            and type(stored_handle) is BrokerAuthorityHandle
            and stored_handle != handle
            and type(role) is BrokerRepositoryRole
            and stored_handle.role is role
            and stored_handle.broker_instance_id == channel.instance_id
            and stored_handle.runtime_id == channel._runtime_id
            and stored_handle.lifecycle_generation
            < handle.lifecycle_generation
        ):
            self._handle = handle
        if type(handle) is not BrokerAuthorityHandle:
            return False
        return bool(
            binding is not None
            and type(channel) is binding[1]
            and role is binding[0]
            and type(handle) is BrokerAuthorityHandle
            and getattr(self, "_handle", None) == handle
            and handle.role is role
            and handle.runtime_id == channel._runtime_id
            and handle.lifecycle_generation
            == channel._lifecycle_generation
            and handle.verify(
                channel.public_key,
                instance_id=channel.instance_id,
            )
            and channel._identity_is_current()
        )

    async def _request(self, operation: str, payload: object) -> object:
        binding = _repository_proxy_binding(type(self))
        channel = getattr(self, "_channel", None)
        role = getattr(channel, "role", None)
        if (
            binding is None
            or type(channel) is not binding[1]
            or type(role) is not BrokerRepositoryRole
            or role is not binding[0]
            or operation not in _ROLE_OPERATIONS[role.value]
        ):
            raise _state_denied("repository_operation_denied")
        return await asyncio.to_thread(
            self._request_sync,
            operation,
            payload,
        )

    def _request_sync(self, operation: str, payload: object) -> object:
        channel = self._channel
        handle = _refreshed_fixed_handle(
            getattr(self, "_handle", None),
            channel,
            channel.role,
        )
        if handle is None:
            raise _state_denied("repository_operation_denied")
        self._handle = handle
        result = channel.request(
            operation=operation,
            payload=payload,  # type: ignore[arg-type]
        )
        self._handle = channel.handle
        return result

    def __copy__(self) -> "_RepositoryProxy":
        _invalid("repository_proxy.copy")

    def __deepcopy__(self, memo: dict[int, object]) -> "_RepositoryProxy":
        del memo
        _invalid("repository_proxy.copy")


class AdmissionRepositoryProxy(_RepositoryProxy):
    __slots__ = ()
    _ROLE = BrokerRepositoryRole.ADMISSION

    def delivery_scope(
        self, *, tenant_id: str, bucket_id: int, layout_generation: int,
    ) -> DeliveryPersistencePartition:
        return _delivery_partition(
            tenant_id=tenant_id,
            bucket_id=bucket_id,
            layout_generation=layout_generation,
        )

    async def read(
        self, *, scope: DeliveryPersistencePartition, key: StateKey,
        consistency: StateConsistency,
    ) -> StateReadResult:
        del consistency
        operation = {
            "delivery": "read_delivery",
            "dedup": "read_admission_dedup",
            "summary": "read_admission_summary",
        }.get(key.object_type)
        if operation is None:
            raise _state_denied("admission_read_resource_denied")
        return decode_read_result(await self._request(operation, {
            "tenant_id": scope.tenant_id,
            "bucket_id": scope.bucket_id,
            "layout_generation": scope.layout_generation,
            "object_id": key.object_id,
        }))

    async def transact(
        self,
        transaction: DeliveryPersistenceTransaction,
    ) -> DeliveryPersistenceTransactionResult:
        partition = transaction.partition
        raw = await self._request(
            "transact_admission",
            encode_transaction_request(
                transaction,
                tenant_id=partition.tenant_id,
                bucket_id=partition.bucket_id,
                layout_generation=partition.layout_generation,
            ),
        )
        return _bind_write_transaction_result(
            transaction, raw, operation="transact_admission",
        )

    async def read_delivery(
        self, *, tenant_id: str, bucket_id: int, layout_generation: int,
        delivery_id: str,
    ) -> StateReadResult:
        return decode_read_result(await self._request("read_delivery", {
            "tenant_id": tenant_id,
            "bucket_id": bucket_id,
            "layout_generation": layout_generation,
            "object_id": delivery_id,
        }))

    async def transact_admission(
        self, *, tenant_id: str, bucket_id: int, layout_generation: int,
        transaction: DeliveryPersistenceTransaction,
    ) -> DeliveryPersistenceTransactionResult:
        if transaction.partition != self.delivery_scope(
            tenant_id=tenant_id,
            bucket_id=bucket_id,
            layout_generation=layout_generation,
        ):
            _invalid("admission.transaction_partition")
        return await self.transact(transaction)


class SchedulerRepositoryProxy(_RepositoryProxy):
    __slots__ = ()
    _ROLE = BrokerRepositoryRole.SCHEDULER

    def delivery_scope(
        self, *, tenant_id: str, bucket_id: int, layout_generation: int,
    ) -> DeliveryPersistencePartition:
        return _delivery_partition(
            tenant_id=tenant_id,
            bucket_id=bucket_id,
            layout_generation=layout_generation,
        )

    async def read(
        self, *, scope: DeliveryPersistencePartition, key: StateKey,
        consistency: StateConsistency,
    ) -> StateReadResult:
        del consistency
        operation = {
            "delivery": "read_delivery",
            "attempt": "read_attempt",
            "summary": "read_summary",
            "delivery_owner": "read_delivery_owner",
            "delivery_scheduler_cursor": "read_scheduler_cursor",
        }.get(key.object_type)
        if operation is None:
            raise _state_denied("scheduler_read_resource_denied")
        return decode_read_result(await self._request(operation, {
            "tenant_id": scope.tenant_id,
            "bucket_id": scope.bucket_id,
            "layout_generation": scope.layout_generation,
            "object_id": key.object_id,
        }))

    async def transact(
        self,
        transaction: DeliveryPersistenceTransaction,
    ) -> DeliveryPersistenceTransactionResult:
        partition = transaction.partition
        raw = await self._request(
            "transact_scheduler",
            encode_transaction_request(
                transaction,
                tenant_id=partition.tenant_id,
                bucket_id=partition.bucket_id,
                layout_generation=partition.layout_generation,
            ),
        )
        return _bind_write_transaction_result(
            transaction, raw, operation="transact_scheduler",
        )

    async def read_ordered_index(
        self, *, scope: DeliveryPersistencePartition,
        index: StateOrderedIndexKey, limit: int,
        max_score: float | None = None,
        start_after: "StateOrderedIndexCursor | None" = None,
    ) -> object:
        return await self.read_scheduler_index(
            tenant_id=scope.tenant_id,
            bucket_id=scope.bucket_id,
            layout_generation=scope.layout_generation,
            index_name=index.name,
            cursor=start_after,
            limit=limit,
            max_score=max_score,
        )

    async def read_delivery(
        self, *, tenant_id: str, bucket_id: int, layout_generation: int,
        delivery_id: str,
    ) -> StateReadResult:
        return decode_read_result(await self._request("read_delivery", {
            "tenant_id": tenant_id,
            "bucket_id": bucket_id,
            "layout_generation": layout_generation,
            "object_id": delivery_id,
        }))

    async def read_attempt(
        self, *, tenant_id: str, bucket_id: int, layout_generation: int,
        attempt_id: str,
    ) -> StateReadResult:
        return decode_read_result(await self._request("read_attempt", {
            "tenant_id": tenant_id,
            "bucket_id": bucket_id,
            "layout_generation": layout_generation,
            "object_id": attempt_id,
        }))

    async def read_summary(
        self, *, tenant_id: str, bucket_id: int, layout_generation: int,
        summary_id: str,
    ) -> StateReadResult:
        return decode_read_result(await self._request("read_summary", {
            "tenant_id": tenant_id,
            "bucket_id": bucket_id,
            "layout_generation": layout_generation,
            "object_id": summary_id,
        }))

    async def read_scheduler_index(
        self, *, tenant_id: str, bucket_id: int, layout_generation: int,
        index_name: str,
        cursor: "StateOrderedIndexCursor | None" = None,
        limit: int = 100,
        max_score: float | None = None,
    ) -> object:
        raw = await self._request("read_scheduler_index", {
            "tenant_id": tenant_id,
            "bucket_id": bucket_id,
            "layout_generation": layout_generation,
            "index_name": index_name,
            "cursor": encode_cursor(
                cursor,
                index_name=index_name,
                index_bucket="delivery",
            ),
            "limit": limit,
            "max_score": max_score,
        })
        return decode_index_result(
            raw,
            index_name=index_name,
            index_bucket="delivery",
        )

    async def transact_scheduler(
        self, *, tenant_id: str, bucket_id: int, layout_generation: int,
        transaction: DeliveryPersistenceTransaction,
    ) -> DeliveryPersistenceTransactionResult:
        if transaction.partition != self.delivery_scope(
            tenant_id=tenant_id,
            bucket_id=bucket_id,
            layout_generation=layout_generation,
        ):
            _invalid("scheduler.transaction_partition")
        return await self.transact(transaction)


class PayloadRepositoryProxy(_RepositoryProxy):
    __slots__ = ()
    _ROLE = BrokerRepositoryRole.PAYLOAD

    def delivery_scope(
        self, *, tenant_id: str, bucket_id: int, layout_generation: int,
    ) -> DeliveryPersistencePartition:
        return _delivery_partition(
            tenant_id=tenant_id,
            bucket_id=bucket_id,
            layout_generation=layout_generation,
        )

    async def read(
        self, *, scope: DeliveryPersistencePartition, key: StateKey,
        consistency: StateConsistency,
    ) -> StateReadResult:
        del consistency
        if key.object_type != "payload_body":
            raise _state_denied("payload_read_resource_denied")
        return await self.read_payload_body(
            tenant_id=scope.tenant_id,
            bucket_id=scope.bucket_id,
            layout_generation=scope.layout_generation,
            object_id=key.object_id,
        )
    async def read_payload_body(
        self, *, tenant_id: str, bucket_id: int, layout_generation: int,
        object_id: str,
    ) -> StateReadResult:
        return decode_read_result(await self._request("read_payload_body", {
            "tenant_id": tenant_id,
            "bucket_id": bucket_id,
            "layout_generation": layout_generation,
            "object_id": object_id,
        }))


class RegistryRepositoryProxy(_RepositoryProxy):
    __slots__ = ()
    _ROLE = BrokerRepositoryRole.REGISTRY

    @property
    def runtime_id(self) -> str:
        return self._handle.runtime_id

    @property
    def namespace(self) -> StateNamespace:
        return _registry_partition(self.runtime_id).namespace

    async def read(
        self, *, key: StateKey, consistency: StateConsistency,
    ) -> StateReadResult:
        del consistency
        operation = {
            "delivery_authority_layout": "read_registry_layout",
            "delivery_tenant_registration": "read_registry_tenant",
        }.get(key.object_type)
        if operation is None or key.namespace != self.namespace:
            raise _state_denied("registry_read_resource_denied")
        return decode_read_result(await self._request(
            operation, {"object_id": key.object_id},
        ))

    async def transact(
        self,
        transaction: DeliveryPersistenceTransaction,
    ) -> DeliveryPersistenceTransactionResult:
        expected = _registry_partition(self.runtime_id)
        if transaction.partition != expected:
            raise _state_denied("registry_partition_denied")
        raw = await self._request(
            "transact_registry",
            encode_transaction_request(
                transaction,
                tenant_id=expected.tenant_id,
                bucket_id=expected.bucket_id,
                layout_generation=expected.layout_generation,
            ),
        )
        return _bind_write_transaction_result(
            transaction, raw, operation="transact_registry",
        )

    async def read_ordered_index(
        self, *, index: StateOrderedIndexKey, limit: int,
        start_after: "StateOrderedIndexCursor | None" = None,
    ) -> object:
        if (
            index.namespace != self.namespace
            or index.name != "delivery.tenant_registry"
            or index.bucket != "runtime"
        ):
            raise _state_denied("registry_index_denied")
        return decode_index_result(
            await self._request("read_registry_index", {
                "index_name": index.name,
                "index_bucket": index.bucket,
                "cursor": encode_cursor(
                    start_after,
                    index_name=index.name,
                    index_bucket=index.bucket,
                ),
                "limit": limit,
            }),
            index_name=index.name,
            index_bucket=index.bucket,
        )

    async def read_registry_layout(self, *, object_id: str) -> StateReadResult:
        return decode_read_result(await self._request(
            "read_registry_layout", {"object_id": object_id},
        ))


class AuditRepositoryProxy(_RepositoryProxy):
    __slots__ = ()
    _ROLE = BrokerRepositoryRole.AUDIT

    async def append_audit(
        self, *, namespace: StateNamespace, object_id: str,
        document: StateDocument,
    ) -> object:
        raw = await self._request("append_audit", {
            "namespace": {
                "kind": namespace.kind.value,
                "domain": namespace.domain,
                "tenant_id": namespace.tenant_id,
                "runtime_id": namespace.runtime_id,
                "plugin_name": namespace.plugin_name,
            },
            "object_id": object_id,
            "document": encode_document(document),
        })
        try:
            return decode_append_result(raw)
        except (NsValidationError, TypeError, ValueError):
            raise _indeterminate(
                "append_audit", "ipc_malformed_write_result",
            ) from None


class _ContractTestAdmissionRepositoryProxy(AdmissionRepositoryProxy):
    __slots__ = ()


class _ContractTestSchedulerRepositoryProxy(SchedulerRepositoryProxy):
    __slots__ = ()


class _ContractTestPayloadRepositoryProxy(PayloadRepositoryProxy):
    __slots__ = ()


class _ContractTestRegistryRepositoryProxy(RegistryRepositoryProxy):
    __slots__ = ()


class _ContractTestAuditRepositoryProxy(AuditRepositoryProxy):
    __slots__ = ()


class _IntegrationTestAdmissionRepositoryProxy(AdmissionRepositoryProxy):
    __slots__ = ()


class _IntegrationTestSchedulerRepositoryProxy(SchedulerRepositoryProxy):
    __slots__ = ()


class _IntegrationTestPayloadRepositoryProxy(PayloadRepositoryProxy):
    __slots__ = ()


class _IntegrationTestRegistryRepositoryProxy(RegistryRepositoryProxy):
    __slots__ = ()


class _IntegrationTestAuditRepositoryProxy(AuditRepositoryProxy):
    __slots__ = ()


class AuthorityBrokerStateStoreProxy:
    """Lifecycle/health proxy used by RuntimeContext; it is not a raw Store."""

    __slots__ = ("_channel", "_handle", "_state")

    def __init__(self, *args: object, **kwargs: object) -> None:
        del self, args, kwargs
        _invalid("state_proxy.broker_authority")

    @property
    def state(self) -> object:
        from ns_common.state_store import StateStoreLifecycleState

        return {
            "new": StateStoreLifecycleState.NEW,
            "open": StateStoreLifecycleState.OPEN,
            "closed": StateStoreLifecycleState.CLOSED,
        }[self._state]

    def _binding_is_current(self) -> bool:
        expected_channel_type = {
            AuthorityBrokerStateStoreProxy: _ProductionRoleBrokerChannel,
            _ContractTestAuthorityBrokerStateStoreProxy:
                _ContractTestRoleBrokerChannel,
            _IntegrationTestAuthorityBrokerStateStoreProxy:
                _IntegrationTestRoleBrokerChannel,
        }.get(type(self))
        channel = getattr(self, "_channel", None)
        handle = getattr(self, "_handle", None)
        try:
            current_handle = (
                channel.handle
                if (
                    type(channel) is expected_channel_type
                    and channel.role is BrokerRepositoryRole.LIFECYCLE
                    and channel._identity_is_current()
                )
                else None
            )
        except (AttributeError, NsRuntimeIamUnavailableError):
            current_handle = None
        if type(current_handle) is not BrokerAuthorityHandle:
            return False
        if (
            type(handle) is BrokerAuthorityHandle
            and type(current_handle) is BrokerAuthorityHandle
            and handle != current_handle
            and handle.role is BrokerRepositoryRole.LIFECYCLE
            and handle.broker_instance_id == channel.instance_id
            and handle.runtime_id == channel._runtime_id
            and handle.lifecycle_generation
            < current_handle.lifecycle_generation
        ):
            self._handle = current_handle
            handle = current_handle
        return bool(
            expected_channel_type is not None
            and type(channel) is expected_channel_type
            and type(handle) is BrokerAuthorityHandle
            and handle.role is BrokerRepositoryRole.LIFECYCLE
            and handle.runtime_id == channel._runtime_id
            and handle.lifecycle_generation
            == channel._lifecycle_generation
            and handle.verify(
                channel.public_key,
                instance_id=channel.instance_id,
            )
            and channel._identity_is_current()
        )

    async def open(self) -> None:
        if self._state == "closed":
            raise _state_unavailable("broker_closed")
        self._validate_local_lifecycle_binding()
        await asyncio.to_thread(self._health_request_sync)
        self._state = "open"

    async def health(self) -> StateStoreHealth:
        self._validate_local_lifecycle_binding()
        return await asyncio.to_thread(self._health_request_sync)

    def _validate_local_lifecycle_binding(self) -> None:
        expected_channel_type = {
            AuthorityBrokerStateStoreProxy: _ProductionRoleBrokerChannel,
            _ContractTestAuthorityBrokerStateStoreProxy:
                _ContractTestRoleBrokerChannel,
            _IntegrationTestAuthorityBrokerStateStoreProxy:
                _IntegrationTestRoleBrokerChannel,
        }.get(type(self))
        channel = getattr(self, "_channel", None)
        if (
            expected_channel_type is None
            or type(channel) is not expected_channel_type
            or channel.role is not BrokerRepositoryRole.LIFECYCLE
        ):
            raise _state_unavailable("broker_provenance_invalid")

    def _health_request_sync(self) -> StateStoreHealth:
        channel = self._channel
        handle = _refreshed_fixed_handle(
            getattr(self, "_handle", None),
            channel,
            BrokerRepositoryRole.LIFECYCLE,
        )
        if handle is None:
            raise _state_unavailable("broker_provenance_invalid")
        self._handle = handle
        raw_result = channel.request(
            operation="state_health",
            payload={},
        )
        self._handle = channel.handle
        try:
            result = decode_health(raw_result)
        except (NsValidationError, KeyError, TypeError, ValueError):
            channel._fail_and_reap()
            raise _state_unavailable("invalid_health") from None
        if type(result) is not StateStoreHealth:
            channel._fail_and_reap()
            raise _state_unavailable("invalid_health")
        return result

    async def close(self) -> None:
        if self._state == "closed":
            return
        self._state = "closed"
        await asyncio.to_thread(self._channel.close)


class _ContractTestAuthorityBrokerStateStoreProxy(
    AuthorityBrokerStateStoreProxy,
):
    __slots__ = ()


class _IntegrationTestAuthorityBrokerStateStoreProxy(
    AuthorityBrokerStateStoreProxy,
):
    __slots__ = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class AuthorityBrokerRepositories:
    admission: AdmissionRepositoryProxy
    scheduler: SchedulerRepositoryProxy
    payload: PayloadRepositoryProxy
    registry: RegistryRepositoryProxy
    audit: AuditRepositoryProxy


class ProductionAuthorityBroker:
    """Main-process ownership of only IPC proxies and public verification data."""

    __slots__ = (
        "iam", "repositories", "state_store",
        "broker_instance_id", "_channel",
    )

    def __init__(self, *args: object, **kwargs: object) -> None:
        del self, args, kwargs
        _invalid("broker.bootstrap")

    @property
    def alive(self) -> bool:
        return self._channel.alive

    @property
    def public_key(self) -> bytes:
        return self._channel.public_key

    def current_session_identity(self) -> Mapping[str, object]:
        return self._channel.current_session_identity()

    def close(self, *, terminate: bool = False) -> None:
        self._channel.close(terminate=terminate)

    def __del__(self) -> None:
        channel = getattr(self, "_channel", None)
        if type(channel) in {
            _ProductionRoleBrokerChannel,
            _ContractTestRoleBrokerChannel,
            _IntegrationTestRoleBrokerChannel,
        }:
            channel.close(terminate=True)


class ContractTestAuthorityBroker(ProductionAuthorityBroker):
    __slots__ = ()


class IntegrationTestAuthorityBroker(ProductionAuthorityBroker):
    __slots__ = ()


def start_production_authority_broker(
    *args: object,
    **kwargs: object,
) -> ProductionAuthorityBroker:
    """Reject the former caller-configured production trust root."""

    del args, kwargs
    _invalid("broker.production_starter_requires_inherited_fds")


def start_contract_test_authority_broker(
    *,
    config: AuthorityBrokerConfig,
    iam_service_credential: str,
    startup_timeout_seconds: float = 15.0,
    session_ttl_seconds: float = _SESSION_CERTIFICATE_TTL_SECONDS,
    delegation_ttl_seconds: float = _DELEGATION_CERTIFICATE_TTL_SECONDS,
) -> ProductionAuthorityBroker:
    """Start an explicitly non-production broker under an ephemeral test root."""

    if (
        type(config) is not AuthorityBrokerConfig
        or type(iam_service_credential) is not str
        or not iam_service_credential
        or config.state_backend in {"redis", "valkey"}
    ):
        _invalid("broker.contract_test_config")
    return _start_test_authority_broker(
        config=config,
        iam_service_credential=iam_service_credential,
        state_password=None,
        startup_timeout_seconds=startup_timeout_seconds,
        realm="contract-test",
        session_ttl_seconds=session_ttl_seconds,
        delegation_ttl_seconds=delegation_ttl_seconds,
    )


def start_integration_test_authority_broker(
    *,
    config: AuthorityBrokerConfig,
    iam_service_credential: str,
    state_password: str | None,
    startup_timeout_seconds: float = 15.0,
    session_ttl_seconds: float = _SESSION_CERTIFICATE_TTL_SECONDS,
    delegation_ttl_seconds: float = _DELEGATION_CERTIFICATE_TTL_SECONDS,
) -> ProductionAuthorityBroker:
    """Run real provider integration under a non-production test trust root."""

    if (
        type(config) is not AuthorityBrokerConfig
        or config.state_backend not in {"redis", "valkey"}
        or type(iam_service_credential) is not str
        or not iam_service_credential
        or (
            state_password is not None
            and (type(state_password) is not str or not state_password)
        )
    ):
        _invalid("broker.integration_test_config")
    return _start_test_authority_broker(
        config=config,
        iam_service_credential=iam_service_credential,
        state_password=state_password,
        startup_timeout_seconds=startup_timeout_seconds,
        realm="integration-test",
        session_ttl_seconds=session_ttl_seconds,
        delegation_ttl_seconds=delegation_ttl_seconds,
    )


def _start_test_authority_broker(
    *,
    config: AuthorityBrokerConfig,
    iam_service_credential: str,
    state_password: str | None,
    startup_timeout_seconds: float,
    realm: str,
    session_ttl_seconds: float,
    delegation_ttl_seconds: float,
) -> ProductionAuthorityBroker:
    root_private_key = Ed25519PrivateKey.generate()
    root_private_bytes = root_private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    root_public_key = root_private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    key_read, key_write = os.pipe()
    secrets_read, secrets_write = os.pipe()
    try:
        os.write(key_write, root_private_bytes)
        os.write(secrets_write, encode_frame({
            "iam_service_credential": iam_service_credential,
            "state_password_base64": (
                None if state_password is None
                else encode_bytes(state_password.encode("utf-8"))
            ),
        }))
    finally:
        os.close(key_write)
        os.close(secrets_write)
        root_private_bytes = b"\0" * len(root_private_bytes)
        del root_private_key
    return _spawn_authority_broker(
        config=config,
        expected_root_public_key=root_public_key,
        root_key_fd=key_read,
        secrets_fd=secrets_read,
        realm=realm,
        startup_timeout_seconds=startup_timeout_seconds,
        session_ttl_seconds=session_ttl_seconds,
        delegation_ttl_seconds=delegation_ttl_seconds,
    )


def _start_production_authority_broker_from_inherited_fds(
    *,
    config: AuthorityBrokerConfig,
    root_key_fd: int,
    secrets_fd: int,
    startup_timeout_seconds: float = 15.0,
) -> ProductionAuthorityBroker:
    """Deployment entry: consume one-shot inherited descriptors."""

    if (
        type(config) is not AuthorityBrokerConfig
        or type(root_key_fd) is not int
        or root_key_fd < 0
        or type(secrets_fd) is not int
        or secrets_fd < 0
    ):
        _invalid("broker.deployment_bootstrap")
    return _spawn_authority_broker(
        config=config,
        expected_root_public_key=_PRODUCTION_ROOT_PUBLIC_KEY,
        root_key_fd=root_key_fd,
        secrets_fd=secrets_fd,
        realm="production",
        startup_timeout_seconds=startup_timeout_seconds,
        session_ttl_seconds=_SESSION_CERTIFICATE_TTL_SECONDS,
        delegation_ttl_seconds=_DELEGATION_CERTIFICATE_TTL_SECONDS,
    )


def _spawn_authority_broker(
    *,
    config: AuthorityBrokerConfig,
    expected_root_public_key: bytes,
    root_key_fd: int,
    secrets_fd: int,
    realm: str,
    startup_timeout_seconds: float,
    session_ttl_seconds: float,
    delegation_ttl_seconds: float,
) -> ProductionAuthorityBroker:
    if realm not in _BROKER_REALMS:
        _invalid("broker.realm")
    context = multiprocessing.get_context("spawn")
    attestor = start_authority_attestor(
        realm=realm,
        expected_test_root_public_key=(
            None if realm == "production" else expected_root_public_key
        ),
        timeout_seconds=startup_timeout_seconds,
    )
    endpoint_pairs = {
        role.value: context.Pipe(duplex=True)
        for role in BrokerRepositoryRole
    }
    parents = {
        role: pair[0] for role, pair in endpoint_pairs.items()
    }
    children = {
        role: pair[1] for role, pair in endpoint_pairs.items()
    }
    root_key_handle = DupFd(root_key_fd)
    secrets_handle = DupFd(secrets_fd)
    process = context.Process(
        target=_authority_broker_process,
        args=(
            children,
            encode_frame(_encode_broker_config(config)),
            root_key_handle,
            secrets_handle,
            realm,
            expected_root_public_key,
            attestor.public_key,
            attestor.instance_id,
            float(session_ttl_seconds),
            float(delegation_ttl_seconds),
        ),
        name="ns-runtime-authority-broker",
        daemon=False,
    )
    try:
        process.start()
    finally:
        for child in children.values():
            child.close()
        for fd in (root_key_fd, secrets_fd):
            try:
                os.close(fd)
            except OSError:
                pass
    try:
        return _accept_started_authority_broker(
            parents=parents,
            process=process,
            attestor=attestor,
            config=config,
            realm=realm,
            startup_timeout_seconds=startup_timeout_seconds,
        )
    except BaseException:
        for parent in parents.values():
            try:
                parent.close()
            except OSError:
                pass
        attestor.close()
        raise


def _complete_inherited_authority_broker_start(
    *,
    parents: Mapping[str, Connection],
    process: multiprocessing.Process,
    attestor: AuthorityAttestorClient,
    config: AuthorityBrokerConfig,
    startup_timeout_seconds: float = 15.0,
) -> ProductionAuthorityBroker:
    """Send only non-secret config to the already isolated broker child."""

    if (
        type(config) is not AuthorityBrokerConfig
        or not process.is_alive()
        or set(parents) != {role.value for role in BrokerRepositoryRole}
    ):
        _invalid("broker.pending_bootstrap")
    lifecycle = parents[BrokerRepositoryRole.LIFECYCLE.value]
    try:
        lifecycle.send_bytes(encode_frame({
            "version": WIRE_VERSION,
            "kind": "bootstrap_config",
            "config": _encode_broker_config(config),
        }))
    except (BrokenPipeError, EOFError, OSError):
        raise _broker_unavailable("bootstrap_channel_closed") from None
    return _accept_started_authority_broker(
        parents=parents,
        process=process,
        attestor=attestor,
        config=config,
        realm="production",
        startup_timeout_seconds=startup_timeout_seconds,
    )


def _accept_started_authority_broker(
    *,
    parents: Mapping[str, Connection],
    process: multiprocessing.Process,
    attestor: AuthorityAttestorClient,
    config: AuthorityBrokerConfig,
    realm: str,
    startup_timeout_seconds: float,
) -> ProductionAuthorityBroker:
    expected_roles = {role.value for role in BrokerRepositoryRole}
    if set(parents) != expected_roles:
        raise _broker_unavailable("startup_endpoint_set_invalid")
    ready_by_role: dict[str, dict[str, object]] = {}
    try:
        for role, parent in parents.items():
            if not parent.poll(startup_timeout_seconds):
                raise _broker_unavailable("startup_timeout")
            ready = decode_frame(parent.recv_bytes(MAX_FRAME_BYTES))
            if type(ready) is not dict or ready.get("ok") is not True:
                reason = (
                    ready.get("reason", "startup_failed")
                    if type(ready) is dict
                    else "startup_failed"
                )
                if reason == "parallel_production_composition":
                    raise _state_denied(reason)
                raise _broker_unavailable(str(reason))
            ready_by_role[role] = ready
    except (EOFError, OSError, NsValidationError):
        raise _broker_unavailable("startup_failed") from None
    except BaseException:
        process.terminate()
        process.join(timeout=5.0)
        for parent in parents.values():
            parent.close()
        raise
    try:
        decoded: dict[str, tuple[dict[str, object], BrokerAuthorityHandle]] = {}
        for role, ready in ready_by_role.items():
            values = require_object(
                ready,
                fields={
                "version", "kind", "ok", "delegation_certificate",
                    "certificate", "endpoint_id", "role", "handle",
                    "identity_handles", "identity_endpoints",
                },
                field="ready",
            )
            if (
                values["version"] != WIRE_VERSION
                or values["kind"] != "ready"
                or values["role"] != role
            ):
                _invalid("ready.version")
            decoded[role] = (values, _decode_handle(values["handle"]))
        lifecycle_values = decoded[
            BrokerRepositoryRole.LIFECYCLE.value
        ][0]
        delegation_certificate = _decode_delegation_certificate(
            lifecycle_values["delegation_certificate"],
        )
        certificate = _decode_certificate(
            lifecycle_values["certificate"],
        )
        public_key = certificate.session_public_key
        instance_id = certificate.broker_instance_id
        raw_handles = lifecycle_values["identity_handles"]
        if type(raw_handles) is not dict:
            _invalid("ready.handles")
        handles = {
            key: _decode_handle(value)
            for key, value in raw_handles.items()
        }
        raw_endpoints = lifecycle_values["identity_endpoints"]
        if type(raw_endpoints) is not dict:
            _invalid("ready.endpoints")
        endpoints = {
            _exact_string(key, "ready.endpoint_role"):
                _exact_string(value, "ready.endpoint_id")
            for key, value in raw_endpoints.items()
        }
        for role, (values, handle) in decoded.items():
            if (
                values["delegation_certificate"]
                != lifecycle_values["delegation_certificate"]
                or values["certificate"] != lifecycle_values["certificate"]
                or values["endpoint_id"] != endpoints[role]
                or handle != handles[role]
            ):
                _invalid("ready.endpoint_binding")
        approved = attestor.approve_identity(
            realm=realm,
            runtime_id=config.runtime_id,
            delegation_certificate=_encode_delegation_certificate(
                delegation_certificate,
            ),
            session_certificate=_encode_certificate(certificate),
            handles={
                name: _encode_handle(handle)
                for name, handle in handles.items()
            },
            endpoints=endpoints,
        )
        identity_id = _exact_string(
            approved.get("identity_id"), "ready.identity_id",
        )
    except (
        NsValidationError, AuthorityAttestationError, TypeError, ValueError,
    ):
        process.terminate()
        process.join(timeout=5.0)
        for parent in parents.values():
            parent.close()
        raise _broker_unavailable("startup_handshake_invalid")
    channel_type = {
        "production": _ProductionRoleBrokerChannel,
        "contract-test": _ContractTestRoleBrokerChannel,
        "integration-test": _IntegrationTestRoleBrokerChannel,
    }[realm]
    custodian = _BrokerProcessCustodian(
        process=process,
        attestor=attestor,
        endpoint_close_resources=tuple(
            _ParentEndpointCloseResource(parents[role])
            for role in sorted(expected_roles)
        ),
    )
    channels = {
        BrokerRepositoryRole(role): channel_type(
            connection=parents[role],
            custodian=custodian,
            public_key=public_key,
            instance_id=instance_id,
            runtime_id=config.runtime_id,
            lifecycle_generation=certificate.lifecycle_generation,
            certificate=certificate,
            delegation_certificate=delegation_certificate,
            attestor=attestor,
            identity_id=identity_id,
            endpoint_id=endpoints[role],
            role=BrokerRepositoryRole(role),
            handle=handles[role],
            timeout_seconds=max(
                config.iam_timeout_seconds,
                config.state_operation_timeout_seconds,
            ) + 2.0,
        )
        for role in sorted(expected_roles)
    }
    if set(handles) != {role.value for role in BrokerRepositoryRole}:
        channels[BrokerRepositoryRole.LIFECYCLE].close(terminate=True)
        raise _broker_unavailable("startup_handle_invalid")

    iam_type = {
        "production": ProductionIamAuthorityProxy,
        "contract-test": ContractTestIamAuthorityProxy,
        "integration-test": IntegrationTestIamAuthorityProxy,
    }[realm]
    iam = object.__new__(iam_type)
    iam._channel = channels[BrokerRepositoryRole.IAM]
    iam._handle = handles[BrokerRepositoryRole.IAM.value]
    iam._clock = SystemClock()
    iam._iam_mode = config.iam_mode
    iam._authorization_service = None
    if realm == "production":
        composition_binding = object.__new__(
            _ProductionIamCompositionBinding,
        )
        for name, value in (
            ("channel", iam._channel),
            ("attestor_instance_id", attestor.instance_id),
            ("attestor_public_key", attestor.public_key),
            ("attestor_identity_id", identity_id),
            ("broker_instance_id", instance_id),
            ("runtime_id", config.runtime_id),
            ("endpoint_id", endpoints[BrokerRepositoryRole.IAM.value]),
        ):
            object.__setattr__(composition_binding, name, value)
        iam._composition_binding = composition_binding
    else:
        iam._composition_binding = None

    proxy_types = {
        "production": (
            AdmissionRepositoryProxy,
            SchedulerRepositoryProxy,
            PayloadRepositoryProxy,
            RegistryRepositoryProxy,
            AuditRepositoryProxy,
        ),
        "contract-test": (
            _ContractTestAdmissionRepositoryProxy,
            _ContractTestSchedulerRepositoryProxy,
            _ContractTestPayloadRepositoryProxy,
            _ContractTestRegistryRepositoryProxy,
            _ContractTestAuditRepositoryProxy,
        ),
        "integration-test": (
            _IntegrationTestAdmissionRepositoryProxy,
            _IntegrationTestSchedulerRepositoryProxy,
            _IntegrationTestPayloadRepositoryProxy,
            _IntegrationTestRegistryRepositoryProxy,
            _IntegrationTestAuditRepositoryProxy,
        ),
    }[realm]
    proxies: dict[BrokerRepositoryRole, _RepositoryProxy] = {}
    for role, proxy_type in zip((
        BrokerRepositoryRole.ADMISSION,
        BrokerRepositoryRole.SCHEDULER,
        BrokerRepositoryRole.PAYLOAD,
        BrokerRepositoryRole.REGISTRY,
        BrokerRepositoryRole.AUDIT,
    ), proxy_types):
        proxy = object.__new__(proxy_type)
        proxy._channel = channels[role]
        proxy._handle = handles[role.value]
        proxies[role] = proxy
    repositories = AuthorityBrokerRepositories(
        admission=proxies[BrokerRepositoryRole.ADMISSION],  # type: ignore[arg-type]
        scheduler=proxies[BrokerRepositoryRole.SCHEDULER],  # type: ignore[arg-type]
        payload=proxies[BrokerRepositoryRole.PAYLOAD],  # type: ignore[arg-type]
        registry=proxies[BrokerRepositoryRole.REGISTRY],  # type: ignore[arg-type]
        audit=proxies[BrokerRepositoryRole.AUDIT],  # type: ignore[arg-type]
    )
    state_store_type = {
        "production": AuthorityBrokerStateStoreProxy,
        "contract-test": _ContractTestAuthorityBrokerStateStoreProxy,
        "integration-test": _IntegrationTestAuthorityBrokerStateStoreProxy,
    }[realm]
    state_store = object.__new__(state_store_type)
    state_store._channel = channels[BrokerRepositoryRole.LIFECYCLE]
    state_store._handle = handles[BrokerRepositoryRole.LIFECYCLE.value]
    state_store._state = "new"

    broker_type = {
        "production": ProductionAuthorityBroker,
        "contract-test": ContractTestAuthorityBroker,
        "integration-test": IntegrationTestAuthorityBroker,
    }[realm]
    value = object.__new__(broker_type)
    value.iam = iam
    value.repositories = repositories
    value.state_store = state_store
    value.broker_instance_id = instance_id
    value._channel = channels[BrokerRepositoryRole.LIFECYCLE]
    return value


class _PhysicalDomainLease:
    __slots__ = ("file", "path")

    def __init__(self, *, file: object, path: str) -> None:
        self.file = file
        self.path = path

    def close(self) -> None:
        file = self.file
        self.file = None
        if file is None:
            return
        try:
            import portalocker

            portalocker.unlock(file)
            file.close()
        except (OSError, ValueError):
            pass


def _broker_password_source(
    password_buffer: bytearray | None,
) -> object:
    """Create a broker-local one-shot provider credential source."""

    _require_isolated_broker_process()
    from ns_common.state_store.redis_provider import StateStorePasswordSource

    class _OneShotPasswordSource(StateStorePasswordSource):
        __slots__ = ("_buffer", "_consumed")

        def __init__(self, value: bytearray | None) -> None:
            self._buffer = value
            self._consumed = False

        def resolve(self) -> str | None:
            if self._consumed:
                raise _state_unavailable("state_credential_already_consumed")
            self._consumed = True
            value = self._buffer
            self._buffer = None
            if value is None:
                return None
            try:
                return bytes(value).decode("utf-8")
            except UnicodeDecodeError:
                raise _state_unavailable(
                    "state_credential_invalid",
                ) from None
            finally:
                for index in range(len(value)):
                    value[index] = 0

    return _OneShotPasswordSource(password_buffer)


class _BrokerIamBackend:
    """Broker-private HTTP adapter with an exact fixed endpoint allowlist."""

    __slots__ = (
        "_client", "_credential", "_clock", "_iam_mode",
        "_ttl", "_backend_origin", "_path_prefix",
    )

    def __init__(
        self,
        config: AuthorityBrokerConfig,
        secrets: Mapping[str, object],
    ) -> None:
        _require_isolated_broker_process()
        from ns_common.http_client import NsAsyncHttpClient

        origin, prefix = _normalize_backend_url(config.iam_base_url)
        self._backend_origin = origin
        self._path_prefix = prefix
        self._client = NsAsyncHttpClient(
            name="runtime-iam-authority-broker",
            base_url=config.iam_base_url,
            timeout_seconds=config.iam_timeout_seconds,
            default_headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            verify=True,
        )
        credential = secrets["iam_service_credential"]
        if type(credential) is not str:
            _invalid("broker.iam_credential")
        self._credential = credential
        self._clock = SystemClock()
        self._iam_mode = config.iam_mode
        self._ttl = float(config.permission_snapshot_ttl_seconds)

    async def close(self) -> None:
        await self._client.aclose()

    async def execute(self, operation: str, payload: object) -> object:
        if operation == "introspect":
            return await self._introspect(payload)
        if operation == "runtime_access_check":
            if type(payload) is not IamAccessCheckRequest:
                _invalid("broker.access_request")
            data = await self._post(operation, payload.to_wire())
            return _parse_backend_result(IamAccessDecision.from_wire, data)
        if operation == "permission_snapshot":
            return await self._permission_snapshot(payload)
        if operation == "payload_validate":
            if type(payload) is not PayloadRefValidationRequest:
                _invalid("broker.payload_request")
            data = await self._post(operation, payload.to_wire())
            return _parse_backend_result(
                PayloadRefValidationResult.from_wire,
                data,
            )
        if operation == "payload_revalidate":
            if type(payload) is not PayloadRefRevalidationRequest:
                _invalid("broker.payload_request")
            data = await self._post(operation, payload.to_wire())
            return _parse_backend_result(
                PayloadRefRevalidationDecision.from_wire,
                data,
            )
        _invalid("broker.operation")

    async def _introspect(self, payload: object) -> HandshakeIamAuthority:
        if (
            type(payload) is not dict
            or set(payload) != {
                "token", "component_type", "requested_capabilities",
                "protocol_version",
            }
            or type(payload["token"]) is not str
            or type(payload["component_type"]) is not str
            or type(payload["requested_capabilities"]) is not list
            or any(
                type(value) is not str
                for value in payload["requested_capabilities"]
            )
            or type(payload["protocol_version"]) is not str
        ):
            _invalid("broker.introspection_request")
        contract = IamIntrospectionRequest(
            token=payload["token"],
            component_type=payload["component_type"],
            requested_capabilities=frozenset(
                payload["requested_capabilities"],
            ),
            protocol_version=payload["protocol_version"],
        )
        data = await self._post("introspect", contract.to_wire())
        if data.get("active") is not True:
            raise NsRuntimeIamDeniedError(details={
                "component": "authority_broker",
                "operation": "introspect",
                "reason": "credential_inactive",
            })
        result = _parse_backend_result(
            IamIntrospectionResult.from_wire,
            data.get("authority"),
        )
        now = self._clock.utc_now()
        if (
            result.credential_status is not IamCredentialStatus.ACTIVE
            or result.issued_at > now
            or result.expires_at <= now
            or result.component_type != payload["component_type"]
            or not result.capabilities.issubset(
                frozenset(payload["requested_capabilities"]),
            )
        ):
            raise NsRuntimeIamDeniedError(details={
                "component": "authority_broker",
                "operation": "introspect",
                "reason": "backend_authority_inconsistent",
            })
        return HandshakeIamAuthority(
            identity=result.identity,
            tenant_id=result.tenant_id,
            component_type=result.component_type,
            principal_type=result.principal_type,
            capabilities=result.capabilities,
            permissions={},
            permission_snapshot_ref=result.permission_snapshot_ref,
            permission_digest=result.permission_digest,
            permission_version=result.permission_version,
            issued_at=result.issued_at,
            expires_at=result.expires_at,
            resume_eligible=result.resume_eligible,
            iam_mode=self._iam_mode,
        )

    async def _permission_snapshot(self, payload: object) -> PermissionSnapshot:
        from ns_runtime.iam.models import PermissionSnapshot

        if (
            type(payload) is not dict
            or set(payload) != {
                "identity", "tenant_id", "permission_snapshot_ref",
                "permission_version", "component_type", "capabilities",
                "expires_at",
            }
        ):
            _invalid("broker.snapshot")
        data = await self._post("permission_snapshot", {
            "identity": payload["identity"],
            "tenant_id": payload["tenant_id"],
            "permission_snapshot_ref": payload["permission_snapshot_ref"],
            "known_version": payload["permission_version"],
            "component_type": payload["component_type"],
            "capabilities": payload["capabilities"],
            "expires_at": payload["expires_at"],
        })
        result = _parse_backend_result(IamIntrospectionResult.from_wire, data)
        return PermissionSnapshot.from_introspection(
            result,
            iam_mode=self._iam_mode,
        )

    async def _post(
        self,
        operation: str,
        payload: Mapping[str, object],
    ) -> dict[str, object]:
        from ns_common.exceptions import NsDependencyError

        path = _IAM_PATHS.get(operation)
        if path is None:
            _invalid("broker.iam_path")
        try:
            response = await self._client.post(
                path,
                json_data=dict(payload),
                bearer_token=self._credential,
                trace_id="op_" + uuid.uuid4().hex,
                expected_statuses={200},
            )
            body = response.json()
        except NsDependencyError as error:
            if "timeout_seconds" in error.details:
                raise NsRuntimeIamTimeoutError(details={
                    "component": "authority_broker",
                    "operation": operation,
                    "reason": "timeout",
                }) from None
            raise _broker_unavailable("backend_unavailable") from None
        if (
            not isinstance(body, Mapping)
            or set(body) != {
                "success", "code", "error", "message", "data", "request_id",
            }
            or body.get("success") is not True
            or not isinstance(body.get("data"), Mapping)
        ):
            raise _broker_unavailable("malformed_backend_response")
        return dict(body["data"])  # type: ignore[arg-type]


class _BrokerStateBackend:
    """Broker-private raw provider and fixed local repository set."""

    __slots__ = (
        "store", "repositories", "lease", "runtime_id", "available",
    )

    def __init__(
        self,
        config: AuthorityBrokerConfig,
        secrets: Mapping[str, object],
    ) -> None:
        _require_isolated_broker_process()
        self.store = None
        self.repositories = {}
        self.lease = None
        self.runtime_id = config.runtime_id
        self.available = config.state_backend in {"redis", "valkey"}
        if not self.available:
            return
        self.lease = _acquire_physical_domain_lease(config)
        try:
            self._create_provider(config, secrets)
        except BaseException:
            self.lease.close()
            self.lease = None
            raise

    def _create_provider(
        self,
        config: AuthorityBrokerConfig,
        secrets: Mapping[str, object],
    ) -> None:
        from ns_common.state_store import (
            StateAuthorityKind,
            StateCallerCapability,
            StateStoreCapabilities,
            StateStoreRepositoryRole,
        )
        from ns_common.state_store.redis_provider import (
            RedisStateStoreOptions,
            RedisValkeyStateStore,
        )
        from ns_common.state_store.store import _ProductionStateScopeValidator

        validator = object.__new__(_ProductionStateScopeValidator)
        validator._repository_specs = {}
        validator._scopes = {}
        validator._closed = False
        validator._realm = "production-broker"
        password_buffer = secrets["state_password_buffer"]
        if password_buffer is not None and type(password_buffer) is not bytearray:
            _invalid("broker.state_password")
        password_source = _broker_password_source(password_buffer)
        store = RedisValkeyStateStore(
            options=RedisStateStoreOptions(
                backend=config.state_backend,
                endpoint=config.state_endpoint,
                username=config.state_username,
                password_source=password_source,
                namespace=config.state_namespace,
                operation_timeout_seconds=float(
                    config.state_operation_timeout_seconds,
                ),
            ),
            capabilities=StateStoreCapabilities.p10_contract(),
            clock=SystemClock(),
            _production_scope_validator=validator,
        )
        specs = (
            (
                StateStoreRepositoryRole.DELIVERY_ADMISSION,
                config.runtime_id, None,
                StateAuthorityKind.DELIVERY_ADMISSION, "delivery.admission",
                frozenset({
                    StateCallerCapability.READ, StateCallerCapability.TRANSACT,
                    StateCallerCapability.ORDERED_INDEX,
                    StateCallerCapability.APPEND,
                }), "delivery-admission.v1",
            ),
            (
                StateStoreRepositoryRole.DELIVERY_SCHEDULER,
                config.runtime_id, None,
                StateAuthorityKind.DELIVERY_ADMISSION, "delivery.scheduling",
                frozenset({
                    StateCallerCapability.READ, StateCallerCapability.TRANSACT,
                    StateCallerCapability.ORDERED_INDEX,
                    StateCallerCapability.APPEND,
                }), "delivery-scheduler.v1",
            ),
            (
                StateStoreRepositoryRole.DELIVERY_PAYLOAD,
                config.runtime_id, None,
                StateAuthorityKind.DELIVERY_ADMISSION,
                "delivery.payload_authority",
                frozenset({StateCallerCapability.READ}),
                "delivery-payload.v1",
            ),
            (
                StateStoreRepositoryRole.DELIVERY_REGISTRY,
                config.runtime_id, None,
                StateAuthorityKind.DELIVERY_ADMISSION,
                "delivery.authority_registry",
                frozenset({
                    StateCallerCapability.READ, StateCallerCapability.TRANSACT,
                    StateCallerCapability.ORDERED_INDEX,
                }), "delivery-registry.v1",
            ),
            (
                StateStoreRepositoryRole.STRONG_AUDIT,
                None, StateNamespace.audit(domain="processor"),
                StateAuthorityKind.STRONG_AUDIT, "strong-audit-authority",
                frozenset({StateCallerCapability.APPEND}),
                "strong-audit.v1",
            ),
        )
        repositories = store._install_repositories(specs)
        self.store = store
        self.repositories = {
            "admission": repositories[0],
            "scheduler": repositories[1],
            "payload": repositories[2],
            "registry": repositories[3],
            "audit": repositories[4],
        }

    async def open(self) -> None:
        if self.store is not None:
            await self.store.open()

    async def close(self) -> None:
        try:
            if self.store is not None:
                await self.store.close()
        finally:
            if self.lease is not None:
                self.lease.close()
                self.lease = None

    async def execute(
        self,
        *,
        role: BrokerRepositoryRole,
        operation: str,
        payload: object,
    ) -> object:
        if operation == "state_health":
            if payload != {}:
                _invalid("broker.health_request")
            if self.store is None:
                from ns_common.state_store import (
                    StateStoreCapabilities,
                    StateStoreHealthStatus,
                )
                return StateStoreHealth(
                    status=StateStoreHealthStatus.READY,
                    checked_at=SystemClock().utc_now(),
                    contract_generation=(
                        StateStoreCapabilities.p10_contract().contract_generation
                    ),
                )
            return await self.store.health()
        if self.store is None:
            raise _state_unavailable("provider_unavailable")
        repository = self.repositories.get(role.value)
        if repository is None:
            raise _state_denied("repository_role_denied")
        if operation in {
            "read_delivery", "read_attempt", "read_summary",
            "read_payload_body", "read_admission_dedup",
            "read_admission_summary", "read_delivery_owner",
            "read_scheduler_cursor",
        }:
            tenant, bucket, generation, object_id = (
                _decode_delivery_request(payload)
            )
            object_type = {
                "read_delivery": "delivery",
                "read_attempt": "attempt",
                "read_summary": "summary",
                "read_payload_body": "payload_body",
                "read_admission_dedup": "dedup",
                "read_admission_summary": "summary",
                "read_delivery_owner": "delivery_owner",
                "read_scheduler_cursor": "delivery_scheduler_cursor",
            }[operation]
            scope = repository.delivery_scope(
                tenant_id=tenant,
                bucket_id=bucket,
                layout_generation=generation,
            )
            return await self.store.read(
                scope=scope,
                key=StateKey(
                    namespace=scope.namespace,
                    object_type=object_type,
                    object_id=object_id,
                ),
                consistency=StateConsistency.LINEARIZABLE,
            )
        if operation in {
            "transact_admission", "transact_scheduler",
            "transact_registry",
        }:
            tenant, bucket, generation = _decode_transaction_dimensions(
                payload,
            )
            if operation == "transact_registry":
                expected = _registry_partition(self.runtime_id)
                if (
                    tenant != expected.tenant_id
                    or bucket != expected.bucket_id
                    or generation != expected.layout_generation
                ):
                    raise _state_denied("registry_partition_denied")
                scope = repository.registry_scope()
            else:
                scope = repository.delivery_scope(
                    tenant_id=tenant,
                    bucket_id=bucket,
                    layout_generation=generation,
                )
            rebound = decode_transaction_request(
                payload,
                scope=scope,
                expected_tenant_id=tenant,
                expected_bucket_id=bucket,
                expected_layout_generation=generation,
            )
            return await self.store.transact(rebound)
        if operation == "read_scheduler_index":
            values = require_object(
                payload,
                fields={
                    "tenant_id", "bucket_id", "layout_generation",
                    "index_name", "cursor", "limit", "max_score",
                },
                field="broker.index_request",
            )
            tenant = _exact_string(
                values["tenant_id"], "broker.index_tenant",
            )
            bucket = _exact_int(
                values["bucket_id"], "broker.index_bucket", minimum=0,
            )
            generation = _exact_int(
                values["layout_generation"],
                "broker.index_generation",
                minimum=1,
            )
            name = _exact_string(
                values["index_name"], "broker.index_name",
            )
            limit = _exact_int(
                values["limit"], "broker.index_limit", minimum=1,
            )
            max_score = values["max_score"]
            if max_score is not None and (
                type(max_score) not in {int, float}
                or not math.isfinite(max_score)
            ):
                _invalid("broker.index_max_score")
            if name not in {
                "delivery.prepared", "delivery.ready", "delivery.claimed",
                "delivery.lease", "delivery.sending", "delivery.ack",
                "delivery.write_failed", "delivery.waiting",
                "delivery.expired", "delivery.payload_rejected",
                "delivery.write_uncertain", "delivery.scheduler_quarantine",
                "delivery.runtime.ready",
            }:
                raise _state_denied("index_denied")
            scope = repository.delivery_scope(
                tenant_id=tenant,
                bucket_id=bucket,
                layout_generation=generation,
            )
            decoded_cursor = decode_cursor(
                values["cursor"],
                index_name=name,
                index_bucket="delivery",
            )
            return await self.store.read_ordered_index(
                scope=scope,
                index=StateOrderedIndexKey(
                    namespace=scope.namespace,
                    name=name,
                    bucket="delivery",
                ),
                start_after=decoded_cursor,
                limit=limit,
                max_score=max_score,
            )
        if operation in {
            "read_registry_layout", "read_registry_tenant",
        }:
            values = require_object(
                payload,
                fields={"object_id"},
                field="broker.registry_request",
            )
            object_id = _exact_string(
                values["object_id"], "broker.registry_object_id",
            )
            scope = repository.registry_scope()
            return await self.store.read(
                scope=scope,
                key=StateKey(
                    namespace=scope.namespace,
                    object_type=(
                        "delivery_authority_layout"
                        if operation == "read_registry_layout"
                        else "delivery_tenant_registration"
                    ),
                    object_id=object_id,
                ),
                consistency=StateConsistency.LINEARIZABLE,
            )
        if operation == "read_registry_index":
            values = require_object(
                payload,
                fields={
                    "index_name", "index_bucket", "cursor", "limit",
                },
                field="broker.registry_index_request",
            )
            name = _exact_string(
                values["index_name"], "broker.registry_index_name",
            )
            bucket = _exact_string(
                values["index_bucket"], "broker.registry_index_bucket",
            )
            if name != "delivery.tenant_registry" or bucket != "runtime":
                raise _state_denied("registry_index_denied")
            limit = _exact_int(
                values["limit"], "broker.registry_index_limit", minimum=1,
            )
            scope = repository.registry_scope()
            return await self.store.read_ordered_index(
                scope=scope,
                index=StateOrderedIndexKey(
                    namespace=scope.namespace,
                    name=name,
                    bucket=bucket,
                ),
                start_after=decode_cursor(
                    values["cursor"],
                    index_name=name,
                    index_bucket=bucket,
                ),
                limit=limit,
            )
        if operation == "append_audit":
            values = require_object(
                payload,
                fields={"namespace", "object_id", "document"},
                field="broker.audit_request",
            )
            namespace_values = values["namespace"]
            if type(namespace_values) is not dict:
                raise _state_denied("audit_resource_denied")
            try:
                namespace = StateNamespace(
                    kind=StateNamespaceKind(
                        namespace_values["kind"],
                    ),
                    domain=namespace_values["domain"],
                    tenant_id=namespace_values["tenant_id"],
                    runtime_id=namespace_values["runtime_id"],
                    plugin_name=namespace_values["plugin_name"],
                )
                document = decode_document(values["document"])
                object_id = _exact_string(
                    values["object_id"], "broker.audit_object_id",
                )
            except (KeyError, ValueError, NsValidationError, TypeError):
                raise _state_denied("audit_resource_denied") from None
            if (
                namespace != StateNamespace.audit(domain="processor")
                or document.schema_name != "runtime.processor_audit"
            ):
                raise _state_denied("audit_resource_denied")
            scope = repository.audit_scope()
            return await self.store.append(
                scope=scope,
                key=StateKey(
                    namespace=scope.namespace,
                    object_type="processor_audit_log",
                    object_id=object_id,
                ),
                document=document,
            )
        raise _state_denied("repository_operation_denied")


def _new_session_authority(
    *,
    delegation_private_key: Ed25519PrivateKey,
    delegation_certificate: BrokerDelegationCertificate,
    realm: str,
    instance_id: str,
    runtime_id: str,
    generation: int,
    endpoints: Mapping[str, str],
    session_ttl_seconds: float,
) -> tuple[
    Ed25519PrivateKey,
    bytes,
    BrokerInstanceCertificate,
    dict[str, BrokerAuthorityHandle],
]:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    now = datetime.now(timezone.utc)
    expires_at = min(
        delegation_certificate.expires_at,
        now + timedelta(seconds=session_ttl_seconds),
    )
    values = {
        "trust_realm": realm,
        "broker_instance_id": instance_id,
        "session_public_key": encode_bytes(public_key),
        "runtime_id": runtime_id,
        "lifecycle_generation": generation,
        "delegation_fingerprint": delegation_certificate.fingerprint,
        "issued_at": encode_time(now),
        "expires_at": encode_time(expires_at),
        "nonce": uuid.uuid4().hex,
    }
    certificate = BrokerInstanceCertificate(
        trust_realm=realm,
        broker_instance_id=instance_id,
        session_public_key=public_key,
        runtime_id=runtime_id,
        lifecycle_generation=generation,
        delegation_fingerprint=delegation_certificate.fingerprint,
        issued_at=now,
        expires_at=expires_at,
        nonce=values["nonce"],
        signature=delegation_private_key.sign(_canonical(values)),
    )
    handles = {
        role.value: _new_handle(
            private_key=private_key,
            instance_id=instance_id,
            endpoint_id=endpoints[role.value],
            role=role,
            runtime_id=runtime_id,
            generation=generation,
        )
        for role in BrokerRepositoryRole
    }
    return private_key, public_key, certificate, handles


def _verify_attestor_ticket(
    ticket: object,
    *,
    delegation_certificate: BrokerDelegationCertificate,
    identity_id: str,
    instance_id: str,
    runtime_id: str,
    generation: int,
    session_public_key: bytes,
    endpoint_id: str,
    endpoint_role: BrokerRepositoryRole,
    handle: BrokerAuthorityHandle | None = None,
    operation: str | None = None,
    request_id: str | None = None,
    request_sequence: int | None = None,
    request_fingerprint: str | None = None,
) -> dict[str, object]:
    if type(ticket) is not dict or "signature" not in ticket:
        _invalid("attestor.ticket")
    signature = decode_bytes(
        ticket["signature"], field="attestor.ticket.signature",
    )
    values = {
        name: value
        for name, value in ticket.items()
        if name != "signature"
    }
    if not _verify(
        delegation_certificate.attestor_public_key,
        _canonical(values),
        signature,
    ):
        _invalid("attestor.ticket.signature")
    now = datetime.now(timezone.utc)
    if (
        values.get("attestor_instance_id")
        != delegation_certificate.attestor_instance_id
        or values.get("identity_id") != identity_id
        or values.get("broker_instance_id") != instance_id
        or values.get("runtime_id") != runtime_id
        or _parse_time(values.get("issued_at")) > now
        or _parse_time(values.get("expires_at")) <= now
    ):
        _invalid("attestor.ticket.binding")
    if handle is None:
        if (
            values.get("endpoint_id") != endpoint_id
            or values.get("role") != endpoint_role.value
            or values.get("current_generation") != generation
            or values.get("next_generation") != generation + 1
        ):
            _invalid("attestor.rotation_ticket")
        return values
    if (
        values.get("lifecycle_generation") != generation
        or values.get("session_key_fingerprint")
        != _session_key_fingerprint(session_public_key)
        or values.get("handle_id") != handle.handle_id
        or values.get("endpoint_id") != endpoint_id
        or values.get("role") != handle.role.value
        or handle.role is not endpoint_role
        or values.get("operation") != operation
        or values.get("request_id") != request_id
        or values.get("request_sequence") != request_sequence
        or values.get("request_fingerprint") != request_fingerprint
    ):
        _invalid("attestor.request_ticket")
    return values


async def _broker_async_main(
    connections: Mapping[str, Connection],
    config: AuthorityBrokerConfig,
    root_private_key: Ed25519PrivateKey,
    secrets: Mapping[str, object],
    realm: str,
    attestor_public_key: bytes,
    attestor_instance_id: str,
    session_ttl_seconds: float,
    delegation_ttl_seconds: float,
) -> None:
    expected_roles = {role.value for role in BrokerRepositoryRole}
    if set(connections) != expected_roles:
        _invalid("broker.endpoint_set")
    endpoints = {
        role: "endpoint_" + uuid.uuid4().hex
        for role in expected_roles
    }
    connection_roles = {
        id(connection): BrokerRepositoryRole(role)
        for role, connection in connections.items()
    }
    delegation_private_key = Ed25519PrivateKey.generate()
    delegation_public_key = delegation_private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    instance_id = "broker_" + uuid.uuid4().hex
    iam = _BrokerIamBackend(config, secrets)
    state = _BrokerStateBackend(config, secrets)
    iam_sequence = 0
    request_sequences = {role: 0 for role in expected_roles}
    response_sequences = {role: 0 for role in expected_roles}
    generation = 1
    now = datetime.now(timezone.utc)
    delegation_values = {
        "trust_realm": realm,
        "broker_instance_id": instance_id,
        "runtime_id": config.runtime_id,
        "delegation_public_key": encode_bytes(delegation_public_key),
        "attestor_instance_id": attestor_instance_id,
        "attestor_public_key": encode_bytes(attestor_public_key),
        "allowed_usages": list(_DELEGATION_USAGES),
        "issued_at": encode_time(now),
        "expires_at": encode_time(
            now + timedelta(seconds=delegation_ttl_seconds),
        ),
        "nonce": uuid.uuid4().hex,
    }
    delegation_certificate = BrokerDelegationCertificate(
        trust_realm=realm,
        broker_instance_id=instance_id,
        runtime_id=config.runtime_id,
        delegation_public_key=delegation_public_key,
        attestor_instance_id=attestor_instance_id,
        attestor_public_key=attestor_public_key,
        allowed_usages=_DELEGATION_USAGES,
        issued_at=now,
        expires_at=now + timedelta(seconds=delegation_ttl_seconds),
        nonce=delegation_values["nonce"],
        signature=root_private_key.sign(_canonical(delegation_values)),
    )
    del root_private_key
    (
        session_private_key,
        session_public_key,
        certificate,
        handles,
    ) = _new_session_authority(
        delegation_private_key=delegation_private_key,
        delegation_certificate=delegation_certificate,
        realm=realm,
        instance_id=instance_id,
        runtime_id=config.runtime_id,
        generation=generation,
        endpoints=endpoints,
        session_ttl_seconds=session_ttl_seconds,
    )
    identity_id = "identity:" + hashlib.sha256(_canonical({
        "delegation_fingerprint": delegation_certificate.fingerprint,
        "broker_instance_id": instance_id,
        "runtime_id": config.runtime_id,
    })).hexdigest()
    try:
        await state.open()
        encoded_handles = {
            role: _encode_handle(handle)
            for role, handle in handles.items()
        }
        for role, connection in connections.items():
            connection.send_bytes(encode_frame({
                "version": WIRE_VERSION,
                "kind": "ready",
                "ok": True,
                "delegation_certificate": _encode_delegation_certificate(
                    delegation_certificate,
                ),
                "certificate": _encode_certificate(certificate),
                "endpoint_id": endpoints[role],
                "role": role,
                "handle": encoded_handles[role],
                "identity_handles": encoded_handles,
                "identity_endpoints": endpoints,
            }))
        stop = False
        while not stop:
            try:
                ready_connections = await asyncio.to_thread(
                    wait_connections,
                    tuple(connections.values()),
                )
            except (OSError, ValueError):
                break
            for connection in ready_connections:
                endpoint_role = connection_roles.get(id(connection))
                if endpoint_role is None:
                    stop = True
                    break
                role_name = endpoint_role.value
                endpoint_id = endpoints[role_name]
                try:
                    message = decode_frame(
                        connection.recv_bytes(MAX_FRAME_BYTES),
                    )
                except (EOFError, OSError, NsValidationError):
                    stop = True
                    break
                if message == {
                    "version": WIRE_VERSION,
                    "kind": "shutdown",
                }:
                    if endpoint_role is not BrokerRepositoryRole.LIFECYCLE:
                        stop = True
                        break
                    connection.send_bytes(encode_frame({
                        "version": WIRE_VERSION,
                        "kind": "shutdown_complete",
                    }))
                    stop = True
                    break
                if (
                    type(message) is dict
                    and set(message) == {"version", "kind", "ticket"}
                    and message.get("version") == WIRE_VERSION
                    and message.get("kind") == "rotate_session"
                ):
                    ticket = _verify_attestor_ticket(
                        message["ticket"],
                        delegation_certificate=delegation_certificate,
                        identity_id=identity_id,
                        instance_id=instance_id,
                        runtime_id=config.runtime_id,
                        generation=generation,
                        session_public_key=session_public_key,
                        endpoint_id=endpoint_id,
                        endpoint_role=endpoint_role,
                    )
                    next_generation = generation + 1
                    (
                        next_private_key,
                        next_public_key,
                        next_certificate,
                        next_handles,
                    ) = _new_session_authority(
                        delegation_private_key=delegation_private_key,
                        delegation_certificate=delegation_certificate,
                        realm=realm,
                        instance_id=instance_id,
                        runtime_id=config.runtime_id,
                        generation=next_generation,
                        endpoints=endpoints,
                        session_ttl_seconds=session_ttl_seconds,
                    )
                    rotation_values = {
                        "kind": "session_rotation",
                        "ticket_nonce": ticket["nonce"],
                        "delegation_fingerprint": (
                            delegation_certificate.fingerprint
                        ),
                        "session_certificate": _encode_certificate(
                            next_certificate,
                        ),
                        "handles": {
                            role: _encode_handle(handle)
                            for role, handle in next_handles.items()
                        },
                    }
                    connection.send_bytes(encode_frame({
                        "version": WIRE_VERSION,
                        **rotation_values,
                        "signature": encode_bytes(
                            delegation_private_key.sign(
                                _canonical(rotation_values),
                            ),
                        ),
                    }))
                    session_private_key = next_private_key
                    session_public_key = next_public_key
                    certificate = next_certificate
                    handles = next_handles
                    generation = next_generation
                    request_sequences = {
                        role: 0 for role in expected_roles
                    }
                    response_sequences = {
                        role: 0 for role in expected_roles
                    }
                    iam_sequence = 0
                    continue
                if type(message) is not dict or set(message) != {
                    "version", "kind", "request_id", "request_sequence",
                    "operation", "payload", "attestation",
                }:
                    stop = True
                    break
                request_id = message["request_id"]
                incoming_request_sequence = message["request_sequence"]
                operation = message["operation"]
                if (
                    message["version"] != WIRE_VERSION
                    or message["kind"] != "request"
                    or type(request_id) is not str
                    or not request_id
                    or type(incoming_request_sequence) is not int
                    or incoming_request_sequence
                    != request_sequences[role_name] + 1
                    or type(operation) is not str
                ):
                    stop = True
                    break
                request_sequences[role_name] = incoming_request_sequence
                handle = handles[role_name]
                payload = message["payload"]
                request_fingerprint = _state_request_fingerprint(
                    operation=operation,
                    handle=handle,
                    payload=payload,
                )
                try:
                    _verify_attestor_ticket(
                        message["attestation"],
                        delegation_certificate=delegation_certificate,
                        identity_id=identity_id,
                        instance_id=instance_id,
                        runtime_id=config.runtime_id,
                        generation=generation,
                        session_public_key=session_public_key,
                        endpoint_id=endpoint_id,
                        endpoint_role=endpoint_role,
                        handle=handle,
                        operation=operation,
                        request_id=request_id,
                        request_sequence=incoming_request_sequence,
                        request_fingerprint=request_fingerprint,
                    )
                except NsValidationError:
                    stop = True
                    break
                if (
                    handle.endpoint_id != endpoint_id
                    or handle.role is not endpoint_role
                    or not handle.verify(
                        session_public_key,
                        instance_id=instance_id,
                    )
                    or handle.lifecycle_generation != generation
                    or not _role_allows(endpoint_role, operation)
                ):
                    response_sequences[role_name] += 1
                    connection.send_bytes(encode_frame(
                        _signed_response_envelope(_sign_state_response(
                            private_key=session_private_key,
                            certificate=certificate,
                            request_id=request_id,
                            request_sequence=incoming_request_sequence,
                            operation=operation,
                            handle=handle,
                            request_fingerprint=request_fingerprint,
                            response_sequence=response_sequences[role_name],
                            error=_error_values(
                                "state_denied", "endpoint_role_denied",
                            ),
                        )),
                    ))
                    continue
                try:
                    if endpoint_role is BrokerRepositoryRole.IAM:
                        typed_request = _decode_iam_request(
                            operation, payload,
                        )
                        typed_result = await iam.execute(
                            operation, typed_request,
                        )
                        iam_sequence += 1
                        result = _sign_iam_result(
                            private_key=session_private_key,
                            instance_id=instance_id,
                            lifecycle_generation=generation,
                            session_public_key=session_public_key,
                            operation=operation,
                            request=typed_request,
                            result=typed_result,
                            sequence=iam_sequence,
                            ttl_seconds=(
                                config.permission_snapshot_ttl_seconds
                            ),
                            certificate_expires_at=certificate.expires_at,
                        )
                        wire_result = _encode_signed_iam_result(result)
                    else:
                        result = await state.execute(
                            role=endpoint_role,
                            operation=operation,
                            payload=payload,
                        )
                        wire_result = _encode_state_response(
                            operation, result, payload,
                        )
                except BaseException as error:
                    if not isinstance(error, Exception):
                        raise
                    response_sequences[role_name] += 1
                    signed_response = _sign_state_response(
                        private_key=session_private_key,
                        certificate=certificate,
                        request_id=request_id,
                        request_sequence=incoming_request_sequence,
                        operation=operation,
                        handle=handle,
                        request_fingerprint=request_fingerprint,
                        response_sequence=response_sequences[role_name],
                        error=_exception_values(error),
                    )
                else:
                    response_sequences[role_name] += 1
                    signed_response = _sign_state_response(
                        private_key=session_private_key,
                        certificate=certificate,
                        request_id=request_id,
                        request_sequence=incoming_request_sequence,
                        operation=operation,
                        handle=handle,
                        request_fingerprint=request_fingerprint,
                        response_sequence=response_sequences[role_name],
                        result=wire_result,
                    )
                connection.send_bytes(encode_frame(
                    _signed_response_envelope(signed_response),
                ))
    finally:
        try:
            await state.close()
        finally:
            await iam.close()
            for connection in connections.values():
                try:
                    connection.close()
                except OSError:
                    pass


def _authority_broker_process(
    connections: Mapping[str, Connection],
    config_raw: bytes | None,
    root_key_handle: object,
    secrets_handle: object,
    realm: str,
    expected_root_public_key: bytes,
    attestor_public_key: bytes,
    attestor_instance_id: str,
    session_ttl_seconds: float,
    delegation_ttl_seconds: float,
) -> None:
    """Top-level spawn target; descriptors are consumed before backends load."""

    try:
        _require_isolated_broker_process()
        if set(connections) != {
            role.value for role in BrokerRepositoryRole
        }:
            _invalid("broker.endpoint_set")
        lifecycle = connections[BrokerRepositoryRole.LIFECYCLE.value]
        if realm not in _BROKER_REALMS:
            _invalid("broker.realm")
        if (
            type(attestor_public_key) is not bytes
            or len(attestor_public_key) != 32
            or type(attestor_instance_id) is not str
            or not attestor_instance_id
            or type(session_ttl_seconds) not in {int, float}
            or not math.isfinite(session_ttl_seconds)
            or session_ttl_seconds <= 0
            or type(delegation_ttl_seconds) not in {int, float}
            or not math.isfinite(delegation_ttl_seconds)
            or delegation_ttl_seconds <= session_ttl_seconds
        ):
            _invalid("broker.attestor_binding")
        root_fd = root_key_handle.detach()
        secret_fd = secrets_handle.detach()
        try:
            root_private_bytes = _read_fd_once(root_fd, maximum=64)
            secrets_raw = _read_fd_once(
                secret_fd,
                maximum=MAX_FRAME_BYTES,
            )
        finally:
            os.close(root_fd)
            os.close(secret_fd)
        if len(root_private_bytes) != 32:
            _invalid("broker.root_private_key")
        root_private_key = Ed25519PrivateKey.from_private_bytes(
            root_private_bytes,
        )
        root_private_bytes = b"\0" * len(root_private_bytes)
        if config_raw is None:
            lifecycle.send_bytes(encode_frame({
                "version": WIRE_VERSION,
                "kind": "fd_custody",
            }))
            bootstrap_message = require_object(
                decode_frame(lifecycle.recv_bytes(MAX_FRAME_BYTES)),
                fields={"version", "kind", "config"},
                field="broker.bootstrap_config",
            )
            if (
                bootstrap_message["version"] != WIRE_VERSION
                or bootstrap_message["kind"] != "bootstrap_config"
            ):
                _invalid("broker.bootstrap_config")
            config_value = bootstrap_message["config"]
        else:
            config_value = decode_frame(config_raw)
        actual_root_public_key = root_private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        # For production the spawn child reloads this module and uses its own
        # build-time trust root.  The parent-supplied value is intentionally
        # ignored so monkey-patching the ordinary runtime interpreter cannot
        # authorize an attacker root.  Test realms use their explicit root.
        authoritative_root = (
            _PRODUCTION_ROOT_PUBLIC_KEY
            if realm == "production"
            else expected_root_public_key
        )
        if (
            type(authoritative_root) is not bytes
            or len(authoritative_root) != 32
            or actual_root_public_key != authoritative_root
        ):
            _invalid("broker.root_trust")
        config = _decode_broker_config(config_value)
        secrets = _decode_broker_secrets(decode_frame(secrets_raw))
        secrets_raw = b"\0" * len(secrets_raw)
        asyncio.run(_broker_async_main(
            connections,
            config,
            root_private_key,
            secrets,
            realm,
            attestor_public_key,
            attestor_instance_id,
            float(session_ttl_seconds),
            float(delegation_ttl_seconds),
        ))
    except BaseException as error:
        try:
            reason = (
                error.details.get("reason", type(error).__name__)
                if isinstance(
                    error,
                    NsRuntimeStateStoreCapabilityUnavailableError,
                )
                else type(error).__name__
            )
            for connection in connections.values():
                connection.send_bytes(encode_frame({
                    "version": WIRE_VERSION,
                    "kind": "ready_error",
                    "ok": False,
                    "reason": str(reason),
                }))
        except (BrokenPipeError, EOFError, OSError):
            pass
        finally:
            try:
                for connection in connections.values():
                    connection.close()
            except OSError:
                pass


def _new_handle(
    *,
    private_key: Ed25519PrivateKey,
    instance_id: str,
    endpoint_id: str,
    role: BrokerRepositoryRole,
    runtime_id: str,
    generation: int,
) -> BrokerAuthorityHandle:
    values = {
        "broker_instance_id": instance_id,
        "endpoint_id": endpoint_id,
        "handle_id": "handle_" + uuid.uuid4().hex,
        "role": role.value,
        "runtime_id": runtime_id,
        "lifecycle_generation": generation,
    }
    return BrokerAuthorityHandle(
        broker_instance_id=instance_id,
        endpoint_id=endpoint_id,
        handle_id=values["handle_id"],
        role=role,
        runtime_id=runtime_id,
        lifecycle_generation=generation,
        signature=private_key.sign(_canonical(values)),
    )


def _sign_iam_result(
    *,
    private_key: Ed25519PrivateKey,
    instance_id: str,
    lifecycle_generation: int,
    session_public_key: bytes,
    operation: str,
    request: object,
    result: object,
    sequence: int,
    ttl_seconds: float,
    certificate_expires_at: datetime | None = None,
) -> BrokerSignedIamResult:
    now = datetime.now(timezone.utc)
    result_values = _encode_iam_result(operation, result)
    request_values = _request_claims(operation, request)
    result_expiry = _result_expiry(result)
    expires_at = min(
        result_expiry,
        now + timedelta(seconds=float(ttl_seconds)),
        (
            certificate_expires_at
            if certificate_expires_at is not None
            else result_expiry
        ),
    )
    values = {
        "broker_instance_id": instance_id,
        "lifecycle_generation": lifecycle_generation,
        "session_key_fingerprint": _session_key_fingerprint(
            session_public_key,
        ),
        "operation": operation,
        "request_fingerprint": _request_fingerprint(operation, request),
        "request_json": json.dumps(
            request_values, sort_keys=True, separators=(",", ":"),
        ),
        "result_json": json.dumps(
            result_values, sort_keys=True, separators=(",", ":"),
        ),
        "backend_decision": _backend_decision(result),
        "permission_snapshot_ref": _result_value(
            result, "permission_snapshot_ref",
            _result_value(request, "permission_snapshot_ref", ""),
        ),
        "permission_version": _result_value(
            result, "permission_version",
            _result_value(request, "permission_version", ""),
        ),
        "tenant_id": str(request_values.get("tenant_id", "")),
        "target": str(request_values.get(
            "target",
            request_values.get("target_fingerprint", ""),
        )),
        "message_type": str(request_values.get(
            "message_type",
            operation,
        )),
        "issued_at": _iso(now),
        "expires_at": _iso(expires_at),
        "sequence": sequence,
        "nonce": uuid.uuid4().hex,
    }
    signature = private_key.sign(_canonical(values))
    return BrokerSignedIamResult(
        broker_instance_id=instance_id,
        lifecycle_generation=lifecycle_generation,
        session_key_fingerprint=values["session_key_fingerprint"],
        operation=operation,
        request_fingerprint=values["request_fingerprint"],
        request_json=values["request_json"],
        result_json=values["result_json"],
        backend_decision=values["backend_decision"],
        permission_snapshot_ref=values["permission_snapshot_ref"],
        permission_version=values["permission_version"],
        tenant_id=values["tenant_id"],
        target=values["target"],
        message_type=values["message_type"],
        issued_at=now,
        expires_at=expires_at,
        sequence=sequence,
        nonce=values["nonce"],
        signature=signature,
    )


def _encode_iam_result(operation: str, result: object) -> dict[str, object]:
    from ns_runtime.iam.models import PermissionSnapshot

    if operation == "introspect" and type(result) is HandshakeIamAuthority:
        return {
            "identity": result.identity,
            "tenant_id": result.tenant_id,
            "component_type": result.component_type,
            "principal_type": result.principal_type.value,
            "capabilities": sorted(result.capabilities),
            "permissions": dict(result.permissions),
            "permission_snapshot_ref": result.permission_snapshot_ref,
            "permission_digest": result.permission_digest,
            "permission_version": result.permission_version,
            "issued_at": _iso(result.issued_at),
            "expires_at": _iso(result.expires_at),
            "resume_eligible": result.resume_eligible,
            "iam_mode": result.iam_mode,
        }
    if operation == "permission_snapshot" and type(result) is PermissionSnapshot:
        return {
            "identity": result.identity,
            "tenant_id": result.tenant_id,
            "principal_type": result.principal_type.value,
            "component_type": result.component_type,
            "capabilities": sorted(result.capabilities),
            "permission_snapshot_ref": result.permission_snapshot_ref,
            "permission_digest": result.permission_digest,
            "permission_version": result.permission_version,
            "iam_mode": result.iam_mode,
            "issued_at": _iso(result.issued_at),
            "expires_at": _iso(result.expires_at),
            "resume_eligible": result.resume_eligible,
        }
    if (
        operation == "runtime_access_check"
        and type(result) is IamAccessDecision
    ) or (
        operation == "payload_validate"
        and type(result) is PayloadRefValidationResult
    ) or (
        operation == "payload_revalidate"
        and type(result) is PayloadRefRevalidationDecision
    ):
        return result.to_wire()
    _invalid("broker.result")


def _decode_iam_result(operation: str, values: Mapping[str, object]) -> object:
    from ns_runtime.iam.models import PermissionSnapshot

    if operation == "runtime_access_check":
        return IamAccessDecision.from_wire(values)
    if operation == "payload_validate":
        return PayloadRefValidationResult.from_wire(values)
    if operation == "payload_revalidate":
        return PayloadRefRevalidationDecision.from_wire(values)
    if operation == "introspect":
        from ns_common.iam import IamPrincipalType

        return HandshakeIamAuthority(
            identity=values["identity"],  # type: ignore[arg-type]
            tenant_id=values["tenant_id"],  # type: ignore[arg-type]
            component_type=values["component_type"],  # type: ignore[arg-type]
            principal_type=IamPrincipalType(values["principal_type"]),
            capabilities=frozenset(values["capabilities"]),  # type: ignore[arg-type]
            permissions=values["permissions"],  # type: ignore[arg-type]
            permission_snapshot_ref=values["permission_snapshot_ref"],  # type: ignore[arg-type]
            permission_digest=values["permission_digest"],  # type: ignore[arg-type]
            permission_version=values["permission_version"],  # type: ignore[arg-type]
            issued_at=_parse_time(values["issued_at"]),
            expires_at=_parse_time(values["expires_at"]),
            resume_eligible=values["resume_eligible"],  # type: ignore[arg-type]
            iam_mode=values["iam_mode"],  # type: ignore[arg-type]
        )
    if operation == "permission_snapshot":
        from ns_common.iam import IamPrincipalType

        return PermissionSnapshot(
            identity=values["identity"],  # type: ignore[arg-type]
            tenant_id=values["tenant_id"],  # type: ignore[arg-type]
            principal_type=IamPrincipalType(values["principal_type"]),
            component_type=values["component_type"],  # type: ignore[arg-type]
            capabilities=frozenset(values["capabilities"]),  # type: ignore[arg-type]
            permission_snapshot_ref=values["permission_snapshot_ref"],  # type: ignore[arg-type]
            permission_digest=values["permission_digest"],  # type: ignore[arg-type]
            permission_version=values["permission_version"],  # type: ignore[arg-type]
            iam_mode=values["iam_mode"],  # type: ignore[arg-type]
            issued_at=_parse_time(values["issued_at"]),
            expires_at=_parse_time(values["expires_at"]),
            resume_eligible=values["resume_eligible"],  # type: ignore[arg-type]
        )
    _invalid("broker.operation")


def _request_fingerprint(operation: str, request: object) -> str:
    return _claims_fingerprint(
        operation,
        _request_claims(operation, request),
    )


def _claims_fingerprint(
    operation: str,
    claims: Mapping[str, object],
) -> str:
    return "sha256:" + hashlib.sha256(
        _canonical({
            "operation": operation,
            "request": claims,
        }),
    ).hexdigest()


def broker_request_fingerprint(operation: str, request: object) -> str:
    """Return the public content binding used to verify a broker signature."""

    return _request_fingerprint(operation, request)


def _request_claims(operation: str, request: object) -> Mapping[str, object]:
    from ns_runtime.iam.models import PermissionSnapshot

    if operation == "introspect":
        if type(request) is not dict:
            _invalid("broker.introspection_request")
        if set(request) == {"token", "claims"}:
            claims = request["claims"]
            component_type = claims.component_type
            requested_capabilities = sorted(
                claims.requested_capabilities,
            )
            protocol_version = str(claims.requested_version)
        elif set(request) == {
            "token", "component_type", "requested_capabilities",
            "protocol_version",
        }:
            component_type = request["component_type"]
            requested_capabilities = request["requested_capabilities"]
            protocol_version = request["protocol_version"]
        else:
            _invalid("broker.introspection_request")
        return {
            "token_fingerprint": "sha256:" + hashlib.sha256(
                request["token"].encode(),
            ).hexdigest(),
            "component_type": component_type,
            "requested_capabilities": requested_capabilities,
            "protocol_version": protocol_version,
        }
    if operation == "permission_snapshot":
        if type(request) is PermissionSnapshot:
            return {
                "identity": request.identity,
                "tenant_id": request.tenant_id,
                "permission_snapshot_ref": request.permission_snapshot_ref,
                "permission_version": request.permission_version,
                "component_type": request.component_type,
                "capabilities": sorted(request.capabilities),
                "expires_at": _iso(request.expires_at),
            }
        if type(request) is not dict:
            _invalid("broker.snapshot")
        return request
    if operation in {
        "runtime_access_check", "payload_validate", "payload_revalidate",
    }:
        values = request.to_wire()
        if operation == "runtime_access_check":
            target = values.get("target")
            values = {
                **values,
                "target": json.dumps(
                    target, sort_keys=True, separators=(",", ":"),
                ),
            }
        return values
    _invalid("broker.operation")


def _result_expiry(result: object) -> datetime:
    value = getattr(result, "expires_at", None)
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    return datetime.now(timezone.utc) + timedelta(seconds=60)


def _backend_decision(result: object) -> str:
    from ns_runtime.iam.models import PermissionSnapshot

    for name in ("allowed", "valid"):
        value = getattr(result, name, None)
        if type(value) is bool:
            return "allow" if value else "deny"
    if type(result) is HandshakeIamAuthority:
        return "active"
    if type(result) is PermissionSnapshot:
        return "snapshot"
    return "unknown"


def _result_value(result: object, name: str, default: object) -> str:
    value = getattr(result, name, default)
    return value if type(value) is str else str(default)


def _role_allows(role: BrokerRepositoryRole, operation: str) -> bool:
    if role is BrokerRepositoryRole.IAM:
        return operation in _IAM_OPERATIONS
    return operation in _ROLE_OPERATIONS.get(role.value, frozenset())


def _repository_proxy_binding(
    proxy_type: type[object],
) -> tuple[BrokerRepositoryRole, type[_RoleBrokerChannel]] | None:
    values: dict[
        type[object],
        tuple[BrokerRepositoryRole, type[_RoleBrokerChannel]],
    ] = {}
    for channel_type, proxy_types in (
        (
            _ProductionRoleBrokerChannel,
            (
                AdmissionRepositoryProxy,
                SchedulerRepositoryProxy,
                PayloadRepositoryProxy,
                RegistryRepositoryProxy,
                AuditRepositoryProxy,
            ),
        ),
        (
            _ContractTestRoleBrokerChannel,
            (
                _ContractTestAdmissionRepositoryProxy,
                _ContractTestSchedulerRepositoryProxy,
                _ContractTestPayloadRepositoryProxy,
                _ContractTestRegistryRepositoryProxy,
                _ContractTestAuditRepositoryProxy,
            ),
        ),
        (
            _IntegrationTestRoleBrokerChannel,
            (
                _IntegrationTestAdmissionRepositoryProxy,
                _IntegrationTestSchedulerRepositoryProxy,
                _IntegrationTestPayloadRepositoryProxy,
                _IntegrationTestRegistryRepositoryProxy,
                _IntegrationTestAuditRepositoryProxy,
            ),
        ),
    ):
        for role, concrete_type in zip((
            BrokerRepositoryRole.ADMISSION,
            BrokerRepositoryRole.SCHEDULER,
            BrokerRepositoryRole.PAYLOAD,
            BrokerRepositoryRole.REGISTRY,
            BrokerRepositoryRole.AUDIT,
        ), proxy_types):
            values[concrete_type] = (role, channel_type)
    return values.get(proxy_type)


def _encode_broker_config(
    config: AuthorityBrokerConfig,
) -> dict[str, object]:
    return {
        "iam_base_url": config.iam_base_url,
        "iam_timeout_seconds": float(config.iam_timeout_seconds),
        "iam_mode": config.iam_mode,
        "permission_snapshot_ttl_seconds": float(
            config.permission_snapshot_ttl_seconds,
        ),
        "state_backend": config.state_backend,
        "state_endpoint": config.state_endpoint,
        "state_username": config.state_username,
        "state_namespace": config.state_namespace,
        "state_operation_timeout_seconds": float(
            config.state_operation_timeout_seconds,
        ),
        "runtime_id": config.runtime_id,
    }


def _decode_broker_config(value: object) -> AuthorityBrokerConfig:
    fields = require_object(
        value,
        fields={
            "iam_base_url", "iam_timeout_seconds", "iam_mode",
            "permission_snapshot_ttl_seconds", "state_backend",
            "state_endpoint", "state_username", "state_namespace",
            "state_operation_timeout_seconds", "runtime_id",
        },
        field="broker.config",
    )
    return AuthorityBrokerConfig(
        iam_base_url=_exact_string(
            fields["iam_base_url"], "config.iam_base_url",
        ),
        iam_timeout_seconds=_exact_number(
            fields["iam_timeout_seconds"], "config.iam_timeout_seconds",
        ),
        iam_mode=_exact_string(fields["iam_mode"], "config.iam_mode"),
        permission_snapshot_ttl_seconds=_exact_number(
            fields["permission_snapshot_ttl_seconds"],
            "config.permission_snapshot_ttl_seconds",
        ),
        state_backend=_exact_string(
            fields["state_backend"], "config.state_backend",
        ),
        state_endpoint=_exact_optional_string(
            fields["state_endpoint"], "config.state_endpoint",
        ),
        state_username=_exact_optional_string(
            fields["state_username"], "config.state_username",
        ),
        state_namespace=_exact_string(
            fields["state_namespace"], "config.state_namespace",
        ),
        state_operation_timeout_seconds=_exact_number(
            fields["state_operation_timeout_seconds"],
            "config.state_operation_timeout_seconds",
        ),
        runtime_id=_exact_string(
            fields["runtime_id"], "config.runtime_id",
        ),
    )


def _decode_broker_secrets(value: object) -> dict[str, object]:
    fields = require_object(
        value,
        fields={"iam_service_credential", "state_password_base64"},
        field="broker.secrets",
    )
    credential = _exact_string(
        fields["iam_service_credential"],
        "secrets.iam_service_credential",
    )
    raw_password = fields["state_password_base64"]
    if raw_password is None:
        password_buffer = None
    else:
        password_buffer = bytearray(decode_bytes(
            raw_password,
            field="secrets.state_password_base64",
        ))
        if not password_buffer:
            _invalid("secrets.state_password_base64")
    return {
        "iam_service_credential": credential,
        "state_password_buffer": password_buffer,
    }


def _encode_certificate(
    value: BrokerInstanceCertificate,
) -> dict[str, object]:
    return {
        **value.signed_values(),
        "signature": encode_bytes(value.signature),
    }


def _decode_certificate(value: object) -> BrokerInstanceCertificate:
    fields = require_object(
        value,
        fields={
            "trust_realm", "broker_instance_id", "session_public_key",
            "runtime_id", "lifecycle_generation",
            "delegation_fingerprint", "issued_at", "expires_at", "nonce",
            "signature",
        },
        field="certificate",
    )
    return BrokerInstanceCertificate(
        trust_realm=_exact_string(
            fields["trust_realm"], "certificate.trust_realm",
        ),
        broker_instance_id=_exact_string(
            fields["broker_instance_id"],
            "certificate.broker_instance_id",
        ),
        session_public_key=decode_bytes(
            fields["session_public_key"],
            field="certificate.session_public_key",
        ),
        runtime_id=_exact_string(
            fields["runtime_id"], "certificate.runtime_id",
        ),
        lifecycle_generation=_exact_int(
            fields["lifecycle_generation"],
            "certificate.lifecycle_generation",
            minimum=1,
        ),
        delegation_fingerprint=_exact_string(
            fields["delegation_fingerprint"],
            "certificate.delegation_fingerprint",
        ),
        issued_at=decode_time(
            fields["issued_at"], field="certificate.issued_at",
        ),
        expires_at=decode_time(
            fields["expires_at"], field="certificate.expires_at",
        ),
        nonce=_exact_string(fields["nonce"], "certificate.nonce"),
        signature=decode_bytes(
            fields["signature"], field="certificate.signature",
        ),
    )


def _encode_delegation_certificate(
    value: BrokerDelegationCertificate,
) -> dict[str, object]:
    if type(value) is not BrokerDelegationCertificate:
        _invalid("delegation_certificate")
    return {
        **value.signed_values(),
        "signature": encode_bytes(value.signature),
    }


def _decode_delegation_certificate(
    value: object,
) -> BrokerDelegationCertificate:
    fields = require_object(
        value,
        fields={
            "trust_realm", "broker_instance_id", "runtime_id",
            "delegation_public_key", "attestor_instance_id",
            "attestor_public_key", "allowed_usages", "issued_at",
            "expires_at", "nonce", "signature",
        },
        field="delegation_certificate",
    )
    usages = fields["allowed_usages"]
    if (
        type(usages) is not list
        or any(type(item) is not str for item in usages)
    ):
        _invalid("delegation_certificate.allowed_usages")
    return BrokerDelegationCertificate(
        trust_realm=_exact_string(
            fields["trust_realm"],
            "delegation_certificate.trust_realm",
        ),
        broker_instance_id=_exact_string(
            fields["broker_instance_id"],
            "delegation_certificate.broker_instance_id",
        ),
        runtime_id=_exact_string(
            fields["runtime_id"],
            "delegation_certificate.runtime_id",
        ),
        delegation_public_key=decode_bytes(
            fields["delegation_public_key"],
            field="delegation_certificate.delegation_public_key",
        ),
        attestor_instance_id=_exact_string(
            fields["attestor_instance_id"],
            "delegation_certificate.attestor_instance_id",
        ),
        attestor_public_key=decode_bytes(
            fields["attestor_public_key"],
            field="delegation_certificate.attestor_public_key",
        ),
        allowed_usages=tuple(usages),
        issued_at=decode_time(
            fields["issued_at"],
            field="delegation_certificate.issued_at",
        ),
        expires_at=decode_time(
            fields["expires_at"],
            field="delegation_certificate.expires_at",
        ),
        nonce=_exact_string(
            fields["nonce"], "delegation_certificate.nonce",
        ),
        signature=decode_bytes(
            fields["signature"],
            field="delegation_certificate.signature",
        ),
    )


def _certificate_fingerprint(
    value: BrokerInstanceCertificate,
) -> str:
    return "sha256:" + hashlib.sha256(
        encode_frame(_encode_certificate(value)),
    ).hexdigest()


def _encode_handle(value: BrokerAuthorityHandle) -> dict[str, object]:
    return {
        **value.signed_values(),
        "signature": encode_bytes(value.signature),
    }


def _decode_handle(value: object) -> BrokerAuthorityHandle:
    fields = require_object(
        value,
        fields={
            "broker_instance_id", "endpoint_id", "handle_id", "role", "runtime_id",
            "lifecycle_generation", "signature",
        },
        field="handle",
    )
    try:
        role = BrokerRepositoryRole(
            _exact_string(fields["role"], "handle.role"),
        )
    except ValueError:
        _invalid("handle.role")
    return BrokerAuthorityHandle(
        broker_instance_id=_exact_string(
            fields["broker_instance_id"], "handle.broker_instance_id",
        ),
        endpoint_id=_exact_string(
            fields["endpoint_id"], "handle.endpoint_id",
        ),
        handle_id=_exact_string(fields["handle_id"], "handle.handle_id"),
        role=role,
        runtime_id=_exact_string(
            fields["runtime_id"], "handle.runtime_id",
        ),
        lifecycle_generation=_exact_int(
            fields["lifecycle_generation"],
            "handle.lifecycle_generation",
            minimum=1,
        ),
        signature=decode_bytes(
            fields["signature"], field="handle.signature",
        ),
    )


def _encode_signed_iam_result(
    value: BrokerSignedIamResult,
) -> dict[str, object]:
    return {
        **value.signed_values(),
        "signature": encode_bytes(value.signature),
    }


def _decode_signed_iam_result(value: object) -> BrokerSignedIamResult:
    fields = require_object(
        value,
        fields={
            "broker_instance_id", "lifecycle_generation",
            "session_key_fingerprint", "operation",
            "request_fingerprint", "request_json", "result_json",
            "backend_decision",
            "permission_snapshot_ref", "permission_version", "tenant_id",
            "target", "message_type", "issued_at", "expires_at",
            "sequence", "nonce", "signature",
        },
        field="signed_result",
    )
    return BrokerSignedIamResult(
        broker_instance_id=_exact_string(
            fields["broker_instance_id"],
            "signed_result.broker_instance_id",
        ),
        lifecycle_generation=_exact_int(
            fields["lifecycle_generation"],
            "signed_result.lifecycle_generation",
            minimum=1,
        ),
        session_key_fingerprint=_exact_string(
            fields["session_key_fingerprint"],
            "signed_result.session_key_fingerprint",
        ),
        operation=_exact_string(
            fields["operation"], "signed_result.operation",
        ),
        request_fingerprint=_exact_string(
            fields["request_fingerprint"],
            "signed_result.request_fingerprint",
        ),
        request_json=_exact_string(
            fields["request_json"], "signed_result.request_json",
        ),
        result_json=_exact_string(
            fields["result_json"], "signed_result.result_json",
        ),
        backend_decision=_exact_string(
            fields["backend_decision"],
            "signed_result.backend_decision",
        ),
        permission_snapshot_ref=_exact_optional_string(
            fields["permission_snapshot_ref"],
            "signed_result.permission_snapshot_ref",
        ),
        permission_version=_exact_optional_string(
            fields["permission_version"],
            "signed_result.permission_version",
        ),
        tenant_id=_exact_optional_string(
            fields["tenant_id"], "signed_result.tenant_id",
        ),
        target=_exact_optional_string(
            fields["target"], "signed_result.target",
        ),
        message_type=_exact_string(
            fields["message_type"], "signed_result.message_type",
        ),
        issued_at=decode_time(
            fields["issued_at"], field="signed_result.issued_at",
        ),
        expires_at=decode_time(
            fields["expires_at"], field="signed_result.expires_at",
        ),
        sequence=_exact_int(
            fields["sequence"], "signed_result.sequence", minimum=1,
        ),
        nonce=_exact_string(fields["nonce"], "signed_result.nonce"),
        signature=decode_bytes(
            fields["signature"], field="signed_result.signature",
        ),
    )


def _encode_iam_request(operation: str, request: object) -> object:
    from ns_runtime.iam.models import PermissionSnapshot

    if operation == "introspect":
        if type(request) is not dict or set(request) != {"token", "claims"}:
            _invalid("iam_request.introspect")
        claims = request["claims"]
        return {
            "token": request["token"],
            "component_type": claims.component_type,
            "requested_capabilities": sorted(
                claims.requested_capabilities,
            ),
            "protocol_version": str(claims.requested_version),
        }
    if operation == "permission_snapshot":
        if type(request) is not PermissionSnapshot:
            _invalid("iam_request.snapshot")
        return {
            "identity": request.identity,
            "tenant_id": request.tenant_id,
            "permission_snapshot_ref": request.permission_snapshot_ref,
            "permission_version": request.permission_version,
            "component_type": request.component_type,
            "capabilities": sorted(request.capabilities),
            "expires_at": encode_time(request.expires_at),
        }
    if operation in {
        "runtime_access_check", "payload_validate", "payload_revalidate",
    }:
        values = request.to_wire()
        encode_frame(values)
        return values
    _invalid("iam_request.operation")


def _decode_iam_request(operation: str, value: object) -> object:
    if operation == "introspect":
        fields = require_object(
            value,
            fields={
                "token", "component_type", "requested_capabilities",
                "protocol_version",
            },
            field="iam_request.introspect",
        )
        capabilities = fields["requested_capabilities"]
        if (
            type(capabilities) is not list
            or any(type(item) is not str for item in capabilities)
        ):
            _invalid("iam_request.capabilities")
        return {
            "token": _exact_string(
                fields["token"], "iam_request.token",
            ),
            "component_type": _exact_string(
                fields["component_type"],
                "iam_request.component_type",
            ),
            "requested_capabilities": list(capabilities),
            "protocol_version": _exact_string(
                fields["protocol_version"],
                "iam_request.protocol_version",
            ),
        }
    if operation == "permission_snapshot":
        fields = require_object(
            value,
            fields={
                "identity", "tenant_id", "permission_snapshot_ref",
                "permission_version", "component_type", "capabilities",
                "expires_at",
            },
            field="iam_request.snapshot",
        )
        capabilities = fields["capabilities"]
        if (
            type(capabilities) is not list
            or any(type(item) is not str for item in capabilities)
        ):
            _invalid("iam_request.capabilities")
        decode_time(fields["expires_at"], field="iam_request.expires_at")
        return dict(fields)
    try:
        if operation == "runtime_access_check":
            fields = require_object(
                value,
                fields={
                    "identity", "tenant_id", "permission_snapshot_ref",
                    "permission_version", "message_type", "target",
                    "cross_tenant", "management", "task_creation",
                },
                field="iam_request.access",
            )
            return IamAccessCheckRequest(
                identity=fields["identity"],  # type: ignore[arg-type]
                tenant_id=fields["tenant_id"],  # type: ignore[arg-type]
                permission_snapshot_ref=fields[
                    "permission_snapshot_ref"
                ],  # type: ignore[arg-type]
                permission_version=fields[
                    "permission_version"
                ],  # type: ignore[arg-type]
                message_type=fields["message_type"],  # type: ignore[arg-type]
                target=_decode_iam_target(fields["target"]),
                cross_tenant=fields["cross_tenant"],  # type: ignore[arg-type]
                management=fields["management"],  # type: ignore[arg-type]
                task_creation=fields["task_creation"],  # type: ignore[arg-type]
            )
        if operation == "payload_validate":
            fields = require_object(
                value,
                fields=(
                    {
                        "object_id", "version", "checksum", "tenant_id",
                        "owner_identity", "source_identity", "target",
                    }
                    | (
                        {"callback_message_type"}
                        if type(value) is dict
                        and "callback_message_type" in value
                        else set()
                    )
                ),
                field="iam_request.payload_validate",
            )
            return PayloadRefValidationRequest(
                object_id=fields["object_id"],  # type: ignore[arg-type]
                version=fields["version"],  # type: ignore[arg-type]
                checksum=fields["checksum"],  # type: ignore[arg-type]
                tenant_id=fields["tenant_id"],  # type: ignore[arg-type]
                owner_identity=fields[
                    "owner_identity"
                ],  # type: ignore[arg-type]
                source_identity=fields[
                    "source_identity"
                ],  # type: ignore[arg-type]
                target=_decode_iam_target(fields["target"]),
                callback_message_type=fields.get(
                    "callback_message_type",
                ),  # type: ignore[arg-type]
            )
        if operation == "payload_revalidate":
            return PayloadRefRevalidationRequest.from_wire(value)
    except (NsValidationError, TypeError, ValueError):
        _invalid("iam_request.typed")
    _invalid("iam_request.operation")


def _decode_iam_target(value: object) -> IamTargetContext:
    if type(value) is not dict or not (
        {"kind"} <= set(value) <= {"kind", "tenant_id", "reference"}
    ):
        _invalid("iam_request.target")
    return IamTargetContext(
        kind=value["kind"],  # type: ignore[arg-type]
        tenant_id=value.get("tenant_id"),  # type: ignore[arg-type]
        reference=value.get("reference"),  # type: ignore[arg-type]
    )


def _encode_state_response(
    operation: str,
    result: object,
    request: object,
) -> object:
    if operation == "state_health":
        return encode_health(result)
    if operation in {
        "read_delivery", "read_attempt", "read_summary",
        "read_payload_body", "read_registry_layout",
        "read_registry_tenant",
        "read_admission_dedup", "read_admission_summary",
        "read_delivery_owner", "read_scheduler_cursor",
    }:
        return encode_read_result(result)
    if operation in {
        "transact_admission", "transact_scheduler", "transact_registry",
    }:
        if type(result) is not StateTransactionResult:
            _invalid("state_response.transaction")
        return encode_transaction_result(
            result.records, result.log_positions,
        )
    if operation == "read_scheduler_index":
        request_values = require_object(
            request,
            fields={
                "tenant_id", "bucket_id", "layout_generation",
                "index_name", "cursor", "limit", "max_score",
            },
            field="state_response.index_request",
        )
        return encode_index_result(
            result,
            index_name=_exact_string(
                request_values["index_name"],
                "state_response.index_name",
            ),
            index_bucket="delivery",
        )
    if operation == "read_registry_index":
        request_values = require_object(
            request,
            fields={"index_name", "index_bucket", "cursor", "limit"},
            field="state_response.registry_index_request",
        )
        return encode_index_result(
            result,
            index_name=_exact_string(
                request_values["index_name"],
                "state_response.registry_index_name",
            ),
            index_bucket=_exact_string(
                request_values["index_bucket"],
                "state_response.registry_index_bucket",
            ),
        )
    if operation == "append_audit":
        return encode_append_result(result)
    _invalid("state_response.operation")


def _session_key_fingerprint(public_key: bytes) -> str:
    if type(public_key) is not bytes or len(public_key) != 32:
        _invalid("session_public_key")
    return "sha256:" + hashlib.sha256(public_key).hexdigest()


def _signed_iam_result_fingerprint(
    authority: BrokerSignedIamResult,
) -> str:
    if type(authority) is not BrokerSignedIamResult:
        _invalid("signed_result.fingerprint")
    return "sha256:" + hashlib.sha256(
        _canonical(_encode_signed_iam_result(authority)),
    ).hexdigest()


def _iam_result_fingerprint(values: Mapping[str, object]) -> str:
    if not isinstance(values, Mapping):
        _invalid("iam_result.fingerprint")
    return "sha256:" + hashlib.sha256(
        _canonical(dict(values)),
    ).hexdigest()


def _canonical_json(value: object) -> str:
    return encode_frame(value).decode("utf-8")  # type: ignore[arg-type]


def _decode_canonical_json(value: str, field: str) -> object:
    if type(value) is not str:
        _invalid(field)
    result = decode_frame(value.encode("utf-8"))
    if _canonical_json(result) != value:
        _invalid(field)
    return result


def _state_request_fingerprint(
    *,
    operation: str,
    handle: BrokerAuthorityHandle,
    payload: object,
) -> str:
    if (
        type(operation) is not str
        or not operation
        or type(handle) is not BrokerAuthorityHandle
    ):
        _invalid("state_request.binding")
    return "sha256:" + hashlib.sha256(encode_frame({
        "operation": operation,
        "endpoint_id": handle.endpoint_id,
        "handle_id": handle.handle_id,
        "role": handle.role.value,
        "payload": payload,
    })).hexdigest()


def _sign_state_response(
    *,
    private_key: Ed25519PrivateKey,
    certificate: BrokerInstanceCertificate,
    request_id: str,
    request_sequence: int,
    operation: str,
    handle: BrokerAuthorityHandle,
    request_fingerprint: str,
    response_sequence: int,
    result: object = None,
    error: object = None,
) -> BrokerSignedStateResponse:
    if (result is None) == (error is None):
        _invalid("state_response.outcome")
    now = datetime.now(timezone.utc)
    values = {
        "broker_instance_id": certificate.broker_instance_id,
        "lifecycle_generation": certificate.lifecycle_generation,
        "session_key_fingerprint": _session_key_fingerprint(
            certificate.session_public_key,
        ),
        "request_id": request_id,
        "request_sequence": request_sequence,
        "operation": operation,
        "handle_id": handle.handle_id,
        "role": handle.role.value,
        "request_fingerprint": request_fingerprint,
        "ok": error is None,
        "result_json": _canonical_json(
            result if error is None else None,
        ),
        "error_json": _canonical_json(
            error if error is not None else None,
        ),
        "response_sequence": response_sequence,
        "issued_at": encode_time(now),
        "nonce": uuid.uuid4().hex,
    }
    return BrokerSignedStateResponse(
        broker_instance_id=values["broker_instance_id"],
        lifecycle_generation=values["lifecycle_generation"],
        session_key_fingerprint=values["session_key_fingerprint"],
        request_id=values["request_id"],
        request_sequence=values["request_sequence"],
        operation=values["operation"],
        handle_id=values["handle_id"],
        role=values["role"],
        request_fingerprint=values["request_fingerprint"],
        ok=values["ok"],
        result_json=values["result_json"],
        error_json=values["error_json"],
        response_sequence=values["response_sequence"],
        issued_at=now,
        nonce=values["nonce"],
        signature=private_key.sign(_canonical(values)),
    )


def _signed_response_envelope(
    value: BrokerSignedStateResponse,
) -> dict[str, object]:
    return {
        "version": WIRE_VERSION,
        "kind": "signed_response",
        "signed_response": {
            **value.signed_values(),
            "signature": encode_bytes(value.signature),
        },
    }


def _decode_signed_state_response(
    value: object,
) -> BrokerSignedStateResponse:
    fields = require_object(
        value,
        fields={
            "broker_instance_id", "lifecycle_generation",
            "session_key_fingerprint", "request_id", "request_sequence",
            "operation", "handle_id", "role", "request_fingerprint",
            "ok", "result_json", "error_json", "response_sequence",
            "issued_at", "nonce", "signature",
        },
        field="signed_state_response",
    )
    if type(fields["ok"]) is not bool:
        _invalid("signed_state_response.ok")
    return BrokerSignedStateResponse(
        broker_instance_id=_exact_string(
            fields["broker_instance_id"],
            "signed_state_response.broker_instance_id",
        ),
        lifecycle_generation=_exact_int(
            fields["lifecycle_generation"],
            "signed_state_response.lifecycle_generation",
            minimum=1,
        ),
        session_key_fingerprint=_exact_string(
            fields["session_key_fingerprint"],
            "signed_state_response.session_key_fingerprint",
        ),
        request_id=_exact_string(
            fields["request_id"], "signed_state_response.request_id",
        ),
        request_sequence=_exact_int(
            fields["request_sequence"],
            "signed_state_response.request_sequence",
            minimum=1,
        ),
        operation=_exact_string(
            fields["operation"], "signed_state_response.operation",
        ),
        handle_id=_exact_string(
            fields["handle_id"], "signed_state_response.handle_id",
        ),
        role=_exact_string(
            fields["role"], "signed_state_response.role",
        ),
        request_fingerprint=_exact_string(
            fields["request_fingerprint"],
            "signed_state_response.request_fingerprint",
        ),
        ok=fields["ok"],
        result_json=_exact_string(
            fields["result_json"], "signed_state_response.result_json",
        ),
        error_json=_exact_string(
            fields["error_json"], "signed_state_response.error_json",
        ),
        response_sequence=_exact_int(
            fields["response_sequence"],
            "signed_state_response.response_sequence",
            minimum=1,
        ),
        issued_at=decode_time(
            fields["issued_at"], field="signed_state_response.issued_at",
        ),
        nonce=_exact_string(
            fields["nonce"], "signed_state_response.nonce",
        ),
        signature=decode_bytes(
            fields["signature"],
            field="signed_state_response.signature",
        ),
    )


def _read_fd_once(fd: int, *, maximum: int) -> bytes:
    chunks: list[bytes] = []
    size = 0
    while True:
        chunk = os.read(fd, min(65_536, maximum + 1 - size))
        if not chunk:
            break
        chunks.append(chunk)
        size += len(chunk)
        if size > maximum:
            _invalid("broker.inherited_fd_too_large")
    return b"".join(chunks)


def _physical_state_domain(
    config: AuthorityBrokerConfig,
) -> str:
    parsed = urlsplit(config.state_endpoint)
    if (
        parsed.scheme not in {"redis", "rediss", "valkey", "valkeys"}
        or not parsed.hostname
        or parsed.query
        or parsed.fragment
    ):
        _invalid("config.state_endpoint")
    try:
        port = parsed.port
    except ValueError:
        _invalid("config.state_endpoint")
    path = unquote(parsed.path or "/0").strip("/")
    if not path.isdigit():
        _invalid("config.state_database")
    principal = config.state_username or parsed.username or "default"
    return "\0".join((
        config.state_backend,
        parsed.scheme,
        parsed.hostname.casefold(),
        str(port or (6380 if parsed.scheme.endswith("s") else 6379)),
        str(int(path)),
        config.state_namespace,
        principal,
    ))


def _acquire_physical_domain_lease(
    config: AuthorityBrokerConfig,
) -> _PhysicalDomainLease:
    import portalocker

    identity = hashlib.sha256(
        _physical_state_domain(config).encode(),
    ).hexdigest()
    # A caller-selected directory would let two brokers lock different files
    # for the same physical Redis/Valkey domain.  Keep the lock location
    # process-global and bind only the canonical domain into the filename.
    directory = Path(tempfile.gettempdir()) / "ns-runtime-authority-leases"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"ns-runtime-state-domain-{identity}.lock"
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    file = os.fdopen(fd, "a+b", buffering=0)
    try:
        portalocker.lock(
            file,
            portalocker.LockFlags.EXCLUSIVE
            | portalocker.LockFlags.NON_BLOCKING,
        )
    except portalocker.AlreadyLocked:
        file.close()
        raise _state_denied("parallel_production_composition") from None
    return _PhysicalDomainLease(file=file, path=str(path))


def _normalize_backend_url(value: str) -> tuple[str, str]:
    if type(value) is not str:
        _invalid("config.iam_base_url")
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        _invalid("config.iam_base_url")
    try:
        port = parsed.port
    except ValueError:
        _invalid("config.iam_base_url")
    normalized_port = port or (443 if parsed.scheme == "https" else 80)
    prefix = "/" + parsed.path.strip("/") + "/"
    origin = f"{parsed.scheme}://{parsed.hostname.casefold()}:{normalized_port}"
    return origin, prefix


def _decode_delivery_request(
    payload: object,
) -> tuple[str, int, int, str]:
    fields = require_object(
        payload,
        fields={
            "tenant_id", "bucket_id", "layout_generation", "object_id",
        },
        field="broker.delivery_request",
    )
    return (
        _exact_string(fields["tenant_id"], "broker.tenant_id"),
        _exact_int(fields["bucket_id"], "broker.bucket_id", minimum=0),
        _exact_int(
            fields["layout_generation"],
            "broker.layout_generation",
            minimum=1,
        ),
        _exact_string(fields["object_id"], "broker.object_id"),
    )


def _delivery_partition(
    *,
    tenant_id: str,
    bucket_id: int,
    layout_generation: int,
) -> DeliveryPersistencePartition:
    return DeliveryPersistencePartition(
        tenant_id=tenant_id,
        bucket_id=bucket_id,
        layout_generation=layout_generation,
        namespace=StateNamespace.tenant(
            tenant_id=tenant_id,
            domain="delivery",
        ),
    )


def _registry_partition(runtime_id: str) -> DeliveryPersistencePartition:
    synthetic_tenant = "runtime-registry:" + hashlib.sha256(
        runtime_id.encode(),
    ).hexdigest()
    return DeliveryPersistencePartition(
        tenant_id=synthetic_tenant,
        bucket_id=0,
        layout_generation=1,
        namespace=StateNamespace.tenant(
            tenant_id=synthetic_tenant,
            domain="delivery",
        ),
    )


def _require_isolated_broker_process() -> None:
    """Reject broker-private material in the ordinary runtime interpreter."""

    parent = multiprocessing.parent_process()
    if parent is None or parent.pid == os.getpid():
        _invalid("broker.os_isolation")


def _decode_transaction_dimensions(
    payload: object,
) -> tuple[str, int, int]:
    if type(payload) is not dict:
        _invalid("broker.transaction_request")
    return (
        _exact_string(payload.get("tenant_id"), "broker.tenant_id"),
        _exact_int(
            payload.get("bucket_id"), "broker.bucket_id", minimum=0,
        ),
        _exact_int(
            payload.get("layout_generation"),
            "broker.layout_generation",
            minimum=1,
        ),
    )


def _parse_backend_result(parser: object, value: object) -> object:
    """Normalize malformed typed IAM payloads as an unavailable backend."""

    try:
        return parser(value)  # type: ignore[operator]
    except (NsValidationError, TypeError, ValueError):
        raise _broker_unavailable("malformed_backend_result") from None


def _exception_values(error: Exception) -> dict[str, object]:
    details = getattr(error, "details", {})
    if isinstance(error, NsRuntimeIamDeniedError):
        kind = "iam_denied"
    elif isinstance(error, NsRuntimeIamTimeoutError):
        kind = "iam_timeout"
    elif isinstance(error, NsRuntimeIamUnavailableError):
        kind = "iam_unavailable"
    elif isinstance(error, NsRuntimeStateStoreIndeterminateWriteError):
        kind = "state_indeterminate"
    elif isinstance(error, NsRuntimeStateStoreCapabilityUnavailableError):
        kind = "state_denied"
    elif isinstance(error, NsRuntimeStateStoreConflictError):
        kind = "state_conflict"
    elif isinstance(error, NsRuntimeStateStoreVersionMismatchError):
        kind = "state_version_mismatch"
    elif isinstance(error, NsRuntimeStateStoreNamespaceViolationError):
        kind = "state_namespace"
    elif isinstance(error, NsRuntimeStateStoreTimeoutError):
        kind = "state_timeout"
    elif isinstance(error, NsValidationError):
        kind = "validation"
    else:
        kind = "state_unavailable"
    return {
        "kind": kind,
        "reason": str(details.get("reason", type(error).__name__)),
    }


def _error_values(kind: str, reason: str) -> dict[str, object]:
    return {"kind": kind, "reason": reason}


def _validate_remote_error(response: object) -> None:
    values = require_object(
        response,
        fields={"kind", "reason"},
        field="remote_error",
    )
    kind = _exact_string(values["kind"], "remote_error.kind")
    _exact_string(values["reason"], "remote_error.reason")
    if kind not in {
        "iam_denied", "iam_timeout", "iam_unavailable",
        "state_indeterminate", "state_denied", "state_conflict",
        "state_version_mismatch", "state_namespace", "state_timeout",
        "validation", "state_unavailable",
    }:
        _invalid("remote_error.kind")


def _raise_remote_error(response: object) -> None:
    values = require_object(
        response,
        fields={"kind", "reason"},
        field="remote_error",
    )
    kind = values["kind"]
    reason = _exact_string(values["reason"], "remote_error.reason")
    details = {
        "component": "authority_broker",
        "reason": reason,
    }
    if kind == "iam_denied":
        raise NsRuntimeIamDeniedError(details=details)
    if kind == "iam_timeout":
        raise NsRuntimeIamTimeoutError(details=details)
    if kind == "iam_unavailable":
        raise NsRuntimeIamUnavailableError(details=details)
    if kind == "state_indeterminate":
        raise NsRuntimeStateStoreIndeterminateWriteError(details=details)
    if kind == "state_denied":
        raise NsRuntimeStateStoreCapabilityUnavailableError(details=details)
    if kind == "state_conflict":
        raise NsRuntimeStateStoreConflictError(details=details)
    if kind == "state_version_mismatch":
        raise NsRuntimeStateStoreVersionMismatchError(details=details)
    if kind == "state_namespace":
        raise NsRuntimeStateStoreNamespaceViolationError(details=details)
    if kind == "state_timeout":
        raise NsRuntimeStateStoreTimeoutError(details=details)
    if kind == "validation":
        raise NsValidationError(
            "Authority broker request is invalid.",
            details=details,
        )
    raise NsRuntimeStateStoreUnavailableError(details=details)


def _indeterminate(
    operation: str,
    reason: str,
) -> NsRuntimeStateStoreIndeterminateWriteError:
    return NsRuntimeStateStoreIndeterminateWriteError(details={
        "component": "authority_broker",
        "operation": operation,
        "reason": reason,
    })


def _bind_write_transaction_result(
    transaction: DeliveryPersistenceTransaction,
    raw: object,
    *,
    operation: str,
) -> DeliveryPersistenceTransactionResult:
    try:
        records, positions = decode_transaction_result(raw)
        return DeliveryPersistenceTransactionResult.for_transaction(
            transaction,
            records=records,
            log_positions=positions,
        )
    except (NsValidationError, TypeError, ValueError):
        raise _indeterminate(
            operation, "ipc_malformed_write_result",
        ) from None


def _exact_string(value: object, field: str) -> str:
    if type(value) is not str or not value:
        _invalid(field)
    return value


def _exact_optional_string(value: object, field: str) -> str:
    if type(value) is not str:
        _invalid(field)
    return value


def _exact_int(value: object, field: str, *, minimum: int) -> int:
    if type(value) is not int or value < minimum:
        _invalid(field)
    return value


def _exact_number(value: object, field: str) -> float:
    if (
        type(value) not in {int, float}
        or not math.isfinite(value)
        or value <= 0
    ):
        _invalid(field)
    return float(value)


def _canonical(values: Mapping[str, object]) -> bytes:
    return json.dumps(
        values,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def _verify(public_key: bytes, payload: bytes, signature: bytes) -> bool:
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(
            signature,
            payload,
        )
    except (ValueError, TypeError, InvalidSignature):
        return False
    return True


def _parse_time(value: object) -> datetime:
    if type(value) is not str:
        _invalid("broker.time")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        _invalid("broker.time")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        _invalid("broker.time")
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _broker_unavailable(reason: str) -> NsRuntimeIamUnavailableError:
    return NsRuntimeIamUnavailableError(details={
        "component": "authority_broker",
        "reason": reason,
    })


def _state_denied(
    reason: str,
) -> NsRuntimeStateStoreCapabilityUnavailableError:
    return NsRuntimeStateStoreCapabilityUnavailableError(details={
        "component": "authority_broker",
        "reason": reason,
    })


def _state_unavailable(reason: str) -> NsRuntimeStateStoreUnavailableError:
    return NsRuntimeStateStoreUnavailableError(details={
        "component": "authority_broker",
        "reason": reason,
    })


def _operation_unavailable(
    operation: str,
    reason: str,
) -> Exception:
    if operation in _IAM_OPERATIONS:
        return _broker_unavailable(reason)
    return _state_unavailable(reason)


def _invalid(field: str) -> None:
    raise NsValidationError(
        "Authority broker value is invalid.",
        details={"component": "authority_broker", "field": field},
    )


__all__ = (
    "AdmissionRepositoryProxy",
    "AuditRepositoryProxy",
    "AuthorityBrokerConfig",
    "AuthorityBrokerRepositories",
    "AuthorityBrokerStateStoreProxy",
    "BrokerAuthorityHandle",
    "BrokerIamVerificationReceipt",
    "BrokerRepositoryRole",
    "BrokerSignedIamResult",
    "broker_request_fingerprint",
    "PayloadRepositoryProxy",
    "ProductionAuthorityBroker",
    "ProductionIamAuthorityProxy",
    "RegistryRepositoryProxy",
    "SchedulerRepositoryProxy",
    "VerifiedBrokerIamResult",
    "start_production_authority_broker",
    "start_contract_test_authority_broker",
    "start_integration_test_authority_broker",
)
