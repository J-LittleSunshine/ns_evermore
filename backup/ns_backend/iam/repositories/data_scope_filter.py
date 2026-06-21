# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ns_backend.iam.schemas import DataScopeFilterPlan

if TYPE_CHECKING:
    pass


class DataScopeQuerySetHelper:
    """Helper for applying IAM data-scope filter plans to querysets."""

    @staticmethod
    def apply(queryset: Any, plan: DataScopeFilterPlan) -> Any:
        """Apply data-scope filter plan to queryset."""
        if not plan.allowed:
            return queryset.none()

        if not plan.filters:
            return queryset

        return queryset.filter(**plan.filters)
