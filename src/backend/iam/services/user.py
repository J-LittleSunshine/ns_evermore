# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from django.contrib.auth.hashers import make_password
from django.utils import timezone

from iam.policies.organization import OrganizationPolicy
from iam.policies.tenant import TenantPolicy
from iam.policies.user import UserPolicy
from iam.repositories.user import UserRepository
from iam.services.tenant import TenantService
from ns_backend.exceptions import BusinessError


class UserService:
	"""用户服务。"""

	@classmethod
	async def list_users(
		cls,
		fields: tuple[str, ...],
		operator,
		page: int = 1,
		page_size: int = 20,
		include_staff: bool = False,
		include_superuser: bool = False,
	) -> dict[str, Any]:
		page, page_size = cls.normalize_page(page, page_size)
		tenant_filter = UserPolicy.get_user_tenant_filter(operator)
		users, total = await UserRepository.list_users(
			page=page,
			page_size=page_size,
			include_staff=include_staff,
			include_superuser=include_superuser,
			tenant_filter=tenant_filter,
		)

		return {
			"items": [cls.serialize(user, fields) for user in users],
			"pagination": {
				"page": page,
				"page_size": page_size,
				"total": total,
				"total_pages": (total + page_size - 1) // page_size,
			},
		}

	@classmethod
	async def get_user(cls, user_id: int, operator):
		if not user_id:
			raise BusinessError("id 不能为空", 10001)

		context = TenantService.from_user(operator)

		if TenantPolicy.is_platform_admin(context):
			user = await UserRepository.get_by_id(user_id)
		elif TenantPolicy.is_enterprise_user(context):
			TenantPolicy.ensure_enterprise_context(context)
			user = await UserRepository.get_by_id_for_company(
				user_id=user_id,
				company_id=context.company_id,
			)
		else:
			user = await UserRepository.get_by_id_for_self(
				user_id=user_id,
				operator_user_id=context.user_id,
			)

		if not user:
			raise BusinessError("用户不存在", 10103)

		return user

	@classmethod
	async def detail_user(cls, user_id: int, fields: tuple[str, ...], operator) -> dict[str, Any]:
		user = await cls.get_user(user_id=user_id, operator=operator)
		return cls.serialize(user, fields)

	@classmethod
	async def create_user(
		cls,
		data: dict[str, Any],
		operator,
		operator_id: int | None = None,
	) -> dict[str, Any]:
		create_payload = UserPolicy.build_create_payload(operator, data)

		company_id = create_payload.get("company_id")

		if company_id:
			await OrganizationPolicy.ensure_subsidiary_belongs_to_company(
				subsidiary_id=create_payload.get("subsidiary_id"),
				company_id=company_id,
			)
			await OrganizationPolicy.ensure_department_belongs_to_company(
				department_id=create_payload.get("department_id"),
				company_id=company_id,
			)

		create_data = cls.build_create_data(
			data=create_payload,
			operator_id=operator_id,
		)
		user = await UserRepository.create_user(create_data)
		return {"id": user.id}

	@classmethod
	async def update_user(
		cls,
		user_id: int,
		data: dict[str, Any],
		operator,
		operator_id: int | None = None,
	) -> None:
		UserPolicy.ensure_can_update_user_fields(operator, data)

		user = await cls.get_user(user_id=user_id, operator=operator)
		update_data = cls.build_update_data(
			data=data,
			operator_id=operator_id,
		)

		next_is_active = update_data.get("is_active")
		should_revoke = (
			next_is_active is not None
			and str(next_is_active) == "0"
			and bool(user.is_active)
		)

		company_scope = UserPolicy.get_operator_company_scope(operator)

		if should_revoke:
			await UserRepository.update_user_and_revoke_sessions_tokens(
				user_id=user.id,
				data=update_data,
				company_id=company_scope,
			)
			return

		await UserRepository.update_user(user=user, data=update_data)

	@classmethod
	async def delete_user(cls, user_id: int, operator) -> None:
		user = await cls.get_user(user_id=user_id, operator=operator)
		await UserRepository.revoke_and_delete_user(
			user_id=user.id,
			company_id=UserPolicy.get_operator_company_scope(operator),
		)

	@classmethod
	async def reset_password(
		cls,
		user_id: int,
		raw_password: str,
		operator,
		operator_id: int | None = None,
	) -> None:
		user = await cls.get_user(user_id=user_id, operator=operator)
		update_data = cls.build_reset_password_data(
			raw_password=raw_password,
			operator_id=operator_id,
		)
		await UserRepository.update_user_and_revoke_sessions_tokens(
			user_id=user.id,
			data=update_data,
			company_id=UserPolicy.get_operator_company_scope(operator),
		)

	@staticmethod
	def normalize_page(page: int | str | None, page_size: int | str | None) -> tuple[int, int]:
		try:
			normalized_page = max(int(page or 1), 1)
			normalized_page_size = min(max(int(page_size or 20), 1), 100)
		except (TypeError, ValueError):
			raise BusinessError("分页参数非法", 12006)

		return normalized_page, normalized_page_size

	@staticmethod
	def build_create_data(data: dict[str, Any], operator_id: int | None = None) -> dict[str, Any]:
		create_data = data.copy()
		raw_password = create_data.pop("password", None)

		if not raw_password:
			raise BusinessError("password 不能为空", 10101)

		now = timezone.now()
		create_data["password"] = make_password(raw_password)
		create_data.setdefault("created_by", operator_id)
		create_data.setdefault("updated_by", operator_id)
		create_data.setdefault("created_at", now)
		create_data.setdefault("updated_at", now)
		return create_data

	@staticmethod
	def build_update_data(data: dict[str, Any], operator_id: int | None = None) -> dict[str, Any]:
		update_data = data.copy()
		update_data["updated_by"] = operator_id
		update_data["updated_at"] = timezone.now()
		return update_data

	@staticmethod
	def build_reset_password_data(
		raw_password: str,
		operator_id: int | None = None,
	) -> dict[str, Any]:
		if not raw_password:
			raise BusinessError("password 不能为空", 10101)

		return {
			"password": make_password(raw_password),
			"updated_by": operator_id,
			"updated_at": timezone.now(),
		}


	@staticmethod
	def serialize(instance, fields: tuple[str, ...]) -> dict[str, Any]:
		result = {}

		for field in fields:
			value = getattr(instance, field)

			if isinstance(value, (datetime, date)):
				value = value.isoformat()

			result[field] = value

		return result


__all__ = ["UserService"]

