# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from dataclasses import (
    dataclass,
    field
)
from typing import (
    Any,
    Literal
)
from urllib.parse import urlparse

from ns_common.exceptions import NsConfigError

RuntimeMode = Literal["master", "sub_node", "singleton"]
RuntimeFailPolicy = Literal["fail_closed", "fail_open"]
RuntimeBackpressurePolicy = Literal["reject", "queue", "timeout_queue"]
RuntimeMigrationPolicy = Literal["wait", "reject", "proxy"]
RuntimeStoreBackend = Literal["sqlite_wal", "redis", "valkey"]
RuntimeAuditStoreBackend = Literal["sqlite_wal", "direct_db", "http_api"]


def _as_dict(value: Any, *, field_name: str) -> dict[str, Any]:
    if value is None:
        return {}

    if not isinstance(value, dict):
        raise NsConfigError(
            f"{field_name} must be a JSON object.",
            details={
                "field": field_name,
                "actual_type": type(value).__name__,
            },
        )

    return dict(value)


@dataclass(slots=True, kw_only=True)
class NsRuntimeWebSocketConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    path: str = "/runtime/ws"
    ping_interval_seconds: int = 20
    ping_timeout_seconds: int = 20
    max_message_size_bytes: int = 1024 * 1024

    @classmethod
    def from_mapping(cls, raw: dict[str, Any] | None) -> "NsRuntimeWebSocketConfig":
        return cls(**_as_dict(raw, field_name="runtime.server.websocket"))


@dataclass(slots=True, kw_only=True)
class NsRuntimeAdminHttpConfig:
    host: str = "127.0.0.1"
    port: int = 8766
    path: str = "/admin/action"

    @classmethod
    def from_mapping(cls, raw: dict[str, Any] | None) -> "NsRuntimeAdminHttpConfig":
        return cls(**_as_dict(raw, field_name="runtime.server.admin_http"))


@dataclass(slots=True, kw_only=True)
class NsRuntimeServerConfig:
    websocket: NsRuntimeWebSocketConfig = field(default_factory=NsRuntimeWebSocketConfig)
    admin_http: NsRuntimeAdminHttpConfig = field(default_factory=NsRuntimeAdminHttpConfig)
    trusted_proxies: list[str] = field(default_factory=lambda: [
        "127.0.0.1"
    ]
    )

    @classmethod
    def from_mapping(cls, raw: dict[str, Any] | None) -> "NsRuntimeServerConfig":
        data = _as_dict(raw, field_name="runtime.server")
        websocket_raw = data.pop("websocket", None)
        admin_http_raw = data.pop("admin_http", None)

        return cls(
            websocket=NsRuntimeWebSocketConfig.from_mapping(websocket_raw),
            admin_http=NsRuntimeAdminHttpConfig.from_mapping(admin_http_raw),
            **data,
        )


@dataclass(slots=True, kw_only=True)
class NsRuntimeAccessCheckConfig:
    enabled: bool = True
    template: dict[str, Any] = field(
        default_factory=lambda: {
            "resource_type": "ns_runtime_connection",
            "resource_id": "{{ client_type }}",
            "action_code": "connect",
            "context": {
                "runtime_id": "{{ runtime_id }}",
                "cluster_id": "{{ cluster_id }}",
                "mode": "{{ mode }}",
                "client_type": "{{ client_type }}",
                "node_id": "{{ node_id }}",
                "node_group": "{{ node_group }}",
            },
        }
    )

    @classmethod
    def from_mapping(cls, raw: dict[str, Any] | None, *, field_name: str) -> "NsRuntimeAccessCheckConfig":
        return cls(**_as_dict(raw, field_name=field_name))


@dataclass(slots=True, kw_only=True)
class NsRuntimeIamConfig:
    base_url: str = "http://127.0.0.1:8000/api/iam"
    internal_token: str = "change-me-runtime-iam-internal-token"
    fail_policy: RuntimeFailPolicy = "fail_closed"
    introspection_cache_ttl_seconds: int = 60
    invalid_cache_ttl_seconds: int = 10
    connection_access_check: NsRuntimeAccessCheckConfig = field(default_factory=NsRuntimeAccessCheckConfig)

    @classmethod
    def from_mapping(cls, raw: dict[str, Any] | None) -> "NsRuntimeIamConfig":
        data = _as_dict(raw, field_name="runtime.iam")
        connection_access_check_raw = data.pop("connection_access_check", None)

        return cls(
            connection_access_check=NsRuntimeAccessCheckConfig.from_mapping(
                connection_access_check_raw,
                field_name="runtime.iam.connection_access_check",
            ),
            **data,
        )


