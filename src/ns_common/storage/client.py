# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from threading import RLock
from typing import TYPE_CHECKING, BinaryIO, ClassVar

from ns_common.config import NsObjectStorageConfig
from ns_common.storage.backends.async_local_fs import AsyncLocalFileObjectStorageBackend
from ns_common.storage.backends.async_minio_backend import AsyncMinioObjectStorageBackend
from ns_common.storage.backends.base import AsyncObjectStorageBackend, ObjectStorageBackend
from ns_common.storage.backends.local_fs import LocalFileObjectStorageBackend
from ns_common.storage.backends.minio_backend import MinioObjectStorageBackend
from ns_common.storage.contracts import NsObjectUploadContext
from ns_common.storage.errors import NsObjectStorageConfigurationError
from ns_common.storage.hashing import calculate_sha256_bytes, calculate_sha256_file, calculate_sha256_stream
from ns_common.storage.models import NsObjectInfo, NsObjectUploadResult
from ns_common.storage.naming import build_object_name
from ns_common.storage.refs import build_object_ref, build_standard_metadata

if TYPE_CHECKING:
    pass


class NsObjectStorageClient:
    """Thread-safe process-local singleton object storage client."""

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

    def put_bytes_with_context(self, *, data: bytes, context: NsObjectUploadContext) -> NsObjectUploadResult:
        """Upload bytes by standard upload context."""
        normalized_context = context.normalized()

        return self.put_bytes_with_ref(
            data=data,
            module_code=normalized_context.module_code,
            resource_type=normalized_context.resource_type,
            resource_id=normalized_context.resource_id,
            original_filename=normalized_context.original_filename,
            object_name=normalized_context.object_name,
            bucket=normalized_context.bucket,
            content_type=normalized_context.content_type,
            uploaded_by=normalized_context.uploaded_by,
            trace_id=normalized_context.trace_id,
            extra_metadata=normalized_context.extra_metadata,
        )

    def put_file_with_context(self, *, file_path: str | Path, context: NsObjectUploadContext) -> NsObjectUploadResult:
        """Upload file by standard upload context."""
        normalized_context = context.normalized()

        return self.put_file_with_ref(
            file_path=file_path,
            module_code=normalized_context.module_code,
            resource_type=normalized_context.resource_type,
            resource_id=normalized_context.resource_id,
            original_filename=normalized_context.original_filename,
            object_name=normalized_context.object_name,
            bucket=normalized_context.bucket,
            content_type=normalized_context.content_type,
            uploaded_by=normalized_context.uploaded_by,
            trace_id=normalized_context.trace_id,
            extra_metadata=normalized_context.extra_metadata,
        )

    def put_stream_with_context(self, *, stream: BinaryIO, length: int, context: NsObjectUploadContext, sha256: str | None = None) -> NsObjectUploadResult:
        """Upload stream by standard upload context."""
        normalized_context = context.normalized()

        return self.put_stream_with_ref(
            stream=stream,
            length=length,
            module_code=normalized_context.module_code,
            resource_type=normalized_context.resource_type,
            resource_id=normalized_context.resource_id,
            original_filename=normalized_context.original_filename,
            object_name=normalized_context.object_name,
            bucket=normalized_context.bucket,
            content_type=normalized_context.content_type,
            uploaded_by=normalized_context.uploaded_by,
            trace_id=normalized_context.trace_id,
            extra_metadata=normalized_context.extra_metadata,
            sha256=sha256,
        )

    def put_bytes_with_ref(
            self,
            *,
            data: bytes,
            module_code: str,
            resource_type: str,
            resource_id: str | int | None = None,
            original_filename: str | None = None,
            object_name: str | None = None,
            bucket: str | None = None,
            content_type: str | None = None,
            uploaded_by: str | int | None = None,
            trace_id: str | None = None,
            extra_metadata: dict[str, str] | None = None,
    ) -> NsObjectUploadResult:
        """Upload bytes and build standard object reference."""
        sha256: str = calculate_sha256_bytes(data)
        selected_object_name: str = object_name or build_object_name(
            module_code=module_code,
            resource_type=resource_type,
            resource_id=resource_id,
            original_filename=original_filename,
        )
        metadata: dict[str, str] = build_standard_metadata(
            module_code=module_code,
            resource_type=resource_type,
            resource_id=resource_id,
            original_filename=original_filename,
            uploaded_by=uploaded_by,
            trace_id=trace_id,
            sha256=sha256,
            extra_metadata=extra_metadata,
        )

        object_info = self.put_bytes(
            bucket=bucket,
            object_name=selected_object_name,
            data=data,
            content_type=content_type,
            metadata=metadata,
        )
        object_ref = build_object_ref(
            config=self.config,
            object_info=object_info,
            module_code=module_code,
            resource_type=resource_type,
            resource_id=resource_id,
            original_filename=original_filename,
            sha256=sha256,
            extra_metadata=metadata,
        )

        return NsObjectUploadResult(object_info=object_info, object_ref=object_ref)

    def put_file_with_ref(
            self,
            *,
            file_path: str | Path,
            module_code: str,
            resource_type: str,
            resource_id: str | int | None = None,
            original_filename: str | None = None,
            object_name: str | None = None,
            bucket: str | None = None,
            content_type: str | None = None,
            uploaded_by: str | int | None = None,
            trace_id: str | None = None,
            extra_metadata: dict[str, str] | None = None,
    ) -> NsObjectUploadResult:
        """Upload file and build standard object reference."""
        source_path: Path = Path(file_path)
        selected_original_filename: str | None = original_filename or source_path.name
        sha256: str = calculate_sha256_file(source_path)
        selected_object_name: str = object_name or build_object_name(
            module_code=module_code,
            resource_type=resource_type,
            resource_id=resource_id,
            original_filename=selected_original_filename,
        )
        metadata: dict[str, str] = build_standard_metadata(
            module_code=module_code,
            resource_type=resource_type,
            resource_id=resource_id,
            original_filename=selected_original_filename,
            uploaded_by=uploaded_by,
            trace_id=trace_id,
            sha256=sha256,
            extra_metadata=extra_metadata,
        )

        object_info = self.put_file(
            bucket=bucket,
            object_name=selected_object_name,
            file_path=source_path,
            content_type=content_type,
            metadata=metadata,
        )
        object_ref = build_object_ref(
            config=self.config,
            object_info=object_info,
            module_code=module_code,
            resource_type=resource_type,
            resource_id=resource_id,
            original_filename=selected_original_filename,
            sha256=sha256,
            extra_metadata=metadata,
        )

        return NsObjectUploadResult(object_info=object_info, object_ref=object_ref)

    def put_stream_with_ref(
            self,
            *,
            stream: BinaryIO,
            length: int,
            module_code: str,
            resource_type: str,
            resource_id: str | int | None = None,
            original_filename: str | None = None,
            object_name: str | None = None,
            bucket: str | None = None,
            content_type: str | None = None,
            uploaded_by: str | int | None = None,
            trace_id: str | None = None,
            extra_metadata: dict[str, str] | None = None,
            sha256: str | None = None,
    ) -> NsObjectUploadResult:
        """Upload stream and build standard object reference.

        If sha256 is not provided, this method calculates it by reading the stream.
        The stream must be seekable so it can be rewound before upload.
        """
        if sha256 is None:
            selected_sha256: str = calculate_sha256_stream(stream)
            try:
                stream.seek(0)
            except Exception as exc:  # noqa
                raise NsObjectStorageConfigurationError("object storage stream must be seekable when sha256 is not provided") from exc
        else:
            selected_sha256 = str(sha256).strip().lower()

        selected_object_name: str = object_name or build_object_name(
            module_code=module_code,
            resource_type=resource_type,
            resource_id=resource_id,
            original_filename=original_filename,
        )
        metadata: dict[str, str] = build_standard_metadata(
            module_code=module_code,
            resource_type=resource_type,
            resource_id=resource_id,
            original_filename=original_filename,
            uploaded_by=uploaded_by,
            trace_id=trace_id,
            sha256=selected_sha256,
            extra_metadata=extra_metadata,
        )

        object_info = self.put_stream(
            bucket=bucket,
            object_name=selected_object_name,
            stream=stream,
            length=length,
            content_type=content_type,
            metadata=metadata,
        )
        object_ref = build_object_ref(
            config=self.config,
            object_info=object_info,
            module_code=module_code,
            resource_type=resource_type,
            resource_id=resource_id,
            original_filename=original_filename,
            sha256=selected_sha256,
            extra_metadata=metadata,
        )

        return NsObjectUploadResult(object_info=object_info, object_ref=object_ref)

    def bucket_exists(self, bucket: str | None = None) -> bool:
        """Return whether bucket exists."""
        return self._backend.bucket_exists(self._resolve_bucket(bucket))

    def ensure_bucket(self, bucket: str | None = None) -> None:
        """Ensure bucket exists."""
        self._backend.ensure_bucket(self._resolve_bucket(bucket))

    def put_bytes(self, *, object_name: str, data: bytes, bucket: str | None = None, content_type: str | None = None, metadata: dict[str, str] | None = None) -> NsObjectInfo:
        """Upload bytes."""
        return self._backend.put_bytes(bucket=self._resolve_bucket(bucket), object_name=object_name, data=data, content_type=content_type, metadata=metadata)

    def put_file(self, *, object_name: str, file_path: str | Path, bucket: str | None = None, content_type: str | None = None, metadata: dict[str, str] | None = None) -> NsObjectInfo:
        """Upload file."""
        return self._backend.put_file(bucket=self._resolve_bucket(bucket), object_name=object_name, file_path=Path(file_path), content_type=content_type, metadata=metadata)

    def put_stream(self, *, object_name: str, stream: BinaryIO, length: int, bucket: str | None = None, content_type: str | None = None, metadata: dict[str, str] | None = None) -> NsObjectInfo:
        """Upload stream."""
        return self._backend.put_stream(bucket=self._resolve_bucket(bucket), object_name=object_name, stream=stream, length=length, content_type=content_type, metadata=metadata)

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
        return self._backend.presigned_get_url(bucket=self._resolve_bucket(bucket), object_name=object_name, expires_seconds=self._resolve_expires_seconds(expires_seconds, self.config.presigned_get_expires_seconds))

    def presigned_put_url(self, *, object_name: str, bucket: str | None = None, expires_seconds: int | None = None, content_type: str | None = None) -> str:
        """Build presigned PUT URL."""
        return self._backend.presigned_put_url(bucket=self._resolve_bucket(bucket), object_name=object_name, expires_seconds=self._resolve_expires_seconds(expires_seconds, self.config.presigned_put_expires_seconds), content_type=content_type)

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


