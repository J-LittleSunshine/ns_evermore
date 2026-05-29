# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


class BusinessError(Exception):
    def __init__(self, msg: str, code: int = 40000, data: Any = None) -> None:
        self.msg = msg
        self.code = code
        self.data = data
        super().__init__(msg)


class ValidateError(BusinessError):
    def __init__(self, msg: str, code: int = 12000, data: Any = None) -> None:
        super().__init__(msg=msg, code=code, data=data)
