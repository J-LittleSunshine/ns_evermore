# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_common.config import NsObjectStorageConfig
from ns_common.storage.models import NsObjectInfo, NsObjectRef
from ns_common.storage.naming import (
    normalize_module_code,
    normalize_original_filename,
    normalize_resource_id,
    normalize_resource_type,
)
from ns_common.storage.utils import normalize_bucket_name, normalize_metadata, normalize_object_name

if TYPE_CHECKING:
    pass

_METADATA_MODULE = "ns-module"
_METADATA_RESOURCE_TYPE = "ns-resource-type"
_METADATA_RESOURCE_ID = "ns-resource-id"
_METADATA_ORIGINAL_FILENAME = "ns-original-filename"
_METADATA_UPLOADED_BY = "ns-uploaded-by"
_METADATA_TRACE_ID = "ns-trace-id"
_METADATA_SHA256 = "ns-sha256"


def build_standard_metadata(
        *,
        module_code: str,
        resource_type: str,
        resource_id: str | int | None = None,
        original_filename: str | None = None,
        uploaded_by: str | int | None = None,
        trace_id: str | None = None,
        sha256: str | None = None,
        extra_metadata: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build standard object metadata."""
    normalized_module_code = normalize_module_code(module_code)
    normalized_resource_type = normalize_resource_type(resource_type)
    normalized_resource_id = normalize_resource_id(resource_id)
    normalized_original_filename = normalize_original_filename(original_filename)

    metadata: dict[str, str] = {
        _METADATA_MODULE: normalized_module_code,
        _METADATA_RESOURCE_TYPE: normalized_resource_type,
    }

    if normalized_resource_id:
        metadata[_METADATA_RESOURCE_ID] = normalized_resource_id

    if normalized_original_filename:
        metadata[_METADATA_ORIGINAL_FILENAME] = normalized_original_filename

    if uploaded_by is not None and str(uploaded_by).strip():
        metadata[_METADATA_UPLOADED_BY] = str(uploaded_by).strip()

    if trace_id is not None and str(trace_id).strip():
        metadata[_METADATA_TRACE_ID] = str(trace_id).strip()

    if sha256 is not None and str(sha256).strip():
        metadata[_METADATA_SHA256] = str(sha256).strip().lower()

    if extra_metadata:
        for key, value in normalize_metadata(extra_metadata).items():
            if key in metadata:
                continue
            metadata[key] = value

    return normalize_metadata(metadata)


def build_object_ref(
        *,
        config: NsObjectStorageConfig,
        object_info: NsObjectInfo,
        module_code: str,
        resource_type: str,
        resource_id: str | int | None = None,
        original_filename: str | None = None,
        sha256: str | None = None,
        extra_metadata: dict[str, str] | None = None,
) -> NsObjectRef:
    """Build stable object reference from uploaded object info."""
    normalized_module_code = normalize_module_code(module_code)
    normalized_resource_type = normalize_resource_type(resource_type)
    normalized_resource_id = normalize_resource_id(resource_id)
    normalized_original_filename = normalize_original_filename(original_filename)

    bucket = normalize_bucket_name(object_info.bucket)
    object_name = normalize_object_name(object_info.object_name)

    metadata = build_standard_metadata(
        module_code=normalized_module_code,
        resource_type=normalized_resource_type,
        resource_id=normalized_resource_id,
        original_filename=normalized_original_filename,
        sha256=sha256,
        extra_metadata={
            **object_info.metadata,
            **(extra_metadata or {}),
        },
    )

    return NsObjectRef(
        bucket=bucket,
        object_name=object_name,
        backend=config.resolved_backend(),
        module_code=normalized_module_code,
        resource_type=normalized_resource_type,
        resource_id=normalized_resource_id,
        original_filename=normalized_original_filename,
        content_type=object_info.content_type,
        size=object_info.size,
        etag=object_info.etag,
        sha256=str(sha256).strip().lower() if sha256 else None,
        version_id=object_info.version_id,
        metadata=metadata,
    )
