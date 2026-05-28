# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from django.conf import settings

from ns_common.error_codes import NsErrorCode
from ns_backend.exceptions import BusinessError


class PasswordTransportService:
    """Resolve inbound password payloads into raw passwords for server-side hashing.

    Production default is ``plain``: HTTPS protects the transport, and Django
    ``make_password`` / ``check_password`` protects storage.

    Optional ``rsa_oaep`` mode is a compliance transport wrapper only. The
    decrypted plaintext is still passed into Django's password hasher; RSA
    ciphertext is never stored or compared as a password-equivalent secret.
    """

    MODE_PLAIN = "plain"
    MODE_RSA_OAEP = "rsa_oaep"

    @classmethod
    def resolve(cls, password_payload: str) -> str:
        """Return the raw password according to configured transport mode."""
        cls._validate_payload(password_payload)

        mode = cls.get_mode()
        if mode == cls.MODE_PLAIN:
            raw_password = password_payload
        elif mode == cls.MODE_RSA_OAEP:
            raw_password = cls.decrypt_rsa_oaep(password_payload)
        else:
            raise BusinessError(
                "password transport mode is invalid",
                NsErrorCode.PASSWORD_TRANSPORT_CONFIG_INVALID,
            )

        cls._validate_raw_password(raw_password)
        return raw_password

    @classmethod
    def validate_payload_basic(cls, password_payload: str) -> None:
        """Validate password payload shape/length without decrypting."""
        cls._validate_payload(password_payload)

    @classmethod
    def get_mode(cls) -> str:
        return str(getattr(settings, "PASSWORD_TRANSPORT_MODE", cls.MODE_PLAIN) or cls.MODE_PLAIN).strip().lower()

    @classmethod
    def _validate_payload(cls, password_payload: str) -> None:
        if not isinstance(password_payload, str) or not password_payload:
            raise BusinessError("password cannot be empty", NsErrorCode.PASSWORD_EMPTY)

        max_length = cls._get_positive_int_setting("PASSWORD_TRANSPORT_MAX_PAYLOAD_LENGTH", 4096)
        if len(password_payload) > max_length:
            raise BusinessError(
                "password payload is invalid",
                NsErrorCode.PASSWORD_TRANSPORT_INVALID,
            )

    @classmethod
    def _validate_raw_password(cls, raw_password: str) -> None:
        if not isinstance(raw_password, str) or not raw_password:
            raise BusinessError("password cannot be empty", NsErrorCode.PASSWORD_EMPTY)

        max_length = cls._get_positive_int_setting("PASSWORD_PLAINTEXT_MAX_LENGTH", 256)
        if len(raw_password) > max_length:
            raise BusinessError(
                "password is invalid",
                NsErrorCode.PASSWORD_TRANSPORT_INVALID,
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
        """Decrypt a base64 RSA-OAEP-SHA256 password payload."""
        try:
            ciphertext = base64.b64decode(password_payload, validate=True)
        except Exception as exc:  # noqa
            raise BusinessError(
                "password payload is invalid",
                NsErrorCode.PASSWORD_TRANSPORT_INVALID,
            ) from exc

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
        except BusinessError:
            raise
        except Exception as exc:  # noqa
            raise BusinessError(
                "password decrypt failed",
                NsErrorCode.PASSWORD_TRANSPORT_DECRYPT_FAILED,
            ) from exc

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
        except Exception as exc:  # noqa
            raise BusinessError(
                "password transport private key is invalid",
                NsErrorCode.PASSWORD_TRANSPORT_CONFIG_INVALID,
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
            except Exception as exc:  # noqa
                raise BusinessError(
                    "password transport private key file is invalid",
                    NsErrorCode.PASSWORD_TRANSPORT_CONFIG_INVALID,
                ) from exc

        raise BusinessError(
            "password transport private key is not configured",
            NsErrorCode.PASSWORD_TRANSPORT_CONFIG_INVALID,
        )


__all__ = ["PasswordTransportService"]
