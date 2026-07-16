# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import fields, is_dataclass
from datetime import date, datetime, time
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import (
    parse_qsl,
    urlencode,
    urlsplit,
    urlunsplit,
)

from ns_common.exceptions import NsValidationError


REDACTED = "[REDACTED]"
CIRCULAR_REFERENCE = "[CIRCULAR]"
MAX_DEPTH_REACHED = "[MAX_DEPTH]"
DEFAULT_SANITIZER_MAX_DEPTH = 32

_URL_SCHEMES = frozenset({
    "http",
    "https",
    "ws",
    "wss",
})
_REDACTED_FIELDS = frozenset({
    "authorization",
    "authcontext",
    "clientsecret",
    "cookie",
    "credentials",
    "envelopepayload",
    "password",
    "passphrase",
    "payload",
    "privatekey",
    "proxyauthorization",
    "rawpayload",
    "requestpayload",
    "responsepayload",
    "secret",
    "secretkey",
    "setcookie",
})
_DIGEST_FIELDS = frozenset({
    "allowedcapabilities",
    "capabilities",
    "certificatedigest",
    "certificatefingerprint",
    "clientaddress",
    "ipaddress",
    "peeraddress",
    "remoteaddress",
    "requestedcapabilities",
})
_SIGNED_URL_FIELDS = frozenset({
    "payloadrefurl",
    "presignedurl",
    "signatureurl",
    "signedurl",
})
_SENSITIVE_QUERY_FIELDS = frozenset({
    "apikey",
    "auth",
    "authorization",
    "code",
    "credential",
    "key",
    "password",
    "secret",
    "sig",
    "signature",
    "token",
    "xamzcredential",
    "xamzsecuritytoken",
    "xamzsignature",
})
_PAYLOAD_REF_CONTEXTS = frozenset({
    "objectref",
    "payloadref",
    "signed",
    "signedrequest",
})
_PEER_CONTEXTS = frozenset({
    "client",
    "connection",
    "peer",
    "remote",
    "transport",
})
_CERTIFICATE_CONTEXTS = frozenset({
    "cert",
    "certificate",
    "peercertificate",
    "tls",
})

