# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    TYPE_CHECKING,
)

from asgiref.sync import sync_to_async
from django.utils import timezone

from backend.common import BaseRepository
from ns_backend.iam.models import IamAuditLog

if TYPE_CHECKING:
    pass


class DecisionAuditRepository:
    audit_fields: tuple[str, ...] = (
        "id",
        "operator_id",
        "subject_type",
        "subject_id",
        "resource_type",
        "resource_id",
        "action_code",
        "result",
        "reason",
        "matched_acl_id",
        "matched_policy_id",
        "matched_rule_id",
        "matched_source",
        "trace_id",
        "created_at",
    )

    @classmethod
    async def create_log(cls, *, data: dict[str, Any]) -> dict[str, Any]:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamAuditLog)

        return await sync_to_async(cls._create_log_sync, thread_sensitive=True)(
            data=data,
            db_alias=db_alias,
        )

    @classmethod
    def _create_log_sync(cls, *, data: dict[str, Any], db_alias: str) -> dict[str, Any]:
        create_data = dict(data)
        create_data["created_at"] = timezone.now()

        instance = IamAuditLog.objects.using(db_alias).create(**create_data)

        return cls.serialize_instance(instance)

    @classmethod
    async def list_logs(cls, *, page: int, page_size: int, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamAuditLog)

        return await sync_to_async(cls._list_logs_sync, thread_sensitive=True)(
            page=page,
            page_size=page_size,
            filters=filters or {},
            db_alias=db_alias,
        )

    @classmethod
    def _list_logs_sync(cls, *, page: int, page_size: int, filters: dict[str, Any], db_alias: str) -> dict[str, Any]:
        queryset = IamAuditLog.objects.using(db_alias).all()

        if filters:
            queryset = queryset.filter(**filters)

        total = queryset.count()
        offset = (page - 1) * page_size
        rows = list(queryset.order_by("-id")[offset: offset + page_size])

        return {
            "items": [
                cls.serialize_instance(row)
                for row in rows
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    @classmethod
    def serialize_instance(cls, instance: IamAuditLog) -> dict[str, Any]:
        data: dict[str, Any] = {}

        for field in cls.audit_fields:
            value = getattr(instance, field, None)

            if hasattr(value, "isoformat"):
                value = value.isoformat()

            data[field] = value

        return data
