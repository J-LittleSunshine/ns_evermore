# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


class IamDomainError(Exception):
    def __init__(self, message: str, code: int, data: Any = None) -> None:
        self.message = message
        self.code = code
        self.data = data
        super().__init__(message)
