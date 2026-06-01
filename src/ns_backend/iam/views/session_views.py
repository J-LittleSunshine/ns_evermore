# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.services import SessionService
from ns_backend.iam.views import IamRequestViewSet

if TYPE_CHECKING:
    pass


class SessionViewSet(IamRequestViewSet):
    audit_resource_type = "iam_user_session"

    async def list_sessions(self, request, *args, **kwargs):
        user = request.current_user
        access_token = self.get_bearer_token_from_request(request)
        data = await SessionService.list_current_user_sessions(user=user, access_token=access_token)
        return self.success_response(data)

    async def revoke_session(self, request, *args, **kwargs):
        user = request.current_user
        session_id = str(request.data.get("session_id", "")).strip()
        data = await SessionService.revoke_current_user_session(user=user, session_id=session_id)
        return self.success_response(data)
