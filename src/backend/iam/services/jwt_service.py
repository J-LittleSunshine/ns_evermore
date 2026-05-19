# -*- coding: utf-8 -*-
from __future__ import annotations
import base64
import hashlib
import hmac
import json
import uuid

from typing import TYPE_CHECKING
from datetime import datetime, timedelta, timezone
from typing import Any

from ns_backend import settings

if TYPE_CHECKING:
    pass


class JwtService:
    ALGORITHM = "HS256"

    SECRET_KEY = settings.SECRET_KEY

    ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

    @classmethod
    def create_access_token(cls, user_id: int, user_type: str) -> tuple[str, str]:
        now = cls._utc_now()
        jti = cls._new_jti()

        payload = {
            "uid": user_id,
            "utp": user_type,
            "typ": "access",
            "jti": jti,
            "iat": int(now.timestamp()),
            "exp": int(
                (now + timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()
            ),
        }

        return cls._encode(payload), jti

    @classmethod
    def create_refresh_token(cls, user_id: int) -> tuple[str, str, datetime]:
        now = cls._utc_now()
        jti = cls._new_jti()
        expired_at = now + timedelta(days=cls.REFRESH_TOKEN_EXPIRE_DAYS)

        payload = {
            "uid": user_id,
            "typ": "refresh",
            "jti": jti,
            "iat": int(now.timestamp()),
            "exp": int(expired_at.timestamp()),
        }

        return cls._encode(payload), jti, expired_at

    @classmethod
    def decode_access_token(cls, token: str) -> dict[str, Any] | None:
        payload = cls._decode(token)

        if not payload:
            return None

        if payload.get("typ") != "access":
            return None

        return payload

    @classmethod
    def decode_refresh_token(cls, token: str) -> dict[str, Any] | None:
        payload = cls._decode(token)

        if not payload:
            return None

        if payload.get("typ") != "refresh":
            return None

        return payload

    @classmethod
    def _encode(cls, payload: dict[str, Any]) -> str:
        header = {
            "typ": "JWT",
            "alg": cls.ALGORITHM,
        }

        header_b64 = cls._base64url_encode_json(header)
        payload_b64 = cls._base64url_encode_json(payload)

        signing_input = f"{header_b64}.{payload_b64}"
        signature = cls._sign(signing_input)

        return f"{signing_input}.{signature}"

    @classmethod
    def _decode(cls, token: str) -> dict[str, Any] | None:
        try:
            header_b64, payload_b64, signature = token.split(".")
        except ValueError:
            return None

        signing_input = f"{header_b64}.{payload_b64}"
        expected_signature = cls._sign(signing_input)

        if not hmac.compare_digest(signature, expected_signature):
            return None

        try:
            header = cls._base64url_decode_json(header_b64)
            payload = cls._base64url_decode_json(payload_b64)
        except Exception:  # noqa
            return None

        if header.get("alg") != cls.ALGORITHM:
            return None

        exp = payload.get("exp")
        if not isinstance(exp, int):
            return None

        if exp <= int(cls._utc_now().timestamp()):
            return None

        return payload

    @classmethod
    def _sign(cls, signing_input: str) -> str:
        digest = hmac.new(cls.SECRET_KEY.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256).digest()

        return cls._base64url_encode_bytes(digest)

    @staticmethod
    def _base64url_encode_json(data: dict[str, Any]) -> str:
        raw = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

        return JwtService._base64url_encode_bytes(raw)

    @staticmethod
    def _base64url_encode_bytes(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

    @staticmethod
    def _base64url_decode_json(data: str) -> dict[str, Any]:
        padding = "=" * (-len(data) % 4)
        raw = base64.urlsafe_b64decode((data + padding).encode("utf-8"))
        return json.loads(raw.decode("utf-8"))

    @staticmethod
    def _new_jti() -> str:
        return uuid.uuid4().hex

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)
