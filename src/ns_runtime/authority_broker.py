# -*- coding: utf-8 -*-
"""Spawn-isolated production IAM and StateStore authority broker.

The runtime process deliberately receives no production HTTP client, raw
StateStore, scope issuer, repository validator, signing key, or resource-policy
table.  It owns only a duplex IPC endpoint, broker public key, instance
identity, and signed least-privilege handles.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import multiprocessing
import os
import tempfile
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from multiprocessing.connection import Connection
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
    NsRuntimeStateStoreIndeterminateWriteError,
    NsRuntimeStateStoreUnavailableError,
    NsValidationError,
)
from ns_common.iam import (
    IamAccessCheckRequest,
    IamAccessDecision,
    IamCredentialStatus,
    IamIntrospectionRequest,
    IamIntrospectionResult,
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


_IAM_OPERATIONS = frozenset({
    "introspect",
    "runtime_access_check",
    "permission_snapshot",
    "payload_validate",
    "payload_revalidate",
})
_ROLE_OPERATIONS: Mapping[str, frozenset[str]] = {
    "admission": frozenset({"read_delivery", "transact_admission"}),
    "scheduler": frozenset({
        "read_delivery", "read_attempt", "read_summary",
        "read_scheduler_index", "transact_scheduler",
    }),
    "payload": frozenset({"read_payload_body"}),
    "registry": frozenset({"read_registry_layout"}),
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
    "transact_admission", "transact_scheduler", "append_audit",
})


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
    iam_service_credential: str
    iam_mode: str
    permission_snapshot_ttl_seconds: float
    state_backend: str
    state_endpoint: str
    state_username: str
    state_password_source: str
    state_namespace: str
    state_operation_timeout_seconds: float
    runtime_id: str

    def __post_init__(self) -> None:
        for name in (
            "iam_base_url",
            "iam_service_credential",
            "iam_mode",
            "state_backend",
            "state_endpoint",
            "state_username",
            "state_password_source",
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
            "iam_service_credential", "iam_mode", "state_namespace",
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
        "_closed", "_timeout_seconds",
    )

    def __init__(
        self,
        *,
        connection: Connection,
        process: multiprocessing.Process,
        public_key: bytes,
        instance_id: str,
        timeout_seconds: float,
    ) -> None:
        self._connection = connection
        self._process = process
        self._public_key = public_key
        self._instance_id = instance_id
        self._lock = threading.Lock()
        self._closed = False
        self._timeout_seconds = float(timeout_seconds)

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
        payload: object,
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
        message = {
            "kind": "request",
            "handle": handle,
            "operation": operation,
            "payload": payload,
        }
        try:
            with self._lock:
                self._connection.send(message)
                if not self._connection.poll(self._timeout_seconds):
                    self._closed = True
                    self._process.terminate()
                    self._connection.close()
                    self._process.join(timeout=5.0)
                    if operation in _WRITE_OPERATIONS:
                        raise NsRuntimeStateStoreIndeterminateWriteError(details={
                            "component": "authority_broker",
                            "operation": operation,
                            "reason": "ipc_timeout_outcome_unknown",
                        })
                    raise _broker_unavailable("ipc_timeout")
                response = self._connection.recv()
        except (BrokenPipeError, EOFError, OSError):
            self._closed = True
            if operation in _WRITE_OPERATIONS:
                raise NsRuntimeStateStoreIndeterminateWriteError(details={
                    "component": "authority_broker",
                    "operation": operation,
                    "reason": "ipc_outcome_unknown",
                }) from None
            raise _broker_unavailable("ipc_closed") from None
        if type(response) is not dict:
            raise _broker_unavailable("malformed_response")
        if response.get("ok") is True and set(response) == {"ok", "result"}:
            return response["result"]
        if response.get("ok") is False:
            _raise_remote_error(response)
        raise _broker_unavailable("malformed_response")

    def close(self, *, terminate: bool = False) -> None:
        if self._closed:
            return
        try:
            with self._lock:
                if self._process.is_alive() and not terminate:
                    self._connection.send({"kind": "shutdown"})
                    if self._connection.poll(5.0):
                        self._connection.recv()
        except (BrokenPipeError, EOFError, OSError):
            pass
        finally:
            self._closed = True
            try:
                self._connection.close()
            except OSError:
                pass
            self._process.join(timeout=5.0)
            if terminate and self._process.is_alive():
                self._process.terminate()
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
        substituted = {
            "authenticate", "access_check", "access_check_signed",
            "refresh_permission_snapshot", "validate_payload_ref",
            "revalidate_payload_ref",
        }.intersection(getattr(self, "__dict__", {}))
        return bool(
            type(self) is ProductionIamAuthorityProxy
            and type(getattr(self, "_channel", None)) is _BrokerChannel
            and type(getattr(self, "_handle", None)) is BrokerAuthorityHandle
            and self._handle.role is BrokerRepositoryRole.IAM
            and self._handle.verify(
                self._channel.public_key,
                instance_id=self._channel.instance_id,
            )
            and self._channel.alive
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
        if not self._is_production_adapter():
            channel = getattr(self, "_channel", None)
            handle = getattr(self, "_handle", None)
            if (
                type(self) is ProductionIamAuthorityProxy
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
        result = await asyncio.to_thread(
            self._channel.request,
            handle=self._handle,
            operation=operation,
            payload=payload,
        )
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

    async def read_delivery(
        self, *, tenant_id: str, bucket_id: int, layout_generation: int,
        delivery_id: str,
    ) -> StateReadResult:
        return await self._request("read_delivery", (
            tenant_id, bucket_id, layout_generation, delivery_id,
        ))  # type: ignore[return-value]

    async def transact_admission(
        self, *, tenant_id: str, bucket_id: int, layout_generation: int,
        transaction: StateTransaction,
    ) -> StateTransactionResult:
        return await self._request("transact_admission", (
            tenant_id, bucket_id, layout_generation, transaction,
        ))  # type: ignore[return-value]


class SchedulerRepositoryProxy(_RepositoryProxy):
    _ROLE = BrokerRepositoryRole.SCHEDULER

    async def read_delivery(
        self, *, tenant_id: str, bucket_id: int, layout_generation: int,
        delivery_id: str,
    ) -> StateReadResult:
        return await self._request("read_delivery", (
            tenant_id, bucket_id, layout_generation, delivery_id,
        ))  # type: ignore[return-value]

    async def read_attempt(
        self, *, tenant_id: str, bucket_id: int, layout_generation: int,
        attempt_id: str,
    ) -> StateReadResult:
        return await self._request("read_attempt", (
            tenant_id, bucket_id, layout_generation, attempt_id,
        ))  # type: ignore[return-value]

    async def read_summary(
        self, *, tenant_id: str, bucket_id: int, layout_generation: int,
        summary_id: str,
    ) -> StateReadResult:
        return await self._request("read_summary", (
            tenant_id, bucket_id, layout_generation, summary_id,
        ))  # type: ignore[return-value]

    async def read_scheduler_index(
        self, *, tenant_id: str, bucket_id: int, layout_generation: int,
        index_name: str, cursor: object = None, limit: int = 100,
    ) -> object:
        return await self._request("read_scheduler_index", (
            tenant_id, bucket_id, layout_generation,
            index_name, cursor, limit,
        ))

    async def transact_scheduler(
        self, *, tenant_id: str, bucket_id: int, layout_generation: int,
        transaction: StateTransaction,
    ) -> StateTransactionResult:
        return await self._request("transact_scheduler", (
            tenant_id, bucket_id, layout_generation, transaction,
        ))  # type: ignore[return-value]


class PayloadRepositoryProxy(_RepositoryProxy):
    _ROLE = BrokerRepositoryRole.PAYLOAD

    async def read_payload_body(
        self, *, tenant_id: str, bucket_id: int, layout_generation: int,
        object_id: str,
    ) -> StateReadResult:
        return await self._request("read_payload_body", (
            tenant_id, bucket_id, layout_generation, object_id,
        ))  # type: ignore[return-value]


class RegistryRepositoryProxy(_RepositoryProxy):
    _ROLE = BrokerRepositoryRole.REGISTRY

    async def read_registry_layout(self, *, object_id: str) -> StateReadResult:
        return await self._request(
            "read_registry_layout", object_id,
        )  # type: ignore[return-value]


class AuditRepositoryProxy(_RepositoryProxy):
    _ROLE = BrokerRepositoryRole.AUDIT

    async def append_audit(
        self, *, namespace: StateNamespace, object_id: str,
        document: StateDocument,
    ) -> object:
        return await self._request(
            "append_audit", (namespace, object_id, document),
        )


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
        result = await asyncio.to_thread(
            self._channel.request,
            handle=self._handle,
            operation="state_health",
            payload=None,
        )
        if type(result) is not StateStoreHealth:
            raise _state_unavailable("invalid_health")
        self._state = "open"

    async def health(self) -> StateStoreHealth:
        result = await asyncio.to_thread(
            self._channel.request,
            handle=self._handle,
            operation="state_health",
            payload=None,
        )
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
    *,
    config: AuthorityBrokerConfig,
    startup_timeout_seconds: float = 15.0,
) -> ProductionAuthorityBroker:
    """Spawn one isolated broker and return only narrow verified proxies."""

    if type(config) is not AuthorityBrokerConfig:
        _invalid("broker.config")
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe(duplex=True)
    process = context.Process(
        target=_authority_broker_process,
        args=(child, config),
        name="ns-runtime-authority-broker",
        daemon=False,
    )
    process.start()
    child.close()
    if not parent.poll(startup_timeout_seconds):
        process.terminate()
        process.join(timeout=5.0)
        parent.close()
        raise _broker_unavailable("startup_timeout")
    try:
        ready = parent.recv()
    except (EOFError, OSError):
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
    public_key = ready.get("public_key")
    instance_id = ready.get("instance_id")
    handles = ready.get("handles")
    if (
        type(public_key) is not bytes
        or type(instance_id) is not str
        or type(handles) is not dict
    ):
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

    iam = object.__new__(ProductionIamAuthorityProxy)
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

    def __init__(self, config: AuthorityBrokerConfig) -> None:
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
        self._credential = config.iam_service_credential
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
            or set(payload) != {"token", "claims"}
            or type(payload["token"]) is not str
        ):
            _invalid("broker.introspection_request")
        claims = payload["claims"]
        contract = IamIntrospectionRequest(
            token=payload["token"],
            component_type=claims.component_type,
            requested_capabilities=claims.requested_capabilities,
            protocol_version=str(claims.requested_version),
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
            or result.component_type != claims.component_type
            or not result.capabilities.issubset(claims.requested_capabilities)
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

        if type(payload) is not PermissionSnapshot:
            _invalid("broker.snapshot")
        data = await self._post("permission_snapshot", {
            "identity": payload.identity,
            "tenant_id": payload.tenant_id,
            "permission_snapshot_ref": payload.permission_snapshot_ref,
            "known_version": payload.permission_version,
            "component_type": payload.component_type,
            "capabilities": sorted(payload.capabilities),
            "expires_at": _iso(payload.expires_at),
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

    def __init__(self, config: AuthorityBrokerConfig) -> None:
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
            self._create_provider(config)
        except BaseException:
            self.lease.close()
            self.lease = None
            raise

    def _create_provider(self, config: AuthorityBrokerConfig) -> None:
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
            password_source=config.state_password_source,
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
            "read_payload_body",
        }:
            tenant, bucket, generation, object_id = _delivery_args(payload)
            object_type = {
                "read_delivery": "delivery",
                "read_attempt": "attempt",
                "read_summary": "summary",
                "read_payload_body": "payload_body",
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
        if operation in {"transact_admission", "transact_scheduler"}:
            tenant, bucket, generation, transaction = _transaction_args(payload)
            scope = repository.delivery_scope(
                tenant_id=tenant,
                bucket_id=bucket,
                layout_generation=generation,
            )
            if transaction.scope.namespace != scope.namespace:
                raise _state_denied("transaction_namespace_denied")
            rebound = StateTransaction(
                scope=scope,
                read_assertions=transaction.read_assertions,
                ordered_index_read_assertions=(
                    transaction.ordered_index_read_assertions
                ),
                mutations=transaction.mutations,
                ordered_index_mutations=transaction.ordered_index_mutations,
                log_appends=transaction.log_appends,
            )
            return await self.store.transact(rebound)
        if operation == "read_scheduler_index":
            if type(payload) is not tuple or len(payload) != 6:
                _invalid("broker.index_request")
            tenant, bucket, generation, name, cursor, limit = payload
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
            return await self.store.read_ordered_index(
                scope=scope,
                index=StateOrderedIndexKey(
                    namespace=scope.namespace,
                    name=name,
                    bucket="delivery",
                ),
                cursor=cursor,
                limit=limit,
            )
        if operation == "read_registry_layout":
            if type(payload) is not str or not payload:
                _invalid("broker.registry_request")
            scope = repository.registry_scope()
            return await self.store.read(
                scope=scope,
                key=StateKey(
                    namespace=scope.namespace,
                    object_type="delivery_authority_layout",
                    object_id=payload,
                ),
                consistency=StateConsistency.LINEARIZABLE,
            )
        if operation == "append_audit":
            if (
                type(payload) is not tuple
                or len(payload) != 3
                or type(payload[0]) is not StateNamespace
                or payload[0] != StateNamespace.audit(domain="processor")
                or type(payload[1]) is not str
                or not payload[1]
                or type(payload[2]) is not StateDocument
                or payload[2].schema_name != "runtime.processor_audit"
            ):
                raise _state_denied("audit_resource_denied")
            scope = repository.audit_scope()
            return await self.store.append(
                scope=scope,
                key=StateKey(
                    namespace=scope.namespace,
                    object_type="processor_audit_log",
                    object_id=payload[1],
                ),
                document=payload[2],
            )
        raise _state_denied("repository_operation_denied")


async def _broker_async_main(
    connection: Connection,
    config: AuthorityBrokerConfig,
) -> None:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    instance_id = "broker_" + uuid.uuid4().hex
    iam = _BrokerIamBackend(config)
    state = _BrokerStateBackend(config)
    sequence = 0
    generation = 1
    handles = {
        role.value: _new_handle(
            private_key=private_key,
            instance_id=instance_id,
            role=role,
            runtime_id=config.runtime_id,
            generation=generation,
        )
        for role in BrokerRepositoryRole
    }
    try:
        await state.open()
        connection.send({
            "ok": True,
            "instance_id": instance_id,
            "public_key": public_key,
            "handles": handles,
        })
        while True:
            try:
                message = await asyncio.to_thread(connection.recv)
            except (EOFError, OSError):
                break
            if type(message) is not dict:
                connection.send(_error_response("validation", "malformed_request"))
                continue
            if message.get("kind") == "shutdown":
                connection.send({"ok": True, "result": None})
                break
            if set(message) != {"kind", "handle", "operation", "payload"}:
                connection.send(_error_response("validation", "malformed_request"))
                continue
            handle = message["handle"]
            operation = message["operation"]
            payload = message["payload"]
            if (
                type(handle) is not BrokerAuthorityHandle
                or not handle.verify(public_key, instance_id=instance_id)
                or handle.lifecycle_generation != generation
                or handles.get(handle.role.value) != handle
                or type(operation) is not str
                or not _role_allows(handle.role, operation)
            ):
                connection.send(_error_response("state_denied", "handle_denied"))
                continue
            try:
                if handle.role is BrokerRepositoryRole.IAM:
                    typed_result = await iam.execute(operation, payload)
                    sequence += 1
                    result = _sign_iam_result(
                        private_key=private_key,
                        instance_id=instance_id,
                        operation=operation,
                        request=payload,
                        result=typed_result,
                        sequence=sequence,
                        ttl_seconds=config.permission_snapshot_ttl_seconds,
                    )
                else:
                    result = await state.execute(
                        role=handle.role,
                        operation=operation,
                        payload=payload,
                    )
            except BaseException as error:
                if not isinstance(error, Exception):
                    raise
                connection.send(_exception_response(error))
            else:
                connection.send({"ok": True, "result": result})
    finally:
        try:
            await state.close()
        finally:
            await iam.close()
            connection.close()


def _authority_broker_process(
    connection: Connection,
    config: AuthorityBrokerConfig,
) -> None:
    """Top-level spawn target.  All private authority is created below here."""

    try:
        _require_isolated_broker_process()
        asyncio.run(_broker_async_main(connection, config))
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
            connection.send({"ok": False, "reason": reason})
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
        if type(request) is not dict or set(request) != {"token", "claims"}:
            _invalid("broker.introspection_request")
        claims = request["claims"]
        return {
            "token_fingerprint": "sha256:" + hashlib.sha256(
                request["token"].encode(),
            ).hexdigest(),
            "component_type": claims.component_type,
            "requested_capabilities": sorted(
                claims.requested_capabilities,
            ),
            "protocol_version": str(claims.requested_version),
        }
    if operation == "permission_snapshot":
        if type(request) is not PermissionSnapshot:
            _invalid("broker.snapshot")
        return {
            "identity": request.identity,
            "tenant_id": request.tenant_id,
            "permission_snapshot_ref": request.permission_snapshot_ref,
            "permission_version": request.permission_version,
            "component_type": request.component_type,
            "capabilities": sorted(request.capabilities),
            "expires_at": _iso(request.expires_at),
        }
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


def _physical_state_domain(config: AuthorityBrokerConfig) -> str:
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
    credential_reference = config.state_password_source or "none"
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


def _delivery_args(payload: object) -> tuple[str, int, int, str]:
    if (
        type(payload) is not tuple
        or len(payload) != 4
        or type(payload[0]) is not str
        or not payload[0]
        or type(payload[1]) is not int
        or payload[1] < 0
        or type(payload[2]) is not int
        or payload[2] <= 0
        or type(payload[3]) is not str
        or not payload[3]
    ):
        _invalid("broker.delivery_request")
    return payload


def _require_isolated_broker_process() -> None:
    """Reject broker-private material in the ordinary runtime interpreter."""

    parent = multiprocessing.parent_process()
    if parent is None or parent.pid == os.getpid():
        _invalid("broker.os_isolation")


def _transaction_args(
    payload: object,
) -> tuple[str, int, int, StateTransaction]:
    if (
        type(payload) is not tuple
        or len(payload) != 4
        or type(payload[0]) is not str
        or not payload[0]
        or type(payload[1]) is not int
        or payload[1] < 0
        or type(payload[2]) is not int
        or payload[2] <= 0
        or type(payload[3]) is not StateTransaction
    ):
        _invalid("broker.transaction_request")
    return payload


def _parse_backend_result(parser: object, value: object) -> object:
    """Normalize malformed typed IAM payloads as an unavailable backend."""

    try:
        return parser(value)  # type: ignore[operator]
    except (NsValidationError, TypeError, ValueError):
        raise _broker_unavailable("malformed_backend_result") from None


def _exception_response(error: Exception) -> dict[str, object]:
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
    elif isinstance(error, NsValidationError):
        kind = "validation"
    else:
        kind = "state_unavailable"
    return {
        "ok": False,
        "error_kind": kind,
        "reason": str(details.get("reason", type(error).__name__)),
    }


def _error_response(kind: str, reason: str) -> dict[str, object]:
    return {"ok": False, "error_kind": kind, "reason": reason}


def _raise_remote_error(response: Mapping[str, object]) -> None:
    kind = response.get("error_kind")
    reason = str(response.get("reason", "remote_failure"))
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
    if kind == "validation":
        raise NsValidationError(
            "Authority broker request is invalid.",
            details=details,
        )
    raise NsRuntimeStateStoreUnavailableError(details=details)


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
)
