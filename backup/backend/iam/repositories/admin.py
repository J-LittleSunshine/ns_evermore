# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from iam.constants import IAM_DB_ALIAS
from iam.models import IamUser

if TYPE_CHECKING:
    pass


class AdminRepository:
    """IAM 管理员初始化数据访问层。"""

    @staticmethod
    def exists_by_username(username: str) -> bool:
        """检查管理员用户名是否已存在。"""
        return IamUser.objects.using(IAM_DB_ALIAS).filter(
            username=username,
        ).exists()

    @staticmethod
    def create_admin_user(data: dict[str, Any]) -> IamUser:
        """创建系统管理员。"""
        return IamUser.objects.using(IAM_DB_ALIAS).create(**data)
