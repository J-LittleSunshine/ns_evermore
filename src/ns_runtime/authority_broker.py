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
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from multiprocessing.connection import Connection
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
_ROOT_CERTIFICATE_TTL_SECONDS = 300
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
            _physical_state_domain(
                self,
                credential_reference="validation-only",
            )
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
        now: datetime,
    ) -> bool:
        if (
            type(self) is not BrokerInstanceCertificate
            or expected_realm not in _BROKER_REALMS
            or self.trust_realm != expected_realm
            or self.runtime_id != expected_runtime_id
            or self.lifecycle_generation != 1
            or self.issued_at > now
            or self.expires_at <= now
            or self.expires_at - self.issued_at
            > timedelta(seconds=_ROOT_CERTIFICATE_TTL_SECONDS)
            or len(self.session_public_key) != 32
            or len(root_public_key) != 32
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
    handle_id: str
    role: BrokerRepositoryRole
    runtime_id: str
    lifecycle_generation: int
    signature: bytes

    def signed_values(self) -> Mapping[str, object]:
        return {
            "broker_instance_id": self.broker_instance_id,
            "handle_id": self.handle_id,
            "role": self.role.value,
            "runtime_id": self.runtime_id,
            "lifecycle_generation": self.lifecycle_generation,
        }

    def verify(self, public_key: bytes, *, instance_id: str) -> bool:
        if (
            type(self) is not BrokerAuthorityHandle
            or self.broker_instance_id != instance_id
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


@dataclass(frozen=True, slots=True, kw_only=True)
class VerifiedBrokerIamResult:
    result: object
    authority: BrokerSignedIamResult


class _BrokerChannel:
    """Serialized IPC channel; it contains no signing or provider material."""

    __slots__ = (
        "_connection", "_process", "_public_key", "_instance_id", "_lock",
        "_closed", "_timeout_seconds", "_realm", "_response_sequence",
    )

    def __init__(
        self,
        *,
        connection: Connection,
        process: multiprocessing.Process,
        public_key: bytes,
        instance_id: str,
        timeout_seconds: float,
        realm: str,
    ) -> None:
        self._connection = connection
        self._process = process
        self._public_key = public_key
        self._instance_id = instance_id
        self._lock = threading.Lock()
        self._closed = False
        self._timeout_seconds = float(timeout_seconds)
        self._realm = realm
        self._response_sequence = 0

    @property
    def public_key(self) -> bytes:
        return bytes(self._public_key)

    @property
    def instance_id(self) -> str:
        return self._instance_id

    @property
    def alive(self) -> bool:
        return bool(not self._closed and self._process.is_alive())

    def request(
        self,
        *,
        handle: BrokerAuthorityHandle,
        operation: str,
        payload: dict[str, object] | list[object] | str | int | float | bool | None,
    ) -> object:
        if not handle.verify(
                self._public_key,
                instance_id=self._instance_id,
        ):
            raise _broker_unavailable("handle_invalid")
        if self._closed or not self._process.is_alive():
            if operation in _WRITE_OPERATIONS:
                raise NsRuntimeStateStoreIndeterminateWriteError(details={
                    "component": "authority_broker",
                    "operation": operation,
                    "reason": "broker_unavailable_outcome_unknown",
                })
            raise _broker_unavailable("broker_unavailable")
        request_id = "ipc_" + uuid.uuid4().hex
        message = {
            "version": WIRE_VERSION,
            "kind": "request",
            "request_id": request_id,
            "handle": _encode_handle(handle),
            "operation": operation,
            "payload": payload,
        }
        raw_request = encode_frame(message)  # pre-send schema/size rejection
        sent = False
        try:
            with self._lock:
                self._connection.send_bytes(raw_request)
                sent = True
                if not self._connection.poll(self._timeout_seconds):
                    self._closed = True
                    self._stop_process()
                    if operation in _WRITE_OPERATIONS:
                        raise _indeterminate(operation, "ipc_timeout")
                    raise _broker_unavailable("ipc_timeout")
                response = decode_frame(
                    self._connection.recv_bytes(MAX_FRAME_BYTES),
                )
        except NsRuntimeStateStoreIndeterminateWriteError:
            raise
        except (BrokenPipeError, EOFError, OSError, NsValidationError):
            self._closed = True
            if operation in _WRITE_OPERATIONS and sent:
                raise _indeterminate(operation, "ipc_invalid_response") from None
            raise _broker_unavailable("ipc_closed") from None
        try:
            values = require_object(
                response,
                fields={
                    "version", "kind", "request_id", "sequence",
                    "ok", "result", "error",
                },
                field="response",
            )
            sequence = values["sequence"]
            if (
                values["version"] != WIRE_VERSION
                or values["kind"] != "response"
                or values["request_id"] != request_id
                or type(sequence) is not int
                or sequence != self._response_sequence + 1
                or type(values["ok"]) is not bool
            ):
                _invalid("response.binding")
            self._response_sequence = sequence
            if values["ok"] is True:
                if values["error"] is not None:
                    _invalid("response.error")
                return values["result"]
            if values["result"] is not None:
                _invalid("response.result")
            _raise_remote_error(values["error"])
        except (NsValidationError, KeyError, TypeError, ValueError):
            if operation in _WRITE_OPERATIONS and sent:
                raise _indeterminate(
                    operation, "ipc_malformed_response",
                ) from None
            raise _broker_unavailable("malformed_response") from None

    def close(self, *, terminate: bool = False) -> None:
        if self._closed:
            return
        try:
            with self._lock:
                if self._process.is_alive() and not terminate:
                    self._connection.send_bytes(encode_frame({
                        "version": WIRE_VERSION,
                        "kind": "shutdown",
                    }))
                    if self._connection.poll(5.0):
                        decode_frame(
                            self._connection.recv_bytes(MAX_FRAME_BYTES),
                        )
        except (BrokenPipeError, EOFError, OSError):
            pass
        finally:
            self._closed = True
            try:
                self._connection.close()
            except OSError:
                pass
            self._process.join(timeout=5.0)
            if self._process.is_alive():
                self._process.terminate()
                self._process.join(timeout=5.0)
            if self._process.is_alive():
                self._process.kill()
                self._process.join(timeout=5.0)
            if self._process.is_alive():
                raise _broker_unavailable("broker_process_did_not_exit")

    def _stop_process(self) -> None:
        try:
            self._connection.close()
        except OSError:
            pass
        self._process.join(timeout=0.1)
        if self._process.is_alive():
            self._process.terminate()
            self._process.join(timeout=5.0)
        if self._process.is_alive():
            self._process.kill()
            self._process.join(timeout=5.0)


class ProductionIamAuthorityProxy(HandshakeIamAdapter):
    """Fixed-operation IAM proxy; all backend decisions originate in broker."""

    __slots__ = (
        "_channel", "_handle", "_clock", "_iam_mode",
        "_authorization_service",
    )

    def __init__(self, *args: object, **kwargs: object) -> None:
        del self, args, kwargs
        _invalid("iam_proxy.broker_authority")

    def _is_production_adapter(self) -> bool:
        return bool(
            type(self) is ProductionIamAuthorityProxy
            and self._is_broker_adapter()
            and self._channel._realm == "production"
        )

    def _is_broker_adapter(self) -> bool:
        substituted = {
            "authenticate", "access_check", "access_check_signed",
            "refresh_permission_snapshot", "validate_payload_ref",
            "revalidate_payload_ref",
        }.intersection(getattr(self, "__dict__", {}))
        return bool(
            type(self) in {
                ProductionIamAuthorityProxy,
                ContractTestIamAuthorityProxy,
            }
            and type(getattr(self, "_channel", None)) is _BrokerChannel
            and type(getattr(self, "_handle", None)) is BrokerAuthorityHandle
            and self._handle.role is BrokerRepositoryRole.IAM
            and self._handle.verify(
                self._channel.public_key,
                instance_id=self._channel.instance_id,
            )
            and self._channel.alive
            and (
                (
                    type(self) is ProductionIamAuthorityProxy
                    and self._channel._realm == "production"
                )
                or (
                    type(self) is ContractTestIamAuthorityProxy
                    and self._channel._realm == "contract-test"
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
        if not self._is_broker_adapter():
            channel = getattr(self, "_channel", None)
            handle = getattr(self, "_handle", None)
            if (
                type(self) in {
                    ProductionIamAuthorityProxy,
                    ContractTestIamAuthorityProxy,
                }
                and type(channel) is _BrokerChannel
                and type(handle) is BrokerAuthorityHandle
                and handle.role is BrokerRepositoryRole.IAM
                and handle.verify(
                    channel.public_key,
                    instance_id=channel.instance_id,
                )
                and not channel.alive
            ):
                raise _broker_unavailable("broker_unavailable")
            _invalid("iam_proxy.provenance")
        request_fingerprint = _request_fingerprint(operation, payload)
        raw_result = await asyncio.to_thread(
            self._channel.request,
            handle=self._handle,
            operation=operation,
            payload=_encode_iam_request(operation, payload),
        )
        result = _decode_signed_iam_result(raw_result)
        if type(result) is not BrokerSignedIamResult or not result.verify(
            public_key=self._channel.public_key,
            broker_instance_id=self._channel.instance_id,
            operation=operation,
            request_fingerprint=request_fingerprint,
            now=self._clock.utc_now(),
        ):
            raise _broker_unavailable("signature_invalid")
        typed = _decode_iam_result(operation, result.result_mapping())
        return VerifiedBrokerIamResult(result=typed, authority=result)

    def _bind_authorization_service(self, service: object) -> None:
        if (
            not self._is_production_adapter()
            or service is None
            or self._authorization_service is not None
        ):
            _invalid("iam_proxy.authorization_service")
        self._authorization_service = service

    def _owns_authorization_service(self, service: object) -> bool:
        return bool(
            self._is_production_adapter()
            and self._authorization_service is service
        )

    def __copy__(self) -> "ProductionIamAuthorityProxy":
        _invalid("iam_proxy.copy")

    def __deepcopy__(self, memo: dict[int, object]) -> "ProductionIamAuthorityProxy":
        del memo
        _invalid("iam_proxy.copy")


class ContractTestIamAuthorityProxy(ProductionIamAuthorityProxy):
    """Explicit non-production broker adapter bound to a test trust root."""


class _RepositoryProxy:
    __slots__ = ("_channel", "_handle")
    _ROLE: BrokerRepositoryRole

    def __init__(self, *args: object, **kwargs: object) -> None:
        del self, args, kwargs
        _invalid("repository_proxy.broker_authority")

    @property
    def role(self) -> BrokerRepositoryRole:
        return self._ROLE

    async def _request(self, operation: str, payload: object) -> object:
        if (
            type(self) is _RepositoryProxy
            or self._handle.role is not self._ROLE
            or operation not in _ROLE_OPERATIONS[self._ROLE.value]
        ):
            raise _state_denied("repository_operation_denied")
        return await asyncio.to_thread(
            self._channel.request,
            handle=self._handle,
            operation=operation,
            payload=payload,
        )

    def __copy__(self) -> "_RepositoryProxy":
        _invalid("repository_proxy.copy")

    def __deepcopy__(self, memo: dict[int, object]) -> "_RepositoryProxy":
        del memo
        _invalid("repository_proxy.copy")


class AdmissionRepositoryProxy(_RepositoryProxy):
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

    async def open(self) -> None:
        if self._state == "closed":
            raise _state_unavailable("broker_closed")
        result = decode_health(await asyncio.to_thread(
            self._channel.request,
            handle=self._handle,
            operation="state_health",
            payload={},
        ))
        if type(result) is not StateStoreHealth:
            raise _state_unavailable("invalid_health")
        self._state = "open"

    async def health(self) -> StateStoreHealth:
        result = decode_health(await asyncio.to_thread(
            self._channel.request,
            handle=self._handle,
            operation="state_health",
            payload={},
        ))
        if type(result) is not StateStoreHealth:
            raise _state_unavailable("invalid_health")
        return result

    async def close(self) -> None:
        if self._state == "closed":
            return
        self._state = "closed"
        await asyncio.to_thread(self._channel.close)


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
        "iam", "repositories", "state_store", "public_key",
        "broker_instance_id", "_channel",
    )

    def __init__(self, *args: object, **kwargs: object) -> None:
        del self, args, kwargs
        _invalid("broker.bootstrap")

    @property
    def alive(self) -> bool:
        return self._channel.alive

    def close(self, *, terminate: bool = False) -> None:
        self._channel.close(terminate=terminate)

    def __del__(self) -> None:
        channel = getattr(self, "_channel", None)
        if type(channel) is _BrokerChannel:
            channel.close(terminate=True)


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
    state_password_source: str = "none",
    startup_timeout_seconds: float = 15.0,
) -> ProductionAuthorityBroker:
    """Start an explicitly non-production broker under an ephemeral test root."""

    if (
        type(config) is not AuthorityBrokerConfig
        or type(iam_service_credential) is not str
        or not iam_service_credential
        or type(state_password_source) is not str
        or not state_password_source
        or config.state_backend in {"redis", "valkey"}
    ):
        _invalid("broker.contract_test_config")
    return _start_test_authority_broker(
        config=config,
        iam_service_credential=iam_service_credential,
        state_password_source=state_password_source,
        startup_timeout_seconds=startup_timeout_seconds,
        realm="contract-test",
    )


def start_integration_test_authority_broker(
    *,
    config: AuthorityBrokerConfig,
    iam_service_credential: str,
    state_password_source: str,
    startup_timeout_seconds: float = 15.0,
) -> ProductionAuthorityBroker:
    """Run real provider integration under a non-production test trust root."""

    if (
        type(config) is not AuthorityBrokerConfig
        or config.state_backend not in {"redis", "valkey"}
        or type(iam_service_credential) is not str
        or not iam_service_credential
        or type(state_password_source) is not str
        or not state_password_source
    ):
        _invalid("broker.integration_test_config")
    return _start_test_authority_broker(
        config=config,
        iam_service_credential=iam_service_credential,
        state_password_source=state_password_source,
        startup_timeout_seconds=startup_timeout_seconds,
        realm="integration-test",
    )


def _start_test_authority_broker(
    *,
    config: AuthorityBrokerConfig,
    iam_service_credential: str,
    state_password_source: str,
    startup_timeout_seconds: float,
    realm: str,
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
            "state_password_source": state_password_source,
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
    )


def _spawn_authority_broker(
    *,
    config: AuthorityBrokerConfig,
    expected_root_public_key: bytes,
    root_key_fd: int,
    secrets_fd: int,
    realm: str,
    startup_timeout_seconds: float,
) -> ProductionAuthorityBroker:
    if realm not in _BROKER_REALMS:
        _invalid("broker.realm")
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe(duplex=True)
    root_key_handle = DupFd(root_key_fd)
    secrets_handle = DupFd(secrets_fd)
    process = context.Process(
        target=_authority_broker_process,
        args=(
            child,
            encode_frame(_encode_broker_config(config)),
            root_key_handle,
            secrets_handle,
            realm,
            expected_root_public_key,
        ),
        name="ns-runtime-authority-broker",
        daemon=False,
    )
    try:
        process.start()
    finally:
        child.close()
        for fd in (root_key_fd, secrets_fd):
            try:
                os.close(fd)
            except OSError:
                pass
    return _accept_started_authority_broker(
        parent=parent,
        process=process,
        config=config,
        expected_root_public_key=expected_root_public_key,
        realm=realm,
        startup_timeout_seconds=startup_timeout_seconds,
    )


def _complete_inherited_authority_broker_start(
    *,
    parent: Connection,
    process: multiprocessing.Process,
    config: AuthorityBrokerConfig,
    startup_timeout_seconds: float = 15.0,
) -> ProductionAuthorityBroker:
    """Send only non-secret config to the already isolated broker child."""

    if (
        type(config) is not AuthorityBrokerConfig
        or not process.is_alive()
    ):
        _invalid("broker.pending_bootstrap")
    try:
        parent.send_bytes(encode_frame({
            "version": WIRE_VERSION,
            "kind": "bootstrap_config",
            "config": _encode_broker_config(config),
        }))
    except (BrokenPipeError, EOFError, OSError):
        raise _broker_unavailable("bootstrap_channel_closed") from None
    return _accept_started_authority_broker(
        parent=parent,
        process=process,
        config=config,
        expected_root_public_key=_PRODUCTION_ROOT_PUBLIC_KEY,
        realm="production",
        startup_timeout_seconds=startup_timeout_seconds,
    )


def _accept_started_authority_broker(
    *,
    parent: Connection,
    process: multiprocessing.Process,
    config: AuthorityBrokerConfig,
    expected_root_public_key: bytes,
    realm: str,
    startup_timeout_seconds: float,
) -> ProductionAuthorityBroker:
    if not parent.poll(startup_timeout_seconds):
        process.terminate()
        process.join(timeout=5.0)
        parent.close()
        raise _broker_unavailable("startup_timeout")
    try:
        ready = decode_frame(parent.recv_bytes(MAX_FRAME_BYTES))
    except (EOFError, OSError, NsValidationError):
        process.join(timeout=5.0)
        parent.close()
        raise _broker_unavailable("startup_failed") from None
    if type(ready) is not dict or ready.get("ok") is not True:
        process.join(timeout=5.0)
        parent.close()
        reason = (
            ready.get("reason", "startup_failed")
            if type(ready) is dict
            else "startup_failed"
        )
        if reason == "parallel_production_composition":
            raise _state_denied(reason)
        raise _broker_unavailable(str(reason))
    try:
        values = require_object(
            ready,
            fields={"version", "kind", "ok", "certificate", "handles"},
            field="ready",
        )
        if values["version"] != WIRE_VERSION or values["kind"] != "ready":
            _invalid("ready.version")
        certificate = _decode_certificate(values["certificate"])
        if not certificate.verify(
            expected_root_public_key,
            expected_realm=realm,
            expected_runtime_id=config.runtime_id,
            now=datetime.now(timezone.utc),
        ):
            _invalid("ready.root_certificate")
        public_key = certificate.session_public_key
        instance_id = certificate.broker_instance_id
        raw_handles = values["handles"]
        if type(raw_handles) is not dict:
            _invalid("ready.handles")
        handles = {
            key: _decode_handle(value)
            for key, value in raw_handles.items()
        }
    except (NsValidationError, TypeError, ValueError):
        process.terminate()
        process.join(timeout=5.0)
        parent.close()
        raise _broker_unavailable("startup_handshake_invalid")
    channel = _BrokerChannel(
        connection=parent,
        process=process,
        public_key=public_key,
        instance_id=instance_id,
        timeout_seconds=max(
            config.iam_timeout_seconds,
            config.state_operation_timeout_seconds,
        ) + 2.0,
        realm=realm,
    )
    expected_roles = tuple(BrokerRepositoryRole)
    for role in expected_roles:
        handle = handles.get(role.value)
        if (
            type(handle) is not BrokerAuthorityHandle
            or handle.role is not role
            or not handle.verify(public_key, instance_id=instance_id)
        ):
            channel.close(terminate=True)
            raise _broker_unavailable("startup_handle_invalid")

    iam_type = (
        ProductionIamAuthorityProxy
        if realm == "production"
        else ContractTestIamAuthorityProxy
    )
    iam = object.__new__(iam_type)
    iam._channel = channel
    iam._handle = handles[BrokerRepositoryRole.IAM.value]
    iam._clock = SystemClock()
    iam._iam_mode = config.iam_mode
    iam._authorization_service = None

    proxies: dict[BrokerRepositoryRole, _RepositoryProxy] = {}
    for role, proxy_type in (
        (BrokerRepositoryRole.ADMISSION, AdmissionRepositoryProxy),
        (BrokerRepositoryRole.SCHEDULER, SchedulerRepositoryProxy),
        (BrokerRepositoryRole.PAYLOAD, PayloadRepositoryProxy),
        (BrokerRepositoryRole.REGISTRY, RegistryRepositoryProxy),
        (BrokerRepositoryRole.AUDIT, AuditRepositoryProxy),
    ):
        proxy = object.__new__(proxy_type)
        proxy._channel = channel
        proxy._handle = handles[role.value]
        proxies[role] = proxy
    repositories = AuthorityBrokerRepositories(
        admission=proxies[BrokerRepositoryRole.ADMISSION],  # type: ignore[arg-type]
        scheduler=proxies[BrokerRepositoryRole.SCHEDULER],  # type: ignore[arg-type]
        payload=proxies[BrokerRepositoryRole.PAYLOAD],  # type: ignore[arg-type]
        registry=proxies[BrokerRepositoryRole.REGISTRY],  # type: ignore[arg-type]
        audit=proxies[BrokerRepositoryRole.AUDIT],  # type: ignore[arg-type]
    )
    state_store = object.__new__(AuthorityBrokerStateStoreProxy)
    state_store._channel = channel
    state_store._handle = handles[BrokerRepositoryRole.LIFECYCLE.value]
    state_store._state = "new"

    value = object.__new__(ProductionAuthorityBroker)
    value.iam = iam
    value.repositories = repositories
    value.state_store = state_store
    value.public_key = bytes(public_key)
    value.broker_instance_id = instance_id
    value._channel = channel
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


class _BrokerIamBackend:
    """Broker-private HTTP adapter with an exact fixed endpoint allowlist."""

    __slots__ = (
        "_client", "_credential", "_clock", "_iam_mode",
        "_ttl", "_backend_origin", "_path_prefix",
    )

    def __init__(
        self,
        config: AuthorityBrokerConfig,
        secrets: Mapping[str, str],
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
        self._credential = secrets["iam_service_credential"]
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
        secrets: Mapping[str, str],
    ) -> None:
        _require_isolated_broker_process()
        self.store = None
        self.repositories = {}
        self.lease = None
        self.runtime_id = config.runtime_id
        self.available = config.state_backend in {"redis", "valkey"}
        if not self.available:
            return
        self.lease = _acquire_physical_domain_lease(
            config,
            credential_reference=secrets["state_password_source"],
        )
        try:
            self._create_provider(config, secrets)
        except BaseException:
            self.lease.close()
            self.lease = None
            raise

    def _create_provider(
        self,
        config: AuthorityBrokerConfig,
        secrets: Mapping[str, str],
    ) -> None:
        from ns_common.config import NsRuntimeStateStoreConfig
        from ns_common.state_store import (
            StateAuthorityKind,
            StateCallerCapability,
            StateStoreRepositoryRole,
        )
        from ns_common.state_store.composition import (
            _create_redis_valkey_provider,
        )
        from ns_common.state_store.store import _ProductionStateScopeValidator

        validator = object.__new__(_ProductionStateScopeValidator)
        validator._repository_specs = {}
        validator._scopes = {}
        validator._closed = False
        validator._realm = "production-broker"
        typed_config = NsRuntimeStateStoreConfig(
            backend=config.state_backend,  # type: ignore[arg-type]
            endpoint=config.state_endpoint,
            username=config.state_username,
            password_source=secrets["state_password_source"],
            namespace=config.state_namespace,
            operation_timeout_seconds=int(
                config.state_operation_timeout_seconds,
            ),
        )
        store = _create_redis_valkey_provider(
            config=typed_config,
            clock=SystemClock(),
            capabilities=None,
            production_scope_validator=validator,
        )
        if store is None:
            raise _state_unavailable("provider_unavailable")
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


async def _broker_async_main(
    connection: Connection,
    config: AuthorityBrokerConfig,
    root_private_key: Ed25519PrivateKey,
    secrets: Mapping[str, str],
    realm: str,
) -> None:
    session_private_key = Ed25519PrivateKey.generate()
    session_public_key = session_private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    instance_id = "broker_" + uuid.uuid4().hex
    iam = _BrokerIamBackend(config, secrets)
    state = _BrokerStateBackend(config, secrets)
    iam_sequence = 0
    response_sequence = 0
    generation = 1
    handles = {
        role.value: _new_handle(
            private_key=session_private_key,
            instance_id=instance_id,
            role=role,
            runtime_id=config.runtime_id,
            generation=generation,
        )
        for role in BrokerRepositoryRole
    }
    now = datetime.now(timezone.utc)
    certificate_values = {
        "trust_realm": realm,
        "broker_instance_id": instance_id,
        "session_public_key": encode_bytes(session_public_key),
        "runtime_id": config.runtime_id,
        "lifecycle_generation": generation,
        "issued_at": encode_time(now),
        "expires_at": encode_time(
            now + timedelta(seconds=_ROOT_CERTIFICATE_TTL_SECONDS),
        ),
        "nonce": uuid.uuid4().hex,
    }
    certificate = BrokerInstanceCertificate(
        trust_realm=realm,
        broker_instance_id=instance_id,
        session_public_key=session_public_key,
        runtime_id=config.runtime_id,
        lifecycle_generation=generation,
        issued_at=now,
        expires_at=(
            now + timedelta(seconds=_ROOT_CERTIFICATE_TTL_SECONDS)
        ),
        nonce=certificate_values["nonce"],
        signature=root_private_key.sign(_canonical(certificate_values)),
    )
    del root_private_key
    try:
        await state.open()
        connection.send_bytes(encode_frame({
            "version": WIRE_VERSION,
            "kind": "ready",
            "ok": True,
            "certificate": _encode_certificate(certificate),
            "handles": {
                role: _encode_handle(handle)
                for role, handle in handles.items()
            },
        }))
        while True:
            try:
                raw_message = await asyncio.to_thread(
                    connection.recv_bytes,
                    MAX_FRAME_BYTES,
                )
                message = decode_frame(raw_message)
            except (EOFError, OSError, NsValidationError):
                break
            if message == {
                "version": WIRE_VERSION,
                "kind": "shutdown",
            }:
                connection.send_bytes(encode_frame({
                    "version": WIRE_VERSION,
                    "kind": "shutdown_complete",
                }))
                break
            if type(message) is not dict or set(message) != {
                "version", "kind", "request_id", "handle",
                "operation", "payload",
            }:
                # No request id can be trusted, so close instead of reflecting
                # attacker-controlled structure into a response.
                break
            request_id = message["request_id"]
            operation = message["operation"]
            if (
                message["version"] != WIRE_VERSION
                or message["kind"] != "request"
                or type(request_id) is not str
                or not request_id
                or type(operation) is not str
            ):
                break
            try:
                handle = _decode_handle(message["handle"])
            except NsValidationError:
                response_sequence += 1
                connection.send_bytes(encode_frame(_wire_response(
                    request_id=request_id,
                    sequence=response_sequence,
                    error=_error_values("state_denied", "handle_denied"),
                )))
                continue
            payload = message["payload"]
            if (
                not handle.verify(
                    session_public_key,
                    instance_id=instance_id,
                )
                or handle.lifecycle_generation != generation
                or handles.get(handle.role.value) != handle
                or not _role_allows(handle.role, operation)
            ):
                response_sequence += 1
                connection.send_bytes(encode_frame(_wire_response(
                    request_id=request_id,
                    sequence=response_sequence,
                    error=_error_values("state_denied", "handle_denied"),
                )))
                continue
            try:
                if handle.role is BrokerRepositoryRole.IAM:
                    typed_request = _decode_iam_request(operation, payload)
                    typed_result = await iam.execute(
                        operation, typed_request,
                    )
                    iam_sequence += 1
                    result = _sign_iam_result(
                        private_key=session_private_key,
                        instance_id=instance_id,
                        operation=operation,
                        request=typed_request,
                        result=typed_result,
                        sequence=iam_sequence,
                        ttl_seconds=config.permission_snapshot_ttl_seconds,
                    )
                    wire_result = _encode_signed_iam_result(result)
                else:
                    result = await state.execute(
                        role=handle.role,
                        operation=operation,
                        payload=payload,
                    )
                    wire_result = _encode_state_response(
                        operation, result, payload,
                    )
            except BaseException as error:
                if not isinstance(error, Exception):
                    raise
                response_sequence += 1
                connection.send_bytes(encode_frame(_wire_response(
                    request_id=request_id,
                    sequence=response_sequence,
                    error=_exception_values(error),
                )))
            else:
                response_sequence += 1
                connection.send_bytes(encode_frame(_wire_response(
                    request_id=request_id,
                    sequence=response_sequence,
                    result=wire_result,
                )))
    finally:
        try:
            await state.close()
        finally:
            await iam.close()
            connection.close()


def _authority_broker_process(
    connection: Connection,
    config_raw: bytes | None,
    root_key_handle: object,
    secrets_handle: object,
    realm: str,
    expected_root_public_key: bytes,
) -> None:
    """Top-level spawn target; descriptors are consumed before backends load."""

    try:
        _require_isolated_broker_process()
        if realm not in _BROKER_REALMS:
            _invalid("broker.realm")
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
            connection.send_bytes(encode_frame({
                "version": WIRE_VERSION,
                "kind": "fd_custody",
            }))
            bootstrap_message = require_object(
                decode_frame(connection.recv_bytes(MAX_FRAME_BYTES)),
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
            connection,
            config,
            root_private_key,
            secrets,
            realm,
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
                connection.close()
            except OSError:
                pass


def _new_handle(
    *,
    private_key: Ed25519PrivateKey,
    instance_id: str,
    role: BrokerRepositoryRole,
    runtime_id: str,
    generation: int,
) -> BrokerAuthorityHandle:
    values = {
        "broker_instance_id": instance_id,
        "handle_id": "handle_" + uuid.uuid4().hex,
        "role": role.value,
        "runtime_id": runtime_id,
        "lifecycle_generation": generation,
    }
    return BrokerAuthorityHandle(
        broker_instance_id=instance_id,
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
    operation: str,
    request: object,
    result: object,
    sequence: int,
    ttl_seconds: float,
) -> BrokerSignedIamResult:
    now = datetime.now(timezone.utc)
    result_values = _encode_iam_result(operation, result)
    request_values = _request_claims(operation, request)
    result_expiry = _result_expiry(result)
    expires_at = min(
        result_expiry,
        now + timedelta(seconds=float(ttl_seconds)),
    )
    values = {
        "broker_instance_id": instance_id,
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


def _decode_broker_secrets(value: object) -> dict[str, str]:
    fields = require_object(
        value,
        fields={"iam_service_credential", "state_password_source"},
        field="broker.secrets",
    )
    credential = _exact_string(
        fields["iam_service_credential"],
        "secrets.iam_service_credential",
    )
    password_source = _exact_string(
        fields["state_password_source"],
        "secrets.state_password_source",
    )
    return {
        "iam_service_credential": credential,
        "state_password_source": password_source,
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
            "runtime_id", "lifecycle_generation", "issued_at",
            "expires_at", "nonce", "signature",
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


def _encode_handle(value: BrokerAuthorityHandle) -> dict[str, object]:
    return {
        **value.signed_values(),
        "signature": encode_bytes(value.signature),
    }


def _decode_handle(value: object) -> BrokerAuthorityHandle:
    fields = require_object(
        value,
        fields={
            "broker_instance_id", "handle_id", "role", "runtime_id",
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
            "broker_instance_id", "operation", "request_fingerprint",
            "request_json", "result_json", "backend_decision",
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


def _wire_response(
    *,
    request_id: str,
    sequence: int,
    result: object = None,
    error: object = None,
) -> dict[str, object]:
    return {
        "version": WIRE_VERSION,
        "kind": "response",
        "request_id": request_id,
        "sequence": sequence,
        "ok": error is None,
        "result": result if error is None else None,
        "error": error,
    }


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
    *,
    credential_reference: str,
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
        credential_reference,
    ))


def _acquire_physical_domain_lease(
    config: AuthorityBrokerConfig,
    *,
    credential_reference: str,
) -> _PhysicalDomainLease:
    import portalocker

    identity = hashlib.sha256(
        _physical_state_domain(
            config,
            credential_reference=credential_reference,
        ).encode(),
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
