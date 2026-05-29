# -*- coding: utf-8 -*-
from __future__ import annotations

from django.utils import timezone


class AuditDataMixin:
    """审计字段填充工具。"""

    @staticmethod
    def fill_create_audit_fields(data: dict, operator_id: int | None = None) -> dict:
        """填充新增场景的审计字段。"""
        now = timezone.now()
        result = data.copy()
        result.setdefault("created_at", now)
        result["updated_at"] = now
        result["created_by"] = operator_id
        result["updated_by"] = operator_id
        return result

    @staticmethod
    def fill_update_audit_fields(data: dict, operator_id: int | None = None) -> dict:
        """填充更新场景的审计字段。"""
        result = data.copy()
        result["updated_at"] = timezone.now()
        result["updated_by"] = operator_id
        return result

    @classmethod
    def fill_grant_audit_fields(cls, data: dict, operator_id: int | None = None) -> dict:
        """填充授权场景的审计字段。"""
        result = cls.fill_create_audit_fields(data, operator_id=operator_id)
        result["granted_by_id"] = operator_id
        return result
