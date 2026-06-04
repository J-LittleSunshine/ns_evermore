# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

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


@dataclass(slots=True, frozen=True, kw_only=True)
class NsStorageResource:
    """Business resource identity for object storage integration."""

    module_code: str
    resource_type: str
    resource_id: str | int | None = None

    def normalized(self) -> "NsStorageResource":
        """Return normalized resource identity."""
        return NsStorageResource(
            module_code=normalize_module_code(self.module_code),
            resource_type=normalize_resource_type(self.resource_type),
            resource_id=normalize_resource_id(self.resource_id),
        )


@dataclass(slots=True, frozen=True, kw_only=True)
class NsObjectUploadContext:
    """Standard upload context passed by business modules."""

    module_code: str
    resource_type: str
    resource_id: str | int | None = None
    original_filename: str | None = None
    object_name: str | None = None
    bucket: str | None = None
    content_type: str | None = None
    uploaded_by: str | int | None = None
    trace_id: str | None = None
    extra_metadata: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_resource(
            cls,
            *,
            resource: NsStorageResource,
            original_filename: str | None = None,
            object_name: str | None = None,
            bucket: str | None = None,
            content_type: str | None = None,
            uploaded_by: str | int | None = None,
            trace_id: str | None = None,
            extra_metadata: dict[str, str] | None = None,
    ) -> "NsObjectUploadContext":
        """Build upload context from business resource identity."""
        normalized_resource = resource.normalized()
        return cls(
            module_code=normalized_resource.module_code,
            resource_type=normalized_resource.resource_type,
            resource_id=normalized_resource.resource_id,
            original_filename=original_filename,
            object_name=object_name,
            bucket=bucket,
            content_type=content_type,
            uploaded_by=uploaded_by,
            trace_id=trace_id,
            extra_metadata=extra_metadata or {},
        )

    def normalized(self) -> "NsObjectUploadContext":
        """Return normalized upload context."""
        normalized_object_name: str | None = normalize_object_name(self.object_name) if self.object_name else None
        normalized_bucket: str | None = normalize_bucket_name(self.bucket) if self.bucket else None

        return NsObjectUploadContext(
            module_code=normalize_module_code(self.module_code),
            resource_type=normalize_resource_type(self.resource_type),
            resource_id=normalize_resource_id(self.resource_id),
            original_filename=normalize_original_filename(self.original_filename),
            object_name=normalized_object_name,
            bucket=normalized_bucket,
            content_type=str(self.content_type).strip() if self.content_type else None,
            uploaded_by=str(self.uploaded_by).strip() if self.uploaded_by is not None and str(self.uploaded_by).strip() else None,
            trace_id=str(self.trace_id).strip() if self.trace_id is not None and str(self.trace_id).strip() else None,
            extra_metadata=normalize_metadata(self.extra_metadata),
        )


class NsObjectRefRepository(Protocol):
    """Protocol business modules can implement to persist object references."""

    def save_object_ref(self, object_ref: NsObjectRef) -> NsObjectRef:
        """Persist object reference and return saved reference."""

    def get_object_ref(self, *, bucket: str, object_name: str) -> NsObjectRef | None:
        """Get one object reference by bucket and object name."""

    def list_object_refs(self, *, module_code: str, resource_type: str, resource_id: str | int | None = None) -> list[NsObjectRef]:
        """List object references by business resource identity."""

    def delete_object_ref(self, *, bucket: str, object_name: str) -> bool:
        """Delete object reference metadata, not necessarily the physical object."""


class AsyncNsObjectRefRepository(Protocol):
    """Async protocol business modules can implement to persist object references."""

    async def save_object_ref(self, object_ref: NsObjectRef) -> NsObjectRef:
        """Persist object reference and return saved reference."""

    async def get_object_ref(self, *, bucket: str, object_name: str) -> NsObjectRef | None:
        """Get one object reference by bucket and object name."""

    async def list_object_refs(self, *, module_code: str, resource_type: str, resource_id: str | int | None = None) -> list[NsObjectRef]:
        """List object references by business resource identity."""

    async def delete_object_ref(self, *, bucket: str, object_name: str) -> bool:
        """Delete object reference metadata, not necessarily the physical object."""