@dataclass(slots=True, kw_only=True)
class NsRuntimeClusterConfig:
    master_urls: list[str] = field(default_factory=list)
    shard_key_fields: list[str] = field(
        default_factory=lambda: [
            "payload.tenant_id",
            "payload.company_id",
            "metadata.tenant_id",
            "metadata.company_id",
            "node_group",
            "target_type+message_type",
            "client_type",
            "message_id",
        ]
    )
    lease_ttl_seconds: int = 30
    lease_renew_interval_seconds: int = 10
    migration_policy: RuntimeMigrationPolicy = "proxy"
    auto_degrade_enabled: bool = True
    master_unavailable_threshold_seconds: int = 60
    auto_recover_enabled: bool = True

    @classmethod
    def from_mapping(cls, raw: dict[str, Any] | None) -> "NsRuntimeClusterConfig":
        return cls(**_as_dict(raw, field_name="runtime.cluster"))


@dataclass(slots=True, kw_only=True)
class NsRuntimeStoreConfig:
    backend: RuntimeStoreBackend = "sqlite_wal"
    sqlite_path: str = ""
    redis_url: str = ""
    key_prefix: str = "ns_runtime"

    @classmethod
    def from_mapping(
            cls,
            raw: dict[str, Any] | None,
            *,
            field_name: str,
            default_sqlite_path: str,
            default_key_prefix: str,
    ) -> "NsRuntimeStoreConfig":
        data = {
            "backend": "sqlite_wal",
            "sqlite_path": default_sqlite_path,
            "redis_url": "",
            "key_prefix": default_key_prefix,
        }
        data.update(_as_dict(raw, field_name=field_name))
        return cls(**data)


@dataclass(slots=True, kw_only=True)
class NsRuntimeAuditStoreConfig:
    backend: RuntimeAuditStoreBackend = "sqlite_wal"
    sqlite_path: str = "data/ns_runtime_audit.sqlite3"
    database: dict[str, Any] = field(default_factory=dict)
    api_url: str = ""
    key_prefix: str = "ns_runtime_audit"

    @classmethod
    def from_mapping(cls, raw: dict[str, Any] | None) -> "NsRuntimeAuditStoreConfig":
        return cls(**_as_dict(raw, field_name="runtime.audit_store"))


@dataclass(slots=True, kw_only=True)
class NsRuntimeRoutingConfig:
    default_strategy: str = "rule_based"
    default_load_balance: str = "weighted_least_loaded"
    max_hops: int = 8
    rules: list[dict[str, Any]] = field(default_factory=list)
    tenant_isolation_enabled: bool = True
    cross_tenant_allow_rules: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, raw: dict[str, Any] | None) -> "NsRuntimeRoutingConfig":
        return cls(**_as_dict(raw, field_name="runtime.routing"))


@dataclass(slots=True, kw_only=True)
class NsRuntimePluginsConfig:
    import_paths: list[str] = field(default_factory=list)
    scan_dirs: list[str] = field(default_factory=list)
    enable_hot_reload: bool = True

    @classmethod
    def from_mapping(cls, raw: dict[str, Any] | None) -> "NsRuntimePluginsConfig":
        return cls(**_as_dict(raw, field_name="runtime.plugins"))


@dataclass(slots=True, kw_only=True)
class NsRuntimeAdminConfig:
    path: str = "/admin/action"
    iam_access_check: NsRuntimeAccessCheckConfig = field(
        default_factory=lambda: NsRuntimeAccessCheckConfig(
            enabled=True,
            template={
                "resource_type": "ns_runtime_admin",
                "resource_id": "{{ runtime_id }}",
                "action_code": "{{ action }}",
                "context": {
                    "runtime_id": "{{ runtime_id }}",
                    "cluster_id": "{{ cluster_id }}",
                    "mode": "{{ mode }}",
                    "admin_action": "{{ action }}",
                    "client_ip": "{{ client_ip }}",
                    "request_id": "{{ request_id }}",
                },
            },
        )
    )

    @classmethod
    def from_mapping(cls, raw: dict[str, Any] | None) -> "NsRuntimeAdminConfig":
        data = _as_dict(raw, field_name="runtime.admin")
        iam_access_check_raw = data.pop("iam_access_check", None)

        return cls(
            iam_access_check=NsRuntimeAccessCheckConfig.from_mapping(
                iam_access_check_raw,
                field_name="runtime.admin.iam_access_check",
            ),
            **data,
        )


