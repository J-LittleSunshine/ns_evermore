# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, BinaryIO

from ns_common.config import NsObjectStorageConfig
from ns_common.storage.models import NsObjectInfo
from ns_common.storage.utils import (
    apply_object_key_prefix,
    normalize_bucket_name,
    normalize_key_prefix,
    normalize_metadata,
    validate_payload_size,
)

if TYPE_CHECKING:
    pass


class ObjectStorageBackend(Protocol):
    """Internal object storage backend protocol."""

    def bucket_exists(self, bucket: str) -> bool:
        """Return whether bucket exists."""

    def ensure_bucket(self, bucket: str) -> None:
        """Ensure bucket exists."""

    def put_bytes(self, *, bucket: str, object_name: str, data: bytes, content_type: str | None = None, metadata: dict[str, str] | None = None) -> NsObjectInfo:
        """Upload bytes."""

    def put_file(self, *, bucket: str, object_name: str, file_path: Path, content_type: str | None = None, metadata: dict[str, str] | None = None) -> NsObjectInfo:
        """Upload file."""

    def put_stream(self, *, bucket: str, object_name: str, stream: BinaryIO, length: int, content_type: str | None = None, metadata: dict[str, str] | None = None) -> NsObjectInfo:
        """Upload stream."""

    def get_bytes(self, *, bucket: str, object_name: str) -> bytes:
        """Download object as bytes."""

    def get_file(self, *, bucket: str, object_name: str, file_path: Path) -> None:
        """Download object to file."""

    def get_stream(self, *, bucket: str, object_name: str) -> BinaryIO:
        """Download object as stream."""

    def stat_object(self, *, bucket: str, object_name: str) -> NsObjectInfo:
        """Return object metadata."""

    def object_exists(self, *, bucket: str, object_name: str) -> bool:
        """Return whether object exists."""

    def remove_object(self, *, bucket: str, object_name: str) -> bool:
        """Remove object."""

    def list_objects(self, *, bucket: str, prefix: str = "", recursive: bool = True) -> list[NsObjectInfo]:
        """List objects."""

    def presigned_get_url(self, *, bucket: str, object_name: str, expires_seconds: int) -> str:
        """Build presigned GET URL."""

    def presigned_put_url(self, *, bucket: str, object_name: str, expires_seconds: int, content_type: str | None = None) -> str:
        """Build presigned PUT URL."""

    def close(self) -> None:
        """Close backend resources."""


class AsyncObjectStorageBackend(Protocol):
    """Internal async object storage backend protocol."""

    async def bucket_exists(self, bucket: str) -> bool:
        """Return whether bucket exists."""

    async def ensure_bucket(self, bucket: str) -> None:
        """Ensure bucket exists."""

    async def put_bytes(self, *, bucket: str, object_name: str, data: bytes, content_type: str | None = None, metadata: dict[str, str] | None = None) -> NsObjectInfo:
        """Upload bytes."""

    async def put_file(self, *, bucket: str, object_name: str, file_path: Path, content_type: str | None = None, metadata: dict[str, str] | None = None) -> NsObjectInfo:
        """Upload file."""

    async def put_stream(self, *, bucket: str, object_name: str, stream: BinaryIO, length: int, content_type: str | None = None, metadata: dict[str, str] | None = None) -> NsObjectInfo:
        """Upload stream."""

    async def get_bytes(self, *, bucket: str, object_name: str) -> bytes:
        """Download object as bytes."""

    async def get_file(self, *, bucket: str, object_name: str, file_path: Path) -> None:
        """Download object to file."""

    async def get_stream(self, *, bucket: str, object_name: str) -> BinaryIO:
        """Download object as stream."""

    async def stat_object(self, *, bucket: str, object_name: str) -> NsObjectInfo:
        """Return object metadata."""

    async def object_exists(self, *, bucket: str, object_name: str) -> bool:
        """Return whether object exists."""

    async def remove_object(self, *, bucket: str, object_name: str) -> bool:
        """Remove object."""

    async def list_objects(self, *, bucket: str, prefix: str = "", recursive: bool = True) -> list[NsObjectInfo]:
        """List objects."""

    async def presigned_get_url(self, *, bucket: str, object_name: str, expires_seconds: int) -> str:
        """Build presigned GET URL."""

    async def presigned_put_url(self, *, bucket: str, object_name: str, expires_seconds: int, content_type: str | None = None) -> str:
        """Build presigned PUT URL."""

    async def close(self) -> None:
        """Close backend resources."""


