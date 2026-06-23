# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    TYPE_CHECKING
)

from backend.db.routers import AppDatabaseRouter
from ns_common import NsDependencyError

if TYPE_CHECKING:
    pass


class BaseRepository:

    @staticmethod
    def ensure_model_class(model_class: Any) -> None:
        if model_class is None:
            raise NsDependencyError("model_class is not configured.",
                details={
                    "field": "model_class",
                },
            )

        meta = getattr(model_class, "_meta", None)
        if meta is None:
            raise NsDependencyError("model_class is not a Django model.",
                details={
                    "model_class": repr(model_class),
                },
            )

    @classmethod
    def resolve_db_alias(cls, model_class: Any, db_alias: str | None = None) -> str:
        if db_alias:
            return db_alias

        cls.ensure_model_class(model_class)

        app_label = str(model_class._meta.app_label)  # noqa
        target_db = AppDatabaseRouter.get_target_db(app_label)

        return target_db or AppDatabaseRouter.DEFAULT_DB_ALIAS

    @classmethod
    def build_queryset(cls, model_class: Any, *, db_alias: str | None = None, order_by: tuple[str, ...] = ("-id",)) -> Any:
        cls.ensure_model_class(model_class)

        resolved_db_alias = cls.resolve_db_alias(model_class=model_class, db_alias=db_alias)
        queryset = model_class.objects.using(resolved_db_alias).all()

        if order_by:
            queryset = queryset.order_by(*order_by)

        return queryset
