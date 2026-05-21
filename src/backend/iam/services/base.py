# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from django.utils import timezone

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
		page, page_size = cls.normalize_page(page, page_size)
		items, total = await CrudRepository.list_items(
			model_class=model_class,
			page=page,
			page_size=page_size,
		)

		return {
			"items": [cls.serialize(item, fields) for item in items],
			"pagination": {
				"page": page,
				"page_size": page_size,
				"total": total,
				"total_pages": (total + page_size - 1) // page_size,
			},
		}

	@classmethod
	async def detail_item(cls, model_class, item_id: int, fields: tuple[str, ...]) -> dict[str, Any]:
		cls.ensure_model_class(model_class)
		item = await cls.get_item(model_class=model_class, item_id=item_id)
		return cls.serialize(item, fields)

	@classmethod
	async def create_item(
		cls,
		model_class,
		data: dict[str, Any],
		operator_id: int | None = None,
	) -> dict[str, Any]:
		cls.ensure_model_class(model_class)
		data = cls.fill_create_audit_fields(
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
		data = cls.fill_update_audit_fields(
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
	def normalize_page(page: int | str | None, page_size: int | str | None) -> tuple[int, int]:
		try:
			normalized_page = max(int(page or 1), 1)
			normalized_page_size = min(max(int(page_size or 20), 1), 100)
		except (TypeError, ValueError):
			raise BusinessError("分页参数非法", 12006)

		return normalized_page, normalized_page_size

	@classmethod
	def fill_create_audit_fields(
		cls,
		model_class,
		data: dict[str, Any],
		operator_id: int | None = None,
	) -> dict[str, Any]:
		result = data.copy()
		now = timezone.now()
		field_names = cls.get_model_field_names(model_class)

		if "created_by" in field_names:
			result.setdefault("created_by", operator_id)

		if "updated_by" in field_names:
			result.setdefault("updated_by", operator_id)

		if "created_at" in field_names:
			result.setdefault("created_at", now)

		if "updated_at" in field_names:
			result.setdefault("updated_at", now)

		return result

	@classmethod
	def fill_update_audit_fields(
		cls,
		model_class,
		data: dict[str, Any],
		operator_id: int | None = None,
	) -> dict[str, Any]:
		result = data.copy()
		field_names = cls.get_model_field_names(model_class)

		if "updated_by" in field_names:
			result["updated_by"] = operator_id

		if "updated_at" in field_names:
			result["updated_at"] = timezone.now()

		return result

	@staticmethod
	def serialize(instance, fields: tuple[str, ...]) -> dict[str, Any]:
		result = {}

		for field in fields:
			value = getattr(instance, field)

			if isinstance(value, (datetime, date)):
				value = value.isoformat()

			result[field] = value

		return result

	@staticmethod
	def ensure_model_class(model_class) -> None:
		if model_class is None:
			raise BusinessError("model_class 未配置", 10006)

	@staticmethod
	def get_model_field_names(model_class) -> set[str]:
		return {field.name for field in model_class._meta.fields}


__all__ = ["CrudService"]

