# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import BinaryIO, TYPE_CHECKING

if TYPE_CHECKING:
    pass

_SHA256_CHUNK_SIZE = 1024 * 1024


def calculate_sha256_bytes(data: bytes) -> str:
    """Calculate sha256 hex digest for bytes."""
    if not isinstance(data, bytes):
        raise TypeError("sha256 data must be bytes")

    return hashlib.sha256(data).hexdigest()


def calculate_sha256_file(file_path: str | Path) -> str:
    """Calculate sha256 hex digest for one file."""
    path: Path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"sha256 file does not exist: {path}")

    digest = hashlib.sha256()
    with path.open("rb") as file:
        while True:
            chunk: bytes = file.read(_SHA256_CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)

    return digest.hexdigest()


def calculate_sha256_stream(stream: BinaryIO, *, chunk_size: int = _SHA256_CHUNK_SIZE) -> str:
    """Calculate sha256 hex digest for a readable binary stream.

    The caller is responsible for resetting stream position when needed.
    """
    if isinstance(chunk_size, bool) or not isinstance(chunk_size, int):
        raise ValueError("sha256 chunk_size must be int")

    if chunk_size <= 0:
        raise ValueError("sha256 chunk_size must be positive")

    digest = hashlib.sha256()

    while True:
        chunk: bytes = stream.read(chunk_size)
        if not chunk:
            break
        digest.update(chunk)

    return digest.hexdigest()