class BaseObjectStorageBackend:
    """Base object storage backend."""

    def __init__(self, config: NsObjectStorageConfig) -> None:
        """Initialize base backend."""
        self._config: NsObjectStorageConfig = config
        self._key_prefix: str = config.key_prefix

    @staticmethod
    def _normalize_bucket(bucket: str) -> str:
        """Normalize bucket name."""
        return normalize_bucket_name(bucket)

    def _normalize_object_name(self, object_name: str) -> str:
        """Normalize object name and apply configured prefix."""
        return apply_object_key_prefix(key_prefix=self._key_prefix, object_name=object_name)

    def _normalize_prefix(self, prefix: str | None = "") -> str:
        """Normalize optional listing prefix and apply configured key prefix."""
        raw_prefix: str = "" if prefix is None else str(prefix).strip().strip("/")
        normalized_key_prefix: str = normalize_key_prefix(self._key_prefix)

        if not raw_prefix:
            return f"{normalized_key_prefix}/" if normalized_key_prefix else ""

        normalized_prefix: str = apply_object_key_prefix(key_prefix=self._key_prefix, object_name=raw_prefix)
        if normalized_key_prefix and normalized_prefix == normalized_key_prefix:
            return f"{normalized_key_prefix}/"

        return normalized_prefix

    @staticmethod
    def _normalize_metadata(metadata: dict[str, str] | None) -> dict[str, str]:
        """Normalize object metadata."""
        return normalize_metadata(metadata)

    def _validate_payload_size(self, size: int) -> None:
        """Validate payload size against config."""
        validate_payload_size(size=size, max_object_size=self._config.max_object_size)


class AsyncObjectStorageBackendWrapper:
    """Async wrapper for synchronous object storage backends.

    The current storage backends are IO-bound synchronous implementations.
    This wrapper provides async APIs by running blocking calls in a worker thread.
    """

    def __init__(self, backend: ObjectStorageBackend) -> None:
        """Initialize async wrapper."""
        self._backend: ObjectStorageBackend = backend

    async def bucket_exists(self, bucket: str) -> bool:
        """Return whether bucket exists."""
        return await asyncio.to_thread(self._backend.bucket_exists, bucket)

    async def ensure_bucket(self, bucket: str) -> None:
        """Ensure bucket exists."""
        await asyncio.to_thread(self._backend.ensure_bucket, bucket)

    async def put_bytes(self, *, bucket: str, object_name: str, data: bytes, content_type: str | None = None, metadata: dict[str, str] | None = None) -> NsObjectInfo:
        """Upload bytes."""
        return await asyncio.to_thread(self._backend.put_bytes, bucket=bucket, object_name=object_name, data=data, content_type=content_type, metadata=metadata)

    async def put_file(self, *, bucket: str, object_name: str, file_path: Path, content_type: str | None = None, metadata: dict[str, str] | None = None) -> NsObjectInfo:
        """Upload file."""
        return await asyncio.to_thread(self._backend.put_file, bucket=bucket, object_name=object_name, file_path=file_path, content_type=content_type, metadata=metadata)

    async def put_stream(self, *, bucket: str, object_name: str, stream: BinaryIO, length: int, content_type: str | None = None, metadata: dict[str, str] | None = None) -> NsObjectInfo:
        """Upload stream."""
        return await asyncio.to_thread(self._backend.put_stream, bucket=bucket, object_name=object_name, stream=stream, length=length, content_type=content_type, metadata=metadata)

    async def get_bytes(self, *, bucket: str, object_name: str) -> bytes:
        """Download object as bytes."""
        return await asyncio.to_thread(self._backend.get_bytes, bucket=bucket, object_name=object_name)

    async def get_file(self, *, bucket: str, object_name: str, file_path: Path) -> None:
        """Download object to file."""
        await asyncio.to_thread(self._backend.get_file, bucket=bucket, object_name=object_name, file_path=file_path)

    async def get_stream(self, *, bucket: str, object_name: str) -> BinaryIO:
        """Download object as stream."""
        return await asyncio.to_thread(self._backend.get_stream, bucket=bucket, object_name=object_name)

    async def stat_object(self, *, bucket: str, object_name: str) -> NsObjectInfo:
        """Return object metadata."""
        return await asyncio.to_thread(self._backend.stat_object, bucket=bucket, object_name=object_name)

    async def object_exists(self, *, bucket: str, object_name: str) -> bool:
        """Return whether object exists."""
        return await asyncio.to_thread(self._backend.object_exists, bucket=bucket, object_name=object_name)

    async def remove_object(self, *, bucket: str, object_name: str) -> bool:
        """Remove object."""
        return await asyncio.to_thread(self._backend.remove_object, bucket=bucket, object_name=object_name)

    async def list_objects(self, *, bucket: str, prefix: str = "", recursive: bool = True) -> list[NsObjectInfo]:
        """List objects."""
        return await asyncio.to_thread(self._backend.list_objects, bucket=bucket, prefix=prefix, recursive=recursive)

    async def presigned_get_url(self, *, bucket: str, object_name: str, expires_seconds: int) -> str:
        """Build presigned GET URL."""
        return await asyncio.to_thread(self._backend.presigned_get_url, bucket=bucket, object_name=object_name, expires_seconds=expires_seconds)

    async def presigned_put_url(self, *, bucket: str, object_name: str, expires_seconds: int, content_type: str | None = None) -> str:
        """Build presigned PUT URL."""
        return await asyncio.to_thread(self._backend.presigned_put_url, bucket=bucket, object_name=object_name, expires_seconds=expires_seconds, content_type=content_type)

    async def close(self) -> None:
        """Close backend resources."""
        await asyncio.to_thread(self._backend.close)
