# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any

from asgiref.sync import sync_to_async

from ns_backend.backend.exceptions import BusinessError
from ns_common.error_codes import NsErrorCode
from ns_common.storage import (
    AsyncNsObjectStorageClient,
    NsObjectInfo,
    NsObjectRef,
    NsObjectUploadContext,
    NsObjectUploadResult,
    NsStorageResource,
    get_async_object_ref_repository,
)
from ns_common.storage.errors import (
    NsObjectStorageConfigurationError,
    NsObjectStorageError,
    NsObjectStorageNotFoundError,
    NsObjectStorageValidationError,
)

if TYPE_CHECKING:
    pass


class StorageObjectService:
    """Application service for generic storage object APIs.

    This service intentionally handles only technical storage object metadata.
    It must not contain business attachment semantics.
    """

    DEFAULT_PAGE = 1
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100

    @classmethod
    async def upload_object(cls, *, request, operator: Any | None = None) -> dict[str, Any]:
        """Upload one object and persist its object reference."""
        request_data = cls._get_request_data(request)
        uploaded_file = cls._get_uploaded_file(request)

        module_code = cls._get_required_text(request_data, "module_code")
        resource_type = cls._get_required_text(request_data, "resource_type")
        resource_id = cls._get_optional_text(request_data, "resource_id")
        bucket = cls._get_optional_text(request_data, "bucket")
        object_name = cls._get_optional_text(request_data, "object_name")
        original_filename = cls._get_optional_text(request_data, "original_filename") or cls._get_uploaded_filename(uploaded_file)
        content_type = cls._get_optional_text(request_data, "content_type") or cls._get_uploaded_content_type(uploaded_file)
        extra_metadata = cls._parse_metadata(request_data.get("metadata"))
        trace_id = cls._resolve_trace_id(request)

        temp_path: Path | None = None

        try:
            temp_path = await sync_to_async(cls._write_uploaded_file_to_temp, thread_sensitive=True)(uploaded_file)

            context = NsObjectUploadContext.from_resource(
                resource=NsStorageResource(
                    module_code=module_code,
                    resource_type=resource_type,
                    resource_id=resource_id,
                ),
                original_filename=original_filename,
                object_name=object_name,
                bucket=bucket,
                content_type=content_type,
                uploaded_by=getattr(operator, "id", None),
                trace_id=trace_id,
                extra_metadata=extra_metadata,
            )

            storage_client = AsyncNsObjectStorageClient.get_default()
            upload_result = await storage_client.put_file_with_context(
                file_path=temp_path,
                context=context,
            )

            repository = get_async_object_ref_repository()

            try:
                saved_ref = await repository.save_object_ref(upload_result.object_ref)
            except Exception:
                await cls._cleanup_uploaded_object(upload_result=upload_result)
                raise

            return cls._serialize_upload_result(
                NsObjectUploadResult(
                    object_info=upload_result.object_info,
                    object_ref=saved_ref,
                )
            )
        except NsObjectStorageValidationError as exc:
            raise BusinessError(str(exc), NsErrorCode.INVALID_VALUE) from exc
        except NsObjectStorageNotFoundError as exc:
            raise BusinessError(str(exc), NsErrorCode.DATA_NOT_FOUND) from exc
        except NsObjectStorageConfigurationError as exc:
            raise BusinessError(str(exc), NsErrorCode.INVALID_VALUE) from exc
        except NsObjectStorageError as exc:
            raise BusinessError(str(exc), NsErrorCode.DATA_CREATION_FAILED) from exc
        finally:
            if temp_path is not None and temp_path.exists():
                await sync_to_async(temp_path.unlink, thread_sensitive=True)()

    @classmethod
    async def list_object_refs(cls, *, data: dict[str, Any]) -> dict[str, Any]:
        """List object references by module/resource identity."""
        request_data = cls._ensure_request_data(data)

        module_code = cls._get_required_text(request_data, "module_code")
        resource_type = cls._get_required_text(request_data, "resource_type")
        resource_id = cls._get_optional_text(request_data, "resource_id")

        page = cls._normalize_page(request_data.get("page"))
        page_size = cls._normalize_page_size(request_data.get("page_size"))

        repository = get_async_object_ref_repository()
        refs = await repository.list_object_refs(
            module_code=module_code,
            resource_type=resource_type,
            resource_id=resource_id,
        )

        total = len(refs)
        start = (page - 1) * page_size
        end = start + page_size
        items = refs[start:end]

        return {
            "items": [cls._serialize_object_ref(item) for item in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    @classmethod
    async def detail_object_ref(cls, *, data: dict[str, Any]) -> dict[str, Any]:
        """Get one object reference detail by bucket/object_name."""
        request_data = cls._ensure_request_data(data)

        bucket = cls._get_required_text(request_data, "bucket")
        object_name = cls._get_required_text(request_data, "object_name")

        repository = get_async_object_ref_repository()
        object_ref = await repository.get_object_ref(bucket=bucket, object_name=object_name)
        if object_ref is None:
            raise BusinessError("object reference not found", NsErrorCode.DATA_NOT_FOUND)

        return cls._serialize_object_ref(object_ref)

    @classmethod
    async def delete_object_ref(cls, *, data: dict[str, Any]) -> dict[str, Any]:
        """Soft delete one object reference.

        This method does not remove the physical object from object storage.
        """
        request_data = cls._ensure_request_data(data)

        bucket = cls._get_required_text(request_data, "bucket")
        object_name = cls._get_required_text(request_data, "object_name")

        repository = get_async_object_ref_repository()
        deleted = await repository.delete_object_ref(bucket=bucket, object_name=object_name)

        if not deleted:
            raise BusinessError("object reference not found", NsErrorCode.DATA_NOT_FOUND)

        return {
            "deleted": True,
            "bucket": bucket,
            "object_name": object_name,
        }

    @classmethod
    async def presigned_get_url(cls, *, data: dict[str, Any]) -> dict[str, Any]:
        """Create presigned GET URL for one registered object reference."""
        request_data = cls._ensure_request_data(data)

        bucket = cls._get_required_text(request_data, "bucket")
        object_name = cls._get_required_text(request_data, "object_name")
        expires_seconds = cls._normalize_expires_seconds(request_data.get("expires_seconds"))

        repository = get_async_object_ref_repository()
        object_ref = await repository.get_object_ref(bucket=bucket, object_name=object_name)
        if object_ref is None:
            raise BusinessError("object reference not found", NsErrorCode.DATA_NOT_FOUND)

        try:
            storage_client = AsyncNsObjectStorageClient.get_default()
            url = await storage_client.presigned_get_url(
                bucket=object_ref.bucket,
                object_name=object_ref.object_name,
                expires_seconds=expires_seconds,
            )
        except NsObjectStorageValidationError as exc:
            raise BusinessError(str(exc), NsErrorCode.INVALID_VALUE) from exc
        except NsObjectStorageNotFoundError as exc:
            raise BusinessError(str(exc), NsErrorCode.DATA_NOT_FOUND) from exc
        except NsObjectStorageConfigurationError as exc:
            raise BusinessError(str(exc), NsErrorCode.INVALID_VALUE) from exc
        except NsObjectStorageError as exc:
            raise BusinessError(str(exc), NsErrorCode.DATA_CREATION_FAILED) from exc

        return {
            "bucket": object_ref.bucket,
            "object_name": object_ref.object_name,
            "url": url,
            "expires_seconds": expires_seconds,
            "object_ref": cls._serialize_object_ref(object_ref),
        }

    @classmethod
    def _get_request_data(cls, request) -> dict[str, Any]:
        """Return request data as dict."""
        try:
            data = request.data
        except Exception as exc:  # noqa
            raise BusinessError("request data is invalid", NsErrorCode.INVALID_VALUE) from exc

        return cls._ensure_request_data(data)

    @staticmethod
    def _ensure_request_data(data: Any) -> dict[str, Any]:
        """Validate and normalize request data as dict."""
        if isinstance(data, dict):
            return data

        if isinstance(data, Mapping):
            return {
                str(key): value
                for key, value in data.items()
            }

        dict_method = getattr(data, "dict", None)
        if callable(dict_method):
            payload = dict_method()
            if isinstance(payload, dict):
                return payload

        raise BusinessError("request data must be an object", NsErrorCode.INVALID_VALUE)

    @staticmethod
    def _get_uploaded_file(request):
        """Return uploaded file object from request."""
        uploaded_file = None

        files = getattr(request, "FILES", None)
        if files is not None:
            uploaded_file = files.get("file")

        if uploaded_file is None:
            try:
                uploaded_file = request.data.get("file")
            except Exception:  # noqa
                uploaded_file = None

        if uploaded_file is None:
            raise BusinessError("file is required", NsErrorCode.INVALID_VALUE)

        if not callable(getattr(uploaded_file, "chunks", None)) and not callable(getattr(uploaded_file, "read", None)):
            raise BusinessError("file is invalid", NsErrorCode.INVALID_VALUE)

        return uploaded_file

    @staticmethod
    def _get_uploaded_filename(uploaded_file) -> str | None:
        """Return uploaded original filename."""
        filename = getattr(uploaded_file, "name", None)
        if filename is None:
            return None

        text = str(filename).strip()
        return text or None

    @staticmethod
    def _get_uploaded_content_type(uploaded_file) -> str | None:
        """Return uploaded content type."""
        content_type = getattr(uploaded_file, "content_type", None)
        if content_type is None:
            return None

        text = str(content_type).strip()
        return text or None

    @staticmethod
    def _write_uploaded_file_to_temp(uploaded_file) -> Path:
        """Write uploaded file to one temporary local file and return its path."""
        filename = StorageObjectService._get_uploaded_filename(uploaded_file)
        suffix = Path(filename).suffix if filename else ""

        temp_file = tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=suffix)
        temp_path = Path(temp_file.name)

        try:
            with temp_file:
                if callable(getattr(uploaded_file, "chunks", None)):
                    for chunk in uploaded_file.chunks():
                        if not chunk:
                            continue
                        temp_file.write(chunk)
                else:
                    payload = uploaded_file.read()
                    if isinstance(payload, str):
                        payload = payload.encode("utf-8")
                    temp_file.write(payload)

                temp_file.flush()

            return temp_path
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

    @staticmethod
    def _get_required_text(data: dict[str, Any], field_name: str) -> str:
        """Return required non-empty text field."""
        value = data.get(field_name)
        text = str(value or "").strip()
        if not text:
            raise BusinessError(f"{field_name} is required", NsErrorCode.INVALID_VALUE)
        return text

    @staticmethod
    def _get_optional_text(data: dict[str, Any], field_name: str) -> str | None:
        """Return optional text field."""
        value = data.get(field_name)
        if value in (None, ""):
            return None

        text = str(value).strip()
        return text or None

    @staticmethod
    def _parse_metadata(value: Any) -> dict[str, str]:
        """Parse optional metadata object."""
        if value in (None, ""):
            return {}

        raw_metadata: Any = value
        if isinstance(value, str):
            try:
                raw_metadata = json.loads(value)
            except json.JSONDecodeError as exc:
                raise BusinessError("metadata must be a JSON object", NsErrorCode.INVALID_VALUE) from exc

        if not isinstance(raw_metadata, dict):
            raise BusinessError("metadata must be an object", NsErrorCode.INVALID_VALUE)

        metadata: dict[str, str] = {}
        for key, item_value in raw_metadata.items():
            key_text = str(key).strip()
            if not key_text:
                continue
            if item_value is None:
                continue
            metadata[key_text] = str(item_value).strip()

        return metadata

    @classmethod
    def _normalize_page(cls, value: Any) -> int:
        """Normalize page number."""
        if value in (None, ""):
            return cls.DEFAULT_PAGE

        try:
            page = int(value)
        except (TypeError, ValueError) as exc:
            raise BusinessError("page is invalid", NsErrorCode.INVALID_PAGINATION_PARAMETERS) from exc

        if page <= 0:
            raise BusinessError("page must be positive", NsErrorCode.INVALID_PAGINATION_PARAMETERS)

        return page

    @classmethod
    def _normalize_page_size(cls, value: Any) -> int:
        """Normalize page size."""
        if value in (None, ""):
            return cls.DEFAULT_PAGE_SIZE

        try:
            page_size = int(value)
        except (TypeError, ValueError) as exc:
            raise BusinessError("page_size is invalid", NsErrorCode.INVALID_PAGINATION_PARAMETERS) from exc

        if page_size <= 0:
            raise BusinessError("page_size must be positive", NsErrorCode.INVALID_PAGINATION_PARAMETERS)

        return min(page_size, cls.MAX_PAGE_SIZE)

    @staticmethod
    def _normalize_expires_seconds(value: Any) -> int | None:
        """Normalize optional presigned URL expires seconds."""
        if value in (None, ""):
            return None

        try:
            expires_seconds = int(value)
        except (TypeError, ValueError) as exc:
            raise BusinessError("expires_seconds is invalid", NsErrorCode.INVALID_VALUE) from exc

        if expires_seconds <= 0:
            raise BusinessError("expires_seconds must be positive", NsErrorCode.INVALID_VALUE)

        return expires_seconds

    @staticmethod
    def _resolve_trace_id(request) -> str | None:
        """Resolve trace id from request."""
        trace_id = getattr(request, "trace_id", None)
        if isinstance(trace_id, str) and trace_id.strip():
            return trace_id.strip()

        headers = getattr(request, "headers", None)
        if headers is None:
            return None

        header_trace_id = headers.get("X-Trace-Id")
        if isinstance(header_trace_id, str) and header_trace_id.strip():
            return header_trace_id.strip()

        return None

    @classmethod
    def _serialize_upload_result(cls, result: NsObjectUploadResult) -> dict[str, Any]:
        """Serialize upload result."""
        return {
            "object_info": cls._serialize_object_info(result.object_info),
            "object_ref": cls._serialize_object_ref(result.object_ref),
        }

    @staticmethod
    def _serialize_object_info(object_info: NsObjectInfo) -> dict[str, Any]:
        """Serialize object info."""
        return {
            "bucket": object_info.bucket,
            "object_name": object_info.object_name,
            "size": object_info.size,
            "etag": object_info.etag,
            "content_type": object_info.content_type,
            "last_modified": object_info.last_modified.isoformat() if object_info.last_modified else None,
            "metadata": dict(object_info.metadata),
            "version_id": object_info.version_id,
        }

    @staticmethod
    def _serialize_object_ref(object_ref: NsObjectRef) -> dict[str, Any]:
        """Serialize object reference."""
        return {
            "bucket": object_ref.bucket,
            "object_name": object_ref.object_name,
            "backend": object_ref.backend,
            "module_code": object_ref.module_code,
            "resource_type": object_ref.resource_type,
            "resource_id": object_ref.resource_id,
            "original_filename": object_ref.original_filename,
            "content_type": object_ref.content_type,
            "size": object_ref.size,
            "etag": object_ref.etag,
            "sha256": object_ref.sha256,
            "version_id": object_ref.version_id,
            "metadata": dict(object_ref.metadata),
        }

    @staticmethod
    async def _cleanup_uploaded_object(*, upload_result: NsObjectUploadResult) -> None:
        """Best-effort cleanup for uploaded object when object ref persistence fails."""
        try:
            storage_client = AsyncNsObjectStorageClient.get_default()
            await storage_client.remove_object(
                bucket=upload_result.object_ref.bucket,
                object_name=upload_result.object_ref.object_name,
            )
        except Exception:  # noqa
            return
