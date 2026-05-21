# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from iam.models import IamRole
from iam.validators import RoleValidator
from iam.views.base import BaseIamViewSet

if TYPE_CHECKING:
    pass


class RoleViewSet(BaseIamViewSet):
    model_class = IamRole
    validator_class = RoleValidator
    list_fields = detail_fields = ("id", "role_code", "role_name", "role_scope", "status")
    create_fields = ("role_code", "role_name", "role_scope", "status")
    update_fields = ("role_name", "role_scope", "status")
