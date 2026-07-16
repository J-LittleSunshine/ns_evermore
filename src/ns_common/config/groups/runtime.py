# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from ...exceptions import NsConfigError
from ..metadata import NsConfigGroupMetadata
from ..primitives import _freeze_config_value


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


RUNTIME_CLUSTER_ROLES: tuple[str, ...] = (
    "active_master",
    "singleton",
    "standby_master",
    "sub_node",
)

@dataclass(frozen=True, slots=True, kw_only=True)
class NsRuntimeClusterConfig:
    role: Literal[
        "active_master",
        "singleton",
        "standby_master",
        "sub_node",
    ] = "singleton"
    node_id: str = "local-runtime"
    active_master_url: str = ""
    heartbeat_interval_seconds: int = 5
    leader_lease_seconds: int = 15
    metadata: NsConfigGroupMetadata = field(
        default_factory=lambda: NsConfigGroupMetadata(apply_mode="restart_required")
    )

    def __post_init__(self) -> None:
        if not isinstance(self.role, str) or self.role not in RUNTIME_CLUSTER_ROLES:
            raise NsConfigError(
                "runtime.cluster.role is invalid.",
                details={
                    "field": "runtime.cluster.role",
                    "value": self.role,
                    "allowed_values": list(RUNTIME_CLUSTER_ROLES),
                },
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
