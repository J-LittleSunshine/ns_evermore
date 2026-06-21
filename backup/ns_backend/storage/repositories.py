# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from asgiref.sync import sync_to_async
from django.utils import timezone

from ns_backend.storage.models import StorageObjectRef
from ns_common.storage import AsyncNsObjectRefRepository, NsObjectRef, NsObjectRefRepository
from ns_common.storage.errors import NsObjectStorageValidationError
from ns_common.storage.naming import normalize_module_code, normalize_original_filename, normalize_resource_id, normalize_resource_type
from ns_common.storage.utils import normalize_bucket_name, normalize_metadata, normalize_object_name

if TYPE_CHECKING:
    pass


class DjangoObjectRefRepository:
    """Django ORM implementation of NsObjectRefRepository."""

    model_class = StorageObjectRef

    def save_object_ref(self, object_ref: NsObjectRef) -> NsObjectRef:
        """Persist object reference and return saved reference."""
        normalized_ref = self._normalize_object_ref(object_ref)
        now = timezone.now()

        defaults = {
            "backend": normalized_ref.backend,
            "module_code": normalized_ref.module_code,
            "resource_type": normalized_ref.resource_type,
            "resource_id": normalized_ref.resource_id,
            "original_filename": normalized_ref.original_filename,
            "content_type": normalized_ref.content_type,
            "object_size": normalized_ref.size,
            "etag": normalized_ref.etag,
            "sha256": normalized_ref.sha256,
            "version_id": normalized_ref.version_id,
            "metadata_json": dict(normalized_ref.metadata),
            "updated_at": now,
            "deleted_at": None,
        }

        item = self.model_class.objects.filter(
            bucket=normalized_ref.bucket,
            object_name=normalized_ref.object_name,
        ).first()

        if item is None:
            item = self.model_class.objects.create(
                bucket=normalized_ref.bucket,
                object_name=normalized_ref.object_name,
                created_at=now,
                **defaults,
            )
            return self._to_object_ref(item)

        for field_name, field_value in defaults.items():
            setattr(item, field_name, field_value)

        item.save(
            update_fields=[
                *defaults.keys()
            ]
        )
        return self._to_object_ref(item)

    def get_object_ref(self, *, bucket: str, object_name: str) -> NsObjectRef | None:
        """Get one object reference by bucket and object name."""
        normalized_bucket = normalize_bucket_name(bucket)
        normalized_object_name = normalize_object_name(object_name)

        item = self.model_class.objects.filter(
            bucket=normalized_bucket,
            object_name=normalized_object_name,
            deleted_at__isnull=True,
        ).first()

        if item is None:
            return None

        return self._to_object_ref(item)

    def list_object_refs(self, *, module_code: str, resource_type: str, resource_id: str | int | None = None) -> list[NsObjectRef]:
        """List object references by business resource identity."""
        normalized_module_code = normalize_module_code(module_code)
        normalized_resource_type = normalize_resource_type(resource_type)
        normalized_resource_id = normalize_resource_id(resource_id)

        queryset = self.model_class.objects.filter(
            module_code=normalized_module_code,
            resource_type=normalized_resource_type,
            deleted_at__isnull=True,
        )

        if normalized_resource_id is not None:
            queryset = queryset.filter(resource_id=normalized_resource_id)

        queryset = queryset.order_by("-created_at", "-id")
        return [self._to_object_ref(item) for item in queryset]

    def delete_object_ref(self, *, bucket: str, object_name: str) -> bool:
        """Soft delete object reference metadata, not the physical object."""
        normalized_bucket = normalize_bucket_name(bucket)
        normalized_object_name = normalize_object_name(object_name)

        updated_count = self.model_class.objects.filter(
            bucket=normalized_bucket,
            object_name=normalized_object_name,
            deleted_at__isnull=True,
        ).update(
            deleted_at=timezone.now(),
            updated_at=timezone.now(),
        )

        return updated_count > 0

    @classmethod
    def _normalize_object_ref(cls, object_ref: NsObjectRef) -> NsObjectRef:
        """Normalize object reference before persistence."""
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
    def _to_object_ref(item: StorageObjectRef) -> NsObjectRef:
        """Convert ORM model to NsObjectRef."""
        metadata = item.metadata_json if isinstance(item.metadata_json, dict) else {}

        return NsObjectRef(
            bucket=item.bucket,
            object_name=item.object_name,
            backend=item.backend,
            module_code=item.module_code,
            resource_type=item.resource_type,
            resource_id=item.resource_id,
            original_filename=item.original_filename,
            content_type=item.content_type,
            size=item.object_size,
            etag=item.etag,
            sha256=item.sha256,
            version_id=item.version_id,
            metadata=dict(metadata),
        )


class AsyncDjangoObjectRefRepository:
    """Async wrapper for DjangoObjectRefRepository."""

    def __init__(self, repository: DjangoObjectRefRepository | None = None) -> None:
        """Initialize async Django object reference repository."""
        self._repository = repository or DjangoObjectRefRepository()

    async def save_object_ref(self, object_ref: NsObjectRef) -> NsObjectRef:
        """Persist object reference and return saved reference."""
        return await sync_to_async(self._repository.save_object_ref, thread_sensitive=True)(object_ref)

    async def get_object_ref(self, *, bucket: str, object_name: str) -> NsObjectRef | None:
        """Get one object reference by bucket and object name."""
        return await sync_to_async(self._repository.get_object_ref, thread_sensitive=True)(bucket=bucket, object_name=object_name)

    async def list_object_refs(self, *, module_code: str, resource_type: str, resource_id: str | int | None = None) -> list[NsObjectRef]:
        """List object references by business resource identity."""
        return await sync_to_async(self._repository.list_object_refs, thread_sensitive=True)(module_code=module_code, resource_type=resource_type, resource_id=resource_id)

    async def delete_object_ref(self, *, bucket: str, object_name: str) -> bool:
        """Soft delete object reference metadata, not the physical object."""
        return await sync_to_async(self._repository.delete_object_ref, thread_sensitive=True)(bucket=bucket, object_name=object_name)


def _type_check_django_repositories() -> None:
    """Validate Django repositories against ns_common protocols for static type checkers."""
    sync_repository: NsObjectRefRepository = DjangoObjectRefRepository()
    async_repository: AsyncNsObjectRefRepository = AsyncDjangoObjectRefRepository()
    _ = (
        sync_repository,
        async_repository
    )
