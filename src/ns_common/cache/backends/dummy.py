# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_common.cache.backends.base import BaseCacheBackend
from ns_common.exceptions import NsStateError

if TYPE_CHECKING:
    pass


class DummyCacheBackend(BaseCacheBackend):
    def initialize(self) -> None:
        return None

    def close(self) -> None:
        return None

    def get(self, key: str) -> str | None:
        return None

    def get_many(self, keys: list[str]) -> dict[str, str]:
        return {}

    def set(self, key: str, value: str, ttl: int | None) -> bool:
        return True

    def set_many(self, mapping: dict[str, str], ttl: int | None) -> bool:
        return True

    def add(self, key: str, value: str, ttl: int | None) -> bool:
        return True

    def touch(self, key: str, ttl: int | None) -> bool:
        return False

    def delete(self, key: str) -> bool:
        return False

    def delete_many(self, keys: list[str]) -> int:
        return 0

    def exists(self, key: str) -> bool:
        return False

    def clear(self, namespace_prefix: str) -> bool:
        return True

    def incr(self, key: str, delta: int = 1) -> int:
        raise NsStateError(
            "dummy cache backend does not support incr/decr.",
            details={
                "key": key,
                "delta": delta,
            },
        )
