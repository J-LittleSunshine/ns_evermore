# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import (
    Any,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from ns_backend.iam.models import IamUser


@dataclass(slots=True, kw_only=True)
class AuthLoginResult:
    user: "IamUser"
    data: dict[str, Any]


@dataclass(slots=True, kw_only=True)
class TokenRotationResult:
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    session_id: str | None


@dataclass(slots=True, kw_only=True)
class TokenRotationOutcome:
    status: str
    result: TokenRotationResult | None = None
