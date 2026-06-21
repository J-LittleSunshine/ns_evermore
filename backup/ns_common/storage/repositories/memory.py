# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import replace
from threading import RLock
from typing import TYPE_CHECKING, ClassVar

from ns_common.storage.contracts import AsyncNsObjectRefRepository, NsObjectRefRepository
from ns_common.storage.errors import NsObjectStorageValidationError
from ns_common.storage.models import NsObjectRef
from ns_common.storage.naming import (
    normalize_module_code,
    normalize_original_filename,
    normalize_resource_id,
    normalize_resource_type,
)
from ns_common.storage.utils import normalize_bucket_name, normalize_metadata, normalize_object_name

if TYPE_CHECKING:
    pass

_ObjectRefKey = tuple[str, str]


class NsInMemoryObjectRefRepository:
    """Thread-safe in-memory object reference repository.

    This repository is intended for local development, tests, demos, and protocol validation.
    It is process-local and does not provide durable persistence.
    """

    _default_lock: ClassVar[RLock] = RLock()
    _default_instances: ClassVar[dict[str, "NsInMemoryObjectRefRepository"]] = {}

    def __init__(self) -> None:
        """Initialize in-memory object reference repository."""
        self._lock: RLock = RLock()
        self._objects: dict[_ObjectRefKey, NsObjectRef] = {}

    @classmethod
    def get_default(cls, name: str = "default") -> "NsInMemoryObjectRefRepository":
        """Get process-local named default repository instance."""
        normalized_name = cls._normalize_repository_name(name)

        with cls._default_lock:
            repository = cls._default_instances.get(normalized_name)
            if repository is not None:
                return repository

            repository = cls()
            cls._default_instances[normalized_name] = repository
            return repository

    @classmethod
    def clear_defaults(cls) -> None:
        """Clear all named default repository instances."""
        with cls._default_lock:
            cls._default_instances.clear()

    def save_object_ref(self, object_ref: NsObjectRef) -> NsObjectRef:
        """Persist object reference and return saved reference."""
        normalized_ref = self._normalize_object_ref(object_ref)
        key = self._build_key(bucket=normalized_ref.bucket, object_name=normalized_ref.object_name)

        with self._lock:
            self._objects[key] = normalized_ref
            return self._copy_object_ref(normalized_ref)

    def get_object_ref(self, *, bucket: str, object_name: str) -> NsObjectRef | None:
        """Get one object reference by bucket and object name."""
        key = self._build_key(bucket=bucket, object_name=object_name)

        with self._lock:
            object_ref = self._objects.get(key)
            if object_ref is None:
                return None
            return self._copy_object_ref(object_ref)

    def list_object_refs(self, *, module_code: str, resource_type: str, resource_id: str | int | None = None) -> list[NsObjectRef]:
        """List object references by business resource identity."""
        normalized_module_code = normalize_module_code(module_code)
        normalized_resource_type = normalize_resource_type(resource_type)
        normalized_resource_id = normalize_resource_id(resource_id)

        with self._lock:
            result = [
                self._copy_object_ref(object_ref)
                for object_ref in self._objects.values()
                if object_ref.module_code == normalized_module_code
                   and object_ref.resource_type == normalized_resource_type
                   and (normalized_resource_id is None or object_ref.resource_id == normalized_resource_id)
            ]

        return sorted(
            result, key=lambda item: (
                item.bucket,
                item.object_name
            )
        )

    def delete_object_ref(self, *, bucket: str, object_name: str) -> bool:
        """Delete object reference metadata, not the physical object."""
        key = self._build_key(bucket=bucket, object_name=object_name)

        with self._lock:
            return self._objects.pop(key, None) is not None

    def exists_object_ref(self, *, bucket: str, object_name: str) -> bool:
        """Return whether object reference exists."""
        key = self._build_key(bucket=bucket, object_name=object_name)

        with self._lock:
            return key in self._objects

    def count_object_refs(self) -> int:
        """Return total object reference count."""
        with self._lock:
            return len(self._objects)

    def clear(self) -> None:
        """Clear all object references in this repository."""
        with self._lock:
            self._objects.clear()

    def snapshot(self) -> list[NsObjectRef]:
        """Return a sorted snapshot of all object references."""
        with self._lock:
            result = [
                self._copy_object_ref(object_ref)
                for object_ref in self._objects.values()
            ]

        return sorted(
            result, key=lambda item: (
                item.bucket,
                item.object_name
            )
        )

    @staticmethod
    def _build_key(*, bucket: str, object_name: str) -> _ObjectRefKey:
        """Build normalized object reference key."""
        return normalize_bucket_name(bucket), normalize_object_name(object_name)

    @staticmethod
    def _normalize_object_ref(object_ref: NsObjectRef) -> NsObjectRef:
        """Normalize object reference before storing."""
        if not isinstance(object_ref, NsObjectRef):
            raise NsObjectStorageValidationError("object_ref must be NsObjectRef")

        backend = str(object_ref.backend or "").strip()
        if not backend:
            raise NsObjectStorageValidationError("object_ref backend cannot be empty")

        content_type = str(object_ref.content_type).strip() if object_ref.content_type else None
        etag = str(object_ref.etag).strip() if object_ref.etag else None
        sha256 = str(object_ref.sha256).strip().lower() if object_ref.sha256 else None
        version_id = str(object_ref.version_id).strip() if object_ref.version_id else None

        return NsObjectRef(
            bucket=normalize_bucket_name(object_ref.bucket),
            object_name=normalize_object_name(object_ref.object_name),
            backend=backend,
            module_code=normalize_module_code(object_ref.module_code),
            resource_type=normalize_resource_type(object_ref.resource_type),
            resource_id=normalize_resource_id(object_ref.resource_id),
            original_filename=normalize_original_filename(object_ref.original_filename),
            content_type=content_type,
            size=object_ref.size,
            etag=etag,
            sha256=sha256,
            version_id=version_id,
            metadata=normalize_metadata(object_ref.metadata),
        )

    @staticmethod
    def _copy_object_ref(object_ref: NsObjectRef) -> NsObjectRef:
        """Return object reference copy with copied metadata mapping."""
        return replace(object_ref, metadata=dict(object_ref.metadata))

    @staticmethod
    def _normalize_repository_name(name: str) -> str:
        """Normalize named default repository name."""
        if not isinstance(name, str) or not name.strip():
            raise NsObjectStorageValidationError("object ref repository name must be a non-empty str")
        return name.strip()


