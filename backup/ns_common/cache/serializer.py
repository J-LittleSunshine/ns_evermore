# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import pickle
from typing import TYPE_CHECKING, Protocol

from ns_common.cache.errors import NsCacheConfigurationError, NsCacheSerializationError

if TYPE_CHECKING:
    pass


class CacheSerializer(Protocol):
    """Cache serializer protocol."""

    def dumps(self, value: object) -> bytes:
        """Serialize Python value to bytes."""

    def loads(self, payload: bytes) -> object:
        """Deserialize bytes to Python value."""


class PickleCacheSerializer:
    """Pickle cache serializer."""

    @staticmethod
    def dumps(value: object) -> bytes:
        """Serialize object by pickle."""
        try:
            return pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as _error:
            raise NsCacheSerializationError("pickle cache serialization failed") from _error

    @staticmethod
    def loads(payload: bytes) -> object:
        """Deserialize object by pickle."""
        try:
            return pickle.loads(payload)
        except Exception as _error:
            raise NsCacheSerializationError("pickle cache deserialization failed") from _error


class JsonCacheSerializer:
    """JSON cache serializer."""

    @staticmethod
    def dumps(value: object) -> bytes:
        """Serialize JSON-compatible value."""
        try:
            return json.dumps(
                value, ensure_ascii=False, separators=(
                    ",",
                    ":"
                )
            ).encode("utf-8")
        except Exception as _error:
            raise NsCacheSerializationError("json cache serialization failed") from _error

    @staticmethod
    def loads(payload: bytes) -> object:
        """Deserialize JSON-compatible value."""
        try:
            return json.loads(payload.decode("utf-8"))
        except Exception as _error:
            raise NsCacheSerializationError("json cache deserialization failed") from _error


class RawCacheSerializer:
    """Raw cache serializer."""

    @staticmethod
    def dumps(value: object) -> bytes:
        """Serialize primitive value to bytes."""
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return value.encode("utf-8")
        if isinstance(
                value, (
                        int,
                        float,
                        bool
                )
        ):
            return str(value).encode("utf-8")
        if value is None:
            return b""
        raise NsCacheSerializationError("raw cache serializer only supports bytes, str, int, float, bool, or None")

    @staticmethod
    def loads(payload: bytes) -> object:
        """Return raw bytes."""
        return payload


def build_serializer(name: str) -> CacheSerializer:
    """Build cache serializer by name."""
    serializer_name = str(name or "pickle").strip().lower()
    if serializer_name == "pickle":
        return PickleCacheSerializer()
    if serializer_name == "json":
        return JsonCacheSerializer()
    if serializer_name == "raw":
        return RawCacheSerializer()
    raise NsCacheConfigurationError(f"unsupported cache serializer: {name}")
