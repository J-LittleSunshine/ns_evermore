# -*- coding: utf-8 -*-
from __future__ import annotations

from ns_backend.exceptions import BusinessError


class BasePolicy:
    """通用策略基类。"""

    @staticmethod
    def deny(message: str, code: int = 11009) -> None:
        """拒绝当前操作。"""
        raise BusinessError(message, code)

    @classmethod
    def ensure(cls, condition: bool, message: str, code: int = 11009) -> None:
        """条件不满足时拒绝。"""
        if not condition:
            cls.deny(message, code)

    @staticmethod
    def is_truthy(value) -> bool:
        """统一 truthy 判断。"""
        return value in (True, 1, "1", "true", "True")

    @staticmethod
    def is_falsy(value) -> bool:
        """统一 falsy 判断。"""
        return value in (False, 0, "0", "false", "False")

