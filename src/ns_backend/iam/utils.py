# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rest_framework.request import Request


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_bearer_token_from_request(request: "Request") -> str | None:
    authorization = str(request.headers.get("Authorization", "") or "").strip()

    if not authorization:
        return None

    parts = authorization.split(None, 1)
    if len(parts) != 2:
        return None

    scheme, token = parts
    if scheme.lower() != "bearer":
        return None

    token = token.strip()
    return token or None
