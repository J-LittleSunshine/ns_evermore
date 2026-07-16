# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Mapping


class NsEvermoreError(Exception):
    code: str = "NS_ERROR"
    numeric_code: int = 100000
    default_message: str = "NsEvermore error."

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        numeric_code: int | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        self.message: str = message or self.default_message
        self.code: str = code or self.code
        self.numeric_code: int = numeric_code or self.numeric_code
        self.details: dict[str, Any] = dict(details or {})

        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "numeric_code": self.numeric_code,
            "message": self.message,
            "details": self.details,
        }

    def __str__(self) -> str:
        if not self.details:
            return f"[{self.code}/{self.numeric_code}] {self.message}"

        return f"[{self.code}/{self.numeric_code}] {self.message} details={self.details}"


class NsRuntimeError(NsEvermoreError):
    code = "NS_RUNTIME_ERROR"
    numeric_code = 100300
    default_message = "NsEvermore runtime error."
