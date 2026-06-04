# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from threading import RLock
from typing import TYPE_CHECKING, ClassVar, BinaryIO

from ns_common.config import NsObjectStorageConfig
from ns_common.storage.backends.local_fs import LocalFileObjectStorageBackend
from ns_common.storage.backends.base import ObjectStorageBackend
from ns_common.storage.backends.minio_backend import MinioObjectStorageBackend
from ns_common.storage.errors import NsObjectStorageConfigurationError
from ns_common.storage.models import NsObjectInfo

if TYPE_CHECKING:
    pass

class NsObjectStorageClient:
    """Thread-safe process-local singleton object storage client.

    Singleton identity is controlled by client name.
    Different config under the same client name is rejected.
    """

    name: str
    config: NsObjectStorageConfig
    _backend: ObjectStorageBackend

    _lock: ClassVar[RLock] = RLock()
    _instances: ClassVar[dict[str, "NsObjectStorageClient"]] = {}
    _default_config: ClassVar[NsObjectStorageConfig | None] = None

    def __new__(cls, name: str = "default", config: NsObjectStorageConfig | None = None) -> "NsObjectStorageClient":
        """Create or return named singleton instance."""
        normalized_name = cls._normalize_client_name(name)

        with cls._lock:
            existing_client = cls._instances.get(normalized_name)
            if existing_client is not None:
                if config is not None and config != existing_client.config:
                    raise NsObjectStorageConfigurationError(f"object storage client already exists with different config: {normalized_name}")
                return existing_client

            selected_config = config or cls._default_config or cls._load_config_from_ns_config()
            instance = super().__new__(cls)
            instance.name = normalized_name
            instance.config = selected_config
            instance._backend = cls._build_backend(selected_config)
            cls._instances[normalized_name] = instance
            return instance

    def __init__(self, name: str = "default", config: NsObjectStorageConfig | None = None) -> None:
        """Keep __init__ idempotent because singleton construction is handled in __new__."""
        _ = (name, config)

    @classmethod
    def configure_default(cls, config: NsObjectStorageConfig) -> None:
        """Configure default object storage config for later default client creation."""
        if not isinstance(config, NsObjectStorageConfig):
            raise NsObjectStorageConfigurationError("default object storage config must be NsObjectStorageConfig")

        with cls._lock:
            cls._default_config = config

    @classmethod
    def get_default(cls) -> "NsObjectStorageClient":
        """Get default object storage client."""
        return cls("default")

    @classmethod
    def get_or_create(cls, name: str = "default", config: NsObjectStorageConfig | None = None) -> "NsObjectStorageClient":
        """Compatibility helper for named singleton access."""
        return cls(name, config)

    @classmethod
    def close_all(cls) -> None:
        """Close all process-local object storage clients."""
        with cls._lock:
            clients = list(cls._instances.values())
            cls._instances.clear()

        for client in clients:
            client.close()

    def bucket_exists(self, bucket: str | None = None) -> bool:
        """Return whether bucket exists."""
        return self._backend.bucket_exists(self._resolve_bucket(bucket))

    def ensure_bucket(self, bucket: str | None = None) -> None:
        """Ensure bucket exists."""
        self._backend.ensure_bucket(self._resolve_bucket(bucket))

    def put_bytes(self, *, object_name: str, data: bytes, bucket: str | None = None, content_type: str | None = None, metadata: dict[str, str] | None = None) -> NsObjectInfo:
        """Upload bytes."""
        return self._backend.put_bytes(
            bucket=self._resolve_bucket(bucket),
            object_name=object_name,
            data=data,
            content_type=content_type,
            metadata=metadata,
        )

    def put_file(self, *, object_name: str, file_path: str | Path, bucket: str | None = None, content_type: str | None = None, metadata: dict[str, str] | None = None) -> NsObjectInfo:
        """Upload file."""
        return self._backend.put_file(
            bucket=self._resolve_bucket(bucket),
            object_name=object_name,
            file_path=Path(file_path),
            content_type=content_type,
            metadata=metadata,
        )

    def put_stream(self, *, object_name: str, stream: BinaryIO, length: int, bucket: str | None = None, content_type: str | None = None, metadata: dict[str, str] | None = None) -> NsObjectInfo:
        """Upload stream."""
        return self._backend.put_stream(
            bucket=self._resolve_bucket(bucket),
            object_name=object_name,
            stream=stream,
            length=length,
            content_type=content_type,
            metadata=metadata,
        )

    def get_bytes(self, *, object_name: str, bucket: str | None = None) -> bytes:
        """Download object as bytes."""
        return self._backend.get_bytes(bucket=self._resolve_bucket(bucket), object_name=object_name)

    def get_file(self, *, object_name: str, file_path: str | Path, bucket: str | None = None) -> None:
        """Download object to file."""
        self._backend.get_file(bucket=self._resolve_bucket(bucket), object_name=object_name, file_path=Path(file_path))

    def get_stream(self, *, object_name: str, bucket: str | None = None) -> BinaryIO:
        """Download object as stream."""
        return self._backend.get_stream(bucket=self._resolve_bucket(bucket), object_name=object_name)

    def stat_object(self, *, object_name: str, bucket: str | None = None) -> NsObjectInfo:
        """Return object metadata."""
        return self._backend.stat_object(bucket=self._resolve_bucket(bucket), object_name=object_name)

    def object_exists(self, *, object_name: str, bucket: str | None = None) -> bool:
        """Return whether object exists."""
        return self._backend.object_exists(bucket=self._resolve_bucket(bucket), object_name=object_name)

    def remove_object(self, *, object_name: str, bucket: str | None = None) -> bool:
        """Remove object."""
        return self._backend.remove_object(bucket=self._resolve_bucket(bucket), object_name=object_name)

    def list_objects(self, *, prefix: str = "", bucket: str | None = None, recursive: bool = True) -> list[NsObjectInfo]:
        """List objects."""
        return self._backend.list_objects(bucket=self._resolve_bucket(bucket), prefix=prefix, recursive=recursive)

    def presigned_get_url(self, *, object_name: str, bucket: str | None = None, expires_seconds: int | None = None) -> str:
        """Build presigned GET URL."""
        return self._backend.presigned_get_url(
            bucket=self._resolve_bucket(bucket),
            object_name=object_name,
            expires_seconds=self._resolve_expires_seconds(expires_seconds, self.config.presigned_get_expires_seconds),
        )

    def presigned_put_url(self, *, object_name: str, bucket: str | None = None, expires_seconds: int | None = None, content_type: str | None = None) -> str:
        """Build presigned PUT URL."""
        return self._backend.presigned_put_url(
            bucket=self._resolve_bucket(bucket),
            object_name=object_name,
            expires_seconds=self._resolve_expires_seconds(expires_seconds, self.config.presigned_put_expires_seconds),
            content_type=content_type,
        )

    def close(self) -> None:
        """Close object storage backend resources and remove singleton reference."""
        with self.__class__._lock:
            existing_client: NsObjectStorageClient | None = self.__class__._instances.get(self.name)
            if existing_client is self:
                self.__class__._instances.pop(self.name, None)

        self._backend.close()

    def _resolve_bucket(self, bucket: str | None = None) -> str:
        """Resolve target bucket."""
        selected_bucket = str(bucket or self.config.default_bucket or "").strip()
        if not selected_bucket:
            raise NsObjectStorageConfigurationError("object storage bucket is required")
        return selected_bucket

    @staticmethod
    def _resolve_expires_seconds(value: int | None, default: int) -> int:
        """Resolve presigned URL expiration seconds."""
        selected_value = default if value is None else value

        if isinstance(selected_value, bool) or not isinstance(selected_value, int):
            raise NsObjectStorageConfigurationError("object storage presigned expires_seconds must be int")

        if selected_value <= 0:
            raise NsObjectStorageConfigurationError("object storage presigned expires_seconds must be positive")

        return selected_value

    @staticmethod
    def _normalize_client_name(name: str) -> str:
        """Normalize singleton client name."""
        if not isinstance(name, str) or not name.strip():
            raise NsObjectStorageConfigurationError("object storage client name must be a non-empty str")
        return name.strip()

    @staticmethod
    def _load_config_from_ns_config() -> NsObjectStorageConfig:
        """Load default object storage config from ns_config."""
        from ns_common.config import ns_config

        return ns_config.object_storage_config

    @staticmethod
    def _build_backend(config: NsObjectStorageConfig) -> MinioObjectStorageBackend | LocalFileObjectStorageBackend:
        """Build object storage backend by explicit configuration."""
        resolved_backend = config.resolved_backend()

        if resolved_backend == "minio":
            return MinioObjectStorageBackend(config)

        if resolved_backend == "local_fs":
            return LocalFileObjectStorageBackend(config)

        raise NsObjectStorageConfigurationError(f"unsupported or unimplemented object storage backend: {config.backend}")
