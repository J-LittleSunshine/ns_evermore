# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    pass


@dataclass(slots=True, kw_only=True)
class NsObjectStorageConfig:
    """Unified object storage configuration loaded through ns_config."""

    backend: Literal["minio", "local_fs", "s3", "oss", "cos", "obs", "azure_blob"] = "local_fs"

    endpoint: str = ""
    access_key: str = ""
    secret_key: str = ""
    secure: bool = False
    region: str | None = None

    default_bucket: str = "ns-default"
    auto_create_bucket: bool = False
    key_prefix: str = "ns"

    presigned_get_expires_seconds: int = 3600
    presigned_put_expires_seconds: int = 900

    connect_timeout_seconds: float = 3.0
    read_timeout_seconds: float = 30.0
    max_pool_connections: int = 64

    local_root_path: str = "object_storage"

    multipart_threshold_size: int = 100 * 1024 * 1024
    multipart_part_size: int = 64 * 1024 * 1024
    max_object_size: int | None = None

    extra_headers: dict[str, str] = field(default_factory=dict)

    def resolved_backend(self) -> Literal["minio", "local_fs", "s3", "oss", "cos", "obs", "azure_blob"]:
        """Resolve configured object storage backend without runtime probing."""
        return self.backend
