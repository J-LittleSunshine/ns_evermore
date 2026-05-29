# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from iam.models import IamPermission
from iam.validators import PermissionValidator
from iam.views.base import BaseIamViewSet

if TYPE_CHECKING:
    pass


class PermissionViewSet(BaseIamViewSet):
    model_class = IamPermission
    validator_class = PermissionValidator
    list_fields = detail_fields = (
        "id", "permission_code", "permission_name",
        "permission_type", "parent_id", "status",
    )
    create_fields = (
        "permission_code", "permission_name", "permission_type", "parent_id", "status",
    )
    update_fields = (
        "permission_name", "permission_type", "parent_id", "status",
    )
