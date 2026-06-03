# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import pickle
from abc import abstractmethod, ABC
from typing import TYPE_CHECKING

from ns_common.cache.exceptions import NsCacheSerializationError, NsCacheConfigurationError

if TYPE_CHECKING:
    pass

class BaseCacheSerializer(ABC):
    @abstractmethod
    def dumps(self, value: object) -> bytes:
        """Serialize Python value to bytes."""
        raise NotImplementedError

    @abstractmethod
    def loads(self, payload: bytes) -> object:
        """Deserialize bytes to Python value."""
        raise NotImplementedError


class PickleCacheSerializer(BaseCacheSerializer):
    def dumps(self, value: object) -> bytes:
        try:
            return pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as _error:
            raise NsCacheSerializationError("pickle cache serialization failed") from _error

    def loads(self, payload: bytes) -> object:
        try:
            return pickle.loads(payload)
        except Exception as _error:
            raise NsCacheSerializationError("pickle cache deserialization failed") from _error


class JsonCacheSerializer(BaseCacheSerializer):
    def dumps(self, value: object) -> bytes:
        try:
            return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        except Exception as _error:
            raise NsCacheSerializationError("json cache serialization failed") from _error

    def loads(self, payload: bytes) -> object:
        try:
            return json.loads(payload.decode("utf-8"))
        except Exception as _error:
            raise NsCacheSerializationError("json cache deserialization failed") from _error


class RawCacheSerializer(BaseCacheSerializer):
    def dumps(self, value: object) -> bytes:
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return value.encode("utf-8")
        if isinstance(value, (int, float, bool)):
            return str(value).encode("utf-8")
        if value is None:
            return b""
        raise NsCacheSerializationError("raw cache serializer only supports bytes, str, int, float, bool, or None")

    def loads(self, payload: bytes) -> object:
        return payload


def build_serializer(name: str) -> BaseCacheSerializer:
    serializer_name = name.strip().lower()
    if serializer_name == "pickle":
        return PickleCacheSerializer()
    if serializer_name == "json":
        return JsonCacheSerializer()
    if serializer_name == "raw":
        return RawCacheSerializer()
    raise NsCacheConfigurationError(f"unsupported cache serializer: {name}")
