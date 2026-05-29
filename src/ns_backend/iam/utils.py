# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import secrets
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

def sha256_text(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_access_token(user_id: int, access_jti: str) -> str:
    return f"{user_id}.{access_jti}.{secrets.token_urlsafe(16)}"


def parse_access_token(access_token: str) -> tuple[int, str] | None:
    if not access_token:
        return None

    parts = str(access_token).split(".")
    if len(parts) < 2:
        return None

    user_id_text = parts[0].strip()
    access_jti = parts[1].strip()

    try:
        user_id = int(user_id_text)
    except (TypeError, ValueError):
        return None

    if user_id <= 0 or not access_jti:
        return None

    return user_id, access_jti


def get_bearer_token_from_request(request) -> str | None:
    headers = getattr(request, "headers", None)
    if headers is None:
        return None

    authorization = str(headers.get("Authorization", "")).strip()
    if not authorization.startswith("Bearer "):
        return None

    token = authorization.removeprefix("Bearer ").strip()
    return token or None
