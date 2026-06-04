# -*- coding: utf-8 -*-
from __future__ import annotations

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
