# -*- coding: utf-8 -*-
from __future__ import annotations

from abc import (
    ABC,
    abstractmethod,
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

    async def aclose(self) -> None:
        self.close()

    @abstractmethod
    def get(self, key: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    async def aget(self, key: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def get_many(self, keys: list[str]) -> dict[str, str]:
        raise NotImplementedError

    @abstractmethod
    async def aget_many(self, keys: list[str]) -> dict[str, str]:
        raise NotImplementedError

    @abstractmethod
    def set(self, key: str, value: str, ttl: int | None) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def aset(self, key: str, value: str, ttl: int | None) -> bool:
        raise NotImplementedError

    @abstractmethod
    def set_many(self, mapping: dict[str, str], ttl: int | None) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def aset_many(self, mapping: dict[str, str], ttl: int | None) -> bool:
        raise NotImplementedError

    @abstractmethod
    def add(self, key: str, value: str, ttl: int | None) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def aadd(self, key: str, value: str, ttl: int | None) -> bool:
        raise NotImplementedError

    @abstractmethod
    def touch(self, key: str, ttl: int | None) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def atouch(self, key: str, ttl: int | None) -> bool:
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def adelete(self, key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def delete_many(self, keys: list[str]) -> int:
        raise NotImplementedError

    @abstractmethod
    async def adelete_many(self, keys: list[str]) -> int:
        raise NotImplementedError

    @abstractmethod
    def exists(self, key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def aexists(self, key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def clear(self, namespace_prefix: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def aclear(self, namespace_prefix: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def incr(self, key: str, delta: int = 1) -> int:
        raise NotImplementedError

    @abstractmethod
    async def aincr(self, key: str, delta: int = 1) -> int:
        raise NotImplementedError

    def decr(self, key: str, delta: int = 1) -> int:
        return self.incr(key, -delta)

    async def adecr(self, key: str, delta: int = 1) -> int:
        return await self.aincr(key, -delta)

    def cleanup_expired(self) -> int:  # noqa
        return 0

    async def acleanup_expired(self) -> int:
        return self.cleanup_expired()
