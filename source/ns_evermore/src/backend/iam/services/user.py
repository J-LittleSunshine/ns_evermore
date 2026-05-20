# -*- coding: utf-8 -*-
from __future__ import annotations

from django.contrib.auth.hashers import make_password
from django.utils import timezone

from iam.constants import IAM_DB_ALIAS
from iam.models import IamUser
from iam.services.base import BaseIamService
from ns_backend.exceptions import BusinessError


class UserService(BaseIamService):
    model = IamUser

    @classmethod
    async def create_user(
        cls,
        data: dict,
        operator_id: int | None = None,
    ) -> dict:
        raw_password = data.pop("password", None)

        if not raw_password:
            raise BusinessError("password 不能为空", 10101)

        data["password"] = make_password(raw_password)

        return await cls.create_item(
            data=data,
            operator_id=operator_id,
        )

    @classmethod
    async def reset_password(
        cls,
        user_id: int,
        raw_password: str,
        operator_id: int | None = None,
    ) -> None:
        if not user_id:
            raise BusinessError("id 不能为空", 10001)

        if not raw_password:
            raise BusinessError("password 不能为空", 10101)

        user = await IamUser.objects.using(IAM_DB_ALIAS).filter(id=user_id).afirst()

        if not user:
            raise BusinessError("用户不存在", 10103)

        user.password = make_password(raw_password)
        user.updated_by = operator_id
        user.updated_at = timezone.now()

        await user.asave(
            using=IAM_DB_ALIAS,
            update_fields=["password", "updated_by", "updated_at"],
        )
