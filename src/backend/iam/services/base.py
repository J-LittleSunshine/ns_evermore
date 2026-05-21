# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from iam.repositories.base import CrudRepository
from ns_backend.exceptions import BusinessError


class CrudService:
	"""通用 CRUD 服务。"""

	@classmethod
	async def list_items(
		cls,
		model_class,
		fields: tuple[str, ...],
		page: int = 1,
		page_size: int = 20,
	) -> dict[str, Any]:
		cls.ensure_model_class(model_class)
		return await CrudRepository.list_items(
			model_class=model_class,
			fields=fields,
			page=page,
			page_size=page_size,
		)

	@classmethod
	async def detail_item(cls, model_class, item_id: int, fields: tuple[str, ...]) -> dict[str, Any]:
		cls.ensure_model_class(model_class)
		item = await cls.get_item(model_class=model_class, item_id=item_id)
		return CrudRepository.serialize(item, fields)

	@classmethod
	async def create_item(
		cls,
		model_class,
		data: dict[str, Any],
		operator_id: int | None = None,
	) -> dict[str, Any]:
		cls.ensure_model_class(model_class)
		data = CrudRepository.fill_create_audit_fields(
			model_class=model_class,
			data=data,
			operator_id=operator_id,
		)
		item = await CrudRepository.create_item(model_class=model_class, data=data)
		return {"id": item.id}

	@classmethod
	async def update_item(
		cls,
		model_class,
		item_id: int,
		data: dict[str, Any],
		operator_id: int | None = None,
	) -> None:
		cls.ensure_model_class(model_class)
		item = await cls.get_item(model_class=model_class, item_id=item_id)
		data = CrudRepository.fill_update_audit_fields(
			model_class=model_class,
			data=data,
			operator_id=operator_id,
		)
		await CrudRepository.update_item(instance=item, data=data)

	@classmethod
	async def delete_item(cls, model_class, item_id: int) -> None:
		cls.ensure_model_class(model_class)
		item = await cls.get_item(model_class=model_class, item_id=item_id)
		await CrudRepository.delete_item(item)

	@staticmethod
	async def get_item(model_class, item_id: int):
		if not item_id:
			raise BusinessError("id 不能为空", 10001)

		item = await CrudRepository.get_by_id(model_class=model_class, item_id=item_id)

		if not item:
			raise BusinessError("数据不存在", 10002)

		return item

	@staticmethod
	def ensure_model_class(model_class) -> None:
		if model_class is None:
			raise BusinessError("model_class 未配置", 10006)



__all__ = ["CrudService"]

