# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

from ns_common import DATA_DIR
from ns_common.config import NsObjectStorageConfig
from ns_common.storage.backends.base import BaseObjectStorageBackend
from ns_common.storage.errors import NsObjectStorageConfigurationError, NsObjectStorageNotFoundError
from ns_common.storage.models import NsObjectInfo


class LocalFileObjectStorageBackend(BaseObjectStorageBackend):
    """Local filesystem object storage backend for dev/test usage only."""

    _META_DIR_NAME = ".nsmeta"

    def __init__(self, config: NsObjectStorageConfig) -> None:
        """Initialize local filesystem backend."""
        super().__init__(config)
        self._root_path: Path = self._resolve_root_path(config.local_root_path)
        self._root_path.mkdir(parents=True, exist_ok=True)

    def bucket_exists(self, bucket: str) -> bool:
        """Return whether bucket directory exists."""
        bucket_name: str = self._normalize_bucket(bucket)
        return self._bucket_path(bucket_name).is_dir()

    def ensure_bucket(self, bucket: str) -> None:
        """Ensure bucket directory exists."""
        bucket_name: str = self._normalize_bucket(bucket)
        self._bucket_path(bucket_name).mkdir(parents=True, exist_ok=True)
        self._meta_bucket_path(bucket_name).mkdir(parents=True, exist_ok=True)

    def put_bytes(self, *, bucket: str, object_name: str, data: bytes, content_type: str | None = None, metadata: dict[str, str] | None = None) -> NsObjectInfo:
        """Upload bytes to local filesystem."""
        if not isinstance(data, bytes):
            raise NsObjectStorageConfigurationError("put_bytes data must be bytes")

        self._validate_payload_size(len(data))

        bucket_name: str = self._normalize_bucket(bucket)
        storage_object_name: str = self._normalize_object_name(object_name)
        normalized_metadata: dict[str, str] = self._normalize_metadata(metadata)

        self.ensure_bucket(bucket_name)

        object_path: Path = self._object_path(bucket_name, storage_object_name)
        object_path.parent.mkdir(parents=True, exist_ok=True)
        self._atomic_write_bytes(object_path, data)

        etag: str = hashlib.md5(data).hexdigest()  # noqa: S324
        selected_content_type: str | None = content_type or self._guess_content_type(storage_object_name)
        self._write_metadata(bucket=bucket_name, object_name=storage_object_name, content_type=selected_content_type, metadata=normalized_metadata, etag=etag)

        return self.stat_object(bucket=bucket_name, object_name=storage_object_name)

    def put_file(self, *, bucket: str, object_name: str, file_path: Path, content_type: str | None = None, metadata: dict[str, str] | None = None) -> NsObjectInfo:
        """Upload file to local filesystem."""
        source_path: Path = Path(file_path)
        if not source_path.is_file():
            raise NsObjectStorageNotFoundError(f"object storage upload file does not exist: {source_path}")

        file_size: int = source_path.stat().st_size
        self._validate_payload_size(file_size)

        bucket_name: str = self._normalize_bucket(bucket)
        storage_object_name: str = self._normalize_object_name(object_name)
        normalized_metadata: dict[str, str] = self._normalize_metadata(metadata)

        self.ensure_bucket(bucket_name)

        object_path: Path = self._object_path(bucket_name, storage_object_name)
        object_path.parent.mkdir(parents=True, exist_ok=True)

        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(mode="wb", delete=False, dir=str(object_path.parent), prefix=".upload_", suffix=".tmp") as temp_file:
                temp_path = Path(temp_file.name)
                with source_path.open("rb") as source_file:
                    # noinspection PyTypeChecker
                    shutil.copyfileobj(source_file, temp_file)
                temp_file.flush()
                os.fsync(temp_file.fileno())

            os.replace(temp_path, object_path)
        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()

        etag: str = self._file_md5(object_path)
        selected_content_type: str | None = content_type or self._guess_content_type(storage_object_name)
        self._write_metadata(bucket=bucket_name, object_name=storage_object_name, content_type=selected_content_type, metadata=normalized_metadata, etag=etag)

        return self.stat_object(bucket=bucket_name, object_name=storage_object_name)

    def put_stream(self, *, bucket: str, object_name: str, stream: BinaryIO, length: int, content_type: str | None = None, metadata: dict[str, str] | None = None) -> NsObjectInfo:
        """Upload stream to local filesystem."""
        self._validate_payload_size(length)

        bucket_name: str = self._normalize_bucket(bucket)
        storage_object_name: str = self._normalize_object_name(object_name)
        normalized_metadata: dict[str, str] = self._normalize_metadata(metadata)

        self.ensure_bucket(bucket_name)

        object_path: Path = self._object_path(bucket_name, storage_object_name)
        object_path.parent.mkdir(parents=True, exist_ok=True)

        remaining_size: int = length
        temp_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(mode="wb", delete=False, dir=str(object_path.parent), prefix=".upload_", suffix=".tmp") as temp_file:
                temp_path = Path(temp_file.name)
                while remaining_size > 0:
                    chunk: bytes = stream.read(min(1024 * 1024, remaining_size))
                    if not chunk:
                        break
                    temp_file.write(chunk)
                    remaining_size -= len(chunk)

                temp_file.flush()
                os.fsync(temp_file.fileno())

            actual_size: int = temp_path.stat().st_size
            if actual_size != length:
                raise NsObjectStorageConfigurationError("object storage stream length does not match actual bytes read")

            os.replace(temp_path, object_path)
        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()

        etag: str = self._file_md5(object_path)
        selected_content_type: str | None = content_type or self._guess_content_type(storage_object_name)
        self._write_metadata(bucket=bucket_name, object_name=storage_object_name, content_type=selected_content_type, metadata=normalized_metadata, etag=etag)

        return self.stat_object(bucket=bucket_name, object_name=storage_object_name)

    def get_bytes(self, *, bucket: str, object_name: str) -> bytes:
        """Download local object as bytes."""
        object_path: Path = self._existing_object_path(bucket, object_name)
        return object_path.read_bytes()

    def get_file(self, *, bucket: str, object_name: str, file_path: Path) -> None:
        """Download local object to target file."""
        object_path: Path = self._existing_object_path(bucket, object_name)
        target_path: Path = Path(file_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(object_path, target_path)

    def get_stream(self, *, bucket: str, object_name: str) -> BinaryIO:
        """Download local object as readable binary stream."""
        object_path: Path = self._existing_object_path(bucket, object_name)
        return object_path.open("rb")

    def stat_object(self, *, bucket: str, object_name: str) -> NsObjectInfo:
        """Return local object metadata."""
        bucket_name: str = self._normalize_bucket(bucket)
        storage_object_name: str = self._normalize_object_name(object_name)
        object_path: Path = self._object_path(bucket_name, storage_object_name)

        if not object_path.is_file():
            raise NsObjectStorageNotFoundError(f"object storage object does not exist: {storage_object_name}")

        stat_result = object_path.stat()
        metadata_payload: dict[str, object] = self._read_metadata(bucket=bucket_name, object_name=storage_object_name)
        content_type_value: object = metadata_payload.get("content_type")
        etag_value: object = metadata_payload.get("etag")
        metadata_value: object = metadata_payload.get("metadata")

        return NsObjectInfo(
            bucket=bucket_name,
            object_name=storage_object_name,
            size=stat_result.st_size,
            etag=str(etag_value) if etag_value else self._file_md5(object_path),
            content_type=str(content_type_value) if content_type_value else self._guess_content_type(storage_object_name),
            last_modified=datetime.fromtimestamp(stat_result.st_mtime),
            metadata=dict(metadata_value) if isinstance(metadata_value, dict) else {},
            version_id=None,
        )

    def object_exists(self, *, bucket: str, object_name: str) -> bool:
        """Return whether local object exists."""
        try:
            self.stat_object(bucket=bucket, object_name=object_name)
            return True
        except NsObjectStorageNotFoundError:
            return False

    def remove_object(self, *, bucket: str, object_name: str) -> bool:
        """Remove local object and metadata."""
        bucket_name: str = self._normalize_bucket(bucket)
        storage_object_name: str = self._normalize_object_name(object_name)
        object_path: Path = self._object_path(bucket_name, storage_object_name)
        metadata_path: Path = self._metadata_path(bucket_name, storage_object_name)

        removed: bool = False
        if object_path.exists():
            object_path.unlink()
            removed = True

        if metadata_path.exists():
            metadata_path.unlink()

        return removed

    def list_objects(self, *, bucket: str, prefix: str = "", recursive: bool = True) -> list[NsObjectInfo]:
        """List local objects."""
        bucket_name: str = self._normalize_bucket(bucket)
        bucket_path: Path = self._bucket_path(bucket_name)

        if not bucket_path.is_dir():
            raise NsObjectStorageNotFoundError(f"object storage bucket does not exist: {bucket_name}")

        storage_prefix: str = self._normalize_prefix(prefix)
        pattern: str = "**/*" if recursive else "*"
        result: list[NsObjectInfo] = []

        for candidate_path in bucket_path.glob(pattern):
            if not candidate_path.is_file():
                continue

            relative_path: str = candidate_path.relative_to(bucket_path).as_posix()
            if relative_path.startswith(f"{self._META_DIR_NAME}/"):
                continue

            if storage_prefix and not relative_path.startswith(storage_prefix):
                continue

            result.append(self.stat_object(bucket=bucket_name, object_name=relative_path))

        return result

    @staticmethod
    def presigned_get_url(*, bucket: str, object_name: str, expires_seconds: int) -> str:
        """Local filesystem backend does not support real presigned GET URLs."""
        _ = (bucket, object_name, expires_seconds)
        raise NsObjectStorageConfigurationError("local_fs object storage backend does not support presigned GET URL")

    @staticmethod
    def presigned_put_url(*, bucket: str, object_name: str, expires_seconds: int, content_type: str | None = None) -> str:
        """Local filesystem backend does not support real presigned PUT URLs."""
        _ = (bucket, object_name, expires_seconds, content_type)
        raise NsObjectStorageConfigurationError("local_fs object storage backend does not support presigned PUT URL")

    @staticmethod
    def close() -> None:
        """Close backend resources."""
        return None

    @staticmethod
    def _resolve_root_path(value: str) -> Path:
        """Resolve local filesystem root path."""
        raw_path: str = str(value or "").strip()
        if not raw_path:
            return DATA_DIR / "object_storage"

        root_path: Path = Path(raw_path)
        if root_path.is_absolute():
            return root_path

        return DATA_DIR / root_path

    def _bucket_path(self, bucket: str) -> Path:
        """Return bucket directory path."""
        return self._root_path / bucket

    def _meta_bucket_path(self, bucket: str) -> Path:
        """Return bucket metadata directory path."""
        return self._bucket_path(bucket) / self._META_DIR_NAME

    def _object_path(self, bucket: str, object_name: str) -> Path:
        """Return safe local object path."""
        bucket_path: Path = self._bucket_path(bucket).resolve()
        object_path: Path = (bucket_path / object_name).resolve()

        if not self._is_relative_to(object_path, bucket_path):
            raise NsObjectStorageConfigurationError("object storage object path escapes bucket directory")

        return object_path

    def _metadata_path(self, bucket: str, object_name: str) -> Path:
        """Return safe metadata sidecar path."""
        meta_bucket_path: Path = self._meta_bucket_path(bucket).resolve()
        metadata_path: Path = (meta_bucket_path / f"{object_name}.json").resolve()

        if not self._is_relative_to(metadata_path, meta_bucket_path):
            raise NsObjectStorageConfigurationError("object storage metadata path escapes bucket metadata directory")

        return metadata_path

    def _existing_object_path(self, bucket: str, object_name: str) -> Path:
        """Return existing local object path."""
        bucket_name: str = self._normalize_bucket(bucket)
        storage_object_name: str = self._normalize_object_name(object_name)
        object_path: Path = self._object_path(bucket_name, storage_object_name)

        if not object_path.is_file():
            raise NsObjectStorageNotFoundError(f"object storage object does not exist: {storage_object_name}")

        return object_path

    def _write_metadata(self, *, bucket: str, object_name: str, content_type: str | None, metadata: dict[str, str], etag: str) -> None:
        """Write metadata sidecar file."""
        metadata_path: Path = self._metadata_path(bucket, object_name)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)

        payload: dict[str, object] = {
            "content_type": content_type,
            "metadata": metadata,
            "etag": etag,
            "version_id": None,
        }

        self._atomic_write_bytes(metadata_path, json.dumps(payload, ensure_ascii=False, indent=4).encode("utf-8"))

    def _read_metadata(self, *, bucket: str, object_name: str) -> dict[str, object]:
        """Read metadata sidecar file."""
        metadata_path: Path = self._metadata_path(bucket, object_name)
        if not metadata_path.is_file():
            return {}

        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def _atomic_write_bytes(path: Path, data: bytes) -> None:
        """Atomically write bytes to target path."""
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(mode="wb", delete=False, dir=str(path.parent), prefix=".write_", suffix=".tmp") as temp_file:
                temp_path = Path(temp_file.name)
                temp_file.write(data)
                temp_file.flush()
                os.fsync(temp_file.fileno())

            os.replace(temp_path, path)
        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()

    @staticmethod
    def _file_md5(path: Path) -> str:
        """Build MD5 hex digest for local dev/test object etag."""
        digest = hashlib.md5()  # noqa: S324
        with path.open("rb") as file:
            while True:
                chunk: bytes = file.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _guess_content_type(object_name: str) -> str | None:
        """Guess content type by object name."""
        content_type, _ = mimetypes.guess_type(object_name)
        return content_type

    @staticmethod
    def _is_relative_to(path: Path, parent: Path) -> bool:
        """Return whether path is inside parent directory."""
        try:
            path.relative_to(parent)
        except ValueError:
            return False
        return True