class AsyncNsInMemoryObjectRefRepository:
    """Async in-memory object reference repository.

    This class wraps the synchronous in-memory repository.
    It is still process-local and non-durable.
    """

    _default_lock: ClassVar[RLock] = RLock()
    _default_instances: ClassVar[dict[str, "AsyncNsInMemoryObjectRefRepository"]] = {}

    def __init__(self, repository: NsInMemoryObjectRefRepository | None = None) -> None:
        """Initialize async in-memory object reference repository."""
        self._repository: NsInMemoryObjectRefRepository = repository or NsInMemoryObjectRefRepository()

    @classmethod
    def get_default(cls, name: str = "default") -> "AsyncNsInMemoryObjectRefRepository":
        """Get process-local named default async repository instance."""
        normalized_name = NsInMemoryObjectRefRepository._normalize_repository_name(name)

        with cls._default_lock:
            repository = cls._default_instances.get(normalized_name)
            if repository is not None:
                return repository

            sync_repository = NsInMemoryObjectRefRepository.get_default(normalized_name)
            repository = cls(sync_repository)
            cls._default_instances[normalized_name] = repository
            return repository

    @classmethod
    def clear_defaults(cls) -> None:
        """Clear all named default async repository instances."""
        with cls._default_lock:
            cls._default_instances.clear()

    async def save_object_ref(self, object_ref: NsObjectRef) -> NsObjectRef:
        """Persist object reference and return saved reference."""
        return self._repository.save_object_ref(object_ref)

    async def get_object_ref(self, *, bucket: str, object_name: str) -> NsObjectRef | None:
        """Get one object reference by bucket and object name."""
        return self._repository.get_object_ref(bucket=bucket, object_name=object_name)

    async def list_object_refs(self, *, module_code: str, resource_type: str, resource_id: str | int | None = None) -> list[NsObjectRef]:
        """List object references by business resource identity."""
        return self._repository.list_object_refs(module_code=module_code, resource_type=resource_type, resource_id=resource_id)

    async def delete_object_ref(self, *, bucket: str, object_name: str) -> bool:
        """Delete object reference metadata, not the physical object."""
        return self._repository.delete_object_ref(bucket=bucket, object_name=object_name)

    async def exists_object_ref(self, *, bucket: str, object_name: str) -> bool:
        """Return whether object reference exists."""
        return self._repository.exists_object_ref(bucket=bucket, object_name=object_name)

    async def count_object_refs(self) -> int:
        """Return total object reference count."""
        return self._repository.count_object_refs()

    async def clear(self) -> None:
        """Clear all object references in this repository."""
        self._repository.clear()

    async def snapshot(self) -> list[NsObjectRef]:
        """Return a sorted snapshot of all object references."""
        return self._repository.snapshot()


def _type_check_repositories() -> None:
    """Validate repository implementations against protocols for static type checkers."""
    sync_repository: NsObjectRefRepository = NsInMemoryObjectRefRepository()
    async_repository: AsyncNsObjectRefRepository = AsyncNsInMemoryObjectRefRepository()
    _ = (
        sync_repository,
        async_repository
    )
