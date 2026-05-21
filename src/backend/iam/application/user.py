# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from iam.domain.services.user import UserDomainService
from iam.repositories.user import UserRepository


class UserApplicationService:
    """用户管理应用服务。"""

    @classmethod
    async def list_users(
        cls,
        fields: tuple[str, ...],
        page: int = 1,
        page_size: int = 20,
        include_staff: bool = False,
        include_superuser: bool = False,
    ) -> dict[str, Any]:
        """获取用户分页列表。"""
        page, page_size = UserDomainService.normalize_page(page, page_size)
        users, total = await UserRepository.list_users(
            page=page,
            page_size=page_size,
            include_staff=include_staff,
            include_superuser=include_superuser,
        )

        return {
            "items": [UserDomainService.serialize(user, fields) for user in users],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
        }

    @classmethod
    async def get_user(cls, user_id: int):
        """获取用户。"""
        return await UserDomainService.get_user(user_id)

    @classmethod
    async def detail_user(cls, user_id: int, fields: tuple[str, ...]) -> dict[str, Any]:
        """获取用户详情。"""
        user = await cls.get_user(user_id)
        return UserDomainService.serialize(user, fields)

    @classmethod
    async def create_user(
        cls,
        data: dict[str, Any],
        operator_id: int | None = None,
    ) -> dict[str, Any]:
        """创建用户。"""
        create_data = UserDomainService.build_create_data(
            data=data,
            operator_id=operator_id,
        )
        user = await UserRepository.create_user(create_data)
        return {"id": user.id}

    @classmethod
    async def update_user(
        cls,
        user_id: int,
        data: dict[str, Any],
        operator_id: int | None = None,
    ) -> None:
        """更新用户。"""
        user = await cls.get_user(user_id)
        update_data = UserDomainService.build_update_data(
            data=data,
            operator_id=operator_id,
        )

        next_is_active = update_data.get("is_active")
        should_revoke = (
            next_is_active is not None
            and str(next_is_active) == "0"
            and bool(user.is_active)
        )

        if should_revoke:
            await UserRepository.update_user_and_revoke_sessions_tokens(
                user_id=user.id,
                data=update_data,
            )
            return

        await UserRepository.update_user(user=user, data=update_data)

    @classmethod
    async def delete_user(cls, user_id: int) -> None:
        """删除用户。"""
        await cls.get_user(user_id)
        await UserRepository.revoke_and_delete_user(user_id=user_id)

    @classmethod
    async def reset_password(
        cls,
        user_id: int,
        raw_password: str,
        operator_id: int | None = None,
    ) -> None:
        """重置用户密码。"""
        user = await cls.get_user(user_id)
        update_data = UserDomainService.build_reset_password_data(
            raw_password=raw_password,
            operator_id=operator_id,
        )
        await UserRepository.update_user_and_revoke_sessions_tokens(
            user_id=user.id,
            data=update_data,
        )

    @staticmethod
    def serialize(instance, fields: tuple[str, ...]) -> dict[str, Any]:
        """序列化用户。"""
        return UserDomainService.serialize(instance, fields)
