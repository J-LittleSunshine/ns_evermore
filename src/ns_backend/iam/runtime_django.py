# -*- coding: utf-8 -*-
"""Django adapters for IAM-R1 backend credential status persistence."""

from __future__ import annotations

import hashlib
from datetime import datetime

from django.core.cache import cache
from django.utils import timezone

from ns_common.iam import IamCredentialStatus


class DjangoRuntimeCredentialStatusStore:
    """Persist credential status in the configured backend IAM cache."""

    _PREFIX = "iam:r1:runtime-credential-status:"

    async def put(
        self,
        credential_id: str,
        status: IamCredentialStatus,
        expires_at: datetime,
    ) -> None:
        ttl = max(1, int((expires_at - timezone.now()).total_seconds()))
        await cache.aset(self._key(credential_id), status.value, timeout=ttl)

    async def get(self, credential_id: str) -> IamCredentialStatus | None:
        value = await cache.aget(self._key(credential_id), default=None)
        try:
            return IamCredentialStatus(value) if value is not None else None
        except ValueError:
            return IamCredentialStatus.INVALID

    @classmethod
    def _key(cls, credential_id: str) -> str:
        digest = hashlib.sha256(credential_id.encode("utf-8")).hexdigest()
        return f"{cls._PREFIX}{digest}"


__all__ = ("DjangoRuntimeCredentialStatusStore",)
