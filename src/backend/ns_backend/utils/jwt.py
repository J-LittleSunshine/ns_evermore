# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from django.conf import settings
from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import OctKey


class JwtService:
    """JWT 基础设施服务。"""

    ALGORITHM = "HS256"
    TOKEN_TYPE = "JWT"
    ACCESS_TYPE = "access"
    REFRESH_TYPE = "refresh"

    SECRET_KEY = settings.JWT_SECRET_KEY

    ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
    ISSUER = settings.JWT_ISSUER
    LEEWAY_SECONDS = settings.JWT_LEEWAY_SECONDS
    MIN_SECRET_LENGTH = settings.JWT_MIN_SECRET_LENGTH

    @classmethod
    def create_access_token(
        cls,
        user_id: int,
        user_type: str,
        access_jti: str | None = None,
    ) -> tuple[str, str]:
        now = cls._utc_now()
        jti = access_jti or cls._new_jti()

        payload = {
            "uid": user_id,
            "sub": str(user_id),
            "utp": user_type,
            "iss": cls.ISSUER,
            "typ": cls.ACCESS_TYPE,
            "jti": jti,
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int(
                (now + timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()
            ),
        }

        return cls._encode(payload), jti

    @classmethod
    def create_access_jti(cls) -> str:
        return cls._new_jti()

    @classmethod
    def create_refresh_token(cls, user_id: int) -> tuple[str, str, str, datetime]:
        now = cls._utc_now()
        jti = cls._new_jti()
        expired_at = now + timedelta(days=cls.REFRESH_TOKEN_EXPIRE_DAYS)

        payload = {
            "uid": user_id,
            "sub": str(user_id),
            "iss": cls.ISSUER,
            "typ": cls.REFRESH_TYPE,
            "jti": jti,
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int(expired_at.timestamp()),
        }

        raw_token = cls._encode(payload)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

        return raw_token, token_hash, jti, expired_at

    @classmethod
    def decode_access_token(cls, token: str) -> dict[str, Any] | None:
        payload = cls._decode(token, expected_type=cls.ACCESS_TYPE)

        if not payload:
            return None

        if not payload.get("utp"):
            return None

        return payload

    @classmethod
    def decode_refresh_token(cls, token: str) -> dict[str, Any] | None:
        return cls._decode(token, expected_type=cls.REFRESH_TYPE)

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    def _encode(cls, payload: dict[str, Any]) -> str:
        cls._validate_secret_key()

        header = {
            "typ": cls.TOKEN_TYPE,
            "alg": cls.ALGORITHM,
        }

        return jwt.encode(
            header,
            payload,
            cls._get_key(),
            algorithms=[cls.ALGORITHM],
        )

    @classmethod
    def _decode(cls, token: str, expected_type: str) -> dict[str, Any] | None:
        cls._validate_secret_key()

        if not isinstance(token, str) or len(token) > 4096:
            return None

        try:
            token_obj = jwt.decode(
                token,
                cls._get_key(),
                algorithms=[cls.ALGORITHM],
            )
        except JoseError:
            return None

        header = token_obj.header

        if header.get("typ") != cls.TOKEN_TYPE:
            return None

        if header.get("alg") != cls.ALGORITHM:
            return None

        payload = dict(token_obj.claims)

        if payload.get("iss") != cls.ISSUER:
            return None

        if payload.get("typ") != expected_type:
            return None

        try:
            cls._claims_registry().validate(payload)
        except JoseError:
            return None

        if not cls._validate_registered_claims(payload):
            return None

        if not cls._validate_subject_claims(payload):
            return None

        return payload

    @staticmethod
    def _new_jti() -> str:
        return uuid.uuid4().hex

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @classmethod
    def _validate_secret_key(cls) -> None:
        if not isinstance(cls.SECRET_KEY, str) or not cls.SECRET_KEY:
            raise RuntimeError("jwt_secret_key is not set")

        if not settings.DEBUG and len(cls.SECRET_KEY.encode("utf-8")) < cls.MIN_SECRET_LENGTH:
            raise RuntimeError(
                f"jwt_secret_key must be at least {cls.MIN_SECRET_LENGTH} bytes when DEBUG is false"
            )

    @classmethod
    def _validate_registered_claims(cls, payload: dict[str, Any]) -> bool:
        now = int(cls._utc_now().timestamp())
        leeway = int(cls.LEEWAY_SECONDS)

        exp = payload.get("exp")
        iat = payload.get("iat")
        nbf = payload.get("nbf")

        if not all(isinstance(value, int) for value in (exp, iat, nbf)):
            return False

        if exp <= now - leeway:
            return False

        if nbf > now + leeway:
            return False

        if iat > now + leeway:
            return False

        return True

    @classmethod
    def _get_key(cls):
        return OctKey.import_key(cls.SECRET_KEY)

    @classmethod
    def _claims_registry(cls):
        return jwt.JWTClaimsRegistry(
            iss={"essential": True, "value": cls.ISSUER},
            sub={"essential": True},
            exp={"essential": True},
            nbf={"essential": True},
            iat={"essential": True},
            jti={"essential": True},
        )

    @staticmethod
    def _validate_subject_claims(payload: dict[str, Any]) -> bool:
        user_id = payload.get("uid")
        subject = payload.get("sub")
        jti = payload.get("jti")

        if not isinstance(user_id, int) or user_id <= 0:
            return False

        if subject != str(user_id):
            return False

        if not isinstance(jti, str) or len(jti) != 32:
            return False

        try:
            uuid.UUID(hex=jti)
        except ValueError:
            return False

        return True