class AsyncNsObjectStorageClient:
    """Thread-safe process-local singleton async object storage client."""

    name: str
    config: NsObjectStorageConfig
    _backend: AsyncObjectStorageBackend

    _lock: ClassVar[RLock] = RLock()
    _instances: ClassVar[dict[str, "AsyncNsObjectStorageClient"]] = {}
    _default_config: ClassVar[NsObjectStorageConfig | None] = None

    def __new__(cls, name: str = "default", config: NsObjectStorageConfig | None = None) -> "AsyncNsObjectStorageClient":
        """Create or return named singleton instance."""
        normalized_name = cls._normalize_client_name(name)

        with cls._lock:
            existing_client = cls._instances.get(normalized_name)
            if existing_client is not None:
                if config is not None and config != existing_client.config:
                    raise NsObjectStorageConfigurationError(f"async object storage client already exists with different config: {normalized_name}")
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
        """Configure default async object storage config for later default client creation."""
        if not isinstance(config, NsObjectStorageConfig):
            raise NsObjectStorageConfigurationError("default async object storage config must be NsObjectStorageConfig")

        with cls._lock:
            cls._default_config = config

    @classmethod
    def get_default(cls) -> "AsyncNsObjectStorageClient":
        """Get default async object storage client."""
        return cls("default")

    @classmethod
    def get_or_create(cls, name: str = "default", config: NsObjectStorageConfig | None = None) -> "AsyncNsObjectStorageClient":
        """Compatibility helper for named singleton access."""
        return cls(name, config)

    @classmethod
    async def close_all(cls) -> None:
        """Close all process-local async object storage clients."""
        with cls._lock:
            clients = list(cls._instances.values())
            cls._instances.clear()

        for client in clients:
            await client.close()

    async def put_bytes_with_context(self, *, data: bytes, context: NsObjectUploadContext) -> NsObjectUploadResult:
        """Upload bytes by standard upload context."""
        normalized_context = context.normalized()

        return await self.put_bytes_with_ref(
            data=data,
            module_code=normalized_context.module_code,
            resource_type=normalized_context.resource_type,
            resource_id=normalized_context.resource_id,
            original_filename=normalized_context.original_filename,
            object_name=normalized_context.object_name,
            bucket=normalized_context.bucket,
            content_type=normalized_context.content_type,
            uploaded_by=normalized_context.uploaded_by,
            trace_id=normalized_context.trace_id,
            extra_metadata=normalized_context.extra_metadata,
        )

    async def put_file_with_context(self, *, file_path: str | Path, context: NsObjectUploadContext) -> NsObjectUploadResult:
        """Upload file by standard upload context."""
        normalized_context = context.normalized()

        return await self.put_file_with_ref(
            file_path=file_path,
            module_code=normalized_context.module_code,
            resource_type=normalized_context.resource_type,
            resource_id=normalized_context.resource_id,
            original_filename=normalized_context.original_filename,
            object_name=normalized_context.object_name,
            bucket=normalized_context.bucket,
            content_type=normalized_context.content_type,
            uploaded_by=normalized_context.uploaded_by,
            trace_id=normalized_context.trace_id,
            extra_metadata=normalized_context.extra_metadata,
        )

    async def put_stream_with_context(self, *, stream: BinaryIO, length: int, context: NsObjectUploadContext, sha256: str | None = None) -> NsObjectUploadResult:
        """Upload stream by standard upload context."""
        normalized_context = context.normalized()

        return await self.put_stream_with_ref(
            stream=stream,
            length=length,
            module_code=normalized_context.module_code,
            resource_type=normalized_context.resource_type,
            resource_id=normalized_context.resource_id,
            original_filename=normalized_context.original_filename,
            object_name=normalized_context.object_name,
            bucket=normalized_context.bucket,
            content_type=normalized_context.content_type,
            uploaded_by=normalized_context.uploaded_by,
            trace_id=normalized_context.trace_id,
            extra_metadata=normalized_context.extra_metadata,
            sha256=sha256,
        )

    async def put_bytes_with_ref(
            self,
            *,
            data: bytes,
            module_code: str,
            resource_type: str,
            resource_id: str | int | None = None,
            original_filename: str | None = None,
            object_name: str | None = None,
            bucket: str | None = None,
            content_type: str | None = None,
            uploaded_by: str | int | None = None,
            trace_id: str | None = None,
            extra_metadata: dict[str, str] | None = None,
    ) -> NsObjectUploadResult:
        """Upload bytes and build standard object reference."""
        sha256: str = calculate_sha256_bytes(data)
        selected_object_name: str = object_name or build_object_name(
            module_code=module_code,
            resource_type=resource_type,
            resource_id=resource_id,
            original_filename=original_filename,
        )
        metadata: dict[str, str] = build_standard_metadata(
            module_code=module_code,
            resource_type=resource_type,
            resource_id=resource_id,
            original_filename=original_filename,
            uploaded_by=uploaded_by,
            trace_id=trace_id,
            sha256=sha256,
            extra_metadata=extra_metadata,
        )

        object_info = await self.put_bytes(
            bucket=bucket,
            object_name=selected_object_name,
            data=data,
            content_type=content_type,
            metadata=metadata,
        )
        object_ref = build_object_ref(
            config=self.config,
            object_info=object_info,
            module_code=module_code,
            resource_type=resource_type,
            resource_id=resource_id,
            original_filename=original_filename,
            sha256=sha256,
            extra_metadata=metadata,
        )

        return NsObjectUploadResult(object_info=object_info, object_ref=object_ref)

    async def put_file_with_ref(
            self,
            *,
            file_path: str | Path,
            module_code: str,
            resource_type: str,
            resource_id: str | int | None = None,
            original_filename: str | None = None,
            object_name: str | None = None,
            bucket: str | None = None,
            content_type: str | None = None,
            uploaded_by: str | int | None = None,
            trace_id: str | None = None,
            extra_metadata: dict[str, str] | None = None,
    ) -> NsObjectUploadResult:
        """Upload file and build standard object reference."""
        source_path: Path = Path(file_path)
        selected_original_filename: str | None = original_filename or source_path.name
        sha256: str = calculate_sha256_file(source_path)
        selected_object_name: str = object_name or build_object_name(
            module_code=module_code,
            resource_type=resource_type,
            resource_id=resource_id,
            original_filename=selected_original_filename,
        )
        metadata: dict[str, str] = build_standard_metadata(
            module_code=module_code,
            resource_type=resource_type,
            resource_id=resource_id,
            original_filename=selected_original_filename,
            uploaded_by=uploaded_by,
            trace_id=trace_id,
            sha256=sha256,
            extra_metadata=extra_metadata,
        )

        object_info = await self.put_file(
            bucket=bucket,
            object_name=selected_object_name,
            file_path=source_path,
            content_type=content_type,
            metadata=metadata,
        )
        object_ref = build_object_ref(
            config=self.config,
            object_info=object_info,
            module_code=module_code,
            resource_type=resource_type,
            resource_id=resource_id,
            original_filename=selected_original_filename,
            sha256=sha256,
            extra_metadata=metadata,
        )

        return NsObjectUploadResult(object_info=object_info, object_ref=object_ref)

    async def put_stream_with_ref(
            self,
            *,
            stream: BinaryIO,
            length: int,
            module_code: str,
            resource_type: str,
            resource_id: str | int | None = None,
            original_filename: str | None = None,
            object_name: str | None = None,
            bucket: str | None = None,
            content_type: str | None = None,
            uploaded_by: str | int | None = None,
            trace_id: str | None = None,
            extra_metadata: dict[str, str] | None = None,
            sha256: str | None = None,
    ) -> NsObjectUploadResult:
        """Upload stream and build standard object reference.

        If sha256 is not provided, this method calculates it by reading the stream.
        The stream must be seekable so it can be rewound before upload.
        """
        if sha256 is None:
            selected_sha256: str = calculate_sha256_stream(stream)
            try:
                stream.seek(0)
            except Exception as exc:  # noqa
                raise NsObjectStorageConfigurationError("async object storage stream must be seekable when sha256 is not provided") from exc
        else:
            selected_sha256 = str(sha256).strip().lower()

        selected_object_name: str = object_name or build_object_name(
            module_code=module_code,
            resource_type=resource_type,
            resource_id=resource_id,
            original_filename=original_filename,
        )
        metadata: dict[str, str] = build_standard_metadata(
            module_code=module_code,
            resource_type=resource_type,
            resource_id=resource_id,
            original_filename=original_filename,
            uploaded_by=uploaded_by,
            trace_id=trace_id,
            sha256=selected_sha256,
            extra_metadata=extra_metadata,
        )

        object_info = await self.put_stream(
            bucket=bucket,
            object_name=selected_object_name,
            stream=stream,
            length=length,
            content_type=content_type,
            metadata=metadata,
        )
        object_ref = build_object_ref(
            config=self.config,
            object_info=object_info,
            module_code=module_code,
            resource_type=resource_type,
            resource_id=resource_id,
            original_filename=original_filename,
            sha256=selected_sha256,
            extra_metadata=metadata,
        )

        return NsObjectUploadResult(object_info=object_info, object_ref=object_ref)

    async def bucket_exists(self, bucket: str | None = None) -> bool:
        """Return whether bucket exists."""
        return await self._backend.bucket_exists(self._resolve_bucket(bucket))

    async def ensure_bucket(self, bucket: str | None = None) -> None:
        """Ensure bucket exists."""
        await self._backend.ensure_bucket(self._resolve_bucket(bucket))

    async def put_bytes(self, *, object_name: str, data: bytes, bucket: str | None = None, content_type: str | None = None, metadata: dict[str, str] | None = None) -> NsObjectInfo:
        """Upload bytes."""
        return await self._backend.put_bytes(bucket=self._resolve_bucket(bucket), object_name=object_name, data=data, content_type=content_type, metadata=metadata)

    async def put_file(self, *, object_name: str, file_path: str | Path, bucket: str | None = None, content_type: str | None = None, metadata: dict[str, str] | None = None) -> NsObjectInfo:
        """Upload file."""
        return await self._backend.put_file(bucket=self._resolve_bucket(bucket), object_name=object_name, file_path=Path(file_path), content_type=content_type, metadata=metadata)

    async def put_stream(self, *, object_name: str, stream: BinaryIO, length: int, bucket: str | None = None, content_type: str | None = None, metadata: dict[str, str] | None = None) -> NsObjectInfo:
        """Upload stream."""
        return await self._backend.put_stream(bucket=self._resolve_bucket(bucket), object_name=object_name, stream=stream, length=length, content_type=content_type, metadata=metadata)

    async def get_bytes(self, *, object_name: str, bucket: str | None = None) -> bytes:
        """Download object as bytes."""
        return await self._backend.get_bytes(bucket=self._resolve_bucket(bucket), object_name=object_name)

    async def get_file(self, *, object_name: str, file_path: str | Path, bucket: str | None = None) -> None:
        """Download object to file."""
        await self._backend.get_file(bucket=self._resolve_bucket(bucket), object_name=object_name, file_path=Path(file_path))

    async def get_stream(self, *, object_name: str, bucket: str | None = None) -> BinaryIO:
        """Download object as stream."""
        return await self._backend.get_stream(bucket=self._resolve_bucket(bucket), object_name=object_name)

    async def stat_object(self, *, object_name: str, bucket: str | None = None) -> NsObjectInfo:
        """Return object metadata."""
        return await self._backend.stat_object(bucket=self._resolve_bucket(bucket), object_name=object_name)

    async def object_exists(self, *, object_name: str, bucket: str | None = None) -> bool:
        """Return whether object exists."""
        return await self._backend.object_exists(bucket=self._resolve_bucket(bucket), object_name=object_name)

    async def remove_object(self, *, object_name: str, bucket: str | None = None) -> bool:
        """Remove object."""
        return await self._backend.remove_object(bucket=self._resolve_bucket(bucket), object_name=object_name)

    async def list_objects(self, *, prefix: str = "", bucket: str | None = None, recursive: bool = True) -> list[NsObjectInfo]:
        """List objects."""
        return await self._backend.list_objects(bucket=self._resolve_bucket(bucket), prefix=prefix, recursive=recursive)

    async def presigned_get_url(self, *, object_name: str, bucket: str | None = None, expires_seconds: int | None = None) -> str:
        """Build presigned GET URL."""
        return await self._backend.presigned_get_url(bucket=self._resolve_bucket(bucket), object_name=object_name, expires_seconds=self._resolve_expires_seconds(expires_seconds, self.config.presigned_get_expires_seconds))

    async def presigned_put_url(self, *, object_name: str, bucket: str | None = None, expires_seconds: int | None = None, content_type: str | None = None) -> str:
        """Build presigned PUT URL."""
        return await self._backend.presigned_put_url(bucket=self._resolve_bucket(bucket), object_name=object_name, expires_seconds=self._resolve_expires_seconds(expires_seconds, self.config.presigned_put_expires_seconds), content_type=content_type)

    async def close(self) -> None:
        """Close async object storage backend resources and remove singleton reference."""
        with self.__class__._lock:
            existing_client: AsyncNsObjectStorageClient | None = self.__class__._instances.get(self.name)
            if existing_client is self:
                self.__class__._instances.pop(self.name, None)

        await self._backend.close()

    def _resolve_bucket(self, bucket: str | None = None) -> str:
        """Resolve target bucket."""
        selected_bucket = str(bucket or self.config.default_bucket or "").strip()
        if not selected_bucket:
            raise NsObjectStorageConfigurationError("async object storage bucket is required")
        return selected_bucket

    @staticmethod
    def _resolve_expires_seconds(value: int | None, default: int) -> int:
        """Resolve presigned URL expiration seconds."""
        selected_value = default if value is None else value

        if isinstance(selected_value, bool) or not isinstance(selected_value, int):
            raise NsObjectStorageConfigurationError("async object storage presigned expires_seconds must be int")

        if selected_value <= 0:
            raise NsObjectStorageConfigurationError("async object storage presigned expires_seconds must be positive")

        return selected_value

    @staticmethod
    def _normalize_client_name(name: str) -> str:
        """Normalize singleton client name."""
        if not isinstance(name, str) or not name.strip():
            raise NsObjectStorageConfigurationError("async object storage client name must be a non-empty str")
        return name.strip()

    @staticmethod
    def _load_config_from_ns_config() -> NsObjectStorageConfig:
        """Load default object storage config from ns_config."""
        from ns_common.config import ns_config

        return ns_config.object_storage_config

    @staticmethod
    def _build_backend(config: NsObjectStorageConfig) -> AsyncMinioObjectStorageBackend | AsyncLocalFileObjectStorageBackend:
        """Build async object storage backend by explicit configuration."""
        resolved_backend = config.resolved_backend()

        if resolved_backend == "minio":
            return AsyncMinioObjectStorageBackend(config)

        if resolved_backend == "local_fs":
            return AsyncLocalFileObjectStorageBackend(config)

        raise NsObjectStorageConfigurationError(f"unsupported or unimplemented async object storage backend: {config.backend}")