@dataclass(slots=True, kw_only=True)
class NsRuntimeConfig:
    enabled: bool = False
    runtime_id: str = "runtime-01"
    cluster_id: str = "default"
    mode: RuntimeMode = "singleton"

    server: NsRuntimeServerConfig = field(default_factory=NsRuntimeServerConfig)
    iam: NsRuntimeIamConfig = field(default_factory=NsRuntimeIamConfig)
    cluster: NsRuntimeClusterConfig = field(default_factory=NsRuntimeClusterConfig)
    state_store: NsRuntimeStoreConfig = field(
        default_factory=lambda: NsRuntimeStoreConfig(
            backend="sqlite_wal",
            sqlite_path="data/ns_runtime_state.sqlite3",
            key_prefix="ns_runtime_state",
        )
    )
    message_store: NsRuntimeStoreConfig = field(
        default_factory=lambda: NsRuntimeStoreConfig(
            backend="sqlite_wal",
            sqlite_path="data/ns_runtime_message.sqlite3",
            key_prefix="ns_runtime_message",
        )
    )
    audit_store: NsRuntimeAuditStoreConfig = field(default_factory=NsRuntimeAuditStoreConfig)
    routing: NsRuntimeRoutingConfig = field(default_factory=NsRuntimeRoutingConfig)
    plugins: NsRuntimePluginsConfig = field(default_factory=NsRuntimePluginsConfig)
    admin: NsRuntimeAdminConfig = field(default_factory=NsRuntimeAdminConfig)

    global_max_concurrency: int = 1000
    default_handler_max_concurrency: int = 100
    default_connection_max_inflight: int = 32
    default_backpressure_policy: RuntimeBackpressurePolicy = "timeout_queue"

    @classmethod
    def from_mapping(cls, raw: dict[str, Any] | None) -> "NsRuntimeConfig":
        data = _as_dict(raw, field_name="runtime")

        server_raw = data.pop("server", None)
        iam_raw = data.pop("iam", None)
        cluster_raw = data.pop("cluster", None)
        state_store_raw = data.pop("state_store", None)
        message_store_raw = data.pop("message_store", None)
        audit_store_raw = data.pop("audit_store", None)
        routing_raw = data.pop("routing", None)
        plugins_raw = data.pop("plugins", None)
        admin_raw = data.pop("admin", None)

        return cls(
            server=NsRuntimeServerConfig.from_mapping(server_raw),
            iam=NsRuntimeIamConfig.from_mapping(iam_raw),
            cluster=NsRuntimeClusterConfig.from_mapping(cluster_raw),
            state_store=NsRuntimeStoreConfig.from_mapping(
                state_store_raw,
                field_name="runtime.state_store",
                default_sqlite_path="data/ns_runtime_state.sqlite3",
                default_key_prefix="ns_runtime_state",
            ),
            message_store=NsRuntimeStoreConfig.from_mapping(
                message_store_raw,
                field_name="runtime.message_store",
                default_sqlite_path="data/ns_runtime_message.sqlite3",
                default_key_prefix="ns_runtime_message",
            ),
            audit_store=NsRuntimeAuditStoreConfig.from_mapping(audit_store_raw),
            routing=NsRuntimeRoutingConfig.from_mapping(routing_raw),
            plugins=NsRuntimePluginsConfig.from_mapping(plugins_raw),
            admin=NsRuntimeAdminConfig.from_mapping(admin_raw),
            **data,
        )


