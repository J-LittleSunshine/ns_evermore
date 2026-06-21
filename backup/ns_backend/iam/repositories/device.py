# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ns_backend.backend.common import BaseRepository
from ns_backend.iam.models import IamUserDevice

if TYPE_CHECKING:
    pass


class UserDeviceRepository:
    """Repository for IAM user device records."""

    @staticmethod
    async def get_by_user_and_fingerprint(*, user_id: int, fingerprint_hash: str) -> IamUserDevice | None:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamUserDevice)
        return await IamUserDevice.objects.using(db_alias).filter(user_id=user_id, fingerprint_hash=fingerprint_hash).afirst()

    @staticmethod
    async def create_device(data: dict[str, Any]) -> IamUserDevice:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamUserDevice)
        return await IamUserDevice.objects.using(db_alias).acreate(**data)

    @staticmethod
    async def update_device(device: IamUserDevice, data: dict[str, Any]) -> None:
        for field, value in data.items():
            setattr(device, field, value)
        db_alias = device._state.db or BaseRepository.resolve_db_alias(model_class=IamUserDevice)  # noqa
        await device.asave(using=db_alias, update_fields=list(data.keys()))
