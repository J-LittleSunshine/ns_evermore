# -*- coding: utf-8 -*-
"""Encrypted, expiring runtime-node credential cache."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

from ns_common.exceptions import NsRuntimeIamDeniedError, NsValidationError
from ns_common.iam import RuntimeRoleScope
from ns_common.security import AesGcmSecretBox
from ns_common.time import Clock


_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:@/-]{0,255}")
_CAPABILITY = re.compile(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+")
_NODE_CREDENTIAL_FIELDS = {
    "credential_id", "identity", "tenant_id", "principal_type",
    "component_type", "roles", "capabilities", "issued_at", "expires_at",
}


@dataclass(frozen=True, slots=True, kw_only=True)
class RuntimeNodeCredentialClaims:
    credential_id: str = field(repr=False)
    identity: str = field(repr=False)
    tenant_id: str = field(repr=False)
    roles: frozenset[RuntimeRoleScope]
    capabilities: frozenset[str] = field(repr=False)
    issued_at: datetime
    expires_at: datetime


class RuntimeNodeCredentialVerifier:
    """Validate issuer signature, lifetime and the runtime-node credential kind."""

    def __init__(self, *, signing_key: bytes, clock: Clock) -> None:
        if not isinstance(signing_key, bytes) or len(signing_key) < 32:
            _invalid("signing_key")
        if not isinstance(clock, Clock):
            _invalid("clock")
        self._key = bytes(signing_key)
        self._clock = clock

    def verify(self, token: str) -> RuntimeNodeCredentialClaims:
        if not isinstance(token, str) or not token or len(token) > 65_536:
            raise _denied("credential_invalid")
        parts = token.split(".")
        if len(parts) != 3 or parts[0] != "nsrn1":
            raise _denied("credential_invalid")
        try:
            payload = _unb64(parts[1])
            signature = _unb64(parts[2])
            expected = hmac.new(self._key, payload, hashlib.sha256).digest()
            if not hmac.compare_digest(signature, expected):
                raise _denied("credential_signature_invalid")
            value = json.loads(payload.decode("utf-8"))
            if not isinstance(value, dict) or set(value) != _NODE_CREDENTIAL_FIELDS:
                raise ValueError
            if value.get("principal_type") != "runtime_node" or value.get("component_type") != "runtime":
                raise _denied("credential_scope_invalid")
            raw_roles = value["roles"]
            raw_capabilities = value["capabilities"]
            if (
                not isinstance(raw_roles, list)
                or len(raw_roles) != len(set(raw_roles))
                or not isinstance(raw_capabilities, list)
                or len(raw_capabilities) != len(set(raw_capabilities))
            ):
                raise ValueError
            issued_at = _parse_time(value["issued_at"])
            expires_at = _parse_time(value["expires_at"])
            claims = RuntimeNodeCredentialClaims(
                credential_id=_text(value["credential_id"]),
                identity=_text(value["identity"]),
                tenant_id=_text(value["tenant_id"]),
                roles=frozenset(RuntimeRoleScope(item) for item in raw_roles),
                capabilities=frozenset(_capability(item) for item in raw_capabilities),
                issued_at=issued_at,
                expires_at=expires_at,
            )
        except NsRuntimeIamDeniedError:
            raise
        except (KeyError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
            raise _denied("credential_invalid") from None
        now = self._clock.utc_now()
        if (
            not claims.roles
            or claims.expires_at <= claims.issued_at
            or claims.issued_at > now
        ):
            raise _denied("credential_scope_invalid")
        if claims.expires_at <= now:
            raise _denied("credential_expired")
        return claims


@dataclass(slots=True)
class _EncryptedEntry:
    ciphertext: bytes
    cached_at: float
    expires_at: datetime


class EncryptedCredentialCache:
    """Holds ciphertext only and exposes no persistence API."""

    _AAD = b"ns_runtime:iam-r1:node-credential"

    def __init__(
        self,
        *,
        encryption_key: bytes,
        verifier: RuntimeNodeCredentialVerifier,
        clock: Clock,
        ttl_seconds: float,
        nonce_factory: Callable[[int], bytes] = os.urandom,
    ) -> None:
        if not isinstance(encryption_key, bytes) or len(encryption_key) not in {16, 24, 32}:
            _invalid("encryption_key")
        if not isinstance(verifier, RuntimeNodeCredentialVerifier):
            _invalid("verifier")
        if not isinstance(clock, Clock):
            _invalid("clock")
        if (
            isinstance(ttl_seconds, bool)
            or not isinstance(ttl_seconds, (int, float))
            or float(ttl_seconds) <= 0
        ):
            _invalid("ttl_seconds")
        if not callable(nonce_factory):
            _invalid("nonce_factory")
        self._secret_box = AesGcmSecretBox(
            encryption_key=encryption_key,
            nonce_factory=nonce_factory,
        )
        self._verifier = verifier
        self._clock = clock
        self._ttl = float(ttl_seconds)
        self._entries: dict[str, _EncryptedEntry] = {}
        self._revoked: set[str] = set()

    def __repr__(self) -> str:
        return f"EncryptedCredentialCache(entries={len(self._entries)}, encrypted=True)"

    def put(
        self,
        token: str,
        *,
        required_role: RuntimeRoleScope,
    ) -> RuntimeNodeCredentialClaims:
        claims = self._verifier.verify(token)
        self._require_role(claims, required_role)
        if claims.credential_id in self._revoked:
            raise _denied("credential_revoked")
        ciphertext = self._secret_box.seal(
            token.encode("utf-8"),
            associated_data=self._AAD,
        )
        self._entries[claims.credential_id] = _EncryptedEntry(
            ciphertext=ciphertext,
            cached_at=self._clock.monotonic(),
            expires_at=claims.expires_at,
        )
        return claims

    def get(
        self,
        credential_id: str,
        *,
        required_role: RuntimeRoleScope,
    ) -> str:
        if credential_id in self._revoked:
            raise _denied("credential_revoked")
        entry = self._entries.get(credential_id)
        if entry is None:
            raise _denied("credential_not_cached")
        if (
            self._clock.monotonic() - entry.cached_at >= self._ttl
            or entry.expires_at <= self._clock.utc_now()
        ):
            del self._entries[credential_id]
            raise _denied("credential_expired")
        try:
            token = self._secret_box.open(
                entry.ciphertext,
                associated_data=self._AAD,
            ).decode("utf-8")
        except Exception:
            del self._entries[credential_id]
            raise _denied("credential_cache_tampered") from None
        claims = self._verifier.verify(token)
        if claims.credential_id != credential_id:
            del self._entries[credential_id]
            raise _denied("credential_cache_tampered")
        self._require_role(claims, required_role)
        return token

    def revoke(self, credential_id: str) -> None:
        self._entries.pop(credential_id, None)
        self._revoked.add(credential_id)

    @staticmethod
    def _require_role(
        claims: RuntimeNodeCredentialClaims,
        required_role: RuntimeRoleScope,
    ) -> None:
        if not isinstance(required_role, RuntimeRoleScope):
            _invalid("required_role")
        if required_role not in claims.roles:
            raise _denied("credential_role_scope_denied")


def _unb64(value: str) -> bytes:
    return base64.b64decode(
        value + "=" * (-len(value) % 4),
        altchars=b"-_",
        validate=True,
    )


def _parse_time(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError
    return parsed.astimezone(timezone.utc)


def _text(value: object) -> str:
    if not isinstance(value, str) or _NAME.fullmatch(value) is None:
        raise ValueError
    return value


def _capability(value: object) -> str:
    if not isinstance(value, str) or _CAPABILITY.fullmatch(value) is None:
        raise ValueError
    return value


def _denied(reason: str) -> NsRuntimeIamDeniedError:
    return NsRuntimeIamDeniedError(
        details={
            "component": "runtime_credential_cache",
            "operation": "credential_validation",
            "reason": reason,
        },
    )


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Runtime credential cache value is invalid.",
        details={"component": "runtime_credential_cache", "field": field_name},
    )


__all__ = (
    "EncryptedCredentialCache", "RuntimeNodeCredentialClaims",
    "RuntimeNodeCredentialVerifier",
)
