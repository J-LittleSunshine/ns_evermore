# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import timedelta
from io import BytesIO
from pathlib import Path
from typing import Any, BinaryIO, TYPE_CHECKING

from ns_common.config import NsObjectStorageConfig
from ns_common.storage.backends.base import BaseObjectStorageBackend
from ns_common.storage.errors import (
    NsObjectStorageConfigurationError,
    NsObjectStorageConnectionError,
    NsObjectStorageConflictError,
    NsObjectStorageNotFoundError,
    NsObjectStoragePermissionError,
)
from ns_common.storage.models import NsObjectInfo

if TYPE_CHECKING:
    pass


class MinioObjectStorageBackend(BaseObjectStorageBackend):
    """MinIO object storage backend."""

    def __init__(self, config: NsObjectStorageConfig) -> None:
        """Initialize MinIO backend."""
        super().__init__(config)
        self._client: Any = self._build_client()

    def bucket_exists(self, bucket: str) -> bool:
        """Return whether bucket exists."""
        bucket_name = self._normalize_bucket(bucket)

        try:
            return bool(self._client.bucket_exists(bucket_name))
        except Exception as _error:  # noqa
            raise self._to_backend_error(_error) from _error

    def ensure_bucket(self, bucket: str) -> None:
        """Ensure bucket exists."""
        bucket_name = self._normalize_bucket(bucket)

        try:
            if self._client.bucket_exists(bucket_name):
                return

            if self._config.region:
                self._client.make_bucket(bucket_name, location=self._config.region)
                return

            self._client.make_bucket(bucket_name)
        except Exception as _error:  # noqa
            raise self._to_backend_error(_error) from _error

    def put_bytes(self, *, bucket: str, object_name: str, data: bytes, content_type: str | None = None, metadata: dict[str, str] | None = None) -> NsObjectInfo:
        """Upload bytes."""
        if not isinstance(data, bytes):
            raise NsObjectStorageConfigurationError("put_bytes data must be bytes")

        self._validate_payload_size(len(data))

        bucket_name = self._normalize_bucket(bucket)
        storage_object_name = self._normalize_object_name(object_name)
        normalized_metadata = self._normalize_metadata(metadata)

        if self._config.auto_create_bucket:
            self.ensure_bucket(bucket_name)

        try:
            result = self._client.put_object(
                bucket_name=bucket_name,
                object_name=storage_object_name,
                data=BytesIO(data),
                length=len(data),
                content_type=content_type,
                metadata=normalized_metadata or None,
            )
        except Exception as _error:  # noqa
            raise self._to_backend_error(_error) from _error

        return NsObjectInfo(
            bucket=bucket_name,
            object_name=storage_object_name,
            size=len(data),
            etag=getattr(result, "etag", None),
            content_type=content_type,
            metadata=normalized_metadata,
            version_id=getattr(result, "version_id", None),
        )

    def put_file(self, *, bucket: str, object_name: str, file_path: Path, content_type: str | None = None, metadata: dict[str, str] | None = None) -> NsObjectInfo:
        """Upload file."""
        source_path = Path(file_path)
        if not source_path.is_file():
            raise NsObjectStorageNotFoundError(f"object storage upload file does not exist: {source_path}")

        file_size = source_path.stat().st_size
        self._validate_payload_size(file_size)

        bucket_name = self._normalize_bucket(bucket)
        storage_object_name = self._normalize_object_name(object_name)
        normalized_metadata = self._normalize_metadata(metadata)

        if self._config.auto_create_bucket:
            self.ensure_bucket(bucket_name)

        try:
            result = self._client.fput_object(
                bucket_name=bucket_name,
                object_name=storage_object_name,
                file_path=str(source_path),
                content_type=content_type,
                metadata=normalized_metadata or None,
            )
        except Exception as _error:  # noqa
            raise self._to_backend_error(_error) from _error

        return NsObjectInfo(
            bucket=bucket_name,
            object_name=storage_object_name,
            size=file_size,
            etag=getattr(result, "etag", None),
            content_type=content_type,
            metadata=normalized_metadata,
            version_id=getattr(result, "version_id", None),
        )

    def put_stream(self, *, bucket: str, object_name: str, stream: BinaryIO, length: int, content_type: str | None = None, metadata: dict[str, str] | None = None) -> NsObjectInfo:
        """Upload stream."""
        self._validate_payload_size(length)

        bucket_name = self._normalize_bucket(bucket)
        storage_object_name = self._normalize_object_name(object_name)
        normalized_metadata = self._normalize_metadata(metadata)

        if self._config.auto_create_bucket:
            self.ensure_bucket(bucket_name)

        try:
            result = self._client.put_object(
                bucket_name=bucket_name,
                object_name=storage_object_name,
                data=stream,
                length=length,
                content_type=content_type,
                metadata=normalized_metadata or None,
            )
        except Exception as _error:  # noqa
            raise self._to_backend_error(_error) from _error

        return NsObjectInfo(
            bucket=bucket_name,
            object_name=storage_object_name,
            size=length,
            etag=getattr(result, "etag", None),
            content_type=content_type,
            metadata=normalized_metadata,
            version_id=getattr(result, "version_id", None),
        )

    def get_bytes(self, *, bucket: str, object_name: str) -> bytes:
        """Download object as bytes."""
        bucket_name = self._normalize_bucket(bucket)
        storage_object_name = self._normalize_object_name(object_name)

        response = None
        try:
            response = self._client.get_object(bucket_name, storage_object_name)
            return response.read()
        except Exception as _error:  # noqa
            raise self._to_backend_error(_error) from _error
        finally:
            if response is not None:
                try:
                    response.close()
                    response.release_conn()
                except Exception:  # noqa
                    pass

    def get_file(self, *, bucket: str, object_name: str, file_path: Path) -> None:
        """Download object to file."""
        bucket_name = self._normalize_bucket(bucket)
        storage_object_name = self._normalize_object_name(object_name)
        target_path = Path(file_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            self._client.fget_object(bucket_name, storage_object_name, str(target_path))
        except Exception as _error:  # noqa
            raise self._to_backend_error(_error) from _error

    def get_stream(self, *, bucket: str, object_name: str) -> BinaryIO:
        """Download object as stream.

        Caller is responsible for closing the returned stream when backend exposes close().
        """
        bucket_name = self._normalize_bucket(bucket)
        storage_object_name = self._normalize_object_name(object_name)

        try:
            return self._client.get_object(bucket_name, storage_object_name)
        except Exception as _error:  # noqa
            raise self._to_backend_error(_error) from _error

    def stat_object(self, *, bucket: str, object_name: str) -> NsObjectInfo:
        """Return object metadata."""
        bucket_name = self._normalize_bucket(bucket)
        storage_object_name = self._normalize_object_name(object_name)

        try:
            stat = self._client.stat_object(bucket_name, storage_object_name)
        except Exception as _error:  # noqa
            raise self._to_backend_error(_error) from _error

        return self._to_object_info(bucket=bucket_name, object_name=storage_object_name, raw_object=stat)

    def object_exists(self, *, bucket: str, object_name: str) -> bool:
        """Return whether object exists."""
        try:
            self.stat_object(bucket=bucket, object_name=object_name)
            return True
        except NsObjectStorageNotFoundError:
            return False

    def remove_object(self, *, bucket: str, object_name: str) -> bool:
        """Remove object."""
        bucket_name = self._normalize_bucket(bucket)
        storage_object_name = self._normalize_object_name(object_name)

        try:
            self._client.remove_object(bucket_name, storage_object_name)
            return True
        except Exception as _error:  # noqa
            raise self._to_backend_error(_error) from _error

    def list_objects(self, *, bucket: str, prefix: str = "", recursive: bool = True) -> list[NsObjectInfo]:
        """List objects."""
        bucket_name = self._normalize_bucket(bucket)
        storage_prefix = self._normalize_object_name(prefix) if prefix else self._normalize_object_name(".")

        if storage_prefix == f"{self._key_prefix}/.":
            storage_prefix = f"{self._key_prefix}/"
        elif storage_prefix == ".":
            storage_prefix = ""

        try:
            raw_objects = self._client.list_objects(bucket_name, prefix=storage_prefix, recursive=recursive)
            return [
                self._to_object_info(bucket=bucket_name, object_name=str(getattr(raw_object, "object_name", "")), raw_object=raw_object)
                for raw_object in raw_objects
            ]
        except Exception as _error:  # noqa
            raise self._to_backend_error(_error) from _error

    def presigned_get_url(self, *, bucket: str, object_name: str, expires_seconds: int) -> str:
        """Build presigned GET URL."""
        bucket_name = self._normalize_bucket(bucket)
        storage_object_name = self._normalize_object_name(object_name)

        try:
            return str(
                self._client.presigned_get_object(
                    bucket_name=bucket_name,
                    object_name=storage_object_name,
                    expires=timedelta(seconds=expires_seconds),
                )
            )
        except Exception as _error:  # noqa
            raise self._to_backend_error(_error) from _error

    def presigned_put_url(self, *, bucket: str, object_name: str, expires_seconds: int, content_type: str | None = None) -> str:
        """Build presigned PUT URL.

        content_type is accepted for stable public API; MinIO SDK does not require it here.
        """
        _ = content_type

        bucket_name = self._normalize_bucket(bucket)
        storage_object_name = self._normalize_object_name(object_name)

        try:
            return str(
                self._client.presigned_put_object(
                    bucket_name=bucket_name,
                    object_name=storage_object_name,
                    expires=timedelta(seconds=expires_seconds),
                )
            )
        except Exception as _error:  # noqa
            raise self._to_backend_error(_error) from _error

    @staticmethod
    def close() -> None:
        """Close backend resources."""
        # MinIO client does not expose a mandatory close API. Keep this method for backend protocol compatibility.
        return None

    def _build_client(self) -> Any:
        """Build MinIO SDK client."""
        if not self._config.endpoint:
            raise NsObjectStorageConfigurationError("minio object storage endpoint is required")

        if not self._config.access_key:
            raise NsObjectStorageConfigurationError("minio object storage access_key is required")

        if not self._config.secret_key:
            raise NsObjectStorageConfigurationError("minio object storage secret_key is required")

        try:
            from minio import Minio
        except ImportError as _error:
            raise NsObjectStorageConfigurationError("minio client is not installed") from _error

        try:
            return Minio(
                endpoint=self._config.endpoint,
                access_key=self._config.access_key,
                secret_key=self._config.secret_key,
                secure=bool(self._config.secure),
                region=self._config.region,
            )
        except Exception as _error:  # noqa
            raise NsObjectStorageConfigurationError("invalid minio object storage configuration") from _error

    @staticmethod
    def _to_object_info(*, bucket: str, object_name: str, raw_object: Any) -> NsObjectInfo:
        """Convert MinIO SDK object metadata to framework object info."""
        raw_metadata = getattr(raw_object, "metadata", None)
        metadata: dict[str, str] = {}

        if isinstance(raw_metadata, dict):
            metadata = {
                str(key): str(value)
                for key, value in raw_metadata.items()
                if key is not None and value is not None
            }

        return NsObjectInfo(
            bucket=bucket,
            object_name=object_name,
            size=getattr(raw_object, "size", None),
            etag=getattr(raw_object, "etag", None),
            content_type=getattr(raw_object, "content_type", None),
            last_modified=getattr(raw_object, "last_modified", None),
            metadata=metadata,
            version_id=getattr(raw_object, "version_id", None),
        )

    @staticmethod
    def _to_backend_error(_error: BaseException) -> Exception:
        """Translate MinIO SDK errors to framework object storage exceptions."""
        error_code = str(getattr(_error, "code", "") or "")
        error_message = str(getattr(_error, "message", "") or str(_error) or "minio object storage operation failed")

        if error_code in {"NoSuchBucket", "NoSuchKey", "NoSuchObject", "NoSuchUpload"}:
            return NsObjectStorageNotFoundError(error_message)

        if error_code in {"AccessDenied", "InvalidAccessKeyId", "SignatureDoesNotMatch", "AllAccessDisabled"}:
            return NsObjectStoragePermissionError(error_message)

        if error_code in {"BucketAlreadyExists", "BucketAlreadyOwnedByYou", "ObjectAlreadyInActiveTierError"}:
            return NsObjectStorageConflictError(error_message)

        if isinstance(_error, (OSError, ConnectionError, TimeoutError)):
            return NsObjectStorageConnectionError("minio object storage backend operation failed")

        return NsObjectStorageConnectionError(error_message)