_URL_PATTERN = re.compile(r"\b(?:https?|wss?)://[^\s<>\"]+", re.IGNORECASE)
_BEARER_PATTERN = re.compile(
    r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+",
)
_ASSIGNMENT_PATTERN = re.compile(
    r"""
    (?<![A-Za-z0-9_])
    (?P<key_quote>["']?)
    (?P<key>
        authorization|proxy[_-]?authorization|
        access[_-]?token|refresh[_-]?token|id[_-]?token|
        bearer[_-]?token|fencing[_-]?token|token|
        api[_-]?key|client[_-]?secret|secret[_-]?key|secret|
        password|passphrase|private[_-]?key|cookie
    )
    (?P=key_quote)
    (?P<separator>\s*[:=]\s*)
    (?P<value>"[^"]*"|'[^']*'|[^\s,;&}\]]+)
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _compact_name(value: object) -> str:
    return "".join(
        character
        for character in str(value).casefold()
        if character.isalnum()
    )


def _field_action(path: tuple[str, ...]) -> str | None:
    if not path:
        return None
    compact_path = tuple(_compact_name(part) for part in path)
    field_name = compact_path[-1]
    ancestors = frozenset(compact_path[:-1])

    if (
        field_name in _REDACTED_FIELDS
        or field_name.endswith("token")
        or field_name.endswith("password")
        or field_name.endswith("passphrase")
        or field_name.endswith("privatekey")
        or field_name.endswith("secretkey")
        or field_name.endswith("signedurl")
        or field_name in _SIGNED_URL_FIELDS
    ):
        return "redact"
    if field_name == "url" and ancestors.intersection(_PAYLOAD_REF_CONTEXTS):
        return "redact"
    if field_name in _DIGEST_FIELDS or field_name.endswith("capabilities"):
        return "digest"
    if field_name == "address" and ancestors.intersection(_PEER_CONTEXTS):
        return "digest"
    if (
        field_name in {"digest", "fingerprint", "sha256"}
        and ancestors.intersection(_CERTIFICATE_CONTEXTS)
    ):
        return "digest"
    return None


class Sanitizer:
    """Convert arbitrary values to detached, JSON-safe, sanitized data.

    Field and path rules run before object traversal. Sensitive values are
    either replaced completely or represented by a deterministic SHA-256
    summary. The sanitizer owns no global state and never mutates its input.
    """

    def __init__(self, *, max_depth: int = DEFAULT_SANITIZER_MAX_DEPTH) -> None:
        if (
            isinstance(max_depth, bool)
            or not isinstance(max_depth, int)
            or max_depth < 1
        ):
            raise NsValidationError(
                "max_depth must be a positive integer.",
                details={
                    "field": "max_depth",
                    "value": max_depth,
                    "actual_type": type(max_depth).__name__,
                },
            )
        self._max_depth = max_depth

    @property
    def max_depth(self) -> int:
        return self._max_depth

    def sanitize(
        self,
        value: object,
        *,
        field_name: str | None = None,
        path: Sequence[str] = (),
    ) -> object:
        normalized_path = self._validate_path(path)
        if field_name is not None:
            if not isinstance(field_name, str) or not field_name.strip():
                raise NsValidationError(
                    "field_name must be a non-empty string.",
                    details={
                        "field": "field_name",
                        "value": field_name,
                        "actual_type": type(field_name).__name__,
                    },
                )
            normalized_path += (field_name,)
        return self._sanitize_value(
            value,
            path=normalized_path,
            depth=0,
            active_ids=set(),
        )

    def sanitize_url(self, value: object) -> str:
        if not isinstance(value, str):
            raise NsValidationError(
                "url must be a string.",
                details={
                    "field": "url",
                    "value": value,
                    "actual_type": type(value).__name__,
                },
            )
        return self._sanitize_url(value)

    def sanitize_text(self, value: object) -> str:
        if not isinstance(value, str):
            raise NsValidationError(
                "text must be a string.",
                details={
                    "field": "text",
                    "value": value,
                    "actual_type": type(value).__name__,
                },
            )
        return self._sanitize_text(value)

    def _sanitize_value(
        self,
        value: object,
        *,
        path: tuple[str, ...],
        depth: int,
        active_ids: set[int],
    ) -> object:
        action = _field_action(path)
        if action == "redact":
            return REDACTED
        if action == "digest":
            return self._digest_summary(value)
        if depth > self._max_depth:
            return MAX_DEPTH_REACHED
        if value is None or isinstance(value, (bool, int, float)):
            return value
        if isinstance(value, str):
            return self._sanitize_text(value)
        if isinstance(value, bytes):
            return self._digest_summary(value)
        if isinstance(value, Enum):
            return self._sanitize_value(
                value.value,
                path=path,
                depth=depth,
                active_ids=active_ids,
            )
        if isinstance(value, (datetime, date, time)):
            return value.isoformat()
        if isinstance(value, Path):
            return self._sanitize_text(str(value))

        value_id = id(value)
        if value_id in active_ids:
            return CIRCULAR_REFERENCE
        active_ids.add(value_id)
        try:
            if isinstance(value, BaseException):
                return self._sanitize_exception(
                    value,
                    path=path,
                    depth=depth,
                    active_ids=active_ids,
                )
            if is_dataclass(value) and not isinstance(value, type):
                result: dict[str, object] = {"__type__": type(value).__name__}
                for field in fields(value):
                    try:
                        field_value = getattr(value, field.name)
                    except Exception:
                        field_value = REDACTED
                    result[field.name] = self._sanitize_value(
                        field_value,
                        path=path + (field.name,),
                        depth=depth + 1,
                        active_ids=active_ids,
                    )
                return result
            if isinstance(value, Mapping):
                return {
                    self._safe_mapping_key(key): self._sanitize_value(
                        item,
                        path=path + (str(key),),
                        depth=depth + 1,
                        active_ids=active_ids,
                    )
                    for key, item in value.items()
                }
            if isinstance(value, (list, tuple)):
                return [
                    self._sanitize_value(
                        item,
                        path=path + (str(index),),
                        depth=depth + 1,
                        active_ids=active_ids,
                    )
                    for index, item in enumerate(value)
                ]
            if isinstance(value, (set, frozenset)):
                sanitized_items = [
                    self._sanitize_value(
                        item,
                        path=path + ("item",),
                        depth=depth + 1,
                        active_ids=active_ids,
                    )
                    for item in value
                ]
                return sorted(sanitized_items, key=repr)
            try:
                attributes = vars(value)
            except (TypeError, ValueError):
                return f"<{type(value).__name__}>"
            return {
                "__type__": type(value).__name__,
                **{
                    str(name): self._sanitize_value(
                        item,
                        path=path + (str(name),),
                        depth=depth + 1,
                        active_ids=active_ids,
                    )
                    for name, item in attributes.items()
                },
            }
        finally:
            active_ids.remove(value_id)

    def _sanitize_exception(
        self,
        error: BaseException,
        *,
        path: tuple[str, ...],
        depth: int,
        active_ids: set[int],
    ) -> dict[str, object]:
        raw_message = getattr(error, "message", None)
        message = raw_message if isinstance(raw_message, str) else str(error)
        result: dict[str, object] = {
            "type": type(error).__name__,
            "message": self._sanitize_text(message),
        }
        for attribute_name in ("code", "numeric_code"):
            attribute_value = getattr(error, attribute_name, None)
            if isinstance(attribute_value, (str, int)):
                result[attribute_name] = attribute_value
        details = getattr(error, "details", None)
        if isinstance(details, Mapping):
            result["details"] = self._sanitize_value(
                details,
                path=path + ("details",),
                depth=depth + 1,
                active_ids=active_ids,
            )
        return result

    def _sanitize_text(self, value: str) -> str:
        stripped = value.strip()
        if self._looks_like_url(stripped):
            prefix_length = len(value) - len(value.lstrip())
            suffix_length = len(value) - len(value.rstrip())
            prefix = value[:prefix_length]
            suffix = value[len(value) - suffix_length:] if suffix_length else ""
            return f"{prefix}{self._sanitize_url(stripped)}{suffix}"

        sanitized = _URL_PATTERN.sub(
            lambda match: self._sanitize_url(match.group(0)),
            value,
        )
        sanitized = _BEARER_PATTERN.sub("Bearer [REDACTED]", sanitized)
        return _ASSIGNMENT_PATTERN.sub(self._replace_assignment, sanitized)

    def _sanitize_url(self, value: str) -> str:
        try:
            parsed = urlsplit(value)
        except (TypeError, ValueError):
            return REDACTED
        if parsed.scheme.casefold() not in _URL_SCHEMES or not parsed.hostname:
            return self._sanitize_non_url_text(value)
        try:
            port = parsed.port
        except ValueError:
            return REDACTED

        hostname = parsed.hostname
        if ":" in hostname and not hostname.startswith("["):
            hostname = f"[{hostname}]"
        netloc = hostname if port is None else f"{hostname}:{port}"
        sanitized_query = []
        for name, query_value in parse_qsl(
            parsed.query,
            keep_blank_values=True,
        ):
            if self._query_field_is_sensitive(name):
                sanitized_query.append((name, REDACTED))
            else:
                sanitized_query.append(
                    (name, self._sanitize_non_url_text(query_value))
                )
        return urlunsplit((
            parsed.scheme.casefold(),
            netloc,
            parsed.path,
            urlencode(sanitized_query, doseq=True),
            REDACTED if parsed.fragment else "",
        ))

    @staticmethod
    def _replace_assignment(match: re.Match[str]) -> str:
        raw_value = match.group("value")
        if (
            len(raw_value) >= 2
            and raw_value[0] in {"\"", "'"}
            and raw_value[-1] == raw_value[0]
        ):
            replacement = f"{raw_value[0]}{REDACTED}{raw_value[0]}"
        else:
            replacement = REDACTED
        return (
            f"{match.group('key_quote')}{match.group('key')}"
            f"{match.group('key_quote')}{match.group('separator')}"
            f"{replacement}"
        )

    @staticmethod
    def _sanitize_non_url_text(value: str) -> str:
        sanitized = _BEARER_PATTERN.sub("Bearer [REDACTED]", value)
        return _ASSIGNMENT_PATTERN.sub(Sanitizer._replace_assignment, sanitized)

    @staticmethod
    def _looks_like_url(value: str) -> bool:
        try:
            parsed = urlsplit(value)
        except (TypeError, ValueError):
            return False
        return (
            parsed.scheme.casefold() in _URL_SCHEMES
            and bool(parsed.netloc)
        )

    @staticmethod
    def _query_field_is_sensitive(field_name: str) -> bool:
        compact = _compact_name(field_name)
        return (
            compact in _SENSITIVE_QUERY_FIELDS
            or compact.endswith("token")
            or compact.endswith("signature")
            or compact.endswith("credential")
        )

    @staticmethod
    def _safe_mapping_key(value: object) -> object:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        return f"<{type(value).__name__}>"

    @staticmethod
    def _validate_path(path: Sequence[str]) -> tuple[str, ...]:
        if isinstance(path, (str, bytes)) or not isinstance(path, Sequence):
            raise NsValidationError(
                "path must be a sequence of strings.",
                details={
                    "field": "path",
                    "value": path,
                    "actual_type": type(path).__name__,
                },
            )
        if any(not isinstance(part, str) or not part for part in path):
            raise NsValidationError(
                "path entries must be non-empty strings.",
                details={"field": "path", "value": path},
            )
        return tuple(path)

    @staticmethod
    def _digest_summary(value: object) -> str:
        try:
            canonical = json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                default=Sanitizer._digest_default,
            ).encode("utf-8", errors="replace")
        except (TypeError, ValueError, RecursionError):
            canonical = type(value).__name__.encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:16]
        return f"[REDACTED sha256:{digest}]"

    @staticmethod
    def _digest_default(value: object) -> object:
        if isinstance(value, bytes):
            return {"type": "bytes", "hex": value.hex()}
        if isinstance(value, (set, frozenset)):
            return sorted(value, key=repr)
        if is_dataclass(value) and not isinstance(value, type):
            return {
                field.name: getattr(value, field.name)
                for field in fields(value)
            }
        try:
            return vars(value)
        except (TypeError, ValueError):
            return {"type": type(value).__name__}


NsSanitizer = Sanitizer


def sanitize(
    value: object,
    *,
    field_name: str | None = None,
    path: Sequence[str] = (),
) -> object:
    return Sanitizer().sanitize(value, field_name=field_name, path=path)


def sanitize_url(value: object) -> str:
    return Sanitizer().sanitize_url(value)


def sanitize_text(value: object) -> str:
    return Sanitizer().sanitize_text(value)


__all__ = [
    "CIRCULAR_REFERENCE",
    "DEFAULT_SANITIZER_MAX_DEPTH",
    "MAX_DEPTH_REACHED",
    "NsSanitizer",
    "REDACTED",
    "Sanitizer",
    "sanitize",
    "sanitize_text",
    "sanitize_url",
]
