# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from cryptography.hazmat.primitives import (
    hashes,
    serialization
)
from cryptography.hazmat.primitives.asymmetric import padding
from django.conf import settings

from ns_backend.iam.errors import (
    IamPasswordEmptyError,
    IamPasswordTransportConfigError,
    IamPasswordTransportDecryptFailedError,
    IamPasswordTransportInvalidError,
)

if TYPE_CHECKING:
    pass


class PasswordTransportService:
    MODE_PLAIN = "plain"
    MODE_RSA_OAEP = "rsa_oaep"

    @classmethod
    def resolve(cls, password_payload: str) -> str:
        cls._validate_payload(password_payload)

        mode = cls.get_mode()
        if mode == cls.MODE_PLAIN:
            raw_password = password_payload
        elif mode == cls.MODE_RSA_OAEP:
            raw_password = cls.decrypt_rsa_oaep(password_payload)
        else:
            raise IamPasswordTransportConfigError(
                details={
                    "mode": mode,
                },
            )

        cls._validate_raw_password(raw_password)

        return raw_password

    @classmethod
    def validate_payload_basic(cls, password_payload: str) -> None:
        cls._validate_payload(password_payload)

    @classmethod
    def get_mode(cls) -> str:
        return str(getattr(settings, "PASSWORD_TRANSPORT_MODE", cls.MODE_PLAIN) or cls.MODE_PLAIN).strip().lower()

    @classmethod
    def _validate_payload(cls, password_payload: str) -> None:
        if not isinstance(password_payload, str) or not password_payload:
            raise IamPasswordEmptyError()

        max_length = cls._get_positive_int_setting("PASSWORD_TRANSPORT_MAX_PAYLOAD_LENGTH", 4096)
        if len(password_payload) > max_length:
            raise IamPasswordTransportInvalidError(
                details={
                    "max_length": max_length,
                },
            )

    @classmethod
    def _validate_raw_password(cls, raw_password: str) -> None:
        if not isinstance(raw_password, str) or not raw_password:
            raise IamPasswordEmptyError()

        max_length = cls._get_positive_int_setting("PASSWORD_PLAINTEXT_MAX_LENGTH", 256)
        if len(raw_password) > max_length:
            raise IamPasswordTransportInvalidError(
                details={
                    "max_length": max_length,
                },
            )

    @staticmethod
    def _get_positive_int_setting(setting_name: str, default: int) -> int:
        value = getattr(settings, setting_name, default)

        if isinstance(value, bool):
            return default

        if isinstance(value, int):
            return value if value > 0 else default

        if isinstance(value, str):
            text = value.strip()
            if not text:
                return default

            try:
                parsed = int(text)
            except (TypeError, ValueError):
                return default

            return parsed if parsed > 0 else default

        return default

    @classmethod
    def decrypt_rsa_oaep(cls, password_payload: str) -> str:
        try:
            ciphertext = base64.b64decode(password_payload, validate=True)
        except Exception as exc:
            raise IamPasswordTransportInvalidError() from exc

        try:
            plaintext = cls._load_private_key().decrypt(
                ciphertext,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            return plaintext.decode("utf-8")
        except IamPasswordTransportConfigError:
            raise
        except Exception as exc:
            raise IamPasswordTransportDecryptFailedError() from exc

    @classmethod
    @lru_cache(maxsize=1)
    def _load_private_key(cls):
        key_data = cls._load_private_key_bytes()
        passphrase = str(getattr(settings, "PASSWORD_RSA_PRIVATE_KEY_PASSPHRASE", "") or "")
        password = passphrase.encode("utf-8") if passphrase else None

        try:
            return serialization.load_pem_private_key(
                key_data,
                password=password,
            )
        except Exception as exc:
            raise IamPasswordTransportConfigError(
                details={
                    "source": "private_key",
                },
            ) from exc

    @staticmethod
    def _load_private_key_bytes() -> bytes:
        inline_key = str(getattr(settings, "PASSWORD_RSA_PRIVATE_KEY", "") or "")
        if inline_key:
            return inline_key.replace("\\n", "\n").encode("utf-8")

        key_file = str(getattr(settings, "PASSWORD_RSA_PRIVATE_KEY_FILE", "") or "")
        if key_file:
            try:
                return Path(key_file).expanduser().read_bytes()
            except Exception as exc:
                raise IamPasswordTransportConfigError(
                    details={
                        "source": "private_key_file",
                        "path": key_file,
                    },
                ) from exc

        raise IamPasswordTransportConfigError(
            details={
                "source": "private_key",
            },
        )