def validate_runtime_config(runtime: NsRuntimeConfig) -> None:
    if not isinstance(runtime, NsRuntimeConfig):
        raise NsConfigError(
            "runtime must be NsRuntimeConfig.",
            details={
                "field": "runtime",
                "actual_type": type(runtime).__name__,
            },
        )

    _validate_bool("runtime.enabled", runtime.enabled)
    _validate_cache_key_part("runtime.runtime_id", runtime.runtime_id)
    _validate_cache_key_part("runtime.cluster_id", runtime.cluster_id)

    if runtime.mode not in {"master", "sub_node", "singleton"}:
        raise NsConfigError(
            "runtime.mode is invalid.",
            details={
                "field": "runtime.mode",
                "value": runtime.mode,
                "allowed_values": [
                    "master",
                    "sub_node",
                    "singleton"
                ],
            },
        )

    _validate_server_config(runtime.server)
    _validate_iam_config(runtime.iam)
    _validate_cluster_config(runtime.cluster)
    _validate_store_config("runtime.state_store", runtime.state_store)
    _validate_store_config("runtime.message_store", runtime.message_store)
    _validate_audit_store_config(runtime.audit_store)
    _validate_routing_config(runtime.routing)
    _validate_plugins_config(runtime.plugins)
    _validate_admin_config(runtime.admin)

    _validate_positive_int("runtime.global_max_concurrency", runtime.global_max_concurrency)
    _validate_positive_int("runtime.default_handler_max_concurrency", runtime.default_handler_max_concurrency)
    _validate_positive_int("runtime.default_connection_max_inflight", runtime.default_connection_max_inflight)

    if runtime.default_backpressure_policy not in {"reject", "queue", "timeout_queue"}:
        raise NsConfigError(
            "runtime.default_backpressure_policy is invalid.",
            details={
                "field": "runtime.default_backpressure_policy",
                "value": runtime.default_backpressure_policy,
                "allowed_values": [
                    "reject",
                    "queue",
                    "timeout_queue"
                ],
            },
        )


def _validate_server_config(server: NsRuntimeServerConfig) -> None:
    _validate_host("runtime.server.websocket.host", server.websocket.host)
    _validate_port("runtime.server.websocket.port", server.websocket.port)
    _validate_http_path("runtime.server.websocket.path", server.websocket.path)
    _validate_positive_int("runtime.server.websocket.ping_interval_seconds", server.websocket.ping_interval_seconds)
    _validate_positive_int("runtime.server.websocket.ping_timeout_seconds", server.websocket.ping_timeout_seconds)
    _validate_positive_int("runtime.server.websocket.max_message_size_bytes", server.websocket.max_message_size_bytes)

    _validate_host("runtime.server.admin_http.host", server.admin_http.host)
    _validate_port("runtime.server.admin_http.port", server.admin_http.port)
    _validate_http_path("runtime.server.admin_http.path", server.admin_http.path)

    _validate_string_list("runtime.server.trusted_proxies", server.trusted_proxies)


def _validate_iam_config(iam: NsRuntimeIamConfig) -> None:
    _validate_http_url("runtime.iam.base_url", iam.base_url)
    _validate_non_empty_string("runtime.iam.internal_token", iam.internal_token)

    if iam.fail_policy not in {"fail_closed", "fail_open"}:
        raise NsConfigError(
            "runtime.iam.fail_policy is invalid.",
            details={
                "field": "runtime.iam.fail_policy",
                "value": iam.fail_policy,
                "allowed_values": [
                    "fail_closed",
                    "fail_open"
                ],
            },
        )

    _validate_positive_int("runtime.iam.introspection_cache_ttl_seconds", iam.introspection_cache_ttl_seconds)
    _validate_positive_int("runtime.iam.invalid_cache_ttl_seconds", iam.invalid_cache_ttl_seconds)
    _validate_access_check_config("runtime.iam.connection_access_check", iam.connection_access_check)


