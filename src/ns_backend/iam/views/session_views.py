# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.services import SessionService
from ns_backend.iam.views import IamRequestViewSet

if TYPE_CHECKING:
    pass


class SessionViewSet(IamRequestViewSet):
    async def list_sessions(self, request, *args, **kwargs):
        user = request.current_user
        data = await SessionService.list_current_user_sessions(user_id=user.id)
        return self.success_response(data)

    async def revoke_session(self, request, *args, **kwargs):
        user = request.current_user
        session_id = str(request.data.get("session_id", "")).strip()
        await SessionService.revoke_current_user_session(user_id=user.id, session_id=session_id)
        return self.success_response()
