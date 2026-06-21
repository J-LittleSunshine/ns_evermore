# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    pass


@dataclass(slots=True, frozen=True, kw_only=True)
class NsObjectInfo:
    """Normalized object metadata returned by object storage backends."""

    bucket: str
    object_name: str
    size: int | None = None
    etag: str | None = None
    content_type: str | None = None
    last_modified: datetime | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    version_id: str | None = None


@dataclass(slots=True, frozen=True, kw_only=True)
class NsPresignedUrl:
    """Normalized presigned URL payload."""

    bucket: str
    object_name: str
    method: Literal["GET", "PUT"]
    url: str
    expires_seconds: int


@dataclass(slots=True, frozen=True, kw_only=True)
class NsPutObjectResult:
    """Normalized put object result."""

    bucket: str
    object_name: str
    etag: str | None = None
    version_id: str | None = None


@dataclass(slots=True, frozen=True, kw_only=True)
class NsObjectRef:
    """Stable object reference payload for business metadata persistence.

    This dataclass is not a database model.
    Business modules may persist these fields in their own tables later.
    """

    bucket: str
    object_name: str
    backend: str
    module_code: str
    resource_type: str
    resource_id: str | None = None
    original_filename: str | None = None
    content_type: str | None = None
    size: int | None = None
    etag: str | None = None
    sha256: str | None = None
    version_id: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True, frozen=True, kw_only=True)
class NsObjectUploadResult:
    """Normalized standard upload result with object info and business object reference."""

    object_info: NsObjectInfo
    object_ref: NsObjectRef
