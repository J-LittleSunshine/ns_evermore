# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.services.session_context import SessionContextService
from iam.views.base import IamRequestViewSet


class SessionViewSet(IamRequestViewSet):
    audit_resource_type = "iam_user_session"
    authentication_required = True

    async def list_item(self, request, *args, **kwargs):
        user = request.current_user
        if not user:
            return self.failed_response("User is not logged in or session has expired", 11007)

        access_token = self.get_bearer_token_from_request(request)
        items = await SessionContextService.list_sessions(
            user=user,
            access_token=access_token,
        )

        return self.success_response({
            "items": items,
        })

    async def revoke(self, request, *args, **kwargs):
        user = request.current_user
        if not user:
            return self.failed_response("User is not logged in or session has expired", 11007)

        session_id = request.data.get("session_id")
        if not isinstance(session_id, str) or not session_id.strip():
            return self.failed_response("session_id cannot be empty", 15001)

        data = await SessionContextService.revoke_session(
            user=user,
            session_id=session_id.strip(),
        )

        return self.success_response(data)


__all__ = ["SessionViewSet"]