def _validate_cluster_config(cluster: NsRuntimeClusterConfig) -> None:
    _validate_string_list("runtime.cluster.master_urls", cluster.master_urls, allow_empty=True)
    for index, master_url in enumerate(cluster.master_urls):
        _validate_ws_or_http_url(f"runtime.cluster.master_urls[{index}]", master_url)

    _validate_string_list("runtime.cluster.shard_key_fields", cluster.shard_key_fields)
    _validate_positive_int("runtime.cluster.lease_ttl_seconds", cluster.lease_ttl_seconds)
    _validate_positive_int("runtime.cluster.lease_renew_interval_seconds", cluster.lease_renew_interval_seconds)

    if cluster.lease_renew_interval_seconds >= cluster.lease_ttl_seconds:
        raise NsConfigError(
            "runtime.cluster.lease_renew_interval_seconds must be less than runtime.cluster.lease_ttl_seconds.",
            details={
                "field": "runtime.cluster.lease_renew_interval_seconds",
                "value": cluster.lease_renew_interval_seconds,
                "lease_ttl_seconds": cluster.lease_ttl_seconds,
            },
        )

    if cluster.migration_policy not in {"wait", "reject", "proxy"}:
        raise NsConfigError(
            "runtime.cluster.migration_policy is invalid.",
            details={
                "field": "runtime.cluster.migration_policy",
                "value": cluster.migration_policy,
                "allowed_values": [
                    "wait",
                    "reject",
                    "proxy"
                ],
            },
        )

    _validate_bool("runtime.cluster.auto_degrade_enabled", cluster.auto_degrade_enabled)
    _validate_positive_int("runtime.cluster.master_unavailable_threshold_seconds", cluster.master_unavailable_threshold_seconds)
    _validate_bool("runtime.cluster.auto_recover_enabled", cluster.auto_recover_enabled)


def _validate_store_config(field_name: str, store: NsRuntimeStoreConfig) -> None:
    if store.backend not in {"sqlite_wal", "redis", "valkey"}:
        raise NsConfigError(
            f"{field_name}.backend is invalid.",
            details={
                "field": f"{field_name}.backend",
                "value": store.backend,
                "allowed_values": [
                    "sqlite_wal",
                    "redis",
                    "valkey"
                ],
            },
        )

    _validate_cache_key_part(f"{field_name}.key_prefix", store.key_prefix)

    if store.backend == "sqlite_wal":
        _validate_non_empty_string(f"{field_name}.sqlite_path", store.sqlite_path)

    if store.backend == "redis":
        _validate_cache_url(f"{field_name}.redis_url", store.redis_url, {"redis", "rediss"})

    if store.backend == "valkey":
        _validate_cache_url(f"{field_name}.redis_url", store.redis_url, {"redis", "rediss", "valkey", "valkeys"})


def _validate_audit_store_config(audit_store: NsRuntimeAuditStoreConfig) -> None:
    if audit_store.backend not in {"sqlite_wal", "direct_db", "http_api"}:
        raise NsConfigError(
            "runtime.audit_store.backend is invalid.",
            details={
                "field": "runtime.audit_store.backend",
                "value": audit_store.backend,
                "allowed_values": [
                    "sqlite_wal",
                    "direct_db",
                    "http_api"
                ],
            },
        )

    _validate_cache_key_part("runtime.audit_store.key_prefix", audit_store.key_prefix)

    if audit_store.backend == "sqlite_wal":
        _validate_non_empty_string("runtime.audit_store.sqlite_path", audit_store.sqlite_path)

    if audit_store.backend == "direct_db" and not isinstance(audit_store.database, dict):
        raise NsConfigError(
            "runtime.audit_store.database must be a dict.",
            details={
                "field": "runtime.audit_store.database",
                "actual_type": type(audit_store.database).__name__,
            },
        )

    if audit_store.backend == "http_api":
        _validate_http_url("runtime.audit_store.api_url", audit_store.api_url)


def _validate_routing_config(routing: NsRuntimeRoutingConfig) -> None:
    _validate_non_empty_string("runtime.routing.default_strategy", routing.default_strategy)
    _validate_non_empty_string("runtime.routing.default_load_balance", routing.default_load_balance)
    _validate_positive_int("runtime.routing.max_hops", routing.max_hops)
    _validate_bool("runtime.routing.tenant_isolation_enabled", routing.tenant_isolation_enabled)

    if not isinstance(routing.rules, list):
        raise NsConfigError(
            "runtime.routing.rules must be a list.",
            details={
                "field": "runtime.routing.rules",
                "actual_type": type(routing.rules).__name__,
            },
        )

    if not isinstance(routing.cross_tenant_allow_rules, list):
        raise NsConfigError(
            "runtime.routing.cross_tenant_allow_rules must be a list.",
            details={
                "field": "runtime.routing.cross_tenant_allow_rules",
                "actual_type": type(routing.cross_tenant_allow_rules).__name__,
            },
        )


def _validate_plugins_config(plugins: NsRuntimePluginsConfig) -> None:
    _validate_bool("runtime.plugins.enable_hot_reload", plugins.enable_hot_reload)
    _validate_string_list("runtime.plugins.import_paths", plugins.import_paths, allow_empty=True)
    _validate_string_list("runtime.plugins.scan_dirs", plugins.scan_dirs, allow_empty=True)


