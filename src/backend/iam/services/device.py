# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import uuid

from django.utils import timezone

from iam.constants import IAM_DB_ALIAS
from iam.models import IamUserDevice


class DeviceService:

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
        fingerprint_hash = hashlib.sha256(
            fingerprint_raw.encode("utf-8")
        ).hexdigest()

        device = await IamUserDevice.objects.using(IAM_DB_ALIAS).filter(
            user_id=user_id,
            fingerprint_hash=fingerprint_hash,
            status=1,
        ).afirst()

        now = timezone.now()

        if device:
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

            return device

        return await IamUserDevice.objects.using(IAM_DB_ALIAS).acreate(
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
