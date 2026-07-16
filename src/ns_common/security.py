# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
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
DEFAULT_SANITIZER_DIGEST_MAX_NODES = 4096
DEFAULT_SANITIZER_DIGEST_MAX_CONTAINER_ITEMS = 256
DEFAULT_SANITIZER_DIGEST_MAX_STRING_LENGTH = 4096
DEFAULT_SANITIZER_DIGEST_MAX_BYTES_LENGTH = 65536
DEFAULT_SANITIZER_DIGEST_MAX_NORMALIZED_BYTES = 262144

_SANITIZATION_FAILED = "[SANITIZATION_FAILED]"
_NON_FINITE_NUMBER = "[NON_FINITE_NUMBER]"
_INTEGER_OUT_OF_RANGE = "[INTEGER_OUT_OF_RANGE]"
_MAX_JSON_INTEGER_BITS = 4096
_MISSING = object()

_URL_SCHEMES = frozenset({
    "http",
    "https",
    "ws",
    "wss",
})
_REDACTED_FIELDS = frozenset({
    "apikey",
    "authorization",
    "authcontext",
    "certificate",
    "clientsecret",
    "cookie",
    "credential",
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
    "signature",
})
_REDACTED_SUFFIXES = (
    "apikey",
    "authorization",
    "certificate",
    "cookie",
    "credential",
    "credentials",
    "fencingtoken",
    "passphrase",
    "password",
    "payload",
    "privatekey",
    "secret",
    "secretkey",
    "signature",
    "signedurl",
    "token",
)
_ADDRESS_SUFFIXES = (
    "clientaddress",
    "clientip",
    "peeraddress",
    "peerip",
    "remoteaddress",
    "remoteip",
)
_ADDRESS_FIELDS = frozenset({
    "clientaddress",
    "clientip",
    "ipaddress",
    "peeraddress",
    "peerip",
    "remoteaddress",
    "remoteip",
})
_DIGEST_FIELDS = frozenset({
    "allowedcapabilities",
    "capabilities",
    "certificatedigest",
    "certificatefingerprint",
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
    r"\bBearer\s+[A-Za-z0-9._~+/=-]+",
    re.IGNORECASE,
)
_SENSITIVE_HEADER_PATTERN = re.compile(
    r"(?P<prefix>\b(?:proxy[_-]?authorization|authorization|"
    r"set[_-]?cookie|cookie)[ \t]*:[ \t]*)[^\r\n]*",
    re.IGNORECASE | re.MULTILINE,
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
        password|passphrase|private[_-]?key|cookie|set[_-]?cookie|
        credential|signature|certificate|[A-Za-z0-9_-]*payload
    )
    (?P=key_quote)
    (?P<separator>\s*[:=]\s*)
    (?P<value>\[[A-Z_]+\]|"[^"]*"|'[^']*'|[^\s,;&}\]]+)
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _compact_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(
        character
        for character in normalized
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
        or field_name in _SIGNED_URL_FIELDS
        or field_name.endswith(_REDACTED_SUFFIXES)
    ):
        return "redact"
    if field_name == "url" and ancestors.intersection(_PAYLOAD_REF_CONTEXTS):
        return "redact"
    if (
        field_name in _ADDRESS_FIELDS
        or field_name.endswith(_ADDRESS_SUFFIXES)
        or field_name in {"address", "ip"}
        and ancestors.intersection(_PEER_CONTEXTS)
    ):
        return "redact"
    if field_name in _DIGEST_FIELDS or field_name.endswith("capabilities"):
        return "digest"
    if (
        field_name in {"digest", "fingerprint", "sha256"}
        and ancestors.intersection(_CERTIFICATE_CONTEXTS)
    ):
        return "digest"
    return None


class _DigestLimitExceeded(Exception):
    """Internal signal that digest normalization exceeded a public limit."""


class _DigestCanonicalizer:
    """Build a deterministic canonical byte string under strict resource limits."""

    def __init__(
        self,
        *,
        max_depth: int,
        max_nodes: int,
        max_container_items: int,
        max_string_length: int,
        max_bytes_length: int,
        max_normalized_bytes: int,
    ) -> None:
        self._max_depth = max_depth
        self._max_nodes = max_nodes
        self._max_container_items = max_container_items
        self._max_string_length = max_string_length
        self._max_bytes_length = max_bytes_length
        self._max_normalized_bytes = max_normalized_bytes
        self._node_count = 0
        self._normalized_bytes = 0

    def canonicalize(self, value: object, *, depth: int) -> bytes:
        return self._encode(value, depth=depth, active_ids=set())

    def _encode(
        self,
        value: object,
        *,
        depth: int,
        active_ids: set[int],
    ) -> bytes:
        if depth > self._max_depth:
            raise _DigestLimitExceeded
        self._claim_node()

        if value is None:
            return self._emit(b"n")
        if isinstance(value, bool):
            return self._emit(b"b1" if value else b"b0")
        if isinstance(value, int):
            if int.bit_length(value) > _MAX_JSON_INTEGER_BITS:
                raise _DigestLimitExceeded
            return self._encode_ascii_scalar(b"i", str(int(value)))
        if isinstance(value, float):
            if not math.isfinite(value):
                raise _DigestLimitExceeded
            return self._encode_ascii_scalar(b"f", float.hex(value))
        if isinstance(value, str):
            return self._encode_text(b"s", value)
        if isinstance(value, bytes):
            return self._encode_nested_bytes(value)
        if isinstance(value, (datetime, date, time)):
            return self._encode_text(b"d", value.isoformat())
        if isinstance(value, Path):
            return self._encode_text(b"p", str(value))

        value_id = id(value)
        if value_id in active_ids:
            return self._emit(b"c")
        active_ids.add(value_id)
        try:
            if isinstance(value, Enum):
                type_name = self._encode_type_name(value)
                enum_value = self._encode(
                    value.value,
                    depth=depth + 1,
                    active_ids=active_ids,
                )
                return self._wrap(b"e[", [type_name, enum_value], b"]")
            if is_dataclass(value) and not isinstance(value, type):
                return self._encode_dataclass(
                    value,
                    depth=depth,
                    active_ids=active_ids,
                )
            if isinstance(value, Mapping):
                return self._encode_mapping(
                    value,
                    depth=depth,
                    active_ids=active_ids,
                )
            if isinstance(value, (list, tuple)):
                return self._encode_sequence(
                    value,
                    tag=b"l[" if isinstance(value, list) else b"t[",
                    depth=depth,
                    active_ids=active_ids,
                )
            if isinstance(value, (set, frozenset)):
                return self._encode_set(
                    value,
                    tag=b"u[" if isinstance(value, set) else b"r[",
                    depth=depth,
                    active_ids=active_ids,
                )
            return self._encode_object(
                value,
                depth=depth,
                active_ids=active_ids,
            )
        finally:
            active_ids.discard(value_id)

    def _encode_mapping(
        self,
        value: Mapping[Any, Any],
        *,
        depth: int,
        active_ids: set[int],
    ) -> bytes:
        entries: list[bytes] = []
        items = value.items()
        for index, (key, item) in enumerate(items):
            if index >= self._max_container_items:
                raise _DigestLimitExceeded
            encoded_key = self._encode(
                key,
                depth=depth + 1,
                active_ids=active_ids,
            )
            encoded_value = self._encode(
                item,
                depth=depth + 1,
                active_ids=active_ids,
            )
            entries.append(self._wrap(b"(", [encoded_key, encoded_value], b")"))
        entries.sort()
        return self._wrap(b"m[", entries, b"]")

    def _encode_sequence(
        self,
        value: list[object] | tuple[object, ...],
        *,
        tag: bytes,
        depth: int,
        active_ids: set[int],
    ) -> bytes:
        items: list[bytes] = []
        for index, item in enumerate(value):
            if index >= self._max_container_items:
                raise _DigestLimitExceeded
            items.append(self._encode(
                item,
                depth=depth + 1,
                active_ids=active_ids,
            ))
        return self._wrap(tag, items, b"]")

    def _encode_set(
        self,
        value: set[object] | frozenset[object],
        *,
        tag: bytes,
        depth: int,
        active_ids: set[int],
    ) -> bytes:
        items: list[bytes] = []
        for index, item in enumerate(value):
            if index >= self._max_container_items:
                raise _DigestLimitExceeded
            items.append(self._encode(
                item,
                depth=depth + 1,
                active_ids=active_ids,
            ))
        items.sort()
        return self._wrap(tag, items, b"]")

    def _encode_dataclass(
        self,
        value: object,
        *,
        depth: int,
        active_ids: set[int],
    ) -> bytes:
        raw_fields = getattr(type(value), "__dataclass_fields__", None)
        if not isinstance(raw_fields, dict):
            raise TypeError("dataclass fields must be a dictionary")
        if len(raw_fields) > self._max_container_items:
            raise _DigestLimitExceeded
        encoded_fields: list[bytes] = []
        for field in fields(value):
            field_name = field.name
            encoded_name = self._encode_text(b"k", field_name)
            field_value = getattr(value, field_name)
            encoded_value = self._encode(
                field_value,
                depth=depth + 1,
                active_ids=active_ids,
            )
            encoded_fields.append(
                self._wrap(b"(", [encoded_name, encoded_value], b")")
            )
        encoded_fields.sort()
        type_name = self._encode_type_name(value)
        body = self._wrap(b"v[", encoded_fields, b"]")
        return self._wrap(b"a[", [type_name, body], b"]")

    def _encode_object(
        self,
        value: object,
        *,
        depth: int,
        active_ids: set[int],
    ) -> bytes:
        attributes = vars(value)
        if not isinstance(attributes, Mapping):
            raise TypeError("vars(value) must return a mapping")
        type_name = self._encode_type_name(value)
        encoded_attributes = self._encode(
            attributes,
            depth=depth + 1,
            active_ids=active_ids,
        )
        return self._wrap(b"o[", [type_name, encoded_attributes], b"]")

    def _encode_nested_bytes(self, value: bytes) -> bytes:
        if len(value) > self._max_bytes_length:
            raise _DigestLimitExceeded
        byte_digest = hashlib.sha256(value).hexdigest()
        return self._encode_ascii_scalar(
            b"y",
            f"{len(value)}:{byte_digest}",
        )

    def _encode_type_name(self, value: object) -> bytes:
        name = type(value).__name__
        if not isinstance(name, str) or not name:
            raise TypeError("type name must be a non-empty string")
        return self._encode_text(b"q", name)

    def _encode_text(self, tag: bytes, value: str) -> bytes:
        if len(value) > self._max_string_length:
            raise _DigestLimitExceeded
        encoded = value.encode("utf-8", errors="strict")
        prefix = tag + str(len(encoded)).encode("ascii") + b":"
        self._reserve(len(prefix) + len(encoded))
        return prefix + encoded

    def _encode_ascii_scalar(self, tag: bytes, value: str) -> bytes:
        encoded = value.encode("ascii", errors="strict")
        prefix = tag + str(len(encoded)).encode("ascii") + b":"
        self._reserve(len(prefix) + len(encoded))
        return prefix + encoded

    def _wrap(
        self,
        prefix: bytes,
        parts: list[bytes],
        suffix: bytes,
    ) -> bytes:
        separator_bytes = max(0, len(parts) - 1)
        self._reserve(len(prefix) + separator_bytes + len(suffix))
        return prefix + b",".join(parts) + suffix

    def _claim_node(self) -> None:
        self._node_count += 1
        if self._node_count > self._max_nodes:
            raise _DigestLimitExceeded

    def _emit(self, value: bytes) -> bytes:
        self._reserve(len(value))
        return value

    def _reserve(self, size: int) -> None:
        if size > self._max_normalized_bytes - self._normalized_bytes:
            raise _DigestLimitExceeded
        self._normalized_bytes += size


class Sanitizer:
    """Convert arbitrary values to detached, strict JSON-safe sanitized data.

    Sensitive fields are replaced before traversal. Selected non-secret values,
    such as capability sets and certificate fingerprints, may use a deterministic
    digest. Peer/client/remote addresses are always replaced completely. Ordinary
    object failures are converted to stable placeholders; process-level control
    exceptions remain visible to the caller.
    """

    def __init__(
        self,
        *,
        max_depth: int = DEFAULT_SANITIZER_MAX_DEPTH,
        max_digest_nodes: int = DEFAULT_SANITIZER_DIGEST_MAX_NODES,
        max_digest_container_items: int = (
            DEFAULT_SANITIZER_DIGEST_MAX_CONTAINER_ITEMS
        ),
        max_digest_string_length: int = (
            DEFAULT_SANITIZER_DIGEST_MAX_STRING_LENGTH
        ),
        max_digest_bytes_length: int = (
            DEFAULT_SANITIZER_DIGEST_MAX_BYTES_LENGTH
        ),
        max_digest_normalized_bytes: int = (
            DEFAULT_SANITIZER_DIGEST_MAX_NORMALIZED_BYTES
        ),
    ) -> None:
        limits = {
            "max_depth": max_depth,
            "max_digest_nodes": max_digest_nodes,
            "max_digest_container_items": max_digest_container_items,
            "max_digest_string_length": max_digest_string_length,
            "max_digest_bytes_length": max_digest_bytes_length,
            "max_digest_normalized_bytes": max_digest_normalized_bytes,
        }
        for field_name, field_value in limits.items():
            if (
                isinstance(field_value, bool)
                or not isinstance(field_value, int)
                or field_value < 1
            ):
                raise NsValidationError(
                    f"{field_name} must be a positive integer.",
                    details={
                        "field": field_name,
                        "value": field_value,
                        "actual_type": type(field_value).__name__,
                    },
                )
        self._max_depth = max_depth
        self._max_digest_nodes = max_digest_nodes
        self._max_digest_container_items = max_digest_container_items
        self._max_digest_string_length = max_digest_string_length
        self._max_digest_bytes_length = max_digest_bytes_length
        self._max_digest_normalized_bytes = max_digest_normalized_bytes

    @property
    def max_depth(self) -> int:
        return self._max_depth

    @property
    def max_digest_nodes(self) -> int:
        return self._max_digest_nodes

    @property
    def max_digest_container_items(self) -> int:
        return self._max_digest_container_items

    @property
    def max_digest_string_length(self) -> int:
        return self._max_digest_string_length

    @property
    def max_digest_bytes_length(self) -> int:
        return self._max_digest_bytes_length

    @property
    def max_digest_normalized_bytes(self) -> int:
        return self._max_digest_normalized_bytes

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
                        "actual_type": type(field_name).__name__,
                    },
                )
            normalized_path += (field_name,)
        try:
            return self._sanitize_value(
                value,
                path=normalized_path,
                depth=0,
                active_ids=set(),
            )
        except Exception:
            return _SANITIZATION_FAILED

    def sanitize_url(self, value: object) -> str:
        if not isinstance(value, str):
            raise NsValidationError(
                "url must be a string.",
                details={
                    "field": "url",
                    "actual_type": type(value).__name__,
                },
            )
        try:
            return self._sanitize_url(value)
        except Exception:
            return REDACTED

    def sanitize_text(self, value: object) -> str:
        if not isinstance(value, str):
            raise NsValidationError(
                "text must be a string.",
                details={
                    "field": "text",
                    "actual_type": type(value).__name__,
                },
            )
        try:
            return self._sanitize_text(value)
        except Exception:
            return REDACTED

    def _sanitize_value(
        self,
        value: object,
        *,
        path: tuple[str, ...],
        depth: int,
        active_ids: set[int],
    ) -> object:
        try:
            return self._sanitize_value_unchecked(
                value,
                path=path,
                depth=depth,
                active_ids=active_ids,
            )
        except Exception:
            return _SANITIZATION_FAILED

    def _sanitize_value_unchecked(
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
            return self._digest_summary(value, depth=depth)
        if depth > self._max_depth:
            return MAX_DEPTH_REACHED
        if value is None or isinstance(value, bool):
            return value
        if isinstance(value, int):
            if int.bit_length(value) > _MAX_JSON_INTEGER_BITS:
                return _INTEGER_OUT_OF_RANGE
            return value
        if isinstance(value, float):
            numeric_value = float(value)
            return (
                numeric_value
                if math.isfinite(numeric_value)
                else _NON_FINITE_NUMBER
            )
        if isinstance(value, str):
            return self._sanitize_text(value)
        if isinstance(value, bytes):
            return self._digest_summary(value, depth=depth)
        if isinstance(value, Enum):
            try:
                enum_value = value.value
            except Exception:
                return _SANITIZATION_FAILED
            return self._sanitize_value(
                enum_value,
                path=path,
                depth=depth,
                active_ids=active_ids,
            )
        if isinstance(value, (datetime, date, time)):
            try:
                iso_value = value.isoformat()
            except Exception:
                return _SANITIZATION_FAILED
            return (
                iso_value
                if isinstance(iso_value, str)
                else _SANITIZATION_FAILED
            )
        if isinstance(value, Path):
            try:
                return self._sanitize_text(str(value))
            except Exception:
                return _SANITIZATION_FAILED

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
                return self._sanitize_dataclass(
                    value,
                    path=path,
                    depth=depth,
                    active_ids=active_ids,
                )
            if isinstance(value, Mapping):
                return self._sanitize_mapping(
                    value,
                    path=path,
                    depth=depth,
                    active_ids=active_ids,
                )
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
                return sorted(sanitized_items, key=self._stable_sort_key)
            return self._sanitize_object(
                value,
                path=path,
                depth=depth,
                active_ids=active_ids,
            )
        finally:
            active_ids.discard(value_id)

    def _sanitize_dataclass(
        self,
        value: object,
        *,
        path: tuple[str, ...],
        depth: int,
        active_ids: set[int],
    ) -> object:
        try:
            dataclass_fields = fields(value)
        except Exception:
            return _SANITIZATION_FAILED
        result: dict[str, object] = {"__type__": self._safe_type_name(value)}
        for field in dataclass_fields:
            field_name = field.name
            try:
                field_value = getattr(value, field_name)
            except Exception:
                field_value = _SANITIZATION_FAILED
            safe_key = self._unique_mapping_key(
                result,
                self._sanitize_mapping_key(field_name),
            )
            result[safe_key] = self._sanitize_value(
                field_value,
                path=path + (field_name,),
                depth=depth + 1,
                active_ids=active_ids,
            )
        return result

    def _sanitize_mapping(
        self,
        value: Mapping[Any, Any],
        *,
        path: tuple[str, ...],
        depth: int,
        active_ids: set[int],
    ) -> object:
        try:
            items = value.items()
            result: dict[str, object] = {}
            for key, item in items:
                safe_key = self._unique_mapping_key(
                    result,
                    self._sanitize_mapping_key(key),
                )
                result[safe_key] = self._sanitize_value(
                    item,
                    path=path + (safe_key,),
                    depth=depth + 1,
                    active_ids=active_ids,
                )
            return result
        except Exception:
            return _SANITIZATION_FAILED

    def _sanitize_object(
        self,
        value: object,
        *,
        path: tuple[str, ...],
        depth: int,
        active_ids: set[int],
    ) -> object:
        try:
            attributes = vars(value)
        except Exception:
            return _SANITIZATION_FAILED
        if not isinstance(attributes, Mapping):
            return _SANITIZATION_FAILED
        sanitized_attributes = self._sanitize_mapping(
            attributes,
            path=path,
            depth=depth,
            active_ids=active_ids,
        )
        if not isinstance(sanitized_attributes, dict):
            return _SANITIZATION_FAILED
        result: dict[str, object] = {"__type__": self._safe_type_name(value)}
        for key, item in sanitized_attributes.items():
            result[self._unique_mapping_key(result, key)] = item
        return result

    def _sanitize_exception(
        self,
        error: BaseException,
        *,
        path: tuple[str, ...],
        depth: int,
        active_ids: set[int],
    ) -> dict[str, object]:
        raw_message, message_failed = self._read_attribute(error, "message")
        if message_failed:
            message = _SANITIZATION_FAILED
        elif raw_message is _MISSING:
            try:
                message = str(error)
            except Exception:
                message = _SANITIZATION_FAILED
        elif isinstance(raw_message, str):
            message = raw_message
        else:
            message = _SANITIZATION_FAILED

        result: dict[str, object] = {
            "type": self._safe_type_name(error),
            "message": self._sanitize_text(message),
        }
        for attribute_name in ("code", "numeric_code"):
            attribute_value, attribute_failed = self._read_attribute(
                error,
                attribute_name,
            )
            if attribute_failed:
                result[attribute_name] = _SANITIZATION_FAILED
            elif (
                attribute_value is not _MISSING
                and isinstance(attribute_value, (str, int))
                and not isinstance(attribute_value, bool)
            ):
                result[attribute_name] = self._sanitize_value(
                    attribute_value,
                    path=path + (attribute_name,),
                    depth=depth + 1,
                    active_ids=active_ids,
                )

        details, details_failed = self._read_attribute(error, "details")
        if details_failed:
            result["details"] = _SANITIZATION_FAILED
        elif details is not _MISSING and details is not None:
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

        sanitized = _SENSITIVE_HEADER_PATTERN.sub(
            self._replace_sensitive_header,
            value,
        )
        sanitized = _URL_PATTERN.sub(
            lambda match: self._sanitize_url(match.group(0)),
            sanitized,
        )
        sanitized = _BEARER_PATTERN.sub("Bearer [REDACTED]", sanitized)
        return _ASSIGNMENT_PATTERN.sub(self._replace_assignment, sanitized)

    def _sanitize_url(self, value: str) -> str:
        try:
            parsed = urlsplit(value)
            scheme = parsed.scheme.casefold()
            hostname = parsed.hostname
            port = parsed.port
        except Exception:
            return REDACTED
        if scheme not in _URL_SCHEMES or not hostname:
            return self._sanitize_non_url_text(value)

        if ":" in hostname and not hostname.startswith("["):
            hostname = f"[{hostname}]"
        netloc = hostname if port is None else f"{hostname}:{port}"
        try:
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
            query = urlencode(sanitized_query, doseq=True)
            return urlunsplit((
                scheme,
                netloc,
                parsed.path,
                query,
                REDACTED if parsed.fragment else "",
            ))
        except Exception:
            return REDACTED

    @staticmethod
    def _replace_sensitive_header(match: re.Match[str]) -> str:
        return f"{match.group('prefix')}{REDACTED}"

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
        sanitized = _SENSITIVE_HEADER_PATTERN.sub(
            Sanitizer._replace_sensitive_header,
            value,
        )
        sanitized = _BEARER_PATTERN.sub("Bearer [REDACTED]", sanitized)
        return _ASSIGNMENT_PATTERN.sub(Sanitizer._replace_assignment, sanitized)

    @staticmethod
    def _looks_like_url(value: str) -> bool:
        try:
            parsed = urlsplit(value)
            return (
                parsed.scheme.casefold() in _URL_SCHEMES
                and bool(parsed.netloc)
            )
        except Exception:
            return False

    @staticmethod
    def _query_field_is_sensitive(field_name: str) -> bool:
        compact = _compact_name(field_name)
        return (
            compact in _SENSITIVE_QUERY_FIELDS
            or compact.endswith("token")
            or compact.endswith("signature")
            or compact.endswith("credential")
        )

    def _sanitize_mapping_key(self, value: object) -> str:
        try:
            if isinstance(value, str):
                return self._sanitize_text(value)
            if value is None:
                return "<null>"
            if isinstance(value, bool):
                return "<bool>"
            if isinstance(value, int):
                return "<int>"
            if isinstance(value, float):
                return "<float>"
            return f"<{self._safe_type_name(value)}>"
        except Exception:
            return "<unsafe-key>"

    @staticmethod
    def _unique_mapping_key(
        result: Mapping[str, object],
        base_key: str,
    ) -> str:
        if base_key not in result:
            return base_key
        collision_number = 2
        while f"{base_key}#{collision_number}" in result:
            collision_number += 1
        return f"{base_key}#{collision_number}"

    @staticmethod
    def _safe_type_name(value: object) -> str:
        try:
            name = type(value).__name__
        except Exception:
            return "object"
        if not isinstance(name, str) or not name:
            return "object"
        try:
            return Sanitizer._sanitize_non_url_text(name)
        except Exception:
            return "object"

    @staticmethod
    def _read_attribute(
        value: object,
        attribute_name: str,
    ) -> tuple[object, bool]:
        try:
            return getattr(value, attribute_name, _MISSING), False
        except Exception:
            return _MISSING, True

    @staticmethod
    def _stable_sort_key(value: object) -> str:
        try:
            return json.dumps(
                value,
                allow_nan=False,
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            )
        except Exception:
            return _SANITIZATION_FAILED

    @staticmethod
    def _validate_path(path: Sequence[str]) -> tuple[str, ...]:
        if isinstance(path, (str, bytes)) or not isinstance(path, Sequence):
            raise NsValidationError(
                "path must be a sequence of strings.",
                details={
                    "field": "path",
                    "actual_type": type(path).__name__,
                },
            )
        try:
            normalized_path = tuple(path)
        except Exception as exc:
            raise NsValidationError(
                "path must be a sequence of strings.",
                details={
                    "field": "path",
                    "actual_type": type(path).__name__,
                },
            ) from exc
        if any(
            not isinstance(part, str) or not part
            for part in normalized_path
        ):
            raise NsValidationError(
                "path entries must be non-empty strings.",
                details={"field": "path"},
            )
        return normalized_path

    def _digest_summary(self, value: object, *, depth: int) -> str:
        try:
            if depth > self._max_depth:
                return REDACTED
            if isinstance(value, bytes):
                if len(value) > self._max_digest_bytes_length:
                    return REDACTED
                digest = hashlib.sha256(value).hexdigest()[:16]
            else:
                canonical = self._normalize_digest_value(value, depth=depth)
                digest = hashlib.sha256(canonical).hexdigest()[:16]
            return f"[REDACTED sha256:{digest}]"
        except Exception:
            return REDACTED

    def _normalize_digest_value(self, value: object, *, depth: int) -> bytes:
        return _DigestCanonicalizer(
            max_depth=self._max_depth,
            max_nodes=self._max_digest_nodes,
            max_container_items=self._max_digest_container_items,
            max_string_length=self._max_digest_string_length,
            max_bytes_length=self._max_digest_bytes_length,
            max_normalized_bytes=self._max_digest_normalized_bytes,
        ).canonicalize(value, depth=depth)


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
    "DEFAULT_SANITIZER_DIGEST_MAX_BYTES_LENGTH",
    "DEFAULT_SANITIZER_DIGEST_MAX_CONTAINER_ITEMS",
    "DEFAULT_SANITIZER_DIGEST_MAX_NODES",
    "DEFAULT_SANITIZER_DIGEST_MAX_NORMALIZED_BYTES",
    "DEFAULT_SANITIZER_DIGEST_MAX_STRING_LENGTH",
    "DEFAULT_SANITIZER_MAX_DEPTH",
    "MAX_DEPTH_REACHED",
    "NsSanitizer",
    "REDACTED",
    "Sanitizer",
    "sanitize",
    "sanitize_text",
    "sanitize_url",
]
