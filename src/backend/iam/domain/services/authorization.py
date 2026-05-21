# -*- coding: utf-8 -*-
from __future__ import annotations

from ns_backend.exceptions import BusinessError
from ns_backend.utils.audit import AuditDataMixin


class AuthorizationDomainService(AuditDataMixin):
    """IAM 授权关系领域服务。"""

    @classmethod
    def build_relation_create_data(
        cls,
        data: dict,
        operator_id: int | None = None,
    ) -> dict:
        """构建关系创建数据。"""
        return cls.fill_create_audit_fields(data, operator_id=operator_id)

    @classmethod
    def build_permission_create_data(
        cls,
        data: dict,
        operator_id: int | None = None,
    ) -> dict:
        """构建权限授权创建数据。"""
        return cls.fill_grant_audit_fields(data, operator_id=operator_id)

    @staticmethod
    def ensure_deleted_rows(deleted_count: int, message: str, code: int) -> None:
        """确保删除操作命中至少一行。"""
        if deleted_count <= 0:
            raise BusinessError(message, code)

    @staticmethod
    def ensure_required_pair(left_value, right_value, message: str, code: int) -> None:
        """确保两个必填参数均存在。"""
        if not left_value or not right_value:
            raise BusinessError(message, code)
