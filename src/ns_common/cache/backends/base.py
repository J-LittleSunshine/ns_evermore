# -*- coding: utf-8 -*-
from __future__ import annotations

from abc import (
    ABC,
    abstractmethod
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class BaseCacheBackend(ABC):
    @abstractmethod
    def initialize(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, key: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def get_many(self, keys: list[str]) -> dict[str, str]:
        raise NotImplementedError

    @abstractmethod
    def set(self, key: str, value: str, ttl: int | None) -> bool:
        raise NotImplementedError

    @abstractmethod
    def set_many(self, mapping: dict[str, str], ttl: int | None) -> bool:
        raise NotImplementedError

    @abstractmethod
    def add(self, key: str, value: str, ttl: int | None) -> bool:
        raise NotImplementedError

    @abstractmethod
    def touch(self, key: str, ttl: int | None) -> bool:
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def delete_many(self, keys: list[str]) -> int:
        raise NotImplementedError

    @abstractmethod
    def exists(self, key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def clear(self, namespace_prefix: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def incr(self, key: str, delta: int = 1) -> int:
        raise NotImplementedError

    def decr(self, key: str, delta: int = 1) -> int:
        return self.incr(key, -delta)

    def cleanup_expired(self) -> int:  # noqa
        return 0
