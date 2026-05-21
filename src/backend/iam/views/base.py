# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from iam.repositories.base import CrudRepository
from iam.services.auth import VerifyService
from iam.services.permission import PermissionService
from ns_backend.auth import AuthenticatedRequestViewSet
from ns_backend.exceptions import BusinessError, ValidateError

if TYPE_CHECKING:
    pass


class IamRequestViewSet(AuthenticatedRequestViewSet):
    verify_service = VerifyService
    permission_service = PermissionService


class BaseIamViewSet(IamRequestViewSet):
    model_class = None
    validator_class = None

    list_fields: tuple[str, ...] = ()
    detail_fields: tuple[str, ...] = ()
    update_fields: tuple[str, ...] = ()

    async def list_item(self, request, *args, **kwargs):
        page = request.data.get("page", 1)
        page_size = request.data.get("page_size", 20)

        self.ensure_model_class()

        data = await CrudRepository.list_items(
            model_class=self.model_class,
            fields=self.list_fields,
            page=page,
            page_size=page_size,
        )

        return self.success_response(data)

    async def detail_item(self, request, *args, **kwargs):
        item_id = request.data.get("id")

        self.ensure_model_class()

        data = await CrudRepository.detail_item(
            model_class=self.model_class,
            item_id=item_id,
            fields=self.detail_fields,
        )

        return self.success_response(data)

    async def create_item(self, request, *args, **kwargs):
        data = self.validate_create_data(request.data)
        operator_id = self.get_operator_id(request)

        self.ensure_model_class()

        result = await CrudRepository.create_item_with_audit(
            model_class=self.model_class,
            data=data,
            operator_id=operator_id,
        )

        return self.success_response(result)

    async def update_item(self, request, *args, **kwargs):
        item_id = request.data.get("id")
        data = self.validate_update_data(request.data)
        operator_id = self.get_operator_id(request)

        self.ensure_model_class()

        await CrudRepository.update_item_with_audit(
            model_class=self.model_class,
            item_id=item_id,
            data=data,
            operator_id=operator_id,
        )

        return self.success_response()

    async def delete_item(self, request, *args, **kwargs):
        item_id = request.data.get("id")

        self.ensure_model_class()

        await CrudRepository.delete_item_by_id(
            model_class=self.model_class,
            item_id=item_id,
        )

        return self.success_response()

    def validate_create_data(self, data: dict[str, Any]) -> dict[str, Any]:
        if self.validator_class:
            return self.validator_class.validate_create(data)

        return data

    def validate_update_data(self, data: dict[str, Any]) -> dict[str, Any]:
        for field in data.keys():
            if field == "id":
                continue

            if field not in self.update_fields:
                raise ValidateError(f"不允许更新字段：{field}", 12005)

        if self.validator_class:
            return self.validator_class.validate_update(data)

        return {
            field: data[field]
            for field in self.update_fields
            if field in data
        }

    @staticmethod
    def get_operator_id(request) -> int | None:
        current_user = getattr(request, "current_user", None)
        return getattr(current_user, "id", None)

    def ensure_model_class(self) -> None:
        if self.model_class is None:
            raise BusinessError("model_class 未配置", 10006)