def _validate_admin_config(admin: NsRuntimeAdminConfig) -> None:
    _validate_http_path("runtime.admin.path", admin.path)
    _validate_access_check_config("runtime.admin.iam_access_check", admin.iam_access_check)


def _validate_access_check_config(field_name: str, access_check: NsRuntimeAccessCheckConfig) -> None:
    _validate_bool(f"{field_name}.enabled", access_check.enabled)

    if not isinstance(access_check.template, dict):
        raise NsConfigError(
            f"{field_name}.template must be a dict.",
            details={
                "field": f"{field_name}.template",
                "actual_type": type(access_check.template).__name__,
            },
        )

    for required_key in ("resource_type", "resource_id", "action_code"):
        if required_key not in access_check.template:
            raise NsConfigError(
                f"{field_name}.template.{required_key} is required.",
                details={
                    "field": f"{field_name}.template",
                    "required_key": required_key,
                },
            )


def _validate_string_list(field_name: str, value: Any, *, allow_empty: bool = False) -> None:
    if not isinstance(value, list):
        raise NsConfigError(
            f"{field_name} must be a list.",
            details={
                "field": field_name,
                "actual_type": type(value).__name__,
            },
        )

    if not allow_empty and not value:
        raise NsConfigError(
            f"{field_name} must not be empty.",
            details={
                "field": field_name,
            },
        )

    for index, item in enumerate(value):
        _validate_non_empty_string(f"{field_name}[{index}]", item)


def _validate_bool(field_name: str, value: Any) -> None:
    if not isinstance(value, bool):
        raise NsConfigError(
            f"{field_name} must be a boolean.",
            details={
                "field": field_name,
                "value": value,
                "actual_type": type(value).__name__,
            },
        )


def _validate_positive_int(field_name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise NsConfigError(
            f"{field_name} must be a positive integer.",
            details={
                "field": field_name,
                "value": value,
                "actual_type": type(value).__name__,
            },
        )


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


def _validate_cache_key_part(field_name: str, value: Any) -> None:
    _validate_non_empty_string(field_name, value)

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


def _validate_host(field_name: str, value: Any) -> None:
    _validate_non_empty_string(field_name, value)


def _validate_port(field_name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1 or value > 65535:
        raise NsConfigError(
            f"{field_name} must be a valid TCP port.",
            details={
                "field": field_name,
                "value": value,
                "actual_type": type(value).__name__,
                "min_value": 1,
                "max_value": 65535,
            },
        )


def _validate_http_path(field_name: str, value: Any) -> None:
    if not isinstance(value, str) or not value.startswith("/"):
        raise NsConfigError(
            f"{field_name} must start with '/'.",
            details={
                "field": field_name,
                "value": value,
                "actual_type": type(value).__name__,
            },
        )


def _validate_http_url(field_name: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        raise NsConfigError(
            f"{field_name} must be a non-empty URL.",
            details={
                "field": field_name,
                "value": value,
                "actual_type": type(value).__name__,
            },
        )

    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"}:
        raise NsConfigError(
            f"{field_name} scheme is invalid.",
            details={
                "field": field_name,
                "scheme": parsed.scheme,
                "allowed_schemes": [
                    "http",
                    "https"
                ],
            },
        )

    if not parsed.hostname:
        raise NsConfigError(
            f"{field_name} host is required.",
            details={
                "field": field_name,
                "value": value,
            },
        )


def _validate_ws_or_http_url(field_name: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        raise NsConfigError(
            f"{field_name} must be a non-empty URL.",
            details={
                "field": field_name,
                "value": value,
                "actual_type": type(value).__name__,
            },
        )

    parsed = urlparse(value.strip())
    if parsed.scheme not in {"ws", "wss", "http", "https"}:
        raise NsConfigError(
            f"{field_name} scheme is invalid.",
            details={
                "field": field_name,
                "scheme": parsed.scheme,
                "allowed_schemes": [
                    "ws",
                    "wss",
                    "http",
                    "https"
                ],
            },
        )

    if not parsed.hostname:
        raise NsConfigError(
            f"{field_name} host is required.",
            details={
                "field": field_name,
                "value": value,
            },
        )


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
