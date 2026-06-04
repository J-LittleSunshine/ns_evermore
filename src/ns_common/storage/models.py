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
