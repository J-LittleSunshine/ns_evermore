# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping

from ..metadata import NsConfigGroupMetadata
from ..primitives import FrozenDict, _freeze_config_value


@dataclass(frozen=True, slots=True, kw_only=True)
class NsBackendConfig:
    debug: bool = True
    secret_key: str = "change-me-secret-key-at-least-32-chars"
    allowed_hosts: tuple[str, ...] = field(
        default_factory=lambda: (
            "127.0.0.1",
            "localhost",
        )
    )

    language_code: str = "zh-hans"
    time_zone: str = "Asia/Shanghai"
    use_i18n: bool = True
    use_tz: bool = True
    static_url: str = "static/"

    databases: Mapping[str, Mapping[str, Any]] = field(default_factory=FrozenDict)
    database_router_map: Mapping[str, str] = field(default_factory=FrozenDict)
    installed_apps: tuple[str, ...] = field(
        default_factory=lambda: (
            "iam",
        )
    )

    jwt_secret_key: str = ""
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14
    jwt_issuer: str = "ns_evermore"
    jwt_leeway_seconds: int = 30
    jwt_min_secret_length: int = 32

    password_transport_mode: Literal["plain", "rsa_oaep"] = "plain"
    password_transport_max_payload_length: int = 4096
    password_plaintext_max_length: int = 256
    password_rsa_private_key: str = ""
    password_rsa_private_key_file: str = ""
    password_rsa_private_key_passphrase: str = ""
    iam_internal_token: str = "change-me-iam-internal-token-at-least-32-chars"
    iam_decision_audit_enabled: bool = True
    iam_decision_audit_strict_mode: bool = False
    iam_operation_audit_enabled: bool = True
    iam_operation_audit_strict_mode: bool = False

    iam_auth_backoff_enabled: bool = True
    iam_auth_backoff_max_retries: int = 3
    iam_auth_backoff_base_delay_ms: int = 50
    iam_auth_backoff_max_delay_ms: int = 1000
    iam_auth_backoff_jitter_ratio: float = 0.5

    iam_cache_enabled: bool = True
    iam_cache_ttl_seconds: int = 300
    iam_user_cache_ttl_seconds: int = 120
    iam_authz_cache_ttl_seconds: int = 300
    metadata: NsConfigGroupMetadata = field(default_factory=NsConfigGroupMetadata)

    def __post_init__(self) -> None:
        object.__setattr__(self, "allowed_hosts", _freeze_config_value(self.allowed_hosts))
        object.__setattr__(self, "databases", _freeze_config_value(self.databases))
        object.__setattr__(self, "database_router_map", _freeze_config_value(self.database_router_map))
        object.__setattr__(self, "installed_apps", _freeze_config_value(self.installed_apps))
