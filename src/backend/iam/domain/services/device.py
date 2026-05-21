# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import uuid

from django.utils import timezone

from iam.models import IamUserDevice
from iam.repositories.device import DeviceRepository


class DeviceDomainService:
    """设备领域服务。"""

    @classmethod
    async def get_or_create_device(
        cls,
        user_id: int,
        device_name: str,
        device_type: str,
        fingerprint_raw: str,
        client_ip: str | None = None,
        os_name: str | None = None,
        browser_name: str | None = None,
    ) -> IamUserDevice:
        """按设备指纹获取或创建设备。"""
        fingerprint_hash = cls.hash_fingerprint(fingerprint_raw)

        device = await DeviceRepository.get_active_by_fingerprint(
            user_id=user_id,
            fingerprint_hash=fingerprint_hash,
        )

        if device:
            await DeviceRepository.update_activity(
                device=device,
                client_ip=client_ip,
            )
            return device

        now = timezone.now()

        return await DeviceRepository.create_device(
            user_id=user_id,
            device_id=uuid.uuid4().hex,
            device_name=device_name,
            device_type=device_type,
            os_name=os_name,
            browser_name=browser_name,
            fingerprint_hash=fingerprint_hash,
            trusted=0,
            status=1,
            first_login_at=now,
            last_active_at=now,
            last_client_ip=client_ip,
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    def hash_fingerprint(fingerprint_raw: str) -> str:
        """计算设备指纹哈希。"""
        return hashlib.sha256(fingerprint_raw.encode("utf-8")).hexdigest()
