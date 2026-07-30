# -*- coding: utf-8 -*-
"""OS-isolated production authority attestation.

This module intentionally imports no runtime business package.  Its spawned
process owns the compiled production trust root, the approved broker identity,
and an attestor signing key.  The ordinary runtime receives only a bytes-only
RPC client and signed request tickets that the broker independently verifies.
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
import multiprocessing
import os
import sys
import threading
import uuid
from datetime import datetime, timedelta, timezone
from multiprocessing.connection import Connection
from typing import Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


ATTESTOR_WIRE_VERSION = 1
IAM_VERIFICATION_RECEIPT_WIRE_VERSION = 1
IAM_VERIFICATION_RECEIPT_KIND = "iam_verification_receipt"
ATTESTOR_MAX_FRAME_BYTES = 8 * 1024 * 1024
_MAX_STRING_CHARS = 2 * 1024 * 1024
_MAX_CONTAINER_ITEMS = 20_000
_MAX_DEPTH = 64
_PRODUCTION_ROOT_PUBLIC_KEY = bytes.fromhex(
    "bb664a4f556a411abe3f91fbde867461"
    "0338069f874a2281413c52332cdacfdf"
)
_ROLES = frozenset({
    "iam", "admission", "scheduler", "payload", "registry", "audit",
    "lifecycle",
})
_ROLE_OPERATIONS: Mapping[str, frozenset[str]] = {
    "iam": frozenset({
        "introspect", "runtime_access_check", "permission_snapshot",
        "payload_validate", "payload_revalidate",
    }),
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
    "audit": frozenset({
        "append_processor_audit",
        "append_connection_audit",
    }),
    "lifecycle": frozenset({"state_health"}),
}
_DELEGATION_USAGES = (
    "role-endpoints", "iam-results", "rotation", "state-responses",
)


class AuthorityAttestationError(RuntimeError):
    """Stable local failure without reflecting untrusted payload text."""


class _AttestorClock:
    """One explicit wall-clock dependency owned by the attestor child."""

    __slots__ = ()

    def utc_now(self) -> datetime:
        return datetime.now(timezone.utc)


class AuthorityAttestorClient:
    """Serialized client for one isolated attestor process."""

    __slots__ = (
        "_connection", "_process", "_public_key", "_instance_id", "_lock",
        "_closed", "_connection_closed", "_process_reaped", "_reaped",
        "_request_sequence", "_response_sequence", "_timeout_seconds",
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
        if (
            not isinstance(connection, Connection)
            or not process.is_alive()
            or type(public_key) is not bytes
            or len(public_key) != 32
            or type(instance_id) is not str
            or not instance_id
            or not math.isfinite(timeout_seconds)
            or timeout_seconds <= 0
        ):
            raise AuthorityAttestationError("attestor_client_invalid")
        self._connection = connection
        self._process = process
        self._public_key = public_key
        self._instance_id = instance_id
        self._lock = threading.Lock()
        self._closed = False
        self._connection_closed = False
        self._process_reaped = False
        self._reaped = False
        self._request_sequence = 0
        self._response_sequence = 0
        self._timeout_seconds = float(timeout_seconds)

    @property
    def instance_id(self) -> str:
        return self._instance_id

    @property
    def public_key(self) -> bytes:
        return bytes(self._public_key)

    @property
    def alive(self) -> bool:
        return bool(
            not self._closed
            and not self._reaped
            and self._process.is_alive()
        )

    def approve_identity(
        self,
        *,
        realm: str,
        runtime_id: str,
        delegation_certificate: dict[str, object],
        session_certificate: dict[str, object],
        handles: dict[str, object],
        endpoints: dict[str, object],
    ) -> dict[str, object]:
        return self._rpc("approve_identity", {
            "realm": realm,
            "runtime_id": runtime_id,
            "delegation_certificate": delegation_certificate,
            "session_certificate": session_certificate,
            "handles": handles,
            "endpoints": endpoints,
        })

    def verify_identity(
        self,
        *,
        identity_id: str,
        broker_instance_id: str,
        runtime_id: str,
        lifecycle_generation: int,
        session_key_fingerprint: str,
        certificate_fingerprint: str,
    ) -> dict[str, object]:
        return self._rpc("verify_identity", {
            "identity_id": identity_id,
            "broker_instance_id": broker_instance_id,
            "runtime_id": runtime_id,
            "lifecycle_generation": lifecycle_generation,
            "session_key_fingerprint": session_key_fingerprint,
            "certificate_fingerprint": certificate_fingerprint,
        })

    def prepare_request(
        self,
        *,
        identity_id: str,
        connection_generation: int,
        endpoint_id: str,
        role: str,
        operation: str,
        request_id: str,
        request_sequence: int,
        request_fingerprint: str,
    ) -> dict[str, object]:
        return self._rpc("prepare_request", {
            "identity_id": identity_id,
            "connection_generation": connection_generation,
            "endpoint_id": endpoint_id,
            "role": role,
            "operation": operation,
            "request_id": request_id,
            "request_sequence": request_sequence,
            "request_fingerprint": request_fingerprint,
        })

    def current_endpoint_identity(
        self,
        *,
        identity_id: str,
        endpoint_id: str,
        role: str,
    ) -> dict[str, object]:
        return self._rpc("current_endpoint_identity", {
            "identity_id": identity_id,
            "endpoint_id": endpoint_id,
            "role": role,
        })

    def approve_rotation(
        self,
        *,
        identity_id: str,
        rotation: dict[str, object],
    ) -> dict[str, object]:
        return self._rpc("approve_rotation", {
            "identity_id": identity_id,
            "rotation": rotation,
        })

    def verify_state_response(
        self,
        *,
        snapshot: dict[str, object],
        signed_response: dict[str, object],
    ) -> dict[str, object]:
        return self._rpc("verify_state_response", {
            "snapshot": snapshot,
            "signed_response": signed_response,
        })

    def verify_iam_result(
        self,
        *,
        identity_id: str,
        operation: str,
        request_fingerprint: str,
        signed_result: dict[str, object],
    ) -> dict[str, object]:
        return self._rpc("verify_iam_result", {
            "identity_id": identity_id,
            "operation": operation,
            "request_fingerprint": request_fingerprint,
            "signed_result": signed_result,
        })

    def _rpc(
        self,
        operation: str,
        payload: dict[str, object],
    ) -> dict[str, object]:
        if self._closed or not self._process.is_alive():
            self._fail_and_reap()
            raise AuthorityAttestationError("attestor_unavailable")
        with self._lock:
            if self._closed or not self._process.is_alive():
                self._fail_and_reap()
                raise AuthorityAttestationError("attestor_unavailable")
            request_id = "attest_" + uuid.uuid4().hex
            request_sequence = self._request_sequence + 1
            raw = _encode_frame({
                "version": ATTESTOR_WIRE_VERSION,
                "kind": "attestor_request",
                "request_id": request_id,
                "request_sequence": request_sequence,
                "operation": operation,
                "payload": payload,
            })
            self._request_sequence = request_sequence
            try:
                self._connection.send_bytes(raw)
                if not self._connection.poll(self._timeout_seconds):
                    raise AuthorityAttestationError("attestor_timeout")
                response = _decode_frame(
                    self._connection.recv_bytes(ATTESTOR_MAX_FRAME_BYTES),
                )
                expected_sequence = self._response_sequence + 1
                result = _verify_attestor_response(
                    response,
                    public_key=self._public_key,
                    attestor_instance_id=self._instance_id,
                    request_id=request_id,
                    request_sequence=request_sequence,
                    expected_response_sequence=expected_sequence,
                )
                self._response_sequence = expected_sequence
                return result
            except (
                BrokenPipeError, EOFError, OSError, ValueError,
                AuthorityAttestationError,
            ):
                self._fail_and_reap()
                raise AuthorityAttestationError(
                    "attestor_verification_failed",
                ) from None

    def close(self) -> None:
        if not self._closed:
            try:
                with self._lock:
                    if self._process.is_alive():
                        self._connection.send_bytes(_encode_frame({
                            "version": ATTESTOR_WIRE_VERSION,
                            "kind": "shutdown",
                        }))
                        if self._connection.poll(2.0):
                            self._connection.recv_bytes(
                                ATTESTOR_MAX_FRAME_BYTES,
                            )
            except (BrokenPipeError, EOFError, OSError, ValueError):
                pass
        self._closed = True
        self._reap()

    def _fail_and_reap(self) -> None:
        self._closed = True
        self._reap()

    def _reap(self) -> None:
        if self._reaped:
            return
        failure: BaseException | None = None
        if not self._connection_closed:
            try:
                self._connection.close()
            except BaseException as error:
                failure = _prioritize_cleanup_failure(failure, error)
            else:
                self._connection_closed = True
        if not self._process_reaped:
            for operation, timeout in (
                ("join", 0.2),
                ("terminate", 2.0),
                ("kill", 2.0),
            ):
                try:
                    if operation == "join":
                        self._process.join(timeout=timeout)
                    elif self._process.is_alive():
                        getattr(self._process, operation)()
                        self._process.join(timeout=timeout)
                except BaseException as error:
                    failure = _prioritize_cleanup_failure(failure, error)
            try:
                process_alive = self._process.is_alive()
            except BaseException as error:
                failure = _prioritize_cleanup_failure(failure, error)
                process_alive = True
            if process_alive:
                failure = _prioritize_cleanup_failure(
                    failure,
                    AuthorityAttestationError(
                        "attestor_process_did_not_exit",
                    ),
                )
            else:
                self._process_reaped = True
        self._reaped = self._connection_closed and self._process_reaped
        if failure is not None:
            raise failure


def _prioritize_cleanup_failure(
    current: BaseException | None,
    candidate: BaseException,
) -> BaseException:
    if current is None:
        return candidate
    if isinstance(current, Exception) and not isinstance(candidate, Exception):
        return candidate
    if (
        isinstance(current, Exception)
        and type(candidate) is AuthorityAttestationError
        and candidate.args == ("attestor_process_did_not_exit",)
    ):
        return candidate
    return current


def start_authority_attestor(
    *,
    realm: str,
    expected_test_root_public_key: bytes | None = None,
    timeout_seconds: float = 5.0,
) -> AuthorityAttestorClient:
    """Start production attestor or an explicitly separate test attestor."""

    if realm not in {"production", "contract-test", "integration-test"}:
        raise AuthorityAttestationError("attestor_realm_invalid")
    if realm == "production":
        test_root = b""
    elif (
        type(expected_test_root_public_key) is not bytes
        or len(expected_test_root_public_key) != 32
    ):
        raise AuthorityAttestationError("attestor_test_root_invalid")
    else:
        test_root = expected_test_root_public_key
    context = multiprocessing.get_context("spawn")
    from ns_runtime.authority_bootstrap import (
        _AuthorityStartupCleanupOwner,
        _close_connections,
        _raise_startup_cleanup_failure,
    )

    connections: dict[str, Connection] = {}
    process: multiprocessing.Process | None = None
    process_start_attempted = False
    transferred = False
    cleanup_owner = _AuthorityStartupCleanupOwner(
        connections=(connections,),
    )
    try:
        parent, child = context.Pipe(duplex=True)
        connections["parent"] = parent
        connections["child"] = child
        process = context.Process(
            target=_authority_attestor_process,
            args=(child, realm, test_root),
            name=f"ns-runtime-authority-attestor-{realm}",
            daemon=False,
        )
        cleanup_owner.process = process
        process_start_attempted = True
        cleanup_owner.process_start_attempted = True
        process.start()
        child_failure = _close_connections({
            "child": connections["child"],
        })
        if child_failure is not None:
            raise child_failure
        connections.pop("child", None)
        if not parent.poll(timeout_seconds):
            raise AuthorityAttestationError("attestor_startup_timeout")
        ready = _decode_frame(
            parent.recv_bytes(ATTESTOR_MAX_FRAME_BYTES),
        )
        fields = _require_object(
            ready,
            {
                "version", "kind", "attestor_instance_id",
                "attestor_public_key",
            },
        )
        if (
            fields["version"] != ATTESTOR_WIRE_VERSION
            or fields["kind"] != "attestor_ready"
        ):
            raise AuthorityAttestationError("attestor_ready_invalid")
        instance_id = _string(
            fields["attestor_instance_id"],
        )
        public_key = _decode_bytes(fields["attestor_public_key"])
        client = AuthorityAttestorClient(
            connection=parent,
            process=process,
            public_key=public_key,
            instance_id=instance_id,
            timeout_seconds=timeout_seconds,
        )
        transferred = True
        cleanup_owner.process = None
        return client
    finally:
        if not transferred:
            active_failure = sys.exc_info()[1]
            cleanup_failure: BaseException | None = None
            try:
                cleanup_owner.close()
            except BaseException as error:
                cleanup_failure = error
            _raise_startup_cleanup_failure(
                cleanup_owner,
                operation_failure=active_failure,
                cleanup_failure=cleanup_failure,
            )


def _authority_attestor_process(
    connection: Connection,
    realm: str,
    expected_test_root_public_key: bytes,
) -> None:
    """Spawn target with no imports from processor/delivery/routing/plugin."""

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    instance_id = "attestor_" + uuid.uuid4().hex
    root_public_key = (
        _PRODUCTION_ROOT_PUBLIC_KEY
        if realm == "production"
        else expected_test_root_public_key
    )
    approved: dict[str, object] | None = None
    pending_rotation: dict[str, object] | None = None
    request_sequence = 0
    response_sequence = 0
    clock = _AttestorClock()
    try:
        connection.send_bytes(_encode_frame({
            "version": ATTESTOR_WIRE_VERSION,
            "kind": "attestor_ready",
            "attestor_instance_id": instance_id,
            "attestor_public_key": _encode_bytes(public_key),
        }))
        while True:
            request_id = "invalid"
            try:
                message = _decode_frame(
                    connection.recv_bytes(ATTESTOR_MAX_FRAME_BYTES),
                )
            except (EOFError, OSError, ValueError):
                break
            if message == {
                "version": ATTESTOR_WIRE_VERSION,
                "kind": "shutdown",
            }:
                connection.send_bytes(_encode_frame({
                    "version": ATTESTOR_WIRE_VERSION,
                    "kind": "shutdown_complete",
                }))
                break
            try:
                fields = _require_object(message, {
                    "version", "kind", "request_id", "request_sequence",
                    "operation", "payload",
                })
                incoming_sequence = _positive_int(
                    fields["request_sequence"],
                )
                if (
                    fields["version"] != ATTESTOR_WIRE_VERSION
                    or fields["kind"] != "attestor_request"
                    or incoming_sequence != request_sequence + 1
                ):
                    raise ValueError
                request_sequence = incoming_sequence
                request_id = _string(fields["request_id"])
                operation = _string(fields["operation"])
                payload = _require_object_value(fields["payload"])
                result, approved, pending_rotation = _execute_attestation(
                    operation=operation,
                    payload=payload,
                    realm=realm,
                    root_public_key=root_public_key,
                    attestor_private_key=private_key,
                    attestor_instance_id=instance_id,
                    approved=approved,
                    pending_rotation=pending_rotation,
                    now=clock.utc_now(),
                )
                ok = True
                error = None
            except (ValueError, InvalidSignature, TypeError):
                result = None
                ok = False
                error = {"kind": "attestation_denied"}
            response_sequence += 1
            response_values = {
                "attestor_instance_id": instance_id,
                "request_id": request_id,
                "request_sequence": request_sequence,
                "response_sequence": response_sequence,
                "ok": ok,
                "result": result,
                "error": error,
            }
            connection.send_bytes(_encode_frame({
                "version": ATTESTOR_WIRE_VERSION,
                "kind": "attestor_response",
                **response_values,
                "signature": _encode_bytes(
                    private_key.sign(_canonical(response_values)),
                ),
            }))
    finally:
        try:
            connection.close()
        except OSError:
            pass


def _execute_attestation(
    *,
    operation: str,
    payload: dict[str, object],
    realm: str,
    root_public_key: bytes,
    attestor_private_key: Ed25519PrivateKey,
    attestor_instance_id: str,
    approved: dict[str, object] | None,
    pending_rotation: dict[str, object] | None,
    now: datetime,
) -> tuple[dict[str, object], dict[str, object] | None, dict[str, object] | None]:
    if operation == "approve_identity":
        if approved is not None:
            raise ValueError
        fields = _require_exact(payload, {
            "realm", "runtime_id", "delegation_certificate",
            "session_certificate", "handles", "endpoints",
        })
        if _string(fields["realm"]) != realm:
            raise ValueError
        approved = _verify_identity_bundle(
            realm=realm,
            expected_runtime_id=_string(fields["runtime_id"]),
            root_public_key=root_public_key,
            delegation=_require_object_value(
                fields["delegation_certificate"],
            ),
            session=_require_object_value(fields["session_certificate"]),
            handles=_require_object_value(fields["handles"]),
            endpoints=_require_object_value(fields["endpoints"]),
            attestor_instance_id=attestor_instance_id,
            attestor_public_key=attestor_private_key.public_key().public_bytes(
                serialization.Encoding.Raw,
                serialization.PublicFormat.Raw,
            ),
            now=now,
        )
        return _identity_result(approved), approved, None
    if approved is None:
        raise ValueError
    if operation == "verify_identity":
        fields = _require_exact(payload, {
            "identity_id", "broker_instance_id", "runtime_id",
            "lifecycle_generation", "session_key_fingerprint",
            "certificate_fingerprint",
        })
        _require_identity_fields(approved, fields)
        return {
            **_identity_result(approved),
            "rotation_required": _rotation_required(approved, now),
        }, approved, pending_rotation
    if operation == "prepare_request":
        fields = _require_exact(payload, {
            "identity_id", "connection_generation", "endpoint_id", "role",
            "operation", "request_id", "request_sequence",
            "request_fingerprint",
        })
        if _string(fields["identity_id"]) != approved["identity_id"]:
            raise ValueError
        role = _string(fields["role"])
        endpoint_id = _string(fields["endpoint_id"])
        _require_endpoint(approved, endpoint_id=endpoint_id, role=role)
        handle = _require_object_value(
            _require_object_value(approved["handles"])[role],
        )
        requested_operation = _string(fields["operation"])
        if requested_operation not in _ROLE_OPERATIONS[role]:
            raise ValueError
        if _rotation_required(approved, now):
            if pending_rotation is None:
                ticket_values = {
                    "attestor_instance_id": attestor_instance_id,
                    "identity_id": approved["identity_id"],
                    "broker_instance_id": approved["broker_instance_id"],
                    "runtime_id": approved["runtime_id"],
                    "endpoint_id": endpoint_id,
                    "role": role,
                    "current_generation": approved["lifecycle_generation"],
                    "next_generation": (
                        int(approved["lifecycle_generation"]) + 1
                    ),
                    "issued_at": _encode_time(now),
                    "expires_at": _encode_time(
                        now + timedelta(seconds=30),
                    ),
                    "nonce": uuid.uuid4().hex,
                }
                pending_rotation = {
                    **ticket_values,
                    "signature": _encode_bytes(
                        attestor_private_key.sign(
                            _canonical(ticket_values),
                        ),
                    ),
                }
            elif (
                pending_rotation["endpoint_id"] != endpoint_id
                or pending_rotation["role"] != role
            ):
                return {
                    "status": "rotation_in_progress",
                    "lifecycle_generation": approved[
                        "lifecycle_generation"
                    ],
                }, approved, pending_rotation
            return {
                "status": "rotation_required",
                "rotation_ticket": pending_rotation,
            }, approved, pending_rotation
        ticket_values = {
            "attestor_instance_id": attestor_instance_id,
            "identity_id": approved["identity_id"],
            "broker_instance_id": approved["broker_instance_id"],
            "runtime_id": approved["runtime_id"],
            "lifecycle_generation": approved["lifecycle_generation"],
            "session_key_fingerprint": approved[
                "session_key_fingerprint"
            ],
            "certificate_fingerprint": approved[
                "certificate_fingerprint"
            ],
            "connection_generation": _positive_int(
                fields["connection_generation"],
            ),
            "endpoint_id": endpoint_id,
            "handle_id": _string(handle["handle_id"]),
            "role": role,
            "operation": requested_operation,
            "request_id": _string(fields["request_id"]),
            "request_sequence": _positive_int(
                fields["request_sequence"],
            ),
            "request_fingerprint": _string(
                fields["request_fingerprint"],
            ),
            "issued_at": _encode_time(now),
            "expires_at": _encode_time(now + timedelta(seconds=30)),
            "nonce": uuid.uuid4().hex,
        }
        return {
            "status": "ready",
            "endpoint_identity": _endpoint_identity_result(
                approved, endpoint_id=endpoint_id, role=role,
            ),
            "ticket": {
                **ticket_values,
                "signature": _encode_bytes(
                    attestor_private_key.sign(_canonical(ticket_values)),
                ),
            },
        }, approved, pending_rotation
    if operation == "current_endpoint_identity":
        fields = _require_exact(payload, {
            "identity_id", "endpoint_id", "role",
        })
        if _string(fields["identity_id"]) != approved["identity_id"]:
            raise ValueError
        endpoint_id = _string(fields["endpoint_id"])
        role = _string(fields["role"])
        _require_endpoint(approved, endpoint_id=endpoint_id, role=role)
        return _endpoint_identity_result(
            approved, endpoint_id=endpoint_id, role=role,
        ), approved, pending_rotation
    if operation == "approve_rotation":
        fields = _require_exact(payload, {"identity_id", "rotation"})
        if (
            _string(fields["identity_id"]) != approved["identity_id"]
            or pending_rotation is None
        ):
            raise ValueError
        rotation = _require_object_value(fields["rotation"])
        approved = _verify_rotation(
            approved=approved,
            pending_ticket=pending_rotation,
            rotation=rotation,
            now=now,
        )
        return _identity_result(approved), approved, None
    if operation == "verify_state_response":
        fields = _require_exact(
            payload, {"snapshot", "signed_response"},
        )
        snapshot = _require_object_value(fields["snapshot"])
        _require_snapshot(approved, snapshot)
        response = _require_object_value(fields["signed_response"])
        result = _verify_state_response(
            approved=approved,
            snapshot=snapshot,
            response=response,
            now=now,
        )
        return result, approved, pending_rotation
    if operation == "verify_iam_result":
        fields = _require_exact(payload, {
            "identity_id", "operation", "request_fingerprint",
            "signed_result",
        })
        if _string(fields["identity_id"]) != approved["identity_id"]:
            raise ValueError
        result = _verify_iam_result(
            approved=approved,
            operation=_string(fields["operation"]),
            request_fingerprint=_string(
                fields["request_fingerprint"],
            ),
            signed_result=_require_object_value(
                fields["signed_result"],
            ),
            attestor_private_key=attestor_private_key,
            attestor_instance_id=attestor_instance_id,
            now=now,
        )
        return result, approved, pending_rotation
    raise ValueError


def _verify_identity_bundle(
    *,
    realm: str,
    expected_runtime_id: str,
    root_public_key: bytes,
    delegation: dict[str, object],
    session: dict[str, object],
    handles: dict[str, object],
    endpoints: dict[str, object],
    attestor_instance_id: str,
    attestor_public_key: bytes,
    now: datetime,
) -> dict[str, object]:
    delegation_values = _without_signature(delegation, {
        "trust_realm", "broker_instance_id", "runtime_id",
        "delegation_public_key", "attestor_instance_id",
        "attestor_public_key", "allowed_usages", "issued_at",
        "expires_at", "nonce", "signature",
    })
    usages = delegation_values["allowed_usages"]
    if (
        delegation_values["trust_realm"] != realm
        or delegation_values["runtime_id"] != expected_runtime_id
        or delegation_values["attestor_instance_id"]
        != attestor_instance_id
        or _decode_bytes(delegation_values["attestor_public_key"])
        != attestor_public_key
        or usages != list(_DELEGATION_USAGES)
    ):
        raise ValueError
    delegation_public_key = _decode_bytes(
        delegation_values["delegation_public_key"],
    )
    issued_at = _decode_time(delegation_values["issued_at"])
    delegation_expiry = _decode_time(delegation_values["expires_at"])
    if not issued_at <= now < delegation_expiry:
        raise ValueError
    _verify_signature(
        root_public_key,
        _canonical(delegation_values),
        _decode_bytes(delegation["signature"]),
    )
    delegation_fingerprint = _fingerprint(delegation)
    session_values = _without_signature(session, {
        "trust_realm", "broker_instance_id", "session_public_key",
        "runtime_id", "lifecycle_generation", "delegation_fingerprint",
        "issued_at", "expires_at", "nonce", "signature",
    })
    if (
        session_values["trust_realm"] != realm
        or session_values["broker_instance_id"]
        != delegation_values["broker_instance_id"]
        or session_values["runtime_id"] != expected_runtime_id
        or session_values["delegation_fingerprint"]
        != delegation_fingerprint
        or _positive_int(session_values["lifecycle_generation"]) != 1
    ):
        raise ValueError
    session_public_key = _decode_bytes(
        session_values["session_public_key"],
    )
    session_issued = _decode_time(session_values["issued_at"])
    session_expiry = _decode_time(session_values["expires_at"])
    if (
        not issued_at <= session_issued <= now < session_expiry
        or session_expiry > delegation_expiry
    ):
        raise ValueError
    _verify_signature(
        delegation_public_key,
        _canonical(session_values),
        _decode_bytes(session["signature"]),
    )
    approved = {
        "identity_id": "identity:" + hashlib.sha256(
            _canonical({
                "delegation_fingerprint": delegation_fingerprint,
                "broker_instance_id": session_values[
                    "broker_instance_id"
                ],
                "runtime_id": expected_runtime_id,
            }),
        ).hexdigest(),
        "realm": realm,
        "broker_instance_id": session_values["broker_instance_id"],
        "runtime_id": expected_runtime_id,
        "delegation": delegation,
        "delegation_public_key": delegation_public_key,
        "delegation_expires_at": delegation_expiry,
        "lifecycle_generation": 1,
        "session_public_key": session_public_key,
        "session_key_fingerprint": _key_fingerprint(session_public_key),
        "certificate_fingerprint": _fingerprint(session),
        "session_issued_at": session_issued,
        "session_expires_at": session_expiry,
        "handles": handles,
        "endpoints": endpoints,
        "session": session,
        "attestor_instance_id": attestor_instance_id,
        "attestor_public_key": attestor_public_key,
    }
    _verify_endpoints(endpoints)
    _verify_all_handles(handles, approved)
    return approved


def _verify_rotation(
    *,
    approved: dict[str, object],
    pending_ticket: dict[str, object],
    rotation: dict[str, object],
    now: datetime,
) -> dict[str, object]:
    fields = _without_signature(rotation, {
        "kind", "ticket_nonce", "delegation_fingerprint",
        "session_certificate", "handles", "signature",
    })
    if (
        fields["kind"] != "session_rotation"
        or fields["ticket_nonce"] != pending_ticket["nonce"]
        or fields["delegation_fingerprint"]
        != _fingerprint(approved["delegation"])
    ):
        raise ValueError
    _verify_signature(
        approved["delegation_public_key"],
        _canonical(fields),
        _decode_bytes(rotation["signature"]),
    )
    session = _require_object_value(fields["session_certificate"])
    session_values = _without_signature(session, {
        "trust_realm", "broker_instance_id", "session_public_key",
        "runtime_id", "lifecycle_generation", "delegation_fingerprint",
        "issued_at", "expires_at", "nonce", "signature",
    })
    next_generation = int(approved["lifecycle_generation"]) + 1
    if (
        session_values["trust_realm"] != approved["realm"]
        or session_values["broker_instance_id"]
        != approved["broker_instance_id"]
        or session_values["runtime_id"] != approved["runtime_id"]
        or session_values["delegation_fingerprint"]
        != _fingerprint(approved["delegation"])
        or _positive_int(session_values["lifecycle_generation"])
        != next_generation
    ):
        raise ValueError
    issued_at = _decode_time(session_values["issued_at"])
    expires_at = _decode_time(session_values["expires_at"])
    if (
        issued_at > now
        or expires_at <= now
        or expires_at > approved["delegation_expires_at"]
    ):
        raise ValueError
    session_public_key = _decode_bytes(
        session_values["session_public_key"],
    )
    _verify_signature(
        approved["delegation_public_key"],
        _canonical(session_values),
        _decode_bytes(session["signature"]),
    )
    updated = {
        **approved,
        "lifecycle_generation": next_generation,
        "session_public_key": session_public_key,
        "session_key_fingerprint": _key_fingerprint(session_public_key),
        "certificate_fingerprint": _fingerprint(session),
        "session_issued_at": issued_at,
        "session_expires_at": expires_at,
        "handles": _require_object_value(fields["handles"]),
        "session": session,
    }
    _verify_all_handles(updated["handles"], updated)
    return updated


def _verify_state_response(
    *,
    approved: dict[str, object],
    snapshot: dict[str, object],
    response: dict[str, object],
    now: datetime,
) -> dict[str, object]:
    response_values = _without_signature(response, {
        "broker_instance_id", "lifecycle_generation",
        "session_key_fingerprint", "request_id", "request_sequence",
        "operation", "handle_id", "role", "request_fingerprint",
        "ok", "result_json", "error_json", "response_sequence",
        "issued_at", "nonce", "signature",
    })
    for response_name, snapshot_name in (
        ("broker_instance_id", "broker_instance_id"),
        ("lifecycle_generation", "lifecycle_generation"),
        ("session_key_fingerprint", "session_key_fingerprint"),
        ("request_id", "request_id"),
        ("request_sequence", "request_sequence"),
        ("operation", "operation"),
        ("handle_id", "handle_id"),
        ("role", "role"),
        ("request_fingerprint", "request_fingerprint"),
        ("response_sequence", "expected_response_sequence"),
    ):
        if response_values[response_name] != snapshot[snapshot_name]:
            raise ValueError
    issued_at = _decode_time(response_values["issued_at"])
    if (
        type(response_values["ok"]) is not bool
        or not approved["session_issued_at"] <= issued_at <= now
        or now >= approved["session_expires_at"]
        or (
            response_values["ok"]
            and response_values["error_json"] != "null"
        )
        or (
            not response_values["ok"]
            and response_values["result_json"] != "null"
        )
    ):
        raise ValueError
    _verify_signature(
        approved["session_public_key"],
        _canonical(response_values),
        _decode_bytes(response["signature"]),
    )
    return {
        "ok": response_values["ok"],
        "result_json": _canonical_json_string(
            response_values["result_json"],
        ),
        "error_json": _canonical_json_string(
            response_values["error_json"],
        ),
        "response_sequence": _positive_int(
            response_values["response_sequence"],
        ),
    }


def _verify_iam_result(
    *,
    approved: dict[str, object],
    operation: str,
    request_fingerprint: str,
    signed_result: dict[str, object],
    attestor_private_key: Ed25519PrivateKey,
    attestor_instance_id: str,
    now: datetime,
) -> dict[str, object]:
    values = _without_signature(signed_result, {
        "broker_instance_id", "lifecycle_generation",
        "session_key_fingerprint", "operation", "request_fingerprint",
        "request_json", "result_json", "backend_decision",
        "permission_snapshot_ref", "permission_version", "tenant_id",
        "target", "message_type", "issued_at", "expires_at", "sequence",
        "nonce", "signature",
    })
    if (
        values["broker_instance_id"] != approved["broker_instance_id"]
        or values["lifecycle_generation"]
        != approved["lifecycle_generation"]
        or values["session_key_fingerprint"]
        != approved["session_key_fingerprint"]
        or values["operation"] != operation
        or values["request_fingerprint"] != request_fingerprint
    ):
        raise ValueError
    issued_at = _decode_time(values["issued_at"])
    expires_at = _decode_time(values["expires_at"])
    if (
        not approved["session_issued_at"] <= issued_at <= now < expires_at
        or expires_at > approved["session_expires_at"]
    ):
        raise ValueError
    _verify_signature(
        approved["session_public_key"],
        _canonical(values),
        _decode_bytes(signed_result["signature"]),
    )
    result_json = _canonical_json_string(values["result_json"])
    request_json = _canonical_json_string(values["request_json"])
    receipt_values = {
        "version": IAM_VERIFICATION_RECEIPT_WIRE_VERSION,
        "kind": IAM_VERIFICATION_RECEIPT_KIND,
        "attestor_instance_id": attestor_instance_id,
        "attestor_identity_id": approved["identity_id"],
        "broker_instance_id": approved["broker_instance_id"],
        "runtime_id": approved["runtime_id"],
        "lifecycle_generation": approved["lifecycle_generation"],
        "session_key_fingerprint": approved["session_key_fingerprint"],
        "endpoint_id": _string(
            _require_object_value(approved["endpoints"])["iam"],
        ),
        "role": "iam",
        "operation": operation,
        "request_fingerprint": request_fingerprint,
        "signed_result_fingerprint": _fingerprint(signed_result),
        "result_fingerprint": _fingerprint(
            _decode_frame(result_json.encode("utf-8")),
        ),
        "request_json_fingerprint": _fingerprint(
            _decode_frame(request_json.encode("utf-8")),
        ),
        "verified_at": _encode_time(now),
        "authority_expires_at": _encode_time(expires_at),
        "nonce": uuid.uuid4().hex,
    }
    return {
        **receipt_values,
        "signature": _encode_bytes(
            attestor_private_key.sign(_canonical(receipt_values)),
        ),
    }


def _require_identity_fields(
    approved: dict[str, object],
    fields: dict[str, object],
) -> None:
    for name in (
        "identity_id", "broker_instance_id", "runtime_id",
        "lifecycle_generation", "session_key_fingerprint",
        "certificate_fingerprint",
    ):
        if fields[name] != approved[name]:
            raise ValueError


def _require_snapshot(
    approved: dict[str, object],
    snapshot: dict[str, object],
) -> None:
    required = {
        "identity_id", "connection_generation", "broker_instance_id",
        "runtime_id", "lifecycle_generation", "session_key_fingerprint",
        "certificate_fingerprint", "endpoint_id", "handle_id", "role", "operation",
        "request_id", "request_sequence", "request_fingerprint",
        "expected_response_sequence",
    }
    fields = _require_exact(snapshot, required)
    for name in (
        "identity_id", "broker_instance_id", "runtime_id",
        "lifecycle_generation", "session_key_fingerprint",
        "certificate_fingerprint",
    ):
        if fields[name] != approved[name]:
            raise ValueError
    role = _string(fields["role"])
    _require_endpoint(
        approved,
        endpoint_id=_string(fields["endpoint_id"]),
        role=role,
    )
    handle = _require_object_value(approved["handles"])[role]
    if _require_object_value(handle)["handle_id"] != fields["handle_id"]:
        raise ValueError
    if _string(fields["operation"]) not in _ROLE_OPERATIONS[role]:
        raise ValueError


def _verify_all_handles(
    handles: object,
    approved: dict[str, object],
) -> None:
    values = _require_object_value(handles)
    if set(values) != _ROLES:
        raise ValueError
    for role in _ROLES:
        handle = _require_object_value(values[role])
        _verify_handle(handle, approved)
        if handle["role"] != role:
            raise ValueError
        endpoint = _require_object_value(approved["endpoints"])[role]
        if handle["endpoint_id"] != endpoint:
            raise ValueError


def _verify_handle(
    handle: dict[str, object],
    approved: dict[str, object],
) -> None:
    values = _without_signature(handle, {
        "broker_instance_id", "endpoint_id", "handle_id", "role", "runtime_id",
        "lifecycle_generation", "signature",
    })
    if (
        values["broker_instance_id"] != approved["broker_instance_id"]
        or values["runtime_id"] != approved["runtime_id"]
        or _require_object_value(approved["endpoints"]).get(
            _string(values["role"]),
        ) != values["endpoint_id"]
        or values["lifecycle_generation"]
        != approved["lifecycle_generation"]
        or values["role"] not in _ROLES
    ):
        raise ValueError
    _verify_signature(
        approved["session_public_key"],
        _canonical(values),
        _decode_bytes(handle["signature"]),
    )
    current = _require_object_value(approved["handles"]).get(
        _string(values["role"]),
    )
    if current is not None and current != handle:
        raise ValueError


def _rotation_required(
    approved: dict[str, object],
    now: datetime,
) -> bool:
    issued_at = approved["session_issued_at"]
    expires_at = approved["session_expires_at"]
    lifetime = (expires_at - issued_at).total_seconds()
    margin = max(0.05, min(60.0, lifetime / 3.0))
    return now + timedelta(seconds=margin) >= expires_at


def _identity_result(approved: dict[str, object]) -> dict[str, object]:
    return {
        "identity_id": approved["identity_id"],
        "realm": approved["realm"],
        "broker_instance_id": approved["broker_instance_id"],
        "runtime_id": approved["runtime_id"],
        "lifecycle_generation": approved["lifecycle_generation"],
        "session_key_fingerprint": approved["session_key_fingerprint"],
        "certificate_fingerprint": approved["certificate_fingerprint"],
        "session_expires_at": _encode_time(
            approved["session_expires_at"],
        ),
    }


def _endpoint_identity_result(
    approved: dict[str, object],
    *,
    endpoint_id: str,
    role: str,
) -> dict[str, object]:
    _require_endpoint(approved, endpoint_id=endpoint_id, role=role)
    return {
        **_identity_result(approved),
        "endpoint_id": endpoint_id,
        "role": role,
        "session_certificate": approved["session"],
        "handle": _require_object_value(approved["handles"])[role],
    }


def _verify_endpoints(endpoints: object) -> None:
    values = _require_object_value(endpoints)
    if set(values) != _ROLES:
        raise ValueError
    seen: set[str] = set()
    for role in _ROLES:
        endpoint_id = _string(values[role])
        if endpoint_id in seen:
            raise ValueError
        seen.add(endpoint_id)


def _require_endpoint(
    approved: dict[str, object],
    *,
    endpoint_id: str,
    role: str,
) -> None:
    if (
        role not in _ROLES
        or _require_object_value(approved["endpoints"]).get(role)
        != endpoint_id
    ):
        raise ValueError


def _verify_attestor_response(
    value: object,
    *,
    public_key: bytes,
    attestor_instance_id: str,
    request_id: str,
    request_sequence: int,
    expected_response_sequence: int,
) -> dict[str, object]:
    fields = _require_object(value, {
        "version", "kind", "attestor_instance_id", "request_id",
        "request_sequence", "response_sequence", "ok", "result",
        "error", "signature",
    })
    signed_values = {
        "attestor_instance_id": fields["attestor_instance_id"],
        "request_id": fields["request_id"],
        "request_sequence": fields["request_sequence"],
        "response_sequence": fields["response_sequence"],
        "ok": fields["ok"],
        "result": fields["result"],
        "error": fields["error"],
    }
    if (
        fields["version"] != ATTESTOR_WIRE_VERSION
        or fields["kind"] != "attestor_response"
        or fields["attestor_instance_id"] != attestor_instance_id
        or fields["request_id"] != request_id
        or fields["request_sequence"] != request_sequence
        or fields["response_sequence"] != expected_response_sequence
        or type(fields["ok"]) is not bool
    ):
        raise AuthorityAttestationError("attestor_response_binding")
    _verify_signature(
        public_key,
        _canonical(signed_values),
        _decode_bytes(fields["signature"]),
    )
    if not fields["ok"]:
        raise AuthorityAttestationError("attestation_denied")
    return _require_object_value(fields["result"])


def _without_signature(
    value: dict[str, object],
    fields: set[str],
) -> dict[str, object]:
    checked = _require_exact(value, fields)
    return {
        name: checked[name]
        for name in fields
        if name != "signature"
    }


def _fingerprint(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _key_fingerprint(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _canonical_json_string(value: object) -> str:
    text = _string(value)
    decoded = _decode_frame(text.encode("utf-8"))
    if _encode_frame(decoded).decode("utf-8") != text:
        raise ValueError
    return text


def _verify_signature(
    public_key: object,
    payload: bytes,
    signature: bytes,
) -> None:
    if type(public_key) is not bytes or len(public_key) != 32:
        raise ValueError
    Ed25519PublicKey.from_public_bytes(public_key).verify(
        signature, payload,
    )


def _encode_frame(value: object) -> bytes:
    _validate_json(value, depth=0)
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if len(encoded) > ATTESTOR_MAX_FRAME_BYTES:
        raise ValueError
    return encoded


def _decode_frame(raw: bytes) -> object:
    if (
        type(raw) is not bytes
        or not raw
        or len(raw) > ATTESTOR_MAX_FRAME_BYTES
    ):
        raise ValueError
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_reject_duplicates,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
    )
    _validate_json(value, depth=0)
    return value


def _canonical(value: object) -> bytes:
    return _encode_frame(value)


def _validate_json(value: object, *, depth: int) -> None:
    if depth > _MAX_DEPTH:
        raise ValueError
    if value is None or type(value) in {bool, int}:
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError
        return
    if type(value) is str:
        if len(value) > _MAX_STRING_CHARS:
            raise ValueError
        return
    if type(value) is list:
        if len(value) > _MAX_CONTAINER_ITEMS:
            raise ValueError
        for item in value:
            _validate_json(item, depth=depth + 1)
        return
    if type(value) is dict:
        if len(value) > _MAX_CONTAINER_ITEMS:
            raise ValueError
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError
            _validate_json(item, depth=depth + 1)
        return
    raise ValueError


def _reject_duplicates(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def _require_object(
    value: object,
    fields: set[str],
) -> dict[str, object]:
    return _require_exact(value, fields)


def _require_exact(
    value: object,
    fields: set[str],
) -> dict[str, object]:
    if type(value) is not dict or set(value) != fields:
        raise ValueError
    return value


def _require_object_value(value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError
    return value


def _string(value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError
    return value


def _positive_int(value: object) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError
    return value


def _encode_bytes(value: bytes) -> str:
    if type(value) is not bytes:
        raise ValueError
    return base64.b64encode(value).decode("ascii")


def _decode_bytes(value: object) -> bytes:
    if type(value) is not str:
        raise ValueError
    try:
        return base64.b64decode(value, validate=True)
    except (ValueError, UnicodeError):
        raise ValueError from None


def _encode_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _decode_time(value: object) -> datetime:
    text = _string(value)
    result = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError
    return result.astimezone(timezone.utc)


__all__ = (
    "ATTESTOR_MAX_FRAME_BYTES",
    "IAM_VERIFICATION_RECEIPT_KIND",
    "IAM_VERIFICATION_RECEIPT_WIRE_VERSION",
    "AuthorityAttestationError",
    "AuthorityAttestorClient",
    "start_authority_attestor",
)
