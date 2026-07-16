# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import json
import os
import re
import tempfile
import types
from collections.abc import Mapping as MappingABC
from dataclasses import (
    MISSING,
    dataclass,
    field,
    fields,
    is_dataclass,
    replace,
)
from datetime import (
    datetime,
    timezone,
)
from enum import Enum
from pathlib import Path
from threading import RLock
from typing import (
    Any,
    get_args,
    get_origin,
    get_type_hints,
    Iterator,
    Literal,
    Mapping,
    TYPE_CHECKING,
    Union,
)
from urllib.parse import urlparse

from ns_common.exceptions import (
    NsConfigError,
    NsDependencyError,
)
from ns_common.paths import (
    ETC_DIR,
    ensure_runtime_dirs
)

if TYPE_CHECKING:
    pass

_ALLOWED_ENVIRONMENTS = {
    "local",
    "dev",
    "test",
    "prod",
}
_CONFIG_VERSION_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}")


class FrozenDict(MappingABC[str, Any]):
    """A read-only mapping used by deeply immutable config snapshots."""

    __slots__ = ("_values",)

    def __init__(self, values: Mapping[str, Any] | None = None) -> None:
        object.__setattr__(self, "_values", types.MappingProxyType(dict(values or {})))

    def __getitem__(self, key: str) -> Any:
        return self._values[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def __repr__(self) -> str:
        return f"FrozenDict({dict(self._values)!r})"

    def __setattr__(self, name: str, value: Any) -> None:
        del name, value
        raise TypeError("configuration snapshots are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise TypeError("configuration snapshots are immutable")

    def __copy__(self) -> "FrozenDict":
        return self

    def __deepcopy__(self, memo: dict[int, Any]) -> "FrozenDict":
        del memo
        return self


def _freeze_config_value(value: Any) -> Any:
    if isinstance(value, FrozenDict):
        return value

    if isinstance(value, MappingABC):
        return FrozenDict({
            key: _freeze_config_value(item)
            for key, item in value.items()
        })

    if isinstance(value, (list, tuple)):
        return tuple(_freeze_config_value(item) for item in value)

    return value


def _to_json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value

    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _to_json_value(getattr(value, item.name))
            for item in fields(value)
        }

    if isinstance(value, MappingABC):
        return {
            str(key): _to_json_value(item)
            for key, item in value.items()
        }

    if isinstance(value, tuple):
        return [_to_json_value(item) for item in value]

    return value


def _value_matches_type(value: Any, expected_type: Any) -> bool:
    if expected_type is Any:
        return True

    origin = get_origin(expected_type)
    arguments = get_args(expected_type)

    if origin is Literal:
        return any(
            value == item and type(value) is type(item)
            for item in arguments
        )

    if origin in {types.UnionType, Union}:
        return any(_value_matches_type(value, item) for item in arguments)

    if origin is tuple:
        if not isinstance(value, tuple):
            return False

        if len(arguments) == 2 and arguments[1] is Ellipsis:
            return all(_value_matches_type(item, arguments[0]) for item in value)

        return len(value) == len(arguments) and all(
            _value_matches_type(item, item_type)
            for item, item_type in zip(value, arguments)
        )

    if origin in {dict, MappingABC}:
        if not isinstance(value, MappingABC):
            return False

        if not arguments:
            return True

        key_type, item_type = arguments
        return all(
            _value_matches_type(key, key_type)
            and _value_matches_type(item, item_type)
            for key, item in value.items()
        )

    if origin is list:
        return isinstance(value, list) and (
            not arguments
            or all(_value_matches_type(item, arguments[0]) for item in value)
        )

    if expected_type is bool:
        return type(value) is bool

    if expected_type is int:
        return type(value) is int

    if expected_type is float:
        return not isinstance(value, bool) and isinstance(value, (int, float))

    if expected_type is None or expected_type is type(None):
        return value is None

    try:
        return isinstance(value, expected_type)
    except TypeError:
        return False


def _validate_dataclass_types(instance: Any, *, path: str = "") -> None:
    type_hints = get_type_hints(type(instance))

    for item in fields(instance):
        value = getattr(instance, item.name)
        field_path = f"{path}.{item.name}" if path else item.name
        expected_type = type_hints.get(item.name, Any)

        if not _value_matches_type(value, expected_type):
            raise NsConfigError(
                f"{field_path} has an invalid type.",
                details={
                    "field": field_path,
                    "actual_type": type(value).__name__,
                    "expected_type": str(expected_type),
                },
            )

        if is_dataclass(value) and not isinstance(value, type):
            _validate_dataclass_types(value, path=field_path)


def get_ns_env() -> str:
    env = os.getenv("NS_ENV", "local").strip().lower()

    if env not in _ALLOWED_ENVIRONMENTS:
        return "local"

    return env


NS_ENV = get_ns_env()


def get_default_config_path(environment: str | None = None) -> Path:
    selected_environment = (environment or get_ns_env()).strip().lower()
    if selected_environment not in _ALLOWED_ENVIRONMENTS:
        selected_environment = "local"

    return ETC_DIR / f"ns_config.{selected_environment}.json"


NS_CONFIG_FILE_PATH = get_default_config_path()


class NsConfigSource(str, Enum):
    LOCAL_FILE = "local_file"
    BACKEND_OVERRIDE = "backend_override"
    VALIDATED_SNAPSHOT = "validated_snapshot"


NS_CONFIG_SOURCE_PRIORITY: Mapping[NsConfigSource, int] = types.MappingProxyType({
    NsConfigSource.LOCAL_FILE: 10,
    NsConfigSource.BACKEND_OVERRIDE: 20,
    NsConfigSource.VALIDATED_SNAPSHOT: 30,
})


@dataclass(frozen=True, slots=True, kw_only=True)
class NsConfigGroupMetadata:
    source: NsConfigSource = NsConfigSource.LOCAL_FILE
    config_version: str = "0"
    policy_version: str = "0"
    group_version: str = "0"
    effective_at: str | None = None
    rollback_from_version: str | None = None
    apply_mode: Literal["immediate", "rolling", "restart_required"] = "restart_required"

    def __post_init__(self) -> None:
        if isinstance(self.source, NsConfigSource):
            return

        try:
            source = NsConfigSource(self.source)
        except (TypeError, ValueError) as error:
            raise NsConfigError(
                "config metadata source is invalid.",
                details={
                    "field": "metadata.source",
                    "value": self.source,
                    "allowed_values": [item.value for item in NsConfigSource],
                },
            ) from error

        object.__setattr__(self, "source", source)


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


@dataclass(frozen=True, slots=True, kw_only=True)
class NsCacheConfig:
    backend: Literal["sqlite", "redis", "valkey", "dummy"] = "sqlite"

    key_prefix: str = "ns_evermore"

    django_namespace: str = "ns_backend"

    cache_url: str = ""

    default_ttl_seconds: int = 300

    none_ttl_means_forever: bool = False

    sqlite_path: str = "data/ns_cache.sqlite3"

    sqlite_busy_timeout_ms: int = 5000
    sqlite_write_max_retries: int = 3
    sqlite_write_retry_base_delay_ms: int = 50
    sqlite_write_retry_max_delay_ms: int = 500

    cleanup_interval_seconds: int = 300
    cleanup_batch_size: int = 500
    metadata: NsConfigGroupMetadata = field(default_factory=NsConfigGroupMetadata)


@dataclass(frozen=True, slots=True, kw_only=True)
class NsLogConfig:
    level: str = "INFO"
    file_level: str = "INFO"
    console_level: str = "INFO"
    console: bool = True

    format_type: Literal["json", "text", "color_text"] = "json"
    console_format_type: Literal["json", "text", "color_text"] | None = "color_text"
    file_format_type: Literal["json", "text"] | None = "json"

    format: str = (
        "%(asctime)s - %(levelname)-8s - %(process)d:%(threadName)s - "
        "%(name)s - %(filename)s:%(lineno)d - %(message)s"
    )
    datefmt: str = "%Y-%m-%d %H:%M:%S"

    when: str = "midnight"
    interval: int = 1
    backup_count: int = 14
    encoding: str = "utf-8"
    delay: bool = True
    utc: bool = False
    at_time: str | None = None
    max_bytes: int = 0
    use_gzip: bool = False
    lock_file_directory: str | None = None

    level_files: tuple[str, ...] = (
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    )
    metadata: NsConfigGroupMetadata = field(default_factory=NsConfigGroupMetadata)

    def __post_init__(self) -> None:
        object.__setattr__(self, "level_files", _freeze_config_value(self.level_files))


@dataclass(frozen=True, slots=True, kw_only=True)
class NsRuntimeEventLoopConfig:
    implementation: Literal["auto", "asyncio", "uvloop"] = "auto"
    debug: bool = False
    slow_callback_threshold_ms: int = 100
    metadata: NsConfigGroupMetadata = field(
        default_factory=lambda: NsConfigGroupMetadata(apply_mode="restart_required")
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class NsRuntimeTransportAdapterConfig:
    enabled: bool = False
    tls_enabled: bool = True
    allowed_origins: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "allowed_origins", _freeze_config_value(self.allowed_origins))


def _default_websocket_tcp_adapter() -> NsRuntimeTransportAdapterConfig:
    return NsRuntimeTransportAdapterConfig(enabled=True, tls_enabled=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class NsRuntimeTransportConfig:
    websocket_tcp: NsRuntimeTransportAdapterConfig = field(default_factory=_default_websocket_tcp_adapter)
    websocket_http3: NsRuntimeTransportAdapterConfig = field(default_factory=NsRuntimeTransportAdapterConfig)
    webtransport_http3: NsRuntimeTransportAdapterConfig = field(default_factory=NsRuntimeTransportAdapterConfig)
    quic_native: NsRuntimeTransportAdapterConfig = field(default_factory=NsRuntimeTransportAdapterConfig)
    default_adapter: Literal[
        "websocket_tcp",
        "websocket_http3",
        "webtransport_http3",
        "quic_native",
    ] = "websocket_tcp"
    preferred_adapter: Literal[
        "websocket_tcp",
        "websocket_http3",
        "webtransport_http3",
        "quic_native",
    ] = "websocket_tcp"
    fallback_order: tuple[
        Literal[
            "websocket_tcp",
            "websocket_http3",
            "webtransport_http3",
            "quic_native",
        ],
        ...,
    ] = ("websocket_tcp",)
    capability_negotiation_enabled: bool = True
    listen_host: str = "127.0.0.1"
    listen_port: int = 8765
    write_queue_capacity: int = 1024
    write_queue_low_watermark: int = 256
    write_queue_high_watermark: int = 768
    path_migration_enabled: bool = False
    datagram_enabled: bool = False
    zero_rtt_enabled: bool = False
    message_type_allowlist: tuple[str, ...] = ()
    metadata: NsConfigGroupMetadata = field(
        default_factory=lambda: NsConfigGroupMetadata(apply_mode="restart_required")
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "fallback_order", _freeze_config_value(self.fallback_order))
        object.__setattr__(self, "message_type_allowlist", _freeze_config_value(self.message_type_allowlist))

    def adapters(self) -> tuple[tuple[str, NsRuntimeTransportAdapterConfig], ...]:
        return (
            ("websocket_tcp", self.websocket_tcp),
            ("websocket_http3", self.websocket_http3),
            ("webtransport_http3", self.webtransport_http3),
            ("quic_native", self.quic_native),
        )

    @property
    def enabled_adapters(self) -> tuple[str, ...]:
        return tuple(name for name, adapter in self.adapters() if adapter.enabled)


@dataclass(frozen=True, slots=True, kw_only=True)
class NsRuntimeWireCodecConfig:
    supported: tuple[Literal["json.v1"], ...] = ("json.v1",)
    preferred: Literal["json.v1"] = "json.v1"
    metadata: NsConfigGroupMetadata = field(
        default_factory=lambda: NsConfigGroupMetadata(apply_mode="restart_required")
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "supported", _freeze_config_value(self.supported))


@dataclass(frozen=True, slots=True, kw_only=True)
class NsRuntimeProtocolConfig:
    supported_versions: tuple[str, ...] = ("1.0",)
    preferred_version: str = "1.0"
    handshake_timeout_seconds: int = 10
    max_envelope_bytes: int = 1_048_576
    metadata: NsConfigGroupMetadata = field(
        default_factory=lambda: NsConfigGroupMetadata(apply_mode="rolling")
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "supported_versions", _freeze_config_value(self.supported_versions))


@dataclass(frozen=True, slots=True, kw_only=True)
class NsRuntimeSecurityConfig:
    require_tls_in_prod: bool = True
    allow_plaintext_non_prod: bool = True
    allow_zero_rtt: bool = False
    reject_inbound_source: bool = True
    reject_inbound_auth_context: bool = True
    metadata: NsConfigGroupMetadata = field(
        default_factory=lambda: NsConfigGroupMetadata(apply_mode="restart_required")
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class NsRuntimeIamConfig:
    base_url: str = "http://127.0.0.1:8000/api/iam/"
    request_timeout_seconds: int = 5
    credential_refresh_interval_seconds: int = 300
    permission_snapshot_ttl_seconds: int = 60
    fail_closed: bool = True
    allow_degraded_startup: bool = False
    metadata: NsConfigGroupMetadata = field(
        default_factory=lambda: NsConfigGroupMetadata(apply_mode="rolling")
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class NsRuntimeStateStoreConfig:
    backend: Literal["sqlite", "redis", "valkey"] = "sqlite"
    url: str = ""
    namespace: str = "ns_runtime"
    sqlite_path: str = "data/ns_runtime_state.sqlite3"
    operation_timeout_seconds: int = 5
    metadata: NsConfigGroupMetadata = field(
        default_factory=lambda: NsConfigGroupMetadata(apply_mode="restart_required")
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class NsRuntimeRoutingConfig:
    no_target_action: Literal["reroute", "queue", "reject", "dead_letter", "degrade", "hybrid"] = "queue"
    max_hops: int = 8
    route_cache_ttl_seconds: int = 30
    allow_cross_node: bool = False
    metadata: NsConfigGroupMetadata = field(
        default_factory=lambda: NsConfigGroupMetadata(apply_mode="immediate")
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class NsRuntimeDeliveryConfig:
    ack_timeout_seconds: int = 30
    max_retry_attempts: int = 5
    retry_base_delay_ms: int = 100
    retry_max_delay_ms: int = 30_000
    persist_delivery_records: bool = True
    metadata: NsConfigGroupMetadata = field(
        default_factory=lambda: NsConfigGroupMetadata(apply_mode="rolling")
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class NsRuntimeWorkerConfig:
    concurrency: int = 32
    shutdown_timeout_seconds: int = 30
    processor_timeout_seconds: int = 30
    metadata: NsConfigGroupMetadata = field(
        default_factory=lambda: NsConfigGroupMetadata(apply_mode="rolling")
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class NsRuntimePoolConfig:
    control_capacity: int = 8
    delivery_capacity: int = 64
    stream_capacity: int = 32
    observability_capacity: int = 4
    metadata: NsConfigGroupMetadata = field(
        default_factory=lambda: NsConfigGroupMetadata(apply_mode="rolling")
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class NsRuntimeTenantQuotaConfig:
    enabled: bool = True
    max_connections: int = 1000
    max_queued_deliveries: int = 10_000
    max_inflight_deliveries: int = 1000
    messages_per_second: int = 1000
    metadata: NsConfigGroupMetadata = field(
        default_factory=lambda: NsConfigGroupMetadata(apply_mode="immediate")
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class NsRuntimeClusterConfig:
    role: Literal["standalone", "master", "sub_node"] = "standalone"
    node_id: str = "local-runtime"
    active_master_url: str = ""
    heartbeat_interval_seconds: int = 5
    leader_lease_seconds: int = 15
    metadata: NsConfigGroupMetadata = field(
        default_factory=lambda: NsConfigGroupMetadata(apply_mode="restart_required")
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class NsRuntimeRecoveryConfig:
    enabled: bool = True
    scan_interval_seconds: int = 30
    scan_batch_size: int = 1000
    stale_after_seconds: int = 60
    metadata: NsConfigGroupMetadata = field(
        default_factory=lambda: NsConfigGroupMetadata(apply_mode="rolling")
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class NsRuntimeObservabilityConfig:
    metrics_enabled: bool = True
    tracing_enabled: bool = False
    diagnostic_snapshots_enabled: bool = True
    trace_sample_ratio: float = 0.0
    export_interval_seconds: int = 15
    metadata: NsConfigGroupMetadata = field(
        default_factory=lambda: NsConfigGroupMetadata(apply_mode="immediate")
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class NsRuntimeLoggingConfig:
    level: str = "INFO"
    structured: bool = True
    include_sanitized_envelope: bool = False
    metadata: NsConfigGroupMetadata = field(
        default_factory=lambda: NsConfigGroupMetadata(apply_mode="immediate")
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class NsRuntimeDebugConfig:
    enabled: bool = False
    emit_sanitized_envelope: bool = False
    fault_injection_enabled: bool = False
    metadata: NsConfigGroupMetadata = field(
        default_factory=lambda: NsConfigGroupMetadata(apply_mode="immediate")
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class NsRuntimeConfig:
    event_loop: NsRuntimeEventLoopConfig = field(default_factory=NsRuntimeEventLoopConfig)
    transport: NsRuntimeTransportConfig = field(default_factory=NsRuntimeTransportConfig)
    wire_codec: NsRuntimeWireCodecConfig = field(default_factory=NsRuntimeWireCodecConfig)
    protocol: NsRuntimeProtocolConfig = field(default_factory=NsRuntimeProtocolConfig)
    security: NsRuntimeSecurityConfig = field(default_factory=NsRuntimeSecurityConfig)
    iam: NsRuntimeIamConfig = field(default_factory=NsRuntimeIamConfig)
    state_store: NsRuntimeStateStoreConfig = field(default_factory=NsRuntimeStateStoreConfig)
    routing: NsRuntimeRoutingConfig = field(default_factory=NsRuntimeRoutingConfig)
    delivery: NsRuntimeDeliveryConfig = field(default_factory=NsRuntimeDeliveryConfig)
    worker: NsRuntimeWorkerConfig = field(default_factory=NsRuntimeWorkerConfig)
    pool: NsRuntimePoolConfig = field(default_factory=NsRuntimePoolConfig)
    tenant_quota: NsRuntimeTenantQuotaConfig = field(default_factory=NsRuntimeTenantQuotaConfig)
    cluster: NsRuntimeClusterConfig = field(default_factory=NsRuntimeClusterConfig)
    recovery: NsRuntimeRecoveryConfig = field(default_factory=NsRuntimeRecoveryConfig)
    observability: NsRuntimeObservabilityConfig = field(default_factory=NsRuntimeObservabilityConfig)
    logging: NsRuntimeLoggingConfig = field(default_factory=NsRuntimeLoggingConfig)
    debug: NsRuntimeDebugConfig = field(default_factory=NsRuntimeDebugConfig)
    metadata: NsConfigGroupMetadata = field(default_factory=NsConfigGroupMetadata)


RUNTIME_CONFIG_GROUP_NAMES: tuple[str, ...] = (
    "event_loop",
    "transport",
    "wire_codec",
    "protocol",
    "security",
    "iam",
    "state_store",
    "routing",
    "delivery",
    "worker",
    "pool",
    "tenant_quota",
    "cluster",
    "recovery",
    "observability",
    "logging",
    "debug",
)

RUNTIME_CONFIG_APPLY_MODES: Mapping[str, str] = types.MappingProxyType({
    "event_loop": "restart_required",
    "transport": "restart_required",
    "wire_codec": "restart_required",
    "protocol": "rolling",
    "security": "restart_required",
    "iam": "rolling",
    "state_store": "restart_required",
    "routing": "immediate",
    "delivery": "rolling",
    "worker": "rolling",
    "pool": "rolling",
    "tenant_quota": "immediate",
    "cluster": "restart_required",
    "recovery": "rolling",
    "observability": "immediate",
    "logging": "immediate",
    "debug": "immediate",
})


@dataclass(frozen=True, slots=True, kw_only=True)
class NsConfig:
    backend: NsBackendConfig = field(default_factory=NsBackendConfig)
    cache: NsCacheConfig = field(default_factory=NsCacheConfig)
    log: NsLogConfig = field(default_factory=NsLogConfig)
    runtime: NsRuntimeConfig = field(default_factory=NsRuntimeConfig)

    _lock = RLock()

    @classmethod
    def load(
        cls,
        config_path: str | Path | None = None,
        *,
        environment: str | None = None,
        backend_override: Mapping[str, Any] | None = None,
        validated_snapshot: "NsConfig" | None = None,
        effective_at: datetime | str | None = None,
    ) -> "NsConfig":
        resolved_environment = cls._resolve_environment(environment)
        if config_path is None:
            ensure_runtime_dirs()
            path = get_default_config_path(resolved_environment)
        else:
            path = Path(config_path).resolve()

        with cls._lock:
            raw_config = cls._load_json_config(path)
            return cls.resolve(
                raw_config,
                environment=resolved_environment,
                backend_override=backend_override,
                validated_snapshot=validated_snapshot,
                effective_at=effective_at,
            )

    @classmethod
    def resolve(
        cls,
        local_config: Mapping[str, Any],
        *,
        environment: str | None = None,
        backend_override: Mapping[str, Any] | None = None,
        validated_snapshot: "NsConfig" | None = None,
        effective_at: datetime | str | None = None,
    ) -> "NsConfig":
        resolver = NsConfigResolver(
            config_type=cls,
            environment=environment,
            effective_at=effective_at,
        )
        return resolver.resolve(
            local_config,
            backend_override=backend_override,
            validated_snapshot=validated_snapshot,
        )

    @classmethod
    def from_dict(cls, raw_config: Mapping[str, Any], *, environment: str | None = None) -> "NsConfig":
        resolved_environment = cls._resolve_environment(environment)
        if not isinstance(raw_config, MappingABC):
            raise NsConfigError(
                "Config root must be a mapping.",
                details={
                    "field": "config",
                    "actual_type": type(raw_config).__name__,
                },
            )

        allowed_top_level_fields = {
            "backend",
            "backend_config",
            "cache",
            "cache_config",
            "log",
            "log_config",
            "runtime",
            "runtime_config",
        }
        cls._reject_unknown_fields(
            raw_config,
            allowed_fields=allowed_top_level_fields,
            path="config",
        )

        backend_raw = cls._get_section(raw_config, preferred_key="backend", compatible_key="backend_config")
        cache_raw = cls._get_section(raw_config, preferred_key="cache", compatible_key="cache_config")
        log_raw = cls._get_section(raw_config, preferred_key="log", compatible_key="log_config")
        runtime_raw = cls._get_section(raw_config, preferred_key="runtime", compatible_key="runtime_config")

        if "cache" in backend_raw:
            raise NsConfigError(
                "backend.cache is deprecated. Move cache config to top-level cache.",
                details={
                    "field": "backend.cache",
                    "expected_field": "cache",
                },
            )

        config = cls(
            backend=cls._build_config_group(NsBackendConfig, backend_raw, path="backend"),
            cache=cls._build_config_group(NsCacheConfig, cache_raw, path="cache"),
            log=cls._build_config_group(NsLogConfig, log_raw, path="log"),
            runtime=cls._build_config_group(NsRuntimeConfig, runtime_raw, path="runtime"),
        )
        config.validate(environment=resolved_environment)
        return config

    def save(self, config_path: str | Path | None = None, *, environment: str | None = None) -> None:
        resolved_environment = self._resolve_environment(environment)
        if config_path is None:
            ensure_runtime_dirs()
            path = get_default_config_path(resolved_environment)
        else:
            path = Path(config_path).resolve()

        with self.__class__._lock:
            self.validate(environment=resolved_environment)
            self.__class__._atomic_write_json(path, self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return _to_json_value(self)

    def as_validated_snapshot(self, *, effective_at: datetime | str | None = None, environment: str | None = None) -> "NsConfig":
        timestamp = self._normalize_effective_at(
            effective_at or datetime.now(timezone.utc),
            field_name="effective_at",
            allow_none=False,
        )
        runtime_group_updates = {
            group_name: replace(
                group_config,
                metadata=replace(
                    group_config.metadata,
                    source=NsConfigSource.VALIDATED_SNAPSHOT,
                    effective_at=timestamp,
                ),
            )
            for group_name, group_config in self._runtime_config_groups(self.runtime)
        }
        runtime_snapshot = replace(
            self.runtime,
            **runtime_group_updates,
            metadata=replace(
                self.runtime.metadata,
                source=NsConfigSource.VALIDATED_SNAPSHOT,
                effective_at=timestamp,
            ),
        )
        snapshot = replace(
            self,
            backend=replace(
                self.backend,
                metadata=replace(
                    self.backend.metadata,
                    source=NsConfigSource.VALIDATED_SNAPSHOT,
                    effective_at=timestamp,
                ),
            ),
            cache=replace(
                self.cache,
                metadata=replace(
                    self.cache.metadata,
                    source=NsConfigSource.VALIDATED_SNAPSHOT,
                    effective_at=timestamp,
                ),
            ),
            log=replace(
                self.log,
                metadata=replace(
                    self.log.metadata,
                    source=NsConfigSource.VALIDATED_SNAPSHOT,
                    effective_at=timestamp,
                ),
            ),
            runtime=runtime_snapshot,
        )
        snapshot.validate(environment=environment)
        self._get_consistent_metadata_value(snapshot, "config_version")
        self._get_consistent_metadata_value(snapshot, "policy_version")
        return snapshot

    @property
    def backend_config(self) -> NsBackendConfig:
        return self.backend

    @property
    def cache_config(self) -> NsCacheConfig:
        return self.cache

    @property
    def log_config(self) -> NsLogConfig:
        return self.log

    @property
    def runtime_config(self) -> NsRuntimeConfig:
        return self.runtime

    @property
    def config_version(self) -> str:
        return self._get_consistent_metadata_value(self, "config_version")

    @property
    def policy_version(self) -> str:
        return self._get_consistent_metadata_value(self, "policy_version")

    def validate(self, *, environment: str | None = None) -> None:
        resolved_environment = self._resolve_environment(environment)
        _validate_dataclass_types(self)

        if self.backend.debug and resolved_environment == "prod":
            raise NsConfigError("backend.debug must be False when NS_ENV is prod.",
                details={
                    "field": "backend.debug",
                    "env": resolved_environment,
                },
            )

        if not self.backend.secret_key.strip():
            raise NsConfigError("backend.secret_key must not be empty.",
                details={
                    "field": "backend.secret_key",
                },
            )

        if resolved_environment == "prod" and self.backend.secret_key.startswith("change-me-"):
            raise NsConfigError("backend.secret_key must be changed in prod.",
                details={
                    "field": "backend.secret_key",
                    "env": resolved_environment,
                },
            )

        if not isinstance(self.backend.allowed_hosts, tuple):
            raise NsConfigError("backend.allowed_hosts must be a sequence.",
                details={
                    "field": "backend.allowed_hosts",
                    "actual_type": type(self.backend.allowed_hosts).__name__,
                },
            )

        if not isinstance(self.backend.databases, MappingABC):
            raise NsConfigError("backend.databases must be a mapping.",
                details={
                    "field": "backend.databases",
                    "actual_type": type(self.backend.databases).__name__,
                },
            )

        if not isinstance(self.backend.database_router_map, MappingABC):
            raise NsConfigError("backend.database_router_map must be a mapping.",
                details={
                    "field": "backend.database_router_map",
                    "actual_type": type(self.backend.database_router_map).__name__,
                },
            )

        for app_label, db_alias in self.backend.database_router_map.items():
            if not isinstance(app_label, str) or not app_label.strip():
                raise NsConfigError("backend.database_router_map app label must be a non-empty string.",
                    details={
                        "field": "backend.database_router_map",
                        "app_label": app_label,
                    },
                )

            if not isinstance(db_alias, str) or not db_alias.strip():
                raise NsConfigError("backend.database_router_map database alias must be a non-empty string.",
                    details={
                        "field": "backend.database_router_map",
                        "app_label": app_label,
                        "db_alias": db_alias,
                    },
                )

        self._validate_positive_int("backend.access_token_expire_minutes", self.backend.access_token_expire_minutes)
        self._validate_positive_int("backend.refresh_token_expire_days", self.backend.refresh_token_expire_days)
        self._validate_positive_int("backend.jwt_leeway_seconds", self.backend.jwt_leeway_seconds)
        self._validate_positive_int("backend.jwt_min_secret_length", self.backend.jwt_min_secret_length)
        self._validate_positive_int("backend.password_transport_max_payload_length", self.backend.password_transport_max_payload_length)
        self._validate_positive_int("backend.password_plaintext_max_length", self.backend.password_plaintext_max_length)
        self._validate_bool("backend.iam_auth_backoff_enabled", self.backend.iam_auth_backoff_enabled)
        self._validate_non_negative_int("backend.iam_auth_backoff_max_retries", self.backend.iam_auth_backoff_max_retries)
        self._validate_non_negative_int("backend.iam_auth_backoff_base_delay_ms", self.backend.iam_auth_backoff_base_delay_ms)
        self._validate_non_negative_int("backend.iam_auth_backoff_max_delay_ms", self.backend.iam_auth_backoff_max_delay_ms)
        self._validate_float_range("backend.iam_auth_backoff_jitter_ratio", self.backend.iam_auth_backoff_jitter_ratio, min_value=0.0, max_value=1.0)

        self._validate_bool("backend.iam_cache_enabled", self.backend.iam_cache_enabled)
        self._validate_positive_int("backend.iam_cache_ttl_seconds", self.backend.iam_cache_ttl_seconds)
        self._validate_positive_int("backend.iam_user_cache_ttl_seconds", self.backend.iam_user_cache_ttl_seconds)
        self._validate_positive_int("backend.iam_authz_cache_ttl_seconds", self.backend.iam_authz_cache_ttl_seconds)

        if self.backend.password_transport_mode not in {"plain", "rsa_oaep"}:
            raise NsConfigError("backend.password_transport_mode is invalid.",
                details={
                    "field": "backend.password_transport_mode",
                    "value": self.backend.password_transport_mode,
                    "allowed_values": [
                        "plain",
                        "rsa_oaep",
                    ],
                },
            )

        if not isinstance(self.backend.installed_apps, tuple):
            raise NsConfigError(
                "backend.installed_apps must be a sequence.",
                details={
                    "field": "backend.installed_apps",
                    "actual_type": type(self.backend.installed_apps).__name__,
                },
            )

        seen_installed_apps: set[str] = set()

        for app_key in self.backend.installed_apps:
            if not isinstance(app_key, str) or not app_key.strip():
                raise NsConfigError(
                    "backend.installed_apps item must be a non-empty string.",
                    details={
                        "field": "backend.installed_apps",
                        "value": app_key,
                    },
                )

            normalized_app_key = app_key.strip()

            if normalized_app_key in seen_installed_apps:
                raise NsConfigError(
                    "backend.installed_apps contains duplicated item.",
                    details={
                        "field": "backend.installed_apps",
                        "value": normalized_app_key,
                    },
                )

            seen_installed_apps.add(normalized_app_key)

        for group_name, group_config in self._config_groups(self):
            self._validate_group_metadata(group_name, group_config.metadata)

        for group_name, group_config in self._runtime_config_groups(self.runtime):
            self._validate_group_metadata(f"runtime.{group_name}", group_config.metadata)

        self._validate_cache_config()
        self._validate_runtime_config(resolved_environment)

    @staticmethod
    def _config_groups(config: "NsConfig") -> tuple[tuple[str, Any], ...]:
        return (
            ("backend", config.backend),
            ("cache", config.cache),
            ("log", config.log),
            ("runtime", config.runtime),
        )

    @staticmethod
    def _runtime_config_groups(runtime: NsRuntimeConfig) -> tuple[tuple[str, Any], ...]:
        return tuple(
            (group_name, getattr(runtime, group_name))
            for group_name in RUNTIME_CONFIG_GROUP_NAMES
        )

    @classmethod
    def _validate_group_metadata(cls, group_name: str, metadata: NsConfigGroupMetadata) -> None:
        for field_name in (
            "config_version",
            "policy_version",
            "group_version",
        ):
            value = getattr(metadata, field_name)
            if _CONFIG_VERSION_PATTERN.fullmatch(value) is None:
                raise NsConfigError(
                    f"{group_name}.metadata.{field_name} is invalid.",
                    details={
                        "field": f"{group_name}.metadata.{field_name}",
                        "value": value,
                        "allowed_pattern": _CONFIG_VERSION_PATTERN.pattern,
                    },
                )

        if metadata.rollback_from_version is not None and _CONFIG_VERSION_PATTERN.fullmatch(metadata.rollback_from_version) is None:
            raise NsConfigError(
                f"{group_name}.metadata.rollback_from_version is invalid.",
                details={
                    "field": f"{group_name}.metadata.rollback_from_version",
                    "value": metadata.rollback_from_version,
                    "allowed_pattern": _CONFIG_VERSION_PATTERN.pattern,
                },
            )

        if metadata.effective_at is not None:
            cls._normalize_effective_at(
                metadata.effective_at,
                field_name=f"{group_name}.metadata.effective_at",
                allow_none=False,
            )

    @staticmethod
    def _normalize_effective_at(value: datetime | str | None, *, field_name: str, allow_none: bool) -> str | None:
        if value is None:
            if allow_none:
                return None

            raise NsConfigError(
                f"{field_name} is required.",
                details={
                    "field": field_name,
                },
            )

        parsed: datetime
        if isinstance(value, datetime):
            parsed = value
        elif isinstance(value, str) and value.strip():
            text = value.strip()
            if text.endswith("Z"):
                text = f"{text[:-1]}+00:00"

            try:
                parsed = datetime.fromisoformat(text)
            except ValueError as error:
                raise NsConfigError(
                    f"{field_name} must be an ISO-8601 timestamp.",
                    details={
                        "field": field_name,
                        "value": value,
                    },
                ) from error
        else:
            raise NsConfigError(
                f"{field_name} must be an ISO-8601 timestamp.",
                details={
                    "field": field_name,
                    "value": value,
                    "actual_type": type(value).__name__,
                },
            )

        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise NsConfigError(
                f"{field_name} must include a timezone.",
                details={
                    "field": field_name,
                    "value": value,
                },
            )

        return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    @classmethod
    def _get_consistent_metadata_value(cls, config: "NsConfig", field_name: str) -> str:
        values = {
            getattr(group_config.metadata, field_name)
            for _, group_config in cls._config_groups(config)
        }
        if len(values) != 1:
            raise NsConfigError(
                f"config metadata {field_name} is inconsistent across groups.",
                details={
                    "field": f"metadata.{field_name}",
                    "values": sorted(values),
                },
            )

        return next(iter(values))

    def _validate_cache_config(self) -> None:
        cache = self.cache

        if not isinstance(cache, NsCacheConfig):
            raise NsConfigError(
                "cache must be NsCacheConfig.",
                details={
                    "field": "cache",
                    "actual_type": type(cache).__name__,
                },
            )

        if cache.backend not in {
            "sqlite",
            "redis",
            "valkey",
            "dummy",
        }:
            raise NsConfigError(
                "cache.backend is invalid.",
                details={
                    "field": "cache.backend",
                    "value": cache.backend,
                    "allowed_values": [
                        "sqlite",
                        "redis",
                        "valkey",
                        "dummy",
                    ],
                },
            )

        self._validate_cache_key_part("cache.key_prefix", cache.key_prefix)
        self._validate_cache_key_part("cache.django_namespace", cache.django_namespace)

        self._validate_positive_int("cache.default_ttl_seconds", cache.default_ttl_seconds)
        self._validate_bool("cache.none_ttl_means_forever", cache.none_ttl_means_forever)
        self._validate_positive_int("cache.sqlite_busy_timeout_ms", cache.sqlite_busy_timeout_ms)
        self._validate_non_negative_int("cache.sqlite_write_max_retries", cache.sqlite_write_max_retries)
        self._validate_non_negative_int("cache.sqlite_write_retry_base_delay_ms", cache.sqlite_write_retry_base_delay_ms)
        self._validate_non_negative_int("cache.sqlite_write_retry_max_delay_ms", cache.sqlite_write_retry_max_delay_ms)
        self._validate_positive_int("cache.cleanup_interval_seconds", cache.cleanup_interval_seconds)
        self._validate_positive_int("cache.cleanup_batch_size", cache.cleanup_batch_size)

        if cache.backend == "redis":
            self._validate_cache_url(
                field_name="cache.cache_url",
                cache_url=cache.cache_url,
                allowed_schemes={
                    "redis",
                    "rediss",
                },
            )
            self._validate_python_dependency(
                field_name="cache.backend",
                package_name="redis",
            )

        if cache.backend == "valkey":
            self._validate_cache_url(
                field_name="cache.cache_url",
                cache_url=cache.cache_url,
                allowed_schemes={
                    "redis",
                    "rediss",
                    "valkey",
                    "valkeys",
                },
            )
            self._validate_python_dependency(
                field_name="cache.backend",
                package_name="valkey",
            )

    def _validate_runtime_config(self, environment: str) -> None:
        runtime = self.runtime

        for group_name, group_config in self._runtime_config_groups(runtime):
            expected_apply_mode = RUNTIME_CONFIG_APPLY_MODES[group_name]
            if group_config.metadata.apply_mode != expected_apply_mode:
                raise NsConfigError(
                    f"runtime.{group_name}.metadata.apply_mode is invalid for this group.",
                    details={
                        "field": f"runtime.{group_name}.metadata.apply_mode",
                        "value": group_config.metadata.apply_mode,
                        "expected": expected_apply_mode,
                    },
                )

            for version_field in ("config_version", "policy_version"):
                value = getattr(group_config.metadata, version_field)
                expected = getattr(runtime.metadata, version_field)
                if value != expected:
                    raise NsConfigError(
                        f"runtime.{group_name}.metadata.{version_field} is inconsistent with runtime metadata.",
                        details={
                            "field": f"runtime.{group_name}.metadata.{version_field}",
                            "value": value,
                            "expected": expected,
                        },
                    )

        event_loop = runtime.event_loop
        if event_loop.implementation not in {"auto", "asyncio", "uvloop"}:
            self._raise_invalid_choice(
                "runtime.event_loop.implementation",
                event_loop.implementation,
                {"auto", "asyncio", "uvloop"},
            )
        self._validate_positive_int(
            "runtime.event_loop.slow_callback_threshold_ms",
            event_loop.slow_callback_threshold_ms,
        )

        transport = runtime.transport
        adapter_names = {name for name, _ in transport.adapters()}
        enabled_adapters = set(transport.enabled_adapters)
        if not enabled_adapters:
            raise NsConfigError(
                "runtime.transport must enable at least one adapter.",
                details={"field": "runtime.transport"},
            )

        for adapter_name, adapter in transport.adapters():
            for origin in adapter.allowed_origins:
                self._validate_non_empty_string(
                    f"runtime.transport.{adapter_name}.allowed_origins",
                    origin,
                )

            if environment == "prod" and adapter.enabled and not adapter.tls_enabled:
                raise NsConfigError(
                    "enabled production transports must use encrypted transport.",
                    details={
                        "field": f"runtime.transport.{adapter_name}.tls_enabled",
                        "env": environment,
                    },
                )

        for field_name, adapter_name in (
            ("default_adapter", transport.default_adapter),
            ("preferred_adapter", transport.preferred_adapter),
        ):
            if adapter_name not in enabled_adapters:
                raise NsConfigError(
                    f"runtime.transport.{field_name} must reference an enabled adapter.",
                    details={
                        "field": f"runtime.transport.{field_name}",
                        "value": adapter_name,
                        "enabled_adapters": sorted(enabled_adapters),
                    },
                )

        self._validate_unique_choices(
            "runtime.transport.fallback_order",
            transport.fallback_order,
            adapter_names,
        )
        disabled_fallbacks = sorted(set(transport.fallback_order).difference(enabled_adapters))
        if disabled_fallbacks:
            raise NsConfigError(
                "runtime.transport.fallback_order contains disabled adapters.",
                details={
                    "field": "runtime.transport.fallback_order",
                    "disabled_adapters": disabled_fallbacks,
                },
            )

        self._validate_non_empty_string("runtime.transport.listen_host", transport.listen_host)
        self._validate_port("runtime.transport.listen_port", transport.listen_port)
        self._validate_positive_int("runtime.transport.write_queue_capacity", transport.write_queue_capacity)
        self._validate_non_negative_int(
            "runtime.transport.write_queue_low_watermark",
            transport.write_queue_low_watermark,
        )
        self._validate_positive_int(
            "runtime.transport.write_queue_high_watermark",
            transport.write_queue_high_watermark,
        )
        if not (
            transport.write_queue_low_watermark
            < transport.write_queue_high_watermark
            <= transport.write_queue_capacity
        ):
            raise NsConfigError(
                "runtime.transport queue watermarks are invalid.",
                details={
                    "field": "runtime.transport.write_queue_low_watermark",
                    "low": transport.write_queue_low_watermark,
                    "high": transport.write_queue_high_watermark,
                    "capacity": transport.write_queue_capacity,
                },
            )

        self._validate_unique_non_empty_strings(
            "runtime.transport.message_type_allowlist",
            transport.message_type_allowlist,
            allow_empty=True,
        )
        migration_capable = {"websocket_http3", "webtransport_http3", "quic_native"}
        datagram_capable = {"webtransport_http3", "quic_native"}
        if transport.path_migration_enabled and not enabled_adapters.intersection(migration_capable):
            raise NsConfigError(
                "path migration requires an enabled HTTP/3, WebTransport, or QUIC adapter.",
                details={"field": "runtime.transport.path_migration_enabled"},
            )
        if transport.datagram_enabled and not enabled_adapters.intersection(datagram_capable):
            raise NsConfigError(
                "datagrams require an enabled WebTransport or native QUIC adapter.",
                details={"field": "runtime.transport.datagram_enabled"},
            )
        if transport.zero_rtt_enabled:
            if not enabled_adapters.intersection(migration_capable):
                raise NsConfigError(
                    "0-RTT requires an enabled HTTP/3, WebTransport, or QUIC adapter.",
                    details={"field": "runtime.transport.zero_rtt_enabled"},
                )
            if not runtime.security.allow_zero_rtt:
                raise NsConfigError(
                    "0-RTT must also be allowed by runtime.security.",
                    details={
                        "field": "runtime.security.allow_zero_rtt",
                        "required_by": "runtime.transport.zero_rtt_enabled",
                    },
                )

        wire_codec = runtime.wire_codec
        if wire_codec.supported != ("json.v1",) or wire_codec.preferred != "json.v1":
            raise NsConfigError(
                "runtime.wire_codec currently supports only json.v1.",
                details={
                    "field": "runtime.wire_codec",
                    "supported": list(wire_codec.supported),
                    "preferred": wire_codec.preferred,
                },
            )

        protocol = runtime.protocol
        self._validate_unique_non_empty_strings(
            "runtime.protocol.supported_versions",
            protocol.supported_versions,
        )
        if protocol.preferred_version not in protocol.supported_versions:
            raise NsConfigError(
                "runtime.protocol.preferred_version must be supported.",
                details={
                    "field": "runtime.protocol.preferred_version",
                    "value": protocol.preferred_version,
                    "supported_versions": list(protocol.supported_versions),
                },
            )
        self._validate_positive_int("runtime.protocol.handshake_timeout_seconds", protocol.handshake_timeout_seconds)
        self._validate_positive_int("runtime.protocol.max_envelope_bytes", protocol.max_envelope_bytes)

        security = runtime.security
        if not security.require_tls_in_prod:
            raise NsConfigError(
                "runtime.security.require_tls_in_prod cannot be disabled.",
                details={"field": "runtime.security.require_tls_in_prod"},
            )
        if not security.reject_inbound_source or not security.reject_inbound_auth_context:
            raise NsConfigError(
                "runtime must reject inbound source and auth_context.",
                details={"field": "runtime.security"},
            )
        if environment != "prod" and not security.allow_plaintext_non_prod:
            plaintext_adapters = [
                name
                for name, adapter in transport.adapters()
                if adapter.enabled and not adapter.tls_enabled
            ]
            if plaintext_adapters:
                raise NsConfigError(
                    "plaintext transport is disabled by runtime.security.",
                    details={
                        "field": "runtime.security.allow_plaintext_non_prod",
                        "plaintext_adapters": plaintext_adapters,
                    },
                )

        iam = runtime.iam
        self._validate_http_url("runtime.iam.base_url", iam.base_url)
        self._validate_positive_int("runtime.iam.request_timeout_seconds", iam.request_timeout_seconds)
        self._validate_positive_int(
            "runtime.iam.credential_refresh_interval_seconds",
            iam.credential_refresh_interval_seconds,
        )
        self._validate_positive_int(
            "runtime.iam.permission_snapshot_ttl_seconds",
            iam.permission_snapshot_ttl_seconds,
        )

        state_store = runtime.state_store
        if environment == "prod" and state_store.backend not in {"redis", "valkey"}:
            raise NsConfigError(
                "runtime.state_store.backend must be redis or valkey in prod.",
                details={
                    "field": "runtime.state_store.backend",
                    "value": state_store.backend,
                    "env": environment,
                },
            )
        self._validate_cache_key_part("runtime.state_store.namespace", state_store.namespace)
        self._validate_positive_int(
            "runtime.state_store.operation_timeout_seconds",
            state_store.operation_timeout_seconds,
        )
        if state_store.backend == "sqlite":
            self._validate_non_empty_string("runtime.state_store.sqlite_path", state_store.sqlite_path)
        elif state_store.backend == "redis":
            self._validate_cache_url("runtime.state_store.url", state_store.url, {"redis", "rediss"})
        elif state_store.backend == "valkey":
            self._validate_cache_url(
                "runtime.state_store.url",
                state_store.url,
                {"redis", "rediss", "valkey", "valkeys"},
            )

        routing = runtime.routing
        self._validate_positive_int("runtime.routing.max_hops", routing.max_hops)
        self._validate_non_negative_int("runtime.routing.route_cache_ttl_seconds", routing.route_cache_ttl_seconds)

        delivery = runtime.delivery
        self._validate_positive_int("runtime.delivery.ack_timeout_seconds", delivery.ack_timeout_seconds)
        self._validate_non_negative_int("runtime.delivery.max_retry_attempts", delivery.max_retry_attempts)
        self._validate_non_negative_int("runtime.delivery.retry_base_delay_ms", delivery.retry_base_delay_ms)
        self._validate_non_negative_int("runtime.delivery.retry_max_delay_ms", delivery.retry_max_delay_ms)
        if delivery.retry_max_delay_ms < delivery.retry_base_delay_ms:
            raise NsConfigError(
                "runtime.delivery.retry_max_delay_ms must not be lower than retry_base_delay_ms.",
                details={"field": "runtime.delivery.retry_max_delay_ms"},
            )
        if not delivery.persist_delivery_records:
            raise NsConfigError(
                "runtime.delivery.persist_delivery_records cannot be disabled.",
                details={"field": "runtime.delivery.persist_delivery_records"},
            )

        worker = runtime.worker
        self._validate_positive_int("runtime.worker.concurrency", worker.concurrency)
        self._validate_positive_int("runtime.worker.shutdown_timeout_seconds", worker.shutdown_timeout_seconds)
        self._validate_positive_int("runtime.worker.processor_timeout_seconds", worker.processor_timeout_seconds)

        pool = runtime.pool
        for field_name in (
            "control_capacity",
            "delivery_capacity",
            "stream_capacity",
            "observability_capacity",
        ):
            self._validate_positive_int(f"runtime.pool.{field_name}", getattr(pool, field_name))

        tenant_quota = runtime.tenant_quota
        for field_name in (
            "max_connections",
            "max_queued_deliveries",
            "max_inflight_deliveries",
            "messages_per_second",
        ):
            self._validate_positive_int(
                f"runtime.tenant_quota.{field_name}",
                getattr(tenant_quota, field_name),
            )

        cluster = runtime.cluster
        self._validate_cache_key_part("runtime.cluster.node_id", cluster.node_id)
        self._validate_positive_int("runtime.cluster.heartbeat_interval_seconds", cluster.heartbeat_interval_seconds)
        self._validate_positive_int("runtime.cluster.leader_lease_seconds", cluster.leader_lease_seconds)
        if cluster.leader_lease_seconds <= cluster.heartbeat_interval_seconds:
            raise NsConfigError(
                "runtime.cluster.leader_lease_seconds must exceed heartbeat_interval_seconds.",
                details={"field": "runtime.cluster.leader_lease_seconds"},
            )
        if cluster.role == "sub_node":
            self._validate_http_url("runtime.cluster.active_master_url", cluster.active_master_url)

        recovery = runtime.recovery
        self._validate_positive_int("runtime.recovery.scan_interval_seconds", recovery.scan_interval_seconds)
        self._validate_positive_int("runtime.recovery.scan_batch_size", recovery.scan_batch_size)
        self._validate_positive_int("runtime.recovery.stale_after_seconds", recovery.stale_after_seconds)

        observability = runtime.observability
        self._validate_float_range(
            "runtime.observability.trace_sample_ratio",
            observability.trace_sample_ratio,
            min_value=0.0,
            max_value=1.0,
        )
        self._validate_positive_int(
            "runtime.observability.export_interval_seconds",
            observability.export_interval_seconds,
        )

        logging_config = runtime.logging
        normalized_level = logging_config.level.strip().upper()
        if normalized_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            self._raise_invalid_choice(
                "runtime.logging.level",
                logging_config.level,
                {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"},
            )

        debug = runtime.debug
        if debug.emit_sanitized_envelope and not debug.enabled:
            raise NsConfigError(
                "runtime.debug.emit_sanitized_envelope requires debug mode.",
                details={"field": "runtime.debug.emit_sanitized_envelope"},
            )
        if debug.fault_injection_enabled and not debug.enabled:
            raise NsConfigError(
                "runtime.debug.fault_injection_enabled requires debug mode.",
                details={"field": "runtime.debug.fault_injection_enabled"},
            )
        if environment == "prod" and debug.enabled:
            raise NsConfigError(
                "runtime.debug.enabled must be false in prod.",
                details={"field": "runtime.debug.enabled", "env": environment},
            )

    @staticmethod
    def _raise_invalid_choice(field_name: str, value: Any, allowed_values: set[str]) -> None:
        raise NsConfigError(
            f"{field_name} is invalid.",
            details={
                "field": field_name,
                "value": value,
                "allowed_values": sorted(allowed_values),
            },
        )

    @staticmethod
    def _validate_non_empty_string(field_name: str, value: Any) -> None:
        if not isinstance(value, str) or not value.strip():
            raise NsConfigError(
                f"{field_name} must be a non-empty string.",
                details={
                    "field": field_name,
                    "value": value,
                    "actual_type": type(value).__name__,
                },
            )

    @classmethod
    def _validate_unique_non_empty_strings(
        cls,
        field_name: str,
        values: tuple[str, ...],
        *,
        allow_empty: bool = False,
    ) -> None:
        if not values and not allow_empty:
            raise NsConfigError(
                f"{field_name} must not be empty.",
                details={"field": field_name},
            )

        seen: set[str] = set()
        for value in values:
            cls._validate_non_empty_string(field_name, value)
            if value in seen:
                raise NsConfigError(
                    f"{field_name} contains duplicate values.",
                    details={"field": field_name, "value": value},
                )
            seen.add(value)

    @classmethod
    def _validate_unique_choices(
        cls,
        field_name: str,
        values: tuple[str, ...],
        allowed_values: set[str],
    ) -> None:
        cls._validate_unique_non_empty_strings(field_name, values)
        invalid_values = sorted(set(values).difference(allowed_values))
        if invalid_values:
            raise NsConfigError(
                f"{field_name} contains invalid values.",
                details={
                    "field": field_name,
                    "invalid_values": invalid_values,
                    "allowed_values": sorted(allowed_values),
                },
            )

    @staticmethod
    def _validate_port(field_name: str, value: Any) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 65535:
            raise NsConfigError(
                f"{field_name} must be between 1 and 65535.",
                details={
                    "field": field_name,
                    "value": value,
                    "actual_type": type(value).__name__,
                },
            )

    @staticmethod
    def _validate_http_url(field_name: str, value: Any) -> None:
        if not isinstance(value, str) or not value.strip():
            raise NsConfigError(
                f"{field_name} must be configured.",
                details={"field": field_name, "value": value},
            )
        parsed = urlparse(value.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise NsConfigError(
                f"{field_name} must be an HTTP(S) URL with a host.",
                details={"field": field_name, "value": value},
            )

    @staticmethod
    def _validate_cache_key_part(field_name: str, value: Any) -> None:
        if not isinstance(value, str) or not value.strip():
            raise NsConfigError(
                f"{field_name} must be a non-empty string.",
                details={
                    "field": field_name,
                    "value": value,
                    "actual_type": type(value).__name__,
                },
            )

        text = value.strip()
        if re.fullmatch(r"[a-zA-Z0-9_.:-]+", text) is None:
            raise NsConfigError(
                f"{field_name} contains invalid characters.",
                details={
                    "field": field_name,
                    "value": value,
                    "allowed_pattern": r"[a-zA-Z0-9_.:-]+",
                },
            )

    @staticmethod
    def _validate_cache_url(field_name: str, cache_url: Any, allowed_schemes: set[str]) -> None:
        if not isinstance(cache_url, str) or not cache_url.strip():
            raise NsConfigError(
                f"{field_name} must be configured.",
                details={
                    "field": field_name,
                    "value": cache_url,
                    "actual_type": type(cache_url).__name__,
                },
            )

        parsed = urlparse(cache_url.strip())
        if parsed.scheme not in allowed_schemes:
            raise NsConfigError(
                f"{field_name} scheme is invalid.",
                details={
                    "field": field_name,
                    "scheme": parsed.scheme,
                    "allowed_schemes": sorted(allowed_schemes),
                },
            )

        if not parsed.hostname:
            raise NsConfigError(
                f"{field_name} host is required.",
                details={
                    "field": field_name,
                    "value": cache_url,
                },
            )

    @staticmethod
    def _validate_python_dependency(field_name: str, package_name: str) -> None:
        if importlib.util.find_spec(package_name) is None:
            raise NsDependencyError(
                f"Python package '{package_name}' is required.",
                details={
                    "field": field_name,
                    "package": package_name,
                },
            )

    @staticmethod
    def _validate_positive_int(field_name: str, value: Any) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise NsConfigError(f"{field_name} must be a positive integer.",
                details={
                    "field": field_name,
                    "value": value,
                    "actual_type": type(value).__name__,
                },
            )

    @staticmethod
    def _validate_bool(field_name: str, value: Any) -> None:
        if not isinstance(value, bool):
            raise NsConfigError(f"{field_name} must be a boolean.",
                details={
                    "field": field_name,
                    "value": value,
                    "actual_type": type(value).__name__,
                },
            )

    @staticmethod
    def _validate_non_negative_int(field_name: str, value: Any) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise NsConfigError(f"{field_name} must be a non-negative integer.",
                details={
                    "field": field_name,
                    "value": value,
                    "actual_type": type(value).__name__,
                },
            )

    @staticmethod
    def _validate_float_range(field_name: str, value: Any, *, min_value: float, max_value: float) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise NsConfigError(f"{field_name} must be a number.",
                details={
                    "field": field_name,
                    "value": value,
                    "actual_type": type(value).__name__,
                },
            )

        parsed = float(value)
        if parsed < min_value or parsed > max_value:
            raise NsConfigError(f"{field_name} must be between {min_value} and {max_value}.",
                details={
                    "field": field_name,
                    "value": value,
                    "min_value": min_value,
                    "max_value": max_value,
                },
            )

    @staticmethod
    def _resolve_environment(environment: str | None) -> str:
        if environment is None:
            return get_ns_env()

        if not isinstance(environment, str):
            raise NsConfigError(
                "environment must be a string.",
                details={
                    "field": "environment",
                    "actual_type": type(environment).__name__,
                },
            )

        normalized = environment.strip().lower()
        if normalized not in _ALLOWED_ENVIRONMENTS:
            raise NsConfigError(
                "environment is invalid.",
                details={
                    "field": "environment",
                    "value": environment,
                    "allowed_values": sorted(_ALLOWED_ENVIRONMENTS),
                },
            )

        return normalized

    @staticmethod
    def _reject_unknown_fields(raw_config: Mapping[str, Any], *, allowed_fields: set[str], path: str) -> None:
        unknown_fields = sorted(
            str(key)
            for key in raw_config
            if key not in allowed_fields
        )
        if unknown_fields:
            raise NsConfigError(
                f"{path} contains unknown fields.",
                details={
                    "field": path,
                    "unknown_fields": unknown_fields,
                    "allowed_fields": sorted(allowed_fields),
                },
            )

    @classmethod
    def _build_config_group(cls, group_type: type[Any], raw_group: Mapping[str, Any], *, path: str) -> Any:
        group_values = dict(raw_group)
        group_fields = {item.name: item for item in fields(group_type)}
        allowed_fields = set(group_fields)
        cls._reject_unknown_fields(
            group_values,
            allowed_fields=allowed_fields,
            path=path,
        )

        type_hints = get_type_hints(group_type)
        for field_name, raw_value in tuple(group_values.items()):
            if field_name == "metadata":
                continue

            expected_type = type_hints.get(field_name)
            if not isinstance(expected_type, type) or not is_dataclass(expected_type):
                continue

            if isinstance(raw_value, expected_type):
                continue

            if not isinstance(raw_value, MappingABC):
                raise NsConfigError(
                    f"{path}.{field_name} must be a JSON object.",
                    details={
                        "field": f"{path}.{field_name}",
                        "actual_type": type(raw_value).__name__,
                    },
                )

            nested_values: Mapping[str, Any] = raw_value
            group_field = group_fields[field_name]
            if group_field.default_factory is not MISSING:
                default_value = group_field.default_factory()
                if is_dataclass(default_value) and not isinstance(default_value, type):
                    nested_values = NsConfigResolver._deep_merge(
                        _to_json_value(default_value),
                        raw_value,
                    )

            group_values[field_name] = cls._build_config_group(
                expected_type,
                nested_values,
                path=f"{path}.{field_name}",
            )

        if "metadata" in group_values:
            group_values["metadata"] = cls._build_group_metadata(
                group_values["metadata"],
                path=f"{path}.metadata",
            )
        try:
            group = group_type(**group_values)
        except TypeError as error:
            raise NsConfigError(
                f"{path} is invalid.",
                details={
                    "field": path,
                    "reason": str(error),
                },
            ) from error

        if isinstance(group, NsRuntimeConfig):
            runtime_updates: dict[str, Any] = {}
            for runtime_group_name, runtime_group in cls._runtime_config_groups(group):
                raw_runtime_group = raw_group.get(runtime_group_name)
                has_explicit_metadata = (
                    isinstance(raw_runtime_group, MappingABC)
                    and "metadata" in raw_runtime_group
                )
                if has_explicit_metadata:
                    continue

                runtime_updates[runtime_group_name] = replace(
                    runtime_group,
                    metadata=replace(
                        runtime_group.metadata,
                        source=group.metadata.source,
                        config_version=group.metadata.config_version,
                        policy_version=group.metadata.policy_version,
                        effective_at=group.metadata.effective_at,
                    ),
                )

            if runtime_updates:
                group = replace(group, **runtime_updates)

        return group

    @classmethod
    def _build_group_metadata(cls, raw_metadata: Any, *, path: str) -> NsConfigGroupMetadata:
        if isinstance(raw_metadata, NsConfigGroupMetadata):
            return raw_metadata

        if not isinstance(raw_metadata, MappingABC):
            raise NsConfigError(
                f"{path} must be a JSON object.",
                details={
                    "field": path,
                    "actual_type": type(raw_metadata).__name__,
                },
            )

        metadata_values = dict(raw_metadata)
        metadata_fields = {item.name for item in fields(NsConfigGroupMetadata)}
        cls._reject_unknown_fields(
            metadata_values,
            allowed_fields=metadata_fields,
            path=path,
        )
        if "source" in metadata_values and not isinstance(metadata_values["source"], NsConfigSource):
            try:
                metadata_values["source"] = NsConfigSource(metadata_values["source"])
            except (TypeError, ValueError) as error:
                raise NsConfigError(
                    f"{path}.source is invalid.",
                    details={
                        "field": f"{path}.source",
                        "value": metadata_values["source"],
                        "allowed_values": [item.value for item in NsConfigSource],
                    },
                ) from error

        try:
            return NsConfigGroupMetadata(**metadata_values)
        except TypeError as error:
            raise NsConfigError(
                f"{path} is invalid.",
                details={
                    "field": path,
                    "reason": str(error),
                },
            ) from error

    @staticmethod
    def _get_section(raw_config: Mapping[str, Any], *, preferred_key: str, compatible_key: str) -> Mapping[str, Any]:
        has_preferred = preferred_key in raw_config
        has_compatible = compatible_key in raw_config

        if has_preferred and has_compatible:
            raise NsConfigError(
                f"Use only {preferred_key}; do not also provide {compatible_key}.",
                details={
                    "field": preferred_key,
                    "conflicting_field": compatible_key,
                },
            )

        if not has_preferred and not has_compatible:
            return {}

        selected_key = preferred_key if has_preferred else compatible_key
        section = raw_config[selected_key]
        if not isinstance(section, MappingABC):
            raise NsConfigError(
                f"{selected_key} must be a JSON object.",
                details={
                    "field": selected_key,
                    "actual_type": type(section).__name__,
                },
            )

        return section

    @staticmethod
    def _load_json_config(config_path: Path) -> dict[str, Any]:
        if not config_path.exists():
            return {}

        try:
            with config_path.open("r", encoding="utf-8") as file:
                raw_config = json.load(file)
        except json.JSONDecodeError as error:
            raise NsConfigError(f"Invalid JSON config file: {config_path}",
                details={
                    "config_path": str(config_path),
                    "line": error.lineno,
                    "column": error.colno,
                },
            ) from error

        if not isinstance(raw_config, dict):
            raise NsConfigError(f"Config root must be a JSON object: {config_path}",
                details={
                    "config_path": str(config_path),
                    "actual_type": type(raw_config).__name__,
                },
            )

        return raw_config

    @staticmethod
    def _atomic_write_json(config_path: Path, data: dict[str, Any]) -> None:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temp_name = tempfile.mkstemp(
            dir=config_path.parent,
            prefix=f".{config_path.name}.",
            suffix=".tmp",
            text=True,
        )
        temp_path = Path(temp_name)

        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())

            os.replace(temp_path, config_path)
        except BaseException:
            temp_path.unlink(missing_ok=True)
            raise


class NsConfigResolver:
    GROUP_NAMES: tuple[str, ...] = (
        "backend",
        "cache",
        "log",
        "runtime",
    )
    REQUIRED_OVERRIDE_METADATA_FIELDS: frozenset[str] = frozenset({
        "source",
        "config_version",
        "policy_version",
        "group_version",
        "effective_at",
        "rollback_from_version",
        "apply_mode",
    })

    def __init__(
        self,
        *,
        config_type: type[NsConfig] = NsConfig,
        environment: str | None = None,
        effective_at: datetime | str | None = None,
    ) -> None:
        self._config_type = config_type
        self._environment = config_type._resolve_environment(environment)
        self._effective_at = config_type._normalize_effective_at(
            effective_at or datetime.now(timezone.utc),
            field_name="effective_at",
            allow_none=False,
        )

    def resolve(
        self,
        local_config: Mapping[str, Any],
        *,
        backend_override: Mapping[str, Any] | None = None,
        validated_snapshot: NsConfig | None = None,
    ) -> NsConfig:
        effective_config = self._resolve_local_config(local_config)

        if backend_override is not None:
            effective_config = self._apply_backend_override(
                effective_config,
                backend_override,
            )

        if validated_snapshot is not None:
            effective_config = self._accept_validated_snapshot(validated_snapshot)

        return effective_config

    def _resolve_local_config(self, raw_config: Mapping[str, Any]) -> NsConfig:
        config = self._config_type.from_dict(
            raw_config,
            environment=self._environment,
        )
        group_updates: dict[str, Any] = {}

        for group_name, group_config in self._config_type._config_groups(config):
            metadata = group_config.metadata
            if metadata.source is not NsConfigSource.LOCAL_FILE:
                self._raise_source_mismatch(
                    layer="local config",
                    group_name=group_name,
                    expected=NsConfigSource.LOCAL_FILE,
                    actual=metadata.source,
                )

            timestamp = self._config_type._normalize_effective_at(
                metadata.effective_at or self._effective_at,
                field_name=f"{group_name}.metadata.effective_at",
                allow_none=False,
            )
            resolved_group = replace(
                group_config,
                metadata=replace(metadata, effective_at=timestamp),
            )
            if group_name == "runtime":
                runtime_updates: dict[str, Any] = {}
                for runtime_group_name, runtime_group in self._config_type._runtime_config_groups(group_config):
                    runtime_metadata = runtime_group.metadata
                    if runtime_metadata.source is not NsConfigSource.LOCAL_FILE:
                        self._raise_source_mismatch(
                            layer="local config",
                            group_name=f"runtime.{runtime_group_name}",
                            expected=NsConfigSource.LOCAL_FILE,
                            actual=runtime_metadata.source,
                        )
                    runtime_timestamp = self._config_type._normalize_effective_at(
                        runtime_metadata.effective_at or self._effective_at,
                        field_name=f"runtime.{runtime_group_name}.metadata.effective_at",
                        allow_none=False,
                    )
                    runtime_updates[runtime_group_name] = replace(
                        runtime_group,
                        metadata=replace(runtime_metadata, effective_at=runtime_timestamp),
                    )
                resolved_group = replace(resolved_group, **runtime_updates)

            group_updates[group_name] = resolved_group

        resolved = replace(config, **group_updates)
        self._validate_effective_config(resolved, layer="local config")
        return resolved

    def _apply_backend_override(self, base_config: NsConfig, raw_override: Mapping[str, Any]) -> NsConfig:
        if not isinstance(raw_override, MappingABC):
            raise NsConfigError(
                "backend override must be a mapping.",
                details={
                    "field": "backend_override",
                    "actual_type": type(raw_override).__name__,
                },
            )

        self._config_type._reject_unknown_fields(
            raw_override,
            allowed_fields=set(self.GROUP_NAMES),
            path="backend_override",
        )
        if not raw_override:
            return base_config

        base_dict = base_config.to_dict()
        effective_dict = base_config.to_dict()
        override_metadata: dict[str, NsConfigGroupMetadata] = {}
        runtime_override_metadata: dict[str, NsConfigGroupMetadata] = {}
        payload_changed = False

        for group_name, raw_group in raw_override.items():
            if not isinstance(raw_group, MappingABC):
                raise NsConfigError(
                    f"backend_override.{group_name} must be a JSON object.",
                    details={
                        "field": f"backend_override.{group_name}",
                        "actual_type": type(raw_group).__name__,
                    },
                )

            raw_metadata = raw_group.get("metadata")
            if not isinstance(raw_metadata, MappingABC):
                raise NsConfigError(
                    f"backend_override.{group_name}.metadata is required.",
                    details={
                        "field": f"backend_override.{group_name}.metadata",
                        "actual_type": type(raw_metadata).__name__,
                    },
                )

            missing_metadata_fields = sorted(
                self.REQUIRED_OVERRIDE_METADATA_FIELDS.difference(raw_metadata)
            )
            if missing_metadata_fields:
                raise NsConfigError(
                    f"backend_override.{group_name}.metadata is incomplete.",
                    details={
                        "field": f"backend_override.{group_name}.metadata",
                        "missing_fields": missing_metadata_fields,
                    },
                )

            metadata = self._config_type._build_group_metadata(
                raw_metadata,
                path=f"backend_override.{group_name}.metadata",
            )
            self._config_type._validate_group_metadata(group_name, metadata)
            if metadata.source is not NsConfigSource.BACKEND_OVERRIDE:
                self._raise_source_mismatch(
                    layer="backend override",
                    group_name=group_name,
                    expected=NsConfigSource.BACKEND_OVERRIDE,
                    actual=metadata.source,
                )

            timestamp = self._config_type._normalize_effective_at(
                metadata.effective_at,
                field_name=f"backend_override.{group_name}.metadata.effective_at",
                allow_none=False,
            )
            metadata = replace(metadata, effective_at=timestamp)
            base_metadata = getattr(base_config, group_name).metadata

            if metadata.rollback_from_version is not None and metadata.rollback_from_version != base_metadata.group_version:
                raise NsConfigError(
                    f"backend_override.{group_name} rollback source does not match the effective group version.",
                    details={
                        "field": f"backend_override.{group_name}.metadata.rollback_from_version",
                        "value": metadata.rollback_from_version,
                        "effective_group_version": base_metadata.group_version,
                    },
                )

            if group_name == "runtime":
                for runtime_group_name in RUNTIME_CONFIG_GROUP_NAMES:
                    if runtime_group_name not in raw_group:
                        continue

                    raw_runtime_group = raw_group[runtime_group_name]
                    if not isinstance(raw_runtime_group, MappingABC):
                        raise NsConfigError(
                            f"backend_override.runtime.{runtime_group_name} must be a JSON object.",
                            details={
                                "field": f"backend_override.runtime.{runtime_group_name}",
                                "actual_type": type(raw_runtime_group).__name__,
                            },
                        )

                    base_runtime_group = getattr(base_config.runtime, runtime_group_name)
                    base_runtime_dict = _to_json_value(base_runtime_group)
                    base_runtime_payload = {
                        key: value
                        for key, value in base_runtime_dict.items()
                        if key != "metadata"
                    }
                    runtime_override_payload = {
                        key: value
                        for key, value in raw_runtime_group.items()
                        if key != "metadata"
                    }
                    merged_runtime_payload = self._deep_merge(
                        base_runtime_payload,
                        runtime_override_payload,
                    )
                    runtime_group_changed = merged_runtime_payload != base_runtime_payload
                    raw_runtime_metadata = raw_runtime_group.get("metadata")
                    if runtime_group_changed and not isinstance(raw_runtime_metadata, MappingABC):
                        raise NsConfigError(
                            f"backend_override.runtime.{runtime_group_name}.metadata is required when values change.",
                            details={
                                "field": f"backend_override.runtime.{runtime_group_name}.metadata",
                            },
                        )
                    if raw_runtime_metadata is None:
                        continue
                    if not isinstance(raw_runtime_metadata, MappingABC):
                        raise NsConfigError(
                            f"backend_override.runtime.{runtime_group_name}.metadata must be a JSON object.",
                            details={
                                "field": f"backend_override.runtime.{runtime_group_name}.metadata",
                                "actual_type": type(raw_runtime_metadata).__name__,
                            },
                        )

                    missing_runtime_metadata = sorted(
                        self.REQUIRED_OVERRIDE_METADATA_FIELDS.difference(raw_runtime_metadata)
                    )
                    if missing_runtime_metadata:
                        raise NsConfigError(
                            f"backend_override.runtime.{runtime_group_name}.metadata is incomplete.",
                            details={
                                "field": f"backend_override.runtime.{runtime_group_name}.metadata",
                                "missing_fields": missing_runtime_metadata,
                            },
                        )

                    runtime_metadata = self._config_type._build_group_metadata(
                        raw_runtime_metadata,
                        path=f"backend_override.runtime.{runtime_group_name}.metadata",
                    )
                    self._config_type._validate_group_metadata(
                        f"runtime.{runtime_group_name}",
                        runtime_metadata,
                    )
                    runtime_timestamp = self._config_type._normalize_effective_at(
                        runtime_metadata.effective_at,
                        field_name=f"backend_override.runtime.{runtime_group_name}.metadata.effective_at",
                        allow_none=False,
                    )
                    runtime_metadata = replace(
                        runtime_metadata,
                        effective_at=runtime_timestamp,
                    )
                    if runtime_metadata.source is not NsConfigSource.BACKEND_OVERRIDE:
                        self._raise_source_mismatch(
                            layer="backend override",
                            group_name=f"runtime.{runtime_group_name}",
                            expected=NsConfigSource.BACKEND_OVERRIDE,
                            actual=runtime_metadata.source,
                        )
                    if runtime_metadata.config_version != metadata.config_version or runtime_metadata.policy_version != metadata.policy_version:
                        raise NsConfigError(
                            f"backend_override.runtime.{runtime_group_name} versions must match runtime metadata.",
                            details={
                                "field": f"backend_override.runtime.{runtime_group_name}.metadata",
                                "config_version": runtime_metadata.config_version,
                                "policy_version": runtime_metadata.policy_version,
                                "expected_config_version": metadata.config_version,
                                "expected_policy_version": metadata.policy_version,
                            },
                        )
                    base_runtime_metadata = base_runtime_group.metadata
                    if runtime_metadata.rollback_from_version is not None and runtime_metadata.rollback_from_version != base_runtime_metadata.group_version:
                        raise NsConfigError(
                            f"backend_override.runtime.{runtime_group_name} rollback source does not match the effective group version.",
                            details={
                                "field": f"backend_override.runtime.{runtime_group_name}.metadata.rollback_from_version",
                                "value": runtime_metadata.rollback_from_version,
                                "effective_group_version": base_runtime_metadata.group_version,
                            },
                        )
                    if runtime_group_changed and runtime_metadata.group_version == base_runtime_metadata.group_version:
                        raise NsConfigError(
                            f"backend_override.runtime.{runtime_group_name} changed values without a new group_version.",
                            details={
                                "field": f"backend_override.runtime.{runtime_group_name}.metadata.group_version",
                                "value": runtime_metadata.group_version,
                            },
                        )
                    runtime_override_metadata[runtime_group_name] = runtime_metadata

            base_payload = {
                key: value
                for key, value in base_dict[group_name].items()
                if key != "metadata"
            }
            override_payload = {
                key: value
                for key, value in raw_group.items()
                if key != "metadata"
            }
            merged_payload = self._deep_merge(base_payload, override_payload)
            if group_name == "runtime":
                for runtime_group_name, runtime_metadata in runtime_override_metadata.items():
                    merged_payload[runtime_group_name]["metadata"] = _to_json_value(runtime_metadata)
            group_changed = merged_payload != base_payload
            if group_changed and metadata.group_version == base_metadata.group_version:
                raise NsConfigError(
                    f"backend_override.{group_name} changed values without a new group_version.",
                    details={
                        "field": f"backend_override.{group_name}.metadata.group_version",
                        "value": metadata.group_version,
                    },
                )

            payload_changed = payload_changed or group_changed
            merged_payload["metadata"] = _to_json_value(metadata)
            effective_dict[group_name] = merged_payload
            override_metadata[group_name] = metadata

        config_versions = {item.config_version for item in override_metadata.values()}
        policy_versions = {item.policy_version for item in override_metadata.values()}
        if len(config_versions) != 1 or len(policy_versions) != 1:
            raise NsConfigError(
                "backend override versions must be consistent across groups.",
                details={
                    "field": "backend_override.metadata",
                    "config_versions": sorted(config_versions),
                    "policy_versions": sorted(policy_versions),
                },
            )

        target_config_version = next(iter(config_versions))
        target_policy_version = next(iter(policy_versions))
        if payload_changed and target_config_version == base_config.config_version:
            raise NsConfigError(
                "backend override changed values without a new config_version.",
                details={
                    "field": "backend_override.metadata.config_version",
                    "value": target_config_version,
                },
            )

        for group_name in self.GROUP_NAMES:
            if group_name in override_metadata:
                continue

            metadata_dict = effective_dict[group_name]["metadata"]
            metadata_dict["config_version"] = target_config_version
            metadata_dict["policy_version"] = target_policy_version

        for runtime_group_name in RUNTIME_CONFIG_GROUP_NAMES:
            runtime_metadata_dict = effective_dict["runtime"][runtime_group_name]["metadata"]
            runtime_metadata_dict["config_version"] = target_config_version
            runtime_metadata_dict["policy_version"] = target_policy_version

        resolved = self._config_type.from_dict(
            effective_dict,
            environment=self._environment,
        )
        self._validate_effective_config(resolved, layer="backend override")
        return resolved

    def _accept_validated_snapshot(self, snapshot: NsConfig) -> NsConfig:
        if not isinstance(snapshot, self._config_type):
            raise NsConfigError(
                "validated_snapshot must be an immutable NsConfig instance.",
                details={
                    "field": "validated_snapshot",
                    "actual_type": type(snapshot).__name__,
                },
            )

        snapshot.validate(environment=self._environment)
        for group_name, group_config in self._config_type._config_groups(snapshot):
            metadata = group_config.metadata
            if metadata.source is not NsConfigSource.VALIDATED_SNAPSHOT:
                self._raise_source_mismatch(
                    layer="validated snapshot",
                    group_name=group_name,
                    expected=NsConfigSource.VALIDATED_SNAPSHOT,
                    actual=metadata.source,
                )

            self._config_type._normalize_effective_at(
                metadata.effective_at,
                field_name=f"validated_snapshot.{group_name}.metadata.effective_at",
                allow_none=False,
            )

        for runtime_group_name, runtime_group in self._config_type._runtime_config_groups(snapshot.runtime):
            metadata = runtime_group.metadata
            if metadata.source is not NsConfigSource.VALIDATED_SNAPSHOT:
                self._raise_source_mismatch(
                    layer="validated snapshot",
                    group_name=f"runtime.{runtime_group_name}",
                    expected=NsConfigSource.VALIDATED_SNAPSHOT,
                    actual=metadata.source,
                )
            self._config_type._normalize_effective_at(
                metadata.effective_at,
                field_name=f"validated_snapshot.runtime.{runtime_group_name}.metadata.effective_at",
                allow_none=False,
            )

        self._validate_effective_config(snapshot, layer="validated snapshot")
        return snapshot

    def _validate_effective_config(self, config: NsConfig, *, layer: str) -> None:
        config.validate(environment=self._environment)
        try:
            config.config_version
            config.policy_version
        except NsConfigError as error:
            error.details["layer"] = layer
            raise

    @staticmethod
    def _deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
        merged = {
            key: _to_json_value(value)
            for key, value in base.items()
        }
        for key, value in override.items():
            current = merged.get(key)
            if isinstance(current, MappingABC) and isinstance(value, MappingABC):
                merged[key] = NsConfigResolver._deep_merge(current, value)
            else:
                merged[key] = _to_json_value(value)

        return merged

    @staticmethod
    def _raise_source_mismatch(
        *,
        layer: str,
        group_name: str,
        expected: NsConfigSource,
        actual: NsConfigSource,
    ) -> None:
        raise NsConfigError(
            f"{layer} source is invalid for {group_name}.",
            details={
                "field": f"{group_name}.metadata.source",
                "expected": expected.value,
                "actual": actual.value,
            },
        )


ns_config = NsConfig.load()
