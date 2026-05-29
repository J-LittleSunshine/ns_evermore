# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils import timezone

from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.models import IamUserSession, IamUserToken
from ns_backend.iam.views import IamRequestViewSet
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


class SessionViewSet(IamRequestViewSet):
    async def list_sessions(self, request, *args, **kwargs):
        user = request.current_user

        items = []
        async for s in IamUserSession.objects.filter(user_id=user.id).order_by("-id").aiterator():
            items.append(
                {
                    "session_id": s.session_id,
                    "device_id": s.device_id,
                    "login_ip": s.login_ip,
                    "user_agent": s.user_agent,
                    "last_active_at": s.last_active_at.isoformat() if s.last_active_at else None,
                    "expired_at": s.expired_at.isoformat() if s.expired_at else None,
                    "revoked_at": s.revoked_at.isoformat() if s.revoked_at else None,
                }
            )
        return self.success_response({"items": items})

    async def revoke_session(self, request, *args, **kwargs):
        user = request.current_user

        session_id = str(request.data.get("session_id", "")).strip()
        if not session_id:
            raise BusinessError("session_id cannot be empty", NsErrorCode.SESSION_ID_EMPTY)

        session = await IamUserSession.objects.filter(user_id=user.id, session_id=session_id).afirst()
        if not session:
            raise BusinessError("session not found", NsErrorCode.SESSION_NOT_FOUND)

        now = timezone.now()
        session.revoked_at = now
        await session.asave(update_fields=["revoked_at"])
        await IamUserToken.objects.filter(session_id=session.id, revoked_at__isnull=True).aupdate(revoked_at=now)
        return self.success_response()
