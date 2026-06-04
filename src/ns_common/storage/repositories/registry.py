# -*- coding: utf-8 -*-
from __future__ import annotations

import inspect
from threading import RLock
from typing import TYPE_CHECKING, ClassVar, cast

from ns_common.storage.contracts import AsyncNsObjectRefRepository, NsObjectRefRepository
from ns_common.storage.errors import NsObjectStorageConfigurationError, NsObjectStorageValidationError
from ns_common.storage.repositories.memory import AsyncNsInMemoryObjectRefRepository, NsInMemoryObjectRefRepository

if TYPE_CHECKING:
    pass

_SYNC_REPOSITORY_METHODS: tuple[str, ...] = (
    "save_object_ref",
    "get_object_ref",
    "list_object_refs",
    "delete_object_ref",
)

_ASYNC_REPOSITORY_METHODS: tuple[str, ...] = (
    "save_object_ref",
    "get_object_ref",
    "list_object_refs",
    "delete_object_ref",
)


class NsObjectRefRepositoryRegistry:
    """Process-local registry for object reference repositories.

    This registry is intended to decouple business modules from concrete object
    reference repository implementations.
    """

    _lock: ClassVar[RLock] = RLock()
    _repositories: ClassVar[dict[str, NsObjectRefRepository]] = {}
    _async_repositories: ClassVar[dict[str, AsyncNsObjectRefRepository]] = {}

    @classmethod
    def register(cls, repository: NsObjectRefRepository, *, name: str = "default", replace: bool = False) -> None:
        """Register sync object reference repository."""
        normalized_name: str = cls._normalize_name(name)
        validated_repository: NsObjectRefRepository = cls._validate_sync_repository(repository)

        with cls._lock:
            if not replace and normalized_name in cls._repositories:
                raise NsObjectStorageConfigurationError(f"object ref repository already registered: {normalized_name}")

            cls._repositories[normalized_name] = validated_repository

    @classmethod
    def get(cls, name: str = "default") -> NsObjectRefRepository:
        """Get sync object reference repository.

        If repository is not registered, a named in-memory repository is returned
        as the default fallback without marking it as explicitly registered.
        """
        normalized_name: str = cls._normalize_name(name)

        with cls._lock:
            repository: NsObjectRefRepository | None = cls._repositories.get(normalized_name)
            if repository is not None:
                return repository

        return NsInMemoryObjectRefRepository.get_default(normalized_name)

    @classmethod
    def unregister(cls, name: str = "default") -> bool:
        """Unregister sync object reference repository."""
        normalized_name: str = cls._normalize_name(name)

        with cls._lock:
            return cls._repositories.pop(normalized_name, None) is not None

    @classmethod
    def is_registered(cls, name: str = "default") -> bool:
        """Return whether sync repository is explicitly registered."""
        normalized_name: str = cls._normalize_name(name)

        with cls._lock:
            return normalized_name in cls._repositories

    @classmethod
    def clear(cls) -> None:
        """Clear all registered sync repositories."""
        with cls._lock:
            cls._repositories.clear()

    @classmethod
    def register_async(cls, repository: AsyncNsObjectRefRepository, *, name: str = "default", replace: bool = False) -> None:
        """Register async object reference repository."""
        normalized_name: str = cls._normalize_name(name)
        validated_repository: AsyncNsObjectRefRepository = cls._validate_async_repository(repository)

        with cls._lock:
            if not replace and normalized_name in cls._async_repositories:
                raise NsObjectStorageConfigurationError(f"async object ref repository already registered: {normalized_name}")

            cls._async_repositories[normalized_name] = validated_repository

    @classmethod
    def get_async(cls, name: str = "default") -> AsyncNsObjectRefRepository:
        """Get async object reference repository.

        If repository is not registered, a named async in-memory repository is
        returned as the default fallback without marking it as explicitly registered.
        """
        normalized_name: str = cls._normalize_name(name)

        with cls._lock:
            repository: AsyncNsObjectRefRepository | None = cls._async_repositories.get(normalized_name)
            if repository is not None:
                return repository

        return AsyncNsInMemoryObjectRefRepository.get_default(normalized_name)

    @classmethod
    def unregister_async(cls, name: str = "default") -> bool:
        """Unregister async object reference repository."""
        normalized_name: str = cls._normalize_name(name)

        with cls._lock:
            return cls._async_repositories.pop(normalized_name, None) is not None

    @classmethod
    def is_async_registered(cls, name: str = "default") -> bool:
        """Return whether async repository is explicitly registered."""
        normalized_name: str = cls._normalize_name(name)

        with cls._lock:
            return normalized_name in cls._async_repositories

    @classmethod
    def clear_async(cls) -> None:
        """Clear all registered async repositories."""
        with cls._lock:
            cls._async_repositories.clear()

    @classmethod
    def clear_all(cls) -> None:
        """Clear all sync and async registered repositories and default fallback repositories."""
        with cls._lock:
            cls._repositories.clear()
            cls._async_repositories.clear()

        NsInMemoryObjectRefRepository.clear_defaults()
        AsyncNsInMemoryObjectRefRepository.clear_defaults()

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize repository registry name."""
        if not isinstance(name, str) or not name.strip():
            raise NsObjectStorageValidationError("object ref repository registry name must be a non-empty str")
        return name.strip()

    @staticmethod
    def _validate_sync_repository(repository: object) -> NsObjectRefRepository:
        """Validate sync repository shape before registration."""
        if repository is None:
            raise NsObjectStorageConfigurationError("object ref repository cannot be None")

        for method_name in _SYNC_REPOSITORY_METHODS:
            method = getattr(repository, method_name, None)
            if not callable(method):
                raise NsObjectStorageConfigurationError(f"object ref repository missing callable method: {method_name}")

        return cast(NsObjectRefRepository, repository)

    @staticmethod
    def _validate_async_repository(repository: object) -> AsyncNsObjectRefRepository:
        """Validate async repository shape before registration."""
        if repository is None:
            raise NsObjectStorageConfigurationError("async object ref repository cannot be None")

        for method_name in _ASYNC_REPOSITORY_METHODS:
            method = getattr(repository, method_name, None)
            if not callable(method):
                raise NsObjectStorageConfigurationError(f"async object ref repository missing callable method: {method_name}")

            if not inspect.iscoroutinefunction(method):
                raise NsObjectStorageConfigurationError(f"async object ref repository method must be async: {method_name}")

        return cast(AsyncNsObjectRefRepository, repository)


def register_object_ref_repository(repository: NsObjectRefRepository, *, name: str = "default", replace: bool = False) -> None:
    """Register sync object reference repository."""
    NsObjectRefRepositoryRegistry.register(repository, name=name, replace=replace)


def get_object_ref_repository(name: str = "default") -> NsObjectRefRepository:
    """Get sync object reference repository."""
    return NsObjectRefRepositoryRegistry.get(name)


def unregister_object_ref_repository(name: str = "default") -> bool:
    """Unregister sync object reference repository."""
    return NsObjectRefRepositoryRegistry.unregister(name)


def register_async_object_ref_repository(repository: AsyncNsObjectRefRepository, *, name: str = "default", replace: bool = False) -> None:
    """Register async object reference repository."""
    NsObjectRefRepositoryRegistry.register_async(repository, name=name, replace=replace)


def get_async_object_ref_repository(name: str = "default") -> AsyncNsObjectRefRepository:
    """Get async object reference repository."""
    return NsObjectRefRepositoryRegistry.get_async(name)


def unregister_async_object_ref_repository(name: str = "default") -> bool:
    """Unregister async object reference repository."""
    return NsObjectRefRepositoryRegistry.unregister_async(name)


def clear_object_ref_repository_registry() -> None:
    """Clear sync and async object reference repository registry."""
    NsObjectRefRepositoryRegistry.clear_all()


def _type_check_repository_registry() -> None:
    """Validate registry return types for static type checkers."""
    sync_repository: NsObjectRefRepository = get_object_ref_repository()
    async_repository: AsyncNsObjectRefRepository = get_async_object_ref_repository()
    _ = (sync_repository, async_repository)
