# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.schemas import DataScopeFilterPlan


class DataScopeQuerySetHelper:
    """Data scope queryset filtering helper."""

    @staticmethod
    def apply(queryset, plan: DataScopeFilterPlan):
        if not plan.allowed:
            return queryset.none()

        if not plan.filters:
            return queryset

        return queryset.filter(**plan.filters)


__all__ = ["DataScopeQuerySetHelper"]

