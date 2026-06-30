# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import (
    asdict,
    dataclass,
    field,
)
from typing import (
    Any,
    Mapping
)

from ns_common.exceptions import NsEvermoreError


@dataclass(slots=True, kw_only=True)
class RuntimeResult:
    success: bool
    code: str
    message: str
    data: Any = None
    error: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, data: Any = None, *, code: str = "OK", message: str = "success", metadata: Mapping[str, Any] | None = None) -> "RuntimeResult":
        return cls(
            success=True,
            code=code,
            message=message,
            data=data,
            error=None,
            metadata=dict(metadata or {}),
        )

    @classmethod
    def fail(cls, *, code: str, message: str, data: Any = None, error: Mapping[str, Any] | None = None, metadata: Mapping[str, Any] | None = None) -> "RuntimeResult":
        return cls(
            success=False,
            code=code,
            message=message,
            data=data,
            error=dict(error or {}),
            metadata=dict(metadata or {}),
        )

    @classmethod
    def from_exception(cls, error: Exception, *, metadata: Mapping[str, Any] | None = None) -> "RuntimeResult":
        if isinstance(error, NsEvermoreError):
            return cls.fail(
                code=error.code,
                message=error.message,
                error={
                    "type": error.__class__.__name__,
                    "numeric_code": error.numeric_code,
                    "details": error.details,
                },
                metadata=metadata,
            )

        return cls.fail(
            code="RUNTIME_HANDLER_ERROR",
            message=str(error) or error.__class__.__name__,
            error={
                "type": error.__class__.__name__,
                "details": {},
            },
            metadata=metadata,
        )

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> "RuntimeResult":
        if not isinstance(raw, dict):
            raise TypeError("runtime result must be a dict.")

        return cls(**dict(raw))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
