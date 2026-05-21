# -*- coding: utf-8 -*-
from __future__ import annotations

from django.utils import timezone

from iam.constants import IAM_DB_ALIAS
from iam.models import IamUserDevice


class DeviceRepository:
    """设备数据访问层。"""

    @staticmethod
    async def get_active_by_fingerprint(
        user_id: int,
        fingerprint_hash: str,
    ) -> IamUserDevice | None:
        return await IamUserDevice.objects.using(IAM_DB_ALIAS).filter(
            user_id=user_id,
            fingerprint_hash=fingerprint_hash,
            status=1,
        ).afirst()

    @staticmethod
    async def update_activity(
        device: IamUserDevice,
        client_ip: str | None = None,
    ) -> None:
        now = timezone.now()
        device.last_active_at = now
        device.last_client_ip = client_ip
        device.updated_at = now

        await device.asave(
            using=IAM_DB_ALIAS,
            update_fields=[
                "last_active_at",
                "last_client_ip",
                "updated_at",
            ],
        )

    @staticmethod
    async def create_device(**kwargs) -> IamUserDevice:
        return await IamUserDevice.objects.using(IAM_DB_ALIAS).acreate(**kwargs)
